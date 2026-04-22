"""Qdrant RAG service."""
import logging
import threading
from typing import Optional

from src.core.config import config

logger = logging.getLogger("vika.rag")

# Lazy imports — optional dependency
_qdrant_available = False
try:
    from qdrant_manager import QdrantManager
    from sentence_transformers import SentenceTransformer
    _qdrant_available = True
except ImportError:
    pass


class RAGService:
    """Vector search over Qdrant knowledge base."""

    def __init__(self):
        self.qdrant: Optional[QdrantManager] = None
        self.embedding_model: Optional[SentenceTransformer] = None
        self._ready = False

        if not _qdrant_available:
            logger.warning("Qdrant/sentence-transformers not available, RAG disabled")
            return

        try:
            self.qdrant = QdrantManager(host=config.qdrant_host, port=config.qdrant_port)
            threading.Thread(target=self._load_model, daemon=True).start()
        except Exception as e:
            logger.warning(f"Qdrant init failed: {e}")

    def _load_model(self):
        try:
            self.embedding_model = SentenceTransformer("distiluse-base-multilingual-cased-v2")
            self._ready = True
            logger.info("Embedding model loaded, RAG ready")
        except Exception as e:
            logger.error(f"Embedding model load failed: {e}")

    def search(self, query: str, limit: int = 3) -> str:
        if not self._ready or not self.qdrant or not self.embedding_model:
            return ""
        try:
            vec = self.embedding_model.encode(query).tolist()
            results = self.qdrant.search(vec, limit=limit)
            return "\n".join(r.payload.get("text", "") for r in results if r.payload.get("text"))
        except Exception as e:
            logger.error(f"RAG search error: {e}")
            return ""
