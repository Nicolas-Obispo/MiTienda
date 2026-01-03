"""
Router HTTP para publicaciones guardadas.

Responsabilidades:
- Exponer endpoints
- Validar autenticación
- Delegar la lógica al service
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.auth import obtener_usuario_actual
from app.schemas.publicaciones_guardadas_schemas import (
    PublicacionGuardadaCreate,
    PublicacionGuardadaResponse,
    PublicacionGuardadaListado
)
from app.services.publicaciones_guardadas_services import (
    guardar_publicacion,
    quitar_publicacion_guardada,
    listar_publicaciones_guardadas
)

router = APIRouter(
    prefix="/publicaciones/guardadas",
    tags=["Publicaciones Guardadas"]
)


@router.post(
    "",
    response_model=PublicacionGuardadaResponse,
    status_code=status.HTTP_201_CREATED
)
def guardar_publicacion_endpoint(
    data: PublicacionGuardadaCreate,
    db: Session = Depends(get_db),
    usuario=Depends(obtener_usuario_actual)

):
    """
    Guarda una publicación para el usuario autenticado.
    """

    try:
        return guardar_publicacion(
            db=db,
            usuario_id=usuario.id,
            publicacion_id=data.publicacion_id
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.delete(
    "/{publicacion_id}",
    status_code=status.HTTP_204_NO_CONTENT
)
def quitar_publicacion_guardada_endpoint(
    publicacion_id: int,
    db: Session = Depends(get_db),
    usuario=Depends(obtener_usuario_actual)

):
    """
    Quita una publicación de los guardados del usuario autenticado.
    """

    try:
        quitar_publicacion_guardada(
            db=db,
            usuario_id=usuario.id,
            publicacion_id=publicacion_id
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get(
    "",
    response_model=list[PublicacionGuardadaListado]
)
def listar_publicaciones_guardadas_endpoint(
    db: Session = Depends(get_db),
    usuario=Depends(obtener_usuario_actual)

):
    """
    Lista todas las publicaciones guardadas del usuario autenticado.
    """

    return listar_publicaciones_guardadas(
        db=db,
        usuario_id=usuario.id
    )
