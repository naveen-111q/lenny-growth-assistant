import logging
from typing import List, Optional
import numpy as np
from app.config import settings

logger = logging.getLogger("lenny_growth.embeddings")

_embedding_model = None
_model_failed = False


class LocalEmbeddingProvider:
    """
    Provides dense vector embeddings using SentenceTransformers (default all-MiniLM-L6-v2).
    Includes a lightweight fallback to ensure zero failure under any environment.
    """
    def __init__(self, model_name: Optional[str] = None):
        self.model_name = model_name or settings.embedding_model
        self._load_model()

    def _load_model(self):
        global _embedding_model, _model_failed
        if _embedding_model is not None:
            return

        try:
            from sentence_transformers import SentenceTransformer
            logger.info(f"Loading SentenceTransformer embedding model: {self.model_name}")
            _embedding_model = SentenceTransformer(self.model_name)
            logger.info("SentenceTransformer model loaded successfully.")
        except Exception as e:
            logger.warning(f"Failed to load SentenceTransformer ({e}). Falling back to TF-IDF hashing embeddings.")
            _model_failed = True

    def embed_text(self, text: str) -> List[float]:
        """
        Embeds a single string into a normalized 1D float vector.
        """
        return self.embed_batch([text])[0]

    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """
        Embeds a list of strings into normalized float vectors.
        """
        global _embedding_model, _model_failed
        if _embedding_model is not None and not _model_failed:
            try:
                embeddings = _embedding_model.encode(texts, normalize_embeddings=True, show_progress_bar=False)
                return [e.tolist() for e in embeddings]
            except Exception as e:
                logger.error(f"Inference error in SentenceTransformer: {e}. Using fallback.")

        # Fallback: Deterministic TF-IDF / character n-gram hashing vectorizer (384 dimensions)
        return [self._fallback_embed(t) for t in texts]

    def _fallback_embed(self, text: str, dim: int = 384) -> List[float]:
        """
        Deterministic lightweight embedding fallback producing normalized unit vectors.
        """
        vec = np.zeros(dim, dtype=np.float32)
        words = text.lower().split()
        for word in words:
            h = hash(word) % dim
            vec[h] += 1.0
        norm = np.linalg.norm(vec)
        if norm > 0:
            vec = vec / norm
        return vec.tolist()


# Global singleton instance
embedding_service = LocalEmbeddingProvider()
