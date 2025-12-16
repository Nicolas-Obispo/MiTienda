# app/routers/feed_publicaciones_routers.py
"""
Router HTTP: Feed personalizado de Publicaciones

Reglas:
- Routers = solo HTTP
- Feed orientado a descubrimiento
- Usa ranking + liked_by_me
"""

from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.auth import obtener_usuario_actual
from app.schemas.publicaciones_schemas import PublicacionRead
from app.services.feed_publicaciones_services import obtener_feed_publicaciones

router = APIRouter(
    prefix="/feed/publicaciones",
    tags=["Feed"],
)


@router.get(
    "",
    response_model=List[PublicacionRead],
)
def obtener_feed_publicaciones_endpoint(
    db: Session = Depends(get_db),
    usuario=Depends(obtener_usuario_actual),
):
    """
    Devuelve el feed personalizado de publicaciones.
    """

    return obtener_feed_publicaciones(
        db,
        usuario_id=usuario.id,
    )
