# app/services/feed_publicaciones_services.py
"""
Service: Feed personalizado de Publicaciones

ETAPA 55 FINAL:
- sin N+1 en guardados
- sin N+1 en embeddings de comercios
- cálculo eficiente en memoria
"""

from datetime import datetime, timedelta
from typing import List, Optional

from sqlalchemy import func, case, literal
from sqlalchemy.orm import Session

from app.models.publicaciones_models import Publicacion
from app.models.likes_publicaciones_models import LikePublicacion

from app.services.publicaciones_services import (
    obtener_guardados_count_por_publicaciones,
    obtener_interacciones_count_por_publicaciones,
)
from app.services.usuarios_embeddings_services import obtener_vector_usuario
from app.services.comercios_embeddings_services import (
    obtener_vectores_embeddings_comercios,
)


def _calcular_similitud_coseno(vector_a: list, vector_b: list) -> float:
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

    ahora = datetime.utcnow()

    # -------------------------------------
    # Embedding usuario (1 sola vez)
    # -------------------------------------
    vector_usuario = None
    tiene_vector_usuario = False

    if usuario_id is not None:
        vector_usuario = obtener_vector_usuario(db=db, usuario_id=usuario_id)
        tiene_vector_usuario = bool(vector_usuario)

    # -------------------------------------
    # Bonus recencia
    # -------------------------------------
    bonus_recencia = case(
        (Publicacion.created_at >= ahora - timedelta(days=1), 3),
        (Publicacion.created_at >= ahora - timedelta(days=3), 2),
        (Publicacion.created_at >= ahora - timedelta(days=7), 1),
        else_=0,
    )

    likes_count_expr = func.count(LikePublicacion.id)

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

    if not resultados:
        return []

    # -------------------------------------
    # IDs base
    # -------------------------------------
    publicaciones_ids = [p.id for p, _, _, _ in resultados]
    comercios_ids = [p.comercio_id for p, _, _, _ in resultados]

    # -------------------------------------
    # MAPAS BULK
    # -------------------------------------

    # likes
    likes_count_map = {
        p.id: int(likes_val or 0)
        for p, likes_val, _, _ in resultados
    }

    # guardados (1 query)
    guardados_count_map = obtener_guardados_count_por_publicaciones(
        db=db,
        publicaciones_ids=publicaciones_ids,
    )

    # interacciones (sin query extra)
    interacciones_count_map = obtener_interacciones_count_por_publicaciones(
        publicaciones_ids=publicaciones_ids,
        likes_count_map=likes_count_map,
        guardados_count_map=guardados_count_map,
    )

    # embeddings comercios (1 query 🔥)
    vectores_comercios_map = {}

    if tiene_vector_usuario:
        vectores_comercios_map = obtener_vectores_embeddings_comercios(
            db=db,
            comercios_ids=comercios_ids,
        )

    # -------------------------------------
    # ARMADO FINAL
    # -------------------------------------
    publicaciones_con_score = []

    for publicacion, likes_val, bonus_val, liked_by_me_val in resultados:

        likes_count_val = likes_count_map.get(publicacion.id, 0)
        guardados_count_val = guardados_count_map.get(publicacion.id, 0)
        interacciones_count_val = interacciones_count_map.get(publicacion.id, 0)
        bonus_recencia_val = int(bonus_val or 0)

        publicacion.guardados_count = guardados_count_val
        publicacion.interacciones_count = interacciones_count_val
        publicacion.likes_count = likes_count_val
        publicacion.liked_by_me = bool(liked_by_me_val)

        # Score base
        score_base = (
            likes_count_val
            + (guardados_count_val * 2)
            + bonus_recencia_val
        )

        # Afinidad IA
        bonus_afinidad = 0.0

        if tiene_vector_usuario:
            vector_comercio = vectores_comercios_map.get(publicacion.comercio_id)

            if vector_comercio:
                similitud = _calcular_similitud_coseno(
                    vector_usuario,
                    vector_comercio,
                )

                bonus_afinidad = similitud * 10

        score_total = score_base + bonus_afinidad
        publicaciones_con_score.append((publicacion, score_total))

    publicaciones_con_score.sort(
        key=lambda item: (item[1], item[0].created_at),
        reverse=True,
    )

    return [item[0] for item in publicaciones_con_score]