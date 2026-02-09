# app/routers/historias_routers.py
"""
Router HTTP: Historias

Reglas:
- Routers = solo HTTP
- Sin lógica de negocio
- Delegan en services
"""

from typing import List

from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.auth import obtener_usuario_actual
from app.schemas.historias_schemas import (
    HistoriaCreate,
    HistoriaRead,
)
from app.services.historias_services import (
    crear_historia,
    listar_historias_activas_por_comercio,
)
from app.services.historias_vistas_services import (
    marcar_historia_como_vista,
)

router = APIRouter(
    prefix="/historias",
    tags=["Historias"],
)


@router.post(
    "/comercios/{comercio_id}",
    response_model=HistoriaRead,
    status_code=status.HTTP_201_CREATED,
)
def crear_historia_endpoint(
    comercio_id: int,
    historia_in: HistoriaCreate,
    db: Session = Depends(get_db),
):
    """
    Crea una historia para un comercio.
    """

    return crear_historia(
        db,
        comercio_id=comercio_id,
        historia_in=historia_in,
    )


@router.get(
    "/comercios/{comercio_id}",
    response_model=List[HistoriaRead],
)
def listar_historias_por_comercio_endpoint(
    comercio_id: int,
    db: Session = Depends(get_db),
):
    """
    Lista historias activas y no expiradas de un comercio.
    """

    return listar_historias_activas_por_comercio(
        db,
        comercio_id=comercio_id,
    )


# ------------------------------------------------------------------
# VISTAS DE HISTORIAS (ETAPA 43)
# ------------------------------------------------------------------

@router.post(
    "/{historia_id}/vistas",
    status_code=status.HTTP_201_CREATED,
)
def marcar_historia_vista_endpoint(
    historia_id: int,
    db: Session = Depends(get_db),
    usuario_actual=Depends(obtener_usuario_actual),
):
    """
    Marca una historia como vista por el usuario autenticado.

    - Idempotente: si ya fue vista, no duplica.
    - Devuelve 201 y {"ok": true}.
    """

    try:
        marcar_historia_como_vista(
            db,
            historia_id=historia_id,
            usuario_id=usuario_actual.id,
        )
        return {"ok": True}
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
