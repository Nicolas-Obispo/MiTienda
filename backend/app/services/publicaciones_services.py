# app/services/publicaciones_services.py
"""
Service: Publicaciones

Reglas:
- Services = lógica de negocio
- Sin HTTP (eso va en routers)
- Acceso a DB explícito
"""

from typing import List

from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.publicaciones_models import Publicacion
from app.models.publicaciones_guardadas_models import PublicacionGuardada
from app.models.likes_publicaciones_models import LikePublicacion
from app.schemas.publicaciones_schemas import PublicacionCreate


# --------------------------------------------------
# Creación de publicaciones
# --------------------------------------------------

def crear_publicacion(
    db: Session,
    *,
    comercio_id: int,
    publicacion_in: PublicacionCreate,
) -> Publicacion:
    """
    Crea una nueva publicación para un comercio.
    El comercio_id viene del contexto (no del body).
    """

    nueva_publicacion = Publicacion(
        comercio_id=comercio_id,
        titulo=publicacion_in.titulo,
        descripcion=publicacion_in.descripcion,
        seccion_id=publicacion_in.seccion_id,
        is_activa=publicacion_in.is_activa,
    )

    db.add(nueva_publicacion)
    db.commit()
    db.refresh(nueva_publicacion)

    return nueva_publicacion


# --------------------------------------------------
# Listados de publicaciones
# --------------------------------------------------

def listar_publicaciones_por_comercio(
    db: Session,
    *,
    comercio_id: int,
) -> List[Publicacion]:
    """
    Devuelve todas las publicaciones de un comercio.
    """

    return (
        db.query(Publicacion)
        .filter(Publicacion.comercio_id == comercio_id)
        .order_by(Publicacion.created_at.desc())
        .all()
    )


# --------------------------------------------------
# Detalle de publicación
# --------------------------------------------------

def obtener_publicacion_por_id_y_sumar_view(
    db: Session,
    *,
    publicacion_id: int,
) -> Publicacion:
    """
    Obtiene una publicación por ID e incrementa su contador de vistas.
    """

    publicacion = (
        db.query(Publicacion)
        .filter(
            Publicacion.id == publicacion_id,
            Publicacion.is_activa.is_(True),
        )
        .first()
    )

    if not publicacion:
        return None

    publicacion.views_count += 1
    db.commit()
    db.refresh(publicacion)

    return publicacion


# --------------------------------------------------
# Métricas avanzadas de interacción (ETAPA 30)
# --------------------------------------------------

def obtener_guardados_count(
    db: Session,
    *,
    publicacion_id: int,
) -> int:
    """
    Devuelve la cantidad de veces que una publicación fue guardada.
    """

    return (
        db.query(func.count(PublicacionGuardada.id))
        .filter(PublicacionGuardada.publicacion_id == publicacion_id)
        .scalar()
        or 0
    )


def obtener_interacciones_count(
    db: Session,
    *,
    publicacion_id: int,
) -> int:
    """
    Devuelve la cantidad total de interacciones de una publicación.

    Interacciones = likes + guardados
    """

    likes_count = (
        db.query(func.count(LikePublicacion.id))
        .filter(LikePublicacion.publicacion_id == publicacion_id)
        .scalar()
        or 0
    )

    guardados_count = obtener_guardados_count(
        db,
        publicacion_id=publicacion_id,
    )

    return likes_count + guardados_count
