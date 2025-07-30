from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class ChatMessage(BaseModel):
    message: str
    language: Optional[str] = None
    session_id: Optional[str] = None

class ChatResponse(BaseModel):
    response: str
    debabelized_text: str
    response_language: Optional[str] = None
    session_id: str

class TTSRequest(BaseModel):
    text: str
    language: Optional[str] = None
    voice: Optional[str] = None

class STTResponse(BaseModel):
    text: str
    language: Optional[str] = None
    confidence: Optional[float] = None

class ClearConversationRequest(BaseModel):
    session_id: Optional[str] = None

class SessionData(BaseModel):
    conversation_history: List[dict]
    created_at: datetime
    last_accessed: datetime