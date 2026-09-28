import os
import threading
import unittest
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta

from sqlalchemy import func, select

from app.modules.users.models.identity_models import AccountActionRateLimit
from app.modules.users.services.account_action_rate_limit_services import (
    PASSWORD_LOGIN,
    PasswordLoginRateLimitConfig,
    cleanup_expired_password_login_buckets,
    complete_password_login_success,
    reserve_password_login_attempt,
)
from tests.mysql_stage97_test_support import isolated_mysql_test_engine


@unittest.skipUnless(
    os.environ.get("FEEDGO_STAGE97_TEST_DATABASE_URL"),
    "requiere FEEDGO_STAGE97_TEST_DATABASE_URL aislada",
)
class PasswordLoginRateLimitMySQLConcurrencyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.engine, cls.Session = isolated_mysql_test_engine()

    @classmethod
    def tearDownClass(cls):
        AccountActionRateLimit.__table__.drop(cls.engine, checkfirst=True)
        cls.engine.dispose()

    def setUp(self):
        AccountActionRateLimit.__table__.drop(self.engine, checkfirst=True)
        AccountActionRateLimit.__table__.create(self.engine)
        self.now = datetime(2026, 9, 25, 12, 0, 0)
        self.secret = "password-login-mysql-concurrency-secret"

    def _config(self, *, subject=5, client=20, subject_window=900, client_window=3600):
        return PasswordLoginRateLimitConfig(
            subject_limit=subject,
            subject_window_seconds=subject_window,
            client_limit=client,
            client_window_seconds=client_window,
            cleanup_retention_seconds=max(subject_window, client_window) * 2,
            cleanup_batch_size=100,
        )

    def _concurrent(self, operations):
        barrier = threading.Barrier(len(operations))

        def run(operation):
            with self.Session() as db:
                barrier.wait(timeout=15)
                return operation(db)

        with ThreadPoolExecutor(max_workers=len(operations)) as executor:
            return list(executor.map(run, operations))

    def _reserve(self, db, *, email, host, config, now=None):
        return reserve_password_login_attempt(
            db,
            email_canonical=email,
            client_host=host,
            config=config,
            now=now or self.now,
            secret=self.secret,
        )

    def test_mismo_subject_multiples_workers_y_clients(self):
        config = self._config(subject=5, client=100)
        operations = [
            lambda db, index=index: self._reserve(
                db,
                email="shared@example.com",
                host=f"198.51.100.{index}",
                config=config,
            )
            for index in range(10)
        ]
        results = self._concurrent(operations)
        self.assertEqual(sum(result.status == "reserved" for result in results), 5)
        self.assertEqual(sum(result.status == "rate_limited" for result in results), 5)
        self.assertNotIn("unavailable", {result.status for result in results})

    def test_mismo_subject_y_client_multiples_workers(self):
        config = self._config(subject=5, client=20)
        operations = [
            lambda db: self._reserve(
                db,
                email="one-bucket-pair@example.com",
                host="198.51.100.8",
                config=config,
            )
            for _ in range(10)
        ]
        results = self._concurrent(operations)
        self.assertEqual(sum(result.status == "reserved" for result in results), 5)
        self.assertEqual(sum(result.status == "rate_limited" for result in results), 5)
        self.assertNotIn("unavailable", {result.status for result in results})

    def test_mismo_client_multiples_subjects(self):
        config = self._config(subject=100, client=5)
        operations = [
            lambda db, index=index: self._reserve(
                db,
                email=f"person-{index}@example.com",
                host="198.51.100.9",
                config=config,
            )
            for index in range(10)
        ]
        results = self._concurrent(operations)
        self.assertEqual(sum(result.status == "reserved" for result in results), 5)
        self.assertEqual(sum(result.status == "rate_limited" for result in results), 5)
        self.assertNotIn("unavailable", {result.status for result in results})

    def test_mezcla_subject_client_sin_incrementos_perdidos(self):
        config = self._config(subject=3, client=3)
        operations = [
            lambda db, index=index: self._reserve(
                db,
                email=f"shared-{index % 2}@example.com",
                host=f"198.51.100.{index % 2}",
                config=config,
            )
            for index in range(8)
        ]
        results = self._concurrent(operations)
        allowed = sum(result.status == "reserved" for result in results)
        self.assertEqual(allowed, 6)
        self.assertNotIn("unavailable", {result.status for result in results})
        with self.Session() as db:
            total = db.scalar(
                select(func.sum(AccountActionRateLimit.attempt_count)).where(
                    AccountActionRateLimit.action == PASSWORD_LOGIN
                )
            )
        self.assertEqual(total, allowed * 2)

    def test_rollback_externo_no_restituye_reserva(self):
        config = self._config(subject=1)
        with self.Session() as db:
            first = self._reserve(
                db,
                email="rollback@example.com",
                host="198.51.100.1",
                config=config,
            )
            db.rollback()
        self.assertEqual(first.status, "reserved")
        with self.Session() as db:
            second = self._reserve(
                db,
                email="rollback@example.com",
                host="198.51.100.2",
                config=config,
            )
        self.assertEqual(second.status, "rate_limited")

    def test_exito_concurrente_no_deja_contador_negativo(self):
        config = self._config(subject=5, client=20)
        reservations = []
        for index in range(10):
            with self.Session() as db:
                result = self._reserve(
                    db,
                    email=f"success-{index}@example.com",
                    host="198.51.100.5",
                    config=config,
                )
            self.assertEqual(result.status, "reserved")
            reservations.append(result.reservation)

        results = self._concurrent(
            [
                lambda db, reservation=reservation: complete_password_login_success(
                    db, reservation=reservation, now=self.now
                )
                for reservation in reservations
            ]
        )
        self.assertEqual({result.status for result in results}, {"completed"})
        with self.Session() as db:
            minimum = db.scalar(
                select(func.min(AccountActionRateLimit.attempt_count)).where(
                    AccountActionRateLimit.action == PASSWORD_LOGIN
                )
            )
            total = db.scalar(
                select(func.sum(AccountActionRateLimit.attempt_count)).where(
                    AccountActionRateLimit.action == PASSWORD_LOGIN
                )
            )
        self.assertGreaterEqual(minimum, 0)
        self.assertEqual(total, 0)

    def test_expiracion_en_borde(self):
        config = self._config(subject=1, client=20, subject_window=10, client_window=20)
        with self.Session() as db:
            first = self._reserve(
                db, email="edge@example.com", host="198.51.100.1", config=config
            )
        with self.Session() as db:
            denied = self._reserve(
                db,
                email="edge@example.com",
                host="198.51.100.2",
                config=config,
                now=self.now + timedelta(seconds=9),
            )
        with self.Session() as db:
            allowed = self._reserve(
                db,
                email="edge@example.com",
                host="198.51.100.3",
                config=config,
                now=self.now + timedelta(seconds=10),
            )
        self.assertEqual(first.status, "reserved")
        self.assertEqual(denied.status, "rate_limited")
        self.assertEqual(allowed.status, "reserved")

    def test_cleanup_concurrente_no_elimina_bucket_vigente(self):
        config = self._config(subject=5, client=20)
        old = self.now - timedelta(hours=3)
        with self.Session() as db:
            self.assertEqual(
                self._reserve(
                    db,
                    email="cleanup@example.com",
                    host="198.51.100.6",
                    config=config,
                    now=old,
                ).status,
                "reserved",
            )

        results = self._concurrent(
            [
                lambda db: cleanup_expired_password_login_buckets(
                    db, config=config, now=self.now
                ),
                lambda db: self._reserve(
                    db,
                    email="cleanup@example.com",
                    host="198.51.100.6",
                    config=config,
                    now=self.now,
                ),
            ]
        )
        reserve_result = next(result for result in results if hasattr(result, "reservation"))
        self.assertEqual(reserve_result.status, "reserved")
        with self.Session() as db:
            rows = list(
                db.scalars(
                    select(AccountActionRateLimit).where(
                        AccountActionRateLimit.action == PASSWORD_LOGIN
                    )
                )
            )
        self.assertEqual(len(rows), 2)
        self.assertEqual({row.attempt_count for row in rows}, {1})


if __name__ == "__main__":
    unittest.main()
