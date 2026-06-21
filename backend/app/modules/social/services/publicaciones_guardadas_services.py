# app/modules/social/services/publicaciones_guardadas_services.py
"""
Servicios para manejar publicaciones guardadas.

Contiene toda la lógica de negocio:
- Guardar publicaciones
- Evitar duplicados sin romper frontend
- Quitar guardados
- Listar publicaciones guardadas por usuario

Optimización ETAPA 55:
- Evita recalcular embedding innecesariamente
- Usa ventana temporal (5 min)

ETAPA 56:
- guardar_publicacion pasa a ser idempotente
- Si ya existe el guardado, no tira error 400
"""

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.modules.social.models.publicaciones_guardadas_models import PublicacionGuardada
from app.modules.social.models.likes_publicaciones_models import LikePublicacion
from app.modules.posts.models.publicaciones_models import Publicacion
from app.modules.spaces.models.comercios_models import Comercio
from app.modules.ai.services.usuarios_embeddings_services import (
    regenerar_embedding_usuario_si_corresponde,
)


def guardar_publicacion(
    db: Session,
    usuario_id: int,
    publicacion_id: int
) -> PublicacionGuardada:
    """
    Guarda una publicación para un usuario.

    Validaciones:
    - La publicación debe existir
    - Si ya estaba guardada, devuelve el registro existente
      (comportamiento idempotente para no romper frontend)
    """

    # Verificar que la publicación exista
    publicacion = (
        db.query(Publicacion)
        .filter(Publicacion.id == publicacion_id)
        .first()
    )

    if not publicacion:
        raise ValueError("La publicación no existe")

    # Si ya estaba guardada, devolvemos el existente y NO rompemos
    guardado_existente = (
        db.query(PublicacionGuardada)
        .filter(
            PublicacionGuardada.usuario_id == usuario_id,
            PublicacionGuardada.publicacion_id == publicacion_id
        )
        .first()
    )

    if guardado_existente:
        return guardado_existente

    guardado = PublicacionGuardada(
        usuario_id=usuario_id,
        publicacion_id=publicacion_id
    )

    db.add(guardado)
    db.commit()
    db.refresh(guardado)

    # Recalcular embedding solo si corresponde
    regenerar_embedding_usuario_si_corresponde(
        db=db,
        usuario_id=usuario_id
    )

    return guardado


def quitar_publicacion_guardada(
    db: Session,
    usuario_id: int,
    publicacion_id: int
) -> None:
    """
    Quita una publicación de los guardados del usuario.
    """

    guardado = (
        db.query(PublicacionGuardada)
        .filter(
            PublicacionGuardada.usuario_id == usuario_id,
            PublicacionGuardada.publicacion_id == publicacion_id
        )
        .first()
    )

    if not guardado:
        raise ValueError("La publicación no está guardada")

    db.delete(guardado)
    db.commit()

    # Recalcular embedding solo si corresponde
    regenerar_embedding_usuario_si_corresponde(
        db=db,
        usuario_id=usuario_id
    )


def listar_publicaciones_guardadas(
    db: Session,
    usuario_id: int
):
    """
    Devuelve todas las publicaciones guardadas por el usuario,
    ordenadas desde la más reciente a la más antigua.
    """

    filas = (
        db.query(
            PublicacionGuardada,
            Publicacion,
            Comercio.nombre.label("comercio_nombre"),
        )
        .join(Publicacion, Publicacion.id == PublicacionGuardada.publicacion_id)
        .outerjoin(Comercio, Comercio.id == Publicacion.comercio_id)
        .filter(PublicacionGuardada.usuario_id == usuario_id)
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
