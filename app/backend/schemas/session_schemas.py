from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field, ConfigDict


class SessionCreateRequest(BaseModel):
    title: Optional[str] = Field(default="New Conversation", description="Title of the session")
    provider: Optional[str] = Field(default=None, description="Preferred LLM provider ('ollama' or 'openrouter')")
    model: Optional[str] = Field(default=None, description="Preferred model name")


class SessionResponse(BaseModel):
    id: str
    title: str
    provider: str
    model: str
    created_at: datetime
    updated_at: datetime
    message_count: int = 0

    model_config = ConfigDict(from_attributes=True)


class MessageItem(BaseModel):
    id: str
    role: str
    content: str
    sources: Optional[List[dict]] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class SessionDetailResponse(BaseModel):
    id: str
    title: str
    provider: str
    model: str
    created_at: datetime
    updated_at: datetime
    messages: List[MessageItem] = []

    model_config = ConfigDict(from_attributes=True)
