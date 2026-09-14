import unittest
from datetime import datetime, timedelta, timezone

from sqlalchemy import create_engine, inspect
from sqlalchemy.exc import IntegrityError

import migrate_account_action_foundation as migration
from app.core.config import Settings
from app.core.database import Base
from app.core.model_registry import import_all_models


class AccountActionMetadataTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import_all_models()

    def test_token_contract_metadata(self):
        table = Base.metadata.tables["account_action_tokens"]
        self.assertNotIn("status", table.columns)
        self.assertEqual(
            set(table.columns.keys()),
            {
                "id", "usuario_id", "purpose", "token_digest",
                "email_canonical_snapshot", "created_at", "expires_at",
                "consumed_at", "invalidated_at", "invalidation_reason",
                "issuance_id",
            },
        )
        self.assertFalse(table.c.usuario_id.nullable)
        self.assertFalse(table.c.token_digest.nullable)
        self.assertFalse(table.c.email_canonical_snapshot.nullable)
        self.assertTrue(table.c.consumed_at.nullable)
        self.assertTrue(table.c.invalidated_at.nullable)
        self.assertTrue(table.c.invalidation_reason.nullable)

        checks = {
            constraint.name
            for constraint in table.constraints
            if constraint.__class__.__name__ == "CheckConstraint"
        }
        self.assertEqual(
            checks,
            {
                "ck_account_action_tokens_purpose",
                "ck_account_action_tokens_expiry",
                "ck_account_action_tokens_terminal_state",
                "ck_account_action_tokens_invalidation_reason",
                "ck_account_action_tokens_invalidation_pair",
            },
        )
        uniques = {
            tuple(column.name for column in constraint.columns)
            for constraint in table.constraints
            if constraint.__class__.__name__ == "UniqueConstraint"
        }
        self.assertEqual(uniques, {("token_digest",), ("issuance_id",)})
        indexes = {
            tuple(column.name for column in index.columns)
            for index in table.indexes
            if not index.unique
        }
        self.assertIn(("usuario_id", "purpose", "created_at"), indexes)
        self.assertIn(("purpose", "expires_at"), indexes)

    def test_rate_limit_contract_metadata(self):
        table = Base.metadata.tables["account_action_rate_limits"]
        self.assertEqual(
            set(table.columns.keys()),
            {
                "id", "action", "subject_digest", "window_started_at",
                "attempt_count", "blocked_until", "updated_at",
            },
        )
        self.assertEqual(table.c.attempt_count.server_default.arg, "0")
        self.assertTrue(table.c.blocked_until.nullable)
        uniques = {
            tuple(column.name for column in constraint.columns)
            for constraint in table.constraints
            if constraint.__class__.__name__ == "UniqueConstraint"
        }
        self.assertEqual(uniques, {("action", "subject_digest")})

    def test_identity_email_config_is_disabled_and_independent(self):
        settings = Settings(
            DATABASE_URL="sqlite://",
            SECRET_KEY="test-only",
            ALGORITHM="HS256",
            ACCESS_TOKEN_EXPIRE_MINUTES=60,
            ADMIN_EMAIL_ENABLED=True,
            _env_file=None,
        )
        self.assertTrue(settings.ADMIN_EMAIL_ENABLED)
        self.assertFalse(settings.IDENTITY_EMAIL_ENABLED)
        self.assertEqual(settings.IDENTITY_EMAIL_PROVIDER, "disabled")
        self.assertIsNone(settings.IDENTITY_EMAIL_FROM_ADDRESS)
        self.assertIsNone(settings.IDENTITY_EMAIL_PUBLIC_BASE_URL)
        self.assertEqual(settings.IDENTITY_EMAIL_TIMEOUT_SECONDS, 5.0)


class AccountActionMigrationTests(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine("sqlite://")
        with self.engine.begin() as connection:
            connection.exec_driver_sql(
                "CREATE TABLE usuarios ("
                "id INTEGER PRIMARY KEY, email VARCHAR(255) NOT NULL, "
                "hashed_password VARCHAR(255) NOT NULL)"
            )
            connection.exec_driver_sql(
                "INSERT INTO usuarios (id, email, hashed_password) "
                "VALUES (1, 'persona@example.com', '$2b$legacy')"
            )

    def tearDown(self):
        self.engine.dispose()

    def _valid_token_parameters(self):
        now = datetime.now(timezone.utc)
        return {
            "usuario_id": 1,
            "purpose": "email_verification",
            "token_digest": "a" * 64,
            "email": "persona@example.com",
            "created_at": now,
            "expires_at": now + timedelta(hours=24),
            "issuance_id": "issuance-1",
        }

    def _insert_token(self, connection, **overrides):
        values = self._valid_token_parameters()
        values.update(overrides)
        connection.exec_driver_sql(
            "INSERT INTO account_action_tokens "
            "(usuario_id, purpose, token_digest, email_canonical_snapshot, "
            "created_at, expires_at, consumed_at, invalidated_at, "
            "invalidation_reason, issuance_id) VALUES "
            "(:usuario_id, :purpose, :token_digest, :email, :created_at, "
            ":expires_at, :consumed_at, :invalidated_at, "
            ":invalidation_reason, :issuance_id)",
            {
                **values,
                "consumed_at": values.get("consumed_at"),
                "invalidated_at": values.get("invalidated_at"),
                "invalidation_reason": values.get("invalidation_reason"),
            },
        )

    def test_upgrade_es_aditivo_idempotente_y_sin_backfill(self):
        with self.engine.begin() as connection:
            first = migration.upgrade(connection)
            second = migration.upgrade(connection)
            self.assertEqual(set(first["changes"]), set(migration.NEW_TABLES))
            self.assertEqual(first["backfill"], {})
            self.assertEqual(second["changes"], [])
            self.assertEqual(second["backfill"], {})
            for table_name in migration.NEW_TABLES:
                self.assertEqual(
                    connection.exec_driver_sql(
                        f"SELECT COUNT(*) FROM {table_name}"
                    ).scalar_one(),
                    0,
                )

        inspector = inspect(self.engine)
        self.assertTrue(set(migration.NEW_TABLES) <= set(inspector.get_table_names()))

    def test_propósitos_y_motivos_cerrados(self):
        with self.engine.begin() as connection:
            migration.upgrade(connection)
        with self.assertRaises(IntegrityError), self.engine.begin() as connection:
            self._insert_token(connection, purpose="otro")
        with self.assertRaises(IntegrityError), self.engine.begin() as connection:
            self._insert_token(
                connection,
                invalidated_at=datetime.now(timezone.utc),
                invalidation_reason="otro",
            )

    def test_estado_terminal_y_expiracion_constraints(self):
        now = datetime.now(timezone.utc)
        with self.engine.begin() as connection:
            migration.upgrade(connection)
        with self.assertRaises(IntegrityError), self.engine.begin() as connection:
            self._insert_token(connection, created_at=now, expires_at=now)
        with self.assertRaises(IntegrityError), self.engine.begin() as connection:
            self._insert_token(
                connection,
                consumed_at=now,
                invalidated_at=now,
                invalidation_reason="superseded",
            )
        with self.assertRaises(IntegrityError), self.engine.begin() as connection:
            self._insert_token(
                connection,
                invalidation_reason="superseded",
            )

    def test_digest_e_issuance_id_son_unicos(self):
        with self.engine.begin() as connection:
            migration.upgrade(connection)
            self._insert_token(connection)
        with self.assertRaises(IntegrityError), self.engine.begin() as connection:
            self._insert_token(connection, issuance_id="issuance-2")
        with self.assertRaises(IntegrityError), self.engine.begin() as connection:
            self._insert_token(connection, token_digest="b" * 64)

    def test_rate_limit_action_count_y_unicidad(self):
        now = datetime.now(timezone.utc)
        with self.engine.begin() as connection:
            migration.upgrade(connection)
            connection.exec_driver_sql(
                "INSERT INTO account_action_rate_limits "
                "(action, subject_digest, window_started_at) "
                "VALUES ('password_reset', :digest, :now)",
                {"digest": "c" * 64, "now": now},
            )
            row = connection.exec_driver_sql(
                "SELECT attempt_count, blocked_until "
                "FROM account_action_rate_limits"
            ).one()
            self.assertEqual(tuple(row), (0, None))
        with self.assertRaises(IntegrityError), self.engine.begin() as connection:
            connection.exec_driver_sql(
                "INSERT INTO account_action_rate_limits "
                "(action, subject_digest, window_started_at) "
                "VALUES ('password_reset', :digest, :now)",
                {"digest": "c" * 64, "now": now},
            )
        with self.assertRaises(IntegrityError), self.engine.begin() as connection:
            connection.exec_driver_sql(
                "INSERT INTO account_action_rate_limits "
                "(action, subject_digest, window_started_at, attempt_count) "
                "VALUES ('otro', :digest, :now, 0)",
                {"digest": "d" * 64, "now": now},
            )
        with self.assertRaises(IntegrityError), self.engine.begin() as connection:
            connection.exec_driver_sql(
                "INSERT INTO account_action_rate_limits "
                "(action, subject_digest, window_started_at, attempt_count) "
                "VALUES ('current_password', :digest, :now, -1)",
                {"digest": "e" * 64, "now": now},
            )

    def test_schema_parcial_incompatible_bloquea(self):
        with self.engine.begin() as connection:
            connection.exec_driver_sql(
                "CREATE TABLE account_action_tokens (id INTEGER PRIMARY KEY)"
            )
            with self.assertRaises(migration.AccountActionMigrationPreflightError):
                migration.upgrade(connection)


if __name__ == "__main__":
    unittest.main()
