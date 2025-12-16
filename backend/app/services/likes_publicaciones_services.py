# app/services/likes_publicaciones_services.py
"""
Service: Likes de Publicaciones

Reglas:
- Like = señal de interés (NO social)
- Toggle: si existe se elimina, si no existe se crea
- Un like por usuario y publicación
"""

from typing import Optional

from sqlalchemy.orm import Session

from app.models.likes_publicaciones_models import LikePublicacion


def toggle_like_publicacion(
    db: Session,
    *,
    usuario_id: int,
    publicacion_id: int,
) -> bool:
    """
    Alterna el like de un usuario sobre una publicación.

    Retorna:
    - True  -> like creado
    - False -> like eliminado
    """

    like_existente: Optional[LikePublicacion] = (
        db.query(LikePublicacion)
        .filter(
            LikePublicacion.usuario_id == usuario_id,
            LikePublicacion.publicacion_id == publicacion_id,
        )
        .first()
    )

    if like_existente:
        db.delete(like_existente)
        db.commit()
        return False

    nuevo_like = LikePublicacion(
        usuario_id=usuario_id,
        publicacion_id=publicacion_id,
    )

    db.add(nuevo_like)
    db.commit()

    return True
