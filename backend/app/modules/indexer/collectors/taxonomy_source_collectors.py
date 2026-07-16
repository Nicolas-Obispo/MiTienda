"""Collectors de Taxonomia para el Indexador."""

from sqlalchemy.orm import Session

from app.modules.discovery.models.taxonomy_models import (
    TaxonomyAssignment,
    TaxonomyNode,
)
from app.modules.indexer.models.source_snapshot_models import (
    TaxonomyAssignmentSourceSnapshot,
    TaxonomyNodeSourceSnapshot,
    TaxonomySourceSnapshot,
)


class TaxonomySourceCollector:
    """Obtiene assignments y nodos taxonomicos de un comercio."""

    source_name = "taxonomy"

    def collect(
        self,
        db: Session,
        *,
        commerce_id: int,
        legacy_rubro_id: int | None = None,
    ) -> TaxonomySourceSnapshot:
        """Devuelve un snapshot de Taxonomia sin interpretar conocimiento."""

        assignments = (
            db.query(TaxonomyAssignment)
            .filter(TaxonomyAssignment.entity_type == "comercio")
            .filter(TaxonomyAssignment.entity_id == commerce_id)
            .all()
        )
        node_ids = {assignment.taxonomy_node_id for assignment in assignments}
        nodes = (
            db.query(TaxonomyNode).filter(TaxonomyNode.id.in_(node_ids)).all()
            if node_ids
            else []
        )
        primary_assignment_id = next(
            (
                assignment.id
                for assignment in assignments
                if assignment.principal and assignment.source == "rubro_principal"
            ),
            None,
        )

        return TaxonomySourceSnapshot(
            source_name=self.source_name,
            nodes=[
                TaxonomyNodeSourceSnapshot(
                    id=node.id,
                    parent_id=node.parent_id,
                    type=node.type,
                    slug=node.slug,
                    nombre=node.nombre,
                    descripcion=node.descripcion,
                    activo=bool(node.activo),
                    metadata_json=node.metadata_json or {},
                )
                for node in nodes
            ],
            assignments=[
                TaxonomyAssignmentSourceSnapshot(
                    id=assignment.id,
                    taxonomy_node_id=assignment.taxonomy_node_id,
                    entity_type=assignment.entity_type,
                    entity_id=assignment.entity_id,
                    source=assignment.source,
                    confidence=float(assignment.confidence or 0.0),
                    principal=bool(assignment.principal),
                )
                for assignment in assignments
            ],
            primary_assignment_id=primary_assignment_id,
            legacy_rubro_id=legacy_rubro_id,
        )
