from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException
import structlog
from typing import Optional
from models import WhatsAppResponse

from config import (
    TWILIO_ACCOUNT_SID, 
    TWILIO_AUTH_TOKEN, 
    TWILIO_WHATSAPP_FROM, 
    WHATSAPP_TO
)

logger = structlog.get_logger()

def validate_twilio_credentials() -> bool:
    """Validate that required Twilio credentials are present."""
    missing = []
    if not TWILIO_ACCOUNT_SID:
        missing.append("TWILIO_ACCOUNT_SID")
    if not TWILIO_AUTH_TOKEN:
        missing.append("TWILIO_AUTH_TOKEN")
    if not TWILIO_WHATSAPP_FROM:
        missing.append("TWILIO_WHATSAPP_FROM")
    if not WHATSAPP_TO:
        missing.append("WHATSAPP_TO")
    
    if missing:
        logger.error("Missing Twilio credentials", missing=missing)
        return False
    return True

def send_whatsapp_message(message: str) -> WhatsAppResponse:
    """
    Send a WhatsApp message using Twilio.
    
    Args:
        message: The message content to send
        
    Returns:
        WhatsAppResponse object with send result
    """
    if not validate_twilio_credentials():
        logger.warning("Twilio credentials missing, skipping WhatsApp message")
        return WhatsAppResponse(
            message_sid=None,
            status="failed",
            error="Twilio credentials not configured"
        )
    
    if not message or not message.strip():
        logger.warning("Empty message provided, skipping WhatsApp send")
        return WhatsAppResponse(
            message_sid=None,
            status="failed",
            error="Message cannot be empty"
        )
    
    # Clean up message
    message = message.strip()
    if len(message) > 1600:  # WhatsApp message limit
        message = message[:1597] + "..."
        logger.info("Message truncated to fit WhatsApp limit", original_length=len(message))
    
    try:
        client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
        
        logger.info("Sending WhatsApp message", 
                   from_number=TWILIO_WHATSAPP_FROM,
                   to_number=WHATSAPP_TO,
                   message_length=len(message))
        
        msg = client.messages.create(
            body=message,
            from_=TWILIO_WHATSAPP_FROM,
            to=WHATSAPP_TO
        )
        
        logger.info("WhatsApp message sent successfully", 
                   message_sid=msg.sid,
                   status=msg.status)
        
        return WhatsAppResponse(
            message_sid=msg.sid,
            status=msg.status,
            error=None
        )
        
    except TwilioRestException as e:
        error_code = getattr(e, 'code', 'Unknown')
        error_msg = f"Twilio API error: {str(e)} (Code: {error_code})"
        logger.error("Twilio API error", error=str(e), code=error_code)
        
        return WhatsAppResponse(
            message_sid=None,
            status="failed",
            error=error_msg
        )
        
    except Exception as e:
        logger.error("Unexpected error sending WhatsApp message", error=str(e))
        return WhatsAppResponse(
            message_sid=None,
            status="failed",
            error=f"Unexpected error: {str(e)}"
        )

def test_twilio_connection() -> bool:
    """
    Test connection to Twilio API.
    
    Returns:
        True if connection is successful, False otherwise
    """
    if not validate_twilio_credentials():
        return False
    
    try:
        client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
        
        # Test by fetching account info
        account = client.api.accounts(TWILIO_ACCOUNT_SID).fetch()
        
        logger.info("Twilio connection test successful", 
                   account_sid=account.sid,
                   account_status=account.status)
        
        return True
        
    except TwilioRestException as e:
        logger.error("Twilio connection test failed", error=str(e))
        return False
        
    except Exception as e:
        logger.error("Unexpected error during Twilio connection test", error=str(e))
        return False

def format_whatsapp_summary(summary: str, tasks_count: int) -> str:
    """
    Format summary and task count for WhatsApp message.
    
    Args:
        summary: Meeting summary text
        tasks_count: Number of tasks extracted
        
    Returns:
        Formatted message string
    """
    emoji_tasks = "📋" if tasks_count > 0 else "✅"
    emoji_summary = "📝"
    
    message = f"{emoji_summary} *Meeting Summary*\n\n{summary}\n\n"
    
    if tasks_count > 0:
        message += f"{emoji_tasks} *{tasks_count} task(s) extracted and added to Trello*"
    else:
        message += f"{emoji_tasks} *No action items identified*"
    
    return message