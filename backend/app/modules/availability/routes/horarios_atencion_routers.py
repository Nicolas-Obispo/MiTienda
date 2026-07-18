"""
Rutas HTTP para horarios habituales de atencion de comercios.
"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.auth import obtener_usuario_actual, obtener_usuario_actual_opcional
from app.core.database import get_db
from app.modules.availability.schemas.horarios_atencion_schemas import (
    HorariosAtencionReemplazo,
    HorariosAtencionResponse,
)
from app.modules.availability.services.horarios_atencion_services import (
    ComercioNoEncontradoError,
    FranjasSolapadasError,
    ZONA_HORARIA_DISPONIBILIDAD,
    calcular_estado_horario,
    obtener_horarios_atencion,
    reemplazar_horarios_atencion,
)
from app.modules.spaces.models.comercios_models import Comercio
from app.modules.users.models.usuarios_models import Usuario


router = APIRouter(
    prefix="/comercios",
    tags=["Horarios de atencion"],
)


def _obtener_comercio_incluyendo_pausa(
    db: Session,
    comercio_id: int,
) -> Comercio | None:
    return db.query(Comercio).filter(Comercio.id == comercio_id).first()


def _construir_response_horarios(
    *,
    comercio_id: int,
    franjas,
) -> HorariosAtencionResponse:
    estado_horario = calcular_estado_horario(
        franjas,
        zona_horaria=ZONA_HORARIA_DISPONIBILIDAD,
    )

    return HorariosAtencionResponse(
        comercio_id=comercio_id,
        zona_horaria=ZONA_HORARIA_DISPONIBILIDAD,
        franjas=franjas,
        estado_horario=estado_horario,
    )


@router.get(
    "/{comercio_id}/horarios",
    response_model=HorariosAtencionResponse,
)
def obtener_horarios_atencion_endpoint(
    comercio_id: int,
    db: Session = Depends(get_db),
    usuario_actual: Optional[Usuario] = Depends(obtener_usuario_actual_opcional),
):
    comercio = _obtener_comercio_incluyendo_pausa(db, comercio_id)

    if not comercio:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Comercio no encontrado",
        )

    es_propietario = (
        usuario_actual is not None
        and comercio.usuario_id == usuario_actual.id
    )

    if not comercio.activo and not es_propietario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Comercio no encontrado",
        )

    franjas = obtener_horarios_atencion(db, comercio_id)
    return _construir_response_horarios(
        comercio_id=comercio_id,
        franjas=franjas,
    )


@router.put(
    "/{comercio_id}/horarios",
    response_model=HorariosAtencionResponse,
)
def reemplazar_horarios_atencion_endpoint(
    comercio_id: int,
    payload: HorariosAtencionReemplazo,
    db: Session = Depends(get_db),
    usuario_actual: Usuario = Depends(obtener_usuario_actual),
):
    comercio = _obtener_comercio_incluyendo_pausa(db, comercio_id)

    try:
        franjas = reemplazar_horarios_atencion(
            db=db,
            comercio=comercio,
            usuario=usuario_actual,
            franjas=payload.franjas,
        )
    except ComercioNoEncontradoError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Comercio no encontrado",
        )
    except PermissionError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(exc),
        )
    except FranjasSolapadasError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )

    return _construir_response_horarios(
        comercio_id=comercio_id,
        franjas=franjas,
    )
