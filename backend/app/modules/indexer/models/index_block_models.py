"""Contratos de bloques del Commerce Index Document."""

from typing import Any, Literal

from pydantic import BaseModel, Field

from app.modules.indexer.models.index_evidence_models import (
    IndexEvidence,
    IndexEvidenceRef,
)
from app.modules.indexer.models.index_trace_models import IndexTrace
from app.modules.knowledge.graph.models.concept_models import Concept
from app.modules.knowledge.graph.models.relation_models import Relation


class IdentityBlock(BaseModel):
    """Identidad principal de la entidad indexable."""

    commerce_id: int = Field(ge=1)
    canonical_name: str
    status: Literal["indexable", "not_indexable"]
    primary_taxonomy_concept_id: int | None = Field(default=None, ge=1)
    primary_taxonomy_assignment_id: int | None = Field(default=None, ge=1)
    legacy_rubro_id: int | None = Field(default=None, ge=1)
    identity_confidence: float = Field(ge=0.0, le=1.0)
    evidence_refs: list[IndexEvidenceRef] = Field(default_factory=list)


class PublicProfileBlock(BaseModel):
    """Perfil publico minimo para busqueda y respuesta."""

    display_name: str
    description: str | None = None
    public_location_label: str | None = None
    public_media_refs: list[str] = Field(default_factory=list)
    evidence_refs: list[IndexEvidenceRef] = Field(default_factory=list)


class SemanticKnowledgeBlock(BaseModel):
    """Conocimiento semantico preparado para el comercio."""

    concepts: list[Concept] = Field(default_factory=list)
    relations: list[Relation] = Field(default_factory=list)
    primary_identity_relation_id: int | None = Field(default=None, ge=1)
    secondary_coverage_relation_ids: list[int] = Field(default_factory=list)
    capabilities: list[str] = Field(default_factory=list)
    restrictions: list[str] = Field(default_factory=list)
    semantic_confidence_summary: dict[str, Any] = Field(default_factory=dict)
    evidence_refs: list[IndexEvidenceRef] = Field(default_factory=list)


class SearchRepresentationBlock(BaseModel):
    """Representacion derivada para consumo del buscador."""

    search_text: str
    normalized_terms: list[str] = Field(default_factory=list)
    aliases: list[str] = Field(default_factory=list)
    taxonomy_terms: list[str] = Field(default_factory=list)
    content_terms: list[str] = Field(default_factory=list)
    semantic_terms: list[str] = Field(default_factory=list)
    embedding_source_text: str | None = None
    representation_version: str
    evidence_refs: list[IndexEvidenceRef] = Field(default_factory=list)


class GeographicCoverageBlock(BaseModel):
    """Cobertura geografica base del comercio."""

    province: str | None = None
    city: str | None = None
    address_public: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    coverage_mode: str | None = None
    evidence_refs: list[IndexEvidenceRef] = Field(default_factory=list)


class DerivedContextBlock(BaseModel):
    """Contexto derivado de contenido y actividad."""

    active_publication_refs: list[int] = Field(default_factory=list)
    active_story_refs: list[int] = Field(default_factory=list)
    recent_activity_summary: dict[str, Any] = Field(default_factory=dict)
    content_coverage_terms: list[str] = Field(default_factory=list)
    evidence_refs: list[IndexEvidenceRef] = Field(default_factory=list)


class SignalsBlock(BaseModel):
    """Senales agregadas y livianas."""

    activity_signals: dict[str, int | float | str | bool | None] = Field(
        default_factory=dict
    )
    engagement_signals: dict[str, int | float | str | bool | None] = Field(
        default_factory=dict
    )
    freshness_signals: dict[str, int | float | str | bool | None] = Field(
        default_factory=dict
    )
    quality_signals: dict[str, int | float | str | bool | None] = Field(
        default_factory=dict
    )
    evidence_refs: list[IndexEvidenceRef] = Field(default_factory=list)


class IntentUseCasesBlock(BaseModel):
    """Intenciones y casos de uso soportados."""

    supported_intents: list[str] = Field(default_factory=list)
    use_cases: list[str] = Field(default_factory=list)
    capabilities: list[str] = Field(default_factory=list)
    restrictions: list[str] = Field(default_factory=list)
    evidence_refs: list[IndexEvidenceRef] = Field(default_factory=list)


class EvidencesBlock(BaseModel):
    """Evidencias consolidadas del documento."""

    items: list[IndexEvidence] = Field(default_factory=list)


class TraceabilityBlock(BaseModel):
    """Trazabilidad y versionado del documento."""

    trace: IndexTrace


class CommerceIndexBlocks(BaseModel):
    """Conjunto completo de bloques del Commerce Index Document."""

    identity: IdentityBlock
    public_profile: PublicProfileBlock
    semantic_knowledge: SemanticKnowledgeBlock
    search_representation: SearchRepresentationBlock
    geographic_coverage: GeographicCoverageBlock
    derived_context: DerivedContextBlock
    signals: SignalsBlock
    intent_use_cases: IntentUseCasesBlock
    evidences: EvidencesBlock
    traceability: TraceabilityBlock
