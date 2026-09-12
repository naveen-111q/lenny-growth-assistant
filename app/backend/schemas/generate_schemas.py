from typing import List, Optional
from pydantic import BaseModel, Field
from app.backend.schemas.chat_schemas import SourceCitation


class Ship30Request(BaseModel):
    session_id: str = Field(..., description="UUID of the chat session to ground the essay upon")
    topic: Optional[str] = Field(default=None, description="Optional custom angle or topic for the essay")
    provider: Optional[str] = Field(default=None, description="Optional override provider")
    model: Optional[str] = Field(default=None, description="Optional override model")


class Ship30Response(BaseModel):
    session_id: str
    title: str
    essay: str
    word_count: int
    sources: List[SourceCitation] = []
    provider: str
    model: str


class ArtifactRequest(BaseModel):
    session_id: str = Field(..., description="UUID of the chat session")
    artifact_type: str = Field(..., description="'markdown' or 'html'")
    prompt: str = Field(..., min_length=3, max_length=5000, description="Instruction for what artifact to produce")
    provider: Optional[str] = Field(default=None, description="Optional override provider")
    model: Optional[str] = Field(default=None, description="Optional override model")


class ArtifactResponse(BaseModel):
    session_id: str
    artifact_type: str
    title: str
    content: str
    sources: List[SourceCitation] = []
    provider: str
    model: str
