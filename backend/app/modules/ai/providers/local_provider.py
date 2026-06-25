"""
local_provider.py

ETAPA 52 — Provider local real usando sentence-transformers.

Implementa correctamente la interfaz EmbeddingProvider.
"""

from functools import lru_cache
from typing import List

from sentence_transformers import SentenceTransformer

from app.modules.ai.core.embedding_provider import EmbeddingProvider


class LocalEmbeddingProvider(EmbeddingProvider):
    """
    Implementación real usando modelo open-source local.

    Modelo actual:
        all-MiniLM-L6-v2 (384 dimensiones)

    Se carga una sola vez al instanciar.
    """

    def __init__(self):
        # Carga del modelo en memoria
        self.model = SentenceTransformer("all-MiniLM-L6-v2")

    def embed_text(self, text: str) -> List[float]:
        """
        Implementación obligatoria de la interfaz.
        """

        if not text:
            text = ""

        return list(self._embed_text_cached(text.strip()))

    @lru_cache(maxsize=256)
    def _embed_text_cached(self, text: str) -> tuple[float, ...]:
        vector = self.model.encode(text)

        return tuple(vector.tolist())
