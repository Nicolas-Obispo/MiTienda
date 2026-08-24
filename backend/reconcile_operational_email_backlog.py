"""Reconciliacion local y controlada del backlog sintetico previo al worker."""

import argparse
import os
import sys
from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.modules.communications.services.operational_email_services import (
    OperationalEmailConflictError,
    reconcile_pre_activation_report_intentions,
)
from app.modules.notifications.models.operational_notification_outbox_models import (
    OperationalNotificationOutbox,
)


ALLOWED_REPORT_IDS = frozenset({2, 3, 4})
SUPPRESSED_BY = "backlog-reconcile-cli"
GATE_ENV = "FEEDGO_OPERATIONAL_EMAIL_BACKLOG_RECONCILE"
GATE_VALUE = "suppress-2-3-4"


@dataclass(frozen=True)
class BacklogAudit:
    matched: int
    pending: int
    suppressed: int
    valid: bool


def validate_report_ids(report_ids: list[int]) -> frozenset[int]:
    selected = frozenset(report_ids)
    if selected != ALLOWED_REPORT_IDS or len(report_ids) != len(ALLOWED_REPORT_IDS):
        raise PermissionError("operational_email_backlog_allowlist_required")
    return selected


def audit_backlog(*, db: Session, report_ids: frozenset[int]) -> BacklogAudit:
    expected = {str(report_id) for report_id in report_ids}
    rows = db.query(
        OperationalNotificationOutbox.aggregate_id,
        OperationalNotificationOutbox.event_type,
        OperationalNotificationOutbox.status,
        OperationalNotificationOutbox.attempt_count,
        OperationalNotificationOutbox.suppressed_at,
        OperationalNotificationOutbox.suppressed_by,
        OperationalNotificationOutbox.suppression_reason,
    ).filter(
        OperationalNotificationOutbox.aggregate_type == "moderation_report",
        OperationalNotificationOutbox.aggregate_id.in_(expected),
    ).all()
    valid = len(rows) == len(report_ids) and {row.aggregate_id for row in rows} == expected
    pending = 0
    suppressed = 0
    for row in rows:
        if row.event_type != "moderation.report.created":
            valid = False
        if row.status == "pending" and row.attempt_count == 0:
            pending += 1
        elif (
            row.status == "suppressed"
            and row.attempt_count == 0
            and row.suppressed_at is not None
            and row.suppressed_by == SUPPRESSED_BY
            and row.suppression_reason == "pre_activation_synthetic"
        ):
            suppressed += 1
        else:
            valid = False
    return BacklogAudit(
        matched=len(rows), pending=pending, suppressed=suppressed, valid=valid,
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Reconcilia backlog sintetico de correo operativo")
    modes = parser.add_mutually_exclusive_group(required=True)
    modes.add_argument("--audit", action="store_true", help="Inspeccion read-only")
    modes.add_argument("--suppress", action="store_true", help="Supresion atomica allowlisted")
    parser.add_argument("--report-ids", nargs="+", type=int, required=True)
    args = parser.parse_args(argv)
    try:
        selected = validate_report_ids(args.report_ids)
    except PermissionError:
        print("reconciliation=blocked reason=allowlist_required", file=sys.stderr)
        return 2
    if args.suppress and os.getenv(GATE_ENV) != GATE_VALUE:
        print("reconciliation=blocked reason=explicit_gate_required", file=sys.stderr)
        return 2
    db = SessionLocal()
    try:
        before = audit_backlog(db=db, report_ids=selected)
        if not before.valid:
            print("reconciliation=blocked reason=backlog_contract_invalid", file=sys.stderr)
            return 2
        if args.audit:
            print("mode=audit read_only=true")
            print(f"matched={before.matched}")
            print(f"pending={before.pending}")
            print(f"suppressed={before.suppressed}")
            print("backlog_contract_valid=true")
            return 0
        result = reconcile_pre_activation_report_intentions(
            db=db, report_ids=selected, suppressed_by=SUPPRESSED_BY,
        )
    except (OperationalEmailConflictError, ValueError, LookupError):
        db.rollback()
        print("reconciliation=failed result=sanitized", file=sys.stderr)
        return 1
    finally:
        db.close()
    print("reconciliation=completed")
    print(f"matched={result.matched}")
    print(f"suppressed_now={result.suppressed_now}")
    print(f"already_suppressed={result.already_suppressed}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
