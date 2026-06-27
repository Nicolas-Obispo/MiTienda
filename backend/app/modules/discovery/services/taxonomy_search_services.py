"""
taxonomy_search_services.py
---------------------------
Búsqueda textual interna sobre nodos activos de taxonomía.
"""

from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.modules.discovery.models.taxonomy_models import (
    TaxonomyAssignment,
    TaxonomyNode,
)


TIPOS_SUGERENCIA_BUSCADOR = {"rubro", "categoria", "subcategoria"}


@dataclass(frozen=True)
class _TaxonomySearchCacheItem:
    node_id: int
    slug: str
    nombre: str
    type: str
    orden: int
    nombre_normalizado: str
    descripcion_normalizada: str
    slug_normalizado: str


_TAXONOMY_SEARCH_CACHE: list[_TaxonomySearchCacheItem] | None = None


@dataclass
class TaxonomySearchResult:
    node_id: int
    slug: str
    nombre: str
    type: str
    score: float


def _normalizar_texto(valor: str | None) -> str:
    if not valor:
        return ""
    return valor.strip().lower()


def invalidar_cache_busqueda_taxonomia() -> None:
    global _TAXONOMY_SEARCH_CACHE
    _TAXONOMY_SEARCH_CACHE = None


def _obtener_cache_nodos_taxonomia(db: Session) -> list[_TaxonomySearchCacheItem]:
    global _TAXONOMY_SEARCH_CACHE

    if _TAXONOMY_SEARCH_CACHE is not None:
        return _TAXONOMY_SEARCH_CACHE

    nodes = (
        db.query(TaxonomyNode)
        .filter(TaxonomyNode.activo == True)
        .filter(TaxonomyNode.type.in_(TIPOS_SUGERENCIA_BUSCADOR))
        .order_by(TaxonomyNode.orden.asc(), TaxonomyNode.nombre.asc())
        .all()
    )

    _TAXONOMY_SEARCH_CACHE = [
        _TaxonomySearchCacheItem(
            node_id=node.id,
            slug=node.slug,
            nombre=node.nombre,
            type=node.type,
            orden=node.orden,
            nombre_normalizado=_normalizar_texto(getattr(node, "nombre", None)),
            descripcion_normalizada=_normalizar_texto(
                getattr(node, "descripcion", None)
            ),
            slug_normalizado=_normalizar_texto(getattr(node, "slug", None)),
        )
        for node in nodes
    ]
    return _TAXONOMY_SEARCH_CACHE


def buscar_rubro_ids_asignados_a_nodos_taxonomia(
    db: Session,
    node_ids: list[int],
) -> set[int]:
    if not node_ids:
        return set()

    rows = (
        db.query(TaxonomyAssignment.entity_id)
        .filter(TaxonomyAssignment.taxonomy_node_id.in_(node_ids))
        .filter(TaxonomyAssignment.entity_type == "rubro")
        .all()
    )

    return {entity_id for (entity_id,) in rows}


def _calcular_score_textual(
    *,
    query: str,
    nombre: str,
    descripcion: str,
    slug: str,
) -> float:
    if not query:
        return 0.0

    if nombre == query:
        return 1.0

    if query in nombre:
        return 0.85

    if query in slug:
        return 0.75

    if query in descripcion:
        return 0.60

    return 0.0


def buscar_nodos_taxonomia_por_texto(
    db: Session,
    query: str,
    limit: int = 10,
) -> list[TaxonomySearchResult]:
    query_normalizada = _normalizar_texto(query)
    limit_normalizado = max(1, int(limit))

    if not query_normalizada:
        return []

    nodes = _obtener_cache_nodos_taxonomia(db)

    results: list[TaxonomySearchResult] = []
    for node in nodes:
        score = _calcular_score_textual(
            query=query_normalizada,
            nombre=node.nombre_normalizado,
            descripcion=node.descripcion_normalizada,
            slug=node.slug_normalizado,
        )
        if score <= 0:
            continue

        results.append(
            TaxonomySearchResult(
                node_id=node.node_id,
                slug=node.slug,
                nombre=node.nombre,
                type=node.type,
                score=score,
            )
        )

    results.sort(key=lambda item: (-item.score, item.nombre.lower(), item.node_id))
    return results[:limit_normalizado]
