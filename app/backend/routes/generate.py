import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.backend.database.session import get_db
from app.backend.schemas.generate_schemas import (
    Ship30Request,
    Ship30Response,
    ArtifactRequest,
    ArtifactResponse
)
from app.agents.ship30_skill import Ship30Skill
from app.agents.artifact_skill import ArtifactSkill

logger = logging.getLogger("lenny_growth.routes.generate")
router = APIRouter(prefix="/generate", tags=["Generation Skills"])


@router.post("/ship30", response_model=Ship30Response)
def generate_ship30_essay(request: Ship30Request, db: Session = Depends(get_db)):
    """
    Generates an atomic ~1,250-word Ship 30 for 30 essay grounded in the current
    session conversation and relevant transcript knowledge.
    """
    try:
        return Ship30Skill.generate_essay(db, request)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating Ship 30 essay: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Ship 30 generation failed: {str(e)}")


@router.post("/artifact", response_model=ArtifactResponse)
def generate_artifact(request: ArtifactRequest, db: Session = Depends(get_db)):
    """
    Generates a production-quality Markdown document or sanitized responsive HTML/CSS artifact.
    """
    try:
        return ArtifactSkill.generate_artifact(db, request)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating artifact: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Artifact generation failed: {str(e)}")
