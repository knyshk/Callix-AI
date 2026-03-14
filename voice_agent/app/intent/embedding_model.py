"""
Embedding Model
Wraps sentence-transformers to generate semantic embeddings.
Used by the intent detector for cosine similarity matching.
"""
import numpy as np
from typing import List
from app.core.errors import IntentError
from app.core.errors_catalog import ErrorCode
from app.core.logger import logger


_embedding_model = None


def _get_model():
    global _embedding_model
    if _embedding_model is None:
        try:
            from sentence_transformers import SentenceTransformer
            logger.info("EMBEDDING_MODEL_LOADING", model="all-MiniLM-L6-v2")
            _embedding_model = SentenceTransformer("all-MiniLM-L6-v2")
            logger.info("EMBEDDING_MODEL_LOADED")
        except Exception as e:
            raise IntentError(ErrorCode.INTENT_MODEL_FAILURE, detail=str(e))
    return _embedding_model


def get_embedding(text: str) -> np.ndarray:
    """Generate a normalized sentence embedding vector."""
    model = _get_model()
    embedding = model.encode(text, normalize_embeddings=True)
    return embedding


def get_embeddings_batch(texts: List[str]) -> np.ndarray:
    """Generate embeddings for a batch of texts."""
    model = _get_model()
    embeddings = model.encode(texts, normalize_embeddings=True, batch_size=32)
    return embeddings


def cosine_similarity(vec_a: np.ndarray, vec_b: np.ndarray) -> float:
    """Compute cosine similarity between two normalized vectors."""
    return float(np.dot(vec_a, vec_b))
