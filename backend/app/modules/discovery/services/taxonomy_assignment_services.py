"""
taxonomy_assignment_services.py
-------------------------------
Servicios idempotentes para vincular entidades existentes con la taxonomia.
"""

from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.modules.discovery.models.taxonomy_models import (
    TaxonomyAssignment,
    TaxonomyNode,
)
from app.modules.products.models.rubros_models import Rubro
from app.modules.spaces.models.comercios_models import Comercio


@dataclass
class AssignmentSyncResult:
    rubros_mapeados: int = 0
    rubro_assignments_creados: int = 0
    rubro_assignments_existentes: int = 0
    comercios_asignados: int = 0
    comercio_assignments_creados: int = 0
    comercio_assignments_existentes: int = 0


def asegurar_assignment(
    db: Session,
    *,
    taxonomy_node_id: int,
    entity_type: str,
    entity_id: int,
    source: str = "sistema",
    confidence: float = 1.0,
    principal: bool = True,
) -> tuple[TaxonomyAssignment, bool]:
    assignment = (
        db.query(TaxonomyAssignment)
        .filter(
            TaxonomyAssignment.taxonomy_node_id == taxonomy_node_id,
            TaxonomyAssignment.entity_type == entity_type,
            TaxonomyAssignment.entity_id == entity_id,
        )
        .first()
    )

    if assignment:
        cambio = False
        if assignment.source != source:
            assignment.source = source
            cambio = True
        if assignment.confidence != confidence:
            assignment.confidence = confidence
            cambio = True
        if assignment.principal != principal:
            assignment.principal = principal
            cambio = True
        return assignment, False if not cambio else False

    assignment = TaxonomyAssignment(
        taxonomy_node_id=taxonomy_node_id,
        entity_type=entity_type,
        entity_id=entity_id,
        source=source,
        confidence=confidence,
        principal=principal,
    )
    db.add(assignment)
    return assignment, True


def sincronizar_assignments_comercio_desde_rubros(
    db: Session,
    comercio_id: int,
    rubro_id_principal: int,
    rubro_ids_secundarios: list[int] | None = None,
) -> None:
    assignments_actuales = (
        db.query(TaxonomyAssignment)
        .filter(TaxonomyAssignment.entity_type == "comercio")
        .filter(TaxonomyAssignment.entity_id == comercio_id)
        .all()
    )
    secundarios_actuales_node_ids = {
        assignment.taxonomy_node_id
        for assignment in assignments_actuales
        if not assignment.principal
    }

    secundarios_reemplazados = rubro_ids_secundarios is not None
    rubro_ids_secundarios_normalizados: list[int] = []
    if secundarios_reemplazados:
        rubro_ids_secundarios_normalizados = [
            rubro_id
            for rubro_id in rubro_ids_secundarios
            if rubro_id != rubro_id_principal
        ]

    rubro_ids = [rubro_id_principal, *rubro_ids_secundarios_normalizados]

    rubro_assignments = (
        db.query(TaxonomyAssignment)
        .filter(TaxonomyAssignment.entity_type == "rubro")
        .filter(TaxonomyAssignment.entity_id.in_(rubro_ids))
        .all()
    )
    rubro_id_a_node_id = {
        assignment.entity_id: assignment.taxonomy_node_id
        for assignment in rubro_assignments
    }

    principal_node_id = rubro_id_a_node_id.get(rubro_id_principal)
    secundarios_node_ids = (
        {
            node_id
            for rubro_id, node_id in rubro_id_a_node_id.items()
            if rubro_id != rubro_id_principal and node_id is not None
        }
        if secundarios_reemplazados
        else secundarios_actuales_node_ids
    )

    node_ids_actuales = set(secundarios_node_ids)
    if principal_node_id is not None:
        node_ids_actuales.add(principal_node_id)

    for assignment in assignments_actuales:
        if assignment.taxonomy_node_id not in node_ids_actuales:
            db.delete(assignment)

    if principal_node_id is not None:
        asegurar_assignment(
            db,
            taxonomy_node_id=principal_node_id,
            entity_type="comercio",
            entity_id=comercio_id,
            source="rubro_principal",
            confidence=1.0,
            principal=True,
        )

    for node_id in secundarios_node_ids:
        if node_id == principal_node_id:
            continue

        asegurar_assignment(
            db,
            taxonomy_node_id=node_id,
            entity_type="comercio",
            entity_id=comercio_id,
            source="rubro_secundario",
            confidence=0.8,
            principal=False,
        )


def sincronizar_assignments_desde_rubros(
    db: Session,
    rubro_nombre_a_taxonomy_slug: dict[str, str],
) -> AssignmentSyncResult:
    result = AssignmentSyncResult()

    nodes_by_slug = {
        node.slug: node
        for node in db.query(TaxonomyNode)
        .filter(TaxonomyNode.slug.in_(set(rubro_nombre_a_taxonomy_slug.values())))
        .all()
    }

    rubros = db.query(Rubro).all()
    rubro_id_a_node: dict[int, TaxonomyNode] = {}

    for rubro in rubros:
        rubro_nombre = (rubro.nombre or "").strip().lower()
        slug = rubro_nombre_a_taxonomy_slug.get(rubro_nombre)
        if not slug:
            continue

        node = nodes_by_slug.get(slug)
        if not node:
            continue

        result.rubros_mapeados += 1
        rubro_id_a_node[rubro.id] = node

        _, creado = asegurar_assignment(
            db,
            taxonomy_node_id=node.id,
            entity_type="rubro",
            entity_id=rubro.id,
        )
        if creado:
            result.rubro_assignments_creados += 1
        else:
            result.rubro_assignments_existentes += 1

    if not rubro_id_a_node:
        return result

    comercios = (
        db.query(Comercio)
        .filter(Comercio.rubro_id.in_(list(rubro_id_a_node.keys())))
        .all()
    )

    for comercio in comercios:
        node = rubro_id_a_node.get(comercio.rubro_id)
        if not node:
            continue

        result.comercios_asignados += 1
        _, creado = asegurar_assignment(
            db,
            taxonomy_node_id=node.id,
            entity_type="comercio",
            entity_id=comercio.id,
        )
        if creado:
            result.comercio_assignments_creados += 1
        else:
            result.comercio_assignments_existentes += 1

    return result
