# app/routers/historias_routers.py
"""
Router HTTP: Historias

Reglas:
- Routers = solo HTTP
- Sin lógica de negocio
- Delegan en services
"""

from typing import List

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.historias_schemas import (
    HistoriaCreate,
    HistoriaRead,
)
from app.services.historias_services import (
    crear_historia,
    listar_historias_activas_por_comercio,
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
