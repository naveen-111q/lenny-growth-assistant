from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.backend.database.session import get_db
from app.backend.services.session_service import SessionService
from app.backend.schemas.session_schemas import (
    SessionCreateRequest,
    SessionResponse,
    SessionDetailResponse
)

router = APIRouter(prefix="/sessions", tags=["Sessions"])


@router.post("", response_model=SessionResponse, status_code=201)
def create_session(request: Optional[SessionCreateRequest] = None, db: Session = Depends(get_db)):
    """
    Creates a new isolated chat session with independent conversation history.
    """
    return SessionService.create_session(db, request)


@router.get("", response_model=List[SessionResponse])
def list_sessions(limit: int = Query(50, ge=1, le=100), db: Session = Depends(get_db)):
    """
    Lists recent chat sessions sorted by last activity.
    """
    return SessionService.list_sessions(db, limit=limit)


@router.get("/{session_id}", response_model=SessionDetailResponse)
def get_session(session_id: str, db: Session = Depends(get_db)):
    """
    Retrieves the complete message history for a specific session.
    """
    return SessionService.get_session(db, session_id)
