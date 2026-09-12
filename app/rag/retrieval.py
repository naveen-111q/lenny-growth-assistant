import logging
from typing import List, Tuple
import numpy as np
from sqlalchemy.orm import Session
from app.backend.models.db_models import TranscriptChunkModel
from app.backend.schemas.chat_schemas import SourceCitation
from app.rag.embeddings import embedding_service
from app.config import settings

logger = logging.getLogger("lenny_growth.retrieval")


def cosine_similarity(a: List[float], b: List[float]) -> float:
    """
    Computes cosine similarity between two 1D float vectors.
    """
    va = np.array(a, dtype=np.float32)
    vb = np.array(b, dtype=np.float32)
    norm_a = np.linalg.norm(va)
    norm_b = np.linalg.norm(vb)
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return float(np.dot(va, vb) / (norm_a * norm_b))


def retrieve_relevant_chunks(
    db: Session,
    query: str,
    top_k: int = 4,
    threshold: float = 0.20
) -> List[SourceCitation]:
    """
    Embeds the user query, retrieves candidate transcript chunks from the database,
    and returns the top-k highest scoring chunks exceeding the threshold.
    """
    chunks = db.query(TranscriptChunkModel).all()
    if not chunks:
        logger.warning("No transcript chunks present in database to search against.")
        return []

    query_embedding = embedding_service.embed_text(query)
    query_lower = query.lower()

    scored_chunks: List[Tuple[float, TranscriptChunkModel]] = []
    for chunk in chunks:
        if not chunk.embedding:
            continue
        sim = cosine_similarity(query_embedding, chunk.embedding)

        # Keyword / metadata boost for guest names or titles present in query
        guest_lower = (chunk.guest or "").lower()
        title_words = [w.lower() for w in (chunk.episode_title or "").split() if len(w) > 3]
        guest_tokens = [t.lower() for t in guest_lower.split() if len(t) > 3]

        boost = 0.0
        if guest_lower and guest_lower in query_lower:
            boost += 0.15
        elif any(t in query_lower for t in guest_tokens):
            boost += 0.10

        # Topic keyword boost
        if any(w in query_lower for w in title_words):
            boost += 0.05

        final_score = sim + boost
        if final_score >= threshold:
            scored_chunks.append((final_score, chunk))

    # Sort descending by relevance score
    scored_chunks.sort(key=lambda x: x[0], reverse=True)
    top_results = scored_chunks[:top_k]

    citations = []
    for score, chunk in top_results:
        citations.append(
            SourceCitation(
                episode_title=chunk.episode_title,
                guest=chunk.guest,
                guest_role=chunk.guest_role,
                url=chunk.url,
                chunk_index=chunk.chunk_index,
                content_snippet=chunk.content,
                relevance_score=round(float(score), 4)
            )
        )

    logger.info(f"Retrieved {len(citations)} relevant chunks for query: '{query[:40]}...'")
    return citations


def construct_grounded_context(sources: List[SourceCitation]) -> str:
    """
    Formats retrieved sources into a clean markdown block for LLM prompt injection.
    """
    if not sources:
        return "No relevant transcript passages found."

    context_parts = []
    for idx, source in enumerate(sources, 1):
        role_text = f" ({source.guest_role})" if source.guest_role else ""
        url_text = f"\nSource URL: {source.url}" if source.url else ""
        part = (
            f"--- TRANSCRIPT EXCERPT {idx} ---\n"
            f"Episode: {source.episode_title}\n"
            f"Guest: {source.guest}{role_text}{url_text}\n"
            f"Content:\n{source.content_snippet}\n"
        )
        context_parts.append(part)

    return "\n".join(context_parts)
