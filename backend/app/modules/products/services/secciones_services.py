"""
secciones_services.py
---------------------
Lógica de negocio para Secciones de Comercios.

Esta capa:
- NO maneja HTTP
- NO maneja autenticación
- NO conoce FastAPI
- Opera solo con SQLAlchemy y reglas de negocio
"""

from sqlalchemy.orm import Session
from typing import List, Optional

from app.modules.products.models.secciones_models import Seccion
from app.modules.products.schemas.secciones_schemas import SeccionCreate, SeccionUpdate
from app.modules.spaces.services.comercios_ownership_services import (
    obtener_comercio_propio_o_error,
)
from app.modules.users.models.usuarios_models import Usuario


class SeccionNoEncontradaError(ValueError):
    pass


def _obtener_seccion_propia_o_error(
    db: Session,
    *,
    seccion_id: int,
    usuario_autenticado: Usuario,
) -> Seccion:
    seccion = obtener_seccion_por_id(db, seccion_id)
    if seccion is None:
        raise SeccionNoEncontradaError("Seccion no encontrada")

    obtener_comercio_propio_o_error(
        db,
        comercio_id=seccion.comercio_id,
        usuario_autenticado=usuario_autenticado,
    )

    return seccion


# ======================================================
# Crear sección
# ======================================================
def crear_seccion(
    db: Session,
    data: SeccionCreate,
    usuario_autenticado: Usuario,
) -> Seccion:
    """
    Crea una nueva sección para un comercio.
    """

    obtener_comercio_propio_o_error(
        db,
        comercio_id=data.comercio_id,
        usuario_autenticado=usuario_autenticado,
    )

    seccion = Seccion(
        comercio_id=data.comercio_id,
        nombre=data.nombre,
        descripcion=data.descripcion,
        orden=data.orden
    )

    db.add(seccion)
    db.commit()
    db.refresh(seccion)

    return seccion


# ======================================================
# Listar secciones por comercio
# ======================================================
def listar_secciones_por_comercio(
    db: Session,
    comercio_id: int,
    solo_activas: bool = True
) -> List[Seccion]:
    """
    Devuelve todas las secciones de un comercio.
    """

    query = db.query(Seccion).filter(
        Seccion.comercio_id == comercio_id
    )

    if solo_activas:
        query = query.filter(Seccion.activo == True)

    return query.order_by(Seccion.orden.asc()).all()


# ======================================================
# Obtener sección por ID
# ======================================================
def obtener_seccion_por_id(
    db: Session,
    seccion_id: int
) -> Optional[Seccion]:
    """
    Obtiene una sección por su ID.
    """

    return db.query(Seccion).filter(
        Seccion.id == seccion_id
    ).first()


# ======================================================
# Actualizar sección
# ======================================================
def actualizar_seccion(
    db: Session,
    seccion_id: int,
    data: SeccionUpdate,
    usuario_autenticado: Usuario,
) -> Seccion:
    """
    Actualiza campos permitidos de una sección.
    """

    seccion = _obtener_seccion_propia_o_error(
        db,
        seccion_id=seccion_id,
        usuario_autenticado=usuario_autenticado,
    )

    if data.nombre is not None:
        seccion.nombre = data.nombre

    if data.descripcion is not None:
        seccion.descripcion = data.descripcion

    if data.orden is not None:
        seccion.orden = data.orden

    if data.activo is not None:
        seccion.activo = data.activo

    db.commit()
    db.refresh(seccion)

    return seccion
