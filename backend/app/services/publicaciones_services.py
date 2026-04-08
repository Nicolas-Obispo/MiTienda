# app/services/publicaciones_services.py
"""
Service: Publicaciones

Reglas:
- Services = lógica de negocio
- Sin HTTP (eso va en routers)
- Acceso a DB explícito

ETAPA 55:
- Se agregan helpers bulk para evitar consultas N+1 en feed
"""

from typing import List, Dict

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
        db=db,
        publicacion_id=publicacion_id,
    )

    return likes_count + guardados_count


def obtener_guardados_count_por_publicaciones(
    db: Session,
    *,
    publicaciones_ids: List[int],
) -> Dict[int, int]:
    """
    Devuelve un diccionario con cantidad de guardados por publicación.

    Formato:
    {
        publicacion_id: guardados_count
    }

    Se usa para evitar consultas N+1 en el feed.
    """

    if not publicaciones_ids:
        return {}

    resultados = (
        db.query(
            PublicacionGuardada.publicacion_id,
            func.count(PublicacionGuardada.id).label("guardados_count"),
        )
        .filter(PublicacionGuardada.publicacion_id.in_(publicaciones_ids))
        .group_by(PublicacionGuardada.publicacion_id)
        .all()
    )

    guardados_map = {publicacion_id: 0 for publicacion_id in publicaciones_ids}

    for publicacion_id, guardados_count in resultados:
        guardados_map[publicacion_id] = int(guardados_count or 0)

    return guardados_map


def obtener_interacciones_count_por_publicaciones(
    *,
    publicaciones_ids: List[int],
    likes_count_map: Dict[int, int],
    guardados_count_map: Dict[int, int],
) -> Dict[int, int]:
    """
    Devuelve un diccionario con cantidad total de interacciones por publicación.

    Interacciones = likes + guardados

    Se apoya en mapas ya calculados para evitar nuevas queries.
    """

    if not publicaciones_ids:
        return {}

    interacciones_map = {}

    for publicacion_id in publicaciones_ids:
        likes_count = int(likes_count_map.get(publicacion_id, 0))
        guardados_count = int(guardados_count_map.get(publicacion_id, 0))
        interacciones_map[publicacion_id] = likes_count + guardados_count

    return interacciones_map


def obtener_publicaciones_interactuadas_por_usuario(
    db: Session,
    *,
    usuario_id: int,
):
    """
    Devuelve las publicaciones con las que el usuario interactuó
    (likes + guardados).
    """

    # IDs de publicaciones con like
    likes_ids = (
        db.query(LikePublicacion.publicacion_id)
        .filter(LikePublicacion.usuario_id == usuario_id)
        .all()
    )

    # IDs de publicaciones guardadas
    guardados_ids = (
        db.query(PublicacionGuardada.publicacion_id)
        .filter(PublicacionGuardada.usuario_id == usuario_id)
        .all()
    )

    # Convertimos a set para evitar duplicados
    publicaciones_ids = set()

    for (pid,) in likes_ids:
        publicaciones_ids.add(pid)

    for (pid,) in guardados_ids:
        publicaciones_ids.add(pid)

    if not publicaciones_ids:
        return []

    # Traemos las publicaciones completas
    publicaciones = (
        db.query(Publicacion)
        .filter(Publicacion.id.in_(publicaciones_ids))
        .all()
    )

    return publicaciones