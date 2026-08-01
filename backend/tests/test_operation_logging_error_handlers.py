import unittest

from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient
from pydantic import BaseModel

from app.core.error_handlers import register_exception_handlers
from app.core.operation_logging import (
    LOG_LEVELS,
    get_operation_logger,
    sanitize_log_value,
)


class Payload(BaseModel):
    nombre: str


def _crear_app_de_prueba() -> FastAPI:
    app = FastAPI()
    register_exception_handlers(app)

    @app.get("/http-secret")
    def http_secret():
        raise HTTPException(
            status_code=400,
            detail="SECRET_KEY=abc123 token=jwt password=secreto",
        )

    @app.get("/http-safe")
    def http_safe():
        raise HTTPException(status_code=404, detail="Recurso no encontrado")

    @app.post("/validation")
    def validation(payload: Payload):
        return payload

    @app.get("/unhandled")
    def unhandled():
        raise RuntimeError("password=secreto Traceback SECRET_KEY=abc")

    return app


class OperationLoggingErrorHandlersTests(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(_crear_app_de_prueba(), raise_server_exceptions=False)

    def test_log_levels_policy_contains_required_levels(self):
        self.assertIn("DEBUG", LOG_LEVELS)
        self.assertIn("INFO", LOG_LEVELS)
        self.assertIn("WARNING", LOG_LEVELS)
        self.assertIn("ERROR", LOG_LEVELS)
        self.assertIn("CRITICAL", LOG_LEVELS)

    def test_get_operation_logger_uses_feedgo_namespace(self):
        logger = get_operation_logger("errors/http")
        self.assertTrue(logger.name.startswith("feedgo."))
        self.assertNotIn("/", logger.name)

    def test_sanitize_log_value_redacts_sensitive_markers(self):
        sanitized = sanitize_log_value(
            "SECRET_KEY=abc token=jwt123 password=clave archivo .env"
        )
        self.assertNotIn("SECRET_KEY", sanitized)
        self.assertNotIn("token", sanitized)
        self.assertNotIn("password", sanitized)
        self.assertNotIn("abc", sanitized)
        self.assertNotIn("jwt123", sanitized)
        self.assertNotIn("clave", sanitized)
        self.assertNotIn(".env", sanitized)
        self.assertIn("[REDACTED]", sanitized)

    def test_http_exception_with_sensitive_detail_returns_generic_message(self):
        response = self.client.get("/http-secret")

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), {"detail": "Solicitud invalida"})
        self.assertNotIn("SECRET_KEY", response.text)
        self.assertNotIn("password", response.text)
        self.assertNotIn("token", response.text)

    def test_http_exception_with_safe_detail_preserves_status_and_detail(self):
        response = self.client.get("/http-safe")

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json(), {"detail": "Recurso no encontrado"})

    def test_validation_error_returns_sanitized_payload_error(self):
        response = self.client.post(
            "/validation",
            json={"nombre": {"password": "secreto"}},
        )

        self.assertEqual(response.status_code, 422)
        self.assertEqual(response.json(), {"detail": "Payload invalido"})
        self.assertNotIn("password", response.text)
        self.assertNotIn("secreto", response.text)

    def test_unhandled_exception_never_exposes_internal_detail(self):
        with self.assertLogs("feedgo.errors", level="ERROR") as logs:
            response = self.client.get("/unhandled")

        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.json(), {"detail": "Error interno del servidor"})
        self.assertNotIn("SECRET_KEY", response.text)
        self.assertNotIn("Traceback", response.text)
        self.assertNotIn("password", response.text)
        joined_logs = "\n".join(logs.output)
        self.assertIn("RuntimeError", joined_logs)
        self.assertNotIn("SECRET_KEY", joined_logs)
        self.assertNotIn("Traceback", joined_logs)
        self.assertNotIn("password", joined_logs)


if __name__ == "__main__":
    unittest.main()
