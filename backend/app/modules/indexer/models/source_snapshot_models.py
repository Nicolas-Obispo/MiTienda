"""Contratos de snapshots de fuentes para el Indexador."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field, field_validator

from app.modules.knowledge.graph.models.concept_models import Concept
from app.modules.knowledge.graph.models.relation_models import Relation


class SourceSnapshotBase(BaseModel):
    """Snapshot derivado de una fuente oficial."""

    source_name: str
    collected_at: datetime | None = None
    warnings: list[str] = Field(default_factory=list)

    @field_validator("source_name")
    @classmethod
    def _source_name_no_vacio(cls, value: str) -> str:
        source_name = value.strip()
        if not source_name:
            raise ValueError("source_name no puede estar vacio")
        return source_name


class CommerceSourceSnapshot(SourceSnapshotBase):
    """Datos publicos y estado base de un comercio."""

    commerce_id: int = Field(ge=1)
    nombre: str
    descripcion: str | None = None
    activo: bool
    provincia: str | None = None
    ciudad: str | None = None
    direccion: str | None = None
    latitud: float | None = None
    longitud: float | None = None
    rubro_id: int | None = Field(default=None, ge=1)
    created_at: datetime | None = None
    updated_at: datetime | None = None

    @field_validator("nombre")
    @classmethod
    def _nombre_no_vacio(cls, value: str) -> str:
        nombre = value.strip()
        if not nombre:
            raise ValueError("nombre no puede estar vacio")
        return nombre


class TaxonomyNodeSourceSnapshot(BaseModel):
    """Nodo taxonomico disponible para indexacion."""

    id: int = Field(ge=1)
    parent_id: int | None = Field(default=None, ge=1)
    type: str
    slug: str
    nombre: str
    descripcion: str | None = None
    activo: bool
    metadata_json: dict[str, Any] = Field(default_factory=dict)


class TaxonomyAssignmentSourceSnapshot(BaseModel):
    """Asignacion taxonomica de una entidad."""

    id: int = Field(ge=1)
    taxonomy_node_id: int = Field(ge=1)
    entity_type: str
    entity_id: int = Field(ge=1)
    source: str
    confidence: float = Field(ge=0.0, le=1.0)
    principal: bool


class TaxonomySourceSnapshot(SourceSnapshotBase):
    """Snapshot de Taxonomia relevante para un comercio."""

    nodes: list[TaxonomyNodeSourceSnapshot] = Field(default_factory=list)
    assignments: list[TaxonomyAssignmentSourceSnapshot] = Field(default_factory=list)
    primary_assignment_id: int | None = Field(default=None, ge=1)
    legacy_rubro_id: int | None = Field(default=None, ge=1)


class PublicationSourceSnapshot(BaseModel):
    """Publicacion utilizable como fuente de contexto."""

    id: int = Field(ge=1)
    comercio_id: int = Field(ge=1)
    titulo: str
    descripcion: str | None = None
    imagen_url: str | None = None
    is_activa: bool
    created_at: datetime | None = None
    updated_at: datetime | None = None


class StorySourceSnapshot(BaseModel):
    """Historia utilizable como fuente de actividad."""

    id: int = Field(ge=1)
    comercio_id: int = Field(ge=1)
    publicacion_id: int | None = Field(default=None, ge=1)
    media_url: str | None = None
    is_activa: bool
    expira_en: datetime | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


class ContentSourceSnapshot(SourceSnapshotBase):
    """Contenido asociado al comercio."""

    publications: list[PublicationSourceSnapshot] = Field(default_factory=list)
    stories: list[StorySourceSnapshot] = Field(default_factory=list)


class SignalSourceSnapshot(SourceSnapshotBase):
    """Senales agregadas disponibles para indexacion."""

    metrics: dict[str, int | float | str | bool | None] = Field(default_factory=dict)
    activity: dict[str, int | float | str | bool | None] = Field(default_factory=dict)


class KnowledgeGraphSourceSnapshot(SourceSnapshotBase):
    """Vista del Knowledge Graph disponible para el documento."""

    concepts: list[Concept] = Field(default_factory=list)
    relations: list[Relation] = Field(default_factory=list)
