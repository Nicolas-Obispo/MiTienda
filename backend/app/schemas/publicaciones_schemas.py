# app/schemas/publicaciones_schemas.py
"""
Schemas Pydantic: Publicaciones

Reglas:
- Schemas = validación y serialización
- Sin lógica de negocio
- Pydantic v1 (migración a v2 pendiente)
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class PublicacionBase(BaseModel):
    """
    Campos comunes a creación y lectura.
    """

    titulo: str
    descripcion: Optional[str] = None
    seccion_id: Optional[int] = None
    is_activa: bool = True


class PublicacionCreate(PublicacionBase):
    """
    Schema para crear una publicación.
    El comercio se obtiene del contexto (no del body).
    """

    pass


class PublicacionRead(PublicacionBase):
    """
    Schema de lectura de publicación.
    """

    id: int
    comercio_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True
