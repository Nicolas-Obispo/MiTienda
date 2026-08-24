"""Smoke local, explicito y de una unica entrega para el correo operativo."""

import argparse
import os
import sys
import uuid
from dataclasses import dataclass

from sqlalchemy import inspect
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

from app.core.database import SessionLocal, engine
from app.modules.communications.providers.email_provider import EmailProvider
from app.modules.communications.services.email_provider_factory import build_configured_email_provider
from app.modules.communications.services.operational_email_services import deliver_pending_operational_email
from app.modules.notifications.models.operational_notification_outbox_models import OperationalNotificationOutbox
from app.modules.notifications.services.operational_notification_services import enqueue_operational_email_smoke
from migrate_operational_notification_outbox import TABLE_NAME

SMOKE_GATE_ENV = "FEEDGO_OPERATIONAL_EMAIL_SMOKE"
SMOKE_GATE_VALUE = "send-one"
EXPECTED_COLUMNS = frozenset({
    "id", "event_type", "aggregate_type", "aggregate_id", "deduplication_key",
    "payload_json", "payload_fingerprint", "status", "attempt_count",
    "next_attempt_at", "provider_reference", "last_error_code", "created_at", "sent_at",
    "lease_expires_at", "claimed_by", "suppressed_at", "suppressed_by",
    "suppression_reason",
})


@dataclass(frozen=True)
class SchemaAudit:
    table_present: bool
    metadata_match: bool
    unique_deduplication: bool


@dataclass(frozen=True)
class SmokeResult:
    delivered: bool
    status: str
    attempt_count: int
    external_reference_present: bool


def audit_outbox_schema(target_engine: Engine) -> SchemaAudit:
    """Inspeccion read-only: no ejecuta DDL ni create_all."""
    with target_engine.connect() as connection:
        inspector = inspect(connection)
        if TABLE_NAME not in inspector.get_table_names():
            return SchemaAudit(False, False, False)
        columns = {column["name"] for column in inspector.get_columns(TABLE_NAME)}
        unique_constraints = {
            tuple(constraint["column_names"])
            for constraint in inspector.get_unique_constraints(TABLE_NAME)
        }
    return SchemaAudit(
        table_present=True,
        metadata_match=columns == EXPECTED_COLUMNS,
        unique_deduplication=("deduplication_key",) in unique_constraints,
    )


def run_single_smoke(*, db: Session, provider: EmailProvider, gate_value: str | None,
                     smoke_id: str | None = None) -> SmokeResult:
    if gate_value != SMOKE_GATE_VALUE:
        raise PermissionError("operational_email_smoke_gate_required")
    identifier = smoke_id or uuid.uuid4().hex
    item = enqueue_operational_email_smoke(db=db, smoke_id=identifier)
    db.commit()
    db.refresh(item)

    delivered = deliver_pending_operational_email(db=db, outbox_id=item.id, provider=provider)
    db.refresh(item)
    if item.attempt_count != 1:
        raise RuntimeError("operational_email_smoke_invalid_attempt_count")
    if delivered and (item.status != "sent" or not item.provider_reference):
        raise RuntimeError("operational_email_smoke_invalid_success_state")
    if not delivered and item.status == "sent":
        raise RuntimeError("operational_email_smoke_invalid_failure_state")
    return SmokeResult(
        delivered=delivered,
        status=item.status,
        attempt_count=item.attempt_count,
        external_reference_present=bool(item.provider_reference),
    )


def _audit_command() -> int:
    result = audit_outbox_schema(engine)
    print("mode=audit read_only=true")
    print(f"table_present={str(result.table_present).lower()}")
    print(f"metadata_match={str(result.metadata_match).lower()}")
    print(f"unique_deduplication={str(result.unique_deduplication).lower()}")
    return 0 if result.table_present and result.metadata_match and result.unique_deduplication else 2


def _send_command() -> int:
    if os.getenv(SMOKE_GATE_ENV) != SMOKE_GATE_VALUE:
        print("smoke=blocked reason=explicit_gate_required", file=sys.stderr)
        return 2
    audit = audit_outbox_schema(engine)
    if not (audit.table_present and audit.metadata_match and audit.unique_deduplication):
        print("smoke=blocked reason=outbox_schema_not_ready", file=sys.stderr)
        return 2
    try:
        provider = build_configured_email_provider()
    except Exception:
        print("smoke=blocked reason=email_configuration_invalid", file=sys.stderr)
        return 2
    if provider is None:
        print("smoke=blocked reason=email_delivery_disabled", file=sys.stderr)
        return 2

    db = SessionLocal()
    try:
        result = run_single_smoke(
            db=db,
            provider=provider,
            gate_value=SMOKE_GATE_VALUE,
        )
    except Exception:
        db.rollback()
        print("smoke=failed result=sanitized", file=sys.stderr)
        return 1
    finally:
        db.close()
    print(f"smoke={'sent' if result.delivered else 'failed'}")
    print(f"status={result.status}")
    print(f"attempt_count={result.attempt_count}")
    print(f"external_reference_present={str(result.external_reference_present).lower()}")
    return 0 if result.delivered else 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Smoke controlado del correo operativo")
    modes = parser.add_mutually_exclusive_group(required=True)
    modes.add_argument("--audit", action="store_true", help="Inspecciona el esquema sin modificarlo")
    modes.add_argument("--send-one", action="store_true", help="Envia exactamente una intencion explicita")
    args = parser.parse_args(argv)
    return _audit_command() if args.audit else _send_command()


if __name__ == "__main__":
    raise SystemExit(main())
