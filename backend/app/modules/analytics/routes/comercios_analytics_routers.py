"""
comercios_analytics_routers.py
------------------------------
Endpoints de analytics e insights
de espacios MiPlaza.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.auth import obtener_usuario_actual

from app.modules.analytics.services.comercios_analytics_services import (
    obtener_analytics_espacio,
)


router = APIRouter(
    prefix="/comercios-analytics",
    tags=["Comercios Analytics"],
)


@router.get("/espacios/{comercio_id}")
def obtener_analytics_completo_espacio(
    comercio_id: int,
    db: Session = Depends(get_db),
    usuario_actual=Depends(obtener_usuario_actual),
):
    """
    Devuelve analytics completos del espacio:
    - métricas
    - métricas derivadas
    - comparaciones
    - insights
    """

    return obtener_analytics_espacio(
        db=db,
        comercio_id=comercio_id,
    )
