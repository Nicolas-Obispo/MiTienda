import os
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
import threading
import unittest

from sqlalchemy import inspect

import migrate_google_identity_foundation as migration
from app.core.database import Base
from app.core.model_registry import import_all_models
from app.modules.users.models.identity_models import OAuthAuthorizationTransaction
from app.modules.users.models.usuarios_models import Usuario
from app.modules.users.services.oauth_authorization_transaction_services import (
    OAuthAuthorizationTransactionError,
    create_oauth_authorization_transaction,
    validate_and_consume_oauth_authorization_transaction,
)
from tests.mysql_stage97_test_support import isolated_mysql_test_engine


import_all_models()


@unittest.skipUnless(
    os.environ.get("FEEDGO_STAGE97_TEST_DATABASE_URL"),
    "requiere FEEDGO_STAGE97_TEST_DATABASE_URL aislada",
)
class GoogleIdentityFoundationMySQLMigrationTests(unittest.TestCase):
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

    def test_clean_migration_makes_legacy_hash_nullable_and_is_idempotent(self):
        with self.engine.begin() as connection:
            connection.exec_driver_sql("DROP TABLE oauth_session_delivery_handles")
            connection.exec_driver_sql("DROP TABLE oauth_authorization_transactions")
            connection.exec_driver_sql(
                "ALTER TABLE usuarios MODIFY COLUMN hashed_password VARCHAR(255) NOT NULL"
            )
            connection.exec_driver_sql(
                "INSERT INTO usuarios "
                "(id, email, hashed_password, modo_activo, onboarding_completo) "
                "VALUES (99, 'existing@test.local', 'existing-hash', 'usuario', 0)"
            )
            first = migration.upgrade(connection)
            second = migration.upgrade(connection)
        self.assertIn("usuarios.hashed_password_nullable", first["changes"])
        self.assertIn(migration.TRANSACTION_TABLE, first["changes"])
        self.assertEqual(second["changes"], [])
        columns = {
            item["name"]: item for item in inspect(self.engine).get_columns("usuarios")
        }
        self.assertTrue(columns["hashed_password"]["nullable"])
        with self.engine.connect() as connection:
            self.assertEqual(
                connection.exec_driver_sql(
                    "SELECT hashed_password FROM usuarios WHERE id = 99"
                ).scalar_one(),
                "existing-hash",
            )

    def test_empty_partial_transaction_table_is_recovered_and_rerun_is_noop(self):
        with self.engine.begin() as connection:
            connection.exec_driver_sql("DROP TABLE oauth_session_delivery_handles")
            connection.exec_driver_sql("DROP TABLE oauth_authorization_transactions")
            connection.exec_driver_sql(
                "CREATE TABLE oauth_authorization_transactions (id VARCHAR(64) PRIMARY KEY)"
            )
            first = migration.upgrade(connection)
            second = migration.upgrade(connection)
        self.assertIn("oauth_authorization_transactions.provider", first["changes"])
        self.assertIn("fk_oauth_authorization_transactions_usuario", first["changes"])
        self.assertIn("uq_oauth_authorization_transactions_state", first["changes"])
        self.assertEqual(second["changes"], [])
        inspector = inspect(self.engine)
        columns = {item["name"] for item in inspector.get_columns(migration.TRANSACTION_TABLE)}
        self.assertTrue(set(migration.TRANSACTION_COLUMNS).issubset(columns))
        self.assertEqual(
            {item["name"] for item in inspector.get_check_constraints(migration.TRANSACTION_TABLE)},
            set(migration.TRANSACTION_CHECKS),
        )

    def test_concurrent_consumption_has_exactly_one_winner(self):
        now = datetime(2026, 9, 15, 12, 0, tzinfo=timezone.utc)
        db = self.Session()
        db.add(Usuario(id=1, email="oauth@test.local", hashed_password=None))
        db.commit()
        material = create_oauth_authorization_transaction(
            db,
            provider="google",
            purpose="signup",
            clock=lambda: now,
        )
        db.commit()
        db.close()
        barrier = threading.Barrier(2)

        def consume():
            worker = self.Session()
            try:
                barrier.wait(timeout=5)
                validate_and_consume_oauth_authorization_transaction(
                    worker,
                    transaction_id=material.transaction_id,
                    state=material.state,
                    nonce=material.nonce,
                    provider="google",
                    purpose="signup",
                    clock=lambda: now + timedelta(seconds=1),
                )
                worker.commit()
                return True
            except OAuthAuthorizationTransactionError:
                worker.rollback()
                return False
            finally:
                worker.close()

        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(lambda _: consume(), range(2)))
        self.assertEqual(results.count(True), 1)
        check = self.Session()
        transaction = check.get(OAuthAuthorizationTransaction, material.transaction_id)
        self.assertIsNotNone(transaction.consumed_at)
        self.assertIsNone(transaction.pkce_verifier)
        check.close()


if __name__ == "__main__":
    unittest.main()
