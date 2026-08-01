import unittest

from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient

from app.core.error_handlers import register_exception_handlers
from app.core.request_context import (
    CORRELATION_ID_HEADER,
    REQUEST_ID_HEADER,
    RequestContextMiddleware,
    get_current_request_context,
)


def _crear_app_de_prueba() -> FastAPI:
    app = FastAPI()
    register_exception_handlers(app)
    app.add_middleware(RequestContextMiddleware)

    @app.get("/context")
    def context():
        request_context = get_current_request_context()
        return {
            "request_id": request_context.request_id,
            "correlation_id": request_context.correlation_id,
        }

    @app.get("/http-error")
    def http_error():
        raise HTTPException(status_code=404, detail="Recurso no encontrado")

    @app.get("/unhandled")
    def unhandled():
        raise RuntimeError("SECRET_KEY=abc password=secreto")

    return app


class RequestContextTests(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(_crear_app_de_prueba(), raise_server_exceptions=False)

    def test_generates_request_and_correlation_ids(self):
        response = self.client.get("/context")

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.headers[REQUEST_ID_HEADER])
        self.assertTrue(response.headers[CORRELATION_ID_HEADER])
        self.assertEqual(response.json()["request_id"], response.headers[REQUEST_ID_HEADER])
        self.assertEqual(
            response.json()["correlation_id"],
            response.headers[CORRELATION_ID_HEADER],
        )

    def test_reuses_safe_incoming_correlation_id(self):
        response = self.client.get(
            "/context",
            headers={CORRELATION_ID_HEADER: "cliente-123"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers[CORRELATION_ID_HEADER], "cliente-123")
        self.assertNotEqual(response.headers[REQUEST_ID_HEADER], "cliente-123")

    def test_replaces_invalid_incoming_correlation_id(self):
        response = self.client.get(
            "/context",
            headers={CORRELATION_ID_HEADER: "Bearer secret token"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertNotEqual(response.headers[CORRELATION_ID_HEADER], "Bearer secret token")
        self.assertTrue(response.headers[CORRELATION_ID_HEADER])

    def test_http_error_response_includes_context_headers_and_logs_ids(self):
        with self.assertLogs("feedgo.errors", level="WARNING") as logs:
            response = self.client.get(
                "/http-error",
                headers={CORRELATION_ID_HEADER: "cliente-404"},
            )

        self.assertEqual(response.status_code, 404)
        self.assertTrue(response.headers[REQUEST_ID_HEADER])
        self.assertEqual(response.headers[CORRELATION_ID_HEADER], "cliente-404")
        joined_logs = "\n".join(logs.output)
        self.assertIn(response.headers[REQUEST_ID_HEADER], joined_logs)
        self.assertIn("cliente-404", joined_logs)

    def test_unhandled_error_response_includes_context_headers_without_secrets(self):
        with self.assertLogs("feedgo.errors", level="ERROR") as logs:
            response = self.client.get(
                "/unhandled",
                headers={CORRELATION_ID_HEADER: "cliente-500"},
            )

        self.assertEqual(response.status_code, 500)
        self.assertTrue(response.headers[REQUEST_ID_HEADER])
        self.assertEqual(response.headers[CORRELATION_ID_HEADER], "cliente-500")
        self.assertEqual(response.json(), {"detail": "Error interno del servidor"})
        joined_logs = "\n".join(logs.output)
        self.assertIn(response.headers[REQUEST_ID_HEADER], joined_logs)
        self.assertIn("cliente-500", joined_logs)
        self.assertNotIn("SECRET_KEY", joined_logs)
        self.assertNotIn("password", joined_logs)
        self.assertNotIn("secreto", joined_logs)


if __name__ == "__main__":
    unittest.main()
