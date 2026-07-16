"""Orquestador de construccion del Commerce Index Document."""

from datetime import datetime
from typing import Any

from app.modules.indexer.builders.derived_context_builders import DerivedContextBuilder
from app.modules.indexer.builders.evidence_builders import EvidenceBuilder
from app.modules.indexer.builders.geographic_coverage_builders import (
    GeographicCoverageBuilder,
)
from app.modules.indexer.builders.identity_builders import IdentityBuilder
from app.modules.indexer.builders.intent_use_case_builders import IntentUseCaseBuilder
from app.modules.indexer.builders.public_profile_builders import PublicProfileBuilder
from app.modules.indexer.builders.search_representation_builders import (
    SearchRepresentationBuilder,
)
from app.modules.indexer.builders.semantic_knowledge_builders import (
    SemanticKnowledgeBuilder,
)
from app.modules.indexer.builders.signal_builders import SignalBuilder
from app.modules.indexer.builders.trace_builders import TraceBuilder
from app.modules.indexer.collectors.commerce_source_collectors import (
    CommerceSourceCollector,
)
from app.modules.indexer.collectors.content_source_collectors import (
    ContentSourceCollector,
)
from app.modules.indexer.collectors.knowledge_graph_collectors import (
    KnowledgeGraphSourceCollector,
)
from app.modules.indexer.collectors.signal_source_collectors import (
    SignalSourceCollector,
)
from app.modules.indexer.collectors.taxonomy_source_collectors import (
    TaxonomySourceCollector,
)
from app.modules.indexer.models.commerce_index_document_models import (
    CommerceIndexDocument,
)
from app.modules.indexer.models.index_block_models import CommerceIndexBlocks
from app.modules.indexer.models.index_trace_models import IndexValidationResult
from app.modules.indexer.services.index_document_validation_services import (
    IndexDocumentValidationService,
)
from app.modules.knowledge.graph.services import KnowledgeGraphService


class CommerceIndexerService:
    """Coordina collectors, builders y validator sin persistir resultados."""

    def __init__(
        self,
        *,
        search_representation_builder: SearchRepresentationBuilder,
        commerce_collector: CommerceSourceCollector | None = None,
        taxonomy_collector: TaxonomySourceCollector | None = None,
        content_collector: ContentSourceCollector | None = None,
        signal_collector: SignalSourceCollector | None = None,
        knowledge_graph_collector: KnowledgeGraphSourceCollector | None = None,
        identity_builder: IdentityBuilder | None = None,
        public_profile_builder: PublicProfileBuilder | None = None,
        geographic_coverage_builder: GeographicCoverageBuilder | None = None,
        semantic_knowledge_builder: SemanticKnowledgeBuilder | None = None,
        derived_context_builder: DerivedContextBuilder | None = None,
        signal_builder: SignalBuilder | None = None,
        intent_use_case_builder: IntentUseCaseBuilder | None = None,
        evidence_builder: EvidenceBuilder | None = None,
        trace_builder: TraceBuilder | None = None,
        validation_service: IndexDocumentValidationService | None = None,
    ) -> None:
        self._commerce_collector = commerce_collector or CommerceSourceCollector()
        self._taxonomy_collector = taxonomy_collector or TaxonomySourceCollector()
        self._content_collector = content_collector or ContentSourceCollector()
        self._signal_collector = signal_collector or SignalSourceCollector()
        self._knowledge_graph_collector = (
            knowledge_graph_collector or KnowledgeGraphSourceCollector()
        )
        self._identity_builder = identity_builder or IdentityBuilder()
        self._public_profile_builder = public_profile_builder or PublicProfileBuilder()
        self._geographic_coverage_builder = (
            geographic_coverage_builder or GeographicCoverageBuilder()
        )
        self._semantic_knowledge_builder = (
            semantic_knowledge_builder or SemanticKnowledgeBuilder()
        )
        self._derived_context_builder = derived_context_builder or DerivedContextBuilder()
        self._signal_builder = signal_builder or SignalBuilder()
        self._intent_use_case_builder = intent_use_case_builder or IntentUseCaseBuilder()
        self._search_representation_builder = search_representation_builder
        self._evidence_builder = evidence_builder or EvidenceBuilder()
        self._trace_builder = trace_builder or TraceBuilder()
        self._validation_service = validation_service or IndexDocumentValidationService()

    def build_commerce_index_document(
        self,
        *,
        source: Any,
        graph: KnowledgeGraphService,
        commerce_id: int,
        document_version: str = "v1",
        indexing_process_version: str = "v1",
    ) -> tuple[CommerceIndexDocument, IndexValidationResult]:
        """Construye y valida un documento sin persistirlo."""

        commerce = self._commerce_collector.collect(source, commerce_id=commerce_id)
        if commerce is None:
            raise ValueError("commerce_not_found")

        taxonomy = self._taxonomy_collector.collect(
            source,
            commerce_id=commerce_id,
            legacy_rubro_id=commerce.rubro_id,
        )
        content = self._content_collector.collect(source, commerce_id=commerce_id)
        signals = self._signal_collector.collect(source, commerce_id=commerce_id)
        knowledge_graph = self._knowledge_graph_collector.collect(
            graph,
            commerce_id=commerce_id,
        )

        identity = self._identity_builder.build(
            commerce=commerce,
            taxonomy=taxonomy,
        )
        warnings = list(self._identity_builder.warnings)

        public_profile = self._public_profile_builder.build(commerce=commerce)
        geographic_coverage = self._geographic_coverage_builder.build(
            commerce=commerce,
        )
        semantic_knowledge = self._semantic_knowledge_builder.build(
            taxonomy=taxonomy,
            knowledge_graph=knowledge_graph,
            content=content,
        )
        derived_context = self._derived_context_builder.build(content=content)
        signal_block = self._signal_builder.build(
            signals=signals,
            derived_context=derived_context,
        )
        intent_use_cases = self._intent_use_case_builder.build(
            semantic_knowledge=semantic_knowledge,
            derived_context=derived_context,
        )
        search_representation = self._search_representation_builder.build(
            identity=identity,
            public_profile=public_profile,
            semantic_knowledge=semantic_knowledge,
            derived_context=derived_context,
            intent_use_cases=intent_use_cases,
        )
        evidences = self._evidence_builder.build(
            commerce=commerce,
            taxonomy=taxonomy,
            content=content,
            signals=signals,
            knowledge_graph=knowledge_graph,
            identity=identity,
            public_profile=public_profile,
            semantic_knowledge=semantic_knowledge,
            geographic_coverage=geographic_coverage,
            derived_context=derived_context,
            signal_block=signal_block,
            intent_use_cases=intent_use_cases,
            search_representation=search_representation,
        )
        traceability = self._trace_builder.build(
            commerce=commerce,
            taxonomy=taxonomy,
            content=content,
            signals=signals,
            knowledge_graph=knowledge_graph,
            identity=identity,
            public_profile=public_profile,
            semantic_knowledge=semantic_knowledge,
            geographic_coverage=geographic_coverage,
            derived_context=derived_context,
            signal_block=signal_block,
            intent_use_cases=intent_use_cases,
            search_representation=search_representation,
            evidences=evidences,
            document_version=document_version,
            indexing_process_version=indexing_process_version,
            warnings=warnings,
        )

        document = CommerceIndexDocument(
            document_id=f"commerce:{commerce.commerce_id}:{document_version}",
            entity_type="commerce",
            entity_id=commerce.commerce_id,
            document_version=document_version,
            indexing_process_version=indexing_process_version,
            generated_at=datetime.utcnow(),
            is_indexable=identity.status == "indexable",
            non_indexable_reasons=(
                [] if identity.status == "indexable" else ["commerce_not_indexable"]
            ),
            blocks=CommerceIndexBlocks(
                identity=identity,
                public_profile=public_profile,
                semantic_knowledge=semantic_knowledge,
                search_representation=search_representation,
                geographic_coverage=geographic_coverage,
                derived_context=derived_context,
                signals=signal_block,
                intent_use_cases=intent_use_cases,
                evidences=evidences,
                traceability=traceability,
            ),
        )
        validation_result = self._validation_service.validate(document)

        return document, validation_result
