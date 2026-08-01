import json
import tempfile
import unittest
from pathlib import Path

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.core.health import (
    DEGRADED,
    HEALTHY,
    UNHEALTHY,
    HealthCheckResult,
    HealthRegistry,
    backup_evidence_check,
    restore_evidence_check,
    uploads_storage_check,
)
from app.core.request_context import (
    CORRELATION_ID_HEADER,
    REQUEST_ID_HEADER,
    RequestContextMiddleware,
)
from app.core.operation_metrics import (
    METRIC_HEALTH_CHECK_DURATION_MS,
    METRIC_HEALTH_READINESS_STATUS,
    local_metrics_sink,
)
from app.modules.operations.routes import health_routers


def _build_test_client(registry: HealthRegistry) -> TestClient:
    app = FastAPI()
    app.add_middleware(RequestContextMiddleware)
    health_routers.health_registry = registry
    app.include_router(health_routers.router)
    return TestClient(app)


def _check(component: str, status: str) -> HealthCheckResult:
    return HealthCheckResult(
        component=component,
        status=status,
        duration_ms=1.0,
        message="Mensaje seguro.",
    )


class HealthEndpointTests(unittest.TestCase):
    def setUp(self):
        self._previous_registry = health_routers.health_registry
        local_metrics_sink.clear()

    def tearDown(self):
        health_routers.health_registry = self._previous_registry
        local_metrics_sink.clear()

    def test_liveness_returns_safe_health_report_and_context_headers(self):
        registry = HealthRegistry()
        registry.register_liveness(lambda: _check("api", HEALTHY))
        client = _build_test_client(registry)

        response = client.get("/health/live")

        self.assertEqual(response.status_code, 200)
        self.assertIn(REQUEST_ID_HEADER, response.headers)
        self.assertIn(CORRELATION_ID_HEADER, response.headers)
        payload = response.json()
        self.assertEqual(payload["status"], HEALTHY)
        self.assertEqual(payload["checks"][0]["component"], "api")
        self.assertNotIn("DATABASE_URL", json.dumps(payload))
        self.assertNotIn("SECRET_KEY", json.dumps(payload))

    def test_readiness_healthy_returns_200(self):
        registry = HealthRegistry()
        registry.register_readiness(lambda: _check("api", HEALTHY))
        registry.register_readiness(lambda: _check("database", HEALTHY))
        client = _build_test_client(registry)

        response = client.get("/health/ready", headers={CORRELATION_ID_HEADER: "flow-1"})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers[CORRELATION_ID_HEADER], "flow-1")
        self.assertEqual(response.json()["status"], HEALTHY)
        names = [sample.name for sample in local_metrics_sink.snapshot()]
        self.assertIn(METRIC_HEALTH_READINESS_STATUS, names)
        self.assertIn(METRIC_HEALTH_CHECK_DURATION_MS, names)

    def test_readiness_degraded_returns_200_without_sensitive_details(self):
        registry = HealthRegistry()
        registry.register_readiness(lambda: _check("api", HEALTHY))
        registry.register_readiness(lambda: _check("backup_evidence", DEGRADED))
        client = _build_test_client(registry)

        response = client.get("/health/ready")

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["status"], DEGRADED)
        self.assertNotIn("C:\\", json.dumps(payload))
        self.assertNotIn(".env", json.dumps(payload))

    def test_readiness_unhealthy_returns_503(self):
        registry = HealthRegistry()
        registry.register_readiness(lambda: _check("api", HEALTHY))
        registry.register_readiness(lambda: _check("database", UNHEALTHY))
        client = _build_test_client(registry)

        response = client.get("/health/ready")

        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.json()["status"], UNHEALTHY)


class HealthCheckTests(unittest.TestCase):
    def test_backup_evidence_check_reports_valid_manifest_without_exposing_path(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            directory = Path(tmpdir)
            manifest = directory / "mitienda_20260801T181443Z.sql.gz.json"
            manifest.write_text(json.dumps({"result": "ok"}), encoding="utf-8")

            result = backup_evidence_check(directory)

        self.assertEqual(result.status, HEALTHY)
        self.assertEqual(result.component, "backup_evidence")
        self.assertNotIn(tmpdir, result.message)

    def test_restore_evidence_check_reports_missing_evidence_as_degraded(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            result = restore_evidence_check(Path(tmpdir))

        self.assertEqual(result.status, DEGRADED)
        self.assertEqual(result.component, "restore_evidence")

    def test_uploads_storage_check_is_read_only(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            directory = Path(tmpdir)
            before = set(directory.iterdir())

            result = uploads_storage_check(directory)

            after = set(directory.iterdir())

        self.assertEqual(result.status, HEALTHY)
        self.assertEqual(before, after)


if __name__ == "__main__":
    unittest.main()
