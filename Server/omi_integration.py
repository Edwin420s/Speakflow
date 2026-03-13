"""
Omi Device Integration Module
Connects SpeakFlow with Omi AI wearable for real-time conversation processing.
"""

import structlog
import time
from typing import Dict, Any, Optional
from models import TranscriptRequest

logger = structlog.get_logger()

class OmiDeviceIntegration:
    """
    Integration layer for Omi AI wearable device.
    Handles real-time conversation streaming and processing.
    """
    
    def __init__(self, device_config: Optional[Dict] = None):
        """
        Initialize Omi device integration.
        
        Args:
            device_config: Configuration for Omi device connection
        """
        self.device_config = device_config or {}
        self.is_connected = False
        self.conversation_buffer = []
        self.processing_enabled = False
        
    def simulate_omi_connection(self) -> bool:
        """
        Simulate connection to Omi device for demo purposes.
        In production, this would connect to actual Omi device via Bluetooth/WiFi.
        """
        try:
            logger.info("Simulating Omi device connection...")
            # In real implementation, this would:
            # 1. Scan for Omi devices via Bluetooth
            # 2. Establish connection to device
            # 3. Authenticate with device
            # 4. Start audio stream
            
            self.is_connected = True
            logger.info("Omi device connected successfully", device_id="OMI-DEMO-001")
            return True
            
        except Exception as e:
            logger.error("Failed to connect to Omi device", error=str(e))
            return False
    
    def start_real_time_processing(self) -> bool:
        """
        Start real-time conversation processing from Omi device.
        """
        if not self.is_connected:
            logger.error("Omi device not connected")
            return False
        
        try:
            self.processing_enabled = True
            logger.info("Started real-time conversation processing")
            return True
            
        except Exception as e:
            logger.error("Failed to start real-time processing", error=str(e))
            return False
    
    def process_conversation_chunk(self, audio_chunk: bytes, transcript_chunk: str) -> Dict[str, Any]:
        """
        Process a chunk of conversation from Omi device.
        
        Args:
            audio_chunk: Raw audio data from Omi device
            transcript_chunk: Transcribed text from audio chunk
            
        Returns:
            Processing result with tasks and summary
        """
        if not self.processing_enabled:
            return {"error": "Real-time processing not enabled"}
        
        try:
            # Add transcript chunk to buffer
            self.conversation_buffer.append(transcript_chunk)
            
            # Process accumulated conversation
            full_transcript = " ".join(self.conversation_buffer)
            
            # Import here to avoid circular imports
            from ai_processor import extract_tasks_and_summary
            
            result = extract_tasks_and_summary(full_transcript)
            
            logger.info("Processed conversation chunk", 
                       chunk_length=len(transcript_chunk),
                       total_buffer_length=len(full_transcript),
                       tasks_found=len(result.get("tasks", [])))
            
            return result
            
        except Exception as e:
            logger.error("Error processing conversation chunk", error=str(e))
            return {"error": str(e), "tasks": [], "summary": "Processing error"}
    
    def get_demo_conversation_stream(self) -> str:
        """
        Get simulated conversation stream for demo purposes.
        This simulates real-time transcription from Omi device.
        """
        demo_conversations = [
            "Edwin: Alright team, let's discuss our fintech app for the Kenyan market.",
            "Sarah: I'll handle the UI design for the mobile app.",
            "John: I should contact KCB and Equity Bank about partnership discussions.",
            "Mary: We need to finalize the API documentation for the developers.",
            "Edwin: Sure, I'll complete the API docs by Friday.",
            "Sarah: Don't forget we need to test the app on Safaricom's network.",
            "Mary: Right, I'll coordinate with the Safaricom developer team."
        ]
        
        for sentence in demo_conversations:
            yield sentence
    
    def create_omi_webhook_payload(self, transcript: str, device_id: str = "OMI-DEMO-001") -> TranscriptRequest:
        """
        Create a webhook payload as if it came from Omi device.
        
        Args:
            transcript: The conversation transcript
            device_id: Omi device identifier
            
        Returns:
            TranscriptRequest object
        """
        return TranscriptRequest(
            text=transcript,
            source="omi_device",
            device_id=device_id,
            timestamp=int(time.time())
        )
    
    def disconnect_device(self):
        """Disconnect from Omi device."""
        try:
            self.is_connected = False
            self.processing_enabled = False
            self.conversation_buffer.clear()
            logger.info("Omi device disconnected")
            
        except Exception as e:
            logger.error("Error disconnecting Omi device", error=str(e))

# Global Omi integration instance
_omi_integration = None

def get_omi_integration() -> OmiDeviceIntegration:
    """Get or create global Omi integration instance."""
    global _omi_integration
    if _omi_integration is None:
        _omi_integration = OmiDeviceIntegration()
    return _omi_integration

def simulate_omi_webhook(transcript: str, device_id: str = "OMI-DEMO-001") -> Dict[str, Any]:
    """
    Simulate a webhook call from Omi device.
    
    Args:
        transcript: Conversation transcript from Omi device
        device_id: Omi device identifier
        
    Returns:
        Webhook payload data
    """
    import time
    
    return {
        "event": "conversation_processed",
        "device_id": device_id,
        "timestamp": int(time.time()),
        "data": {
            "transcript": transcript,
            "source": "omi_ai_wearable",
            "confidence": 0.95,
            "language": "en"
        }
    }
