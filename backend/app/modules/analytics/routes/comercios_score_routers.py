"""
comercios_score_routers.py
--------------------------
Endpoints del Space Score Engine
para espacios MiPlaza.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.auth import obtener_usuario_actual
from app.modules.spaces.services.comercios_ownership_services import (
    ComercioNoEncontradoError,
    ComercioUsuarioNoPropietarioError,
    obtener_comercio_propio_o_error,
)

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

    try:
        obtener_comercio_propio_o_error(
            db,
            comercio_id=comercio_id,
            usuario_autenticado=usuario_actual,
        )
    except ComercioNoEncontradoError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ComercioUsuarioNoPropietarioError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc

    return calcular_space_score(
        db=db,
        comercio_id=comercio_id,
    )
