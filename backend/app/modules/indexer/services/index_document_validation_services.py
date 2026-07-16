"""Servicio de validacion del Commerce Index Document."""

from app.modules.indexer.models.commerce_index_document_models import (
    CommerceIndexDocument,
)
from app.modules.indexer.models.index_evidence_models import EvidenceSourceType
from app.modules.indexer.models.index_trace_models import (
    IndexValidationIssue,
    IndexValidationResult,
    IndexValidationSeverity,
    IndexValidationStatus,
)


class IndexDocumentValidationService:
    """Valida consistencia estructural sin modificar el documento."""

    def validate(self, document: CommerceIndexDocument) -> IndexValidationResult:
        """Devuelve el resultado de validacion del documento."""

        issues: list[IndexValidationIssue] = []
        self._validate_document(document, issues)
        self._validate_identity(document, issues)
        self._validate_blocks(document, issues)
        self._validate_evidences(document, issues)
        self._validate_traceability(document, issues)
        self._validate_search_representation(document, issues)

        status = (
            IndexValidationStatus.INVALID
            if any(issue.severity == IndexValidationSeverity.ERROR for issue in issues)
            else IndexValidationStatus.VALID
        )
        return IndexValidationResult(status=status, issues=issues)

    def _validate_document(
        self,
        document: CommerceIndexDocument,
        issues: list[IndexValidationIssue],
    ) -> None:
        self._require_text(
            document.document_version,
            "document_version_required",
            "document_version es obligatorio",
            issues,
        )
        self._require_text(
            document.indexing_process_version,
            "indexing_process_version_required",
            "indexing_process_version es obligatorio",
            issues,
        )
        if document.entity_type != "commerce":
            self._error("invalid_entity_type", "entity_type debe ser commerce", issues)
        if document.entity_id < 1:
            self._error("invalid_entity_id", "entity_id debe ser positivo", issues)
        if not document.is_indexable and not document.non_indexable_reasons:
            self._error(
                "non_indexable_reasons_required",
                "Documento no indexable requiere motivos",
                issues,
            )

    def _validate_identity(
        self,
        document: CommerceIndexDocument,
        issues: list[IndexValidationIssue],
    ) -> None:
        identity = document.blocks.identity
        self._require_text(
            identity.canonical_name,
            "identity_canonical_name_required",
            "Identidad requiere canonical_name",
            issues,
            block_name="identity",
        )
        if identity.commerce_id != document.entity_id:
            self._error(
                "identity_document_entity_mismatch",
                "commerce_id de Identidad debe coincidir con entity_id del documento",
                issues,
                block_name="identity",
            )
        if document.is_indexable and identity.status != "indexable":
            self._error(
                "indexable_document_identity_not_indexable",
                "Documento indexable requiere Identidad indexable",
                issues,
                block_name="identity",
            )

    def _validate_blocks(
        self,
        document: CommerceIndexDocument,
        issues: list[IndexValidationIssue],
    ) -> None:
        required_blocks = {
            "identity": document.blocks.identity,
            "public_profile": document.blocks.public_profile,
            "semantic_knowledge": document.blocks.semantic_knowledge,
            "search_representation": document.blocks.search_representation,
            "geographic_coverage": document.blocks.geographic_coverage,
            "derived_context": document.blocks.derived_context,
            "signals": document.blocks.signals,
            "intent_use_cases": document.blocks.intent_use_cases,
            "evidences": document.blocks.evidences,
            "traceability": document.blocks.traceability,
        }
        for block_name, block in required_blocks.items():
            if block is None:
                self._error(
                    "required_block_missing",
                    f"Bloque obligatorio ausente: {block_name}",
                    issues,
                    block_name=block_name,
                )

    def _validate_evidences(
        self,
        document: CommerceIndexDocument,
        issues: list[IndexValidationIssue],
    ) -> None:
        evidence_ids = {
            evidence.evidence_id
            for evidence in document.blocks.evidences.items
            if evidence.evidence_id
        }
        for evidence in document.blocks.evidences.items:
            if evidence.source_type not in set(EvidenceSourceType):
                self._error(
                    "invalid_evidence_source_type",
                    "Evidencia requiere origen definido",
                    issues,
                    block_name="evidences",
                )
            if not 0.0 <= evidence.confidence <= 1.0:
                self._error(
                    "invalid_evidence_confidence",
                    "Evidencia requiere confianza entre 0 y 1",
                    issues,
                    block_name="evidences",
                )

        for block_name, refs in self._evidence_refs_by_block(document).items():
            for ref in refs:
                if ref.evidence_id not in evidence_ids:
                    self._error(
                        "invalid_evidence_ref",
                        f"Referencia de evidencia inexistente: {ref.evidence_id}",
                        issues,
                        block_name=block_name,
                    )

    def _validate_traceability(
        self,
        document: CommerceIndexDocument,
        issues: list[IndexValidationIssue],
    ) -> None:
        trace = document.blocks.traceability.trace
        if trace.indexing_started_at is None:
            self._error(
                "indexing_started_at_required",
                "Trazabilidad requiere indexing_started_at",
                issues,
                block_name="traceability",
            )
        if trace.indexing_finished_at is None:
            self._error(
                "indexing_finished_at_required",
                "Trazabilidad requiere indexing_finished_at",
                issues,
                block_name="traceability",
            )
        if not trace.source_traces:
            self._error(
                "source_traces_required",
                "Trazabilidad requiere fuentes",
                issues,
                block_name="traceability",
            )
        if not trace.builder_traces:
            self._error(
                "builder_traces_required",
                "Trazabilidad requiere versiones de builders",
                issues,
                block_name="traceability",
            )
        if (
            trace.indexing_started_at is not None
            and trace.indexing_finished_at is not None
            and trace.indexing_finished_at < trace.indexing_started_at
        ):
            self._error(
                "invalid_trace_timestamps",
                "indexing_finished_at no puede ser anterior a indexing_started_at",
                issues,
                block_name="traceability",
            )
        for source_trace in trace.source_traces:
            self._require_text(
                source_trace.source_name,
                "source_trace_name_required",
                "Cada source trace requiere nombre de fuente",
                issues,
                block_name="traceability",
            )
        for builder_trace in trace.builder_traces:
            self._require_text(
                builder_trace.builder_version,
                "builder_version_required",
                "Cada builder trace requiere version",
                issues,
                block_name="traceability",
            )

    def _validate_search_representation(
        self,
        document: CommerceIndexDocument,
        issues: list[IndexValidationIssue],
    ) -> None:
        search = document.blocks.search_representation
        self._require_text(
            search.search_text,
            "search_text_required",
            "Representacion de Busqueda requiere search_text",
            issues,
            block_name="search_representation",
        )
        self._require_text(
            search.embedding_source_text or "",
            "embedding_source_text_required",
            "Representacion de Busqueda requiere embedding_source_text",
            issues,
            block_name="search_representation",
        )
        if not search.normalized_terms:
            self._error(
                "normalized_terms_required",
                "Representacion de Busqueda requiere terminos preparados",
                issues,
                block_name="search_representation",
            )

    @staticmethod
    def _evidence_refs_by_block(document: CommerceIndexDocument) -> dict[str, list]:
        return {
            "identity": document.blocks.identity.evidence_refs,
            "public_profile": document.blocks.public_profile.evidence_refs,
            "semantic_knowledge": document.blocks.semantic_knowledge.evidence_refs,
            "search_representation": document.blocks.search_representation.evidence_refs,
            "geographic_coverage": document.blocks.geographic_coverage.evidence_refs,
            "derived_context": document.blocks.derived_context.evidence_refs,
            "signals": document.blocks.signals.evidence_refs,
            "intent_use_cases": document.blocks.intent_use_cases.evidence_refs,
        }

    def _require_text(
        self,
        value: str | None,
        code: str,
        message: str,
        issues: list[IndexValidationIssue],
        *,
        block_name: str | None = None,
    ) -> None:
        if not value or not value.strip():
            self._error(code, message, issues, block_name=block_name)

    @staticmethod
    def _error(
        code: str,
        message: str,
        issues: list[IndexValidationIssue],
        *,
        block_name: str | None = None,
    ) -> None:
        issues.append(
            IndexValidationIssue(
                code=code,
                message=message,
                severity=IndexValidationSeverity.ERROR,
                block_name=block_name,
            )
        )
