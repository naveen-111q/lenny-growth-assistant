import logging
import re
from typing import List, Optional
from sqlalchemy.orm import Session
from app.backend.models.db_models import ChatSession
from app.backend.schemas.generate_schemas import ArtifactRequest, ArtifactResponse
from app.backend.schemas.chat_schemas import SourceCitation
from app.backend.services.session_service import SessionService
from app.backend.services.provider_service import get_llm_provider
from app.rag.retrieval import retrieve_relevant_chunks, construct_grounded_context
from app.rag.prompts import ARTIFACT_SYSTEM_PROMPT
from app.config import settings

logger = logging.getLogger("lenny_growth.artifact_skill")


def sanitize_html(raw_html: str) -> str:
    """
    Sanitizes untrusted LLM-generated HTML.
    - Strips executable <script> tags and contents.
    - Removes dangerous inline event handlers (onload, onclick, onerror, etc.).
    - Disallows javascript: URIs.
    - Blocks nested framing attempts.
    """
    # 1. Strip script tags entirely
    cleaned = re.sub(r'<script\b[^<]*(?:(?!<\/script>)<[^<]*)*<\/script>', '', raw_html, flags=re.IGNORECASE)

    # 2. Strip inline event handlers like onclick=, onerror=, onmouseover=
    cleaned = re.sub(r'\son\w+\s*=\s*(["\']).*?\1', '', cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r'\son\w+\s*=\s*[^ >]+', '', cleaned, flags=re.IGNORECASE)

    # 3. Strip javascript: and data: URIs in href and src
    cleaned = re.sub(r'(href|src)\s*=\s*(["\'])\s*(javascript|vbscript|data):.*?\2', r'\1="#"', cleaned, flags=re.IGNORECASE)

    # 4. Remove nested iframes to prevent clickjacking
    cleaned = re.sub(r'<iframe\b[^<]*(?:(?!<\/iframe>)<[^<]*)*<\/iframe>', '', cleaned, flags=re.IGNORECASE)

    return cleaned


class ArtifactSkill:
    """
    Dedicated skill module to generate structured Markdown documents or
    self-contained, sanitized HTML/CSS prototypes grounded in conversation history.
    """
    @staticmethod
    def generate_artifact(db: Session, request: ArtifactRequest) -> ArtifactResponse:
        session = db.query(ChatSession).filter(ChatSession.id == request.session_id).first()
        session_detail = SessionService.get_session(db, request.session_id)

        # 1. Compile conversation history
        conv_text = []
        for msg in session_detail.messages:
            if msg.role in ("user", "assistant"):
                conv_text.append(f"{msg.role.capitalize()}: {msg.content}")
        conversation_context = "\n\n".join(conv_text) if conv_text else "General Growth Context"

        # 2. Retrieve grounded sources based on prompt
        sources: List[SourceCitation] = retrieve_relevant_chunks(db, request.prompt, top_k=4, threshold=0.18)
        grounded_context = construct_grounded_context(sources)

        # 3. Choose provider
        chosen_provider = request.provider or (session.provider if session else settings.llm_provider)
        chosen_model = request.model or (session.model if session else None)
        llm = get_llm_provider(chosen_provider, chosen_model)

        artifact_type = request.artifact_type.lower().strip()
        if artifact_type not in ("markdown", "html"):
            artifact_type = "markdown"

        prompt = f"""
REQUESTED ARTIFACT TYPE: {artifact_type.upper()}
USER INSTRUCTION:
{request.prompt}

GROUNDED PODCAST TRANSCRIPTS:
{grounded_context}

CONVERSATION CONTEXT:
{conversation_context}

REQUIREMENTS:
- Output ONLY the artifact content enclosed in ```{artifact_type} ... ```.
- If markdown, create an exhaustive, production-grade product document with structured sections, tables, and metrics.
- If html, create a complete self-contained HTML5/CSS document with embedded responsive CSS, modern cards, vibrant gradients, and clean typography. Do NOT include <script> tags.
"""

        raw_output = llm.generate(
            prompt=prompt,
            system_prompt=ARTIFACT_SYSTEM_PROMPT,
            temperature=0.3,
            max_tokens=1500
        )

        # Extract content from code block if wrapped
        extracted = raw_output.strip()
        pattern = rf"```{artifact_type}\s*([\s\S]*?)```"
        match = re.search(pattern, raw_output, re.IGNORECASE)
        if match:
            extracted = match.group(1).strip()
        else:
            # Robustly strip leading ```html or ``` even if closing fence was not generated
            extracted = re.sub(r"^```(?:[a-zA-Z0-9_\-]+)?\s*\n?", "", extracted)
            extracted = re.sub(r"\n?```\s*$", "", extracted).strip()

        # Sanitize if HTML
        if artifact_type == "html":
            extracted = sanitize_html(extracted)

            # Fix any unclosed <style> tag if model generation was truncated
            if "<style" in extracted.lower() and "</style>" not in extracted.lower():
                extracted += "\n</style>\n"

            if "<html" not in extracted.lower():
                # Wrap in standard clean HTML template if partial
                extracted = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Lenny Growth Assistant Artifact</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
            background: #f8fafc;
            color: #0f172a;
            margin: 0;
            padding: 24px;
            line-height: 1.6;
        }}
        .container {{
            max-width: 900px;
            margin: 0 auto;
            background: #ffffff;
            padding: 32px;
            border-radius: 16px;
            border: 1px solid #e2e8f0;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
        }}
    </style>
</head>
<body>
    <div class="container">
        {extracted}
    </div>
</body>
</html>"""
            else:
                # Ensure closing tags exist so browser completes DOM rendering
                if "</body" not in extracted.lower():
                    extracted += "\n</body>"
                if "</html" not in extracted.lower():
                    extracted += "\n</html>"

        title = f"{request.prompt[:40]}... ({artifact_type.upper()})"

        # Persist as message in session
        SessionService.add_message(
            db=db,
            session_id=request.session_id,
            role="assistant",
            content=f"### 📦 Generated Artifact: {title}\n*(Switch to the Artifact Viewer tab to preview or copy the raw code)*",
            sources=[s.model_dump() for s in sources]
        )

        return ArtifactResponse(
            session_id=request.session_id,
            artifact_type=artifact_type,
            title=title,
            content=extracted,
            sources=sources,
            provider=chosen_provider,
            model=llm.model
        )
