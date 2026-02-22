"""
embedding_factory.py
--------------------

Factory para obtener el EmbeddingProvider activo según configuración.

- Mantiene desacoplado el dominio del motor IA
- Permite cambiar provider sin tocar services/routers
"""

from app.core.config import settings
from app.ai.embedding_provider import EmbeddingProvider
from app.ai.providers.simulated_provider import SimulatedEmbeddingProvider
from app.ai.providers.local_provider import LocalEmbeddingProvider


def get_embedding_provider() -> EmbeddingProvider:
    """
    Devuelve el provider configurado en settings.

    Soporta:
    - simulated (gratis, 0 dependencias)
    - local (modelo open-source local)
    """

    provider_name = (settings.EMBEDDINGS_PROVIDER or "simulated").strip().lower()

    if provider_name == "simulated":
        return SimulatedEmbeddingProvider()

    if provider_name == "local":
        return LocalEmbeddingProvider()

    raise ValueError(
        f"EMBEDDINGS_PROVIDER no soportado: '{provider_name}'. "
        "Valores soportados: simulated, local"
    )