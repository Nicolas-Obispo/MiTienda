"""
query_interpreter_services.py
-----------------------------
Fachada interna para interpretacion de queries desde Knowledge Core.
"""

from typing import TYPE_CHECKING

from app.modules.knowledge.schemas.knowledge_query_schemas import (
    KnowledgeQueryInterpretation,
)
from app.modules.knowledge.services.knowledge_legacy_adapter_services import (
    interpretar_intencion_legacy,
)

if TYPE_CHECKING:
    from sqlalchemy.orm import Session


def _normalizar_query(query: str | None) -> str:
    if not query:
        return ""
    return query.strip().lower()


def interpretar_query_knowledge(
    db: "Session",
    query: str | None,
) -> KnowledgeQueryInterpretation:
    """
    Interpreta una query sin modificar Discovery ni ranking.

    En esta etapa, Knowledge Core solo encapsula el comportamiento legacy.
    """
    _ = db
    query_original = query or ""
    query_normalizada = _normalizar_query(query_original)
    legacy = interpretar_intencion_legacy(query_normalizada)

    confidence = 1.0 if legacy.tiene_intencion_conocida else 0.0

    return KnowledgeQueryInterpretation(
        query_original=query_original,
        query_normalizada=query_normalizada,
        terminos_expandidos=legacy.terminos_expandidos,
        familia_intencion=legacy.familia_intencion,
        terminos_familia=legacy.terminos_familia,
        taxonomy_node_ids=[],
        confidence=confidence,
        source=legacy.source,
        fallback_usado=legacy.fallback_usado,
    )
