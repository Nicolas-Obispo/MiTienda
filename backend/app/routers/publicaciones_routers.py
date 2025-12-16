# app/routers/publicaciones_routers.py
"""
Router HTTP: Publicaciones

Reglas:
- Routers = solo HTTP
- Sin lógica de negocio
- Llaman a services
"""

from typing import List

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from app.services.publicaciones_services import obtener_publicacion_por_id_y_sumar_view


from app.core.database import get_db
from app.schemas.publicaciones_schemas import (
    PublicacionCreate,
    PublicacionRead,
)
from app.services.publicaciones_services import (
    crear_publicacion,
    listar_publicaciones_por_comercio,
)

router = APIRouter(
    prefix="/publicaciones",
    tags=["Publicaciones"],
)


@router.post(
    "/comercios/{comercio_id}",
    response_model=PublicacionRead,
    status_code=status.HTTP_201_CREATED,
)
def crear_publicacion_endpoint(
    comercio_id: int,
    publicacion_in: PublicacionCreate,
    db: Session = Depends(get_db),
):
    """
    Crea una publicación para un comercio.
    """

    return crear_publicacion(
        db,
        comercio_id=comercio_id,
        publicacion_in=publicacion_in,
    )


@router.get(
    "/comercios/{comercio_id}",
    response_model=List[PublicacionRead],
)
def listar_publicaciones_por_comercio_endpoint(
    comercio_id: int,
    db: Session = Depends(get_db),
):
    """
    Lista publicaciones de un comercio.
    """

    return listar_publicaciones_por_comercio(
        db,
        comercio_id=comercio_id,
    )

@router.get(
    "/{publicacion_id}",
    response_model=PublicacionRead,
)
def obtener_publicacion_detalle_endpoint(
    publicacion_id: int,
    db: Session = Depends(get_db),
):
    """
    Devuelve el detalle de una publicación e incrementa su contador de vistas.
    """

    publicacion = obtener_publicacion_por_id_y_sumar_view(
        db,
        publicacion_id=publicacion_id,
    )

    if not publicacion:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Publicación no encontrada")

    return publicacion
