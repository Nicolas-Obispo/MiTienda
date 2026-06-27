"""
comercios_schemas.py
-------------------
Schemas Pydantic para Comercios (MiPlaza).

Validan datos de entrada y salida.
No contienen lógica de negocio.
"""

from pydantic import BaseModel, Field, HttpUrl
from typing import Optional


# ============================================================
# Base
# ============================================================

class ComercioBase(BaseModel):
    nombre: str
    descripcion: Optional[str] = None
    portada_url: HttpUrl

    rubro_id: int
    provincia: str
    ciudad: str
    direccion: Optional[str] = None
    latitud: Optional[float] = None
    longitud: Optional[float] = None

    whatsapp: Optional[str] = None
    instagram: Optional[str] = None
    maps_url: Optional[HttpUrl] = None


# ============================================================
# Crear comercio
# ============================================================

class ComercioCreate(ComercioBase):
    rubro_secundario_ids: list[int] = Field(default_factory=list)


# ============================================================
# Actualizar comercio
# ============================================================

class ComercioUpdate(BaseModel):
    nombre: Optional[str] = None
    descripcion: Optional[str] = None
    portada_url: Optional[HttpUrl] = None

    rubro_id: Optional[int] = None
    rubro_secundario_ids: Optional[list[int]] = None
    provincia: Optional[str] = None
    ciudad: Optional[str] = None
    direccion: Optional[str] = None
    latitud: Optional[float] = None
    longitud: Optional[float] = None

    whatsapp: Optional[str] = None
    instagram: Optional[str] = None
    maps_url: Optional[HttpUrl] = None

    activo: Optional[bool] = None


# ============================================================
# Respuesta
# ============================================================

class ComercioResponse(ComercioBase):
    id: int
    usuario_id: int
    activo: bool
    rubro_nombre: Optional[str] = None
    distancia_km: Optional[float] = None

    model_config = {
        "from_attributes": True
    }
