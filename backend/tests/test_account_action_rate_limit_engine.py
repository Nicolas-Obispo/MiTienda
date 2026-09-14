from datetime import datetime, timedelta
import unittest
from unittest.mock import patch

from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import Base
from app.modules.users.models.identity_models import AccountActionRateLimit
from app.modules.users.services.account_action_rate_limit_services import (
    LocalPublicRateLimiter,
    clear_current_password_failures,
    record_current_password_failure,
    record_email_verification,
    record_password_reset,
    subject_digest,
)


class AccountActionRateLimitEngineTests(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine(
            "sqlite://", connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        AccountActionRateLimit.__table__.create(self.engine)
        self.Session = sessionmaker(bind=self.engine)
        self.secret = "dedicated-rate-limit-secret"
        self.now = datetime(2026, 1, 1, 12, 0, 0)

    def tearDown(self):
        self.engine.dispose()

    def test_hmac_determinista_y_separado_por_dominio(self):
        first = subject_digest(action="password_reset", scope="hour", subject="destination:a@b.com", secret=self.secret)
        self.assertEqual(first, subject_digest(action="password_reset", scope="hour", subject="destination:a@b.com", secret=self.secret))
        self.assertNotEqual(first, subject_digest(action="password_reset", scope="hour", subject="destination:a@c.com", secret=self.secret))
        self.assertNotEqual(first, subject_digest(action="password_reset", scope="client-hour", subject="destination:a@b.com", secret=self.secret))

    def test_secreto_no_puede_reutilizar_jwt_o_resend(self):
        with patch("app.modules.users.services.account_action_rate_limit_services.settings.SECRET_KEY", "same"):
            with self.assertRaisesRegex(RuntimeError, "secret_reused"):
                subject_digest(action="password_reset", scope="hour", subject="x", secret="same")
        with patch("app.modules.users.services.account_action_rate_limit_services.settings.RESEND_API_KEY", "same"):
            with self.assertRaisesRegex(RuntimeError, "secret_reused"):
                subject_digest(action="password_reset", scope="hour", subject="x", secret="same")
        with patch("app.modules.users.services.account_action_rate_limit_services.settings.IDENTITY_RESEND_API_KEY", "same"):
            with self.assertRaisesRegex(RuntimeError, "secret_reused"):
                subject_digest(action="password_reset", scope="hour", subject="x", secret="same")

    def test_canonical_no_se_persiste(self):
        with self.Session.begin() as db:
            record_password_reset(db, email_canonical="persona@example.com", now=self.now, secret=self.secret)
        with self.Session() as db:
            rows = db.scalars(select(AccountActionRateLimit)).all()
            self.assertTrue(rows)
            self.assertNotIn("persona@example.com", repr([(r.subject_digest, r.action) for r in rows]))

    def test_verification_cooldown_60_segundos(self):
        with self.Session.begin() as db:
            self.assertTrue(record_email_verification(db, usuario_id=1, now=self.now, secret=self.secret).allowed)
        with self.Session.begin() as db:
            denied = record_email_verification(db, usuario_id=1, now=self.now + timedelta(seconds=59), secret=self.secret)
            self.assertFalse(denied.allowed)
            self.assertEqual(denied.retry_after_seconds, 1)
        with self.Session.begin() as db:
            self.assertTrue(record_email_verification(db, usuario_id=1, now=self.now + timedelta(seconds=60), secret=self.secret).allowed)

    def test_verification_limite_cinco_hora(self):
        for minute in range(5):
            with self.Session.begin() as db:
                self.assertTrue(record_email_verification(db, usuario_id=2, now=self.now + timedelta(minutes=minute), secret=self.secret).allowed)
        with self.Session.begin() as db:
            self.assertFalse(record_email_verification(db, usuario_id=2, now=self.now + timedelta(minutes=5), secret=self.secret).allowed)
        with self.Session.begin() as db:
            self.assertTrue(record_email_verification(db, usuario_id=2, now=self.now + timedelta(hours=1), secret=self.secret).allowed)

    def test_verification_limite_diez_dia(self):
        for hour in range(10):
            with self.Session.begin() as db:
                self.assertTrue(record_email_verification(db, usuario_id=3, now=self.now + timedelta(hours=hour), secret=self.secret).allowed)
        with self.Session.begin() as db:
            self.assertFalse(record_email_verification(db, usuario_id=3, now=self.now + timedelta(hours=10), secret=self.secret).allowed)
        with self.Session.begin() as db:
            self.assertTrue(record_email_verification(db, usuario_id=3, now=self.now + timedelta(days=1), secret=self.secret).allowed)

    def test_password_reset_cinco_por_hora_y_borde(self):
        for _ in range(5):
            with self.Session.begin() as db:
                self.assertTrue(record_password_reset(db, email_canonical="a@b.com", now=self.now, secret=self.secret).allowed)
        with self.Session.begin() as db:
            self.assertFalse(record_password_reset(db, email_canonical="a@b.com", now=self.now + timedelta(minutes=59, seconds=59), secret=self.secret).allowed)
        with self.Session.begin() as db:
            self.assertTrue(record_password_reset(db, email_canonical="a@b.com", now=self.now + timedelta(hours=1), secret=self.secret).allowed)

    def test_current_password_cinco_fallos_en_quince_minutos(self):
        for _ in range(5):
            with self.Session.begin() as db:
                self.assertTrue(record_current_password_failure(db, usuario_id=4, now=self.now, secret=self.secret).allowed)
        with self.Session.begin() as db:
            self.assertFalse(record_current_password_failure(db, usuario_id=4, now=self.now + timedelta(minutes=14), secret=self.secret).allowed)
        with self.Session.begin() as db:
            self.assertTrue(record_current_password_failure(db, usuario_id=4, now=self.now + timedelta(minutes=15), secret=self.secret).allowed)

    def test_password_actual_correcta_reinicia_fallos(self):
        for _ in range(5):
            with self.Session.begin() as db:
                record_current_password_failure(db, usuario_id=5, now=self.now, secret=self.secret)
        with self.Session.begin() as db:
            clear_current_password_failures(db, usuario_id=5, now=self.now, secret=self.secret)
        with self.Session.begin() as db:
            self.assertTrue(record_current_password_failure(db, usuario_id=5, now=self.now, secret=self.secret).allowed)

    def test_defensa_local_20_hora_y_reloj_inyectable(self):
        clock = [self.now]
        limiter = LocalPublicRateLimiter(secret=self.secret, clock=lambda: clock[0])
        for _ in range(20):
            self.assertTrue(limiter.record_password_reset(client_host="203.0.113.5").allowed)
        self.assertFalse(limiter.record_password_reset(client_host="203.0.113.5").allowed)
        clock[0] += timedelta(hours=1)
        self.assertTrue(limiter.record_password_reset(client_host="203.0.113.5").allowed)

    def test_accion_desconocida_rechazada(self):
        with self.assertRaisesRegex(ValueError, "account_action_unknown"):
            subject_digest(action="unknown", scope="hour", subject="x", secret=self.secret)

    def test_resultado_y_logs_no_exponen_pii(self):
        with self.Session.begin() as db:
            result = record_password_reset(db, email_canonical="private@example.com", now=self.now, secret=self.secret)
        self.assertEqual(result.reason, None)
        self.assertFalse(hasattr(result, "subject_digest"))


if __name__ == "__main__":
    unittest.main()
