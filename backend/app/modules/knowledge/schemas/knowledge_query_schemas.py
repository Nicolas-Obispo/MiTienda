"""
knowledge_query_schemas.py
--------------------------
Schemas internos para interpretacion de consultas Knowledge.
"""

from pydantic import BaseModel, Field


class KnowledgeQueryInput(BaseModel):
    query_original: str | None = None


class KnowledgeQueryInterpretation(BaseModel):
    query_original: str
    query_normalizada: str
    terminos_expandidos: list[str] = Field(default_factory=list)
    familia_intencion: str | None = None
    terminos_familia: list[str] = Field(default_factory=list)
    taxonomy_node_ids: list[int] = Field(default_factory=list)
    confidence: float = 0.0
    source: str = "none"
    fallback_usado: bool = False
