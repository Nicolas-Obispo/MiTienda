# app/schemas/publicaciones_schemas.py
"""
Schemas Pydantic: Publicaciones

Reglas:
- Schemas = validación y serialización
- Sin lógica de negocio
- Compatible Pydantic v2

ETAPA 57:
- Se expone comercio_nombre desde la relación Publicacion.comercio.nombre
- Se agrega imagen_url para permitir devolver media real al frontend
- Se permite recibir imagen_url al crear publicaciones
- Se agregan liked_by_me y guardada_by_me para reflejar
  el estado real del usuario actual en frontend
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, AliasPath


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

    # --------------------------------------------------
    # ETAPA 57:
    # URL opcional de la imagen de la publicación.
    # Se deja opcional para no romper compatibilidad
    # con publicaciones anteriores o sin media.
    # --------------------------------------------------
    imagen_url: Optional[str] = None

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

    Incluye:
    - datos persistidos
    - métricas calculadas
    - nombre real del comercio expuesto para frontend
    - imagen_url real de la publicación
    - estado real del usuario actual

    Métricas calculadas:
    - guardados_count
    - interacciones_count
    - likes_count
    - liked_by_me
    - guardada_by_me
    """

    model_config = ConfigDict(from_attributes=True)

    # --------------------------------------------------
    # Campos persistidos
    # --------------------------------------------------
    id: int
    comercio_id: int
    created_at: datetime
    updated_at: datetime

    # --------------------------------------------------
    # Campo derivado desde la relación ORM:
    # Publicacion.comercio.nombre
    #
    # Esto permite que el frontend reciba directamente:
    # - comercio_nombre
    #
    # y deje de depender del fallback "Comercio #ID"
    # --------------------------------------------------
    comercio_nombre: Optional[str] = Field(
        default=None,
        validation_alias=AliasPath("comercio", "nombre"),
    )

    # --------------------------------------------------
    # Métricas calculadas (no persistidas)
    # --------------------------------------------------
    guardados_count: int = 0
    interacciones_count: int = 0
    likes_count: int = 0

    # --------------------------------------------------
    # Estado del usuario actual respecto a la publicación
    # --------------------------------------------------
    liked_by_me: bool = False
    guardada_by_me: bool = False