# app/services/ranking_publicaciones_services.py
"""
Service: Ranking de Publicaciones

Reglas:
- Ranking basado en likes + recencia
- Like = señal de interés (NO social)
- Solo publicaciones activas
- Sin HTTP (esto se usa desde routers)
"""

from datetime import datetime, timedelta
from typing import List

from sqlalchemy import func, case
from sqlalchemy.orm import Session

from app.models.publicaciones_models import Publicacion
from app.models.likes_publicaciones_models import LikePublicacion


def listar_publicaciones_ranked(
    db: Session,
) -> List[Publicacion]:
    """
    Devuelve publicaciones ordenadas por score:
    score = likes + bonus por recencia
    """

    ahora = datetime.utcnow()

    # Definición de bonus por recencia
    bonus_recencia = case(
        (
            Publicacion.created_at >= ahora - timedelta(days=1),
            3,
        ),
        (
            Publicacion.created_at >= ahora - timedelta(days=3),
            2,
        ),
        (
            Publicacion.created_at >= ahora - timedelta(days=7),
            1,
        ),
        else_=0,
    )

    likes_count = func.count(LikePublicacion.id)

    query = (
        db.query(
            Publicacion,
            likes_count.label("likes_count"),
            (likes_count + bonus_recencia).label("score"),
        )
        .outerjoin(
            LikePublicacion,
            LikePublicacion.publicacion_id == Publicacion.id,
        )
        .filter(
            Publicacion.is_activa.is_(True),
        )
        .group_by(Publicacion.id)
        .order_by(
            func.coalesce((likes_count + bonus_recencia), 0).desc(),
            Publicacion.created_at.desc(),
        )
    )

    # Devuelve solo las publicaciones (el resto se usa internamente)
    return [row[0] for row in query.all()]
