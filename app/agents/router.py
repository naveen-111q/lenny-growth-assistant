import logging
import re
from typing import Optional, Union
from sqlalchemy.orm import Session
from app.backend.schemas.chat_schemas import ChatRequest, ChatResponse
from app.backend.schemas.generate_schemas import (
    Ship30Request,
    Ship30Response,
    ArtifactRequest,
    ArtifactResponse
)
from app.agents.growth_assistant import GrowthAssistantAgent
from app.agents.ship30_skill import Ship30Skill
from app.agents.artifact_skill import ArtifactSkill

from app.backend.models.db_models import ChatSession
from app.backend.services.session_service import SessionService
from app.config import settings

logger = logging.getLogger("lenny_growth.router")

GREETING_RESPONSE_TEXT = (
    "Hey there! 👋 I am **The Lenny Growth Assistant**, an AI advisor strictly grounded in the wisdom, tactics, and frameworks from Lenny's Podcast and Newsletter.\n\n"
    "I can help you break down proven startup and product strategies from top leaders:\n"
    "- 🎯 **Product-Market Fit:** Rahul Vohra (Superhuman) on the 40% benchmark and PMF engine\n"
    "- 🔄 **B2B Product-Led Growth:** Elena Verna on acquisition vs retention loops and collaborative virality\n"
    "- ⚡ **High Agency & Execution:** Shreyas Doshi on bending reality and the LNO time management framework\n"
    "- 🏰 **Founder Mode:** Brian Chesky (Airbnb) on hands-on leadership and the 11-Star experience\n"
    "- 📈 **Compounding Growth Loops:** Gustaf Alströmer (YC) on retention curves and growth loops\n\n"
    "**Try asking me a question like:**\n"
    "- *\"How did Superhuman measure product market fit?\"*\n"
    "- *\"What is Elena Verna's advice on freemium paywalls?\"*\n"
    "- *\"Write a Ship 30 atomic essay on High Agency\"*\n\n"
    "What would you like to explore today?"
)


class AgentRouter:
    """
    Directs user prompts to the appropriate specialized skill or default grounded Q&A.
    """
    def __init__(self):
        self.growth_assistant = GrowthAssistantAgent()
        self.ship30_skill = Ship30Skill()
        self.artifact_skill = ArtifactSkill()

    def route_chat(self, db: Session, request: ChatRequest) -> Union[ChatResponse, Ship30Response, ArtifactResponse]:
        """
        Evaluates prompt intent and dispatches to the correct agent/skill.
        """
        text = request.message.lower().strip()

        # Check for conversational greeting / introduction
        greeting_pattern = r"^(hi+|hey+|hello+|hola|howdy|good\s+(morning|afternoon|evening|day)|greetings)(\s+(there|all|team|lenny))?[\s\.\!\?\:\)]*$"
        intro_pattern = r"^(who are you\??|what can you do\??|help\??|what topics do you know\??|tell me about yourself\??)$"

        if re.match(greeting_pattern, text) or re.match(intro_pattern, text):
            logger.info(f"Router identified conversational greeting/intro: '{request.message}'")
            session = db.query(ChatSession).filter(ChatSession.id == request.session_id).first()
            if not session:
                new_s = SessionService.create_session(db)
                request.session_id = new_s.id
                session = db.query(ChatSession).filter(ChatSession.id == request.session_id).first()

            SessionService.add_message(db, request.session_id, "user", request.message)
            SessionService.add_message(db, request.session_id, "assistant", GREETING_RESPONSE_TEXT, sources=[])

            chosen_provider = request.provider or (session.provider if session else settings.llm_provider)
            chosen_model = request.model or (session.model if session else settings.openrouter_model)

            return ChatResponse(
                session_id=request.session_id,
                user_message=request.message,
                assistant_message=GREETING_RESPONSE_TEXT,
                sources=[],
                provider=chosen_provider,
                model=chosen_model,
                latency_ms=1.0
            )

        # Check for Ship 30 essay trigger
        ship30_pattern = r"(ship 30|atomic essay|1,?250[- ]word essay|write an essay|generate essay)"
        if re.search(ship30_pattern, text):
            logger.info(f"Router identified Ship 30 skill request: '{request.message[:40]}'")
            return self.ship30_skill.generate_essay(
                db=db,
                request=Ship30Request(
                    session_id=request.session_id,
                    topic=request.message,
                    provider=request.provider,
                    model=request.model
                )
            )

        # Check for HTML artifact trigger
        html_pattern = r"(landing page|html|dashboard in html|component in html|webpage|ui prototype)"
        if re.search(html_pattern, text) and ("create" in text or "generate" in text or "build" in text):
            logger.info(f"Router identified HTML artifact request: '{request.message[:40]}'")
            return self.artifact_skill.generate_artifact(
                db=db,
                request=ArtifactRequest(
                    session_id=request.session_id,
                    artifact_type="html",
                    prompt=request.message,
                    provider=request.provider,
                    model=request.model
                )
            )

        # Check for Markdown artifact trigger
        md_pattern = r"(prd|spec document|strategy doc|matrix|framework doc|in markdown|generate artifact)"
        if re.search(md_pattern, text) and ("create" in text or "generate" in text or "build" in text):
            logger.info(f"Router identified Markdown artifact request: '{request.message[:40]}'")
            return self.artifact_skill.generate_artifact(
                db=db,
                request=ArtifactRequest(
                    session_id=request.session_id,
                    artifact_type="markdown",
                    prompt=request.message,
                    provider=request.provider,
                    model=request.model
                )
            )

        # Default to standard grounded Q&A
        logger.info(f"Router dispatching to default Growth Assistant Q&A: '{request.message[:40]}'")
        return self.growth_assistant.run(db, request)


# Global singleton instance
agent_router = AgentRouter()
