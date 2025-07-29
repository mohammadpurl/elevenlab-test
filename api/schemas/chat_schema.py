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


class ChatResponse(BaseModel):
    messages: List[Message]
