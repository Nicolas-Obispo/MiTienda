import json
import re
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from sqlalchemy import and_, or_
from sqlalchemy.orm import Session

from app.core.config import settings
from app.modules.communications.providers.email_provider import EmailDeliveryError, EmailMessage, EmailProvider
from app.modules.notifications.models.operational_notification_outbox_models import OperationalNotificationOutbox


ACTIONABLE_STATUSES = frozenset({"pending", "retryable_failed"})
TERMINAL_STATUSES = frozenset({"sent", "permanent_failed", "suppressed"})
SUPPRESSION_REASONS = frozenset({
    "pre_activation_synthetic",
    "operator_requested",
    "invalid_legacy_intent",
})
OPAQUE_REFERENCE_PATTERN = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9._:-]{0,79}$")


class OperationalEmailConflictError(ValueError):
    pass


class OperationalEmailBacklogError(RuntimeError):
    pass


@dataclass(frozen=True)
class ClaimedOperationalEmail:
    outbox_id: int
    event_type: str
    payload_json: str
    deduplication_key: str
    claimed_by: str
    attempt_count: int


@dataclass(frozen=True)
class BacklogReconciliationResult:
    matched: int
    suppressed_now: int
    already_suppressed: int


def _utc(value: datetime) -> datetime:
    return value if value.tzinfo is not None else value.replace(tzinfo=timezone.utc)


def _configured_destination() -> tuple[str, str]:
    recipient = (settings.ADMINISTRATIVE_OPERATIONAL_EMAIL or "").strip()
    sender = (settings.EMAIL_FROM_ADDRESS or "").strip()
    if not recipient or "@" not in recipient or not sender or "@" not in sender:
        raise EmailDeliveryError("email_configuration_invalid", retryable=False)
    return recipient, sender


def _render(event_type: str, payload_json: str) -> tuple[str, str]:
    payload = json.loads(payload_json)
    if event_type == "moderation.report.created":
        return "Nueva denuncia en FeedGo", f"Denuncia {payload['report_id']} sobre {payload['resource_type']} {payload['resource_id']}."
    if event_type == "operations.email.smoke":
        return (
            "[FeedGo] Prueba controlada de correo operativo",
            "El canal operativo de FeedGo fue validado mediante una prueba controlada.",
        )
    return "Incidente operativo en FeedGo", f"Incidente {payload['incident_public_id']} con severidad {payload['severity']}."


def assert_dispatcher_activation_ready(*, db: Session, activated_at: datetime) -> None:
    """Impide activar el procesamiento si existe backlog anterior sin reconciliar."""
    backlog_exists = db.query(OperationalNotificationOutbox.id).filter(
        OperationalNotificationOutbox.created_at < activated_at,
        OperationalNotificationOutbox.status.in_((*ACTIONABLE_STATUSES, "processing")),
    ).first() is not None
    if backlog_exists:
        raise OperationalEmailBacklogError("operational_email_backlog_requires_reconciliation")


def claim_due_operational_emails(
    *, db: Session, claimed_by: str, now: datetime | None = None,
    limit: int = 25, lease_seconds: int | None = None,
    only_outbox_id: int | None = None,
) -> list[ClaimedOperationalEmail]:
    """Reclama y confirma filas; ninguna llamada al provider ocurre bajo el lock."""
    if not OPAQUE_REFERENCE_PATTERN.fullmatch(claimed_by):
        raise ValueError("operational_email_claimed_by_invalid")
    current = now or datetime.now(timezone.utc)
    lease_duration = lease_seconds or settings.OPERATIONAL_EMAIL_LEASE_SECONDS
    if lease_duration <= 0:
        raise ValueError("operational_email_lease_invalid")
    max_attempts = settings.ADMIN_EMAIL_MAX_ATTEMPTS
    due_actionable = and_(
        OperationalNotificationOutbox.status.in_(ACTIONABLE_STATUSES),
        or_(
            OperationalNotificationOutbox.next_attempt_at.is_(None),
            OperationalNotificationOutbox.next_attempt_at <= current,
        ),
    )
    expired_processing = and_(
        OperationalNotificationOutbox.status == "processing",
        OperationalNotificationOutbox.lease_expires_at.is_not(None),
        OperationalNotificationOutbox.lease_expires_at <= current,
    )
    query = db.query(OperationalNotificationOutbox).filter(
        OperationalNotificationOutbox.attempt_count < max_attempts,
        or_(due_actionable, expired_processing),
    )
    if only_outbox_id is not None:
        query = query.filter(OperationalNotificationOutbox.id == only_outbox_id)
    rows = (
        query.order_by(OperationalNotificationOutbox.id.asc())
        .with_for_update(skip_locked=True)
        .limit(max(1, min(limit, 100)))
        .all()
    )
    lease_expires_at = current + timedelta(seconds=lease_duration)
    claims: list[ClaimedOperationalEmail] = []
    for item in rows:
        item.status = "processing"
        item.claimed_by = claimed_by
        item.lease_expires_at = lease_expires_at
        item.next_attempt_at = None
        item.attempt_count += 1
        claims.append(ClaimedOperationalEmail(
            outbox_id=item.id,
            event_type=item.event_type,
            payload_json=item.payload_json,
            deduplication_key=item.deduplication_key,
            claimed_by=claimed_by,
            attempt_count=item.attempt_count,
        ))
    db.commit()
    return claims


def _finish_claim(
    *, db: Session, claim: ClaimedOperationalEmail, status: str,
    provider_reference: str | None = None, error_code: str | None = None,
    next_attempt_at: datetime | None = None, sent_at: datetime | None = None,
) -> bool:
    item = db.query(OperationalNotificationOutbox).filter(
        OperationalNotificationOutbox.id == claim.outbox_id,
    ).with_for_update().first()
    if item is None or item.status != "processing" or item.claimed_by != claim.claimed_by:
        db.rollback()
        return False
    item.status = status
    item.provider_reference = provider_reference[:190] if provider_reference else None
    item.last_error_code = error_code[:80] if error_code else None
    item.next_attempt_at = next_attempt_at
    item.sent_at = sent_at
    item.claimed_by = None
    item.lease_expires_at = None
    db.commit()
    return True


def deliver_claimed_operational_email(
    *, db: Session, claim: ClaimedOperationalEmail, provider: EmailProvider,
    now: datetime | None = None,
) -> bool:
    """Ejecuta el efecto externo sin mantener el lock de reclamacion."""
    current = now or datetime.now(timezone.utc)
    try:
        recipient, sender = _configured_destination()
        subject, body = _render(claim.event_type, claim.payload_json)
        reference = provider.send(EmailMessage(
            recipient=recipient,
            sender=sender,
            subject=subject,
            body=body,
            idempotency_key=claim.deduplication_key,
        ))
        return _finish_claim(
            db=db, claim=claim, status="sent", provider_reference=reference,
            sent_at=current,
        )
    except EmailDeliveryError as exc:
        exhausted = claim.attempt_count >= settings.ADMIN_EMAIL_MAX_ATTEMPTS
        permanent = not exc.retryable or exhausted
        retry_at = None if permanent else current + timedelta(minutes=2 ** claim.attempt_count)
        _finish_claim(
            db=db, claim=claim,
            status="permanent_failed" if permanent else "retryable_failed",
            error_code=exc.safe_code, next_attempt_at=retry_at,
        )
        return False
    except Exception:
        exhausted = claim.attempt_count >= settings.ADMIN_EMAIL_MAX_ATTEMPTS
        retry_at = None if exhausted else current + timedelta(minutes=2 ** claim.attempt_count)
        _finish_claim(
            db=db, claim=claim,
            status="permanent_failed" if exhausted else "retryable_failed",
            error_code="email_provider_unavailable", next_attempt_at=retry_at,
        )
        return False


def suppress_operational_email(
    *, db: Session, outbox_id: int, suppressed_by: str, reason: str,
    now: datetime | None = None,
) -> OperationalNotificationOutbox:
    if not OPAQUE_REFERENCE_PATTERN.fullmatch(suppressed_by):
        raise ValueError("operational_email_suppressed_by_invalid")
    if reason not in SUPPRESSION_REASONS:
        raise ValueError("operational_email_suppression_reason_invalid")
    item = db.query(OperationalNotificationOutbox).filter(
        OperationalNotificationOutbox.id == outbox_id,
    ).with_for_update().first()
    if item is None:
        db.rollback()
        raise LookupError("operational_email_not_found")
    if item.status not in ACTIONABLE_STATUSES:
        db.rollback()
        raise OperationalEmailConflictError("operational_email_not_suppressible")
    item.status = "suppressed"
    item.suppressed_at = now or datetime.now(timezone.utc)
    item.suppressed_by = suppressed_by
    item.suppression_reason = reason
    item.next_attempt_at = None
    item.claimed_by = None
    item.lease_expires_at = None
    db.commit()
    db.refresh(item)
    return item


def reconcile_pre_activation_report_intentions(
    *, db: Session, report_ids: frozenset[int], suppressed_by: str,
    now: datetime | None = None,
) -> BacklogReconciliationResult:
    """Reconcilia un conjunto previamente auditado en una unica transaccion."""
    if not report_ids or any(report_id <= 0 for report_id in report_ids):
        raise ValueError("operational_email_report_ids_invalid")
    if not OPAQUE_REFERENCE_PATTERN.fullmatch(suppressed_by):
        raise ValueError("operational_email_suppressed_by_invalid")
    expected_ids = {str(report_id) for report_id in report_ids}
    rows = db.query(OperationalNotificationOutbox).filter(
        OperationalNotificationOutbox.aggregate_type == "moderation_report",
        OperationalNotificationOutbox.aggregate_id.in_(expected_ids),
    ).order_by(OperationalNotificationOutbox.id.asc()).with_for_update().all()
    if len(rows) != len(report_ids) or {row.aggregate_id for row in rows} != expected_ids:
        db.rollback()
        raise OperationalEmailConflictError("operational_email_backlog_set_incomplete")
    suppressed_now = 0
    already_suppressed = 0
    suppressed_at = now or datetime.now(timezone.utc)
    for item in rows:
        if item.event_type != "moderation.report.created":
            db.rollback()
            raise OperationalEmailConflictError("operational_email_backlog_event_invalid")
        if item.status == "suppressed":
            if (
                item.suppression_reason != "pre_activation_synthetic"
                or item.suppressed_by != suppressed_by
                or item.suppressed_at is None
            ):
                db.rollback()
                raise OperationalEmailConflictError("operational_email_backlog_suppression_mismatch")
            already_suppressed += 1
            continue
        if item.status != "pending" or item.attempt_count != 0:
            db.rollback()
            raise OperationalEmailConflictError("operational_email_backlog_not_suppressible")
        item.status = "suppressed"
        item.suppressed_at = suppressed_at
        item.suppressed_by = suppressed_by
        item.suppression_reason = "pre_activation_synthetic"
        item.next_attempt_at = None
        item.claimed_by = None
        item.lease_expires_at = None
        suppressed_now += 1
    db.commit()
    return BacklogReconciliationResult(
        matched=len(rows),
        suppressed_now=suppressed_now,
        already_suppressed=already_suppressed,
    )


def deliver_pending_operational_email(*, db: Session, outbox_id: int, provider: EmailProvider) -> bool:
    """Entrega explicita de compatibilidad; no instala scheduler ni loop."""
    if not settings.ADMIN_EMAIL_ENABLED:
        return False
    claimed_by = f"explicit-{uuid.uuid4().hex}"
    claims = claim_due_operational_emails(
        db=db, claimed_by=claimed_by, limit=1, only_outbox_id=outbox_id,
    )
    return bool(claims) and deliver_claimed_operational_email(db=db, claim=claims[0], provider=provider)


def deliver_due_operational_emails(*, db: Session, provider: EmailProvider, limit: int = 25) -> int:
    """Dispatcher acotado e invocable; esta etapa no instala scheduler alguno."""
    if not settings.ADMIN_EMAIL_ENABLED:
        return 0
    claimed_by = f"batch-{uuid.uuid4().hex}"
    claims = claim_due_operational_emails(db=db, claimed_by=claimed_by, limit=limit)
    return sum(
        int(deliver_claimed_operational_email(db=db, claim=claim, provider=provider))
        for claim in claims
    )
