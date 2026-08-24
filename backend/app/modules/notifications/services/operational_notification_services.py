import hashlib
import json

from sqlalchemy.orm import Session

from app.core.config import settings
from app.modules.notifications.models.operational_notification_outbox_models import (
    OperationalNotificationOutbox,
)

REPORT_CREATED = "moderation.report.created"
INCIDENT_OPENED = "operations.incident.opened"
INCIDENT_SEVERITY_ESCALATED = "operations.incident.severity_escalated"
OPERATIONAL_EMAIL_SMOKE = "operations.email.smoke"
NOTIFIABLE_SEVERITIES = frozenset({"sev1_critical", "sev2_high"})
SEVERITY_RANK = {"sev4_low": 1, "sev3_medium": 2, "sev2_high": 3, "sev1_critical": 4}


def _enqueue(*, db: Session, event_type: str, aggregate_type: str, aggregate_id: str,
             deduplication_key: str, payload: dict) -> OperationalNotificationOutbox:
    serialized = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    fingerprint = hashlib.sha256(serialized.encode("utf-8")).hexdigest()
    existing = db.query(OperationalNotificationOutbox).filter(
        OperationalNotificationOutbox.deduplication_key == deduplication_key
    ).first()
    if existing is not None:
        if existing.payload_fingerprint != fingerprint:
            raise ValueError("notification_deduplication_conflict")
        return existing
    item = OperationalNotificationOutbox(
        event_type=event_type,
        aggregate_type=aggregate_type,
        aggregate_id=aggregate_id,
        deduplication_key=deduplication_key,
        payload_json=serialized,
        payload_fingerprint=fingerprint,
        status="pending",
        attempt_count=0,
    )
    db.add(item)
    return item


def enqueue_report_created(*, db: Session, report) -> OperationalNotificationOutbox:
    return _enqueue(
        db=db,
        event_type=REPORT_CREATED,
        aggregate_type="moderation_report",
        aggregate_id=str(report.id),
        deduplication_key=f"{REPORT_CREATED}:{report.id}",
        payload={
            "report_id": report.id,
            "resource_type": report.recurso_tipo,
            "resource_id": report.recurso_id,
            "reason_code": report.motivo,
        },
    )


def incident_severity_is_notifiable(severity: str) -> bool:
    return severity in NOTIFIABLE_SEVERITIES or settings.ADMIN_EMAIL_NOTIFY_SEV3_SEV4


def enqueue_incident_opened(*, db: Session, incident) -> OperationalNotificationOutbox | None:
    if not incident_severity_is_notifiable(incident.severity):
        return None
    return _enqueue(
        db=db,
        event_type=INCIDENT_OPENED,
        aggregate_type="operational_incident",
        aggregate_id=incident.public_id,
        deduplication_key=f"{INCIDENT_OPENED}:{incident.public_id}",
        payload={
            "incident_public_id": incident.public_id,
            "incident_type": incident.incident_type,
            "severity": incident.severity,
        },
    )


def enqueue_incident_escalated(*, db: Session, incident, previous_severity: str) -> OperationalNotificationOutbox | None:
    if (
        not incident_severity_is_notifiable(incident.severity)
        or SEVERITY_RANK.get(incident.severity, 0) <= SEVERITY_RANK.get(previous_severity, 0)
    ):
        return None
    return _enqueue(
        db=db,
        event_type=INCIDENT_SEVERITY_ESCALATED,
        aggregate_type="operational_incident",
        aggregate_id=incident.public_id,
        deduplication_key=f"{INCIDENT_SEVERITY_ESCALATED}:{incident.public_id}:{incident.version}",
        payload={
            "incident_public_id": incident.public_id,
            "incident_type": incident.incident_type,
            "previous_severity": previous_severity,
            "severity": incident.severity,
            "resulting_version": incident.version,
        },
    )


def enqueue_operational_email_smoke(*, db: Session, smoke_id: str) -> OperationalNotificationOutbox:
    """Intencion tecnica explicita; no crea denuncias ni incidentes ficticios."""
    return _enqueue(
        db=db,
        event_type=OPERATIONAL_EMAIL_SMOKE,
        aggregate_type="operational_email_smoke",
        aggregate_id=smoke_id,
        deduplication_key=f"{OPERATIONAL_EMAIL_SMOKE}:{smoke_id}",
        payload={"smoke_id": smoke_id},
    )
