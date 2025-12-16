"""
comercios_routers.py
-------------------
Rutas HTTP para Comercios (MiPlaza).

Este router:
- Maneja HTTP
- Usa JWT existente
- Llama a services
- NO contiene lógica de negocio
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

# DB
from app.core.database import get_db

# Auth
from app.core.auth import obtener_usuario_actual

# Models
from app.models.comercios_models import Comercio

# Schemas
from app.schemas.comercios_schemas import (
    ComercioCreate,
    ComercioUpdate,
    ComercioResponse,
)

# Services
from app.services.comercios_services import (
    crear_comercio,
    listar_comercios,
    obtener_comercio_por_id,
    actualizar_comercio,
    desactivar_comercio,
)


router = APIRouter(
    prefix="/comercios",
    tags=["Comercios"]
)


# ============================================================
# Crear comercio
# ============================================================

@router.post(
    "",
    response_model=ComercioResponse,
    status_code=status.HTTP_201_CREATED
)
def crear_comercio_endpoint(
    payload: ComercioCreate,
    db: Session = Depends(get_db),
    usuario_actual=Depends(obtener_usuario_actual),
):
    try:
        return crear_comercio(db, usuario_actual, payload)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )


# ============================================================
# Listar comercios
# ============================================================

@router.get("", response_model=list[ComercioResponse])
def listar_comercios_endpoint(
    ciudad: str | None = None,
    rubro_id: int | None = None,
    db: Session = Depends(get_db),
):
    return listar_comercios(db, ciudad=ciudad, rubro_id=rubro_id)


# ============================================================
# Obtener comercio por ID
# ============================================================

@router.get("/{comercio_id}", response_model=ComercioResponse)
def obtener_comercio_endpoint(
    comercio_id: int,
    db: Session = Depends(get_db),
):
    comercio = obtener_comercio_por_id(db, comercio_id)

    if not comercio:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Comercio no encontrado"
        )

    return comercio


# ============================================================
# Actualizar comercio
# ============================================================

@router.put("/{comercio_id}", response_model=ComercioResponse)
def actualizar_comercio_endpoint(
    comercio_id: int,
    payload: ComercioUpdate,
    db: Session = Depends(get_db),
    usuario_actual=Depends(obtener_usuario_actual),
):
    comercio = obtener_comercio_por_id(db, comercio_id)

    if not comercio:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Comercio no encontrado"
        )

    try:
        return actualizar_comercio(db, usuario_actual, comercio, payload)
    except PermissionError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )


# ============================================================
# Desactivar comercio
# ============================================================

@router.delete("/{comercio_id}", response_model=ComercioResponse)
def desactivar_comercio_endpoint(
    comercio_id: int,
    db: Session = Depends(get_db),
    usuario_actual=Depends(obtener_usuario_actual),
):
    comercio = obtener_comercio_por_id(db, comercio_id)

    if not comercio:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Comercio no encontrado"
        )

    try:
        return desactivar_comercio(db, usuario_actual, comercio)
    except PermissionError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )
