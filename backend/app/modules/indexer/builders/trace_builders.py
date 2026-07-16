"""Builder del bloque Trazabilidad."""

from datetime import datetime

from app.modules.indexer.models.index_block_models import (
    DerivedContextBlock,
    EvidencesBlock,
    GeographicCoverageBlock,
    IdentityBlock,
    IntentUseCasesBlock,
    PublicProfileBlock,
    SearchRepresentationBlock,
    SemanticKnowledgeBlock,
    SignalsBlock,
    TraceabilityBlock,
)
from app.modules.indexer.models.index_trace_models import (
    BuilderTrace,
    IndexTrace,
    IndexValidationResult,
    SourceTrace,
)
from app.modules.indexer.models.source_snapshot_models import (
    CommerceSourceSnapshot,
    ContentSourceSnapshot,
    KnowledgeGraphSourceSnapshot,
    SignalSourceSnapshot,
    TaxonomySourceSnapshot,
)


class TraceBuilder:
    """Construye trazabilidad del proceso de indexacion."""

    def build(
        self,
        *,
        commerce: CommerceSourceSnapshot,
        taxonomy: TaxonomySourceSnapshot,
        content: ContentSourceSnapshot,
        signals: SignalSourceSnapshot,
        knowledge_graph: KnowledgeGraphSourceSnapshot,
        identity: IdentityBlock,
        public_profile: PublicProfileBlock,
        semantic_knowledge: SemanticKnowledgeBlock,
        geographic_coverage: GeographicCoverageBlock,
        derived_context: DerivedContextBlock,
        signal_block: SignalsBlock,
        intent_use_cases: IntentUseCasesBlock,
        search_representation: SearchRepresentationBlock,
        evidences: EvidencesBlock,
        document_version: str,
        indexing_process_version: str,
        warnings: list[str] | None = None,
        validation_result: IndexValidationResult | None = None,
    ) -> TraceabilityBlock:
        """Construye Trazabilidad sin corregir ni reconstruir bloques."""

        _ = (
            identity,
            public_profile,
            semantic_knowledge,
            geographic_coverage,
            derived_context,
            signal_block,
            intent_use_cases,
            search_representation,
            evidences,
        )
        generated_at = datetime.utcnow()

        return TraceabilityBlock(
            trace=IndexTrace(
                indexing_started_at=generated_at,
                indexing_finished_at=generated_at,
                source_traces=self._source_traces(
                    commerce,
                    taxonomy,
                    content,
                    signals,
                    knowledge_graph,
                ),
                builder_traces=self._builder_traces(
                    document_version=document_version,
                    indexing_process_version=indexing_process_version,
                ),
                warnings=[
                    *commerce.warnings,
                    *taxonomy.warnings,
                    *content.warnings,
                    *signals.warnings,
                    *knowledge_graph.warnings,
                    *(warnings or []),
                ],
                validation_result=validation_result,
            )
        )

    @staticmethod
    def _source_traces(
        commerce: CommerceSourceSnapshot,
        taxonomy: TaxonomySourceSnapshot,
        content: ContentSourceSnapshot,
        signals: SignalSourceSnapshot,
        knowledge_graph: KnowledgeGraphSourceSnapshot,
    ) -> list[SourceTrace]:
        return [
            SourceTrace(
                source_name=commerce.source_name,
                source_id=commerce.commerce_id,
                updated_at=commerce.updated_at,
            ),
            SourceTrace(source_name=taxonomy.source_name),
            SourceTrace(source_name=content.source_name),
            SourceTrace(source_name=signals.source_name),
            SourceTrace(source_name=knowledge_graph.source_name),
        ]

    @staticmethod
    def _builder_traces(
        *,
        document_version: str,
        indexing_process_version: str,
    ) -> list[BuilderTrace]:
        builder_names = [
            "IdentityBuilder",
            "PublicProfileBuilder",
            "GeographicCoverageBuilder",
            "SemanticKnowledgeBuilder",
            "DerivedContextBuilder",
            "SignalBuilder",
            "IntentUseCaseBuilder",
            "SearchRepresentationBuilder",
            "EvidenceBuilder",
            "TraceBuilder",
        ]

        return [
            BuilderTrace(
                builder_name=builder_name,
                builder_version=f"{document_version}:{indexing_process_version}",
            )
            for builder_name in builder_names
        ]
