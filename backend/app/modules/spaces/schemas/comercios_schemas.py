"""
comercios_schemas.py
-------------------
Schemas Pydantic para Comercios (MiPlaza).

Validan datos de entrada y salida.
No contienen lógica de negocio.
"""

from pydantic import BaseModel, HttpUrl
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

    whatsapp: Optional[str] = None
    instagram: Optional[str] = None
    maps_url: Optional[HttpUrl] = None


# ============================================================
# Crear comercio
# ============================================================

class ComercioCreate(ComercioBase):
    pass


# ============================================================
# Actualizar comercio
# ============================================================

class ComercioUpdate(BaseModel):
    nombre: Optional[str] = None
    descripcion: Optional[str] = None
    portada_url: Optional[HttpUrl] = None

    rubro_id: Optional[int] = None
    provincia: Optional[str] = None
    ciudad: Optional[str] = None
    direccion: Optional[str] = None

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

    class Config:
        orm_mode = True
