from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.core.auth import obtener_usuario_actual
from app.core.database import get_db
from app.modules.moderation.schemas.contenido_denuncias_schemas import (
    ContenidoDenunciaCreate,
    ContenidoDenunciaResponse,
)
from app.modules.moderation.services.contenido_denuncias_services import (
    RecursoDenunciableNoEncontradoError,
    crear_denuncia_contenido,
)


router = APIRouter(prefix="/moderacion", tags=["Moderacion"])


@router.post(
    "/denuncias",
    response_model=ContenidoDenunciaResponse,
    status_code=status.HTTP_201_CREATED,
)
def crear_denuncia_endpoint(
    payload: ContenidoDenunciaCreate,
    response: Response,
    db: Session = Depends(get_db),
    usuario_actual=Depends(obtener_usuario_actual),
):
    try:
        denuncia, creada = crear_denuncia_contenido(
            db=db,
            payload=payload,
            usuario=usuario_actual,
        )
    except RecursoDenunciableNoEncontradoError:
        raise HTTPException(status_code=404, detail="Recurso no denunciable")

    if not creada:
        response.status_code = status.HTTP_200_OK

    return denuncia
