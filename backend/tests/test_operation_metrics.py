import unittest
import time

from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient

from app.modules.media.routes.media_routers import _record_upload_metrics
from app.modules.spaces.services.comercios_services import _record_search_no_results_metric
from app.core.error_handlers import register_exception_handlers
from app.core.operation_metrics import (
    METRIC_AUTH_FAILURE_COUNT,
    METRIC_AUTHORIZATION_FAILURE_COUNT,
    METRIC_HTTP_REQUEST_COUNT,
    METRIC_HTTP_REQUEST_DURATION_MS,
    METRIC_HTTP_RESPONSE_4XX_COUNT,
    METRIC_HTTP_UNHANDLED_ERROR_COUNT,
    METRIC_KIND_COUNTER,
    METRIC_KIND_DURATION,
    METRIC_KIND_GAUGE,
    METRIC_SEARCH_NO_RESULTS_COUNT,
    METRIC_UPLOAD_ACCEPTED_COUNT,
    METRIC_UPLOAD_DURATION_MS,
    METRIC_UPLOAD_REJECTED_COUNT,
    OperationalMetricsMiddleware,
    increment_counter,
    local_metrics_sink,
    record_duration,
    record_gauge,
)
from app.core.request_context import RequestContextMiddleware


def _build_test_client() -> TestClient:
    app = FastAPI()
    register_exception_handlers(app)
    app.add_middleware(OperationalMetricsMiddleware)
    app.add_middleware(RequestContextMiddleware)

    @app.get("/ok")
    def ok():
        return {"ok": True}

    @app.get("/private")
    def private():
        raise HTTPException(status_code=401, detail="No autenticado")

    @app.get("/forbidden")
    def forbidden():
        raise HTTPException(status_code=403, detail="No autorizado")

    @app.get("/broken")
    def broken():
        raise RuntimeError("SECRET_KEY=abc password=secreto")

    return TestClient(app, raise_server_exceptions=False)


class OperationMetricsTests(unittest.TestCase):
    def setUp(self):
        local_metrics_sink.clear()

    def tearDown(self):
        local_metrics_sink.clear()

    def test_metric_contracts_record_counter_duration_and_gauge(self):
        increment_counter("custom.metric", tags={"component": "test"})
        record_duration(METRIC_HTTP_REQUEST_DURATION_MS, 12.5, tags={"route": "/ok"})
        record_gauge("custom.gauge", 1, tags={"status": "healthy"})

        samples = local_metrics_sink.snapshot()

        self.assertEqual(samples[0].kind, METRIC_KIND_COUNTER)
        self.assertEqual(samples[1].kind, METRIC_KIND_DURATION)
        self.assertEqual(samples[1].unit, "ms")
        self.assertEqual(samples[2].kind, METRIC_KIND_GAUGE)

    def test_metrics_sanitize_sensitive_tags(self):
        increment_counter(
            "custom.metric",
            tags={
                "component": "auth",
                "email": "persona@example.com",
                "token": "Bearer secret",
                "unsafe key": "ignored",
                "payload": "valor con espacios y SECRET_KEY",
            },
        )

        sample = local_metrics_sink.snapshot()[0]

        self.assertEqual(sample.tags, {"component": "auth"})

    def test_request_middleware_records_request_count_duration_and_context(self):
        client = _build_test_client()

        response = client.get("/ok", headers={"X-Correlation-ID": "cliente-1"})

        self.assertEqual(response.status_code, 200)
        samples = local_metrics_sink.snapshot()
        names = [sample.name for sample in samples]
        self.assertIn(METRIC_HTTP_REQUEST_COUNT, names)
        self.assertIn(METRIC_HTTP_REQUEST_DURATION_MS, names)
        request_sample = next(
            sample for sample in samples if sample.name == METRIC_HTTP_REQUEST_COUNT
        )
        self.assertEqual(request_sample.tags["route"], "/ok")
        self.assertEqual(request_sample.tags["status"], "200")
        self.assertTrue(request_sample.request_id)
        self.assertEqual(request_sample.correlation_id, "cliente-1")

    def test_http_401_and_403_emit_auth_metrics(self):
        client = _build_test_client()

        client.get("/private")
        client.get("/forbidden")

        names = [sample.name for sample in local_metrics_sink.snapshot()]
        self.assertIn(METRIC_AUTH_FAILURE_COUNT, names)
        self.assertIn(METRIC_AUTHORIZATION_FAILURE_COUNT, names)
        self.assertIn(METRIC_HTTP_RESPONSE_4XX_COUNT, names)

    def test_unhandled_error_emits_safe_metric_without_secret(self):
        client = _build_test_client()

        response = client.get("/broken")

        self.assertEqual(response.status_code, 500)
        samples = local_metrics_sink.snapshot()
        unhandled = [
            sample
            for sample in samples
            if sample.name == METRIC_HTTP_UNHANDLED_ERROR_COUNT
        ]
        self.assertEqual(len(unhandled), 1)
        serialized = repr(unhandled[0])
        self.assertNotIn("SECRET_KEY", serialized)
        self.assertNotIn("password", serialized)
        self.assertEqual(unhandled[0].tags["error_class"], "RuntimeError")

    def test_upload_module_emits_accepted_and_rejected_metrics(self):
        started = time.perf_counter()

        _record_upload_metrics(started, accepted=True, media_type="image")
        _record_upload_metrics(started, accepted=False, reason="size")

        samples = local_metrics_sink.snapshot()
        names = [sample.name for sample in samples]
        self.assertIn(METRIC_UPLOAD_ACCEPTED_COUNT, names)
        self.assertIn(METRIC_UPLOAD_REJECTED_COUNT, names)
        self.assertIn(METRIC_UPLOAD_DURATION_MS, names)
        serialized = repr(samples)
        self.assertNotIn("filename", serialized)
        self.assertNotIn("usuario_id", serialized)

    def test_search_module_emits_no_results_without_query_text(self):
        _record_search_no_results_metric(smart=True, smart_semantic=False)

        sample = local_metrics_sink.snapshot()[0]

        self.assertEqual(sample.name, METRIC_SEARCH_NO_RESULTS_COUNT)
        self.assertEqual(sample.tags["endpoint"], "comercios_activos")
        self.assertEqual(sample.tags["mode"], "smart")
        self.assertNotIn("query", sample.tags)


if __name__ == "__main__":
    unittest.main()
