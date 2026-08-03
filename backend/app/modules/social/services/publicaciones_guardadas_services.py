"""
Servicios para manejar publicaciones guardadas.

Contiene toda la logica de negocio:
- Guardar publicaciones.
- Evitar duplicados sin romper frontend.
- Quitar guardados.
- Listar publicaciones guardadas por usuario.
"""

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.modules.ai.services.usuarios_embeddings_services import (
    regenerar_embedding_usuario_si_corresponde,
)
from app.modules.posts.models.publicaciones_models import Publicacion
from app.modules.posts.services.publicaciones_services import (
    obtener_publicacion_visible_o_error,
)
from app.modules.social.models.likes_publicaciones_models import LikePublicacion
from app.modules.social.models.publicaciones_guardadas_models import PublicacionGuardada
from app.modules.spaces.models.comercios_models import Comercio


def guardar_publicacion(
    db: Session,
    usuario_id: int,
    publicacion_id: int,
) -> PublicacionGuardada:
    """
    Guarda una publicacion visible para un usuario.

    Si ya estaba guardada, devuelve el registro existente.
    """

    obtener_publicacion_visible_o_error(db, publicacion_id=publicacion_id)

    guardado_existente = (
        db.query(PublicacionGuardada)
        .filter(
            PublicacionGuardada.usuario_id == usuario_id,
            PublicacionGuardada.publicacion_id == publicacion_id,
        )
        .first()
    )

    if guardado_existente:
        return guardado_existente

    guardado = PublicacionGuardada(
        usuario_id=usuario_id,
        publicacion_id=publicacion_id,
    )

    db.add(guardado)
    db.commit()
    db.refresh(guardado)

    regenerar_embedding_usuario_si_corresponde(
        db=db,
        usuario_id=usuario_id,
    )

    return guardado


def quitar_publicacion_guardada(
    db: Session,
    usuario_id: int,
    publicacion_id: int,
) -> None:
    """
    Quita una publicacion de los guardados del usuario.

    La operacion es idempotente: si no existe la relacion, no falla.
    """

    guardado = (
        db.query(PublicacionGuardada)
        .filter(
            PublicacionGuardada.usuario_id == usuario_id,
            PublicacionGuardada.publicacion_id == publicacion_id,
        )
        .first()
    )

    if not guardado:
        return

    db.delete(guardado)
    db.commit()

    regenerar_embedding_usuario_si_corresponde(
        db=db,
        usuario_id=usuario_id,
    )


def listar_publicaciones_guardadas(
    db: Session,
    usuario_id: int,
):
    """
    Devuelve publicaciones guardadas visibles, ordenadas desde la mas reciente.
    """

    filas = (
        db.query(
            PublicacionGuardada,
            Publicacion,
            Comercio.nombre.label("comercio_nombre"),
        )
        .join(Publicacion, Publicacion.id == PublicacionGuardada.publicacion_id)
        .join(Comercio, Comercio.id == Publicacion.comercio_id)
        .filter(
            PublicacionGuardada.usuario_id == usuario_id,
            Publicacion.is_activa.is_(True),
            Comercio.activo.is_(True),
        )
        .order_by(PublicacionGuardada.created_at.desc())
        .all()
    )

    if not filas:
        return []

    publicaciones_ids = [publicacion.id for _, publicacion, _ in filas]

    likes_count_rows = (
        db.query(
            LikePublicacion.publicacion_id,
            func.count(LikePublicacion.id).label("likes_count"),
        )
        .filter(LikePublicacion.publicacion_id.in_(publicaciones_ids))
        .group_by(LikePublicacion.publicacion_id)
        .all()
    )

    guardados_count_rows = (
        db.query(
            PublicacionGuardada.publicacion_id,
            func.count(PublicacionGuardada.id).label("guardados_count"),
        )
        .filter(PublicacionGuardada.publicacion_id.in_(publicaciones_ids))
        .group_by(PublicacionGuardada.publicacion_id)
        .all()
    )

    liked_by_me_rows = (
        db.query(LikePublicacion.publicacion_id)
        .filter(
            LikePublicacion.usuario_id == usuario_id,
            LikePublicacion.publicacion_id.in_(publicaciones_ids),
        )
        .all()
    )

    likes_count_map = {
        publicacion_id: int(likes_count or 0)
        for publicacion_id, likes_count in likes_count_rows
    }
    guardados_count_map = {
        publicacion_id: int(guardados_count or 0)
        for publicacion_id, guardados_count in guardados_count_rows
    }
    liked_by_me_set = {publicacion_id for (publicacion_id,) in liked_by_me_rows}

    resultado = []

    for guardado, publicacion, comercio_nombre in filas:
        likes_count = likes_count_map.get(publicacion.id, 0)
        guardados_count = guardados_count_map.get(publicacion.id, 0)

        resultado.append(
            {
                "publicacion_id": guardado.publicacion_id,
                "created_at": guardado.created_at,
                "publicacion": {
                    "id": publicacion.id,
                    "publicacion_id": publicacion.id,
                    "comercio_id": publicacion.comercio_id,
                    "comercio_nombre": comercio_nombre,
                    "titulo": publicacion.titulo,
                    "descripcion": publicacion.descripcion,
                    "seccion_id": publicacion.seccion_id,
                    "imagen_url": publicacion.imagen_url,
                    "is_activa": publicacion.is_activa,
                    "created_at": publicacion.created_at,
                    "updated_at": publicacion.updated_at,
                    "likes_count": likes_count,
                    "guardados_count": guardados_count,
                    "interacciones_count": likes_count + guardados_count,
                    "liked_by_me": publicacion.id in liked_by_me_set,
                    "guardada_by_me": True,
                },
            }
        )

    return resultado
