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

from app.schemas.secciones_schemas import (
    SeccionCreate,
    SeccionUpdate,
    SeccionResponse
)

from app.services.secciones_services import (
    crear_seccion,
    listar_secciones_por_comercio,
    obtener_seccion_por_id,
    actualizar_seccion
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

    return crear_seccion(db, payload)


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

    seccion = obtener_seccion_por_id(db, seccion_id)
    if not seccion:
        raise HTTPException(
            status_code=404,
            detail="Sección no encontrada"
        )

    return actualizar_seccion(db, seccion, payload)
