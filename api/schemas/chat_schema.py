from pydantic import BaseModel
from typing import List, Optional, Dict, Any


class Message(BaseModel):
    text: str
    # audio: Optional[str] = None  # base64 encoded
    # lipsync: Optional[Dict[str, Any]] = None
    # facialExpression: str
    # animation: str


class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None
    language: Optional[str] = "fa"  # Default to Persian, can be "fa" or "en"


class ChatResponse(BaseModel):
    messages: List[Message]
    session_id: Optional[str] = None
