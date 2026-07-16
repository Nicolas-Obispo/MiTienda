"""Mappers de Taxonomia hacia Knowledge Graph."""

from __future__ import annotations

import hashlib
from typing import Any

from app.modules.knowledge.graph.models import (
    Concept,
    ConceptStatus,
    ConceptType,
    ConfidenceLevel,
    Promotability,
    Relation,
    RelationDirection,
    RelationType,
    RelationWeight,
)


PROJECTED_TAXONOMY_TYPES = {
    "rubro": ConceptType.RUBRO,
    "especialidad": ConceptType.ESPECIALIDAD,
}


def map_numeric_confidence(confidence: float | int | None) -> ConfidenceLevel:
    """Traduce confianza numerica de Taxonomia a nivel conceptual."""
    value = float(confidence or 0.0)
    if value >= 0.95:
        return ConfidenceLevel.MUY_ALTA
    if value >= 0.80:
        return ConfidenceLevel.ALTA
    if value >= 0.60:
        return ConfidenceLevel.MEDIA
    if value >= 0.30:
        return ConfidenceLevel.BAJA
    return ConfidenceLevel.EXPERIMENTAL


class TaxonomyNodeToConceptMapper:
    """Proyecta nodos estables de Taxonomia como Concept."""

    def project(self, node: Any) -> Concept | None:
        """Proyecta rubros y especialidades activos."""
        taxonomy_type = _text_attr(node, "type")
        if taxonomy_type not in PROJECTED_TAXONOMY_TYPES:
            return None

        if not bool(_attr(node, "activo", False)):
            return None

        taxonomy_node_id = _positive_int_attr(node, "id")
        taxonomy_slug = _required_text_attr(node, "slug")

        return Concept(
            id=_stable_positive_id(
                "taxonomy-node",
                taxonomy_node_id,
                taxonomy_slug,
                taxonomy_type,
            ),
            canonical_name=_required_text_attr(node, "nombre"),
            concept_type=PROJECTED_TAXONOMY_TYPES[taxonomy_type],
            description=_optional_text_attr(node, "descripcion"),
            status=ConceptStatus.OFICIAL,
            confidence=ConfidenceLevel.MUY_ALTA,
            version=1,
            aliases=_aliases_from_metadata(_attr(node, "metadata_json", None)),
            source="taxonomy",
            evidence={
                "taxonomy_node_id": taxonomy_node_id,
                "taxonomy_slug": taxonomy_slug,
                "taxonomy_type": taxonomy_type,
            },
        )


class TaxonomyAssignmentToRelationMapper:
    """Proyecta assignments de Taxonomia como Relation."""

    def project(self, assignment: Any, concept: Concept) -> Relation | None:
        """Proyecta assignments de comercio hacia Concept."""
        if concept.id is None:
            raise ValueError("concept proyectado sin id")

        entity_type = _text_attr(assignment, "entity_type")
        if entity_type != "comercio":
            return None

        if concept.concept_type not in {ConceptType.RUBRO, ConceptType.ESPECIALIDAD}:
            return None

        entity_id = _positive_int_attr(assignment, "entity_id")
        taxonomy_assignment_id = _positive_int_attr(assignment, "id")
        taxonomy_node_id = _positive_int_attr(assignment, "taxonomy_node_id")
        source = _required_text_attr(assignment, "source")
        principal = bool(_attr(assignment, "principal", False))
        raw_confidence = _raw_confidence(assignment)
        confidence = map_numeric_confidence(raw_confidence)

        return Relation(
            id=_stable_positive_id(
                "taxonomy-assignment",
                taxonomy_assignment_id,
                taxonomy_node_id,
                entity_type,
                entity_id,
                concept.id,
            ),
            source_entity_type=entity_type,
            source_entity_id=entity_id,
            target_concept_id=concept.id,
            relation_type=RelationType.OFRECE,
            direction=RelationDirection.UNIDIRECCIONAL,
            confidence=confidence,
            base_weight=(
                RelationWeight.PRINCIPAL
                if principal
                else RelationWeight.SECUNDARIA
            ),
            promotability=_promotability(principal=principal, source=source),
            status=_relation_status(
                principal=principal,
                source=source,
                confidence=confidence,
            ),
            source="taxonomy_assignment",
            evidence={
                "taxonomy_assignment_id": taxonomy_assignment_id,
                "taxonomy_node_id": taxonomy_node_id,
                "entity_type": entity_type,
                "entity_id": entity_id,
                "source": source,
                "principal": principal,
                "confidence": raw_confidence,
            },
            version=1,
        )


def _promotability(*, principal: bool, source: str) -> Promotability:
    if principal and source == "rubro_principal":
        return Promotability.IDENTIDAD_OFICIAL
    if principal:
        return Promotability.PROMOVIBLE_MEDIANTE_VALIDACION
    if source in {"rubro_secundario", "especialidad_manual", "sistema"}:
        return Promotability.EVALUABLE
    return Promotability.NO_PROMOVIBLE


def _relation_status(
    *,
    principal: bool,
    source: str,
    confidence: ConfidenceLevel,
) -> ConceptStatus:
    if principal and source == "rubro_principal":
        return ConceptStatus.OFICIAL
    if confidence in {ConfidenceLevel.MUY_ALTA, ConfidenceLevel.ALTA}:
        return ConceptStatus.VALIDADO
    if confidence == ConfidenceLevel.MEDIA:
        return ConceptStatus.PROPUESTO
    return ConceptStatus.DETECTADO


def _aliases_from_metadata(metadata: Any) -> list[str]:
    if not isinstance(metadata, dict):
        return []

    aliases: list[str] = []
    for key in ("search_terms", "synonyms"):
        values = metadata.get(key)
        if isinstance(values, list):
            aliases.extend(str(value) for value in values)
    return aliases


def _stable_positive_id(namespace: str, *parts: object) -> int:
    payload = ":".join([namespace, *(str(part) for part in parts)])
    digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()
    return int(digest[:12], 16) + 1


def _raw_confidence(assignment: Any) -> float:
    return float(_attr(assignment, "confidence", 0.0) or 0.0)


def _attr(item: Any, name: str, default: Any = None) -> Any:
    if isinstance(item, dict):
        return item.get(name, default)
    return getattr(item, name, default)


def _text_attr(item: Any, name: str) -> str:
    value = _attr(item, name, "")
    return str(value or "").strip().lower()


def _optional_text_attr(item: Any, name: str) -> str | None:
    value = str(_attr(item, name, "") or "").strip()
    return value or None


def _required_text_attr(item: Any, name: str) -> str:
    value = str(_attr(item, name, "") or "").strip()
    if not value:
        raise ValueError(f"{name} es requerido")
    return value


def _positive_int_attr(item: Any, name: str) -> int:
    value = int(_attr(item, name, 0) or 0)
    if value <= 0:
        raise ValueError(f"{name} debe ser positivo")
    return value
