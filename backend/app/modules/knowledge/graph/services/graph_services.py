"""Servicio en memoria para Knowledge Graph."""

from app.modules.knowledge.graph.models import (
    Concept,
    ConceptStatus,
    ConceptType,
    Relation,
    RelationDirection,
    RelationType,
)


class KnowledgeGraphService:
    """Opera Concept y Relation en memoria."""

    def __init__(self) -> None:
        self._concepts: dict[int, Concept] = {}
        self._relations: dict[int, Relation] = {}
        self._next_concept_id = 1
        self._next_relation_id = 1

    def add_concept(self, concept: Concept) -> Concept:
        """Agrega un Concept."""
        concept_to_store = self._with_concept_id(concept)
        if concept_to_store.id in self._concepts:
            raise ValueError("concept id duplicado")

        self._concepts[concept_to_store.id] = concept_to_store
        self._next_concept_id = max(self._next_concept_id, concept_to_store.id + 1)
        return concept_to_store

    def get_concept(self, concept_id: int) -> Concept | None:
        """Obtiene un Concept por id."""
        return self._concepts.get(concept_id)

    def list_concepts(self) -> list[Concept]:
        """Lista Concepts."""
        return list(self._concepts.values())

    def find_concepts(
        self,
        *,
        canonical_name: str | None = None,
        alias: str | None = None,
        concept_type: ConceptType | None = None,
        status: ConceptStatus | None = None,
    ) -> list[Concept]:
        """Busca Concepts por campos principales."""
        concepts = self.list_concepts()
        if canonical_name is not None:
            normalized = self._normalize(canonical_name)
            concepts = [
                concept
                for concept in concepts
                if self._normalize(concept.canonical_name) == normalized
            ]
        if alias is not None:
            normalized = self._normalize(alias)
            concepts = [
                concept
                for concept in concepts
                if normalized in {self._normalize(item) for item in concept.aliases}
            ]
        if concept_type is not None:
            concepts = [
                concept for concept in concepts if concept.concept_type == concept_type
            ]
        if status is not None:
            concepts = [concept for concept in concepts if concept.status == status]
        return concepts

    def add_relation(self, relation: Relation) -> Relation:
        """Agrega una Relation."""
        self._validate_relation_concepts(relation)
        relation_to_store = self._with_relation_id(relation)
        if relation_to_store.id in self._relations:
            raise ValueError("relation id duplicado")

        self._relations[relation_to_store.id] = relation_to_store
        self._next_relation_id = max(self._next_relation_id, relation_to_store.id + 1)
        return relation_to_store

    def get_relation(self, relation_id: int) -> Relation | None:
        """Obtiene una Relation por id."""
        return self._relations.get(relation_id)

    def list_relations(self) -> list[Relation]:
        """Lista Relations."""
        return list(self._relations.values())

    def find_relations(
        self,
        *,
        source_concept_id: int | None = None,
        target_concept_id: int | None = None,
        source_entity_type: str | None = None,
        source_entity_id: int | None = None,
        target_entity_type: str | None = None,
        target_entity_id: int | None = None,
        relation_type: RelationType | None = None,
        status: ConceptStatus | None = None,
    ) -> list[Relation]:
        """Busca Relations por extremos y estado."""
        relations = self.list_relations()
        filters = {
            "source_concept_id": source_concept_id,
            "target_concept_id": target_concept_id,
            "source_entity_type": source_entity_type,
            "source_entity_id": source_entity_id,
            "target_entity_type": target_entity_type,
            "target_entity_id": target_entity_id,
            "relation_type": relation_type,
            "status": status,
        }
        for field_name, expected in filters.items():
            if expected is None:
                continue
            relations = [
                relation
                for relation in relations
                if getattr(relation, field_name) == expected
            ]
        return relations

    def related_concepts(self, concept_id: int) -> list[Concept]:
        """Obtiene conceptos vecinos respetando direccion."""
        neighbor_ids: list[int] = []
        for relation in self._relations.values():
            if relation.source_concept_id == concept_id and relation.target_concept_id:
                neighbor_ids.append(relation.target_concept_id)
            elif (
                relation.direction == RelationDirection.BIDIRECCIONAL
                and relation.target_concept_id == concept_id
                and relation.source_concept_id
            ):
                neighbor_ids.append(relation.source_concept_id)

        return [
            self._concepts[neighbor_id]
            for neighbor_id in dict.fromkeys(neighbor_ids)
            if neighbor_id in self._concepts
        ]

    def _with_concept_id(self, concept: Concept) -> Concept:
        if concept.id is not None:
            return concept
        return concept.model_copy(update={"id": self._next_concept_id})

    def _with_relation_id(self, relation: Relation) -> Relation:
        if relation.id is not None:
            return relation
        return relation.model_copy(update={"id": self._next_relation_id})

    def _validate_relation_concepts(self, relation: Relation) -> None:
        for concept_id in (
            relation.source_concept_id,
            relation.target_concept_id,
        ):
            if concept_id is not None and concept_id not in self._concepts:
                raise ValueError("relation referencia un concept inexistente")

    @staticmethod
    def _normalize(value: str) -> str:
        return value.strip().lower()
