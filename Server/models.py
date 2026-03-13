from pydantic import BaseModel, Field, validator
from typing import List, Optional
from datetime import datetime
import re

class Task(BaseModel):
    """Represents an extracted task from a conversation."""
    task: str = Field(..., description="Description of the task to be completed", min_length=1, max_length=500)
    assigned_to: Optional[str] = Field(None, description="Person responsible for the task", max_length=100)
    deadline: Optional[str] = Field(None, description="Deadline for the task", max_length=50)
    
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

class SpeakFlowResponse(BaseModel):
    """Response model containing extracted tasks and summary."""
    tasks: List[Task] = Field(default=[], description="List of extracted tasks")
    summary: str = Field(..., description="Meeting summary", min_length=1, max_length=1000)
    
    @validator('summary')
    def validate_summary(cls, v):
        if not v or not v.strip():
            raise ValueError('Summary cannot be empty')
        return v.strip()

class ErrorResponse(BaseModel):
    """Standard error response model."""
    error: str = Field(..., description="Error message")
    details: Optional[dict] = Field(None, description="Additional error details")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Error timestamp")

class HealthCheck(BaseModel):
    """Health check response model."""
    status: str = Field(..., description="Service status")
    services: dict = Field(..., description="Status of external services")
    timestamp: float = Field(..., description="Unix timestamp")

class TrelloCardResponse(BaseModel):
    """Response model for Trello card creation."""
    id: str = Field(..., description="Card ID")
    name: str = Field(..., description="Card name")
    url: Optional[str] = Field(None, description="Card URL")
    error: Optional[str] = Field(None, description="Error message if creation failed")

class WhatsAppResponse(BaseModel):
    """Response model for WhatsApp message sending."""
    message_sid: Optional[str] = Field(None, description="Message SID if successful")
    status: str = Field(..., description="Message status")
    error: Optional[str] = Field(None, description="Error message if failed")