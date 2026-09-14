from datetime import datetime, timedelta, timezone
import unittest
from unittest.mock import patch

from sqlalchemy import create_engine, event, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import Base
from app.core.model_registry import import_all_models
from app.modules.communications.providers.email_provider import EmailDeliveryError, FakeEmailProvider
from app.modules.users.models.identity_models import AccountActionToken, FeedGoSession, PasswordCredential
from app.modules.users.models.usuarios_models import Usuario
from app.modules.users.services.account_action_rate_limit_services import LocalPublicRateLimiter
from app.modules.users.services.account_action_token_services import EMAIL_VERIFICATION, PASSWORD_RESET, issue_account_action_token
from app.modules.users.services.password_recovery_services import (
    PasswordResetError,
    request_password_recovery,
    reset_password_with_token,
)
from app.modules.users.services.feedgo_session_services import create_feedgo_session
from app.modules.users.schemas.usuarios_schemas import PasswordRecoveryRequest

import_all_models()


class PasswordRecoveryFlowTests(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)
        with self.Session.begin() as db:
            db.add(Usuario(id=1, email="Person@Example.com", email_canonical="person@example.com", hashed_password="legacy", email_verified_at=datetime(2026, 1, 1, tzinfo=timezone.utc)))
            db.add(PasswordCredential(usuario_id=1, password_hash="legacy", hash_version="bcrypt"))
            db.add(Usuario(id=2, email="google@example.com", email_canonical="google@example.com", hashed_password="legacy"))
        self.now = datetime(2026, 9, 5, 12, 0, tzinfo=timezone.utc)
        self.clock = lambda: self.now
        self.provider = FakeEmailProvider()
        self.local = LocalPublicRateLimiter(secret="rate-secret", clock=lambda: self.now.replace(tzinfo=None))
        self.patches = [
            patch("app.modules.users.services.account_action_rate_limit_services.settings.ACCOUNT_ACTION_RATE_LIMIT_HMAC_SECRET", "rate-secret"),
            patch("app.modules.users.services.password_recovery_services.build_identity_email_provider", return_value=self.provider),
            patch("app.modules.users.services.password_recovery_services.settings.IDENTITY_EMAIL_ENABLED", True),
            patch("app.modules.users.services.password_recovery_services.settings.IDENTITY_EMAIL_PROVIDER", "fake"),
            patch("app.modules.communications.services.identity_email_services.settings.IDENTITY_EMAIL_FROM_ADDRESS", "hola@feedgo.test"),
            patch("app.modules.communications.services.identity_email_services.settings.IDENTITY_EMAIL_PUBLIC_BASE_URL", "https://feedgo.test"),
        ]
        for item in self.patches: item.start()

    def tearDown(self):
        for item in reversed(self.patches): item.stop()
        self.engine.dispose()

    def recover(self, email, host="203.0.113.1"):
        db = self.Session()
        request_password_recovery(db=db, email=email, client_host=host, clock=self.clock, local_limiter=self.local)
        db.close()

    def test_existente_emite_y_canonicaliza(self):
        self.recover("  PERSON@example.COM  ")
        self.assertEqual(len(self.provider.messages), 1)
        with self.Session() as db:
            token = db.scalar(select(AccountActionToken))
            self.assertEqual(token.purpose, PASSWORD_RESET)
            self.assertEqual(token.email_canonical_snapshot, "person@example.com")

    def test_inexistente_y_sin_credential_no_emiten_sin_diferenciar(self):
        self.recover("missing@example.com")
        self.recover("google@example.com")
        self.assertEqual(self.provider.messages, [])

    def test_canonical_invalido_no_es_rechazado_por_el_contrato_http(self):
        self.assertEqual(PasswordRecoveryRequest(email="").email, "")
        oversized = "x" * 512
        self.assertEqual(PasswordRecoveryRequest(email=oversized).email, oversized)
        self.recover("")
        self.recover(oversized)
        self.assertEqual(self.provider.messages, [])

    def test_provider_failure_y_rate_limit_son_publicamente_silenciosos(self):
        failing = FakeEmailProvider(EmailDeliveryError("down", retryable=False))
        with patch("app.modules.users.services.password_recovery_services.build_identity_email_provider", return_value=failing):
            self.recover("person@example.com")
        for index in range(5):
            self.now += timedelta(minutes=1)
            self.recover("person@example.com", host=f"203.0.113.{index + 10}")
        self.assertLessEqual(len(self.provider.messages), 4)

    def test_nueva_emision_supersede_anterior(self):
        self.recover("person@example.com")
        self.now += timedelta(minutes=1)
        self.recover("person@example.com")
        with self.Session() as db:
            tokens = db.scalars(select(AccountActionToken).order_by(AccountActionToken.id)).all()
            self.assertEqual(tokens[0].invalidation_reason, "superseded")
            self.assertIsNone(tokens[1].invalidated_at)

    def issue(self, purpose=PASSWORD_RESET):
        db = self.Session()
        issued = issue_account_action_token(db=db, usuario_id=1, purpose=purpose, clock=self.clock)
        db.close()
        return issued

    def create_sessions(self, count=3):
        db = self.Session()
        for _ in range(count):
            create_feedgo_session(
                db, usuario_id=1, authentication_method="password", clock=self.clock
            )
        db.commit(); db.close()

    def test_reset_hash_unico_dual_write_consumo_y_no_login(self):
        self.create_sessions()
        issued = self.issue()
        with patch("app.modules.users.services.password_recovery_services.hash_password", return_value="new-hash") as hasher:
            db = self.Session()
            result = reset_password_with_token(db=db, secret=issued.secret, new_password="Password1", clock=self.clock)
            db.close()
        self.assertIsNone(result)
        hasher.assert_called_once_with("Password1")
        with self.Session() as db:
            self.assertEqual(db.get(Usuario, 1).hashed_password, "new-hash")
            self.assertEqual(db.get(PasswordCredential, 1).password_hash, "new-hash")
            self.assertIsNotNone(db.get(AccountActionToken, issued.token_id).consumed_at)
            self.assertEqual(db.query(FeedGoSession).filter(FeedGoSession.revoked_at.is_(None)).count(), 0)

    def test_reset_invalida_otros_tokens_como_password_changed(self):
        issued = self.issue()
        with self.Session.begin() as db:
            db.add(AccountActionToken(usuario_id=1, purpose=PASSWORD_RESET, token_digest="a" * 64,
                email_canonical_snapshot="person@example.com", created_at=self.now,
                expires_at=self.now + timedelta(minutes=30), issuance_id="sibling"))
        with patch("app.modules.users.services.password_recovery_services.hash_password", return_value="new-hash"):
            db = self.Session(); reset_password_with_token(db=db, secret=issued.secret, new_password="Password1", clock=self.clock); db.close()
        with self.Session() as db:
            sibling = db.scalar(select(AccountActionToken).where(AccountActionToken.issuance_id == "sibling"))
            self.assertEqual(sibling.invalidation_reason, "password_changed")

    def test_invalido_expirado_usado_purpose_y_snapshot_comparten_error(self):
        secrets = []
        invalid = self.issue(); secrets.append((invalid.secret, self.clock))
        with self.Session() as db:
            with patch("app.modules.users.services.password_recovery_services.hash_password", return_value="x"):
                reset_password_with_token(db=db, secret=invalid.secret, new_password="Password1", clock=self.clock)
        expired = self.issue(); secrets.append((expired.secret, lambda: self.now + timedelta(minutes=31)))
        wrong = self.issue(EMAIL_VERIFICATION); secrets.append((wrong.secret, self.clock))
        snapshot = self.issue()
        with self.Session.begin() as db: db.get(Usuario, 1).email_canonical = "changed@example.com"
        secrets.append((snapshot.secret, self.clock))
        for secret, clock in secrets:
            with self.Session() as db, self.assertRaises(PasswordResetError) as caught:
                reset_password_with_token(db=db, secret=secret, new_password="Password1", clock=clock)
            self.assertEqual(caught.exception.code, "password_reset_link_invalid")

    def test_password_policy_se_aplica_antes_de_hash(self):
        issued = self.issue()
        with patch("app.modules.users.services.password_recovery_services.hash_password") as hasher:
            with self.Session() as db, self.assertRaises(ValueError):
                reset_password_with_token(db=db, secret=issued.secret, new_password="weak", clock=self.clock)
        hasher.assert_not_called()

    def test_rollback_no_consume_ni_diverge_hashes(self):
        self.create_sessions()
        issued = self.issue()
        db = self.Session(); failed = {"done": False}
        def fail_once(session):
            if not failed["done"]: failed["done"] = True; raise RuntimeError("commit_failed")
        event.listen(db, "before_commit", fail_once)
        with patch("app.modules.users.services.password_recovery_services.hash_password", return_value="new-hash"):
            with self.assertRaisesRegex(RuntimeError, "commit_failed"):
                reset_password_with_token(db=db, secret=issued.secret, new_password="Password1", clock=self.clock)
        event.remove(db, "before_commit", fail_once); db.close()
        with self.Session() as check:
            self.assertEqual(check.get(Usuario, 1).hashed_password, "legacy")
            self.assertEqual(check.get(PasswordCredential, 1).password_hash, "legacy")
            self.assertIsNone(check.get(AccountActionToken, issued.token_id).consumed_at)
            self.assertEqual(check.query(FeedGoSession).filter(FeedGoSession.revoked_at.is_(None)).count(), 3)

    def test_failure_during_session_revocation_rolls_back_password_and_token(self):
        self.create_sessions()
        issued = self.issue()
        with patch(
            "app.modules.users.services.password_recovery_services.revoke_user_feedgo_sessions",
            side_effect=RuntimeError("session_revocation_failed"),
        ):
            with self.Session() as db, self.assertRaisesRegex(RuntimeError, "session_revocation_failed"):
                reset_password_with_token(
                    db=db, secret=issued.secret, new_password="Password1", clock=self.clock
                )
        with self.Session() as db:
            self.assertEqual(db.get(Usuario, 1).hashed_password, "legacy")
            self.assertEqual(db.get(PasswordCredential, 1).password_hash, "legacy")
            self.assertIsNone(db.get(AccountActionToken, issued.token_id).consumed_at)
            self.assertEqual(db.query(FeedGoSession).filter(FeedGoSession.revoked_at.is_(None)).count(), 3)


if __name__ == "__main__": unittest.main()
