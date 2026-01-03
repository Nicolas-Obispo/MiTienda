# app/services/ranking_publicaciones_services.py
"""
Service: Ranking de Publicaciones

Reglas:
- Ranking = score por publicación
- Score recomendado:
    score = likes_count + (guardados_count * 2) + bonus_recencia
- Solo publicaciones activas
- Sin HTTP (esto se usa desde routers)
- No depende de usuario (liked_by_me siempre False)
"""

from datetime import datetime, timedelta
from typing import List

from sqlalchemy import case, func
from sqlalchemy.orm import Session

from app.models.publicaciones_models import Publicacion
from app.models.likes_publicaciones_models import LikePublicacion

# ✅ Import robusto del modelo de guardados (por si el nombre cambia)
try:
    from app.models.publicaciones_guardadas_models import PublicacionGuardada
except ImportError:
    # Si en tu proyecto el nombre es distinto, ajustalo acá.
    from app.models.publicaciones_guardadas_models import PublicacionGuardadaModel as PublicacionGuardada


def listar_publicaciones_ranked(db: Session) -> List[Publicacion]:
    """
    Devuelve publicaciones ordenadas por score:

    score = likes_count + (guardados_count * 2) + bonus_recencia
    """

    ahora = datetime.utcnow()

    # Bonus por recencia (mismo criterio que venías usando)
    bonus_recencia = case(
        (Publicacion.created_at >= ahora - timedelta(days=1), 3),
        (Publicacion.created_at >= ahora - timedelta(days=3), 2),
        (Publicacion.created_at >= ahora - timedelta(days=7), 1),
        else_=0,
    )

    # Contadores (distinct para evitar duplicados por joins)
    likes_count_expr = func.count(func.distinct(LikePublicacion.id))
    guardados_count_expr = func.count(func.distinct(PublicacionGuardada.id))

    # Score final
    score_expr = likes_count_expr + (guardados_count_expr * 2) + bonus_recencia

    query = (
        db.query(
            Publicacion,
            likes_count_expr.label("likes_count"),
            guardados_count_expr.label("guardados_count"),
            score_expr.label("score"),
        )
        .outerjoin(
            LikePublicacion,
            LikePublicacion.publicacion_id == Publicacion.id,
        )
        .outerjoin(
            PublicacionGuardada,
            PublicacionGuardada.publicacion_id == Publicacion.id,
        )
        .filter(Publicacion.is_activa.is_(True))
        .group_by(Publicacion.id)
        .order_by(
            func.coalesce(score_expr, 0).desc(),
            Publicacion.created_at.desc(),
        )
    )

    resultados = query.all()

    publicaciones: List[Publicacion] = []

    for publicacion, likes_count, guardados_count, _score in resultados:
        # ✅ Seteamos los campos calculados para que el schema los devuelva
        publicacion.likes_count = int(likes_count or 0)
        publicacion.guardados_count = int(guardados_count or 0)

        # Interacciones (si tu definición es otra, lo ajustamos después)
        publicacion.interacciones_count = publicacion.likes_count + publicacion.guardados_count

        # Ranking no depende de usuario
        publicacion.liked_by_me = False

        publicaciones.append(publicacion)

    return publicaciones
