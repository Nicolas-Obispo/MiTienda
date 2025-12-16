# app/routers/likes_publicaciones_routers.py
"""
Router HTTP: Likes en Publicaciones

Reglas:
- Routers = solo HTTP
- Like = señal de interés (NO social)
- Toggle (crear / eliminar)
"""

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.auth import obtener_usuario_actual
from app.services.likes_publicaciones_services import toggle_like_publicacion

router = APIRouter(
    prefix="/likes/publicaciones",
    tags=["Likes"],
)


@router.post(
    "/{publicacion_id}",
    status_code=status.HTTP_200_OK,
)
def toggle_like_publicacion_endpoint(
    publicacion_id: int,
    db: Session = Depends(get_db),
    usuario=Depends(obtener_usuario_actual),

):
    """
    Da o quita like a una publicación (toggle).
    """

    liked = toggle_like_publicacion(
        db,
        usuario_id=usuario.id,
        publicacion_id=publicacion_id,
    )

    return {
        "liked": liked
    }
