from pydantic import BaseModel, ConfigDict
from typing import Optional, List, Any, Dict
from datetime import datetime


class ChatRequest(BaseModel):
    session_id: Optional[str] = None
    message: str
    language: Optional[str] = "en"


class ChatResponse(BaseModel):
    session_id: str
    message: str
    quick_replies: Optional[List[str]] = None
    actions_taken: Optional[List[Dict[str, Any]]] = None


class MessageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    session_id: str
    role: str
    content: Optional[str] = None
    tool_name: Optional[str] = None
    created_at: Optional[datetime] = None


class SessionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    session_id: str
    use_case: Optional[str] = None
    language: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    messages: Optional[List[MessageResponse]] = None
