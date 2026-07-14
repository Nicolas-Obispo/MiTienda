"""Contrato de dominio para Relation."""

from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field, field_validator, model_validator

from app.modules.knowledge.graph.models.concept_models import (
    ConceptStatus,
    ConfidenceLevel,
)


class RelationType(StrEnum):
    """Tipos iniciales de relacion."""

    ES_UN = "es_un"
    PERTENECE_A = "pertenece_a"
    OFRECE = "ofrece"
    VENDE = "vende"
    UTILIZA = "utiliza"
    RESUELVE = "resuelve"
    SATISFACE = "satisface"
    REQUIERE = "requiere"
    COMPLEMENTA = "complementa"
    RELACIONADO_CON = "relacionado_con"


class RelationDirection(StrEnum):
    """Direcciones posibles de una relacion."""

    UNIDIRECCIONAL = "unidireccional"
    BIDIRECCIONAL = "bidireccional"


class RelationWeight(StrEnum):
    """Peso estructural base."""

    PRINCIPAL = "principal"
    SECUNDARIA = "secundaria"
    INFERIDA = "inferida"
    EXPERIMENTAL = "experimental"


class Promotability(StrEnum):
    """Promovibilidad conceptual."""

    NO_PROMOVIBLE = "no_promovible"
    EVALUABLE = "evaluable"
    PROMOVIBLE_MEDIANTE_VALIDACION = "promovible_mediante_validacion"
    IDENTIDAD_OFICIAL = "identidad_oficial"


class Relation(BaseModel):
    """Relacion independiente de persistencia fisica."""

    id: int | None = Field(default=None, ge=1)
    source_concept_id: int | None = Field(default=None, ge=1)
    source_entity_type: str | None = None
    source_entity_id: int | None = Field(default=None, ge=1)
    target_concept_id: int | None = Field(default=None, ge=1)
    target_entity_type: str | None = None
    target_entity_id: int | None = Field(default=None, ge=1)
    relation_type: RelationType
    direction: RelationDirection
    confidence: ConfidenceLevel
    base_weight: RelationWeight
    promotability: Promotability
    status: ConceptStatus
    source: str
    evidence: dict[str, Any] = Field(default_factory=dict)
    version: int = Field(ge=1)
    created_at: datetime | None = None
    updated_at: datetime | None = None

    @field_validator("source", "source_entity_type", "target_entity_type")
    @classmethod
    def _normalizar_texto_opcional(cls, value: str | None) -> str | None:
        if value is None:
            return None

        normalizado = value.strip()
        if not normalizado:
            raise ValueError("los campos de texto no pueden estar vacios")
        return normalizado

    @model_validator(mode="after")
    def _validar_extremos(self) -> "Relation":
        source_ref = self._reference(
            concept_id=self.source_concept_id,
            entity_type=self.source_entity_type,
            entity_id=self.source_entity_id,
            label="source",
        )
        target_ref = self._reference(
            concept_id=self.target_concept_id,
            entity_type=self.target_entity_type,
            entity_id=self.target_entity_id,
            label="target",
        )

        if source_ref == target_ref:
            raise ValueError("origen y destino no pueden ser la misma referencia")

        return self

    @staticmethod
    def _reference(
        *,
        concept_id: int | None,
        entity_type: str | None,
        entity_id: int | None,
        label: str,
    ) -> tuple[str, int | str, int | None]:
        has_concept = concept_id is not None
        has_entity_type = entity_type is not None
        has_entity_id = entity_id is not None
        has_entity = has_entity_type or has_entity_id

        if has_concept and has_entity:
            raise ValueError(
                f"{label} no puede tener Concepto y Entidad simultaneamente"
            )

        if has_concept:
            return ("concept", concept_id, None)

        if has_entity_type != has_entity_id:
            raise ValueError(f"{label} requiere entity_type y entity_id")

        if has_entity_type and has_entity_id:
            return ("entity", entity_type or "", entity_id)

        raise ValueError(f"{label} no puede estar vacio")
