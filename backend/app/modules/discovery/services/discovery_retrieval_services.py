"""
discovery_retrieval_services.py
-------------------------------
Recuperacion unificada de nodos Discovery por texto y embeddings.
"""

from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.modules.discovery.services.taxonomy_embeddings_services import (
    detectar_nodos_taxonomia_por_query,
)
from app.modules.discovery.services.taxonomy_search_services import (
    buscar_nodos_taxonomia_por_texto,
)


@dataclass(frozen=True)
class DiscoveryRetrievalResult:
    node_id: int
    slug: str
    nombre: str
    type: str
    score: float
    source: str
    text_score: float
    semantic_score: float


def recuperar_nodos_discovery(
    db: Session,
    query: str,
    limit: int = 10,
    min_semantic_score: float = 0.40,
    usar_embeddings: bool = True,
) -> list[DiscoveryRetrievalResult]:
    limit_normalizado = max(1, int(limit))

    resultados_por_id: dict[int, DiscoveryRetrievalResult] = {}

    resultados_textuales = buscar_nodos_taxonomia_por_texto(
        db,
        query,
        limit=limit_normalizado,
    )
    for item in resultados_textuales:
        resultados_por_id[item.node_id] = DiscoveryRetrievalResult(
            node_id=item.node_id,
            slug=item.slug,
            nombre=item.nombre,
            type=item.type,
            score=item.score,
            source="text",
            text_score=item.score,
            semantic_score=0.0,
        )

    if usar_embeddings:
        resultados_semanticos = detectar_nodos_taxonomia_por_query(
            db,
            query,
            top_k=limit_normalizado,
            min_score=min_semantic_score,
        )
        for item in resultados_semanticos:
            existente = resultados_por_id.get(item.node_id)
            if existente is None:
                resultados_por_id[item.node_id] = DiscoveryRetrievalResult(
                    node_id=item.node_id,
                    slug=item.slug,
                    nombre=item.nombre,
                    type=item.type,
                    score=item.score,
                    source="semantic",
                    text_score=0.0,
                    semantic_score=item.score,
                )
                continue

            resultados_por_id[item.node_id] = DiscoveryRetrievalResult(
                node_id=existente.node_id,
                slug=existente.slug,
                nombre=existente.nombre,
                type=existente.type,
                score=existente.text_score,
                source="mixed",
                text_score=existente.text_score,
                semantic_score=item.score,
            )

    resultados = sorted(
        resultados_por_id.values(),
        key=lambda item: (
            -item.text_score,
            -item.semantic_score,
            item.nombre.lower(),
        ),
    )
    return resultados[:limit_normalizado]
