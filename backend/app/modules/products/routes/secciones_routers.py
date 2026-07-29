"""
secciones_routers.py
--------------------
Rutas HTTP para Secciones de Comercios.

Este router:
- Solo maneja HTTP
- No contiene lógica de negocio
- Delegada todo a la capa services
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.core.database import get_db
from app.core.auth import obtener_usuario_actual

from app.modules.products.schemas.secciones_schemas import (
    SeccionCreate,
    SeccionUpdate,
    SeccionResponse,
)

from app.modules.spaces.services.comercios_ownership_services import (
    ComercioNoEncontradoError,
    ComercioUsuarioNoPropietarioError,
)
from app.modules.products.services.secciones_services import (
    SeccionNoEncontradaError,
    crear_seccion,
    listar_secciones_por_comercio,
    actualizar_seccion,
)

router = APIRouter(
    prefix="/secciones",
    tags=["Secciones"]
)


# ======================================================
# Crear sección
# ======================================================
@router.post("/", response_model=SeccionResponse)
def crear_seccion_endpoint(
    payload: SeccionCreate,
    db: Session = Depends(get_db),
    usuario_actual=Depends(obtener_usuario_actual)
):
    """
    Crea una sección para un comercio.
    Requiere usuario autenticado.
    """

    try:
        return crear_seccion(
            db,
            payload,
            usuario_autenticado=usuario_actual,
        )
    except ComercioNoEncontradoError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ComercioUsuarioNoPropietarioError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc


# ======================================================
# Listar secciones por comercio
# ======================================================
@router.get(
    "/comercio/{comercio_id}",
    response_model=List[SeccionResponse]
)
def listar_secciones_endpoint(
    comercio_id: int,
    db: Session = Depends(get_db)
):
    """
    Lista secciones activas de un comercio.
    Público.
    """

    return listar_secciones_por_comercio(db, comercio_id)


# ======================================================
# Actualizar sección
# ======================================================
@router.put(
    "/{seccion_id}",
    response_model=SeccionResponse
)
def actualizar_seccion_endpoint(
    seccion_id: int,
    payload: SeccionUpdate,
    db: Session = Depends(get_db),
    usuario_actual=Depends(obtener_usuario_actual)
):
    """
    Actualiza una sección existente.
    Requiere usuario autenticado.
    """

    try:
        return actualizar_seccion(
            db,
            seccion_id,
            payload,
            usuario_autenticado=usuario_actual,
        )
    except SeccionNoEncontradaError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ComercioNoEncontradoError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ComercioUsuarioNoPropietarioError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
