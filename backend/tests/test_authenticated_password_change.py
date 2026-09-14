from datetime import datetime, timedelta, timezone
import unittest
from unittest.mock import patch

from sqlalchemy import create_engine, event, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import Base
from app.core.model_registry import import_all_models
from app.core.security import hash_password
from app.modules.users.models.identity_models import AccountActionRateLimit, AccountActionToken, FeedGoSession, PasswordCredential
from app.modules.users.models.tokens_models import TokenRevocado
from app.modules.users.models.usuarios_models import Usuario
from app.modules.users.services.account_action_rate_limit_services import CURRENT_PASSWORD, subject_digest
from app.modules.users.services.account_action_token_services import PASSWORD_RESET, issue_account_action_token
from app.modules.users.services.authenticated_password_services import (
    AuthenticatedPasswordChangeError,
    change_authenticated_password,
)
from app.modules.users.services.feedgo_session_services import create_feedgo_session

import_all_models()


class AuthenticatedPasswordChangeTests(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)
        self.legacy_password = "abc"
        legacy_hash = hash_password(self.legacy_password)
        with self.Session.begin() as db:
            db.add(Usuario(id=1, email="person@example.com", email_canonical="person@example.com", hashed_password=legacy_hash))
            db.add(PasswordCredential(usuario_id=1, password_hash=legacy_hash, hash_version="bcrypt"))
        self.now = datetime(2026, 9, 5, 12, 0, tzinfo=timezone.utc)
        self.clock = lambda: self.now
        self.secret_patch = patch(
            "app.modules.users.services.account_action_rate_limit_services.settings.ACCOUNT_ACTION_RATE_LIMIT_HMAC_SECRET",
            "current-password-rate-secret",
        )
        self.secret_patch.start()

    def tearDown(self):
        self.secret_patch.stop(); self.engine.dispose()

    def change(self, current="abc", new="Password1"):
        db = self.Session()
        try:
            return change_authenticated_password(db=db, usuario=db.get(Usuario, 1), current_password=current, new_password=new, clock=self.clock)
        finally:
            db.close()

    def create_sessions(self):
        db = self.Session()
        for sid in ("current", "other"):
            create_feedgo_session(
                db, usuario_id=1, authentication_method="password",
                clock=self.clock, sid_factory=lambda value=sid: value,
            )
        db.commit(); db.close()

    def test_password_legacy_actual_es_valida_sin_politica_nueva(self):
        self.change(current="abc")
        with self.Session() as db:
            self.assertNotEqual(db.get(PasswordCredential, 1).password_hash, "abc")

    def test_hash_unico_y_dual_write_identico(self):
        with patch("app.modules.users.services.authenticated_password_services.hash_password", return_value="new-hash") as hasher:
            self.change()
        hasher.assert_called_once_with("Password1")
        with self.Session() as db:
            self.assertEqual(db.get(Usuario, 1).hashed_password, "new-hash")
            self.assertEqual(db.get(PasswordCredential, 1).password_hash, "new-hash")

    def test_incorrecta_registra_fallos_y_bloquea_despues_de_cinco(self):
        for _ in range(5):
            with self.assertRaises(AuthenticatedPasswordChangeError) as caught:
                self.change(current="wrong")
            self.assertEqual(caught.exception.code, "current_password_incorrect")
        with self.assertRaises(AuthenticatedPasswordChangeError) as caught:
            self.change(current=self.legacy_password)
        self.assertEqual(caught.exception.code, "current_password_rate_limited")

    def test_correcta_reinicia_fallos(self):
        for _ in range(2):
            with self.assertRaises(AuthenticatedPasswordChangeError): self.change(current="wrong")
        self.change()
        digest = subject_digest(action=CURRENT_PASSWORD, scope="15m", subject="user:1", secret="current-password-rate-secret")
        with self.Session() as db:
            row = db.scalar(select(AccountActionRateLimit).where(AccountActionRateLimit.subject_digest == digest))
            self.assertEqual(row.attempt_count, 0)

    def test_ventana_de_bloqueo_expira(self):
        for _ in range(5):
            with self.assertRaises(AuthenticatedPasswordChangeError): self.change(current="wrong")
        self.now += timedelta(minutes=15)
        self.change()

    def test_politica_nueva_y_limite_bcrypt_se_aplican(self):
        for invalid in ("short", "password1", "PASSWORD1", "Password", "Pass word1", "Áa1" + "x" * 70):
            with self.Session() as db, self.assertRaises(ValueError):
                change_authenticated_password(db=db, usuario=db.get(Usuario, 1), current_password="abc", new_password=invalid, clock=self.clock)

    def test_invalida_password_reset_activo(self):
        db = self.Session(); issued = issue_account_action_token(db=db, usuario_id=1, purpose=PASSWORD_RESET, clock=self.clock); db.close()
        self.change()
        with self.Session() as db:
            token = db.get(AccountActionToken, issued.token_id)
            self.assertEqual(token.invalidation_reason, "password_changed")

    def test_incorrecta_no_invalida_token(self):
        db = self.Session(); issued = issue_account_action_token(db=db, usuario_id=1, purpose=PASSWORD_RESET, clock=self.clock); db.close()
        with self.assertRaises(AuthenticatedPasswordChangeError): self.change(current="wrong")
        with self.Session() as db: self.assertIsNone(db.get(AccountActionToken, issued.token_id).invalidated_at)

    def test_rollback_no_diverge_ni_invalida(self):
        self.create_sessions()
        db = self.Session(); issued = issue_account_action_token(db=db, usuario_id=1, purpose=PASSWORD_RESET, clock=self.clock); db.close()
        db = self.Session(); original = db.get(Usuario, 1).hashed_password; failed = {"done": False}
        def fail_once(session):
            if not failed["done"]: failed["done"] = True; raise RuntimeError("commit_failed")
        event.listen(db, "before_commit", fail_once)
        with patch("app.modules.users.services.authenticated_password_services.hash_password", return_value="new-hash"):
            with self.assertRaisesRegex(RuntimeError, "commit_failed"):
                change_authenticated_password(db=db, usuario=db.get(Usuario, 1), current_password="abc", new_password="Password1", clock=self.clock)
        event.remove(db, "before_commit", fail_once); db.close()
        with self.Session() as check:
            self.assertEqual(check.get(Usuario, 1).hashed_password, original)
            self.assertEqual(check.get(PasswordCredential, 1).password_hash, original)
            self.assertIsNone(check.get(AccountActionToken, issued.token_id).invalidated_at)
            self.assertEqual(check.query(FeedGoSession).filter(FeedGoSession.revoked_at.is_(None)).count(), 2)

    def test_fallo_de_revocacion_hace_rollback_completo(self):
        self.create_sessions()
        with patch(
            "app.modules.users.services.authenticated_password_services.revoke_user_feedgo_sessions",
            side_effect=RuntimeError("session_revocation_failed"),
        ):
            with self.Session() as db, self.assertRaisesRegex(RuntimeError, "session_revocation_failed"):
                change_authenticated_password(
                    db=db,
                    usuario=db.get(Usuario, 1),
                    current_password="abc",
                    new_password="Password1",
                    current_session_sid="current",
                    clock=self.clock,
                )
        with self.Session() as db:
            self.assertTrue(db.get(PasswordCredential, 1).password_hash != "Password1")
            self.assertEqual(db.get(Usuario, 1).hashed_password, db.get(PasswordCredential, 1).password_hash)
            self.assertEqual(db.query(FeedGoSession).filter(FeedGoSession.revoked_at.is_(None)).count(), 2)

    def test_no_crea_revocacion_ni_feedgo_session(self):
        self.change()
        with self.Session() as db:
            self.assertEqual(db.query(TokenRevocado).count(), 0)
            self.assertEqual(db.query(FeedGoSession).count(), 0)


if __name__ == "__main__": unittest.main()
