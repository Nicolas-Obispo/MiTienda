"""
comercios_schemas.py
-------------------
Schemas Pydantic para Comercios (MiPlaza).

Validan datos de entrada y salida.
No contienen lógica de negocio.
"""

from math import isfinite

from pydantic import BaseModel, Field, HttpUrl, field_validator, model_validator
from typing import Optional

from app.modules.availability.schemas.horarios_atencion_schemas import (
    EstadoHorarioResponse,
)


# ============================================================
# Base
# ============================================================

def _validar_portada_url(valor: str | None, *, requerido: bool) -> str | None:
    if valor is None:
        if requerido:
            raise ValueError("portada_url es requerida")
        return None

    valor_normalizado = str(valor).strip()

    if not valor_normalizado:
        if requerido:
            raise ValueError("portada_url es requerida")
        return None

    if (
        valor_normalizado.startswith("http://")
        or valor_normalizado.startswith("https://")
        or valor_normalizado.startswith("/uploads/")
    ):
        return valor_normalizado

    raise ValueError("portada_url debe ser una URL absoluta o una ruta /uploads/")


def _validar_coordenada(
    valor: float | None,
    *,
    nombre: str,
    minimo: float,
    maximo: float,
) -> float | None:
    if valor is None:
        return None

    valor_numerico = float(valor)
    if not isfinite(valor_numerico):
        raise ValueError(f"{nombre} debe ser un valor finito")
    if not minimo <= valor_numerico <= maximo:
        raise ValueError(f"{nombre} debe estar entre {minimo:g} y {maximo:g}")
    return valor_numerico


class ComercioBase(BaseModel):
    nombre: str
    descripcion: Optional[str] = None
    portada_url: str

    rubro_id: int
    provincia: str
    ciudad: str
    direccion: Optional[str] = None
    latitud: Optional[float] = None
    longitud: Optional[float] = None

    whatsapp: Optional[str] = None
    instagram: Optional[str] = None
    maps_url: Optional[HttpUrl] = None
    mostrar_direccion_publicamente: bool = True

    @field_validator("portada_url")
    @classmethod
    def validar_portada_url(cls, valor):
        return _validar_portada_url(valor, requerido=True)

    @field_validator("latitud")
    @classmethod
    def validar_latitud(cls, valor):
        return _validar_coordenada(
            valor,
            nombre="latitud",
            minimo=-90,
            maximo=90,
        )

    @field_validator("longitud")
    @classmethod
    def validar_longitud(cls, valor):
        return _validar_coordenada(
            valor,
            nombre="longitud",
            minimo=-180,
            maximo=180,
        )


# ============================================================
# Crear comercio
# ============================================================

class ComercioCreate(ComercioBase):
    direccion: str
    latitud: float
    longitud: float
    rubro_secundario_ids: list[int] = Field(default_factory=list)
    especialidad_ids: list[int] = Field(default_factory=list)

    @model_validator(mode="after")
    def validar_ubicacion_completa(self):
        for campo in ("provincia", "ciudad", "direccion"):
            valor = getattr(self, campo)
            if not valor or not valor.strip():
                raise ValueError(f"{campo} es requerido para crear un comercio")
            setattr(self, campo, valor.strip())
        return self


# ============================================================
# Actualizar comercio
# ============================================================

class ComercioUpdate(BaseModel):
    nombre: Optional[str] = None
    descripcion: Optional[str] = None
    portada_url: Optional[str] = None

    rubro_id: Optional[int] = None
    rubro_secundario_ids: Optional[list[int]] = None
    especialidad_ids: Optional[list[int]] = None
    provincia: Optional[str] = None
    ciudad: Optional[str] = None
    direccion: Optional[str] = None
    latitud: Optional[float] = None
    longitud: Optional[float] = None

    whatsapp: Optional[str] = None
    instagram: Optional[str] = None
    maps_url: Optional[HttpUrl] = None
    mostrar_direccion_publicamente: Optional[bool] = None

    activo: Optional[bool] = None

    @field_validator("portada_url")
    @classmethod
    def validar_portada_url(cls, valor):
        return _validar_portada_url(valor, requerido=False)

    @field_validator("latitud")
    @classmethod
    def validar_latitud(cls, valor):
        return _validar_coordenada(
            valor,
            nombre="latitud",
            minimo=-90,
            maximo=90,
        )

    @field_validator("longitud")
    @classmethod
    def validar_longitud(cls, valor):
        return _validar_coordenada(
            valor,
            nombre="longitud",
            minimo=-180,
            maximo=180,
        )


# ============================================================
# Respuesta
# ============================================================

class ComercioResponseBase(ComercioBase):
    id: int
    activo: bool
    rubro_nombre: Optional[str] = None
    especialidad_ids: list[int] = Field(default_factory=list)
    distancia_km: Optional[float] = None
    horario_atencion: Optional[EstadoHorarioResponse] = None
    es_propietario: bool = False

    model_config = {
        "from_attributes": True
    }


class ComercioPublicResponse(ComercioResponseBase):
    @model_validator(mode="after")
    def ocultar_ubicacion_privada(self):
        if not self.mostrar_direccion_publicamente:
            self.direccion = None
            self.latitud = None
            self.longitud = None
            self.maps_url = None
            self.distancia_km = None
        return self


class ComercioResponse(ComercioResponseBase):
    usuario_id: int
