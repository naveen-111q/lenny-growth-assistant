import uuid
from datetime import datetime
from typing import List, Optional
from fastapi import HTTPException
from sqlalchemy.orm import Session
from app.backend.models.db_models import ChatSession, ChatMessage
from app.backend.schemas.session_schemas import (
    SessionCreateRequest,
    SessionResponse,
    SessionDetailResponse,
    MessageItem
)
from app.config import settings


class SessionService:
    @staticmethod
    def create_session(db: Session, request: Optional[SessionCreateRequest] = None) -> SessionResponse:
        """
        Creates a new isolated chat session.
        """
        title = request.title if request and request.title else "New Conversation"
        provider = request.provider if request and request.provider else settings.llm_provider
        model = request.model if request and request.model else (
            settings.ollama_model if provider == "ollama" else settings.openrouter_model
        )

        session_id = str(uuid.uuid4())
        session = ChatSession(
            id=session_id,
            title=title,
            provider=provider,
            model=model,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        db.add(session)
        db.commit()
        db.refresh(session)
        return SessionResponse(
            id=session.id,
            title=session.title,
            provider=session.provider,
            model=session.model,
            created_at=session.created_at,
            updated_at=session.updated_at,
            message_count=0
        )

    @staticmethod
    def get_session(db: Session, session_id: str) -> SessionDetailResponse:
        """
        Retrieves a session and its ordered messages.
        """
        session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
        if not session:
            raise HTTPException(status_code=404, detail=f"Session '{session_id}' not found.")

        messages = [
            MessageItem(
                id=msg.id,
                role=msg.role,
                content=msg.content,
                sources=msg.sources or [],
                created_at=msg.created_at
            )
            for msg in session.messages
        ]

        return SessionDetailResponse(
            id=session.id,
            title=session.title,
            provider=session.provider,
            model=session.model,
            created_at=session.created_at,
            updated_at=session.updated_at,
            messages=messages
        )

    @staticmethod
    def list_sessions(db: Session, limit: int = 50) -> List[SessionResponse]:
        """
        Lists all sessions sorted by last updated time.
        """
        sessions = db.query(ChatSession).order_by(ChatSession.updated_at.desc()).limit(limit).all()
        return [
            SessionResponse(
                id=s.id,
                title=s.title,
                provider=s.provider,
                model=s.model,
                created_at=s.created_at,
                updated_at=s.updated_at,
                message_count=len(s.messages)
            )
            for s in sessions
        ]

    @staticmethod
    def add_message(
        db: Session,
        session_id: str,
        role: str,
        content: str,
        sources: Optional[List[dict]] = None
    ) -> ChatMessage:
        """
        Adds a message to a session and updates the session's updated_at timestamp.
        """
        session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
        if not session:
            raise HTTPException(status_code=404, detail=f"Session '{session_id}' not found.")

        msg = ChatMessage(
            id=str(uuid.uuid4()),
            session_id=session_id,
            role=role,
            content=content,
            sources=sources or [],
            created_at=datetime.utcnow()
        )
        session.updated_at = datetime.utcnow()
        
        # If title is default and user sent first message, generate a brief title from the question
        if role == "user" and session.title == "New Conversation":
            first_line = content.strip().split("\n")[0][:45]
            if first_line:
                session.title = first_line + ("..." if len(content) > 45 else "")

        db.add(msg)
        db.commit()
        db.refresh(msg)
        return msg
