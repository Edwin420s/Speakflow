import os
import structlog
import time
import uvicorn
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Request, status, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from pydantic import ValidationError

from models import TranscriptRequest, SpeakFlowResponse, ErrorResponse
from ai_processor import extract_tasks_and_summary
from trello_integration import create_trello_cards
from whatsapp_integration import send_whatsapp_message, format_whatsapp_summary
from config import WHATSAPP_ENABLED, TRELLO_ENABLED
from database import init_database, get_database
from auth import get_current_api_key, log_api_usage, AuthManager

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
        
        # 1. AI processing
        result = extract_tasks_and_summary(transcript_request.text)
        
        # 2. Optional: create Trello cards
        trello_results = []
        if TRELLO_ENABLED and result["tasks"]:
            try:
                trello_results = create_trello_cards(result["tasks"])
                logger.info("Trello cards created", count=len(trello_results))
            except Exception as e:
                logger.error("Failed to create Trello cards", error=str(e))
        
        # 3. Optional: send WhatsApp summary
        if WHATSAPP_ENABLED and result["summary"]:
            try:
                formatted_message = format_whatsapp_summary(result["summary"], len(result["tasks"]))
                whatsapp_result = send_whatsapp_message(formatted_message)
                logger.info("WhatsApp message sent", result=whatsapp_result.status)
            except Exception as e:
                logger.error("Failed to send WhatsApp message", error=str(e))
        
        logger.info(
            "Successfully processed transcript",
            tasks_count=len(result["tasks"]),
            summary_length=len(result["summary"])
        )
        
        return SpeakFlowResponse(
            tasks=result["tasks"],
            summary=result["summary"]
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

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    host = os.getenv("HOST", "0.0.0.0")
    logger.info("Starting server", host=host, port=port)
    uvicorn.run("main:app", host=host, port=port, reload=True)