"""
comercios_services.py
--------------------
Lógica de negocio para Comercios (MiPlaza).

Este módulo:
- NO maneja HTTP
- NO maneja JWT
- NO accede a headers
- SOLO lógica de negocio
"""

from sqlalchemy.orm import Session
from app.models.comercios_models import Comercio
from app.models.usuarios_models import Usuario
from app.schemas.comercios_schemas import ComercioCreate, ComercioUpdate


# ============================================================
# Crear comercio
# ============================================================

def crear_comercio(
    db: Session,
    usuario: Usuario,
    data: ComercioCreate
) -> Comercio:
    """
    Crea un comercio asociado al usuario autenticado.

    Reglas:
    - El usuario debe estar en modo 'publicador'
    """

    if usuario.modo_activo != "publicador":
        raise ValueError("El usuario no está en modo publicador")

    comercio = Comercio(
        usuario_id=usuario.id,
        nombre=data.nombre,
        descripcion=data.descripcion,
        portada_url=str(data.portada_url),
        rubro_id=data.rubro_id,
        provincia=data.provincia,
        ciudad=data.ciudad,
        direccion=data.direccion,
        whatsapp=data.whatsapp,
        instagram=data.instagram,
        maps_url=str(data.maps_url) if data.maps_url else None,
    )

    db.add(comercio)
    db.commit()
    db.refresh(comercio)

    return comercio


# ============================================================
# Obtener comercio por ID
# ============================================================

def obtener_comercio_por_id(
    db: Session,
    comercio_id: int
) -> Comercio | None:
    return (
        db.query(Comercio)
        .filter(Comercio.id == comercio_id, Comercio.activo == True)
        .first()
    )


# ============================================================
# Listar comercios activos
# ============================================================

def listar_comercios(
    db: Session,
    ciudad: str | None = None,
    rubro_id: int | None = None
) -> list[Comercio]:
    query = db.query(Comercio).filter(Comercio.activo == True)

    if ciudad:
        query = query.filter(Comercio.ciudad == ciudad)

    if rubro_id:
        query = query.filter(Comercio.rubro_id == rubro_id)

    return query.all()


# ============================================================
# Actualizar comercio
# ============================================================

def actualizar_comercio(
    db: Session,
    usuario: Usuario,
    comercio: Comercio,
    data: ComercioUpdate
) -> Comercio:
    """
    Actualiza un comercio.

    Reglas:
    - Solo el dueño puede modificarlo
    """

    if comercio.usuario_id != usuario.id:
        raise PermissionError("No tenés permiso para modificar este comercio")

    for campo, valor in data.dict(exclude_unset=True).items():
        setattr(comercio, campo, valor)

    db.commit()
    db.refresh(comercio)

    return comercio


# ============================================================
# Desactivar comercio (soft delete)
# ============================================================

def desactivar_comercio(
    db: Session,
    usuario: Usuario,
    comercio: Comercio
) -> Comercio:
    """
    Desactiva un comercio sin borrarlo físicamente.
    """

    if comercio.usuario_id != usuario.id:
        raise PermissionError("No tenés permiso para desactivar este comercio")

    comercio.activo = False

    db.commit()
    db.refresh(comercio)

    return comercio
