"""Builder del bloque Conocimiento Semantico."""

from app.modules.indexer.models.index_block_models import SemanticKnowledgeBlock
from app.modules.indexer.models.source_snapshot_models import (
    ContentSourceSnapshot,
    KnowledgeGraphSourceSnapshot,
    TaxonomySourceSnapshot,
)
from app.modules.knowledge.graph.models.concept_models import Concept
from app.modules.knowledge.graph.models.relation_models import Relation, RelationType


class SemanticKnowledgeBuilder:
    """Construye el bloque Conocimiento Semantico desde snapshots."""

    def build(
        self,
        *,
        taxonomy: TaxonomySourceSnapshot,
        knowledge_graph: KnowledgeGraphSourceSnapshot,
        content: ContentSourceSnapshot,
    ) -> SemanticKnowledgeBlock:
        """Construye conocimiento semantico sin consultar fuentes externas."""

        relations = knowledge_graph.relations

        return SemanticKnowledgeBlock(
            concepts=knowledge_graph.concepts,
            relations=relations,
            primary_identity_relation_id=self._primary_identity_relation_id(relations),
            secondary_coverage_relation_ids=self._secondary_coverage_relation_ids(
                relations
            ),
            capabilities=self._capabilities(knowledge_graph.concepts, relations),
            restrictions=self._restrictions(content),
            semantic_confidence_summary=self._confidence_summary(taxonomy),
        )

    @staticmethod
    def _primary_identity_relation_id(relations: list[Relation]) -> int | None:
        for relation in relations:
            if relation.promotability.value == "identidad_oficial":
                return relation.id
        return None

    @staticmethod
    def _secondary_coverage_relation_ids(relations: list[Relation]) -> list[int]:
        return [
            relation.id
            for relation in relations
            if relation.id is not None
            and relation.promotability.value != "identidad_oficial"
        ]

    @staticmethod
    def _capabilities(
        concepts: list[Concept],
        relations: list[Relation],
    ) -> list[str]:
        concepts_by_id = {
            concept.id: concept
            for concept in concepts
            if concept.id is not None
        }
        capability_relation_types = {
            RelationType.OFRECE,
            RelationType.VENDE,
            RelationType.RESUELVE,
            RelationType.SATISFACE,
        }
        capabilities: list[str] = []
        seen: set[str] = set()

        for relation in relations:
            if relation.relation_type not in capability_relation_types:
                continue

            concept_id = relation.target_concept_id or relation.source_concept_id
            concept = concepts_by_id.get(concept_id)
            if concept is None:
                continue

            capability = concept.canonical_name.strip()
            dedupe_key = capability.lower()
            if capability and dedupe_key not in seen:
                capabilities.append(capability)
                seen.add(dedupe_key)

        return capabilities

    @staticmethod
    def _restrictions(content: ContentSourceSnapshot) -> list[str]:
        """Devuelve restricciones solo cuando existan en fuentes preparadas."""

        _ = content
        return []

    @staticmethod
    def _confidence_summary(taxonomy: TaxonomySourceSnapshot) -> dict[str, float | int]:
        if not taxonomy.assignments:
            return {
                "assignment_count": 0,
                "max_assignment_confidence": 0.0,
                "avg_assignment_confidence": 0.0,
            }

        confidences = [assignment.confidence for assignment in taxonomy.assignments]
        return {
            "assignment_count": len(confidences),
            "max_assignment_confidence": max(confidences),
            "avg_assignment_confidence": sum(confidences) / len(confidences),
        }
