# app/models/historias_vistas_models.py
"""
Modelo ORM: HistoriasVistas

Responsabilidad:
- Registrar qué usuario vio qué historia (1 vez por usuario).
- Evitar duplicados con unique constraint (historia_id, usuario_id).

Reglas del proyecto:
- Models = solo SQLAlchemy (sin lógica de negocio).
- Dominio en español: historias_vistas.
"""

from __future__ import annotations

from sqlalchemy import Column, DateTime, ForeignKey, Integer, UniqueConstraint, func
from sqlalchemy.orm import relationship

from app.core.database import Base


class HistoriaVista(Base):
    """
    Representa una vista de una historia por un usuario.

    Regla:
    - Un usuario puede "ver" una historia una sola vez (idempotente).
    """

    __tablename__ = "historias_vistas"

    # -------------------------
    # PK
    # -------------------------
    id = Column(Integer, primary_key=True, index=True)

    # -------------------------
    # FKs (relación)
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
    # Restricciones
    # -------------------------
    __table_args__ = (
        UniqueConstraint(
            "historia_id",
            "usuario_id",
            name="uq_historias_vistas_historia_usuario",
        ),
    )

    # -------------------------
    # ORM relationships (sin back_populates todavía)
    # -------------------------
    historia = relationship("Historia", lazy="selectin")
    usuario = relationship("Usuario", lazy="selectin")
