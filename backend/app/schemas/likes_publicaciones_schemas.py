# app/schemas/likes_publicaciones_schemas.py
"""
Schemas Pydantic: Likes de Publicaciones

Reglas:
- Like = señal de interés (NO social)
- Input mínimo
- Output controlado
- Pydantic v1 (migración a v2 pendiente)
"""

from datetime import datetime

from pydantic import BaseModel


class LikePublicacionBase(BaseModel):
    """
    Base común (no expone IDs sensibles).
    """
    pass


class LikePublicacionCreate(LikePublicacionBase):
    """
    Schema para dar like.
    El usuario y la publicación se obtienen del contexto.
    """
    pass


class LikePublicacionRead(BaseModel):
    """
    Schema de lectura de un like.
    """
    id: int
    usuario_id: int
    publicacion_id: int
    created_at: datetime

    class Config:
        orm_mode = True
