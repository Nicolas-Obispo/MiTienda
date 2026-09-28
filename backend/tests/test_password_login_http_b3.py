from datetime import datetime
import unittest
from unittest.mock import patch

from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import Base, get_db
from app.core.model_registry import import_all_models
from app.core.operation_metrics import (
    METRIC_AUTH_LOGIN_COUNT,
    local_metrics_sink,
)
from app.core.security import DUMMY_BCRYPT_HASH, hash_password, pwd_context
from app.modules.users.models.identity_models import (
    AccountActionRateLimit,
    FeedGoSession,
    PasswordCredential,
)
from app.modules.users.models.usuarios_models import Usuario
from app.modules.users.routes.usuarios_routers import router
from app.modules.users.services.account_action_rate_limit_services import (
    PASSWORD_LOGIN,
    PasswordLoginReservationResult,
    PasswordLoginSuccessResult,
)


import_all_models()
engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


app = FastAPI()
app.include_router(router)
app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)


class PasswordLoginHttpB3Tests(unittest.TestCase):
    def setUp(self):
        Base.metadata.create_all(engine)
        self.now = datetime(2026, 9, 25, 12, 0, 0)
        self.patches = [
            patch(
                "app.modules.users.services.account_action_rate_limit_services."
                "settings.ACCOUNT_ACTION_RATE_LIMIT_HMAC_SECRET",
                "password-login-http-b3-secret",
            ),
            patch(
                "app.modules.users.services.account_action_rate_limit_services._utcnow",
                return_value=self.now,
            ),
        ]
        for item in self.patches:
            item.start()
        local_metrics_sink.clear()
        password_hash = hash_password("Password1")
        with SessionLocal.begin() as db:
            db.add(
                Usuario(
                    id=1,
                    email="existing@example.com",
                    email_canonical="existing@example.com",
                    hashed_password=password_hash,
                )
            )
            db.add(
                PasswordCredential(
                    usuario_id=1,
                    password_hash=password_hash,
                    hash_version="bcrypt",
                )
            )

    def tearDown(self):
        for item in reversed(self.patches):
            item.stop()
        local_metrics_sink.clear()
        Base.metadata.drop_all(engine)

    def login(self, email, password="wrong-password", headers=None):
        return client.post(
            "/usuarios/login",
            json={"email": email, "password": password},
            headers=headers or {},
        )

    def test_inexistente_e_incorrecta_hacen_un_bcrypt_y_mismo_contrato(self):
        with patch.object(
            pwd_context,
            "verify",
            wraps=pwd_context.verify,
        ) as verify:
            missing = self.login("missing@example.com")
            self.assertEqual(verify.call_count, 1)
            self.assertEqual(verify.call_args.args[1], DUMMY_BCRYPT_HASH)
            verify.reset_mock()
            wrong = self.login("existing@example.com")
            self.assertEqual(verify.call_count, 1)
            self.assertNotEqual(verify.call_args.args[1], DUMMY_BCRYPT_HASH)

        self.assertEqual(missing.status_code, 401)
        self.assertEqual(wrong.status_code, 401)
        self.assertEqual(missing.json(), wrong.json())
        self.assertEqual(missing.headers["cache-control"], "no-store")
        self.assertEqual(wrong.headers["cache-control"], "no-store")

    def test_inexistente_e_incorrecta_consumen_ambas_dimensiones(self):
        self.login("missing@example.com")
        self.login("existing@example.com")
        with SessionLocal() as db:
            rows = list(
                db.scalars(
                    select(AccountActionRateLimit).where(
                        AccountActionRateLimit.action == PASSWORD_LOGIN
                    )
                )
            )
        self.assertEqual(len(rows), 3)
        self.assertEqual(sorted(row.attempt_count for row in rows), [1, 1, 2])

    def test_subject_cinco_y_siguiente_429_generico(self):
        with patch(
            "app.modules.users.services.usuarios_services.verificar_password_o_dummy",
            return_value=False,
        ):
            allowed = [self.login("subject@example.com") for _ in range(5)]
            blocked = self.login("subject@example.com")
        self.assertEqual([item.status_code for item in allowed], [401] * 5)
        self.assertEqual(blocked.status_code, 429)
        self.assertEqual(blocked.headers["retry-after"], "900")
        self.assertEqual(blocked.headers["cache-control"], "no-store")
        text = blocked.text.lower()
        for forbidden in ("subject", "client", "bucket", "digest", "email", "ip"):
            self.assertNotIn(forbidden, text)

    def test_client_veinte_headers_spoofed_y_siguiente_429(self):
        with patch(
            "app.modules.users.services.usuarios_services.verificar_password_o_dummy",
            return_value=False,
        ):
            allowed = []
            for index in range(20):
                allowed.append(
                    self.login(
                        f"client-{index}@example.com",
                        headers={
                            "X-Forwarded-For": f"203.0.113.{index + 1}",
                            "Forwarded": f"for=198.51.100.{index + 1}",
                        },
                    )
                )
            blocked = self.login(
                "client-blocked@example.com",
                headers={
                    "X-Forwarded-For": "192.0.2.200",
                    "Forwarded": "for=192.0.2.201",
                },
            )
        self.assertEqual([item.status_code for item in allowed], [401] * 20)
        self.assertEqual(blocked.status_code, 429)
        self.assertEqual(blocked.headers["retry-after"], "3600")
        self.assertEqual(blocked.headers["cache-control"], "no-store")

    def test_limiter_unavailable_falla_cerrado(self):
        unavailable = PasswordLoginReservationResult(status="unavailable")
        with (
            patch(
                "app.modules.users.routes.usuarios_routers."
                "reserve_password_login_attempt",
                return_value=unavailable,
            ),
            patch(
                "app.modules.users.routes.usuarios_routers.autenticar_usuario"
            ) as authenticate,
        ):
            response = self.login("existing@example.com", "Password1")
        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.headers["cache-control"], "no-store")
        self.assertNotIn("database", response.text.lower())
        self.assertNotIn("limiter", response.text.lower())
        authenticate.assert_not_called()

    def test_fallo_de_finalizacion_no_emite_sesion(self):
        with (
            patch(
                "app.modules.users.routes.usuarios_routers."
                "complete_password_login_success",
                return_value=PasswordLoginSuccessResult(status="unavailable"),
            ),
            patch(
                "app.modules.users.routes.usuarios_routers.create_feedgo_session"
            ) as create_session,
        ):
            response = self.login("existing@example.com", "Password1")
        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.headers["cache-control"], "no-store")
        create_session.assert_not_called()
        with SessionLocal() as db:
            self.assertEqual(db.query(FeedGoSession).count(), 0)

    def test_exito_finaliza_reserva_antes_de_emitir_sesion(self):
        response = self.login("existing@example.com", "Password1")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers["cache-control"], "no-store")
        self.assertIn("token", response.json())
        with SessionLocal() as db:
            rows = list(
                db.scalars(
                    select(AccountActionRateLimit).where(
                        AccountActionRateLimit.action == PASSWORD_LOGIN
                    )
                )
            )
            self.assertEqual(db.query(FeedGoSession).count(), 1)
        self.assertEqual(len(rows), 2)
        self.assertEqual({row.attempt_count for row in rows}, {0})

    def test_observabilidad_usa_outcomes_acotados_sin_identidad(self):
        self.login("missing@example.com")
        self.login("existing@example.com", "Password1")
        samples = [
            sample
            for sample in local_metrics_sink.snapshot()
            if sample.name == METRIC_AUTH_LOGIN_COUNT
        ]
        self.assertEqual(
            [sample.tags["outcome"] for sample in samples],
            ["attempt", "invalid_credentials", "attempt", "success"],
        )
        serialized = repr(samples).lower()
        for forbidden in (
            "missing@example.com",
            "existing@example.com",
            "password1",
            "subject_digest",
        ):
            self.assertNotIn(forbidden, serialized)


if __name__ == "__main__":
    unittest.main()
