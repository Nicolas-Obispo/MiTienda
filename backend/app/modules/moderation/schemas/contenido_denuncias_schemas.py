import re
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.modules.moderation.constants import (
    ACCIONES_MODERACION,
    ACCION_OCULTAR_RECURSO,
    ACCION_RESTAURAR_RECURSO,
    MOTIVOS_DECISION_MODERACION,
    MOTIVOS_DENUNCIA,
    RECURSOS_DENUNCIABLES,
)


OPAQUE_EVIDENCE_REFERENCE = re.compile(r"^[A-Za-z0-9_.:-]{1,128}$")
SENSITIVE_EVIDENCE_MARKERS = (
    "authorization", "bearer", "password", "secret", "api_key", "apikey", "token",
)
FORBIDDEN_EVIDENCE_SCHEMES = ("http:", "https:", "file:", "ftp:", "data:")


class ContenidoDenunciaCreate(BaseModel):
    recurso_tipo: str
    recurso_id: int = Field(gt=0)
    motivo: str
    detalle: Optional[str] = Field(default=None, max_length=500)

    model_config = ConfigDict(extra="ignore")

    @field_validator("recurso_tipo")
    @classmethod
    def validar_recurso_tipo(cls, valor: str) -> str:
        if valor not in RECURSOS_DENUNCIABLES:
            raise ValueError("recurso_tipo invalido")
        return valor

    @field_validator("motivo")
    @classmethod
    def validar_motivo(cls, valor: str) -> str:
        if valor not in MOTIVOS_DENUNCIA:
            raise ValueError("motivo invalido")
        return valor

    @field_validator("detalle")
    @classmethod
    def normalizar_detalle(cls, valor: Optional[str]) -> Optional[str]:
        if valor is None:
            return None

        valor_normalizado = valor.strip()
        return valor_normalizado or None


class ContenidoDenunciaResponse(BaseModel):
    id: int
    recurso_tipo: str
    recurso_id: int
    motivo: str
    estado: str
    creado_en: datetime

    model_config = ConfigDict(from_attributes=True)


class ContenidoDenunciaAdminListItem(BaseModel):
    id: int
    recurso_tipo: str
    recurso_id: int
    motivo: str
    estado: str
    creado_en: datetime
    tiene_detalle: bool


class ContenidoDenunciaAdminListResponse(BaseModel):
    items: list[ContenidoDenunciaAdminListItem]
    next_cursor: Optional[str] = None
    has_more: bool


class RecursoDenunciadoActualResponse(BaseModel):
    disponible: bool
    ruta_publica: Optional[str] = None
    moderation_hidden: bool
    moderation_revision: int
    moderation_hidden_by_decision_id: Optional[int] = None


class ContenidoDenunciaAdminDetailResponse(BaseModel):
    id: int
    recurso_tipo: str
    recurso_id: int
    motivo: str
    detalle: Optional[str] = None
    estado: str
    creado_en: datetime
    version: int
    recurso_actual: RecursoDenunciadoActualResponse


class ModerationDecisionCreate(BaseModel):
    accion: str
    motivo_codigo: str
    fundamento: str = Field(min_length=1, max_length=1000)
    evidencia_resumen: str = Field(min_length=1, max_length=1000)
    evidencia_referencia: Optional[str] = Field(default=None, max_length=128)
    expected_denuncia_version: int = Field(ge=1)
    expected_resource_revision: Optional[int] = Field(default=None, ge=0)
    reverses_decision_id: Optional[int] = Field(default=None, gt=0)
    idempotency_key: str = Field(min_length=8, max_length=64, pattern=r"^[A-Za-z0-9._:-]+$")

    model_config = ConfigDict(extra="forbid")

    @field_validator("accion")
    @classmethod
    def validar_accion(cls, value: str) -> str:
        if value not in ACCIONES_MODERACION:
            raise ValueError("accion invalida")
        return value

    @field_validator("motivo_codigo")
    @classmethod
    def validar_motivo_decision(cls, value: str) -> str:
        if value not in MOTIVOS_DECISION_MODERACION:
            raise ValueError("motivo_codigo invalido")
        return value

    @field_validator("fundamento", "evidencia_resumen")
    @classmethod
    def normalizar_texto(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        normalized = value.strip()
        if not normalized:
            raise ValueError("texto obligatorio")
        return normalized

    @field_validator("evidencia_referencia")
    @classmethod
    def validar_referencia_opaca(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        normalized = value.strip()
        lowered = normalized.lower()
        if (
            not OPAQUE_EVIDENCE_REFERENCE.fullmatch(normalized)
            or lowered.startswith(FORBIDDEN_EVIDENCE_SCHEMES)
            or any(marker in lowered for marker in SENSITIVE_EVIDENCE_MARKERS)
        ):
            raise ValueError("evidencia_referencia debe ser una referencia opaca")
        return normalized

    @model_validator(mode="after")
    def validar_contrato_accion(self):
        necesita_revision = self.accion in {ACCION_OCULTAR_RECURSO, ACCION_RESTAURAR_RECURSO}
        if necesita_revision and self.expected_resource_revision is None:
            raise ValueError("expected_resource_revision es obligatorio")
        if self.accion == ACCION_RESTAURAR_RECURSO and self.reverses_decision_id is None:
            raise ValueError("reverses_decision_id es obligatorio")
        if self.accion != ACCION_RESTAURAR_RECURSO and self.reverses_decision_id is not None:
            raise ValueError("reverses_decision_id solo corresponde a restauracion")
        return self


class ModerationDecisionResponse(BaseModel):
    id: int
    denuncia_id: int
    operador_usuario_id: int
    accion: str
    motivo_codigo: str
    fundamento: str
    evidencia_resumen: str
    evidencia_referencia: Optional[str]
    resultado: str
    recurso_tipo: str
    recurso_id: int
    estado_recurso_anterior: str
    estado_recurso_resultante: str
    denuncia_version_resultante: int
    resource_revision_anterior: int
    resource_revision_resultante: int
    reverses_decision_id: Optional[int]
    creado_en: datetime

    model_config = ConfigDict(from_attributes=True)
