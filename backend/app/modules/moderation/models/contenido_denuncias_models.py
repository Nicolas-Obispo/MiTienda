from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import relationship

from app.core.database import Base


class ContenidoDenuncia(Base):
    __tablename__ = "contenido_denuncias"

    id = Column(Integer, primary_key=True, index=True)
    usuario_id = Column(
        Integer,
        ForeignKey("usuarios.id"),
        nullable=False,
        index=True,
    )
    recurso_tipo = Column(String(40), nullable=False)
    recurso_id = Column(Integer, nullable=False)
    motivo = Column(String(80), nullable=False)
    detalle = Column(String(500), nullable=True)
    estado = Column(String(40), nullable=False)
    creado_en = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    usuario = relationship("Usuario", lazy="selectin")

    __table_args__ = (
        UniqueConstraint(
            "usuario_id",
            "recurso_tipo",
            "recurso_id",
            "motivo",
            name="uq_contenido_denuncias_usuario_recurso_motivo",
        ),
        Index(
            "ix_contenido_denuncias_recurso",
            "recurso_tipo",
            "recurso_id",
        ),
    )
