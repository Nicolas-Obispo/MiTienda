"""
candidate_sources.py
--------------------
Candidate source contracts and initial source implementations.
"""

from __future__ import annotations

import re
import unicodedata
from typing import Any, Protocol

from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.modules.discovery.models.taxonomy_models import (
    TaxonomyAssignment,
    TaxonomyNode,
)
from app.modules.discovery.services.taxonomy_search_services import (
    buscar_rubro_ids_asignados_a_nodos_taxonomia,
)
from app.modules.posts.models.publicaciones_models import Publicacion
from app.modules.products.models.rubros_models import Rubro
from app.modules.search.services.candidate_engine.candidate_types import (
    CandidateEvidence,
    CandidateGenerationContext,
)
from app.modules.spaces.models.comercios_models import Comercio


class CandidateSource(Protocol):
    """
    Contract implemented by independent candidate sources.
    """

    def generate(
        self,
        context: CandidateGenerationContext,
        db: Session,
    ) -> list[CandidateEvidence]:
        """
        Return candidate evidence without ranking or hydration.
        """


def _get_discovery_value(node: Any, key: str) -> Any:
    if isinstance(node, dict):
        return node.get(key)

    return getattr(node, key, None)


def _normalize_match_text(value: Any) -> str:
    if value is None:
        return ""

    normalized = unicodedata.normalize("NFKD", str(value).strip().lower())
    without_accents = "".join(
        char
        for char in normalized
        if not unicodedata.combining(char)
    )
    return re.sub(r"[^a-z0-9]+", " ", without_accents).strip()


def _get_discovery_node_id(node: Any) -> int | None:
    node_id = _get_discovery_value(node, "node_id")
    if node_id is None:
        node_id = _get_discovery_value(node, "id")

    try:
        node_id_normalizado = int(node_id)
    except (TypeError, ValueError):
        return None

    return node_id_normalizado if node_id_normalizado > 0 else None


def _get_discovery_node_type(node: Any) -> str:
    return str(_get_discovery_value(node, "type") or "").strip().lower()


def _unique_node_ids(nodes: list[Any]) -> list[int]:
    node_ids: list[int] = []
    vistos: set[int] = set()

    for node in nodes:
        node_id = _get_discovery_node_id(node)
        if node_id is None or node_id in vistos:
            continue

        node_ids.append(node_id)
        vistos.add(node_id)

    return node_ids


def _get_discovery_score(node: Any, key: str) -> float:
    try:
        return float(_get_discovery_value(node, key) or 0)
    except (TypeError, ValueError):
        return 0.0


def _extract_metadata_terms(metadata: dict[str, Any] | None) -> list[str]:
    if not isinstance(metadata, dict):
        return []

    terms: list[str] = []
    for key in ("search_terms", "synonyms"):
        values = metadata.get(key)
        if not isinstance(values, list):
            continue

        terms.extend(str(value) for value in values if value)

    return terms


def _clear_query_match(
    *,
    query: str,
    node: Any,
    taxonomy_node: TaxonomyNode | None,
) -> bool:
    normalized_query = _normalize_match_text(query)
    if not normalized_query:
        return False

    terms = [
        _get_discovery_value(node, "nombre"),
        _get_discovery_value(node, "slug"),
    ]
    if taxonomy_node is not None:
        terms.extend(
            [
                taxonomy_node.nombre,
                taxonomy_node.slug,
                *_extract_metadata_terms(taxonomy_node.metadata_json),
            ]
        )

    for term in terms:
        normalized_term = _normalize_match_text(term)
        if not normalized_term:
            continue

        if normalized_query == normalized_term:
            return True
        if normalized_query in normalized_term:
            return True
        if normalized_term in normalized_query:
            return True

    return False


def _is_reliable_discovery_node(
    node: Any,
    *,
    query: str,
    taxonomy_node: TaxonomyNode | None = None,
) -> bool:
    source = str(_get_discovery_value(node, "source") or "").strip().lower()
    text_score = _get_discovery_score(node, "text_score")
    score = _get_discovery_score(node, "score")

    if source in {"text", "mixed"} and text_score >= 0.85:
        return True

    if score >= 0.85:
        return True

    return _clear_query_match(
        query=query,
        node=node,
        taxonomy_node=taxonomy_node,
    )


def _reliable_discovery_nodes(
    context: CandidateGenerationContext,
    db: Session,
) -> list[Any]:
    if not context.discovery_nodes:
        return []

    node_ids = _unique_node_ids(context.discovery_nodes)
    taxonomy_nodes_by_id: dict[int, TaxonomyNode] = {}
    if node_ids:
        taxonomy_nodes_by_id = {
            node.id: node
            for node in (
                db.query(TaxonomyNode)
                .filter(TaxonomyNode.id.in_(node_ids))
                .filter(TaxonomyNode.activo == True)
                .all()
            )
        }

    reliable_nodes: list[Any] = []
    for node in context.discovery_nodes:
        node_id = _get_discovery_node_id(node)
        taxonomy_node = (
            taxonomy_nodes_by_id.get(node_id)
            if node_id is not None
            else None
        )
        if _is_reliable_discovery_node(
            node,
            query=context.query_normalizada,
            taxonomy_node=taxonomy_node,
        ):
            reliable_nodes.append(node)

    return reliable_nodes


def _node_ids_for_rubro_candidates(
    nodes: list[Any],
    db: Session,
) -> list[int]:
    direct_node_ids = _unique_node_ids(
        [
            node
            for node in nodes
            if _get_discovery_node_type(node) != "especialidad"
        ]
    )
    specialty_node_ids = _unique_node_ids(
        [
            node
            for node in nodes
            if _get_discovery_node_type(node) == "especialidad"
        ]
    )

    assigned_specialty_node_ids: set[int] = set()
    if specialty_node_ids:
        assigned_specialty_node_ids = {
            node_id
            for (node_id,) in (
                db.query(TaxonomyAssignment.taxonomy_node_id)
                .filter(TaxonomyAssignment.entity_type == "comercio")
                .filter(TaxonomyAssignment.taxonomy_node_id.in_(specialty_node_ids))
                .all()
            )
        }

    node_ids: list[int] = []
    seen: set[int] = set()
    for node_id in [*direct_node_ids, *specialty_node_ids]:
        if (
            node_id in seen
            or node_id in specialty_node_ids
            and node_id not in assigned_specialty_node_ids
        ):
            continue

        node_ids.append(node_id)
        seen.add(node_id)

    return node_ids


class ComercioNombreCandidateSource:
    """
    Finds active commerces whose name matches the normalized query.
    """

    source = "comercio_nombre"

    def generate(
        self,
        context: CandidateGenerationContext,
        db: Session,
    ) -> list[CandidateEvidence]:
        query = context.query_normalizada.strip()
        if not query:
            return []

        limit = max(1, int(context.limit_por_fuente))
        like = f"%{query}%"

        rows = (
            db.query(Comercio.id, Comercio.nombre)
            .filter(Comercio.activo == True)
            .filter(Comercio.nombre.ilike(like))
            .order_by(Comercio.id.desc())
            .limit(limit)
            .all()
        )

        return [
            CandidateEvidence(
                comercio_id=comercio_id,
                source=self.source,
                reason=nombre,
                matched_entity_type="comercio",
                matched_entity_id=comercio_id,
                matched_text=query,
            )
            for comercio_id, nombre in rows
        ]


class EspecialidadCandidateSource:
    """
    Finds commerce assignments for matched specialty taxonomy nodes.
    """

    source = "especialidad"

    def generate(
        self,
        context: CandidateGenerationContext,
        db: Session,
    ) -> list[CandidateEvidence]:
        reliable_nodes = _reliable_discovery_nodes(context, db)
        if not reliable_nodes:
            return []

        node_ids = _unique_node_ids(
            [
                node
                for node in reliable_nodes
                if _get_discovery_node_type(node) == "especialidad"
            ]
        )
        if not node_ids:
            return []

        limit = max(1, int(context.limit_por_fuente))
        query = context.query_normalizada.strip()

        rows = (
            db.query(
                TaxonomyAssignment.entity_id,
                TaxonomyNode.id,
                TaxonomyNode.nombre,
            )
            .join(TaxonomyNode, TaxonomyNode.id == TaxonomyAssignment.taxonomy_node_id)
            .filter(TaxonomyAssignment.entity_type == "comercio")
            .filter(TaxonomyAssignment.taxonomy_node_id.in_(node_ids))
            .filter(TaxonomyNode.type == "especialidad")
            .filter(TaxonomyNode.activo == True)
            .order_by(TaxonomyNode.orden.asc(), TaxonomyNode.nombre.asc())
            .limit(limit)
            .all()
        )

        return [
            CandidateEvidence(
                comercio_id=comercio_id,
                source=self.source,
                reason=nombre,
                matched_entity_type="taxonomy_node",
                matched_entity_id=taxonomy_node_id,
                matched_text=query,
            )
            for comercio_id, taxonomy_node_id, nombre in rows
        ]


class AssignmentCandidateSource:
    """
    Finds commerce assignments for reliable matched taxonomy nodes.
    """

    source = "assignment"

    def generate(
        self,
        context: CandidateGenerationContext,
        db: Session,
    ) -> list[CandidateEvidence]:
        reliable_nodes = _reliable_discovery_nodes(context, db)
        if not reliable_nodes:
            return []

        node_ids = _unique_node_ids(reliable_nodes)
        if not node_ids:
            return []

        limit = max(1, int(context.limit_por_fuente))
        query = context.query_normalizada.strip()

        rows = (
            db.query(
                TaxonomyAssignment.entity_id,
                TaxonomyAssignment.id,
                TaxonomyNode.nombre,
            )
            .join(TaxonomyNode, TaxonomyNode.id == TaxonomyAssignment.taxonomy_node_id)
            .filter(TaxonomyAssignment.entity_type == "comercio")
            .filter(TaxonomyAssignment.taxonomy_node_id.in_(node_ids))
            .filter(TaxonomyNode.activo == True)
            .order_by(TaxonomyNode.orden.asc(), TaxonomyNode.nombre.asc())
            .limit(limit)
            .all()
        )

        return [
            CandidateEvidence(
                comercio_id=comercio_id,
                source=self.source,
                reason=nombre,
                matched_entity_type="taxonomy_assignment",
                matched_entity_id=assignment_id,
                matched_text=query,
            )
            for comercio_id, assignment_id, nombre in rows
        ]


class RubroCandidateSource:
    """
    Finds active commerces whose rubro is mapped to matched taxonomy nodes.
    """

    source = "rubro"

    def generate(
        self,
        context: CandidateGenerationContext,
        db: Session,
    ) -> list[CandidateEvidence]:
        reliable_nodes = _reliable_discovery_nodes(context, db)
        if not reliable_nodes:
            return []

        node_ids = _node_ids_for_rubro_candidates(reliable_nodes, db)
        if not node_ids:
            return []

        rubro_ids = buscar_rubro_ids_asignados_a_nodos_taxonomia(db, node_ids)
        if not rubro_ids:
            return []

        limit = max(1, int(context.limit_por_fuente))
        query = context.query_normalizada.strip()

        rows = (
            db.query(
                Comercio.id,
                Rubro.id,
                Rubro.nombre,
            )
            .join(Rubro, Rubro.id == Comercio.rubro_id)
            .filter(Comercio.activo == True)
            .filter(Comercio.rubro_id.in_(rubro_ids))
            .order_by(Comercio.id.desc())
            .limit(limit)
            .all()
        )

        return [
            CandidateEvidence(
                comercio_id=comercio_id,
                source=self.source,
                reason=rubro_nombre,
                matched_entity_type="rubro",
                matched_entity_id=rubro_id,
                matched_text=query,
            )
            for comercio_id, rubro_id, rubro_nombre in rows
        ]


class DiscoveryCandidateSource:
    """
    Finds commerce assignments for reliable matched discovery nodes.
    """

    source = "discovery"

    def generate(
        self,
        context: CandidateGenerationContext,
        db: Session,
    ) -> list[CandidateEvidence]:
        reliable_nodes = _reliable_discovery_nodes(context, db)
        if not reliable_nodes:
            return []

        node_ids = _unique_node_ids(reliable_nodes)
        if not node_ids:
            return []

        limit = max(1, int(context.limit_por_fuente))
        query = context.query_normalizada.strip()

        rows = (
            db.query(
                TaxonomyAssignment.entity_id,
                TaxonomyNode.id,
                TaxonomyNode.nombre,
            )
            .join(TaxonomyNode, TaxonomyNode.id == TaxonomyAssignment.taxonomy_node_id)
            .filter(TaxonomyAssignment.entity_type == "comercio")
            .filter(TaxonomyAssignment.taxonomy_node_id.in_(node_ids))
            .filter(TaxonomyNode.activo == True)
            .order_by(TaxonomyNode.orden.asc(), TaxonomyNode.nombre.asc())
            .limit(limit)
            .all()
        )

        return [
            CandidateEvidence(
                comercio_id=comercio_id,
                source=self.source,
                reason=nombre,
                matched_entity_type="taxonomy_node",
                matched_entity_id=taxonomy_node_id,
                matched_text=query,
            )
            for comercio_id, taxonomy_node_id, nombre in rows
        ]


class PublicacionCandidateSource:
    """
    Finds active posts whose title or description matches the normalized query.
    """

    source = "publicacion"

    def generate(
        self,
        context: CandidateGenerationContext,
        db: Session,
    ) -> list[CandidateEvidence]:
        query = context.query_normalizada.strip()
        if not query:
            return []

        limit = max(1, int(context.limit_por_fuente))
        like = f"%{query}%"

        rows = (
            db.query(
                Publicacion.id,
                Publicacion.comercio_id,
                Publicacion.titulo,
            )
            .filter(Publicacion.is_activa.is_(True))
            .filter(
                or_(
                    Publicacion.titulo.ilike(like),
                    Publicacion.descripcion.ilike(like),
                )
            )
            .order_by(Publicacion.id.desc())
            .limit(limit)
            .all()
        )

        return [
            CandidateEvidence(
                comercio_id=comercio_id,
                source=self.source,
                reason=titulo,
                matched_entity_type="publicacion",
                matched_entity_id=publicacion_id,
                matched_text=query,
            )
            for publicacion_id, comercio_id, titulo in rows
        ]
