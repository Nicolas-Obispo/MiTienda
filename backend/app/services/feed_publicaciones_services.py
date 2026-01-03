# app/services/feed_publicaciones_services.py
"""
Service: Feed personalizado de Publicaciones

- Calcula likes_count y liked_by_me en la misma query (sin EXISTS -> evita auto-correlation)
- Score:
  score = likes_count + (guardados_count * 2) + bonus_recencia
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


def obtener_feed_publicaciones(
    db: Session,
    *,
    usuario_id: Optional[int] = None,
) -> List[Publicacion]:
    """
    Devuelve publicaciones para el feed personalizado.
    """

    ahora = datetime.utcnow()

    # Bonus por recencia
    bonus_recencia = case(
        (Publicacion.created_at >= ahora - timedelta(days=1), 3),
        (Publicacion.created_at >= ahora - timedelta(days=3), 2),
        (Publicacion.created_at >= ahora - timedelta(days=7), 1),
        else_=0,
    )

    # likes_count por publicación (vía LEFT JOIN)
    likes_count_expr = func.count(LikePublicacion.id)

    # liked_by_me sin EXISTS (anti auto-correlation):
    # si usuario_id coincide con un like de esa publicación => 1, sino 0
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

        # ✅ FIX: likes_count real en response
        publicacion.likes_count = likes_count_val

        # ✅ liked_by_me real en response
        publicacion.liked_by_me = bool(liked_by_me_val)

        score = likes_count_val + (guardados_count_val * 2) + bonus_recencia_val
        publicaciones_con_score.append((publicacion, score))

    publicaciones_con_score.sort(
        key=lambda item: (item[1], item[0].created_at),
        reverse=True,
    )

    return [item[0] for item in publicaciones_con_score]
