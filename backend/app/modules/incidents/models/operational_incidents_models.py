from sqlalchemy import Column, DateTime, ForeignKey, Index, Integer, String, Text, UniqueConstraint, func

from app.core.database import Base


class OperationalIncident(Base):
    """Fuente oficial del estado vigente de un incidente operativo."""

    __tablename__ = "operational_incidents"

    id = Column(Integer, primary_key=True, index=True)
    public_id = Column(String(40), nullable=False, unique=True)
    title = Column(String(160), nullable=False)
    summary_sanitized = Column(String(1200), nullable=False)
    incident_type = Column(String(40), nullable=False)
    severity = Column(String(20), nullable=False)
    status = Column(String(20), nullable=False, server_default="open")
    owner_usuario_id = Column(Integer, ForeignKey("usuarios.id", ondelete="RESTRICT"), nullable=False, index=True)
    opened_by_usuario_id = Column(Integer, ForeignKey("usuarios.id", ondelete="RESTRICT"), nullable=False, index=True)
    version = Column(Integer, nullable=False, server_default="1")
    operational_deadline_at = Column(DateTime(timezone=True), nullable=True)
    contained_at = Column(DateTime(timezone=True), nullable=True)
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    reviewed_at = Column(DateTime(timezone=True), nullable=True)
    residual_risk_level = Column(String(20), nullable=True)
    residual_risk_summary = Column(String(1000), nullable=True)
    residual_risk_owner_usuario_id = Column(Integer, ForeignKey("usuarios.id", ondelete="RESTRICT"), nullable=True)
    residual_risk_review_at = Column(DateTime(timezone=True), nullable=True)
    legal_assessment_status = Column(String(30), nullable=False, server_default="pending")
    personal_data_impact = Column(String(30), nullable=False, server_default="unknown")
    legal_owner_usuario_id = Column(Integer, ForeignKey("usuarios.id", ondelete="RESTRICT"), nullable=True)
    user_communication_status = Column(String(30), nullable=False, server_default="pending")
    authority_communication_status = Column(String(30), nullable=False, server_default="pending")
    legal_deadline_at = Column(DateTime(timezone=True), nullable=True)
    idempotency_key = Column(String(64), nullable=False)
    request_fingerprint = Column(String(64), nullable=False)
    opened_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        UniqueConstraint("idempotency_key", name="uq_operational_incidents_idempotency_key"),
        Index("ix_operational_incidents_status_severity_id", "status", "severity", "id"),
        Index("ix_operational_incidents_owner_status_id", "owner_usuario_id", "status", "id"),
    )


class OperationalIncidentEvent(Base):
    """Evento append-only de la cronologia segura de un incidente."""

    __tablename__ = "operational_incident_events"

    id = Column(Integer, primary_key=True, index=True)
    incident_id = Column(Integer, ForeignKey("operational_incidents.id", ondelete="RESTRICT"), nullable=False)
    event_type = Column(String(40), nullable=False)
    actor_usuario_id = Column(Integer, ForeignKey("usuarios.id", ondelete="RESTRICT"), nullable=False, index=True)
    status_before = Column(String(20), nullable=True)
    status_after = Column(String(20), nullable=False)
    severity_before = Column(String(20), nullable=True)
    severity_after = Column(String(20), nullable=False)
    owner_before_usuario_id = Column(Integer, ForeignKey("usuarios.id", ondelete="RESTRICT"), nullable=True)
    owner_after_usuario_id = Column(Integer, ForeignKey("usuarios.id", ondelete="RESTRICT"), nullable=False)
    safe_summary = Column(String(1200), nullable=False)
    evidence_type = Column(String(40), nullable=True)
    evidence_reference = Column(String(128), nullable=True)
    request_id = Column(String(128), nullable=True)
    correlation_id = Column(String(128), nullable=True)
    alert_id = Column(String(128), nullable=True)
    safe_details_json = Column(Text, nullable=True)
    expected_incident_version = Column(Integer, nullable=False)
    resulting_incident_version = Column(Integer, nullable=False)
    idempotency_key = Column(String(64), nullable=False)
    request_fingerprint = Column(String(64), nullable=False)
    occurred_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    __table_args__ = (
        UniqueConstraint("idempotency_key", name="uq_operational_incident_events_idempotency_key"),
        Index("ix_operational_incident_events_incident_id", "incident_id", "id"),
    )
