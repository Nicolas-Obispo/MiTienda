"""
rubros_embeddings_services.py
-----------------------------
Deteccion semantica de rubros para busquedas.

MVP:
- Calcula embeddings de rubros activos en memoria.
- Usa nombre + descripcion como texto semantico.
- No persiste embeddings de rubros todavia.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.modules.ai.core.embedding_factory import get_embedding_provider
from app.modules.products.models.rubros_models import Rubro


@dataclass(frozen=True)
class RubroDetectado:
    rubro_id: int
    nombre: str
    score: float


_RUBROS_EMBEDDINGS_CACHE: dict[
    tuple[tuple[int, str, str], ...],
    list[tuple[int, str, list[float]]],
] = {}


def _normalizar_texto(valor: str | None) -> str:
    if not valor:
        return ""
    return valor.strip().lower()


def _build_texto_rubro(rubro: Rubro) -> str:
    partes = [
        str(getattr(rubro, "nombre", "") or "").strip(),
        str(getattr(rubro, "descripcion", "") or "").strip(),
    ]
    return ". ".join(parte for parte in partes if parte)


def _cosine_similarity(a: list[float] | None, b: list[float] | None) -> float:
    if not a or not b or len(a) != len(b):
        return 0.0

    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(y * y for y in b))

    if norm_a == 0 or norm_b == 0:
        return 0.0

    return dot / (norm_a * norm_b)


def _firma_rubros(rubros: list[Rubro]) -> tuple[tuple[int, str, str], ...]:
    return tuple(
        (
            rubro.id,
            _normalizar_texto(getattr(rubro, "nombre", None)),
            _normalizar_texto(getattr(rubro, "descripcion", None)),
        )
        for rubro in rubros
    )


def _obtener_embeddings_rubros(
    db: Session,
) -> list[tuple[int, str, list[float]]]:
    rubros = (
        db.query(Rubro)
        .filter(Rubro.activo == True)
        .order_by(Rubro.id.asc())
        .all()
    )

    firma = _firma_rubros(rubros)
    cacheado = _RUBROS_EMBEDDINGS_CACHE.get(firma)
    if cacheado is not None:
        return cacheado

    provider = get_embedding_provider()
    embeddings: list[tuple[int, str, list[float]]] = []

    for rubro in rubros:
        texto = _build_texto_rubro(rubro)
        if not texto:
            continue

        embeddings.append(
            (
                rubro.id,
                str(rubro.nombre),
                provider.embed_text(texto),
            )
        )

    _RUBROS_EMBEDDINGS_CACHE.clear()
    _RUBROS_EMBEDDINGS_CACHE[firma] = embeddings
    return embeddings


def detectar_rubros_por_query(
    db: Session,
    query: str,
    top_k: int = 3,
    min_score: float = 0.30,
) -> list[RubroDetectado]:
    query_normalizada = _normalizar_texto(query)
    if not query_normalizada:
        return []

    provider = get_embedding_provider()
    query_vector = provider.embed_text(query_normalizada)

    scored: list[RubroDetectado] = []
    for rubro_id, nombre, vector in _obtener_embeddings_rubros(db):
        score = _cosine_similarity(query_vector, vector)
        if score >= min_score:
            scored.append(
                RubroDetectado(
                    rubro_id=rubro_id,
                    nombre=nombre,
                    score=score,
                )
            )

    scored.sort(key=lambda item: (item.score, item.rubro_id), reverse=True)
    return scored[:top_k]
