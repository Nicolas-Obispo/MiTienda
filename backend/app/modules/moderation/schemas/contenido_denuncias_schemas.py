from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.modules.moderation.constants import (
    MOTIVOS_DENUNCIA,
    RECURSOS_DENUNCIABLES,
)


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
