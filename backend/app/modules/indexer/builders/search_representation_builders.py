"""Builder del bloque Representacion de Busqueda."""

from app.modules.indexer.models.index_block_models import (
    DerivedContextBlock,
    IdentityBlock,
    IntentUseCasesBlock,
    PublicProfileBlock,
    SearchRepresentationBlock,
    SemanticKnowledgeBlock,
)
from app.modules.indexer.models.text_normalization_contract_models import (
    TextNormalizationContract,
)


class SearchRepresentationBuilder:
    """Construye la representacion derivada para busqueda."""

    def __init__(
        self,
        *,
        normalizer: TextNormalizationContract,
        representation_version: str = "v1",
    ) -> None:
        self._normalizer = normalizer
        self._representation_version = representation_version

    def build(
        self,
        *,
        identity: IdentityBlock,
        public_profile: PublicProfileBlock,
        semantic_knowledge: SemanticKnowledgeBlock,
        derived_context: DerivedContextBlock,
        intent_use_cases: IntentUseCasesBlock,
    ) -> SearchRepresentationBlock:
        """Construye Search Text derivado sin generar embeddings."""

        taxonomy_terms = self._taxonomy_terms(semantic_knowledge)
        content_terms = self._normalized_unique(derived_context.content_coverage_terms)
        semantic_terms = self._semantic_terms(semantic_knowledge, intent_use_cases)
        aliases = self._aliases(semantic_knowledge)
        source_parts = [
            identity.canonical_name,
            public_profile.description,
            public_profile.public_location_label,
            *taxonomy_terms,
            *content_terms,
            *semantic_terms,
            *intent_use_cases.supported_intents,
            *intent_use_cases.use_cases,
            *intent_use_cases.capabilities,
            *intent_use_cases.restrictions,
        ]
        search_text = self._build_search_text(source_parts)

        return SearchRepresentationBlock(
            search_text=search_text,
            normalized_terms=self._normalized_terms(source_parts),
            aliases=aliases,
            taxonomy_terms=taxonomy_terms,
            content_terms=content_terms,
            semantic_terms=semantic_terms,
            embedding_source_text=search_text,
            representation_version=self._representation_version,
        )

    def _build_search_text(self, values: list[str | None]) -> str:
        return " ".join(self._normalized_unique(values))

    def _normalized_terms(self, values: list[str | None]) -> list[str]:
        tokens: list[str] = []
        seen: set[str] = set()

        for value in values:
            for token in self._normalizer.tokenize(value):
                normalized = self._normalizer.normalize(token)
                if normalized and normalized not in seen:
                    tokens.append(normalized)
                    seen.add(normalized)

        return tokens

    def _taxonomy_terms(
        self,
        semantic_knowledge: SemanticKnowledgeBlock,
    ) -> list[str]:
        return self._normalized_unique(
            [
                concept.canonical_name
                for concept in semantic_knowledge.concepts
                if concept.concept_type.value in {"rubro", "especialidad"}
            ]
        )

    def _semantic_terms(
        self,
        semantic_knowledge: SemanticKnowledgeBlock,
        intent_use_cases: IntentUseCasesBlock,
    ) -> list[str]:
        return self._normalized_unique(
            [
                *[
                    concept.canonical_name
                    for concept in semantic_knowledge.concepts
                    if concept.concept_type.value not in {"rubro", "especialidad"}
                ],
                *semantic_knowledge.capabilities,
                *semantic_knowledge.restrictions,
                *intent_use_cases.supported_intents,
                *intent_use_cases.use_cases,
                *intent_use_cases.capabilities,
                *intent_use_cases.restrictions,
            ]
        )

    def _aliases(self, semantic_knowledge: SemanticKnowledgeBlock) -> list[str]:
        return self._normalized_unique(
            [
                alias
                for concept in semantic_knowledge.concepts
                for alias in concept.aliases
            ]
        )

    def _normalized_unique(self, values: list[str | None]) -> list[str]:
        result: list[str] = []
        seen: set[str] = set()

        for value in values:
            normalized = self._normalizer.normalize(value)
            if normalized and normalized not in seen:
                result.append(normalized)
                seen.add(normalized)

        return result
