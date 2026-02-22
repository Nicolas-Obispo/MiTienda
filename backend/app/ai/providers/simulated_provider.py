"""
simulated_provider.py
---------------------

Proveedor de embeddings SIMULADO (0 dependencias externas).

Objetivo:
- Que el sistema funcione sin pagar APIs y sin modelos pesados
- Validar arquitectura (persistencia + similitud + ranking)
- Permitir swap futuro a local/openai/remoto sin tocar routers/services

Genera un vector determinístico basado en hashing.
No es semántico real, pero sirve para el pipeline.
"""

import hashlib
from typing import List

from app.ai.embedding_provider import EmbeddingProvider


class SimulatedEmbeddingProvider(EmbeddingProvider):
    """
    Provider simulado: genera vectores determinísticos a partir del texto.
    """

    def __init__(self, dim: int = 128) -> None:
        self.dim = dim

    def embed_text(self, text: str) -> List[float]:
        """
        Convierte el texto en un vector [0..1] de tamaño fijo (dim).

        - Determinístico: mismo texto -> mismo vector
        - 0 dependencias externas
        """
        normalized_text = (text or "").strip().lower()

        if not normalized_text:
            return [0.0] * self.dim

        # Hash estable (sha256) y expansión repetida hasta cubrir dim
        digest_bytes = hashlib.sha256(normalized_text.encode("utf-8")).digest()

        values: List[float] = []
        i = 0

        while len(values) < self.dim:
            b = digest_bytes[i % len(digest_bytes)]
            values.append(b / 255.0)
            i += 1

        return values