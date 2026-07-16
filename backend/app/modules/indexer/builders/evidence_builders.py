"""Builder del bloque Evidencias."""

from typing import Iterable

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
)
from app.modules.indexer.models.index_evidence_models import (
    EvidenceSourceType,
    IndexEvidence,
)
from app.modules.indexer.models.source_snapshot_models import (
    CommerceSourceSnapshot,
    ContentSourceSnapshot,
    KnowledgeGraphSourceSnapshot,
    SignalSourceSnapshot,
    TaxonomySourceSnapshot,
)


class EvidenceBuilder:
    """Consolida evidencias desde snapshots y bloques ya construidos."""

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
    ) -> EvidencesBlock:
        """Construye Evidencias sin modificar bloques ni inferir conocimiento."""

        _ = (
            public_profile,
            semantic_knowledge,
            geographic_coverage,
            derived_context,
            signal_block,
            intent_use_cases,
            search_representation,
        )
        evidences = [
            self._commerce_evidence(commerce, identity),
            *self._taxonomy_evidences(taxonomy),
            *self._content_evidences(content),
            *self._signal_evidences(signals),
            *self._knowledge_graph_evidences(knowledge_graph),
        ]
        return EvidencesBlock(items=self._dedupe(evidences))

    @staticmethod
    def _commerce_evidence(
        commerce: CommerceSourceSnapshot,
        identity: IdentityBlock,
    ) -> IndexEvidence:
        return IndexEvidence(
            evidence_id=f"commerce:{commerce.commerce_id}:identity",
            source_type=EvidenceSourceType.COMMERCE,
            source_id=commerce.commerce_id,
            source_field="commerce",
            claim=f"commerce_identity:{identity.canonical_name}",
            confidence=identity.identity_confidence,
            weight=1.0,
            created_at=commerce.updated_at or commerce.created_at,
        )

    @staticmethod
    def _taxonomy_evidences(
        taxonomy: TaxonomySourceSnapshot,
    ) -> list[IndexEvidence]:
        evidences: list[IndexEvidence] = []

        for assignment in taxonomy.assignments:
            evidences.append(
                IndexEvidence(
                    evidence_id=f"taxonomy_assignment:{assignment.id}",
                    source_type=EvidenceSourceType.TAXONOMY_ASSIGNMENT,
                    source_id=assignment.id,
                    source_field="assignment",
                    claim=(
                        "taxonomy_assignment:"
                        f"{assignment.entity_type}:{assignment.entity_id}:"
                        f"{assignment.taxonomy_node_id}"
                    ),
                    confidence=assignment.confidence,
                    weight=1.0 if assignment.principal else 0.7,
                )
            )

        for node in taxonomy.nodes:
            evidences.append(
                IndexEvidence(
                    evidence_id=f"taxonomy_node:{node.id}",
                    source_type=EvidenceSourceType.TAXONOMY_NODE,
                    source_id=node.id,
                    source_field="node",
                    claim=f"taxonomy_node:{node.type}:{node.slug}",
                    confidence=1.0 if node.activo else 0.0,
                    weight=1.0,
                )
            )

        return evidences

    @staticmethod
    def _content_evidences(content: ContentSourceSnapshot) -> list[IndexEvidence]:
        evidences: list[IndexEvidence] = []

        for publication in content.publications:
            evidences.append(
                IndexEvidence(
                    evidence_id=f"publication:{publication.id}",
                    source_type=EvidenceSourceType.PUBLICATION,
                    source_id=publication.id,
                    source_field="publication",
                    claim=f"publication_active:{publication.titulo}",
                    confidence=1.0 if publication.is_activa else 0.0,
                    weight=0.7,
                    created_at=publication.updated_at or publication.created_at,
                )
            )

        for story in content.stories:
            evidences.append(
                IndexEvidence(
                    evidence_id=f"story:{story.id}",
                    source_type=EvidenceSourceType.STORY,
                    source_id=story.id,
                    source_field="story",
                    claim=f"story_active:{story.id}",
                    confidence=1.0 if story.is_activa else 0.0,
                    weight=0.4,
                    created_at=story.updated_at or story.created_at,
                )
            )

        return evidences

    @staticmethod
    def _signal_evidences(signals: SignalSourceSnapshot) -> list[IndexEvidence]:
        return [
            IndexEvidence(
                evidence_id=f"signal:{key}",
                source_type=EvidenceSourceType.SIGNAL,
                source_id=key,
                source_field="metrics",
                claim=f"signal:{key}:{value}",
                confidence=1.0,
                weight=0.5,
            )
            for key, value in signals.metrics.items()
        ]

    @staticmethod
    def _knowledge_graph_evidences(
        knowledge_graph: KnowledgeGraphSourceSnapshot,
    ) -> list[IndexEvidence]:
        evidences: list[IndexEvidence] = []

        for concept in knowledge_graph.concepts:
            evidences.append(
                IndexEvidence(
                    evidence_id=f"knowledge_graph:concept:{concept.id}",
                    source_type=EvidenceSourceType.KNOWLEDGE_GRAPH,
                    source_id=concept.id,
                    source_field="concept",
                    claim=f"concept:{concept.concept_type.value}:{concept.canonical_name}",
                    confidence=1.0,
                    weight=0.8,
                    created_at=concept.updated_at or concept.created_at,
                )
            )

        for relation in knowledge_graph.relations:
            evidences.append(
                IndexEvidence(
                    evidence_id=f"knowledge_graph:relation:{relation.id}",
                    source_type=EvidenceSourceType.KNOWLEDGE_GRAPH,
                    source_id=relation.id,
                    source_field="relation",
                    claim=f"relation:{relation.relation_type.value}",
                    confidence=1.0,
                    weight=0.8,
                    created_at=relation.updated_at or relation.created_at,
                )
            )

        return evidences

    @staticmethod
    def _dedupe(evidences: Iterable[IndexEvidence]) -> list[IndexEvidence]:
        result: list[IndexEvidence] = []
        seen: set[str] = set()

        for evidence in evidences:
            if evidence.evidence_id in seen:
                continue
            result.append(evidence)
            seen.add(evidence.evidence_id)

        return result
