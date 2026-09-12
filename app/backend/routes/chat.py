import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.backend.database.session import get_db
from app.backend.schemas.chat_schemas import ChatRequest, ChatResponse
from app.backend.schemas.generate_schemas import Ship30Response, ArtifactResponse
from app.agents.router import agent_router

logger = logging.getLogger("lenny_growth.routes.chat")
router = APIRouter(prefix="/chat", tags=["Chat"])


@router.post("", response_model=ChatResponse)
def handle_chat(request: ChatRequest, db: Session = Depends(get_db)):
    """
    Processes a user question, retrieves grounded transcript excerpts,
    generates an answer with citations, and isolates conversation history to the session.
    """
    try:
        result = agent_router.route_chat(db, request)
        if isinstance(result, ChatResponse):
            return result
        elif isinstance(result, Ship30Response):
            return ChatResponse(
                session_id=result.session_id,
                user_message=request.message,
                assistant_message=f"### ✍️ Ship 30 for 30 Essay: {result.title}\n\n{result.essay}",
                sources=result.sources,
                provider=result.provider,
                model=result.model,
                latency_ms=0.0
            )
        elif isinstance(result, ArtifactResponse):
            return ChatResponse(
                session_id=result.session_id,
                user_message=request.message,
                assistant_message=f"### 📦 Generated Artifact ({result.artifact_type.upper()}): {result.title}\n*(View and render in the Artifact Viewer)*",
                sources=result.sources,
                provider=result.provider,
                model=result.model,
                latency_ms=0.0
            )
        else:
            raise HTTPException(status_code=500, detail="Unexpected response type from agent router.")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error handling chat request: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Chat processing failed: {str(e)}")
