"""
comercios_schemas.py
-------------------
Schemas Pydantic para Comercios (MiPlaza).

Validan datos de entrada y salida.
No contienen lógica de negocio.
"""

from pydantic import BaseModel, Field, HttpUrl, field_validator
from typing import Optional


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

    @field_validator("portada_url")
    @classmethod
    def validar_portada_url(cls, valor):
        return _validar_portada_url(valor, requerido=True)


# ============================================================
# Crear comercio
# ============================================================

class ComercioCreate(ComercioBase):
    rubro_secundario_ids: list[int] = Field(default_factory=list)
    especialidad_ids: list[int] = Field(default_factory=list)


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

    activo: Optional[bool] = None

    @field_validator("portada_url")
    @classmethod
    def validar_portada_url(cls, valor):
        return _validar_portada_url(valor, requerido=False)


# ============================================================
# Respuesta
# ============================================================

class ComercioResponse(ComercioBase):
    id: int
    usuario_id: int
    activo: bool
    rubro_nombre: Optional[str] = None
    especialidad_ids: list[int] = Field(default_factory=list)
    distancia_km: Optional[float] = None

    model_config = {
        "from_attributes": True
    }
