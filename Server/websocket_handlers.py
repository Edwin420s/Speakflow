"""
WebSocket handlers for real-time Omi device integration.
Implements the /v4/listen endpoint following Omi documentation standards.
"""

import asyncio
import json
import structlog
from typing import Dict, Any, Optional
from fastapi import WebSocket, WebSocketDisconnect, Query
from enum import Enum
import uuid

logger = structlog.get_logger()

class STTService(str, Enum):
    """Speech-to-Text service providers."""
    DEEPGRAM = "deepgram"
    SONIOX = "soniox"
    SPEECHMATICS = "speechmatics"

class WebSocketConnection:
    """Manages a single WebSocket connection for Omi device."""
    
    def __init__(self, websocket: WebSocket, uid: str, language: str = "en"):
        self.websocket = websocket
        self.uid = uid
        self.language = language
        self.connection_id = str(uuid.uuid4())
        self.is_connected = True
        self.transcript_buffer = []
        self.audio_buffer = []
        
    async def send_transcript(self, transcript: str, is_final: bool = False):
        """Send transcript data to client."""
        message = {
            "type": "transcript",
            "data": {
                "text": transcript,
                "is_final": is_final,
                "timestamp": asyncio.get_event_loop().time(),
                "language": self.language
            }
        }
        await self.websocket.send_text(json.dumps(message))
    
    async def send_error(self, error: str):
        """Send error message to client."""
        message = {
            "type": "error",
            "data": {
                "error": error,
                "timestamp": asyncio.get_event_loop().time()
            }
        }
        await self.websocket.send_text(json.dumps(message))
    
    async def send_status(self, status: str):
        """Send status update to client."""
        message = {
            "type": "status",
            "data": {
                "status": status,
                "timestamp": asyncio.get_event_loop().time()
            }
        }
        await self.websocket.send_text(json.dumps(message))

class OmiWebSocketManager:
    """Manages WebSocket connections for Omi devices."""
    
    def __init__(self):
        self.active_connections: Dict[str, WebSocketConnection] = {}
        
    async def connect(self, websocket: WebSocket, uid: str, language: str = "en") -> WebSocketConnection:
        """Accept and register new WebSocket connection."""
        await websocket.accept()
        
        # Validate user ID (in production, check against Firebase)
        if not uid or not uid.strip():
            await websocket.close(code=4001, reason="Invalid user ID")
            raise ValueError("Invalid user ID")
        
        connection = WebSocketConnection(websocket, uid, language)
        self.active_connections[connection.connection_id] = connection
        
        logger.info("WebSocket connection established", 
                   connection_id=connection.connection_id,
                   uid=uid,
                   language=language)
        
        await connection.send_status("connected")
        return connection
    
    def disconnect(self, connection_id: str):
        """Remove and close WebSocket connection."""
        if connection_id in self.active_connections:
            connection = self.active_connections[connection_id]
            connection.is_connected = False
            del self.active_connections[connection_id]
            logger.info("WebSocket connection closed", connection_id=connection_id)
    
    async def handle_audio_stream(self, connection: WebSocketConnection, audio_data: bytes):
        """Handle incoming audio data from Omi device."""
        try:
            # Add to audio buffer
            connection.audio_buffer.append(audio_data)
            
            # In production, this would:
            # 1. Send to STT service (Deepgram/Soniox/Speechmatics)
            # 2. Process real-time transcription
            # 3. Send results back to client
            
            # For demo, simulate transcription
            if len(connection.audio_buffer) % 10 == 0:  # Every 10 chunks
                demo_transcript = f"Sample transcript chunk {len(connection.audio_buffer)}"
                await connection.send_transcript(demo_transcript, is_final=False)
                
        except Exception as e:
            logger.error("Error handling audio stream", error=str(e))
            await connection.send_error(f"Audio processing error: {str(e)}")
    
    async def process_conversation_end(self, connection: WebSocketConnection):
        """Process conversation when recording ends."""
        try:
            # Combine all transcript chunks
            full_transcript = " ".join(connection.transcript_buffer)
            
            if full_transcript.strip():
                # Send final transcript
                await connection.send_transcript(full_transcript, is_final=True)
                
                # Process with AI (import to avoid circular import)
                from ai_processor import extract_tasks_and_summary
                
                result = extract_tasks_and_summary(full_transcript)
                
                # Send processing results
                message = {
                    "type": "conversation_processed",
                    "data": {
                        "tasks": result.get("tasks", []),
                        "summary": result.get("summary", ""),
                        "timestamp": asyncio.get_event_loop().time()
                    }
                }
                await connection.websocket.send_text(json.dumps(message))
                
                logger.info("Conversation processed successfully",
                           connection_id=connection.connection_id,
                           tasks_count=len(result.get("tasks", [])))
            
        except Exception as e:
            logger.error("Error processing conversation", error=str(e))
            await connection.send_error(f"Conversation processing error: {str(e)}")

# Global WebSocket manager
websocket_manager = OmiWebSocketManager()

def get_websocket_manager() -> OmiWebSocketManager:
    """Get global WebSocket manager instance."""
    return websocket_manager

def get_stt_service_for_language(language: str) -> STTService:
    """Select appropriate STT service based on language."""
    # Omi documentation shows automatic service selection
    service_mapping = {
        "en": STTService.DEEPGRAM,
        "es": STTService.DEEPGRAM,
        "fr": STTService.DEEPGRAM,
        "de": STTService.DEEPGRAM,
        # Add more language mappings as needed
    }
    return service_mapping.get(language, STTService.DEEPGRAM)
