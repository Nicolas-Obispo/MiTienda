# app/modules/stories/models/historias_likes_models.py
"""
Modelo ORM: HistoriasLikes

Responsabilidad:
- Registrar likes de usuarios sobre historias.
- Evitar duplicados con unique constraint:
    1 usuario -> 1 like por historia.

Reglas del proyecto:
- Models = solo SQLAlchemy
- Sin lógica de negocio
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


class HistoriaLike(Base):
    """
    Like de un usuario sobre una historia.
    """

    __tablename__ = "historias_likes"

    # -------------------------
    # PK
    # -------------------------
    id = Column(Integer, primary_key=True, index=True)

    # -------------------------
    # Relaciones
    # -------------------------
    historia_id = Column(
        Integer,
        ForeignKey("historias.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    usuario_id = Column(
        Integer,
        ForeignKey("usuarios.id", ondelete="CASCADE"),
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
    # Restricción:
    # 1 usuario = 1 like por historia
    # -------------------------
    __table_args__ = (
        UniqueConstraint(
            "historia_id",
            "usuario_id",
            name="uq_historias_likes_historia_usuario",
        ),
    )

    # -------------------------
    # ORM relationships
    # -------------------------
    historia = relationship(
        "Historia",
        lazy="selectin",
        overlaps="likes",
    )

    usuario = relationship(
        "Usuario",
        lazy="selectin",
        overlaps="historias_likes",
    )
    