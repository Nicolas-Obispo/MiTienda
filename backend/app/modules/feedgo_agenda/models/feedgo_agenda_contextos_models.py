"""
Modelo de integracion entre FeedGo y el nucleo Agenda.
"""

from sqlalchemy import Column, DateTime, ForeignKey, Integer, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


class FeedGoAgendaContexto(Base):
    """
    Vincula un Comercio de FeedGo con un ContextoAgendable.

    No pertenece al nucleo Agenda y no duplica datos del comercio.
    """

    __tablename__ = "feedgo_agenda_contextos"

    id = Column(Integer, primary_key=True, index=True)
    comercio_id = Column(
        Integer,
        ForeignKey("comercios.id", ondelete="RESTRICT"),
        nullable=False,
    )
    agenda_contexto_id = Column(
        Integer,
        ForeignKey("agenda_contextos_agendables.id", ondelete="RESTRICT"),
        nullable=False,
    )

    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    comercio = relationship("Comercio")
    agenda_contexto = relationship("ContextoAgendable")

    __table_args__ = (
        UniqueConstraint("comercio_id", name="uq_feedgo_agenda_contextos_comercio_id"),
        UniqueConstraint(
            "agenda_contexto_id",
            name="uq_feedgo_agenda_contextos_agenda_contexto_id",
        ),
    )
