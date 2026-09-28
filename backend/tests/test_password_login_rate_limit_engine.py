from datetime import datetime, timedelta
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from pydantic import ValidationError
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.config import Settings
from app.modules.users.models.identity_models import AccountActionRateLimit
from app.modules.users.services.account_action_rate_limit_services import (
    PASSWORD_LOGIN,
    PASSWORD_RESET,
    PasswordLoginRateLimitConfig,
    cleanup_expired_password_login_buckets,
    complete_password_login_success,
    direct_client_host,
    reserve_password_login_attempt,
    subject_digest,
)


class PasswordLoginRateLimitEngineTests(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine(
            "sqlite://",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        AccountActionRateLimit.__table__.create(self.engine)
        self.Session = sessionmaker(bind=self.engine)
        self.secret = "password-login-dedicated-test-secret"
        self.now = datetime(2026, 9, 25, 12, 0, 0)
        self.config = PasswordLoginRateLimitConfig(
            subject_limit=5,
            subject_window_seconds=900,
            client_limit=20,
            client_window_seconds=3600,
            cleanup_retention_seconds=7200,
            cleanup_batch_size=10,
        )

    def tearDown(self):
        self.engine.dispose()

    def _reserve(self, *, email="person@example.com", host="203.0.113.4", **kwargs):
        with self.Session() as db:
            return reserve_password_login_attempt(
                db,
                email_canonical=email,
                client_host=host,
                config=kwargs.pop("config", self.config),
                now=kwargs.pop("now", self.now),
                secret=kwargs.pop("secret", self.secret),
                **kwargs,
            )

    def _rows(self):
        with self.Session() as db:
            return list(
                db.scalars(
                    select(AccountActionRateLimit).order_by(
                        AccountActionRateLimit.subject_digest
                    )
                )
            )

    def test_digests_separan_subject_client_action_y_scope(self):
        subject = subject_digest(
            action=PASSWORD_LOGIN,
            scope="subject",
            subject="destination:person@example.com",
            secret=self.secret,
        )
        client = subject_digest(
            action=PASSWORD_LOGIN,
            scope="client",
            subject="client:203.0.113.4",
            secret=self.secret,
        )
        other_action = subject_digest(
            action=PASSWORD_RESET,
            scope="subject",
            subject="destination:person@example.com",
            secret=self.secret,
        )
        self.assertEqual(len({subject, client, other_action}), 3)

    def test_direct_client_host_ignora_headers_forwarded(self):
        request = SimpleNamespace(
            client=SimpleNamespace(host="198.51.100.7"),
            headers={"x-forwarded-for": "203.0.113.99", "forwarded": "for=203.0.113.98"},
        )
        self.assertEqual(direct_client_host(request), "198.51.100.7")
        with self.assertRaisesRegex(ValueError, "client_missing"):
            direct_client_host(SimpleNamespace(client=None))

    def test_configuracion_valida_e_invalida(self):
        self.config.validate()
        with self.assertRaisesRegex(ValueError, "configuration_invalid"):
            PasswordLoginRateLimitConfig(0, 900, 20, 3600, 7200, 10).validate()
        with self.assertRaisesRegex(ValueError, "retention_too_short"):
            PasswordLoginRateLimitConfig(5, 900, 20, 3600, 3599, 10).validate()
        with self.assertRaises(ValidationError):
            Settings(
                DATABASE_URL="sqlite://",
                SECRET_KEY="test-only",
                ALGORITHM="HS256",
                ACCESS_TOKEN_EXPIRE_MINUTES=60,
                PASSWORD_LOGIN_SUBJECT_LIMIT=0,
                _env_file=None,
            )

    def test_reserva_subject_y_client_sin_pii(self):
        result = self._reserve()
        self.assertEqual(result.status, "reserved")
        rows = self._rows()
        self.assertEqual(len(rows), 2)
        self.assertEqual({row.action for row in rows}, {PASSWORD_LOGIN})
        self.assertEqual({row.attempt_count for row in rows}, {1})
        self.assertNotIn("person@example.com", repr(rows))
        self.assertNotIn("203.0.113.4", repr(rows))
        self.assertNotIn(result.reservation.subject_digest, repr(result))

    def test_limite_exacto_subject_y_retry_after(self):
        for _ in range(5):
            self.assertEqual(self._reserve().status, "reserved")
        denied = self._reserve()
        self.assertEqual(denied.status, "rate_limited")
        self.assertEqual(denied.retry_after_seconds, 900)

    def test_limite_client_compartido_entre_subjects(self):
        config = PasswordLoginRateLimitConfig(5, 900, 2, 3600, 7200, 10)
        self.assertEqual(self._reserve(email="one@example.com", config=config).status, "reserved")
        self.assertEqual(self._reserve(email="two@example.com", config=config).status, "reserved")
        denied = self._reserve(email="three@example.com", config=config)
        self.assertEqual(denied.status, "rate_limited")
        self.assertEqual(denied.retry_after_seconds, 3600)

    def test_expiracion_en_borde_abre_ventana_nueva(self):
        config = PasswordLoginRateLimitConfig(1, 10, 10, 20, 40, 10)
        self.assertEqual(self._reserve(config=config).status, "reserved")
        self.assertEqual(
            self._reserve(config=config, now=self.now + timedelta(seconds=9)).status,
            "rate_limited",
        )
        self.assertEqual(
            self._reserve(config=config, now=self.now + timedelta(seconds=10)).status,
            "reserved",
        )

    def test_rollback_externo_no_devuelve_capacidad(self):
        config = PasswordLoginRateLimitConfig(1, 900, 20, 3600, 7200, 10)
        with self.Session() as db:
            self.assertEqual(
                reserve_password_login_attempt(
                    db,
                    email_canonical="person@example.com",
                    client_host="203.0.113.4",
                    config=config,
                    now=self.now,
                    secret=self.secret,
                ).status,
                "reserved",
            )
            db.rollback()
        self.assertEqual(self._reserve(config=config).status, "rate_limited")

    def test_exito_limpia_subject_y_descuenta_client(self):
        reserved = self._reserve()
        with self.Session() as db:
            result = complete_password_login_success(
                db, reservation=reserved.reservation, now=self.now
            )
        self.assertEqual(result.status, "completed")
        self.assertTrue(result.subject_cleared)
        self.assertTrue(result.client_released)
        self.assertEqual(sorted(row.attempt_count for row in self._rows()), [0, 0])

    def test_exito_no_descuenta_otra_ventana_ni_hace_negativo(self):
        reserved = self._reserve()
        with self.Session.begin() as db:
            client = db.scalar(
                select(AccountActionRateLimit).where(
                    AccountActionRateLimit.subject_digest
                    == reserved.reservation.client_digest
                )
            )
            client.window_started_at = self.now + timedelta(hours=1)
            client.attempt_count = 3
        with self.Session() as db:
            result = complete_password_login_success(
                db, reservation=reserved.reservation, now=self.now
            )
        self.assertFalse(result.client_released)
        with self.Session() as db:
            client_count = db.scalar(
                select(AccountActionRateLimit.attempt_count).where(
                    AccountActionRateLimit.subject_digest
                    == reserved.reservation.client_digest
                )
            )
        self.assertEqual(client_count, 3)

        reserved_again = self._reserve(email="other@example.com")
        with self.Session() as db:
            complete_password_login_success(db, reservation=reserved_again.reservation)
        with self.Session() as db:
            second = complete_password_login_success(db, reservation=reserved_again.reservation)
        self.assertFalse(second.client_released)
        self.assertGreaterEqual(min(row.attempt_count for row in self._rows()), 0)

    def test_fail_closed_sin_secreto_config_o_store(self):
        with patch(
            "app.modules.users.services.account_action_rate_limit_services.settings.ACCOUNT_ACTION_RATE_LIMIT_HMAC_SECRET",
            None,
        ):
            self.assertEqual(self._reserve(secret=None).status, "unavailable")
        invalid = PasswordLoginRateLimitConfig(0, 900, 20, 3600, 7200, 10)
        self.assertEqual(self._reserve(config=invalid).status, "unavailable")
        db = self.Session()
        db.close()
        self.engine.dispose()
        result = reserve_password_login_attempt(
            db,
            email_canonical="person@example.com",
            client_host="203.0.113.4",
            config=self.config,
            now=self.now,
            secret=self.secret,
        )
        self.assertEqual(result.status, "unavailable")

        class BrokenStore:
            def get_bind(self):
                raise RuntimeError("store unavailable")

            def rollback(self):
                raise RuntimeError("rollback unavailable")

        result = reserve_password_login_attempt(
            BrokenStore(),
            email_canonical="person@example.com",
            client_host="203.0.113.4",
            config=self.config,
            now=self.now,
            secret=self.secret,
        )
        self.assertEqual(result.status, "unavailable")

    def test_cleanup_por_lote_preserva_activos_bloqueados_y_otras_acciones(self):
        old = self.now - timedelta(hours=3)
        with self.Session.begin() as db:
            db.add_all(
                [
                    AccountActionRateLimit(
                        action=PASSWORD_LOGIN,
                        subject_digest="a" * 64,
                        window_started_at=old,
                        attempt_count=1,
                        blocked_until=None,
                        updated_at=old,
                    ),
                    AccountActionRateLimit(
                        action=PASSWORD_LOGIN,
                        subject_digest="b" * 64,
                        window_started_at=old,
                        attempt_count=5,
                        blocked_until=self.now + timedelta(minutes=1),
                        updated_at=old,
                    ),
                    AccountActionRateLimit(
                        action=PASSWORD_LOGIN,
                        subject_digest="c" * 64,
                        window_started_at=self.now,
                        attempt_count=1,
                        blocked_until=None,
                        updated_at=self.now,
                    ),
                    AccountActionRateLimit(
                        action=PASSWORD_RESET,
                        subject_digest="d" * 64,
                        window_started_at=old,
                        attempt_count=1,
                        blocked_until=None,
                        updated_at=old,
                    ),
                ]
            )
        with self.Session() as db:
            result = cleanup_expired_password_login_buckets(
                db, config=self.config, now=self.now
            )
        self.assertEqual(result.status, "completed")
        self.assertEqual(result.deleted_count, 1)
        self.assertEqual({row.subject_digest for row in self._rows()}, {"b" * 64, "c" * 64, "d" * 64})


if __name__ == "__main__":
    unittest.main()
