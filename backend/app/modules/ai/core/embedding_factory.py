"""
embedding_factory.py
--------------------

Factory para obtener el EmbeddingProvider activo según configuración.

- Mantiene desacoplado el dominio del motor IA
- Permite cambiar provider sin tocar services/routers
"""

from app.core.config import settings
from app.modules.ai.core.embedding_provider import EmbeddingProvider
from app.modules.ai.providers.simulated_provider import SimulatedEmbeddingProvider
from app.modules.ai.providers.local_provider import LocalEmbeddingProvider


_PROVIDERS_CACHE: dict[str, EmbeddingProvider] = {}


def get_embedding_provider() -> EmbeddingProvider:
    """
    Devuelve el provider configurado en settings.

    Soporta:
    - simulated (gratis, 0 dependencias)
    - local (modelo open-source local)
    """

    provider_name = (settings.EMBEDDINGS_PROVIDER or "simulated").strip().lower()

    provider = _PROVIDERS_CACHE.get(provider_name)
    if provider is not None:
        return provider

    if provider_name == "simulated":
        provider = SimulatedEmbeddingProvider()
        _PROVIDERS_CACHE[provider_name] = provider
        return provider

    if provider_name == "local":
        try:
            provider = LocalEmbeddingProvider()
        except Exception:
            provider = SimulatedEmbeddingProvider()
        _PROVIDERS_CACHE[provider_name] = provider
        return provider

    raise ValueError(
        f"EMBEDDINGS_PROVIDER no soportado: '{provider_name}'. "
        "Valores soportados: simulated, local"
    )
