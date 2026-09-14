from datetime import datetime, timedelta, timezone
import unittest
from unittest.mock import patch

from sqlalchemy import create_engine, event, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import Base
from app.core.model_registry import import_all_models
from app.modules.communications.providers.email_provider import (
    EmailDeliveryError,
    FakeEmailProvider,
)
from app.modules.users.models.identity_models import (
    AccountActionRateLimit,
    AccountActionToken,
)
from app.modules.users.models.usuarios_models import Usuario
from app.modules.users.services.account_action_token_services import (
    EMAIL_VERIFICATION,
    PASSWORD_RESET,
    issue_account_action_token,
)
from app.modules.users.services.email_verification_services import (
    EMAIL_LINK_SOURCE,
    EmailVerificationError,
    confirm_email_verification,
    send_email_verification,
    send_registration_verification,
)

import_all_models()


class EmailVerificationFlowTests(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine(
            "sqlite://", connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)
        with self.Session.begin() as db:
            db.add(Usuario(id=1, email="person@example.com", email_canonical="person@example.com", hashed_password="hash"))
        self.now = datetime(2026, 9, 5, 12, 0, tzinfo=timezone.utc)
        self.clock = lambda: self.now
        self.provider = FakeEmailProvider()
        self.patches = [
            patch("app.modules.users.services.account_action_rate_limit_services.settings.ACCOUNT_ACTION_RATE_LIMIT_HMAC_SECRET", "verification-rate-secret"),
            patch("app.modules.users.services.email_verification_services.build_identity_email_provider", return_value=self.provider),
            patch("app.modules.communications.services.identity_email_services.settings.IDENTITY_EMAIL_FROM_ADDRESS", "hola@feedgo.test"),
            patch("app.modules.communications.services.identity_email_services.settings.IDENTITY_EMAIL_PUBLIC_BASE_URL", "https://feedgo.test"),
        ]
        for item in self.patches:
            item.start()

    def tearDown(self):
        for item in reversed(self.patches):
            item.stop()
        self.engine.dispose()

    def _user(self, db):
        return db.get(Usuario, 1)

    def test_reenvio_emite_envia_e_invalida_anterior(self):
        db = self.Session()
        first = send_email_verification(db=db, usuario=self._user(db), clock=self.clock)
        self.assertEqual(first.status, "sent")
        self.now += timedelta(seconds=60)
        second = send_email_verification(db=db, usuario=self._user(db), clock=self.clock)
        self.assertEqual(second.status, "sent")
        tokens = db.scalars(select(AccountActionToken).order_by(AccountActionToken.id)).all()
        self.assertEqual(tokens[0].invalidation_reason, "superseded")
        self.assertIsNone(tokens[1].invalidated_at)
        self.assertEqual(len(self.provider.messages), 2)
        db.close()

    def test_confirmacion_correcta_actualiza_usuario_y_consume_atomicamente(self):
        db = self.Session()
        send_email_verification(db=db, usuario=self._user(db), clock=self.clock)
        secret = self.provider.messages[0].body.split("#token=")[1].splitlines()[0]
        usuario = confirm_email_verification(db=db, secret=secret, clock=self.clock)
        self.assertEqual(usuario.email_verified_at.replace(tzinfo=timezone.utc), self.now)
        self.assertEqual(usuario.email_verification_source, EMAIL_LINK_SOURCE)
        token = db.scalar(select(AccountActionToken))
        self.assertEqual(token.consumed_at.replace(tzinfo=timezone.utc), self.now)
        db.close()

    def test_replay_y_estados_invalidos_comparten_error(self):
        cases = []
        for purpose, clock_offset, state in [
            (EMAIL_VERIFICATION, timedelta(0), "consumed"),
            (EMAIL_VERIFICATION, timedelta(hours=25), "active"),
            (PASSWORD_RESET, timedelta(0), "active"),
            (EMAIL_VERIFICATION, timedelta(0), "invalidated"),
        ]:
            db = self.Session()
            issued = issue_account_action_token(db=db, usuario_id=1, purpose=purpose, clock=self.clock)
            db.close()
            if state == "invalidated":
                with self.Session.begin() as db:
                    token = db.get(AccountActionToken, issued.token_id)
                    token.invalidated_at = self.now
                    token.invalidation_reason = "superseded"
            if state == "consumed":
                with self.Session() as db:
                    confirm_email_verification(db=db, secret=issued.secret, clock=self.clock)
            with self.Session() as db:
                with self.assertRaises(EmailVerificationError) as caught:
                    confirm_email_verification(db=db, secret=issued.secret, clock=lambda: self.now + clock_offset)
                cases.append(caught.exception.code)
        self.assertEqual(set(cases), {"email_verification_link_invalid"})

    def test_snapshot_incorrecto_es_error_publico_uniforme(self):
        db = self.Session()
        issued = issue_account_action_token(db=db, usuario_id=1, purpose=EMAIL_VERIFICATION, clock=self.clock)
        db.close()
        with self.Session.begin() as db:
            self._user(db).email_canonical = "changed@example.com"
        with self.Session() as db, self.assertRaises(EmailVerificationError) as caught:
            confirm_email_verification(db=db, secret=issued.secret, clock=self.clock)
        self.assertEqual(caught.exception.code, "email_verification_link_invalid")

    def test_usuario_verificado_no_emite_y_es_idempotente(self):
        with self.Session.begin() as db:
            user = self._user(db)
            user.email_verified_at = self.now
            user.email_verification_source = EMAIL_LINK_SOURCE
        db = self.Session()
        result = send_email_verification(db=db, usuario=self._user(db), clock=self.clock)
        self.assertEqual(result.status, "already_verified")
        self.assertEqual(self.provider.messages, [])
        self.assertEqual(db.scalar(select(AccountActionToken)), None)
        db.close()

    def test_cooldown_y_limites_se_aplican(self):
        db = self.Session()
        send_email_verification(db=db, usuario=self._user(db), clock=self.clock)
        with self.assertRaises(EmailVerificationError) as caught:
            send_email_verification(db=db, usuario=self._user(db), clock=lambda: self.now + timedelta(seconds=59))
        self.assertEqual(caught.exception.code, "email_verification_rate_limited")
        self.assertEqual(caught.exception.retry_after_seconds, 1)
        db.close()

    def test_fallo_provider_no_revierte_usuario_y_permite_reenvio(self):
        failing = FakeEmailProvider(EmailDeliveryError("provider_down", retryable=False))
        with patch("app.modules.users.services.email_verification_services.build_identity_email_provider", return_value=failing):
            db = self.Session()
            result = send_registration_verification(db=db, usuario=self._user(db), clock=self.clock)
            self.assertEqual(result.status, "delivery_failed")
            self.assertIsNotNone(db.get(Usuario, 1))
            self.assertEqual(db.scalar(select(AccountActionToken)).purpose, EMAIL_VERIFICATION)
            db.close()

    def test_confirmacion_es_atomica_si_falla_commit(self):
        db = self.Session()
        send_email_verification(db=db, usuario=self._user(db), clock=self.clock)
        secret = self.provider.messages[0].body.split("#token=")[1].splitlines()[0]
        failed = {"done": False}

        def fail_once(session):
            if not failed["done"]:
                failed["done"] = True
                raise RuntimeError("commit_failed")

        event.listen(db, "before_commit", fail_once)
        with self.assertRaisesRegex(RuntimeError, "commit_failed"):
            confirm_email_verification(db=db, secret=secret, clock=self.clock)
        event.remove(db, "before_commit", fail_once)
        db.close()
        with self.Session() as check:
            self.assertIsNone(self._user(check).email_verified_at)
            self.assertIsNone(check.scalar(select(AccountActionToken)).consumed_at)

    def test_verificacion_no_activa_enforcement(self):
        db = self.Session()
        issued = issue_account_action_token(db=db, usuario_id=1, purpose=EMAIL_VERIFICATION, clock=self.clock)
        db.close()
        with self.Session() as db:
            confirm_email_verification(db=db, secret=issued.secret, clock=self.clock)
        # El bloque no incorpora guards ni capabilities: sólo cambia evidencia.
        from app.modules.users.services import email_verification_services as source
        self.assertFalse(hasattr(source, "enforce_verified_email"))


if __name__ == "__main__":
    unittest.main()
