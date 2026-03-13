import os
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from models import TranscriptRequest, SpeakFlowResponse
from ai_processor import extract_tasks_and_summary
from trello_integration import create_trello_cards
from whatsapp_integration import send_whatsapp_message
from config import WHATSAPP_ENABLED, TRELLO_ENABLED

app = FastAPI(title="SpeakFlow API", version="1.0.0")

# Allow CORS for frontend (adjust origins in production)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {"message": "SpeakFlow backend is running"}

@app.post("/api/analyze", response_model=SpeakFlowResponse)
async def analyze_conversation(request: TranscriptRequest):
    """
    Accept a conversation transcript, extract tasks/summary,
    and optionally push to Trello and WhatsApp.
    """
    try:
        # 1. AI processing
        result = extract_tasks_and_summary(request.text)

        # 2. Optional: create Trello cards
        if TRELLO_ENABLED:
            create_trello_cards(result["tasks"])

        # 3. Optional: send WhatsApp summary
        if WHATSAPP_ENABLED:
            send_whatsapp_message(result["summary"])

        return SpeakFlowResponse(
            tasks=result["tasks"],
            summary=result["summary"]
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)