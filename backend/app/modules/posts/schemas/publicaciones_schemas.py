# app/schemas/publicaciones_schemas.py

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

    # Imagen opcional
    imagen_url: Optional[str] = None

    is_activa: bool = True


class PublicacionCreate(PublicacionBase):
    """
    Schema para crear una publicación.
    """
    pass


# --------------------------------------------------
# Schema de lectura
# --------------------------------------------------

class PublicacionRead(PublicacionBase):
    """
    Schema de lectura de publicación.

    Incluye:
    - datos persistidos
    - métricas calculadas
    - nombre real del comercio
    - estado del usuario
    """

    model_config = ConfigDict(from_attributes=True)

    # Persistidos
    id: int
    comercio_id: int
    created_at: datetime
    updated_at: datetime

    # 👇 CORREGIDO: ahora lo toma directo del router
    comercio_nombre: Optional[str] = None

    # Métricas
    guardados_count: int = 0
    interacciones_count: int = 0
    likes_count: int = 0

    # Estado usuario
    liked_by_me: bool = False
    guardada_by_me: bool = False