import time
import logging
from typing import List, Dict, Any, Tuple
from sqlalchemy.orm import Session
from app.backend.models.db_models import ChatSession
from app.backend.schemas.chat_schemas import ChatRequest, ChatResponse, SourceCitation
from app.backend.services.session_service import SessionService
from app.backend.services.provider_service import get_llm_provider
from app.rag.retrieval import retrieve_relevant_chunks, construct_grounded_context
from app.rag.prompts import (
    GROUNDED_SYSTEM_PROMPT,
    GROUNDED_USER_PROMPT_TEMPLATE,
    NO_CONTEXT_FALLBACK_RESPONSE
)
from app.config import settings

logger = logging.getLogger("lenny_growth.growth_assistant")


class GrowthAssistantAgent:
    """
    Grounded conversational agent powered by Lenny Podcast transcripts.
    """
    def __init__(self):
        pass

    def run(self, db: Session, request: ChatRequest) -> ChatResponse:
        start_time = time.time()

        # 1. Validate session
        session = db.query(ChatSession).filter(ChatSession.id == request.session_id).first()
        if not session:
            # Auto-create session if not present
            SessionService.create_session(db)

        # 2. Retrieve relevant transcript chunks
        sources: List[SourceCitation] = retrieve_relevant_chunks(
            db=db,
            query=request.message,
            top_k=settings.rag_top_k,
            threshold=settings.rag_score_threshold
        )

        # 3. Choose provider and model
        chosen_provider = request.provider or session.provider if session else settings.llm_provider
        chosen_model = request.model or session.model if session else None
        llm = get_llm_provider(chosen_provider, chosen_model)

        # 4. Handle empty retrieval
        if not sources:
            logger.info(f"No grounded sources met threshold for question: '{request.message}'")
            assistant_content = NO_CONTEXT_FALLBACK_RESPONSE
            latency_ms = round((time.time() - start_time) * 1000, 2)

            # Persist messages
            SessionService.add_message(db, request.session_id, "user", request.message)
            SessionService.add_message(db, request.session_id, "assistant", assistant_content, sources=[])

            return ChatResponse(
                session_id=request.session_id,
                user_message=request.message,
                assistant_message=assistant_content,
                sources=[],
                provider=chosen_provider,
                model=llm.model,
                latency_ms=latency_ms
            )

        # 5. Format grounded context and conversation history
        context_str = construct_grounded_context(sources)

        # Fetch recent session history for conversational continuity
        session_detail = SessionService.get_session(db, request.session_id)
        history_msgs = []
        for msg in session_detail.messages[-6:]:  # Last 6 messages for context window efficiency
            history_msgs.append({"role": msg.role, "content": msg.content})

        history_summary = "\n".join([f"{m['role'].capitalize()}: {m['content']}" for m in history_msgs]) or "None (New chat)"

        formatted_user_prompt = GROUNDED_USER_PROMPT_TEMPLATE.format(
            context=context_str,
            history=history_summary,
            question=request.message
        )

        # 6. Execute LLM generation
        assistant_content = llm.generate(
            prompt=formatted_user_prompt,
            system_prompt=GROUNDED_SYSTEM_PROMPT,
            temperature=0.3  # Low temperature for strict factual adherence
        )

        latency_ms = round((time.time() - start_time) * 1000, 2)

        # 7. Check if model determined lack of information / refusal
        refusal_markers = [
            "not enough information",
            "no mention of",
            "is not mentioned",
            "does not mention",
            "not found in the provided",
            "transcripts do not contain",
            "transcripts do not provide",
            "there is no mention"
        ]
        is_refusal = any(marker in assistant_content.lower() for marker in refusal_markers)
        active_sources = [] if is_refusal else sources

        # 8. Persist messages and citations
        source_dicts = [s.model_dump() for s in active_sources]
        SessionService.add_message(db, request.session_id, "user", request.message)
        SessionService.add_message(db, request.session_id, "assistant", assistant_content, sources=source_dicts)

        return ChatResponse(
            session_id=request.session_id,
            user_message=request.message,
            assistant_message=assistant_content,
            sources=active_sources,
            provider=chosen_provider,
            model=llm.model,
            latency_ms=latency_ms
        )
