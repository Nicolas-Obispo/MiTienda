import io
import tempfile
import threading
import unittest
from contextlib import redirect_stderr, redirect_stdout
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from unittest.mock import patch

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.config import settings
from app.core.database import Base
from app.core.model_registry import import_all_models
from app.modules.communications.providers.email_provider import FakeEmailProvider
from app.modules.notifications.models.operational_notification_outbox_models import OperationalNotificationOutbox
from app.modules.notifications.services.operational_notification_services import enqueue_report_created
from app.modules.operations.services.operational_worker_state_services import read_sanitized_worker_state
from run_operational_email_worker import (
    PreflightResult,
    WorkerConfig,
    WorkerMetrics,
    WorkerPreflightError,
    audit_preflight,
    main,
    process_one_cycle,
    require_ready_preflight,
    run_continuous,
)


import_all_models()


class OperationalEmailWorkerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.engine = create_engine(
            "sqlite://", connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        cls.Session = sessionmaker(bind=cls.engine)

    def setUp(self):
        Base.metadata.drop_all(self.engine)
        Base.metadata.create_all(self.engine)
        self.original = {
            "ADMIN_EMAIL_ENABLED": settings.ADMIN_EMAIL_ENABLED,
            "ADMINISTRATIVE_OPERATIONAL_EMAIL": settings.ADMINISTRATIVE_OPERATIONAL_EMAIL,
            "EMAIL_FROM_ADDRESS": settings.EMAIL_FROM_ADDRESS,
            "OPERATIONAL_EMAIL_DISPATCHER_ENABLED": settings.OPERATIONAL_EMAIL_DISPATCHER_ENABLED,
            "OPERATIONAL_EMAIL_DISPATCHER_ACTIVATED_AT": settings.OPERATIONAL_EMAIL_DISPATCHER_ACTIVATED_AT,
            "OPERATIONAL_EMAIL_BATCH_SIZE": settings.OPERATIONAL_EMAIL_BATCH_SIZE,
            "OPERATIONAL_EMAIL_POLL_INTERVAL_SECONDS": settings.OPERATIONAL_EMAIL_POLL_INTERVAL_SECONDS,
            "OPERATIONAL_EMAIL_LEASE_SECONDS": settings.OPERATIONAL_EMAIL_LEASE_SECONDS,
            "OPERATIONAL_EMAIL_WORKER_STATE_FILE": settings.OPERATIONAL_EMAIL_WORKER_STATE_FILE,
        }
        self.tempdir = tempfile.TemporaryDirectory()
        settings.OPERATIONAL_EMAIL_WORKER_STATE_FILE = f"{self.tempdir.name}/worker-state.json"
        settings.ADMIN_EMAIL_ENABLED = True
        settings.ADMINISTRATIVE_OPERATIONAL_EMAIL = "ops@example.test"
        settings.EMAIL_FROM_ADDRESS = "feedgo@example.test"
        settings.OPERATIONAL_EMAIL_DISPATCHER_ENABLED = True
        settings.OPERATIONAL_EMAIL_DISPATCHER_ACTIVATED_AT = datetime.now(timezone.utc) - timedelta(minutes=1)
        settings.OPERATIONAL_EMAIL_BATCH_SIZE = 2
        settings.OPERATIONAL_EMAIL_POLL_INTERVAL_SECONDS = 0.01
        settings.OPERATIONAL_EMAIL_LEASE_SECONDS = 30

    def tearDown(self):
        for key, value in self.original.items():
            setattr(settings, key, value)
        self.tempdir.cleanup()

    def _enqueue(self, report_id=1):
        db = self.Session()
        item = enqueue_report_created(
            db=db,
            report=SimpleNamespace(
                id=report_id, recurso_tipo="comercio", recurso_id=10,
                motivo="spam",
            ),
        )
        db.commit()
        item_id = item.id
        db.close()
        return item_id

    def _config(self, batch_size=2):
        return WorkerConfig(
            batch_size=batch_size,
            poll_interval_seconds=0.01,
            lease_seconds=30,
            activated_at=settings.OPERATIONAL_EMAIL_DISPATCHER_ACTIVATED_AT,
        )

    def test_startup_is_blocked_when_channel_or_dispatcher_is_disabled(self):
        settings.ADMIN_EMAIL_ENABLED = False
        result = audit_preflight(
            target_engine=self.engine, session_factory=self.Session,
            provider_factory=lambda: FakeEmailProvider(),
        )
        self.assertFalse(result.ready)
        self.assertFalse(result.channel_enabled)
        settings.ADMIN_EMAIL_ENABLED = True
        settings.OPERATIONAL_EMAIL_DISPATCHER_ENABLED = False
        result = audit_preflight(
            target_engine=self.engine, session_factory=self.Session,
            provider_factory=lambda: FakeEmailProvider(),
        )
        self.assertFalse(result.ready)
        self.assertFalse(result.dispatcher_enabled)

    def test_invalid_provider_configuration_blocks_startup_safely(self):
        with self.assertRaises(WorkerPreflightError):
            require_ready_preflight(
                target_engine=self.engine, session_factory=self.Session,
                provider_factory=lambda: (_ for _ in ()).throw(ValueError("private-detail")),
            )

    def test_preexisting_backlog_blocks_activation(self):
        self._enqueue()
        settings.OPERATIONAL_EMAIL_DISPATCHER_ACTIVATED_AT = datetime.now(timezone.utc) + timedelta(minutes=1)
        result = audit_preflight(
            target_engine=self.engine, session_factory=self.Session,
            provider_factory=lambda: FakeEmailProvider(),
        )
        self.assertFalse(result.ready)
        self.assertFalse(result.backlog_reconciled)

    def test_once_processes_batch_through_fake_provider(self):
        self._enqueue(1)
        self._enqueue(2)
        provider = FakeEmailProvider()
        metrics = WorkerMetrics()
        process_one_cycle(
            session_factory=self.Session, provider=provider, config=self._config(),
            claimed_by="worker-test-once", metrics=metrics,
            stop_event=threading.Event(),
        )
        self.assertEqual((metrics.cycles, metrics.claimed, metrics.sent, metrics.failed), (1, 2, 2, 0))
        self.assertEqual(len(provider.messages), 2)
        db = self.Session()
        self.assertEqual(db.query(OperationalNotificationOutbox).filter_by(status="sent").count(), 2)
        db.close()

    def test_loop_stops_after_current_delivery_and_claims_no_new_batch(self):
        self._enqueue(1)
        self._enqueue(2)
        stop_event = threading.Event()

        class StopAfterSendProvider(FakeEmailProvider):
            def send(inner_self, message):
                reference = super().send(message)
                stop_event.set()
                return reference

        metrics = run_continuous(
            session_factory=self.Session, provider=StopAfterSendProvider(),
            config=self._config(batch_size=1), stop_event=stop_event,
        )
        self.assertEqual(metrics.cycles, 1)
        self.assertEqual(metrics.claimed, 1)
        db = self.Session()
        self.assertEqual(db.query(OperationalNotificationOutbox).filter_by(status="sent").count(), 1)
        self.assertEqual(db.query(OperationalNotificationOutbox).filter_by(status="pending").count(), 1)
        db.close()

    def test_isolated_fake_delivery_transitions_heartbeat_active_to_stopped(self):
        self._enqueue(91)
        stop_event = threading.Event()
        observed = []

        class ObservingFakeProvider(FakeEmailProvider):
            def send(inner_self, message):
                observed.append(read_sanitized_worker_state()["status"])
                reference = super().send(message)
                stop_event.set()
                return reference

        provider = ObservingFakeProvider()
        metrics = run_continuous(
            session_factory=self.Session,
            provider=provider,
            config=self._config(batch_size=1),
            stop_event=stop_event,
        )
        self.assertEqual(observed, ["active"])
        self.assertEqual(read_sanitized_worker_state()["status"], "stopped")
        self.assertEqual((metrics.claimed, metrics.sent, metrics.failed), (1, 1, 0))
        self.assertEqual(len(provider.messages), 1)
        db = self.Session()
        item = db.query(OperationalNotificationOutbox).filter_by(aggregate_id="91").one()
        self.assertEqual((item.status, item.attempt_count), ("sent", 1))
        db.close()

    def test_shutdown_requested_before_cycle_claims_nothing(self):
        self._enqueue()
        stop_event = threading.Event()
        stop_event.set()
        metrics = WorkerMetrics()
        process_one_cycle(
            session_factory=self.Session, provider=FakeEmailProvider(),
            config=self._config(), claimed_by="worker-shutdown",
            metrics=metrics, stop_event=stop_event,
        )
        self.assertEqual(metrics, WorkerMetrics())
        db = self.Session()
        self.assertEqual(db.query(OperationalNotificationOutbox).one().status, "pending")
        db.close()

    def test_restart_recovers_expired_lease(self):
        item_id = self._enqueue()
        db = self.Session()
        item = db.get(OperationalNotificationOutbox, item_id)
        item.status = "processing"
        item.claimed_by = "terminated-worker"
        item.lease_expires_at = datetime.now(timezone.utc) - timedelta(seconds=1)
        item.attempt_count = 1
        db.commit()
        db.close()
        provider = FakeEmailProvider()
        metrics = WorkerMetrics()
        process_one_cycle(
            session_factory=self.Session, provider=provider, config=self._config(),
            claimed_by="restarted-worker", metrics=metrics,
            stop_event=threading.Event(),
        )
        self.assertEqual(metrics.sent, 1)
        db = self.Session()
        recovered = db.get(OperationalNotificationOutbox, item_id)
        self.assertEqual(recovered.status, "sent")
        self.assertEqual(recovered.attempt_count, 2)
        db.close()

    def test_cli_blocked_output_is_sanitized(self):
        blocked = PreflightResult(True, False, False, False, False)
        stdout, stderr = io.StringIO(), io.StringIO()
        with patch("run_operational_email_worker.audit_preflight", return_value=blocked), redirect_stdout(stdout), redirect_stderr(stderr):
            result = main(["--once"])
        output = stdout.getvalue() + stderr.getvalue()
        self.assertEqual(result, 2)
        self.assertIn("preflight_failed", output)
        self.assertNotIn("example.test", output)
        self.assertNotIn("private-detail", output)


if __name__ == "__main__":
    unittest.main()
