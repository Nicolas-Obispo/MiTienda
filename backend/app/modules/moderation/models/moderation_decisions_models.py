from sqlalchemy import Column, DateTime, ForeignKey, Index, Integer, String, Text, UniqueConstraint, func

from app.core.database import Base


class ModerationDecision(Base):
    """Decision administrativa append-only, separada de denuncia y recurso."""

    __tablename__ = "moderation_decisions"

    id = Column(Integer, primary_key=True, index=True)
    denuncia_id = Column(Integer, ForeignKey("contenido_denuncias.id", ondelete="RESTRICT"), nullable=False, index=True)
    operador_usuario_id = Column(Integer, ForeignKey("usuarios.id", ondelete="RESTRICT"), nullable=False, index=True)
    accion = Column(String(40), nullable=False)
    motivo_codigo = Column(String(80), nullable=False)
    fundamento = Column(String(1000), nullable=False)
    evidencia_resumen = Column(String(1000), nullable=False)
    evidencia_referencia = Column(String(500), nullable=True)
    resultado = Column(String(40), nullable=False)
    recurso_tipo = Column(String(40), nullable=False)
    recurso_id = Column(Integer, nullable=False)
    estado_recurso_anterior = Column(String(40), nullable=False)
    estado_recurso_resultante = Column(String(40), nullable=False)
    expected_denuncia_version = Column(Integer, nullable=False)
    denuncia_version_resultante = Column(Integer, nullable=False)
    expected_resource_revision = Column(Integer, nullable=True)
    resource_revision_anterior = Column(Integer, nullable=False)
    resource_revision_resultante = Column(Integer, nullable=False)
    reverses_decision_id = Column(Integer, ForeignKey("moderation_decisions.id", ondelete="RESTRICT"), nullable=True)
    idempotency_key = Column(String(64), nullable=False)
    request_fingerprint = Column(String(64), nullable=False)
    creado_en = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    __table_args__ = (
        UniqueConstraint("idempotency_key", name="uq_moderation_decisions_idempotency_key"),
        Index("ix_moderation_decisions_report_created_id", "denuncia_id", "creado_en", "id"),
        Index("ix_moderation_decisions_resource_created_id", "recurso_tipo", "recurso_id", "creado_en", "id"),
    )
