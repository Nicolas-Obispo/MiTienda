"""Builder del bloque Identidad."""

from app.modules.indexer.models.index_block_models import IdentityBlock
from app.modules.indexer.models.source_snapshot_models import (
    CommerceSourceSnapshot,
    TaxonomyAssignmentSourceSnapshot,
    TaxonomySourceSnapshot,
)


class IdentityBuilder:
    """Construye el bloque Identidad desde snapshots."""

    def __init__(self) -> None:
        self.warnings: list[str] = []

    def build(
        self,
        *,
        commerce: CommerceSourceSnapshot,
        taxonomy: TaxonomySourceSnapshot,
    ) -> IdentityBlock:
        """Construye Identidad sin consultar fuentes externas."""

        self.warnings = []
        primary_assignment = self._primary_assignment(taxonomy)
        legacy_rubro_id = taxonomy.legacy_rubro_id or commerce.rubro_id

        if primary_assignment and legacy_rubro_id:
            self._warn_if_sources_differ(primary_assignment, legacy_rubro_id)

        identity_confidence = (
            float(primary_assignment.confidence) if primary_assignment else 0.5
        )

        return IdentityBlock(
            commerce_id=commerce.commerce_id,
            canonical_name=commerce.nombre,
            status="indexable" if commerce.activo else "not_indexable",
            primary_taxonomy_concept_id=None,
            primary_taxonomy_assignment_id=(
                primary_assignment.id if primary_assignment else None
            ),
            legacy_rubro_id=legacy_rubro_id,
            identity_confidence=identity_confidence,
        )

    @staticmethod
    def _primary_assignment(
        taxonomy: TaxonomySourceSnapshot,
    ) -> TaxonomyAssignmentSourceSnapshot | None:
        if taxonomy.primary_assignment_id is not None:
            for assignment in taxonomy.assignments:
                if assignment.id == taxonomy.primary_assignment_id:
                    return assignment

        return next(
            (
                assignment
                for assignment in taxonomy.assignments
                if assignment.principal and assignment.source == "rubro_principal"
            ),
            None,
        )

    def _warn_if_sources_differ(
        self,
        assignment: TaxonomyAssignmentSourceSnapshot,
        legacy_rubro_id: int,
    ) -> None:
        if assignment.taxonomy_node_id != legacy_rubro_id:
            self.warnings.append("identity_taxonomy_assignment_legacy_rubro_differ")
