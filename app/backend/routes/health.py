import logging
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.backend.database.session import get_db, check_db_health
from app.backend.models.db_models import TranscriptChunkModel
from app.backend.services.provider_service import OllamaProvider, OpenRouterProvider
from app.config import settings

logger = logging.getLogger("lenny_growth.routes.health")
router = APIRouter(tags=["Health"])


@router.get("/health")
def health_check(db: Session = Depends(get_db)):
    """
    Returns system readiness, database status, LLM provider availability,
    and knowledge base statistics.
    """
    db_ok, dialect, db_msg = check_db_health()
    chunk_count = db.query(TranscriptChunkModel).count()

    # Provider health checks
    ollama_health = OllamaProvider().check_health()
    openrouter_health = OpenRouterProvider().check_health()

    overall_status = "healthy" if db_ok and (ollama_health.is_available or openrouter_health.is_available) else "degraded"

    return {
        "status": overall_status,
        "active_provider": settings.llm_provider,
        "database": {
            "status": "connected" if db_ok else "unreachable",
            "dialect": dialect,
            "message": db_msg,
            "ingested_chunks": chunk_count
        },
        "providers": {
            "ollama": ollama_health.model_dump(),
            "openrouter": openrouter_health.model_dump()
        }
    }
