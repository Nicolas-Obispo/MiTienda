# app/routers/ranking_publicaciones_routers.py
"""
Router HTTP: Ranking de Publicaciones

Reglas:
- Routers = solo HTTP
- Ranking basado en likes + recencia
- Endpoint de solo lectura
"""

from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.publicaciones_schemas import PublicacionRead
from app.services.ranking_publicaciones_services import (
    listar_publicaciones_ranked,
)

router = APIRouter(
    prefix="/ranking/publicaciones",
    tags=["Ranking"],
)


@router.get(
    "",
    response_model=List[PublicacionRead],
)
def obtener_publicaciones_ranked(
    db: Session = Depends(get_db),
):
    """
    Devuelve publicaciones ordenadas por ranking (likes + recencia).
    """

    return listar_publicaciones_ranked(db)
