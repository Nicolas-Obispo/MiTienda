# app/services/feed_publicaciones_services.py
"""
Service: Feed personalizado de Publicaciones

- Calcula likes_count y liked_by_me en la misma query
- Score base:
  score = likes_count + (guardados_count * 2) + bonus_recencia
- ETAPA 54:
  si el usuario tiene embedding, suma bonus por afinidad semántica
"""

from datetime import datetime, timedelta
from typing import List, Optional

from sqlalchemy import func, case, literal
from sqlalchemy.orm import Session

from app.models.publicaciones_models import Publicacion
from app.models.likes_publicaciones_models import LikePublicacion

from app.services.publicaciones_services import (
    obtener_guardados_count,
    obtener_interacciones_count,
)
from app.services.usuarios_embeddings_services import obtener_vector_usuario
from app.services.comercios_embeddings_services import obtener_vector_embedding_comercio


def _calcular_similitud_coseno(vector_a: list, vector_b: list) -> float:
    """
    Calcula similitud coseno entre dos vectores.
    """

    if not vector_a or not vector_b:
        return 0.0

    if len(vector_a) != len(vector_b):
        return 0.0

    producto_punto = sum(a * b for a, b in zip(vector_a, vector_b))
    norma_a = sum(a * a for a in vector_a) ** 0.5
    norma_b = sum(b * b for b in vector_b) ** 0.5

    if norma_a == 0 or norma_b == 0:
        return 0.0

    return producto_punto / (norma_a * norma_b)


def obtener_feed_publicaciones(
    db: Session,
    *,
    usuario_id: Optional[int] = None,
) -> List[Publicacion]:
    """
    Devuelve publicaciones para el feed personalizado.
    """

    ahora = datetime.utcnow()

    # Embedding del usuario (si existe)
    vector_usuario = None
    if usuario_id is not None:
        vector_usuario = obtener_vector_usuario(db=db, usuario_id=usuario_id)

    # Bonus por recencia
    bonus_recencia = case(
        (Publicacion.created_at >= ahora - timedelta(days=1), 3),
        (Publicacion.created_at >= ahora - timedelta(days=3), 2),
        (Publicacion.created_at >= ahora - timedelta(days=7), 1),
        else_=0,
    )

    # likes_count por publicación
    likes_count_expr = func.count(LikePublicacion.id)

    # liked_by_me real
    if usuario_id is None:
        liked_by_me_expr = literal(False).label("liked_by_me")
    else:
        liked_by_me_expr = func.max(
            case(
                (LikePublicacion.usuario_id == usuario_id, 1),
                else_=0,
            )
        ).label("liked_by_me")

    query = (
        db.query(
            Publicacion,
            likes_count_expr.label("likes_count"),
            bonus_recencia.label("bonus_recencia"),
            liked_by_me_expr,
        )
        .outerjoin(
            LikePublicacion,
            LikePublicacion.publicacion_id == Publicacion.id,
        )
        .filter(Publicacion.is_activa.is_(True))
        .group_by(Publicacion.id)
    )

    resultados = query.all()

    publicaciones_con_score = []

    for publicacion, likes_val, bonus_val, liked_by_me_val in resultados:
        likes_count_val = int(likes_val or 0)
        bonus_recencia_val = int(bonus_val or 0)

        guardados_count_val = obtener_guardados_count(
            db,
            publicacion_id=publicacion.id,
        )

        publicacion.guardados_count = guardados_count_val
        publicacion.interacciones_count = obtener_interacciones_count(
            db,
            publicacion_id=publicacion.id,
        )
        publicacion.likes_count = likes_count_val
        publicacion.liked_by_me = bool(liked_by_me_val)

        # Score base
        score = likes_count_val + (guardados_count_val * 2) + bonus_recencia_val

        # Bonus semántico por afinidad usuario <-> comercio de la publicación
        bonus_afinidad = 0.0

        if vector_usuario:
            vector_comercio = obtener_vector_embedding_comercio(
                db=db,
                comercio_id=publicacion.comercio_id,
            )

            if vector_comercio:
                similitud = _calcular_similitud_coseno(
                    vector_usuario,
                    vector_comercio,
                )

                # Escalamos la similitud para que impacte en el ranking
                bonus_afinidad = similitud * 10

        score_total = score + bonus_afinidad
        publicaciones_con_score.append((publicacion, score_total))

    publicaciones_con_score.sort(
        key=lambda item: (item[1], item[0].created_at),
        reverse=True,
    )

    return [item[0] for item in publicaciones_con_score]