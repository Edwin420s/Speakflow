"""
Conversation storage and memory system following Omi documentation.
Implements conversation storage, vector search, and memory extraction.
"""

import structlog
from typing import Dict, Any, List, Optional
from datetime import datetime
from dataclasses import dataclass
from enum import Enum
import json

logger = structlog.get_logger()

class ConversationSource(str, Enum):
    """Sources of conversation data."""
    OMI = "omi"
    PHONE = "phone"
    DESKTOP = "desktop"
    OPENGLASS = "openglass"
    WEB = "web"

class ConversationStatus(str, Enum):
    """Conversation processing status."""
    IN_PROGRESS = "in_progress"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

@dataclass
class TranscriptSegment:
    """Represents a segment of transcribed conversation."""
    text: str
    speaker: Optional[str] = None
    timestamp: float = 0.0
    confidence: float = 0.0
    is_final: bool = True

@dataclass
class StructuredData:
    """Structured data extracted from conversation."""
    title: str
    overview: str
    category: str
    action_items: List[Dict[str, Any]]
    events: List[Dict[str, Any]]
    memories: List[Dict[str, Any]]

@dataclass
class Conversation:
    """Complete conversation data structure following Omi docs."""
    id: str
    created_at: datetime
    started_at: Optional[datetime]
    finished_at: Optional[datetime]
    
    source: ConversationSource
    language: str
    status: ConversationStatus
    
    structured: StructuredData
    transcript_segments: List[TranscriptSegment]
    
    user_id: str
    device_id: Optional[str]
    
    # Metadata
    duration: Optional[float]
    geolocation: Optional[Dict[str, Any]]
    photos: List[Dict[str, Any]]
    
    # Processing metadata
    apps_results: List[Dict[str, Any]]
    external_data: Optional[Dict[str, Any]]
    
    # Flags
    discarded: bool = False
    deleted: bool = False
    visibility: str = "private"  # private, shared, public

class ConversationStorage:
    """Manages conversation storage and retrieval following Omi patterns."""
    
    def __init__(self):
        self.conversations: Dict[str, Conversation] = {}
        self.user_memories: Dict[str, List[Dict[str, Any]]] = {}
        
    def create_conversation(self, user_id: str, source: ConversationSource = ConversationSource.OMI) -> Conversation:
        """Create a new conversation."""
        conversation_id = f"conv_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{user_id[:8]}"
        
        now = datetime.utcnow()
        conversation = Conversation(
            id=conversation_id,
            created_at=now,
            started_at=now,
            finished_at=None,
            source=source,
            language="en",
            status=ConversationStatus.IN_PROGRESS,
            structured=StructuredData(
                title="",
                overview="",
                category="",
                action_items=[],
                events=[],
                memories=[]
            ),
            transcript_segments=[],
            user_id=user_id,
            device_id=None,
            duration=None,
            geolocation=None,
            photos=[],
            apps_results=[],
            external_data=None
        )
        
        self.conversations[conversation_id] = conversation
        logger.info("Conversation created", conversation_id=conversation_id, user_id=user_id)
        return conversation
    
    def add_transcript_segment(self, conversation_id: str, segment: TranscriptSegment):
        """Add a transcript segment to conversation."""
        if conversation_id not in self.conversations:
            raise ValueError(f"Conversation {conversation_id} not found")
        
        conversation = self.conversations[conversation_id]
        conversation.transcript_segments.append(segment)
        
        logger.debug("Transcript segment added", 
                    conversation_id=conversation_id,
                    segment_length=len(segment.text))
    
    def finish_conversation(self, conversation_id: str) -> Conversation:
        """Mark conversation as finished and trigger processing."""
        if conversation_id not in self.conversations:
            raise ValueError(f"Conversation {conversation_id} not found")
        
        conversation = self.conversations[conversation_id]
        conversation.finished_at = datetime.utcnow()
        conversation.status = ConversationStatus.PROCESSING
        
        # Calculate duration
        if conversation.started_at and conversation.finished_at:
            conversation.duration = (conversation.finished_at - conversation.started_at).total_seconds()
        
        logger.info("Conversation finished", 
                   conversation_id=conversation_id,
                   duration=conversation.duration)
        
        return conversation
    
    def process_conversation(self, conversation_id: str, structured_data: StructuredData):
        """Store processed structured data for conversation."""
        if conversation_id not in self.conversations:
            raise ValueError(f"Conversation {conversation_id} not found")
        
        conversation = self.conversations[conversation_id]
        conversation.structured = structured_data
        conversation.status = ConversationStatus.COMPLETED
        
        # Extract and store memories
        if structured_data.memories:
            self._store_user_memories(conversation.user_id, structured_data.memories)
        
        logger.info("Conversation processed", 
                   conversation_id=conversation_id,
                   memories_count=len(structured_data.memories),
                   action_items_count=len(structured_data.action_items))
    
    def get_conversation(self, conversation_id: str) -> Optional[Conversation]:
        """Retrieve a specific conversation."""
        return self.conversations.get(conversation_id)
    
    def get_user_conversations(self, user_id: str, limit: int = 50, include_discarded: bool = False) -> List[Conversation]:
        """Get conversations for a user."""
        conversations = [
            conv for conv in self.conversations.values()
            if conv.user_id == user_id and (include_discarded or not conv.discarded)
        ]
        
        # Sort by created_at descending
        conversations.sort(key=lambda x: x.created_at, reverse=True)
        return conversations[:limit]
    
    def search_conversations(self, user_id: str, query: str, limit: int = 10) -> List[Conversation]:
        """Search conversations by content (simplified vector search)."""
        conversations = self.get_user_conversations(user_id, include_discarded=False)
        
        # Simple text-based search (in production, use proper vector search like Pinecone)
        query_lower = query.lower()
        matching_conversations = []
        
        for conv in conversations:
            # Search in transcript
            transcript_text = " ".join([seg.text for seg in conv.transcript_segments]).lower()
            
            # Search in structured data
            structured_text = f"{conv.structured.title} {conv.structured.overview}".lower()
            
            # Search in memories
            memories_text = " ".join([mem.get("fact", "") for mem in conv.structured.memories]).lower()
            
            combined_text = f"{transcript_text} {structured_text} {memories_text}"
            
            if query_lower in combined_text:
                matching_conversations.append(conv)
        
        return matching_conversations[:limit]
    
    def get_user_memories(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all stored memories for a user."""
        return self.user_memories.get(user_id, [])
    
    def _store_user_memories(self, user_id: str, memories: List[Dict[str, Any]]):
        """Store memories for a user."""
        if user_id not in self.user_memories:
            self.user_memories[user_id] = []
        
        # Add timestamp to memories
        for memory in memories:
            memory["stored_at"] = datetime.utcnow().isoformat()
        
        self.user_memories[user_id].extend(memories)
        
        logger.info("User memories stored", 
                   user_id=user_id,
                   memories_count=len(memories),
                   total_memories=len(self.user_memories[user_id]))

# Global storage instance
_conversation_storage = None

def get_conversation_storage() -> ConversationStorage:
    """Get global conversation storage instance."""
    global _conversation_storage
    if _conversation_storage is None:
        _conversation_storage = ConversationStorage()
    return _conversation_storage

def extract_structured_data_from_ai_result(ai_result: Dict[str, Any]) -> StructuredData:
    """Convert AI processing result to structured data format."""
    tasks = ai_result.get("tasks", [])
    summary = ai_result.get("summary", "")
    
    # Convert tasks to action items
    action_items = []
    for task in tasks:
        action_items.append({
            "type": "task",
            "description": task.get("task", ""),
            "assigned_to": task.get("assigned_to"),
            "priority": task.get("priority", "medium"),
            "deadline": task.get("deadline"),
            "status": task.get("status", "pending")
        })
    
    return StructuredData(
        title=_generate_title_from_transcript(summary),
        overview=summary,
        category="work",  # Could be determined by AI
        action_items=action_items,
        events=[],  # Could be extracted by AI
        memories=[]  # Could be extracted by AI
    )

def _generate_title_from_transcript(summary: str) -> str:
    """Generate a title from conversation summary."""
    if not summary:
        return "New Conversation"
    
    # Take first 50 characters and add ellipsis if needed
    title = summary.strip()[:50]
    if len(summary) > 50:
        title += "..."
    
    return title
