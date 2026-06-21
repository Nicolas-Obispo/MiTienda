"""
Schemas Pydantic para publicaciones guardadas.

Estos schemas se utilizan para:
- Validar requests
- Serializar respuestas
- Listar publicaciones guardadas por un usuario

No contienen lógica de negocio.
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class PublicacionGuardadaCreate(BaseModel):
    """
    Schema para guardar una publicación.

    Se recibe únicamente el ID de la publicación.
    El usuario se obtiene desde el token JWT.
    """
    publicacion_id: int


class PublicacionGuardadaResponse(BaseModel):
    """
    Schema de respuesta básica al guardar una publicación.
    """
    id: int
    publicacion_id: int
    created_at: datetime

    model_config = {
        "from_attributes": True
    }


class PublicacionGuardadaPublicacion(BaseModel):
    """
    Datos de la publicacion guardada listos para renderizar cards.
    """
    id: int
    publicacion_id: int
    comercio_id: int
    comercio_nombre: Optional[str] = None
    titulo: str
    descripcion: Optional[str] = None
    seccion_id: Optional[int] = None
    imagen_url: Optional[str] = None
    is_activa: bool
    created_at: datetime
    updated_at: datetime
    likes_count: int = 0
    guardados_count: int = 0
    interacciones_count: int = 0
    liked_by_me: bool = False
    guardada_by_me: bool = True

    model_config = {
        "from_attributes": True
    }


class PublicacionGuardadaListado(BaseModel):
    """
    Schema para listar publicaciones guardadas por el usuario.

    Incluye información mínima de la publicación
    (se puede ampliar más adelante si es necesario).
    """
    publicacion_id: int
    created_at: datetime
    publicacion: Optional[PublicacionGuardadaPublicacion] = None

    model_config = {
        "from_attributes": True
    }
