"""Chat message schemas."""
from typing import Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field
from app.schemas.base import BaseSchema, TimestampSchema, IDSchema


class MessageBase(BaseSchema):
    """Base message fields."""
    content: str
    message_type: str = "text"  # text, voice, image


class MessageCreate(MessageBase):
    """Create new message from user."""
    session_id: Optional[str] = None
    table_id: Optional[int] = None


class MessageResponse(MessageBase, IDSchema, TimestampSchema):
    """Message response."""
    session_id: str
    business_id: int
    sender_type: str  # customer, bot
    intent_detected: Optional[str]
    ai_model_used: Optional[str]
    response_time_ms: Optional[int]
    metadata: Optional[Dict[str, Any]] = {}


class ChatSession(BaseModel):
    """Chat session info."""
    session_id: str
    business_id: int
    table_id: Optional[int]
    created_at: datetime
    last_message_at: datetime
    message_count: int
    status: str = "active"  # active, closed, expired


class ChatRequest(BaseModel):
    """Chat request from user."""
    message: str
    session_id: Optional[str] = None
    table_id: Optional[int] = None
    context: Optional[Dict[str, Any]] = {}


class ChatResponse(BaseModel):
    """Chat response from bot."""
    message: str
    session_id: str
    suggested_actions: Optional[List[str]] = []
    metadata: Optional[Dict[str, Any]] = {}