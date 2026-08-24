"""Worker dedicado del monolito para el correo operativo administrativo."""

import argparse
import signal
import sys
import threading
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Callable

from sqlalchemy import inspect
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import SessionLocal, engine
from app.modules.communications.providers.email_provider import EmailProvider
from app.modules.communications.services.email_provider_factory import build_configured_email_provider
from app.modules.communications.services.operational_email_services import (
    OperationalEmailBacklogError,
    assert_dispatcher_activation_ready,
    claim_due_operational_emails,
    deliver_claimed_operational_email,
)
from app.modules.operations.services.operational_worker_state_services import publish_worker_state
from migrate_operational_notification_outbox import TABLE_NAME


REQUIRED_COLUMNS = frozenset({
    "id", "event_type", "aggregate_type", "aggregate_id", "deduplication_key",
    "payload_json", "payload_fingerprint", "status", "attempt_count",
    "next_attempt_at", "lease_expires_at", "claimed_by", "provider_reference",
    "last_error_code", "suppressed_at", "suppressed_by", "suppression_reason",
    "created_at", "sent_at",
})
DISPATCH_INDEX = "ix_operational_notification_outbox_dispatch"


class WorkerPreflightError(RuntimeError):
    pass


@dataclass(frozen=True)
class WorkerConfig:
    batch_size: int
    poll_interval_seconds: float
    lease_seconds: int
    activated_at: datetime


@dataclass
class WorkerMetrics:
    cycles: int = 0
    claimed: int = 0
    sent: int = 0
    failed: int = 0


@dataclass(frozen=True)
class PreflightResult:
    schema_ready: bool
    channel_enabled: bool
    dispatcher_enabled: bool
    configuration_ready: bool
    backlog_reconciled: bool

    @property
    def ready(self) -> bool:
        return all((
            self.schema_ready,
            self.channel_enabled,
            self.dispatcher_enabled,
            self.configuration_ready,
            self.backlog_reconciled,
        ))


def schema_is_ready(target_engine: Engine) -> bool:
    """Inspeccion read-only del contrato fisico requerido por el worker."""
    with target_engine.connect() as connection:
        inspector = inspect(connection)
        if TABLE_NAME not in inspector.get_table_names():
            return False
        columns = {column["name"] for column in inspector.get_columns(TABLE_NAME)}
        indexes = {index["name"] for index in inspector.get_indexes(TABLE_NAME)}
        unique_constraints = {
            tuple(constraint["column_names"])
            for constraint in inspector.get_unique_constraints(TABLE_NAME)
        }
    return (
        REQUIRED_COLUMNS <= columns
        and DISPATCH_INDEX in indexes
        and ("deduplication_key",) in unique_constraints
    )


def worker_config_from_settings() -> WorkerConfig:
    if settings.OPERATIONAL_EMAIL_DISPATCHER_ACTIVATED_AT is None:
        raise WorkerPreflightError("worker_activation_timestamp_required")
    if not 1 <= settings.OPERATIONAL_EMAIL_BATCH_SIZE <= 100:
        raise WorkerPreflightError("worker_batch_size_invalid")
    if settings.OPERATIONAL_EMAIL_POLL_INTERVAL_SECONDS <= 0:
        raise WorkerPreflightError("worker_poll_interval_invalid")
    if settings.OPERATIONAL_EMAIL_LEASE_SECONDS <= 0:
        raise WorkerPreflightError("worker_lease_invalid")
    activated_at = settings.OPERATIONAL_EMAIL_DISPATCHER_ACTIVATED_AT
    if activated_at.tzinfo is None:
        activated_at = activated_at.replace(tzinfo=timezone.utc)
    return WorkerConfig(
        batch_size=settings.OPERATIONAL_EMAIL_BATCH_SIZE,
        poll_interval_seconds=settings.OPERATIONAL_EMAIL_POLL_INTERVAL_SECONDS,
        lease_seconds=settings.OPERATIONAL_EMAIL_LEASE_SECONDS,
        activated_at=activated_at,
    )


def audit_preflight(
    *, target_engine: Engine = engine,
    session_factory: Callable[[], Session] = SessionLocal,
    provider_factory: Callable[[], EmailProvider | None] = build_configured_email_provider,
) -> PreflightResult:
    schema_ready = schema_is_ready(target_engine)
    channel_enabled = bool(settings.ADMIN_EMAIL_ENABLED)
    dispatcher_enabled = bool(settings.OPERATIONAL_EMAIL_DISPATCHER_ENABLED)
    configuration_ready = False
    backlog_reconciled = False
    config: WorkerConfig | None = None
    try:
        config = worker_config_from_settings()
        configuration_ready = provider_factory() is not None
    except Exception:
        configuration_ready = False
    if schema_ready and config is not None:
        db = session_factory()
        try:
            assert_dispatcher_activation_ready(db=db, activated_at=config.activated_at)
            backlog_reconciled = True
        except OperationalEmailBacklogError:
            backlog_reconciled = False
        finally:
            db.close()
    return PreflightResult(
        schema_ready=schema_ready,
        channel_enabled=channel_enabled,
        dispatcher_enabled=dispatcher_enabled,
        configuration_ready=configuration_ready,
        backlog_reconciled=backlog_reconciled,
    )


def require_ready_preflight(**kwargs) -> tuple[WorkerConfig, EmailProvider]:
    result = audit_preflight(**kwargs)
    if not result.ready:
        raise WorkerPreflightError("operational_email_worker_preflight_failed")
    provider_factory = kwargs.get("provider_factory", build_configured_email_provider)
    provider = provider_factory()
    if provider is None:
        raise WorkerPreflightError("operational_email_provider_unavailable")
    return worker_config_from_settings(), provider


def process_one_cycle(
    *, session_factory: Callable[[], Session], provider: EmailProvider,
    config: WorkerConfig, claimed_by: str, metrics: WorkerMetrics,
    stop_event: threading.Event,
) -> None:
    if stop_event.is_set():
        return
    db = session_factory()
    try:
        claims = claim_due_operational_emails(
            db=db,
            claimed_by=claimed_by,
            limit=config.batch_size,
            lease_seconds=config.lease_seconds,
        )
        metrics.cycles += 1
        metrics.claimed += len(claims)
        for claim in claims:
            # Una vez reclamado, el intento en curso termina de forma controlada.
            delivered = deliver_claimed_operational_email(
                db=db, claim=claim, provider=provider,
            )
            metrics.sent += int(delivered)
            metrics.failed += int(not delivered)
    finally:
        db.close()


def run_continuous(
    *, session_factory: Callable[[], Session], provider: EmailProvider,
    config: WorkerConfig, stop_event: threading.Event,
    metrics: WorkerMetrics | None = None,
) -> WorkerMetrics:
    counters = metrics or WorkerMetrics()
    claimed_by = f"worker-{uuid.uuid4().hex}"
    publish_worker_state("active")
    try:
        while not stop_event.is_set():
            process_one_cycle(
                session_factory=session_factory,
                provider=provider,
                config=config,
                claimed_by=claimed_by,
                metrics=counters,
                stop_event=stop_event,
            )
            publish_worker_state("active")
            if stop_event.wait(config.poll_interval_seconds):
                break
    finally:
        publish_worker_state("stopped")
    return counters


def install_shutdown_handlers(stop_event: threading.Event) -> None:
    def request_shutdown(_signum, _frame):
        stop_event.set()

    signal.signal(signal.SIGINT, request_shutdown)
    if hasattr(signal, "SIGTERM"):
        signal.signal(signal.SIGTERM, request_shutdown)
    if hasattr(signal, "SIGBREAK"):
        signal.signal(signal.SIGBREAK, request_shutdown)


def _print_preflight(result: PreflightResult) -> None:
    print("mode=audit read_only=true")
    print(f"schema_ready={str(result.schema_ready).lower()}")
    print(f"channel_enabled={str(result.channel_enabled).lower()}")
    print(f"dispatcher_enabled={str(result.dispatcher_enabled).lower()}")
    print(f"configuration_ready={str(result.configuration_ready).lower()}")
    print(f"backlog_reconciled={str(result.backlog_reconciled).lower()}")
    print(f"worker_ready={str(result.ready).lower()}")


def _print_metrics(metrics: WorkerMetrics) -> None:
    print("worker=stopped")
    print(f"cycles={metrics.cycles}")
    print(f"claimed={metrics.claimed}")
    print(f"sent={metrics.sent}")
    print(f"failed={metrics.failed}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Worker de correo operativo FeedGo")
    modes = parser.add_mutually_exclusive_group(required=True)
    modes.add_argument("--audit", action="store_true", help="Preflight read-only")
    modes.add_argument("--once", action="store_true", help="Procesa un unico lote elegible")
    modes.add_argument("--run", action="store_true", help="Ejecuta el loop continuo")
    args = parser.parse_args(argv)
    if args.audit:
        result = audit_preflight()
        _print_preflight(result)
        return 0 if result.ready else 2
    try:
        config, provider = require_ready_preflight()
    except Exception:
        print("worker=blocked reason=preflight_failed", file=sys.stderr)
        return 2
    stop_event = threading.Event()
    install_shutdown_handlers(stop_event)
    metrics = WorkerMetrics()
    try:
        if args.once:
            process_one_cycle(
                session_factory=SessionLocal, provider=provider, config=config,
                claimed_by=f"worker-once-{uuid.uuid4().hex}", metrics=metrics,
                stop_event=stop_event,
            )
        else:
            run_continuous(
                session_factory=SessionLocal, provider=provider, config=config,
                stop_event=stop_event, metrics=metrics,
            )
    except Exception:
        print("worker=failed result=sanitized", file=sys.stderr)
        return 1
    _print_metrics(metrics)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
