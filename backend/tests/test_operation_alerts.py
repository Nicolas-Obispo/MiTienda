import unittest
from datetime import datetime, timedelta, timezone

from app.core.operation_alerts import (
    ALERT_SEVERITY_CRITICAL,
    ALERT_SEVERITY_WARNING,
    ALERT_STATUS_ACTIVE,
    ALERT_STATUS_SUPPRESSED,
    AlertEngine,
    LocalAlertSink,
    default_alert_rules,
)
from app.core.operation_metrics import (
    METRIC_BACKUP_RUN_COUNT,
    METRIC_HEALTH_CHECK_DURATION_MS,
    METRIC_HEALTH_READINESS_STATUS,
    METRIC_HTTP_RESPONSE_5XX_COUNT,
    METRIC_RESTORE_RUN_COUNT,
    METRIC_UPLOAD_REJECTED_COUNT,
    clear_metric_listeners,
    increment_counter,
    local_metrics_sink,
    record_duration,
    record_gauge,
    register_metric_listener,
)


class Clock:
    def __init__(self) -> None:
        self.now = datetime(2026, 8, 1, 12, 0, 0, tzinfo=timezone.utc)

    def __call__(self) -> datetime:
        return self.now

    def advance(self, seconds: int) -> None:
        self.now += timedelta(seconds=seconds)


class OperationAlertsTests(unittest.TestCase):
    def setUp(self):
        local_metrics_sink.clear()
        clear_metric_listeners()
        self.clock = Clock()
        self.sink = LocalAlertSink()
        self.engine = AlertEngine(
            rules=default_alert_rules(),
            sink=self.sink,
            metrics_snapshot_provider=local_metrics_sink.snapshot,
            clock=self.clock,
        )
        register_metric_listener(self.engine.evaluate_metric_sample)

    def tearDown(self):
        local_metrics_sink.clear()
        clear_metric_listeners()

    def test_readiness_unhealthy_emits_critical_alert(self):
        record_gauge(
            METRIC_HEALTH_READINESS_STATUS,
            0,
            tags={"status": "unhealthy"},
        )

        alerts = self.sink.snapshot()

        self.assertEqual(len(alerts), 1)
        self.assertEqual(alerts[0].rule_name, "readiness_unhealthy")
        self.assertEqual(alerts[0].severity, ALERT_SEVERITY_CRITICAL)
        self.assertEqual(alerts[0].status, ALERT_STATUS_ACTIVE)
        self.assertEqual(alerts[0].context["status"], "unhealthy")

    def test_repeated_5xx_waits_for_threshold_and_uses_cooldown(self):
        for _ in range(2):
            increment_counter(
                METRIC_HTTP_RESPONSE_5XX_COUNT,
                tags={"method": "GET", "route": "/broken", "status": "500"},
            )

        self.assertEqual(self.sink.snapshot(), [])

        increment_counter(
            METRIC_HTTP_RESPONSE_5XX_COUNT,
            tags={"method": "GET", "route": "/broken", "status": "500"},
        )
        increment_counter(
            METRIC_HTTP_RESPONSE_5XX_COUNT,
            tags={"method": "GET", "route": "/broken", "status": "500"},
        )

        alerts = self.sink.snapshot()
        self.assertEqual(alerts[0].rule_name, "http_5xx_repeated")
        self.assertEqual(alerts[0].status, ALERT_STATUS_ACTIVE)
        self.assertEqual(alerts[1].status, ALERT_STATUS_SUPPRESSED)

    def test_cooldown_allows_new_active_alert_after_window(self):
        for _ in range(3):
            increment_counter(
                METRIC_HTTP_RESPONSE_5XX_COUNT,
                tags={"method": "GET", "route": "/broken", "status": "500"},
            )

        self.clock.advance(301)
        for _ in range(3):
            increment_counter(
                METRIC_HTTP_RESPONSE_5XX_COUNT,
                tags={"method": "GET", "route": "/broken", "status": "500"},
            )

        active_alerts = [
            alert for alert in self.sink.snapshot()
            if alert.status == ALERT_STATUS_ACTIVE
        ]
        self.assertEqual(len(active_alerts), 2)

    def test_backup_failure_and_backup_evidence_degraded_emit_alerts(self):
        increment_counter(
            METRIC_BACKUP_RUN_COUNT,
            tags={"provider": "mysqldump", "result": "failed"},
        )
        record_duration(
            METRIC_HEALTH_CHECK_DURATION_MS,
            2.0,
            tags={"component": "backup_evidence", "status": "degraded"},
        )

        alerts = self.sink.snapshot()
        self.assertEqual(alerts[0].rule_name, "backup_failed")
        self.assertEqual(alerts[0].severity, ALERT_SEVERITY_CRITICAL)
        self.assertEqual(alerts[1].rule_name, "backup_evidence_not_healthy")
        self.assertEqual(alerts[1].severity, ALERT_SEVERITY_WARNING)

    def test_restore_failure_emits_critical_alert(self):
        increment_counter(
            METRIC_RESTORE_RUN_COUNT,
            tags={"provider": "mysql_client", "result": "failed"},
        )

        alerts = self.sink.snapshot()

        self.assertEqual(len(alerts), 1)
        self.assertEqual(alerts[0].rule_name, "restore_failed")
        self.assertEqual(alerts[0].severity, ALERT_SEVERITY_CRITICAL)

    def test_repeated_upload_failures_emit_warning_alert(self):
        for _ in range(5):
            increment_counter(
                METRIC_UPLOAD_REJECTED_COUNT,
                tags={"reason": "size", "media_type": "image"},
            )

        alerts = self.sink.snapshot()

        self.assertEqual(alerts[0].rule_name, "uploads_rejected_repeated")
        self.assertEqual(alerts[0].severity, ALERT_SEVERITY_WARNING)
        self.assertEqual(alerts[0].context["reason"], "size")

    def test_alert_context_never_keeps_sensitive_tags(self):
        increment_counter(
            METRIC_BACKUP_RUN_COUNT,
            tags={
                "provider": "mysqldump",
                "result": "failed",
                "token": "secret",
                "password": "secret",
            },
        )

        alert = self.sink.snapshot()[0]
        serialized = repr(alert)

        self.assertNotIn("token", serialized)
        self.assertNotIn("password", serialized)
        self.assertNotIn("secret", serialized)


if __name__ == "__main__":
    unittest.main()
