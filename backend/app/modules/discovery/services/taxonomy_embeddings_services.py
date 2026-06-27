"""
taxonomy_embeddings_services.py
-------------------------------
Deteccion semantica de nodos de taxonomia para busquedas.

MVP:
- Calcula embeddings de nodos activos en memoria.
- Usa nombre, slug, descripcion y type como texto semantico.
- No persiste embeddings de taxonomia todavia.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.modules.ai.core.embedding_factory import get_embedding_provider
from app.modules.discovery.models.taxonomy_models import TaxonomyNode


TIPOS_EMBEDDINGS_TAXONOMIA = {"rubro", "categoria", "subcategoria"}


@dataclass(frozen=True)
class TaxonomyNodeDetectado:
    node_id: int
    slug: str
    nombre: str
    type: str
    score: float


_TAXONOMY_EMBEDDINGS_CACHE: dict[
    tuple[tuple[int, str, str, str, str], ...],
    list[tuple[int, str, str, str, list[float]]],
] = {}


def _normalizar_texto(valor: str | None) -> str:
    if not valor:
        return ""
    return valor.strip().lower()


def _build_texto_taxonomy_node(node: TaxonomyNode) -> str:
    slug = str(getattr(node, "slug", "") or "").replace("-", " ").strip()
    partes = [
        str(getattr(node, "nombre", "") or "").strip(),
        slug,
        str(getattr(node, "descripcion", "") or "").strip(),
        str(getattr(node, "type", "") or "").strip(),
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


def _firma_nodos_taxonomia(
    nodes: list[TaxonomyNode],
) -> tuple[tuple[int, str, str, str, str], ...]:
    return tuple(
        (
            node.id,
            _normalizar_texto(getattr(node, "slug", None)),
            _normalizar_texto(getattr(node, "nombre", None)),
            _normalizar_texto(getattr(node, "type", None)),
            _normalizar_texto(getattr(node, "descripcion", None)),
        )
        for node in nodes
    )


def _obtener_embeddings_nodos_taxonomia(
    db: Session,
) -> list[tuple[int, str, str, str, list[float]]]:
    nodes = (
        db.query(TaxonomyNode)
        .filter(TaxonomyNode.activo == True)
        .filter(TaxonomyNode.type.in_(TIPOS_EMBEDDINGS_TAXONOMIA))
        .order_by(TaxonomyNode.id.asc())
        .all()
    )

    firma = _firma_nodos_taxonomia(nodes)
    cacheado = _TAXONOMY_EMBEDDINGS_CACHE.get(firma)
    if cacheado is not None:
        return cacheado

    provider = get_embedding_provider()
    embeddings: list[tuple[int, str, str, str, list[float]]] = []

    for node in nodes:
        texto = _build_texto_taxonomy_node(node)
        if not texto:
            continue

        embeddings.append(
            (
                node.id,
                str(node.slug),
                str(node.nombre),
                str(node.type),
                provider.embed_text(texto),
            )
        )

    _TAXONOMY_EMBEDDINGS_CACHE.clear()
    _TAXONOMY_EMBEDDINGS_CACHE[firma] = embeddings
    return embeddings


def detectar_nodos_taxonomia_por_query(
    db: Session,
    query: str,
    top_k: int = 5,
    min_score: float = 0.30,
) -> list[TaxonomyNodeDetectado]:
    query_normalizada = _normalizar_texto(query)
    if not query_normalizada:
        return []

    try:
        provider = get_embedding_provider()
        query_vector = provider.embed_text(query_normalizada)

        scored: list[TaxonomyNodeDetectado] = []
        for node_id, slug, nombre, type, vector in _obtener_embeddings_nodos_taxonomia(
            db
        ):
            score = _cosine_similarity(query_vector, vector)
            if score >= min_score:
                scored.append(
                    TaxonomyNodeDetectado(
                        node_id=node_id,
                        slug=slug,
                        nombre=nombre,
                        type=type,
                        score=score,
                    )
                )
    except Exception:
        return []

    scored.sort(key=lambda item: (item.score, item.node_id), reverse=True)
    return scored[:top_k]
