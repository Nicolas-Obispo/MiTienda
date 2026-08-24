import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

from app.core.config import settings
from app.modules.operations.services.operational_worker_state_services import (
    publish_worker_state,
    read_sanitized_worker_state,
)


class OperationalWorkerStateTests(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        self.original = {
            "ADMIN_EMAIL_ENABLED": settings.ADMIN_EMAIL_ENABLED,
            "OPERATIONAL_EMAIL_DISPATCHER_ENABLED": settings.OPERATIONAL_EMAIL_DISPATCHER_ENABLED,
            "OPERATIONAL_EMAIL_WORKER_STATE_FILE": settings.OPERATIONAL_EMAIL_WORKER_STATE_FILE,
            "OPERATIONAL_EMAIL_WORKER_HEARTBEAT_TTL_SECONDS": settings.OPERATIONAL_EMAIL_WORKER_HEARTBEAT_TTL_SECONDS,
            "OPERATIONAL_EMAIL_POLL_INTERVAL_SECONDS": settings.OPERATIONAL_EMAIL_POLL_INTERVAL_SECONDS,
        }
        settings.OPERATIONAL_EMAIL_WORKER_STATE_FILE = str(Path(self.tempdir.name) / "worker.json")
        settings.OPERATIONAL_EMAIL_WORKER_HEARTBEAT_TTL_SECONDS = 10
        settings.OPERATIONAL_EMAIL_POLL_INTERVAL_SECONDS = 1

    def tearDown(self):
        for key, value in self.original.items():
            setattr(settings, key, value)
        self.tempdir.cleanup()

    def enable(self):
        settings.ADMIN_EMAIL_ENABLED = True
        settings.OPERATIONAL_EMAIL_DISPATCHER_ENABLED = True

    def test_disabled_gates_report_disabled_without_reading_runtime_state(self):
        settings.ADMIN_EMAIL_ENABLED = False
        settings.OPERATIONAL_EMAIL_DISPATCHER_ENABLED = True
        self.assertEqual(read_sanitized_worker_state()["status"], "disabled")

    def test_enabled_without_heartbeat_reports_stopped(self):
        self.enable()
        self.assertEqual(read_sanitized_worker_state()["status"], "stopped")

    def test_fresh_active_heartbeat_reports_active(self):
        self.enable()
        publish_worker_state("active")
        self.assertEqual(read_sanitized_worker_state()["status"], "active")

    def test_stopped_heartbeat_reports_stopped(self):
        self.enable()
        publish_worker_state("stopped")
        self.assertEqual(read_sanitized_worker_state()["status"], "stopped")

    def test_stale_or_invalid_heartbeat_is_safely_stopped(self):
        self.enable()
        publish_worker_state("active")
        future = datetime.now(timezone.utc) + timedelta(seconds=30)
        self.assertEqual(read_sanitized_worker_state(now=future)["status"], "stopped")
        Path(settings.OPERATIONAL_EMAIL_WORKER_STATE_FILE).write_text("private-invalid", encoding="utf-8")
        self.assertEqual(read_sanitized_worker_state()["status"], "stopped")


if __name__ == "__main__":
    unittest.main()
