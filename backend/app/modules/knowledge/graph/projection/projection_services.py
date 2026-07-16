"""Servicios de proyeccion hacia Knowledge Graph."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Iterable

from app.modules.knowledge.graph.models import Concept
from app.modules.knowledge.graph.projection.taxonomy_mappers import (
    TaxonomyAssignmentToRelationMapper,
    TaxonomyNodeToConceptMapper,
)
from app.modules.knowledge.graph.services import KnowledgeGraphService


@dataclass
class TaxonomyProjectionSummary:
    """Resumen de una proyeccion Taxonomia -> Knowledge Graph."""

    conceptos_proyectados: int = 0
    relaciones_proyectadas: int = 0
    nodos_omitidos: int = 0
    assignments_omitidos: int = 0
    errores_controlados: list[str] = field(default_factory=list)


class TaxonomyKnowledgeGraphProjectionService:
    """Proyecta Taxonomia estable hacia un KnowledgeGraphService."""

    def __init__(
        self,
        graph: KnowledgeGraphService,
        *,
        node_mapper: TaxonomyNodeToConceptMapper | None = None,
        assignment_mapper: TaxonomyAssignmentToRelationMapper | None = None,
    ) -> None:
        self._graph = graph
        self._node_mapper = node_mapper or TaxonomyNodeToConceptMapper()
        self._assignment_mapper = (
            assignment_mapper or TaxonomyAssignmentToRelationMapper()
        )

    def project(
        self,
        *,
        nodes: Iterable[Any],
        assignments: Iterable[Any],
    ) -> TaxonomyProjectionSummary:
        """Proyecta colecciones ya cargadas sin consultar la DB."""
        summary = TaxonomyProjectionSummary()
        concepts_by_taxonomy_node_id: dict[int, Concept] = {}

        for node in nodes:
            self._project_node(
                node,
                concepts_by_taxonomy_node_id,
                summary,
            )

        for assignment in assignments:
            self._project_assignment(
                assignment,
                concepts_by_taxonomy_node_id,
                summary,
            )

        return summary

    def _project_node(
        self,
        node: Any,
        concepts_by_taxonomy_node_id: dict[int, Concept],
        summary: TaxonomyProjectionSummary,
    ) -> None:
        try:
            concept = self._node_mapper.project(node)
            if concept is None:
                summary.nodos_omitidos += 1
                return

            taxonomy_node_id = int(concept.evidence["taxonomy_node_id"])
            stored = self._graph.get_concept(concept.id) if concept.id else None
            if stored is None:
                stored = self._graph.add_concept(concept)
                summary.conceptos_proyectados += 1

            concepts_by_taxonomy_node_id[taxonomy_node_id] = stored
        except (TypeError, ValueError, KeyError) as exc:
            summary.nodos_omitidos += 1
            summary.errores_controlados.append(f"node: {exc}")

    def _project_assignment(
        self,
        assignment: Any,
        concepts_by_taxonomy_node_id: dict[int, Concept],
        summary: TaxonomyProjectionSummary,
    ) -> None:
        try:
            taxonomy_node_id = _assignment_taxonomy_node_id(assignment)
            concept = concepts_by_taxonomy_node_id.get(taxonomy_node_id)
            if concept is None:
                summary.assignments_omitidos += 1
                return

            relation = self._assignment_mapper.project(assignment, concept)
            if relation is None:
                summary.assignments_omitidos += 1
                return

            if relation.id is None or self._graph.get_relation(relation.id) is None:
                self._graph.add_relation(relation)
                summary.relaciones_proyectadas += 1
        except (TypeError, ValueError, KeyError) as exc:
            summary.assignments_omitidos += 1
            summary.errores_controlados.append(f"assignment: {exc}")


def _assignment_taxonomy_node_id(assignment: Any) -> int:
    value = (
        assignment.get("taxonomy_node_id")
        if isinstance(assignment, dict)
        else getattr(assignment, "taxonomy_node_id", None)
    )
    value = int(value or 0)
    if value <= 0:
        raise ValueError("taxonomy_node_id debe ser positivo")
    return value
