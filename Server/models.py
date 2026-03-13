from pydantic import BaseModel
from typing import List, Optional

class Task(BaseModel):
    task: str
    assigned_to: Optional[str] = None
    deadline: Optional[str] = None

class TranscriptRequest(BaseModel):
    text: str

class SpeakFlowResponse(BaseModel):
    tasks: List[Task]
    summary: str