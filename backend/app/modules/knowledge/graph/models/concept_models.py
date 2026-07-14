"""Contrato de dominio para Concept."""

from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field, field_validator


class ConceptType(StrEnum):
    """Tipos conceptuales iniciales."""

    RUBRO = "rubro"
    ESPECIALIDAD = "especialidad"
    SERVICIO = "servicio"
    PRODUCTO = "producto"
    MARCA = "marca"
    MATERIAL = "material"
    PROBLEMA = "problema"
    NECESIDAD = "necesidad"
    INTENCION = "intencion"
    ACCION = "accion"
    ATRIBUTO = "atributo"


class ConceptStatus(StrEnum):
    """Estados conceptuales iniciales."""

    DETECTADO = "detectado"
    PROPUESTO = "propuesto"
    VALIDADO = "validado"
    OFICIAL = "oficial"
    DEPRECADO = "deprecado"


class ConfidenceLevel(StrEnum):
    """Niveles conceptuales de confianza."""

    MUY_ALTA = "muy_alta"
    ALTA = "alta"
    MEDIA = "media"
    BAJA = "baja"
    EXPERIMENTAL = "experimental"


class Concept(BaseModel):
    """Concepto independiente de persistencia física."""

    id: int | None = Field(default=None, ge=1)
    canonical_name: str
    concept_type: ConceptType
    description: str | None = None
    status: ConceptStatus
    confidence: ConfidenceLevel
    version: int = Field(ge=1)
    aliases: list[str] = Field(default_factory=list)
    source: str
    evidence: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime | None = None
    updated_at: datetime | None = None

    @field_validator("canonical_name")
    @classmethod
    def _canonical_name_no_vacio(cls, value: str) -> str:
        nombre = value.strip()
        if not nombre:
            raise ValueError("canonical_name no puede estar vacío")
        return nombre

    @field_validator("source")
    @classmethod
    def _source_no_vacio(cls, value: str) -> str:
        source = value.strip()
        if not source:
            raise ValueError("source no puede estar vacío")
        return source

    @field_validator("aliases")
    @classmethod
    def _normalizar_aliases(cls, aliases: list[str]) -> list[str]:
        normalizados: list[str] = []
        vistos: set[str] = set()

        for alias in aliases:
            alias_normalizado = alias.strip()
            if not alias_normalizado:
                continue

            dedupe_key = alias_normalizado.lower()
            if dedupe_key in vistos:
                continue

            normalizados.append(alias_normalizado)
            vistos.add(dedupe_key)

        return normalizados
