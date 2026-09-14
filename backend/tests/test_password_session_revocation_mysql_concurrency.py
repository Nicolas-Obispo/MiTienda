import threading
import unittest
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from unittest.mock import patch

from app.core.database import Base
from app.core.model_registry import import_all_models
from app.core.security import hash_password
from app.modules.users.models.identity_models import FeedGoSession, PasswordCredential
from app.modules.users.models.usuarios_models import Usuario
from app.modules.users.services.account_action_token_services import (
    PASSWORD_RESET,
    issue_account_action_token,
)
from app.modules.users.services.authenticated_password_services import (
    AuthenticatedPasswordChangeError,
    change_authenticated_password,
)
from app.modules.users.services.feedgo_session_services import create_feedgo_session
from app.modules.users.services.password_recovery_services import (
    PasswordResetError,
    reset_password_with_token,
)
from tests.mysql_stage97_test_support import isolated_mysql_test_engine


import_all_models()


class PasswordSessionRevocationMySQLConcurrencyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.engine, cls.Session = isolated_mysql_test_engine()

    @classmethod
    def tearDownClass(cls):
        Base.metadata.drop_all(cls.engine)
        cls.engine.dispose()

    def setUp(self):
        Base.metadata.drop_all(self.engine)
        Base.metadata.create_all(self.engine)
        self.now = datetime.now(timezone.utc)
        password_hash = hash_password("Password1")
        db = self.Session()
        db.add(Usuario(
            id=1, email="user@example.com", email_canonical="user@example.com",
            hashed_password=password_hash,
        ))
        db.commit()
        db.add(PasswordCredential(
            usuario_id=1, password_hash=password_hash, hash_version="bcrypt"
        ))
        db.commit()
        for sid in ("current", "other"):
            create_feedgo_session(
                db, usuario_id=1, authentication_method="password",
                sid_factory=lambda value=sid: value, clock=lambda: self.now,
            )
        db.commit(); db.close()
        self.rate_patch = patch(
            "app.modules.users.services.account_action_rate_limit_services.settings.ACCOUNT_ACTION_RATE_LIMIT_HMAC_SECRET",
            "mysql-password-session-rate-secret",
        )
        self.rate_patch.start()

    def tearDown(self):
        self.rate_patch.stop()

    def run_two(self, operation):
        barrier = threading.Barrier(2)
        def worker():
            db = self.Session()
            try:
                barrier.wait(timeout=5)
                operation(db)
                return "ok"
            except (PasswordResetError, AuthenticatedPasswordChangeError):
                return "rejected"
            finally:
                db.close()
        with ThreadPoolExecutor(max_workers=2) as executor:
            return list(executor.map(lambda _: worker(), range(2)))

    def test_concurrent_reset_has_one_winner_and_revokes_all_sessions(self):
        db = self.Session()
        issued = issue_account_action_token(
            db=db, usuario_id=1, purpose=PASSWORD_RESET, clock=lambda: self.now
        )
        db.close()
        results = self.run_two(lambda db: reset_password_with_token(
            db=db, secret=issued.secret, new_password="Password2", clock=lambda: self.now
        ))
        self.assertEqual(results.count("ok"), 1)
        self.assertEqual(results.count("rejected"), 1)
        db = self.Session()
        self.assertEqual(db.query(FeedGoSession).filter(FeedGoSession.revoked_at.is_(None)).count(), 0)
        self.assertEqual(db.get(Usuario, 1).hashed_password, db.get(PasswordCredential, 1).password_hash)
        db.close()

    def test_concurrent_change_preserves_only_current_session(self):
        results = self.run_two(lambda db: change_authenticated_password(
            db=db,
            usuario=db.get(Usuario, 1),
            current_password="Password1",
            new_password="Password2",
            current_session_sid="current",
            clock=lambda: self.now,
        ))
        self.assertEqual(results.count("ok"), 1)
        self.assertEqual(results.count("rejected"), 1)
        db = self.Session()
        self.assertIsNone(db.get(FeedGoSession, "current").revoked_at)
        self.assertIsNotNone(db.get(FeedGoSession, "other").revoked_at)
        self.assertEqual(db.get(Usuario, 1).hashed_password, db.get(PasswordCredential, 1).password_hash)
        db.close()


if __name__ == "__main__":
    unittest.main()
