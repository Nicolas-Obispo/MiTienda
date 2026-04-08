# app/services/likes_publicaciones_services.py
"""
Service: Likes de Publicaciones

Reglas:
- Like = señal de interés (NO social)
- Toggle: si existe se elimina, si no existe se crea
- Un like por usuario y publicación

Optimización ETAPA 55:
- Evita recalcular embedding innecesariamente
- Usa ventana temporal (5 min)
"""

from typing import Optional

from sqlalchemy.orm import Session

from app.models.likes_publicaciones_models import LikePublicacion
from app.services.usuarios_embeddings_services import (
    regenerar_embedding_usuario_si_corresponde
)


def toggle_like_publicacion(
    db: Session,
    *,
    usuario_id: int,
    publicacion_id: int,
) -> bool:
    """
    Alterna el like de un usuario sobre una publicación.

    Retorna:
    - True  -> like creado
    - False -> like eliminado
    """

    like_existente: Optional[LikePublicacion] = (
        db.query(LikePublicacion)
        .filter(
            LikePublicacion.usuario_id == usuario_id,
            LikePublicacion.publicacion_id == publicacion_id,
        )
        .first()
    )

    if like_existente:
        db.delete(like_existente)
        db.commit()

        # ✅ ETAPA 55: recalcular SOLO si corresponde
        regenerar_embedding_usuario_si_corresponde(
            db=db,
            usuario_id=usuario_id,
        )

        return False

    nuevo_like = LikePublicacion(
        usuario_id=usuario_id,
        publicacion_id=publicacion_id,
    )

    db.add(nuevo_like)
    db.commit()

    # ✅ ETAPA 55: recalcular SOLO si corresponde
    regenerar_embedding_usuario_si_corresponde(
        db=db,
        usuario_id=usuario_id,
    )

    return True