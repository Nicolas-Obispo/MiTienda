"""
secciones_schemas.py
--------------------
Schemas Pydantic para Secciones de Comercios.

Una Sección organiza publicaciones dentro de un comercio.
"""

from pydantic import BaseModel
from typing import Optional


# =========================
# Schema de creación
# =========================
class SeccionCreate(BaseModel):
    comercio_id: int
    nombre: str
    descripcion: Optional[str] = None
    orden: int = 0


# =========================
# Schema de actualización
# =========================
class SeccionUpdate(BaseModel):
    nombre: Optional[str] = None
    descripcion: Optional[str] = None
    orden: Optional[int] = None
    activo: Optional[bool] = None


# =========================
# Schema de respuesta
# =========================
class SeccionResponse(BaseModel):
    id: int
    comercio_id: int
    nombre: str
    descripcion: Optional[str]
    orden: int
    activo: bool

    class Config:
        orm_mode = True  # (pendiente migrar a Pydantic v2)
