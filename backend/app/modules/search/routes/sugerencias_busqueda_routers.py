"""
sugerencias_busqueda_routers.py
-------------------------------
Rutas publicas para sugerencias predictivas del buscador.
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.modules.search.schemas.sugerencias_busqueda_schemas import (
    SugerenciasBusquedaResponse,
)
from app.modules.search.services.sugerencias_busqueda_services import (
    obtener_sugerencias_busqueda,
)


router = APIRouter(
    prefix="/buscar",
    tags=["Buscar"],
)


@router.get("/sugerencias", response_model=SugerenciasBusquedaResponse)
def obtener_sugerencias_busqueda_endpoint(
    q: str | None = Query(default=None, description="Texto de busqueda"),
    limit: int = Query(default=5, ge=1, le=10, description="Maximo de sugerencias"),
    db: Session = Depends(get_db),
):
    return obtener_sugerencias_busqueda(
        db=db,
        q=q,
        limit=limit,
    )
