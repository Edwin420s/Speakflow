from twilio.rest import Client
from config import TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_WHATSAPP_FROM, WHATSAPP_TO

def send_whatsapp_message(message: str) -> str:
    """
    Send a WhatsApp message using Twilio.
    Returns message SID if successful, else error string.
    """
    if not all([TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_WHATSAPP_FROM, WHATSAPP_TO]):
        print("Twilio credentials missing, skipping WhatsApp message.")
        return "Missing credentials"

    client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

    try:
        msg = client.messages.create(
            body=message,
            from_=TWILIO_WHATSAPP_FROM,
            to=WHATSAPP_TO
        )
        return msg.sid
    except Exception as e:
        print(f"Failed to send WhatsApp: {e}")
        return str(e)