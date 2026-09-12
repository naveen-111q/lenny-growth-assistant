import logging
import re
from typing import List, Optional
from sqlalchemy.orm import Session
from app.backend.models.db_models import ChatSession
from app.backend.schemas.generate_schemas import Ship30Request, Ship30Response
from app.backend.schemas.chat_schemas import SourceCitation
from app.backend.services.session_service import SessionService
from app.backend.services.provider_service import get_llm_provider
from app.rag.retrieval import retrieve_relevant_chunks, construct_grounded_context
from app.rag.prompts import SHIP30_SYSTEM_PROMPT
from app.config import settings

logger = logging.getLogger("lenny_growth.ship30_skill")


class Ship30Skill:
    """
    Dedicated skill module to synthesize conversation insights into an atomic,
    skimmable ~1,250-word essay following the Ship 30 for 30 digital writing framework.
    """
    @staticmethod
    def generate_essay(db: Session, request: Ship30Request) -> Ship30Response:
        session = db.query(ChatSession).filter(ChatSession.id == request.session_id).first()
        session_detail = SessionService.get_session(db, request.session_id)

        # 1. Compile recent user/assistant conversation
        conv_text = []
        for msg in session_detail.messages:
            if msg.role in ("user", "assistant"):
                conv_text.append(f"{msg.role.capitalize()}: {msg.content}")
        conversation_context = "\n\n".join(conv_text) if conv_text else "General Product Management & Growth Principles"

        # 2. Retrieve grounded transcript context
        search_query = request.topic or (session_detail.messages[-1].content if session_detail.messages else "Product Market Fit Growth")
        sources: List[SourceCitation] = retrieve_relevant_chunks(db, search_query, top_k=5, threshold=0.18)
        grounded_context = construct_grounded_context(sources)

        # 3. Choose provider
        chosen_provider = request.provider or (session.provider if session else settings.llm_provider)
        chosen_model = request.model or (session.model if session else None)
        llm = get_llm_provider(chosen_provider, chosen_model)

        # 4. Construct high-fidelity Ship 30 generation prompt
        topic_clause = f"Focus Topic: {request.topic}\n" if request.topic else ""
        prompt = f"""
{topic_clause}
GROUNDED TRANSCRIPT MATERIAL:
{grounded_context}

RECENT CONVERSATION CONTEXT:
{conversation_context}

INSTRUCTIONS:
Transform the above grounded insights into a comprehensive ~1,250-word Ship 30 for 30 atomic essay.
Adhere strictly to:
1. HOOK: A punchy, counter-intuitive opening 1-2 sentences.
2. SUBHEADINGS: Use clear, magnetic H2 and H3 headings.
3. STRUCTURE:
   - Part 1: The Trap (Why traditional intuition fails)
   - Part 2: The Mental Shift (The foundational paradigm)
   - Part 3: The Framework (Detailed breakdown of the guest's mental models, e.g., Superhuman PMF Engine, Elena Verna's PLG loops, Shreyas Doshi's LNO, or Brian Chesky's Founder Mode)
   - Part 4: The 4-Step Execution Playbook (Exact operational steps, metrics, and cadences)
   - Part 5: The Parting Thought (Summary & core challenge question)
4. FORMATTING: Use bulleted breakdowns and bold text on key phrases.
5. GROUNDING: Anchor every recommendation in the provided transcript facts.
6. TARGET LENGTH: Provide thorough, actionable depth reaching approximately 1,250 words.

Title your essay on the very first line with '# [Essay Title]'.
"""

        essay_content = llm.generate(
            prompt=prompt,
            system_prompt=SHIP30_SYSTEM_PROMPT,
            temperature=0.4,
            max_tokens=2500
        )

        # Extract title if present
        title = "The Lenny Growth Playbook"
        first_line = essay_content.strip().split("\n")[0]
        if first_line.startswith("# "):
            title = first_line.replace("# ", "").strip()

        # Compute word count
        words = re.findall(r'\b\w+\b', essay_content)
        word_count = len(words)

        # Persist to chat session as an assistant artifact message
        SessionService.add_message(
            db=db,
            session_id=request.session_id,
            role="assistant",
            content=f"### ✍️ Ship 30 for 30 Essay: {title}\n\n{essay_content}",
            sources=[s.model_dump() for s in sources]
        )

        return Ship30Response(
            session_id=request.session_id,
            title=title,
            essay=essay_content,
            word_count=word_count,
            sources=sources,
            provider=chosen_provider,
            model=llm.model
        )
