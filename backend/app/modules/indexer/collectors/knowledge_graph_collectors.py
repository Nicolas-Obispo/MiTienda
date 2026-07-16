"""Collectors de Knowledge Graph para el Indexador."""

from app.modules.indexer.models.source_snapshot_models import (
    KnowledgeGraphSourceSnapshot,
)
from app.modules.knowledge.graph.models.relation_models import Relation
from app.modules.knowledge.graph.services import KnowledgeGraphService


class KnowledgeGraphSourceCollector:
    """Obtiene la vista del Knowledge Graph relevante para un comercio."""

    source_name = "knowledge_graph"

    def collect(
        self,
        graph: KnowledgeGraphService,
        *,
        commerce_id: int,
    ) -> KnowledgeGraphSourceSnapshot:
        """Devuelve conceptos y relaciones vinculados al comercio."""

        relations = [
            relation
            for relation in graph.list_relations()
            if self._relation_matches_commerce(relation, commerce_id)
        ]
        concept_ids = {
            concept_id
            for relation in relations
            for concept_id in (relation.source_concept_id, relation.target_concept_id)
            if concept_id is not None
        }
        concepts = [
            concept
            for concept_id in concept_ids
            if (concept := graph.get_concept(concept_id)) is not None
        ]

        return KnowledgeGraphSourceSnapshot(
            source_name=self.source_name,
            concepts=concepts,
            relations=relations,
        )

    @staticmethod
    def _relation_matches_commerce(relation: Relation, commerce_id: int) -> bool:
        return (
            relation.source_entity_type == "comercio"
            and relation.source_entity_id == commerce_id
        ) or (
            relation.target_entity_type == "comercio"
            and relation.target_entity_id == commerce_id
        )
