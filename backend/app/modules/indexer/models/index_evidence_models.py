"""Contratos de evidencias del Documento de Indice."""

from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field, field_validator


class EvidenceSourceType(StrEnum):
    """Fuentes posibles de evidencia."""

    COMMERCE = "commerce"
    TAXONOMY_NODE = "taxonomy_node"
    TAXONOMY_ASSIGNMENT = "taxonomy_assignment"
    PUBLICATION = "publication"
    STORY = "story"
    KNOWLEDGE_GRAPH = "knowledge_graph"
    SIGNAL = "signal"
    INDEXER = "indexer"


class IndexEvidenceRef(BaseModel):
    """Referencia liviana a una evidencia."""

    evidence_id: str

    @field_validator("evidence_id")
    @classmethod
    def _evidence_id_no_vacio(cls, value: str) -> str:
        evidence_id = value.strip()
        if not evidence_id:
            raise ValueError("evidence_id no puede estar vacio")
        return evidence_id


class IndexEvidence(BaseModel):
    """Evidencia usada para construir una decision del documento."""

    evidence_id: str
    source_type: EvidenceSourceType
    source_id: int | str | None = None
    source_field: str | None = None
    claim: str
    confidence: float = Field(ge=0.0, le=1.0)
    weight: float = Field(default=1.0, ge=0.0)
    sensitive: bool = False
    created_at: datetime | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("evidence_id", "claim")
    @classmethod
    def _texto_no_vacio(cls, value: str) -> str:
        text = value.strip()
        if not text:
            raise ValueError("los campos de texto no pueden estar vacios")
        return text

    @field_validator("sensitive")
    @classmethod
    def _evidencia_no_sensible(cls, value: bool) -> bool:
        if value:
            raise ValueError("la evidencia del indice no puede ser sensible")
        return value
