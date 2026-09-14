import threading
import unittest
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime

from sqlalchemy import select

from app.core.database import Base
from app.core.model_registry import import_all_models
from app.modules.users.models.identity_models import AccountActionRateLimit
from app.modules.users.services.account_action_rate_limit_services import (
    PASSWORD_RESET,
    record_password_reset,
    subject_digest,
)
from tests.mysql_stage97_test_support import isolated_mysql_test_engine


import_all_models()


class AccountActionRateLimitMySQLConcurrencyTests(unittest.TestCase):
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
        self.now = datetime(2026, 9, 5, 12, 0, 0)
        self.secret = "mysql-concurrency-dedicated-secret"

    def _concurrent(self, count, operation):
        barrier = threading.Barrier(count)

        def run(_):
            db = self.Session()
            try:
                barrier.wait(timeout=10)
                result = operation(db)
                db.commit()
                return result
            except Exception:
                db.rollback()
                raise
            finally:
                db.close()

        with ThreadPoolExecutor(max_workers=count) as executor:
            return list(executor.map(run, range(count)))

    def test_requests_concurrentes_no_pierden_incrementos(self):
        results = self._concurrent(
            5,
            lambda db: record_password_reset(
                db,
                email_canonical="parallel@example.com",
                now=self.now,
                secret=self.secret,
            ),
        )
        self.assertEqual(sum(result.allowed for result in results), 5)
        digest = subject_digest(
            action=PASSWORD_RESET,
            scope="hour",
            subject="destination:parallel@example.com",
            secret=self.secret,
        )
        with self.Session() as db:
            row = db.execute(
                select(AccountActionRateLimit).where(
                    AccountActionRateLimit.action == PASSWORD_RESET,
                    AccountActionRateLimit.subject_digest == digest,
                )
            ).scalar_one()
            self.assertEqual(row.attempt_count, 5)

    def test_limite_concurrente_deja_exactamente_cinco_permitidos(self):
        results = self._concurrent(
            10,
            lambda db: record_password_reset(
                db,
                email_canonical="limit@example.com",
                now=self.now,
                secret=self.secret,
            ),
        )
        self.assertEqual(sum(result.allowed for result in results), 5)
        self.assertEqual(sum(not result.allowed for result in results), 5)


if __name__ == "__main__":
    unittest.main()
