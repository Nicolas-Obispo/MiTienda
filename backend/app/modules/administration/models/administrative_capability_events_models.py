from sqlalchemy import Column, DateTime, ForeignKey, Index, Integer, String, func
from sqlalchemy.orm import relationship

from app.core.database import Base


class AdministrativeCapabilityEvent(Base):
    """Evento append-only que otorga o revoca una capacidad administrativa."""

    __tablename__ = "administrative_capability_events"

    id = Column(Integer, primary_key=True, index=True)
    usuario_id = Column(
        Integer,
        ForeignKey("usuarios.id"),
        nullable=False,
        index=True,
    )
    capability = Column(String(80), nullable=False)
    action = Column(String(20), nullable=False)
    actor_usuario_id = Column(
        Integer,
        ForeignKey("usuarios.id"),
        nullable=True,
        index=True,
    )
    source = Column(String(40), nullable=False)
    reason = Column(String(500), nullable=False)
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    usuario = relationship("Usuario", foreign_keys=[usuario_id])
    actor_usuario = relationship("Usuario", foreign_keys=[actor_usuario_id])

    __table_args__ = (
        Index(
            "ix_admin_capability_events_user_capability_id",
            "usuario_id",
            "capability",
            "id",
        ),
    )
