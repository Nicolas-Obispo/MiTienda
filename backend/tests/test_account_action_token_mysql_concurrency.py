import threading
import unittest
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone

from app.core.database import Base
from app.core.model_registry import import_all_models
from app.modules.users.models.identity_models import AccountActionToken
from app.modules.users.models.usuarios_models import Usuario
from app.modules.users.services.account_action_token_services import (
    EMAIL_VERIFICATION,
    AccountActionTokenInvalidError,
    consume_account_action_token,
    derive_token_state,
    issue_account_action_token,
)
from tests.mysql_stage97_test_support import isolated_mysql_test_engine


import_all_models()


class AccountActionTokenMySQLConcurrencyTests(unittest.TestCase):
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
        db = self.Session()
        db.add(
            Usuario(
                id=1,
                email="persona@example.com",
                email_canonical="persona@example.com",
                hashed_password="$2b$test",
            )
        )
        db.commit()
        db.close()
        self.now = datetime(2026, 9, 5, 12, 0, tzinfo=timezone.utc)

    def run_concurrently(self, operations):
        barrier = threading.Barrier(len(operations))

        def run(operation):
            db = self.Session()
            try:
                barrier.wait(timeout=5)
                return ("ok", operation(db))
            except Exception as exc:
                return ("error", exc)
            finally:
                db.close()

        with ThreadPoolExecutor(max_workers=len(operations)) as executor:
            return list(executor.map(run, operations))

    def test_two_concurrent_issues_leave_only_latest_active(self):
        results = self.run_concurrently(
            [
                lambda db: issue_account_action_token(
                    db=db,
                    usuario_id=1,
                    purpose=EMAIL_VERIFICATION,
                    clock=lambda: self.now,
                ),
                lambda db: issue_account_action_token(
                    db=db,
                    usuario_id=1,
                    purpose=EMAIL_VERIFICATION,
                    clock=lambda: self.now,
                ),
            ]
        )
        self.assertEqual([kind for kind, _ in results].count("ok"), 2)
        db = self.Session()
        tokens = db.query(AccountActionToken).all()
        states = [derive_token_state(token, now=self.now) for token in tokens]
        self.assertEqual(states.count("active"), 1)
        self.assertEqual(states.count("invalidated"), 1)
        db.close()

    def test_two_concurrent_consumptions_have_one_winner(self):
        db = self.Session()
        issued = issue_account_action_token(
            db=db,
            usuario_id=1,
            purpose=EMAIL_VERIFICATION,
            clock=lambda: self.now,
        )
        db.close()
        results = self.run_concurrently(
            [
                lambda db: consume_account_action_token(
                    db=db,
                    secret=issued.secret,
                    purpose=EMAIL_VERIFICATION,
                    clock=lambda: self.now,
                ),
                lambda db: consume_account_action_token(
                    db=db,
                    secret=issued.secret,
                    purpose=EMAIL_VERIFICATION,
                    clock=lambda: self.now,
                ),
            ]
        )
        self.assertEqual([kind for kind, _ in results].count("ok"), 1)
        errors = [value for kind, value in results if kind == "error"]
        self.assertEqual(len(errors), 1)
        self.assertIsInstance(errors[0], AccountActionTokenInvalidError)


if __name__ == "__main__":
    unittest.main()
