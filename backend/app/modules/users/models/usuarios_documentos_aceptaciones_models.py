"""
usuarios_documentos_aceptaciones_models.py
------------------------------------------
Modelo ORM para evidencia minima de aceptacion de documentos versionados.
"""

from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Index, Integer, String
from sqlalchemy.orm import relationship
from sqlalchemy.schema import UniqueConstraint

from app.core.database import Base


class UsuarioDocumentoAceptacion(Base):
    """
    Registra la aceptacion o estado de un documento versionado aplicable a un
    usuario.
    """

    __tablename__ = "usuarios_documentos_aceptaciones"

    id = Column(Integer, primary_key=True, index=True)
    usuario_id = Column(
        Integer,
        ForeignKey("usuarios.id"),
        nullable=False,
        index=True,
    )
    documento_tipo = Column(String(80), nullable=False)
    documento_version = Column(String(40), nullable=False)
    aceptado_en = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    canal = Column(String(30), nullable=False)
    metodo = Column(String(40), nullable=False)
    estado = Column(String(30), nullable=False)
    documento_referencia = Column(String(160), nullable=False)

    usuario = relationship("Usuario", backref="documentos_aceptaciones")

    __table_args__ = (
        UniqueConstraint(
            "usuario_id",
            "documento_tipo",
            "documento_version",
            name="uq_usuario_documento_version",
        ),
        Index(
            "ix_usuarios_documentos_tipo_version",
            "documento_tipo",
            "documento_version",
        ),
    )
