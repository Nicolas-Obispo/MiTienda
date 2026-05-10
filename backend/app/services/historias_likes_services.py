# app/services/historias_likes_services.py
"""
Service: historias_likes_services

Responsabilidad:
- Registrar likes de usuarios sobre historias.
- Permitir toggle like / unlike.
- Mantener una interacción real persistida para métricas futuras del espacio.

Reglas:
- Services = lógica/orquestación.
- No acceder a request/response aquí.
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.historias_models import Historia
from app.models.historias_likes_models import HistoriaLike


def toggle_like_historia(
    db: Session,
    *,
    historia_id: int,
    usuario_id: int,
) -> dict:
    """
    Alterna el like de una historia.

    - Si no existe la historia -> ValueError.
    - Si el usuario ya dio like -> lo quita.
    - Si no dio like -> lo crea.

    Retorna:
    {
        "liked": bool,
        "likes_count": int
    }
    """

    historia = db.query(Historia).filter(Historia.id == historia_id).first()

    if not historia:
        raise ValueError("Historia no encontrada")

    like_existente = (
        db.query(HistoriaLike)
        .filter(
            HistoriaLike.historia_id == historia_id,
            HistoriaLike.usuario_id == usuario_id,
        )
        .first()
    )

    if like_existente:
        db.delete(like_existente)
        db.commit()
        liked = False
    else:
        nuevo_like = HistoriaLike(
            historia_id=historia_id,
            usuario_id=usuario_id,
        )

        db.add(nuevo_like)
        db.commit()
        liked = True

    likes_count = (
        db.query(HistoriaLike)
        .filter(HistoriaLike.historia_id == historia_id)
        .count()
    )

    return {
        "liked": liked,
        "likes_count": likes_count,
    }