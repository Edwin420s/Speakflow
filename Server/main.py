import os
import structlog
import time
import asyncio
import uvicorn
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Request, status, Depends, Query, WebSocket
from typing import Optional
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from pydantic import ValidationError

from models import (
    TranscriptRequest, SpeakFlowResponse, ErrorResponse, 
    Activity, ActivityFeed, Timeline, TimelineEvent as TimelineEventModel, 
    ActivityType, Priority, TaskStatus
)
from ai_processor import extract_tasks_and_summary
from trello_integration import create_trello_cards
from whatsapp_integration import send_whatsapp_message, format_whatsapp_summary
from config import WHATSAPP_ENABLED, TRELLO_ENABLED
from database import init_database, get_database, Activity as DBActivity, TimelineEvent as DBTimelineEvent
from auth import get_current_api_key, log_api_usage, AuthManager
from websocket_handlers import get_websocket_manager, get_stt_service_for_language
from device_integration import get_device_protocol, identify_device_type, validate_device_compatibility
from user_auth import get_auth_manager, AuthProvider, create_demo_users
from conversation_storage import get_conversation_storage, extract_structured_data_from_ai_result

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()

# Rate limiting
limiter = Limiter(key_func=get_remote_address)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    logger.info("Starting SpeakFlow API server")
    
    # Initialize database
    try:
        init_database()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error("Failed to initialize database", error=str(e))
        raise
    
    yield
    logger.info("Shutting down SpeakFlow API server")

app = FastAPI(
    title="SpeakFlow API",
    version="1.0.0",
    description="AI-powered meeting transcript analysis and task extraction API",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# Rate limiting exception handler
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Security middleware
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["*"]  # Configure appropriately for production
)

# CORS middleware (configure origins for production)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
    allow_credentials=True,
)

@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    """Add processing time header and log API usage."""
    start_time = time.time()
    
    # Get request details for logging
    api_key = None
    try:
        # Try to get API key without raising exception for missing auth
        authorization = request.headers.get("authorization")
        if authorization:
            from fastapi.security import HTTPBearer
            security = HTTPBearer(auto_error=False)
            credentials = await security(request)
            if credentials:
                api_key = auth_manager.validate_api_key(credentials.credentials)
    except:
        pass
    
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    
    # Log API usage if we have an API key
    if api_key:
        try:
            await log_api_usage(
                api_key=api_key,
                endpoint=str(request.url.path),
                method=request.method,
                ip_address=get_remote_address(request),
                user_agent=request.headers.get("user-agent", ""),
                request_size=len(request.body) if hasattr(request, 'body') else 0,
                response_size=len(response.body) if hasattr(response, 'body') else 0,
                status_code=response.status_code,
                processing_time_ms=int(process_time * 1000),
                error_message=None if response.status_code < 400 else "Request failed"
            )
        except Exception as e:
            logger.error("Failed to log API usage", error=str(e))
    
    return response

@app.exception_handler(ValidationError)
async def validation_exception_handler(request: Request, exc: ValidationError):
    """Handle Pydantic validation errors."""
    logger.warning("Validation error", error=exc.errors(), path=request.url.path)
    return HTTPException(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        detail={"error": "Validation failed", "details": exc.errors()}
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle general exceptions."""
    logger.error("Unhandled exception", error=str(exc), path=request.url.path)
    return HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail={"error": "Internal server error"}
    )

@app.get("/")
@limiter.limit("10/minute")
def root(request: Request):
    """Health check endpoint."""
    return {
        "message": "SpeakFlow backend is running",
        "status": "healthy",
        "version": "1.0.0"
    }

@app.get("/health")
@limiter.limit("30/minute")
def health_check(request: Request):
    """Detailed health check endpoint."""
    return {
        "status": "healthy",
        "services": {
            "openai": bool(os.getenv("OPENAI_API_KEY")),
            "trello": TRELLO_ENABLED,
            "whatsapp": WHATSAPP_ENABLED,
            "database": True,  # If we can respond, DB is working
        },
        "timestamp": time.time()
    }

@app.post("/api/analyze", response_model=SpeakFlowResponse)
@limiter.limit("5/minute")
async def analyze_conversation(
    request: Request, 
    transcript_request: TranscriptRequest,
    api_key = Depends(get_current_api_key)
):
    """
    Analyze conversation transcript to extract tasks and summary.
    
    - **text**: The conversation transcript to analyze
    - **Returns**: Extracted tasks and meeting summary
    
    Requires API key authentication.
    """
    try:
        # Validate input
        if not transcript_request.text or not transcript_request.text.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"error": "Transcript text cannot be empty"}
            )
        
        # Log request
        logger.info(
            "Processing transcript analysis request",
            text_length=len(transcript_request.text),
            client_ip=get_remote_address(request),
            api_key_name=api_key.name
        )
        
        # 1. Log AI processing started activity
        start_activity = log_activity(
            type=ActivityType.AI_PROCESSING_STARTED,
            title="AI Processing Started",
            description=f"Processing transcript of {len(transcript_request.text)} characters",
            metadata={"text_length": len(transcript_request.text), "client_ip": get_remote_address(request)}
        )
        
        # 2. AI processing
        result = extract_tasks_and_summary(transcript_request.text)
        processing_time = int((time.time() - start_time) * 1000)
        
        # 3. Log transcript processed activity
        transcript_activity = log_activity(
            type=ActivityType.TRANSCRIPT_PROCESSED,
            title="Transcript Processed",
            description=f"Successfully processed transcript and extracted {len(result['tasks'])} tasks",
            metadata={
                "tasks_count": len(result['tasks']),
                "summary_length": len(result['summary']),
                "processing_time_ms": processing_time
            }
        )
        
        # 4. Log AI processing completed activity
        completion_activity = log_activity(
            type=ActivityType.AI_PROCESSING_COMPLETED,
            title="AI Processing Completed",
            description="AI processing completed successfully",
            metadata={
                "processing_time_ms": processing_time,
                "tasks_extracted": len(result['tasks']),
                "confidence_score": result.get("confidence_score", 0.0)
            }
        )
        
        # 5. Optional: create Trello cards
        trello_results = []
        if TRELLO_ENABLED and result["tasks"]:
            try:
                trello_results = create_trello_cards(result["tasks"])
                logger.info("Trello cards created", count=len(trello_results))
                
                # Log Trello activity
                log_activity(
                    type=ActivityType.TRELLO_CARD_CREATED,
                    title="Trello Cards Created",
                    description=f"Created {len(trello_results)} Trello cards",
                    metadata={"card_count": len(trello_results), "cards": trello_results}
                )
            except Exception as e:
                logger.error("Failed to create Trello cards", error=str(e))
        
        # 6. Optional: send WhatsApp summary
        if WHATSAPP_ENABLED and result["summary"]:
            try:
                formatted_message = format_whatsapp_summary(result["summary"], len(result["tasks"]), result["tasks"])
                whatsapp_result = send_whatsapp_message(formatted_message)
                logger.info("WhatsApp message sent", result=whatsapp_result.status)
                
                # Log WhatsApp activity
                log_activity(
                    type=ActivityType.WHATSAPP_SENT,
                    title="WhatsApp Summary Sent",
                    description="Meeting summary sent via WhatsApp",
                    metadata={"message_status": whatsapp_result.status, "message_length": len(formatted_message)}
                )
            except Exception as e:
                logger.error("Failed to send WhatsApp message", error=str(e))
        
        logger.info(
            "Successfully processed transcript",
            tasks_count=len(result["tasks"]),
            summary_length=len(result["summary"])
        )
        
        return SpeakFlowResponse(
            tasks=result["tasks"],
            summary=result["summary"],
            processing_time_ms=processing_time,
            confidence_score=result.get("confidence_score"),
            activity_id=completion_activity.id if completion_activity else None
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error processing transcript", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "Failed to process transcript"}
        )

# Admin endpoints for API key management
@app.post("/admin/api-keys")
@limiter.limit("2/minute")
async def create_api_key(
    request: Request,
    name: str,
    expires_in_days: int = 365,
    api_key = Depends(get_current_api_key)
):
    """Create a new API key (admin endpoint)."""
    try:
        auth_manager_obj = AuthManager()
        new_key = auth_manager_obj.create_api_key(
            name=name,
            created_by=api_key.name,
            expires_in_days=expires_in_days
        )
        
        logger.info("API key created", created_by=api_key.name, key_name=name)
        
        return {
            "api_key": new_key,
            "name": name,
            "expires_in_days": expires_in_days,
            "message": "API key created successfully"
        }
        
    except Exception as e:
        logger.error("Failed to create API key", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "Failed to create API key"}
        )

@app.get("/admin/api-keys")
@limiter.limit("10/minute")
async def list_api_keys(
    request: Request,
    api_key = Depends(get_current_api_key)
):
    """List all API keys (admin endpoint)."""
    try:
        auth_manager_obj = AuthManager()
        keys = auth_manager_obj.list_api_keys()
        
        return {
            "api_keys": [
                {
                    "id": key.id,
                    "name": key.name,
                    "active": key.active,
                    "usage_count": key.usage_count,
                    "last_used": key.last_used,
                    "created_at": key.created_at,
                    "expires_at": key.expires_at
                }
                for key in keys
            ]
        }
        
    except Exception as e:
        logger.error("Failed to list API keys", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "Failed to list API keys"}
        )

@app.delete("/admin/api-keys/{key_id}")
@limiter.limit("5/minute")
async def revoke_api_key(
    request: Request,
    key_id: int,
    api_key = Depends(get_current_api_key)
):
    """Revoke an API key (admin endpoint)."""
    try:
        auth_manager_obj = AuthManager()
        success = auth_manager_obj.revoke_api_key(key_id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"error": "API key not found"}
            )
        
        logger.info("API key revoked", revoked_by=api_key.name, key_id=key_id)
        
        return {"message": "API key revoked successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to revoke API key", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "Failed to revoke API key"}
        )

# Initialize auth manager
auth_manager = AuthManager()

def log_activity(type: ActivityType, title: str, description: str, metadata: dict = None, 
                user_id: str = None, session_id: str = None, transcript_id: int = None, 
                task_id: int = None) -> Activity:
    """Log an activity to the database."""
    try:
        db = get_database()
        session = db.get_session()
        
        activity = Activity(
            type=type.value,
            title=title,
            description=description,
            activity_metadata=metadata or {},
            user_id=user_id,
            session_id=session_id,
            transcript_id=transcript_id,
            task_id=task_id
        )
        
        session.add(activity)
        session.commit()
        session.refresh(activity)
        
        logger.info("Activity logged", activity_type=type.value, activity_id=activity.id)
        return activity
        
    except Exception as e:
        logger.error("Failed to log activity", error=str(e), activity_type=type.value)
        return None
    finally:
        if 'session' in locals():
            session.close()

def create_timeline_event(title: str, description: str, event_type: ActivityType, 
                         related_task_id: int = None, metadata: dict = None) -> TimelineEvent:
    """Create a timeline event."""
    try:
        db = get_database()
        session = db.get_session()
        
        event = TimelineEvent(
            title=title,
            description=description,
            event_type=event_type.value,
            related_task_id=related_task_id,
            event_metadata=metadata or {}
        )
        
        session.add(event)
        session.commit()
        session.refresh(event)
        
        logger.info("Timeline event created", event_type=event_type.value, event_id=event.id)
        return event
        
    except Exception as e:
        logger.error("Failed to create timeline event", error=str(e), event_type=event_type.value)
        return None
    finally:
        if 'session' in locals():
            session.close()

@app.post("/api/trello/create")
@limiter.limit("10/minute")
async def create_trello_card(
    request: Request,
    task: dict,
    api_key = Depends(get_current_api_key)
):
    """Create a Trello card for a single task."""
    try:
        if not TRELLO_ENABLED:
            return {"error": "Trello integration is disabled"}
        
        results = create_trello_cards([task])
        return results[0] if results else {"error": "Failed to create card"}
        
    except Exception as e:
        logger.error("Error creating Trello card", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "Failed to create Trello card"}
        )

@app.post("/api/whatsapp/send")
@limiter.limit("10/minute")
async def send_whatsapp(
    request: Request,
    message_data: dict,
    api_key = Depends(get_current_api_key)
):
    """Send WhatsApp message."""
    try:
        if not WHATSAPP_ENABLED:
            return {"error": "WhatsApp integration is disabled"}
        
        message = message_data.get("message", "")
        if not message:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"error": "Message cannot be empty"}
            )
        
        result = send_whatsapp_message(message)
        return {
            "message_sid": result.message_sid,
            "status": result.status,
            "success": not result.error
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error sending WhatsApp message", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "Failed to send WhatsApp message"}
        )

@app.post("/api/omi/webhook")
@limiter.limit("20/minute")
async def omi_webhook(
    request: Request,
    webhook_data: dict,
    api_key = Depends(get_current_api_key)
):
    """
    Handle webhook from Omi AI wearable device.
    Processes real-time conversation data from Omi device.
    """
    try:
        # Validate webhook structure
        if not webhook_data.get("data", {}).get("transcript"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"error": "Missing transcript in webhook data"}
            )
        
        transcript = webhook_data["data"]["transcript"]
        device_id = webhook_data.get("device_id", "unknown")
        
        logger.info(
            "Processing Omi webhook",
            device_id=device_id,
            transcript_length=len(transcript),
            api_key_name=api_key.name
        )
        
        # Process the transcript using existing AI processor
        result = extract_tasks_and_summary(transcript)
        
        # Create Trello cards if enabled
        trello_results = []
        if TRELLO_ENABLED and result["tasks"]:
            try:
                trello_results = create_trello_cards(result["tasks"])
                logger.info("Trello cards created from Omi webhook", count=len(trello_results))
            except Exception as e:
                logger.error("Failed to create Trello cards from Omi webhook", error=str(e))
        
        # Send WhatsApp summary if enabled
        if WHATSAPP_ENABLED and result["summary"]:
            try:
                formatted_message = format_whatsapp_summary(
                    result["summary"], 
                    len(result["tasks"]), 
                    result["tasks"]
                )
                whatsapp_result = send_whatsapp_message(formatted_message)
                logger.info("WhatsApp message sent from Omi webhook", result=whatsapp_result.status)
            except Exception as e:
                logger.error("Failed to send WhatsApp message from Omi webhook", error=str(e))
        
        return SpeakFlowResponse(
            tasks=result["tasks"],
            summary=result["summary"],
            source="omi_webhook",
            device_id=device_id
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error processing Omi webhook", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "Failed to process Omi webhook"}
        )

@app.get("/api/omi/status")
@limiter.limit("10/minute")
async def omi_device_status(
    request: Request,
    api_key = Depends(get_current_api_key)
):
    """Get Omi device connection status."""
    try:
        omi_integration = get_omi_integration()
        
        return {
            "device_connected": omi_integration.is_connected,
            "real_time_processing": omi_integration.processing_enabled,
            "conversation_buffer_length": len(omi_integration.conversation_buffer),
            "device_config": omi_integration.device_config,
            "message": "Omi device integration ready for hackathon demo"
        }
        
    except Exception as e:
        logger.error("Error getting Omi device status", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "Failed to get Omi device status"}
        )

# Activity Feed endpoints
@app.get("/api/activities", response_model=ActivityFeed)
@limiter.limit("10/minute")
async def get_activity_feed(
    request: Request,
    page: int = 1,
    page_size: int = 20,
    activity_type: Optional[str] = None,
    user_id: Optional[str] = None,
    api_key = Depends(get_current_api_key)
):
    """Get paginated activity feed."""
    try:
        db = get_database()
        session = db.get_session()
        
        # Build query
        query = session.query(DBActivity)
        
        # Apply filters
        if activity_type:
            query = query.filter(DBActivity.type == activity_type)
        if user_id:
            query = query.filter(DBActivity.user_id == user_id)
        
        # Count total activities
        total_count = query.count()
        
        # Apply pagination
        offset = (page - 1) * page_size
        activities = query.order_by(DBActivity.timestamp.desc()).offset(offset).limit(page_size).all()
        
        # Convert to response models
        activity_models = []
        for activity in activities:
            activity_models.append(Activity(
                id=activity.id,
                type=ActivityType(activity.type),
                title=activity.title,
                description=activity.description,
                metadata=activity.activity_metadata or {},
                timestamp=activity.timestamp,
                user_id=activity.user_id,
                session_id=activity.session_id
            ))
        
        has_more = (offset + len(activities)) < total_count
        
        return ActivityFeed(
            activities=activity_models,
            total_count=total_count,
            page=page,
            page_size=page_size,
            has_more=has_more
        )
        
    except Exception as e:
        logger.error("Error fetching activity feed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "Failed to fetch activity feed"}
        )
    finally:
        if 'session' in locals():
            session.close()

@app.get("/api/timeline", response_model=Timeline)
@limiter.limit("10/minute")
async def get_timeline(
    request: Request,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    event_type: Optional[str] = None,
    api_key = Depends(get_current_api_key)
):
    """Get timeline with progress tracking."""
    try:
        db = get_database()
        session = db.get_session()
        
        # Build query for timeline events
        query = session.query(TimelineEvent)
        
        # Apply filters
        if event_type:
            query = query.filter(TimelineEvent.event_type == event_type)
        if start_date:
            query = query.filter(TimelineEvent.timestamp >= datetime.fromisoformat(start_date))
        if end_date:
            query = query.filter(TimelineEvent.timestamp <= datetime.fromisoformat(end_date))
        
        # Get all events
        events = query.order_by(TimelineEvent.timestamp.asc()).all()
        
        # Calculate completion statistics
        total_events = len(events)
        completed_events = sum(1 for event in events if event.completed)
        completion_percentage = (completed_events / total_events * 100) if total_events > 0 else 0.0
        
        # Get task statistics
        active_tasks = session.query(Task).filter(Task.status.in_(['pending', 'in_progress'])).count()
        completed_tasks = session.query(Task).filter(Task.status == 'completed').count()
        
        # Convert to response models
        timeline_events = []
        for event in events:
            timeline_events.append(TimelineEvent(
                id=event.id,
                title=event.title,
                description=event.description,
                event_type=ActivityType(event.event_type),
                timestamp=event.timestamp,
                completed=event.completed,
                progress_percentage=event.progress_percentage,
                related_task_id=event.related_task_id,
                metadata=event.event_metadata or {}
            ))
        
        # Get timeline date range
        start_timeline = events[0].timestamp if events else None
        end_timeline = events[-1].timestamp if events else None
        
        return Timeline(
            events=timeline_events,
            total_events=total_events,
            completion_percentage=completion_percentage,
            start_date=start_timeline,
            end_date=end_timeline,
            active_tasks=active_tasks,
            completed_tasks=completed_tasks
        )
        
    except Exception as e:
        logger.error("Error fetching timeline", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "Failed to fetch timeline"}
        )
    finally:
        if 'session' in locals():
            session.close()

@app.post("/api/timeline/events", response_model=TimelineEventModel)
@limiter.limit("5/minute")
async def create_timeline_event_endpoint(
    request: Request,
    event_data: dict,
    api_key = Depends(get_current_api_key)
):
    """Create a new timeline event."""
    try:
        # Validate required fields
        required_fields = ['title', 'description', 'event_type']
        for field in required_fields:
            if field not in event_data:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={"error": f"Missing required field: {field}"}
                )
        
        # Validate event type
        try:
            event_type = ActivityType(event_data['event_type'])
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"error": "Invalid event type"}
            )
        
        # Create timeline event
        event = create_timeline_event(
            title=event_data['title'],
            description=event_data['description'],
            event_type=event_type,
            related_task_id=event_data.get('related_task_id'),
            metadata=event_data.get('metadata', {})
        )
        
        if not event:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={"error": "Failed to create timeline event"}
            )
        
        return TimelineEvent(
            id=event.id,
            title=event.title,
            description=event.description,
            event_type=ActivityType(event.event_type),
            timestamp=event.timestamp,
            completed=event.completed,
            progress_percentage=event.progress_percentage,
            related_task_id=event.related_task_id,
            metadata=event.metadata or {}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error creating timeline event", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "Failed to create timeline event"}
        )

@app.put("/api/timeline/events/{event_id}", response_model=TimelineEventModel)
@limiter.limit("5/minute")
async def update_timeline_event(
    request: Request,
    event_id: int,
    event_data: dict,
    api_key = Depends(get_current_api_key)
):
    """Update a timeline event."""
    try:
        db = get_database()
        session = db.get_session()
        
        # Get existing event
        event = session.query(DBTimelineEvent).filter(DBTimelineEvent.id == event_id).first()
        if not event:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"error": "Timeline event not found"}
            )
        
        # Update fields
        if 'title' in event_data:
            event.title = event_data['title']
        if 'description' in event_data:
            event.description = event_data['description']
        if 'completed' in event_data:
            event.completed = event_data['completed']
        if 'progress_percentage' in event_data:
            event.progress_percentage = event_data['progress_percentage']
        if 'metadata' in event_data:
            event.metadata = event_data['metadata']
        
        event.updated_at = datetime.utcnow()
        session.commit()
        session.refresh(event)
        
        return TimelineEvent(
            id=event.id,
            title=event.title,
            description=event.description,
            event_type=ActivityType(event.event_type),
            timestamp=event.timestamp,
            completed=event.completed,
            progress_percentage=event.progress_percentage,
            related_task_id=event.related_task_id,
            metadata=event.metadata or {}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error updating timeline event", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "Failed to update timeline event"}
        )
    finally:
        if 'session' in locals():
            session.close()

@app.post("/api/omi/connect", response_model=TimelineEventModel)
@limiter.limit("5/minute")
async def connect_omi_device(
    request: Request,
    api_key = Depends(get_current_api_key)
):
    """Connect to Omi device (simulated for demo)."""
    try:
        omi_integration = get_omi_integration()
        success = omi_integration.simulate_omi_connection()
        
        if success:
            return {
                "message": "Omi device connected successfully",
                "device_id": "OMI-DEMO-001",
                "status": "connected",
                "capabilities": [
                    "real_time_transcription",
                    "ai_task_extraction", 
                    "trello_integration",
                    "whatsapp_followups"
                ]
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={"error": "Failed to connect to Omi device"}
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error connecting Omi device", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "Failed to connect to Omi device"}
        )

@app.post("/api/omi/demo-stream")
@limiter.limit("3/minute")
async def start_demo_stream(
    request: Request,
    api_key = Depends(get_current_api_key)
):
    """Start demo conversation stream from Omi device."""
    try:
        omi_integration = get_omi_integration()
        
        if not omi_integration.is_connected:
            # Auto-connect for demo
            omi_integration.simulate_omi_connection()
        
        # Start real-time processing
        omi_integration.start_real_time_processing()
        
        # Simulate processing demo conversation
        demo_tasks = []
        for sentence in omi_integration.get_demo_conversation_stream():
            result = omi_integration.process_conversation_chunk(b"", sentence)
            if result.get("tasks"):
                demo_tasks.extend(result["tasks"])
        
        return {
            "message": "Demo stream completed",
            "processed_sentences": len(list(omi_integration.get_demo_conversation_stream())),
            "tasks_extracted": len(demo_tasks),
            "demo_tasks": demo_tasks[:3],  # Return first 3 tasks as preview
            "note": "Full processing results sent to Trello and WhatsApp"
        }
        
    except Exception as e:
        logger.error("Error starting demo stream", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "Failed to start demo stream"}
        )

# Authentication Endpoints (following Omi Firebase Auth patterns)
@app.post("/auth/firebase/login")
@limiter.limit("5/minute")
async def firebase_login(request: Request, auth_data: dict):
    """Authenticate with Firebase ID token."""
    try:
        id_token = auth_data.get("id_token")
        if not id_token:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"error": "id_token is required"}
            )
        
        auth_manager = get_auth_manager()
        uid = auth_manager.verify_firebase_token(id_token)
        
        if not uid:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={"error": "Invalid Firebase token"}
            )
        
        # Generate auth tokens
        tokens = auth_manager.generate_auth_tokens(uid)
        if not tokens:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={"error": "Failed to generate tokens"}
            )
        
        # Get user profile
        profile = auth_manager.get_user_profile(uid)
        
        return {
            "user": {
                "uid": profile.uid,
                "email": profile.email,
                "display_name": profile.display_name,
                "photo_url": profile.photo_url,
                "auth_provider": profile.auth_provider.value,
                "created_at": profile.created_at.isoformat(),
                "last_login": profile.last_login.isoformat() if profile.last_login else None,
                "device_preferences": profile.device_preferences,
                "notification_settings": profile.notification_settings,
                "subscription_tier": profile.subscription_tier
            },
            "tokens": {
                "access_token": tokens.access_token,
                "refresh_token": tokens.refresh_token,
                "token_type": tokens.token_type,
                "expires_in": tokens.expires_in
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Firebase login failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "Authentication failed"}
        )

@app.post("/auth/email/login")
@limiter.limit("5/minute")
async def email_login(request: Request, auth_data: dict):
    """Login with email and password."""
    try:
        email = auth_data.get("email")
        password = auth_data.get("password")
        
        if not email or not password:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"error": "email and password are required"}
            )
        
        auth_manager = get_auth_manager()
        uid = auth_manager.authenticate_with_email_password(email, password)
        
        if not uid:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={"error": "Invalid email or password"}
            )
        
        # Generate auth tokens
        tokens = auth_manager.generate_auth_tokens(uid)
        if not tokens:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={"error": "Failed to generate tokens"}
            )
        
        # Get user profile
        profile = auth_manager.get_user_profile(uid)
        
        return {
            "user": {
                "uid": profile.uid,
                "email": profile.email,
                "display_name": profile.display_name,
                "photo_url": profile.photo_url,
                "auth_provider": profile.auth_provider.value,
                "created_at": profile.created_at.isoformat(),
                "last_login": profile.last_login.isoformat() if profile.last_login else None,
                "device_preferences": profile.device_preferences,
                "notification_settings": profile.notification_settings,
                "subscription_tier": profile.subscription_tier
            },
            "tokens": {
                "access_token": tokens.access_token,
                "refresh_token": tokens.refresh_token,
                "token_type": tokens.token_type,
                "expires_in": tokens.expires_in
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Email login failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "Authentication failed"}
        )

@app.post("/auth/refresh")
@limiter.limit("10/minute")
async def refresh_token(request: Request, auth_data: dict):
    """Refresh access token."""
    try:
        refresh_token = auth_data.get("refresh_token")
        if not refresh_token:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"error": "refresh_token is required"}
            )
        
        auth_manager = get_auth_manager()
        access_token = auth_manager.refresh_access_token(refresh_token)
        
        if not access_token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={"error": "Invalid or expired refresh token"}
            )
        
        return {
            "access_token": access_token,
            "token_type": "Bearer",
            "expires_in": 3600
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Token refresh failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "Token refresh failed"}
        )

# Device Management Endpoints (following Omi documentation)
@app.get("/v1/devices/scan")
@limiter.limit("10/minute")
async def scan_devices(
    request: Request,
    device_type: Optional[str] = None,
    api_key = Depends(get_current_api_key)
):
    """Scan for available Omi devices following BLE protocol."""
    try:
        device_protocol = get_device_protocol()
        
        # Convert string to DeviceType enum if provided
        target_type = None
        if device_type:
            try:
                target_type = DeviceType(device_type)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={"error": f"Invalid device type: {device_type}"}
                )
        
        # Scan for devices
        devices = await device_protocol.scan_for_devices(target_type)
        
        # Convert to response format
        device_list = []
        for device in devices:
            device_list.append({
                "device_id": device.device_id,
                "name": device.name,
                "type": device.device_type.value,
                "manufacturer": device.manufacturer,
                "firmware_version": device.firmware_version,
                "audio_codec": device.audio_codec.value,
                "sample_rate": device.sample_rate,
                "battery_level": device.battery_level,
                "connected": device.device_id in device_protocol.connected_devices
            })
        
        return {
            "devices": device_list,
            "count": len(device_list),
            "scan_time": time.time()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error scanning devices", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "Failed to scan devices"}
        )

@app.post("/v1/devices/{device_id}/connect")
@limiter.limit("5/minute")
async def connect_device(
    request: Request,
    device_id: str,
    api_key = Depends(get_current_api_key)
):
    """Connect to Omi device via BLE."""
    try:
        device_protocol = get_device_protocol()
        
        # Validate device exists
        available_devices = await device_protocol.scan_for_devices()
        device_exists = any(d.device_id == device_id for d in available_devices)
        
        if not device_exists:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"error": "Device not found"}
            )
        
        # Connect to device
        success = await device_protocol.connect_device(device_id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={"error": "Failed to connect to device"}
            )
        
        # Get device info
        device_info = await device_protocol.get_device_info(device_id)
        
        # Log connection activity
        await log_activity(
            type=ActivityType.OMI_DEVICE_CONNECTED,
            title=f"Omi Device Connected",
            description=f"Connected to {device_info.name}",
            metadata={"device_id": device_id, "device_type": device_info.device_type.value}
        )
        
        return {
            "device_id": device_id,
            "name": device_info.name,
            "type": device_info.device_type.value,
            "connected": True,
            "battery_level": device_info.battery_level,
            "audio_codec": device_info.audio_codec.value,
            "sample_rate": device_info.sample_rate
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error connecting device", device_id=device_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "Failed to connect to device"}
        )

@app.post("/v1/devices/{device_id}/disconnect")
@limiter.limit("5/minute")
async def disconnect_device(
    request: Request,
    device_id: str,
    api_key = Depends(get_current_api_key)
):
    """Disconnect from Omi device."""
    try:
        device_protocol = get_device_protocol()
        
        # Check if device is connected
        if device_id not in device_protocol.connected_devices:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"error": "Device not connected"}
            )
        
        # Disconnect device
        await device_protocol.disconnect_device(device_id)
        
        return {
            "device_id": device_id,
            "connected": False,
            "message": "Device disconnected successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error disconnecting device", device_id=device_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "Failed to disconnect device"}
        )

@app.get("/v1/devices/{device_id}/status")
@limiter.limit("10/minute")
async def get_device_status(
    request: Request,
    device_id: str,
    api_key = Depends(get_current_api_key)
):
    """Get device status and information."""
    try:
        device_protocol = get_device_protocol()
        
        # Get device info
        device_info = await device_protocol.get_device_info(device_id)
        if not device_info:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"error": "Device not found"}
            )
        
        # Get battery level
        battery_level = await device_protocol.get_battery_level(device_id)
        
        return {
            "device_id": device_id,
            "name": device_info.name,
            "type": device_info.device_type.value,
            "manufacturer": device_info.manufacturer,
            "firmware_version": device_info.firmware_version,
            "connected": device_id in device_protocol.connected_devices,
            "battery_level": battery_level,
            "audio_codec": device_info.audio_codec.value,
            "sample_rate": device_info.sample_rate,
            "supported_services": [
                {
                    "uuid": service.uuid,
                    "name": service.name,
                    "characteristics": service.characteristics
                }
                for service in device_protocol.get_supported_services()
            ]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error getting device status", device_id=device_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "Failed to get device status"}
        )

@app.get("/v1/conversations")
@limiter.limit("10/minute")
async def get_conversations(
    request: Request,
    user_id: str = Query(..., description="User ID"),
    limit: int = Query(default=50, ge=1, le=100),
    include_discarded: bool = Query(default=False),
    api_key = Depends(get_current_api_key)
):
    """Get user conversations following Omi documentation."""
    try:
        conversation_storage = get_conversation_storage()
        
        # Get conversations
        conversations = conversation_storage.get_user_conversations(
            user_id=user_id,
            limit=limit,
            include_discarded=include_discarded
        )
        
        # Convert to response format
        conversation_list = []
        for conv in conversations:
            conversation_list.append({
                "id": conv.id,
                "created_at": conv.created_at.isoformat(),
                "started_at": conv.started_at.isoformat() if conv.started_at else None,
                "finished_at": conv.finished_at.isoformat() if conv.finished_at else None,
                "source": conv.source.value,
                "language": conv.language,
                "status": conv.status.value,
                "title": conv.structured.title,
                "overview": conv.structured.overview,
                "category": conv.structured.category,
                "duration": conv.duration,
                "transcript_segments_count": len(conv.transcript_segments),
                "action_items_count": len(conv.structured.action_items),
                "memories_count": len(conv.structured.memories),
                "device_id": conv.device_id,
                "visibility": conv.visibility
            })
        
        return {
            "conversations": conversation_list,
            "count": len(conversation_list),
            "user_id": user_id
        }
        
    except Exception as e:
        logger.error("Error getting conversations", user_id=user_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "Failed to get conversations"}
        )

@app.get("/v1/conversations/{conversation_id}")
@limiter.limit("10/minute")
async def get_conversation(
    request: Request,
    conversation_id: str,
    api_key = Depends(get_current_api_key)
):
    """Get specific conversation details."""
    try:
        conversation_storage = get_conversation_storage()
        conversation = conversation_storage.get_conversation(conversation_id)
        
        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"error": "Conversation not found"}
            )
        
        # Convert to response format
        return {
            "id": conversation.id,
            "created_at": conversation.created_at.isoformat(),
            "started_at": conversation.started_at.isoformat() if conversation.started_at else None,
            "finished_at": conversation.finished_at.isoformat() if conversation.finished_at else None,
            "source": conversation.source.value,
            "language": conversation.language,
            "status": conversation.status.value,
            "structured": {
                "title": conversation.structured.title,
                "overview": conversation.structured.overview,
                "category": conversation.structured.category,
                "action_items": conversation.structured.action_items,
                "events": conversation.structured.events,
                "memories": conversation.structured.memories
            },
            "transcript_segments": [
                {
                    "text": seg.text,
                    "speaker": seg.speaker,
                    "timestamp": seg.timestamp,
                    "confidence": seg.confidence,
                    "is_final": seg.is_final
                }
                for seg in conversation.transcript_segments
            ],
            "user_id": conversation.user_id,
            "device_id": conversation.device_id,
            "duration": conversation.duration,
            "geolocation": conversation.geolocation,
            "photos": conversation.photos,
            "apps_results": conversation.apps_results,
            "external_data": conversation.external_data,
            "visibility": conversation.visibility
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error getting conversation", conversation_id=conversation_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "Failed to get conversation"}
        )

@app.post("/v1/conversations/search")
@limiter.limit("5/minute")
async def search_conversations(
    request: Request,
    search_data: dict,
    api_key = Depends(get_current_api_key)
):
    """Search conversations by content."""
    try:
        user_id = search_data.get("user_id")
        query = search_data.get("query", "")
        limit = search_data.get("limit", 10)
        
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"error": "user_id is required"}
            )
        
        if not query.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"error": "query is required"}
            )
        
        conversation_storage = get_conversation_storage()
        
        # Search conversations
        conversations = conversation_storage.search_conversations(
            user_id=user_id,
            query=query,
            limit=limit
        )
        
        # Convert to response format
        conversation_list = []
        for conv in conversations:
            conversation_list.append({
                "id": conv.id,
                "created_at": conv.created_at.isoformat(),
                "title": conv.structured.title,
                "overview": conv.structured.overview,
                "status": conv.status.value,
                "relevance_score": 0.8  # In production, calculate actual relevance
            })
        
        return {
            "conversations": conversation_list,
            "count": len(conversation_list),
            "query": query,
            "user_id": user_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error searching conversations", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "Failed to search conversations"}
        )

# WebSocket endpoint for real-time Omi device integration
@app.websocket("/v4/listen")
async def websocket_endpoint(
    websocket: WebSocket, 
    uid: str = Query(..., description="User ID from Firebase"),
    language: str = Query(default="en", description="Language code"),
    device_type: str = Query(default="omi", description="Device type")
):
    """Real-time WebSocket endpoint for Omi device audio streaming.
    
    Follows Omi documentation for /v4/listen endpoint.
    Supports bidirectional audio streaming and real-time transcription.
    """
    import json
    from websocket_handlers import WebSocketConnection
    from conversation_storage import ConversationSource, TranscriptSegment, ConversationStatus
    
    websocket_manager = get_websocket_manager()
    conversation_storage = get_conversation_storage()
    
    # Validate language and get STT service
    try:
        stt_service = get_stt_service_for_language(language)
        logger.info("STT service selected", language=language, service=stt_service.value)
    except Exception as e:
        logger.error("Invalid language parameter", language=language, error=str(e))
        await websocket.close(code=4003, reason="Invalid language")
        return
    
    # Establish connection
    try:
        connection = await websocket_manager.connect(websocket, uid, language)
    except ValueError as e:
        logger.error("WebSocket connection failed", error=str(e))
        return
    
    # Create conversation for this session
    conversation = conversation_storage.create_conversation(uid, ConversationSource.OMI)
    
    try:
        # Main WebSocket message loop
        while connection.is_connected:
            try:
                # Receive message from client
                message = await websocket.receive_text()
                data = json.loads(message)
                
                message_type = data.get("type")
                
                if message_type == "audio_data":
                    # Handle audio streaming
                    audio_data = data.get("data", "")
                    if audio_data:
                        # Convert base64 to bytes if needed
                        import base64
                        if isinstance(audio_data, str):
                            audio_bytes = base64.b64decode(audio_data)
                        else:
                            audio_bytes = audio_data
                        
                        await websocket_manager.handle_audio_stream(connection, audio_bytes)
                
                elif message_type == "transcript_chunk":
                    # Handle transcript segment
                    segment_data = data.get("data", {})
                    segment = TranscriptSegment(
                        text=segment_data.get("text", ""),
                        speaker=segment_data.get("speaker"),
                        timestamp=segment_data.get("timestamp", 0),
                        confidence=segment_data.get("confidence", 0),
                        is_final=segment_data.get("is_final", True)
                    )
                    
                    conversation_storage.add_transcript_segment(conversation.id, segment)
                    connection.transcript_buffer.append(segment.text)
                    
                    # Send acknowledgment
                    await connection.send_status("transcript_received")
                
                elif message_type == "conversation_end":
                    # End conversation and process
                    conversation_storage.finish_conversation(conversation.id)
                    
                    # Process with AI
                    full_transcript = " ".join(connection.transcript_buffer)
                    if full_transcript.strip():
                        ai_result = extract_tasks_and_summary(full_transcript)
                        
                        # Convert to structured format
                        structured_data = extract_structured_data_from_ai_result(ai_result)
                        conversation_storage.process_conversation(conversation.id, structured_data)
                        
                        # Send final results
                        await connection.websocket.send_text(json.dumps({
                            "type": "conversation_complete",
                            "data": {
                                "conversation_id": conversation.id,
                                "structured": {
                                    "title": structured_data.title,
                                    "overview": structured_data.overview,
                                    "action_items": structured_data.action_items,
                                    "events": structured_data.events,
                                    "memories": structured_data.memories
                                },
                                "tasks": ai_result.get("tasks", []),
                                "summary": ai_result.get("summary", "")
                            }
                        }))
                    
                    await connection.send_status("conversation_processed")
                
                elif message_type == "ping":
                    # Health check
                    await connection.websocket.send_text(json.dumps({
                        "type": "pong",
                        "data": {"timestamp": asyncio.get_event_loop().time()}
                    }))
                
                else:
                    logger.warning("Unknown message type", message_type=message_type)
                    await connection.send_error(f"Unknown message type: {message_type}")
                    
            except WebSocketDisconnect:
                logger.info("WebSocket disconnected by client", connection_id=connection.connection_id)
                break
            except json.JSONDecodeError:
                await connection.send_error("Invalid JSON format")
            except Exception as e:
                logger.error("Error processing WebSocket message", error=str(e))
                await connection.send_error(f"Processing error: {str(e)}")
                
    except WebSocketDisconnect:
        logger.info("WebSocket connection closed", connection_id=connection.connection_id)
    except Exception as e:
        logger.error("WebSocket error", error=str(e))
    finally:
        # Cleanup
        websocket_manager.disconnect(connection.connection_id)
        if conversation.status == ConversationStatus.IN_PROGRESS:
            conversation_storage.finish_conversation(conversation.id)

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    host = os.getenv("HOST", "0.0.0.0")
    logger.info("Starting server", host=host, port=port)
    uvicorn.run("main:app", host=host, port=port, reload=True)