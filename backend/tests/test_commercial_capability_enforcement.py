from datetime import date, datetime, timezone
import inspect
import unittest
from unittest.mock import patch

from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import Base
from app.core.error_handlers import register_exception_handlers
from app.core.model_registry import import_all_models
from app.modules.users.models.usuarios_documentos_aceptaciones_models import (
    UsuarioDocumentoAceptacion,
)
from app.modules.users.models.usuarios_models import Usuario
from app.modules.users.services.commercial_capabilities_services import (
    COMMERCIAL_CAPABILITY_NAMES,
    COMMERCIAL_CAPABILITY_REQUIRED_CODE,
    CommercialCapabilityRequiredError,
    UnknownCommercialCapabilityError,
    commercial_capability_http_detail,
    require_commercial_capability,
)
from app.modules.users.services.documentos_aceptacion_services import (
    CANAL_REGISTRO_WEB,
    DOCUMENTOS_OBLIGATORIOS_REGISTRO,
    ESTADO_ACEPTADO,
    METODO_CHECKBOX_EXPLICITO,
)


import_all_models()
engine = create_engine(
    "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
)
SessionLocal = sessionmaker(bind=engine)


def _http_contract_client() -> TestClient:
    app = FastAPI()
    register_exception_handlers(app)

    @app.get("/test/commercial-capability")
    def protected_test_route():
        raise HTTPException(
            status_code=403,
            detail=commercial_capability_http_detail(),
        )

    @app.get("/test/existing-code-contract")
    def existing_code_route():
        raise HTTPException(status_code=400, detail={"code": "legacy_code"})

    return TestClient(app, raise_server_exceptions=False)


class CommercialCapabilityEnforcementTests(unittest.TestCase):
    def setUp(self):
        Base.metadata.create_all(engine)
        self.db = SessionLocal()

    def tearDown(self):
        self.db.close()
        Base.metadata.drop_all(engine)

    def _usuario(self, **overrides) -> Usuario:
        values = {
            "email": "enforcement@example.com",
            "hashed_password": "hash",
            "modo_activo": "usuario",
            "onboarding_completo": False,
            "provincia": "Buenos Aires",
            "ciudad": "La Plata",
            "fecha_nacimiento": date(1990, 1, 1),
            "email_verified_at": datetime(2026, 1, 1, tzinfo=timezone.utc),
            "telefono_e164": "+5491123456789",
            "telefono_verified_at": datetime(2026, 1, 1, tzinfo=timezone.utc),
            "telefono_verification_source": "phone_otp",
        }
        values.update(overrides)
        usuario = Usuario(**values)
        self.db.add(usuario)
        self.db.flush()
        return usuario

    def _aceptar_legal(self, usuario: Usuario) -> None:
        for documento in DOCUMENTOS_OBLIGATORIOS_REGISTRO:
            self.db.add(
                UsuarioDocumentoAceptacion(
                    usuario_id=usuario.id,
                    documento_tipo=documento.tipo,
                    documento_version=documento.version,
                    canal=CANAL_REGISTRO_WEB,
                    metodo=METODO_CHECKBOX_EXPLICITO,
                    estado=ESTADO_ACEPTADO,
                    documento_referencia=documento.referencia,
                )
            )
        self.db.flush()

    def test_default_configuration_is_off(self):
        from app.core.config import Settings

        configured = Settings(
            DATABASE_URL="sqlite://",
            SECRET_KEY="test-secret",
            ALGORITHM="HS256",
            ACCESS_TOKEN_EXPIRE_MINUTES=60,
            _env_file=None,
        )
        self.assertFalse(configured.COMMERCIAL_CAPABILITIES_ENFORCEMENT_ENABLED)

    def test_off_derives_without_blocking_each_capability(self):
        usuario = self._usuario(provincia="")
        self._aceptar_legal(usuario)
        with patch(
            "app.modules.users.services.commercial_capabilities_services.settings.COMMERCIAL_CAPABILITIES_ENFORCEMENT_ENABLED",
            False,
        ):
            for capability in COMMERCIAL_CAPABILITY_NAMES:
                result = require_commercial_capability(
                    self.db, usuario, capability, today=date(2026, 9, 8)
                )
                self.assertFalse(getattr(result.capabilities, capability))

    def test_on_allows_each_derived_capability(self):
        usuario = self._usuario()
        self._aceptar_legal(usuario)
        with patch(
            "app.modules.users.services.commercial_capabilities_services.settings.COMMERCIAL_CAPABILITIES_ENFORCEMENT_ENABLED",
            True,
        ):
            for capability in COMMERCIAL_CAPABILITY_NAMES:
                result = require_commercial_capability(
                    self.db, usuario, capability, today=date(2026, 9, 8)
                )
                self.assertTrue(getattr(result.capabilities, capability))

    def test_on_rejects_each_missing_capability_without_detail(self):
        usuario = self._usuario(email_verified_at=None)
        self._aceptar_legal(usuario)
        with patch(
            "app.modules.users.services.commercial_capabilities_services.settings.COMMERCIAL_CAPABILITIES_ENFORCEMENT_ENABLED",
            True,
        ):
            for capability in COMMERCIAL_CAPABILITY_NAMES:
                with self.assertRaises(CommercialCapabilityRequiredError) as raised:
                    require_commercial_capability(
                        self.db, usuario, capability, today=date(2026, 9, 8)
                    )
                self.assertEqual(str(raised.exception), COMMERCIAL_CAPABILITY_REQUIRED_CODE)
                self.assertFalse(hasattr(raised.exception, "missing_fields"))

    def test_guard_uses_official_capabilities_and_has_no_ownership_input(self):
        signature = inspect.signature(require_commercial_capability)
        self.assertEqual(set(signature.parameters), {"db", "usuario", "capability", "today"})
        with self.assertRaises(UnknownCommercialCapabilityError):
            require_commercial_capability(self.db, self._usuario(), "administrative")

    def test_legacy_presentation_flags_do_not_control_guard(self):
        usuario = self._usuario(modo_activo="publicador", onboarding_completo=True)
        self._aceptar_legal(usuario)
        with patch(
            "app.modules.users.services.commercial_capabilities_services.settings.COMMERCIAL_CAPABILITIES_ENFORCEMENT_ENABLED",
            True,
        ):
            allowed = require_commercial_capability(
                self.db, usuario, "puede_crear_espacio", today=date(2026, 9, 8)
            )
            self.assertTrue(allowed.capabilities.puede_crear_espacio)
            usuario.email_verified_at = None
            with self.assertRaises(CommercialCapabilityRequiredError):
                require_commercial_capability(
                    self.db, usuario, "puede_crear_espacio", today=date(2026, 9, 8)
                )

    def test_http_contract_is_opt_in_safe_and_exact(self):
        client = _http_contract_client()
        response = client.get("/test/commercial-capability")
        self.assertEqual(response.status_code, 403)
        self.assertEqual(
            response.json(),
            {"detail": "No autorizado", "code": COMMERCIAL_CAPABILITY_REQUIRED_CODE},
        )
        self.assertNotIn("email", response.text.lower())
        self.assertNotIn("telefono", response.text.lower())
        self.assertNotIn("perfil", response.text.lower())

        existing = client.get("/test/existing-code-contract")
        self.assertEqual(existing.json(), {"detail": "Solicitud invalida"})


if __name__ == "__main__":
    unittest.main()
