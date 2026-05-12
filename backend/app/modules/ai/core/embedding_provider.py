"""
embedding_provider.py
---------------------

Interfaz base para proveedores de embeddings.

Esta capa es infraestructura técnica reusable.
No conoce nada del dominio (Comercio, Usuario, etc.).

Permite intercambiar motores:
- simulated
- local
- openai
- remoto

Sin modificar servicios ni routers.
"""

from abc import ABC, abstractmethod
from typing import List


class EmbeddingProvider(ABC):
    """
    Interfaz abstracta para cualquier motor de embeddings.
    """

    @abstractmethod
    def embed_text(self, text: str) -> List[float]:
        """
        Genera embedding vectorial para un texto.
        """
        pass