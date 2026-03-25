from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum
import re

class ActivityType(str, Enum):
    """Types of activities in the system."""
    TASK_CREATED = "task_created"
    TASK_COMPLETED = "task_completed"
    TASK_ASSIGNED = "task_assigned"
    TRANSCRIPT_PROCESSED = "transcript_processed"
    TRELLO_CARD_CREATED = "trello_card_created"
    WHATSAPP_SENT = "whatsapp_sent"
    OMI_DEVICE_CONNECTED = "omi_device_connected"
    OMI_CONVERSATION_PROCESSED = "omi_conversation_processed"
    AI_PROCESSING_STARTED = "ai_processing_started"
    AI_PROCESSING_COMPLETED = "ai_processing_completed"

class Priority(str, Enum):
    """Task priority levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"

class TaskStatus(str, Enum):
    """Task status values."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

class Task(BaseModel):
    """Represents an extracted task from a conversation."""
    task: str = Field(..., description="Description of the task to be completed", min_length=1, max_length=500)
    assigned_to: Optional[str] = Field(None, description="Person responsible for the task", max_length=100)
    deadline: Optional[str] = Field(None, description="Deadline for the task", max_length=50)
    priority: Priority = Field(Priority.MEDIUM, description="Task priority level")
    status: TaskStatus = Field(TaskStatus.PENDING, description="Current task status")
    tags: List[str] = Field(default=[], description="Tags associated with the task")
    estimated_time: Optional[str] = Field(None, description="Estimated time to complete", max_length=50)
    context: Optional[str] = Field(None, description="Additional context for the task", max_length=1000)
    
    @validator('task')
    def validate_task(cls, v):
        if not v or not v.strip():
            raise ValueError('Task description cannot be empty')
        return v.strip()
    
    @validator('assigned_to')
    def validate_assigned_to(cls, v):
        if v is not None:
            return v.strip() if v.strip() else None
        return v
    
    @validator('deadline')
    def validate_deadline(cls, v):
        if v is not None:
            v = v.strip()
            # Basic date format validation (can be enhanced)
            if not v:
                return None
        return v

class TranscriptRequest(BaseModel):
    """Request model for transcript analysis."""
    text: str = Field(..., description="The conversation transcript text to analyze", min_length=10, max_length=10000)
    
    @validator('text')
    def validate_text(cls, v):
        if not v or not v.strip():
            raise ValueError('Transcript text cannot be empty')
        if len(v.strip()) < 10:
            raise ValueError('Transcript text must be at least 10 characters long')
        return v.strip()

class Activity(BaseModel):
    """Represents an activity/event in the system."""
    id: Optional[int] = Field(None, description="Activity ID")
    type: ActivityType = Field(..., description="Type of activity")
    title: str = Field(..., description="Activity title", min_length=1, max_length=200)
    description: str = Field(..., description="Activity description", min_length=1, max_length=1000)
    metadata: Dict[str, Any] = Field(default={}, description="Additional activity metadata")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="When the activity occurred")
    user_id: Optional[str] = Field(None, description="User who performed the activity")
    session_id: Optional[str] = Field(None, description="Session identifier")
    
class TimelineEvent(BaseModel):
    """Represents a timeline event for visual progress tracking."""
    id: Optional[int] = Field(None, description="Timeline event ID")
    title: str = Field(..., description="Event title", min_length=1, max_length=200)
    description: str = Field(..., description="Event description", min_length=1, max_length=500)
    event_type: ActivityType = Field(..., description="Type of event")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="When the event occurred")
    completed: bool = Field(False, description="Whether the event is completed")
    progress_percentage: float = Field(0.0, description="Progress percentage (0-100)", ge=0, le=100)
    related_task_id: Optional[int] = Field(None, description="Related task ID if applicable")
    metadata: Dict[str, Any] = Field(default={}, description="Additional event metadata")

class ActivityFeed(BaseModel):
    """Response model for activity feed endpoint."""
    activities: List[Activity] = Field(default=[], description="List of activities")
    total_count: int = Field(..., description="Total number of activities")
    page: int = Field(1, description="Current page number")
    page_size: int = Field(20, description="Number of activities per page")
    has_more: bool = Field(False, description="Whether there are more pages")

class Timeline(BaseModel):
    """Response model for timeline endpoint."""
    events: List[TimelineEvent] = Field(default=[], description="List of timeline events")
    total_events: int = Field(..., description="Total number of events")
    completion_percentage: float = Field(0.0, description="Overall completion percentage", ge=0, le=100)
    start_date: Optional[datetime] = Field(None, description="Timeline start date")
    end_date: Optional[datetime] = Field(None, description="Timeline end date")
    active_tasks: int = Field(0, description="Number of active tasks")
    completed_tasks: int = Field(0, description="Number of completed tasks")

class SpeakFlowResponse(BaseModel):
    """Response model containing extracted tasks and summary."""
    tasks: List[Task] = Field(default=[], description="List of extracted tasks")
    summary: str = Field(..., description="Meeting summary", min_length=1, max_length=1000)
    processing_time_ms: Optional[int] = Field(None, description="Processing time in milliseconds")
    confidence_score: Optional[float] = Field(None, description="AI confidence score", ge=0, le=1)
    activity_id: Optional[int] = Field(None, description="Associated activity ID")
    
    @validator('summary')
    def validate_summary(cls, v):
        if not v or not v.strip():
            raise ValueError('Summary cannot be empty')
        return v.strip()

class HealthCheck(BaseModel):
    """Health check response model."""
    status: str = Field(..., description="Service status")
    services: dict = Field(..., description="Status of external services")
    timestamp: float = Field(..., description="Unix timestamp")

class TrelloCardResponse(BaseModel):
    """Response model for Trello card creation."""
    id: str = Field(..., description="Card ID")
    name: str = Field(..., description="Card name")
    url: str = Field(..., description="Card URL")
    success: bool = Field(default=True, description="Success status")

class WhatsAppResponse(BaseModel):
    """Response model for WhatsApp message sending."""
    message_sid: Optional[str] = Field(None, description="Message SID if successful")
    status: str = Field(..., description="Message status")
    error: Optional[str] = Field(None, description="Error message if failed")

class ErrorResponse(BaseModel):
    """Standard error response model."""
    error: str = Field(..., description="Error message")
    details: Optional[dict] = Field(None, description="Additional error details")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Error timestamp")