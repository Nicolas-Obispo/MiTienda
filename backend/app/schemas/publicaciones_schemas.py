# app/schemas/publicaciones_schemas.py
"""
Schemas Pydantic: Publicaciones

Reglas:
- Schemas = validación y serialización
- Sin lógica de negocio
- Compatible Pydantic v2
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


# --------------------------------------------------
# Schemas base
# --------------------------------------------------

class PublicacionBase(BaseModel):
    """
    Campos comunes a creación y lectura de publicaciones.
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


# --------------------------------------------------
# Schema de lectura
# --------------------------------------------------

class PublicacionRead(PublicacionBase):
    """
    Schema de lectura de publicación.

    Incluye métricas calculadas:
    - guardados_count
    - interacciones_count
    - likes_count
    - liked_by_me
    """

    model_config = ConfigDict(from_attributes=True)

    id: int
    comercio_id: int
    created_at: datetime
    updated_at: datetime

    # Métricas calculadas (no persistidas)
    guardados_count: int = 0
    interacciones_count: int = 0
    likes_count: int = 0
    liked_by_me: bool = False
