"""
comercios_score_routers.py
--------------------------
Endpoints del Space Score Engine
para espacios MiPlaza.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.auth import obtener_usuario_actual

from app.modules.analytics.services.comercios_score_services import (
    calcular_space_score,
)


router = APIRouter(
    prefix="/comercios-score",
    tags=["Comercios Score"],
)


@router.get("/espacios/{comercio_id}")
def obtener_score_espacio(
    comercio_id: int,
    db: Session = Depends(get_db),
    usuario_actual=Depends(obtener_usuario_actual),
):
    """
    Devuelve el score interno del espacio.

    Este score podrá usarse en:
    - ranking
    - explorar
    - feed
    - recomendaciones
    - IA futura
    """

    return calcular_space_score(
        db=db,
        comercio_id=comercio_id,
    )
