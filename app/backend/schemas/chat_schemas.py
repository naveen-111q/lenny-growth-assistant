from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field


class SourceCitation(BaseModel):
    episode_title: str
    guest: str
    guest_role: Optional[str] = None
    url: Optional[str] = None
    chunk_index: int = 0
    content_snippet: str
    relevance_score: float = 0.0


class ChatRequest(BaseModel):
    session_id: str = Field(..., description="UUID of the chat session")
    message: str = Field(..., min_length=1, max_length=10000, description="User prompt or question")
    provider: Optional[str] = Field(default=None, description="Optional override provider ('ollama' or 'openrouter')")
    model: Optional[str] = Field(default=None, description="Optional override model name")


class ChatResponse(BaseModel):
    session_id: str
    user_message: str
    assistant_message: str
    sources: List[SourceCitation] = []
    provider: str
    model: str
    latency_ms: float = 0.0
