import os
import unittest

from sqlalchemy import inspect

from app.modules.users.models.identity_models import AccountActionRateLimit
import migrate_password_login_rate_limit as migration
from tests.mysql_stage97_test_support import isolated_mysql_test_engine


@unittest.skipUnless(
    os.environ.get("FEEDGO_STAGE97_TEST_DATABASE_URL"),
    "requiere FEEDGO_STAGE97_TEST_DATABASE_URL aislada",
)
class PasswordLoginRateLimitMigrationMySQLTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.engine, _ = isolated_mysql_test_engine()

    @classmethod
    def tearDownClass(cls):
        AccountActionRateLimit.__table__.drop(cls.engine, checkfirst=True)
        cls.engine.dispose()

    def setUp(self):
        AccountActionRateLimit.__table__.drop(self.engine, checkfirst=True)
        AccountActionRateLimit.__table__.create(self.engine)

    def _replace_check(self, actions):
        quoted = ",".join(f"'{action}'" for action in actions)
        with self.engine.begin() as connection:
            connection.exec_driver_sql(
                "ALTER TABLE account_action_rate_limits "
                "DROP CHECK ck_account_action_rate_limits_action, "
                "ADD CONSTRAINT ck_account_action_rate_limits_action "
                f"CHECK (action IN ({quoted}))"
            )

    def _drop_cleanup_index(self):
        with self.engine.begin() as connection:
            connection.exec_driver_sql(
                "DROP INDEX ix_account_action_rate_limits_action_updated "
                "ON account_action_rate_limits"
            )

    def test_migra_schema_preupgrade_y_preserva_filas(self):
        self._replace_check(sorted(migration.PHONE_ACTIONS))
        self._drop_cleanup_index()
        with self.engine.begin() as connection:
            tables_before = set(inspect(connection).get_table_names())
            connection.exec_driver_sql(
                "INSERT INTO account_action_rate_limits "
                "(action, subject_digest, window_started_at, attempt_count, updated_at) "
                "VALUES ('password_reset', %s, NOW(), 3, NOW())",
                ("a" * 64,),
            )
            result = migration.upgrade(connection)
            row = connection.exec_driver_sql(
                "SELECT action, subject_digest, attempt_count "
                "FROM account_action_rate_limits"
            ).one()
            tables_after = set(inspect(connection).get_table_names())
        self.assertEqual(
            row,
            ("password_reset", "a" * 64, 3),
        )
        self.assertIn(migration.CHECK_NAME, result["changes"])
        self.assertIn(migration.INDEX_NAME, result["changes"])
        self.assertEqual(tables_after, tables_before)
        self.assertNotIn("oauth_authorization_transactions", tables_after)
        self.assertNotIn("oauth_session_delivery_handles", tables_after)

    def test_metadata_actual_e_idempotencia(self):
        with self.engine.begin() as connection:
            first = migration.upgrade(connection)
            second = migration.upgrade(connection)
        self.assertEqual(first["changes"], [])
        self.assertEqual(second["changes"], [])

    def test_estado_parcial_sin_check_es_recuperable(self):
        with self.engine.begin() as connection:
            connection.exec_driver_sql(
                "ALTER TABLE account_action_rate_limits "
                "DROP CHECK ck_account_action_rate_limits_action"
            )
            result = migration.upgrade(connection)
        self.assertIn(migration.CHECK_NAME, result["changes"])

    def test_constraint_inesperado_aborta(self):
        self._replace_check(sorted(migration.GOOGLE_ACTIONS | {"unexpected"}))
        with self.engine.begin() as connection:
            with self.assertRaisesRegex(
                migration.PasswordLoginRateLimitMigrationError,
                "check_unexpected",
            ):
                migration.upgrade(connection)

    def test_indice_cleanup_y_rollback_de_app_compatible(self):
        self._drop_cleanup_index()
        with self.engine.begin() as connection:
            migration.upgrade(connection)
            indexes = {
                tuple(item.get("column_names") or ())
                for item in inspect(connection).get_indexes(
                    "account_action_rate_limits"
                )
            }
            connection.exec_driver_sql(
                "INSERT INTO account_action_rate_limits "
                "(action, subject_digest, window_started_at, attempt_count, updated_at) "
                "VALUES ('current_password', %s, NOW(), 1, NOW())",
                ("b" * 64,),
            )
        self.assertIn(("action", "updated_at"), indexes)


if __name__ == "__main__":
    unittest.main()
