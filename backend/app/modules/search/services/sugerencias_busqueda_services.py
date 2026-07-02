"""
sugerencias_busqueda_services.py
--------------------------------
Orquestacion backend para sugerencias predictivas del buscador.
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.modules.ai.services.rubros_embeddings_services import (
    detectar_rubros_por_query,
)
from app.modules.discovery.models.taxonomy_models import TaxonomyNode
from app.modules.discovery.services.taxonomy_search_services import (
    buscar_rubro_ids_asignados_a_nodos_taxonomia,
    buscar_nodos_taxonomia_por_texto,
)
from app.modules.products.models.rubros_models import Rubro
from app.modules.search.schemas.sugerencias_busqueda_schemas import (
    SugerenciaBusqueda,
    SugerenciasBusquedaResponse,
)

_SCORE_SEMANTICO_MINIMO = 0.34
_SCORE_SEMANTICO_CON_TEXTO_MINIMO = 0.30
_SCORE_TEXTO_NOMBRE = 0.95
_SCORE_TEXTO_DESCRIPCION = 0.85
_SCORE_TAXONOMIA_RELACIONADA = 0.72
_TIPOS_TAXONOMIA_SUGERIBLES = {
    "rubro",
    "categoria",
    "subcategoria",
    "especialidad",
}


def obtener_sugerencias_busqueda(
    db: Session,
    q: str | None,
    limit: int = 5,
) -> SugerenciasBusquedaResponse:
    query = (q or "").strip()
    limit_normalizado = max(1, min(int(limit), 10))

    if len(query) < 2:
        return SugerenciasBusquedaResponse(query=query, suggestions=[])

    nodos_taxonomia = buscar_nodos_taxonomia_por_texto(
        db,
        query,
        limit=limit_normalizado,
    )
    nodos_taxonomia_fuertes = [
        node for node in nodos_taxonomia if node.score >= _SCORE_TEXTO_DESCRIPCION
    ]
    discovery_tiene_resultado_fuerte = bool(nodos_taxonomia_fuertes)
    rubro_ids_discovery_fuertes = buscar_rubro_ids_asignados_a_nodos_taxonomia(
        db,
        [node.node_id for node in nodos_taxonomia_fuertes],
    )

    sugerencias_textuales = _buscar_rubros_por_texto(
        db=db,
        query=query,
        limit=limit_normalizado,
    )
    sugerencias_textuales_por_id = {
        sugerencia.id: sugerencia for sugerencia in sugerencias_textuales
    }

    rubros_detectados = (
        detectar_rubros_por_query(
            db,
            query,
            top_k=limit_normalizado,
        )
        if not nodos_taxonomia and not sugerencias_textuales
        else []
    )

    suggestions: list[_SugerenciaOrdenable] = [
        _SugerenciaOrdenable(
            suggestion=SugerenciaBusqueda(
                type=node.type,
                id=node.node_id,
                label=node.nombre,
                score=round(node.score, 4),
            ),
            match_en_nombre=node.score == 1.0,
            prioridad=1 if node.score >= _SCORE_TEXTO_DESCRIPCION else 2,
        )
        for node in nodos_taxonomia
    ]

    suggestions.extend(
        _buscar_sugerencias_relacionadas_taxonomia(
            db=db,
            nodos_taxonomia_fuertes=nodos_taxonomia_fuertes,
            limit=limit_normalizado,
        )
    )

    suggestions.extend(
        _SugerenciaOrdenable(
            suggestion=SugerenciaBusqueda(
                type="rubro",
                id=rubro.rubro_id,
                label=rubro.nombre,
                score=round(rubro.score, 4),
            ),
            match_en_nombre=rubro.rubro_id in sugerencias_textuales_por_id
            and sugerencias_textuales_por_id[rubro.rubro_id].score
            == _SCORE_TEXTO_NOMBRE,
            prioridad=4,
        )
        for rubro in rubros_detectados
        if rubro.score >= _SCORE_SEMANTICO_MINIMO
        or (
            rubro.score >= _SCORE_SEMANTICO_CON_TEXTO_MINIMO
            and rubro.rubro_id in sugerencias_textuales_por_id
        )
    )

    suggestions.extend(
        _SugerenciaOrdenable(
            suggestion=sugerencia,
            match_en_nombre=sugerencia.score == _SCORE_TEXTO_NOMBRE,
            prioridad=_prioridad_sugerencia_textual(
                sugerencia,
                rubro_ids_discovery_fuertes,
            ),
        )
        for sugerencia in sugerencias_textuales
    )

    suggestions = _deduplicar_y_ordenar_sugerencias(suggestions)

    return SugerenciasBusquedaResponse(
        query=query,
        suggestions=[item.suggestion for item in suggestions[:limit_normalizado]],
    )


def _buscar_rubros_por_texto(
    db: Session,
    query: str,
    limit: int,
) -> list[SugerenciaBusqueda]:
    query_normalizada = query.strip().lower()
    if not query_normalizada:
        return []

    rubros = (
        db.query(Rubro)
        .filter(Rubro.activo == True)
        .order_by(Rubro.nombre.asc())
        .all()
    )

    suggestions: list[SugerenciaBusqueda] = []
    for rubro in rubros:
        nombre = str(getattr(rubro, "nombre", "") or "")
        descripcion = str(getattr(rubro, "descripcion", "") or "")
        nombre_normalizado = nombre.lower()
        descripcion_normalizada = descripcion.lower()
        texto = " ".join(
            parte
            for parte in [
                nombre,
                descripcion,
            ]
            if parte
        ).lower()

        if query_normalizada not in texto:
            continue

        score = (
            _SCORE_TEXTO_NOMBRE
            if query_normalizada in nombre_normalizado
            else _SCORE_TEXTO_DESCRIPCION
        )

        suggestions.append(
            SugerenciaBusqueda(
                type="rubro",
                id=rubro.id,
                label=rubro.nombre,
                score=score,
            )
        )

        if len(suggestions) >= limit:
            break

    return suggestions


def _buscar_sugerencias_relacionadas_taxonomia(
    db: Session,
    nodos_taxonomia_fuertes: list,
    limit: int,
) -> list[_SugerenciaOrdenable]:
    node_ids_fuertes = [node.node_id for node in nodos_taxonomia_fuertes]
    if not node_ids_fuertes:
        return []

    nodos_fuertes = (
        db.query(TaxonomyNode)
        .filter(TaxonomyNode.id.in_(node_ids_fuertes))
        .filter(TaxonomyNode.activo == True)
        .all()
    )
    if not nodos_fuertes:
        return []

    grupo_ids: set[int] = set()
    for node in nodos_fuertes:
        if node.parent_id is not None:
            grupo_ids.add(node.parent_id)

        if node.type != "especialidad":
            grupo_ids.add(node.id)

    if not grupo_ids:
        return []

    relacionados = (
        db.query(TaxonomyNode)
        .filter(TaxonomyNode.activo == True)
        .filter(TaxonomyNode.type.in_(_TIPOS_TAXONOMIA_SUGERIBLES))
        .filter(
            (TaxonomyNode.id.in_(grupo_ids))
            | (TaxonomyNode.parent_id.in_(grupo_ids))
        )
        .order_by(TaxonomyNode.orden.asc(), TaxonomyNode.nombre.asc())
        .limit(max(limit * 3, limit))
        .all()
    )

    node_ids_fuertes_set = set(node_ids_fuertes)
    suggestions: list[_SugerenciaOrdenable] = []
    for node in relacionados:
        if node.id in node_ids_fuertes_set:
            continue

        suggestions.append(
            _SugerenciaOrdenable(
                suggestion=SugerenciaBusqueda(
                    type=node.type,
                    id=node.id,
                    label=node.nombre,
                    score=_SCORE_TAXONOMIA_RELACIONADA,
                ),
                match_en_nombre=False,
                prioridad=2,
            )
        )

    return suggestions


def _prioridad_sugerencia_textual(
    sugerencia: SugerenciaBusqueda,
    rubro_ids_discovery_fuertes: set[int],
) -> int:
    asignado_a_discovery_fuerte = sugerencia.id in rubro_ids_discovery_fuertes

    if sugerencia.score == _SCORE_TEXTO_NOMBRE and asignado_a_discovery_fuerte:
        return 0

    if sugerencia.score == _SCORE_TEXTO_NOMBRE:
        return 1

    if asignado_a_discovery_fuerte:
        return 2

    return 3


class _SugerenciaOrdenable:
    def __init__(
        self,
        suggestion: SugerenciaBusqueda,
        match_en_nombre: bool,
        prioridad: int,
    ) -> None:
        self.suggestion = suggestion
        self.match_en_nombre = match_en_nombre
        self.prioridad = prioridad


def _deduplicar_y_ordenar_sugerencias(
    suggestions: list[_SugerenciaOrdenable],
) -> list[_SugerenciaOrdenable]:
    deduplicadas: dict[tuple[str, int], _SugerenciaOrdenable] = {}
    labels: dict[str, tuple[str, int]] = {}

    for item in suggestions:
        key = (item.suggestion.type, item.suggestion.id)
        label_key = _normalizar_label_sugerencia(item.suggestion.label)
        key_por_label = labels.get(label_key)
        key_final = key_por_label or key
        existente = deduplicadas.get(key_final)

        if existente is None:
            deduplicadas[key_final] = item
            labels[label_key] = key_final
            continue

        if _debe_reemplazar_sugerencia(item, existente):
            deduplicadas[key_final] = item
            continue

    return sorted(
        deduplicadas.values(),
        key=lambda item: (
            item.prioridad,
            -item.suggestion.score,
            not item.match_en_nombre,
            item.suggestion.label.lower(),
        ),
    )


def _debe_reemplazar_sugerencia(
    item: _SugerenciaOrdenable,
    existente: _SugerenciaOrdenable,
) -> bool:
    if item.prioridad < existente.prioridad:
        return True

    if item.prioridad > existente.prioridad:
        return False

    if item.suggestion.score > existente.suggestion.score:
        return True

    if item.suggestion.score < existente.suggestion.score:
        return False

    return item.match_en_nombre and not existente.match_en_nombre


def _normalizar_label_sugerencia(label: str) -> str:
    return " ".join(str(label or "").strip().lower().split())
