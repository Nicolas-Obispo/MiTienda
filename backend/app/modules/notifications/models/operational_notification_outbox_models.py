from sqlalchemy import Column, DateTime, Index, Integer, String, Text, UniqueConstraint, func

from app.core.database import Base


class OperationalNotificationOutbox(Base):
    __tablename__ = "operational_notification_outbox"

    id = Column(Integer, primary_key=True)
    event_type = Column(String(80), nullable=False)
    aggregate_type = Column(String(40), nullable=False)
    aggregate_id = Column(String(80), nullable=False)
    deduplication_key = Column(String(190), nullable=False)
    payload_json = Column(Text, nullable=False)
    payload_fingerprint = Column(String(64), nullable=False)
    status = Column(String(32), nullable=False, server_default="pending")
    attempt_count = Column(Integer, nullable=False, server_default="0")
    next_attempt_at = Column(DateTime(timezone=True), nullable=True)
    lease_expires_at = Column(DateTime(timezone=True), nullable=True)
    claimed_by = Column(String(80), nullable=True)
    provider_reference = Column(String(190), nullable=True)
    last_error_code = Column(String(80), nullable=True)
    suppressed_at = Column(DateTime(timezone=True), nullable=True)
    suppressed_by = Column(String(80), nullable=True)
    suppression_reason = Column(String(80), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    sent_at = Column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        UniqueConstraint("deduplication_key", name="uq_operational_notification_outbox_dedupe"),
        Index(
            "ix_operational_notification_outbox_dispatch",
            "status",
            "next_attempt_at",
            "lease_expires_at",
            "id",
        ),
    )
