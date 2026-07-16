"""Contratos de trazabilidad del proceso de indexacion."""

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, Field, field_validator


class IndexValidationStatus(StrEnum):
    """Estados de validacion del documento."""

    VALID = "valid"
    INVALID = "invalid"


class IndexValidationSeverity(StrEnum):
    """Severidad de un hallazgo de validacion."""

    WARNING = "warning"
    ERROR = "error"


class SourceTrace(BaseModel):
    """Fuente utilizada por el proceso de indexacion."""

    source_name: str
    source_id: int | str | None = None
    source_version: str | None = None
    updated_at: datetime | None = None


class BuilderTrace(BaseModel):
    """Version de un builder utilizado."""

    builder_name: str
    builder_version: str

    @field_validator("builder_name", "builder_version")
    @classmethod
    def _texto_no_vacio(cls, value: str) -> str:
        text = value.strip()
        if not text:
            raise ValueError("los campos de texto no pueden estar vacios")
        return text


class IndexValidationIssue(BaseModel):
    """Hallazgo de validacion del documento."""

    code: str
    message: str
    severity: IndexValidationSeverity
    block_name: str | None = None


class IndexValidationResult(BaseModel):
    """Resultado de validacion del documento."""

    status: IndexValidationStatus
    issues: list[IndexValidationIssue] = Field(default_factory=list)


class IndexTrace(BaseModel):
    """Trazabilidad general de una reconstruccion."""

    indexing_started_at: datetime | None = None
    indexing_finished_at: datetime | None = None
    source_traces: list[SourceTrace] = Field(default_factory=list)
    builder_traces: list[BuilderTrace] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    validation_result: IndexValidationResult | None = None
