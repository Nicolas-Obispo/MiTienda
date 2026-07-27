from enum import Enum

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


class TipoElementoAgenda(str, Enum):
    evento = "evento"
    tarea = "tarea"
    recordatorio = "recordatorio"
    bloqueo = "bloqueo"


class EstadoElementoAgenda(str, Enum):
    activo = "activo"
    completado = "completado"
    cancelado = "cancelado"


class EstadoContextoAgendable(str, Enum):
    activo = "activo"
    archivado = "archivado"


def _enum_values(enum_cls):
    return [item.value for item in enum_cls]


class ContextoAgendable(Base):
    """
    Identidad estable y autonoma del dominio Agenda.

    La integracion de cada aplicacion host vincula sus recursos externos con
    este contexto sin que Agenda conozca esos modelos.
    """

    __tablename__ = "agenda_contextos_agendables"

    id = Column(Integer, primary_key=True, index=True)
    estado = Column(
        SQLEnum(
            EstadoContextoAgendable,
            values_callable=_enum_values,
            native_enum=False,
            create_constraint=True,
            name="estado_contexto_agendable",
        ),
        nullable=False,
        default=EstadoContextoAgendable.activo.value,
        server_default=EstadoContextoAgendable.activo.value,
    )

    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    elementos = relationship(
        "ElementoAgenda",
        back_populates="contexto",
    )


class ElementoAgenda(Base):
    """
    Elemento privado de Agenda asociado unicamente a un ContextoAgendable.
    """

    __tablename__ = "agenda_elementos"

    id = Column(Integer, primary_key=True, index=True)
    contexto_id = Column(
        Integer,
        ForeignKey("agenda_contextos_agendables.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    tipo = Column(
        SQLEnum(
            TipoElementoAgenda,
            values_callable=_enum_values,
            native_enum=False,
            create_constraint=True,
            name="tipo_elemento_agenda",
        ),
        nullable=False,
    )
    estado = Column(
        SQLEnum(
            EstadoElementoAgenda,
            values_callable=_enum_values,
            native_enum=False,
            create_constraint=True,
            name="estado_elemento_agenda",
        ),
        nullable=False,
        default=EstadoElementoAgenda.activo.value,
        server_default=EstadoElementoAgenda.activo.value,
    )
    version = Column(Integer, nullable=False, default=1, server_default="1")
    titulo = Column(String(255), nullable=False)
    descripcion = Column(Text, nullable=True)
    inicio = Column(DateTime(timezone=True), nullable=True)
    fin = Column(DateTime(timezone=True), nullable=True)
    todo_el_dia = Column(Boolean, nullable=False, default=False, server_default="0")

    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    contexto = relationship("ContextoAgendable", back_populates="elementos")

    __table_args__ = (
        CheckConstraint(
            "fin IS NULL OR inicio IS NULL OR inicio < fin",
            name="ck_agenda_elementos_rango_temporal",
        ),
        Index("ix_agenda_elementos_contexto_inicio", "contexto_id", "inicio"),
    )
