"""
Modelo ORM para franjas semanales de atencion de comercios.
"""

from sqlalchemy import (
    CheckConstraint,
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Time,
)
from sqlalchemy.sql import func

from app.core.database import Base


class ComercioHorarioAtencion(Base):
    """
    Franja habitual semanal de atencion declarada por un comercio.

    La ausencia de filas para un comercio significa que no hay horarios declarados.
    """

    __tablename__ = "comercios_horarios_atencion"

    id = Column(Integer, primary_key=True, index=True)

    comercio_id = Column(
        Integer,
        ForeignKey("comercios.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    dia_semana = Column(Integer, nullable=False)
    hora_apertura = Column(Time, nullable=False)
    hora_cierre = Column(Time, nullable=False)

    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    __table_args__ = (
        CheckConstraint(
            "dia_semana >= 0 AND dia_semana <= 6",
            name="ck_comercios_horarios_atencion_dia_semana",
        ),
        CheckConstraint(
            "hora_apertura < hora_cierre",
            name="ck_comercios_horarios_atencion_rango_horario",
        ),
        Index(
            "ix_comercios_horarios_atencion_comercio_dia",
            "comercio_id",
            "dia_semana",
        ),
    )
