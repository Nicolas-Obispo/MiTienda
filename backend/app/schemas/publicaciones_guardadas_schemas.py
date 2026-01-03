"""
Schemas Pydantic para publicaciones guardadas.

Estos schemas se utilizan para:
- Validar requests
- Serializar respuestas
- Listar publicaciones guardadas por un usuario

No contienen lógica de negocio.
"""

from datetime import datetime
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

    class Config:
        orm_mode = True


class PublicacionGuardadaListado(BaseModel):
    """
    Schema para listar publicaciones guardadas por el usuario.

    Incluye información mínima de la publicación
    (se puede ampliar más adelante si es necesario).
    """
    publicacion_id: int
    created_at: datetime

    class Config:
        orm_mode = True
