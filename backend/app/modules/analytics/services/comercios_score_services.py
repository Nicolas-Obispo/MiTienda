"""
comercios_score_services.py
---------------------------
Motor de scoring interno para espacios MiPlaza.

Este score NO es visual solamente.
Se usa para:

- explorar
- ranking
- feed
- IA
- recomendaciones
- espacios destacados

Diseñado como sistema escalable.
"""

from sqlalchemy.orm import Session

from app.modules.analytics.services.comercios_analytics_services import (
    obtener_analytics_espacio,
)


def calcular_space_score(
    db: Session,
    comercio_id: int,
):
    """
    Calcula score interno del espacio.

    Fórmula v1:
    combinación de actividad + interacción.
    """

    analytics = obtener_analytics_espacio(
        db=db,
        comercio_id=comercio_id,
    )

    metricas = analytics["metricas"]
    derivadas = analytics["metricas_derivadas"]

    score = 0

    # -------------------------------------------------
    # Seguidores
    # -------------------------------------------------

    score += metricas["total_seguidores"] * 5

    # -------------------------------------------------
    # Publicaciones
    # -------------------------------------------------

    score += metricas["total_publicaciones"] * 3

    # -------------------------------------------------
    # Likes publicaciones
    # -------------------------------------------------

    score += metricas["total_likes_publicaciones"] * 2

    # -------------------------------------------------
    # Guardados (más valiosos)
    # -------------------------------------------------

    score += metricas["total_guardados_publicaciones"] * 4

    # -------------------------------------------------
    # Historias
    # -------------------------------------------------

    score += metricas["total_historias"] * 1

    # -------------------------------------------------
    # Vistas historias
    # -------------------------------------------------

    score += metricas["total_vistas_historias"] * 1

    # -------------------------------------------------
    # Likes historias
    # -------------------------------------------------

    score += metricas["total_likes_historias"] * 2

    # -------------------------------------------------
    # Engagement publicaciones
    # -------------------------------------------------

    score += derivadas["engagement_publicaciones"] * 1.5

    return {
        "comercio_id": comercio_id,
        "space_score": round(score, 2),

        "factores": {
            "seguidores": metricas["total_seguidores"],
            "publicaciones": metricas["total_publicaciones"],
            "likes_publicaciones": metricas["total_likes_publicaciones"],
            "guardados_publicaciones": metricas["total_guardados_publicaciones"],
            "historias": metricas["total_historias"],
            "vistas_historias": metricas["total_vistas_historias"],
            "likes_historias": metricas["total_likes_historias"],
            "engagement_publicaciones": derivadas["engagement_publicaciones"],
        },
    }