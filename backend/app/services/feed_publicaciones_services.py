# app/services/feed_publicaciones_services.py
"""
Service: Feed personalizado de Publicaciones

Reglas:
- Feed orientado a descubrimiento
- Ranking basado en likes + recencia
- Incluye:
  - likes_count
  - views_count
  - liked_by_me (según usuario autenticado)
- Sin lógica HTTP
"""

from datetime import datetime, timedelta
from typing import List, Optional

from sqlalchemy import func, case, exists
from sqlalchemy.orm import Session

from app.models.publicaciones_models import Publicacion
from app.models.likes_publicaciones_models import LikePublicacion


def obtener_feed_publicaciones(
    db: Session,
    *,
    usuario_id: Optional[int] = None,
) -> List[Publicacion]:
    """
    Devuelve publicaciones para el feed personalizado.

    Si usuario_id es None:
    - liked_by_me siempre False
    """

    ahora = datetime.utcnow()

    # Bonus por recencia
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

    # Subquery para saber si el usuario dio like
    liked_by_me_subquery = (
        exists()
        .where(
            LikePublicacion.publicacion_id == Publicacion.id,
        )
        .where(
            LikePublicacion.usuario_id == usuario_id,
        )
    )

    query = (
        db.query(
            Publicacion,
            likes_count.label("likes_count"),
            (likes_count + bonus_recencia).label("score"),
            liked_by_me_subquery.label("liked_by_me"),
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

    # Por ahora devolvemos solo las publicaciones (los extras se usan luego)
    return [row[0] for row in query.all()]
