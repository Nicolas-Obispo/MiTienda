# app/models/likes_publicaciones_models.py
"""
Modelo ORM: Likes de Publicaciones

Reglas:
- Like = señal de interés (NO social)
- Un usuario puede dar like una sola vez por publicación
- Base para ranking y métricas
"""

from __future__ import annotations

from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Integer,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import relationship

from app.core.database import Base


class LikePublicacion(Base):
    """
    Representa un like (señal de interés) de un usuario sobre una publicación.
    """

    __tablename__ = "likes_publicaciones"

    # -------------------------
    # PK
    # -------------------------
    id = Column(Integer, primary_key=True, index=True)

    # -------------------------
    # Relaciones
    # -------------------------
    usuario_id = Column(
        Integer,
        ForeignKey("usuarios.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    publicacion_id = Column(
        Integer,
        ForeignKey("publicaciones.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # -------------------------
    # Auditoría
    # -------------------------
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    # -------------------------
    # Constraints
    # -------------------------
    __table_args__ = (
        UniqueConstraint(
            "usuario_id",
            "publicacion_id",
            name="uq_usuario_publicacion_like",
        ),
    )

    # -------------------------
    # ORM relationships
    # -------------------------
    usuario = relationship(
        "Usuario",
        back_populates="likes_publicaciones",
        lazy="selectin",
    )

    publicacion = relationship(
        "Publicacion",
        back_populates="likes",
        lazy="selectin",
    )
