"""Builder del bloque Intenciones y Casos de Uso."""

from app.modules.indexer.models.index_block_models import (
    DerivedContextBlock,
    IntentUseCasesBlock,
    SemanticKnowledgeBlock,
)


class IntentUseCaseBuilder:
    """Construye intenciones y casos de uso desde bloques preparados."""

    def build(
        self,
        *,
        semantic_knowledge: SemanticKnowledgeBlock,
        derived_context: DerivedContextBlock,
    ) -> IntentUseCasesBlock:
        """Construye el bloque sin interpretar consultas de usuario."""

        capabilities = self._unique(
            [
                *semantic_knowledge.capabilities,
                *self._terms_as_capabilities(derived_context.content_coverage_terms),
            ]
        )
        restrictions = self._unique(semantic_knowledge.restrictions)

        return IntentUseCasesBlock(
            supported_intents=capabilities,
            use_cases=self._unique(derived_context.content_coverage_terms),
            capabilities=capabilities,
            restrictions=restrictions,
        )

    @staticmethod
    def _terms_as_capabilities(terms: list[str]) -> list[str]:
        return [term for term in terms if term.strip()]

    @staticmethod
    def _unique(values: list[str]) -> list[str]:
        result: list[str] = []
        seen: set[str] = set()

        for value in values:
            normalized = value.strip()
            key = normalized.lower()
            if normalized and key not in seen:
                result.append(normalized)
                seen.add(key)

        return result
