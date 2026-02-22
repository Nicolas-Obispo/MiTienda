"""
comercios_routers.py
-------------------
Rutas HTTP para Comercios (MiPlaza).

Este router:
- Maneja HTTP
- Usa JWT existente
- Llama a services
- NO contiene lógica de negocio

ETAPA 50 (IA v1 - MVP):
- Se agrega modo de búsqueda "smart" (ranking inteligente basado en keywords)
- El router SOLO expone el flag y delega todo al service
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
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
    listar_comercios_activos,
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
# Explorar comercios (público) - ETAPA 48 + ETAPA 50 (smart)
# ============================================================

@router.get("/activos", response_model=list[ComercioResponse])
def listar_comercios_activos_endpoint(
    q: str | None = Query(
        default=None,
        description="Búsqueda por nombre (contiene). En modo smart o semantic, se usa como query base para ranking."
    ),
    smart: bool = Query(
        default=False,
        description="Si true, aplica ranking inteligente (IA v1 keyword) en el orden de resultados."
    ),
    smart_semantic: bool = Query(
        default=False,
        description="Si true, aplica ranking semántico (IA v2 embeddings) en el orden de resultados."
    ),
    limit: int = Query(default=20, ge=1, le=100, description="Tamaño de página (1..100)"),
    offset: int = Query(default=0, ge=0, description="Offset para paginado"),
    db: Session = Depends(get_db),
):
    """
    Endpoint público para pantalla Explorar.

    - Devuelve SOLO comercios activos
    - Soporta búsqueda por q
    - Soporta paginado (limit/offset)

    ETAPA 50:
    - smart=false (default): comportamiento clásico
    - smart=true: ranking IA v1 (keyword)

    ETAPA 51:
    - smart_semantic=true: ranking IA v2 (embeddings)
    """

    return listar_comercios_activos(
        db,
        q=q,
        smart=smart,
        smart_semantic=smart_semantic,
        limit=limit,
        offset=offset
    )


# ============================================================
# Mis comercios (del usuario logueado)
# ============================================================
@router.get("/mis", response_model=list[ComercioResponse])
def listar_mis_comercios_endpoint(
    db: Session = Depends(get_db),
    usuario_actual=Depends(obtener_usuario_actual),
):
    """
    Devuelve los comercios del usuario logueado.
    - Es un endpoint "admin" del Perfil.
    - NO aplica filtros de ciudad/rubro: es "mis recursos".
    """
    # Nota: evitamos lógica de negocio acá; solo resolvemos el query simple.
    # Si más adelante esto crece (paginado/estado/etc), se mueve a services.
    comercios = (
        db.query(Comercio)
        .filter(Comercio.usuario_id == usuario_actual.id)
        .order_by(Comercio.id.desc())
        .all()
    )

    return comercios


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


# ============================================================
# Reactivar comercio
# ============================================================

@router.post("/{comercio_id}/reactivar", response_model=ComercioResponse)
def reactivar_comercio_endpoint(
    comercio_id: int,
    db: Session = Depends(get_db),
    usuario_actual=Depends(obtener_usuario_actual),
):
    """
    Reactiva un comercio del usuario logueado.
    - Revierte el soft delete (activo = True).
    - Importante: acá buscamos por ID sin filtrar activo, porque si está inactivo
      el "obtener_comercio_por_id" puede no encontrarlo.
    """
    # Buscamos directo en DB (incluye activos e inactivos)
    comercio = db.query(Comercio).filter(Comercio.id == comercio_id).first()

    if not comercio:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Comercio no encontrado"
        )

    # Solo el dueño puede reactivar
    if comercio.usuario_id != usuario_actual.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tenés permisos para reactivar este comercio"
        )

    comercio.activo = True
    db.add(comercio)
    db.commit()
    db.refresh(comercio)

    return comercio