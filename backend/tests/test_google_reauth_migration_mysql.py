import os
import unittest

from sqlalchemy import inspect

import migrate_google_reauth as migration
from app.core.database import Base
from app.core.model_registry import import_all_models
from tests.mysql_stage97_test_support import isolated_mysql_test_engine


import_all_models()


@unittest.skipUnless(
    os.environ.get("FEEDGO_STAGE97_TEST_DATABASE_URL"),
    "requiere FEEDGO_STAGE97_TEST_DATABASE_URL aislada",
)
class GoogleReauthMigrationMySQLTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.engine, _ = isolated_mysql_test_engine()

    @classmethod
    def tearDownClass(cls):
        Base.metadata.drop_all(cls.engine)
        cls.engine.dispose()

    def setUp(self):
        Base.metadata.drop_all(self.engine)
        Base.metadata.create_all(self.engine)

    def test_upgrade_recovers_old_and_missing_checks_and_is_idempotent(self):
        with self.engine.begin() as connection:
            connection.exec_driver_sql(
                "ALTER TABLE oauth_authorization_transactions DROP CHECK "
                "ck_oauth_authorization_transactions_purpose"
            )
            connection.exec_driver_sql(
                "ALTER TABLE oauth_authorization_transactions ADD CONSTRAINT "
                "ck_oauth_authorization_transactions_purpose CHECK "
                "(purpose IN ('signup', 'login', 'link'))"
            )
            # Simula una ejecucion interrumpida despues del DROP del segundo check.
            connection.exec_driver_sql(
                "ALTER TABLE oauth_authorization_transactions DROP CHECK "
                "ck_oauth_authorization_transactions_correlation"
            )
            first = migration.upgrade(connection)
            checks = {
                item.get("name"): item.get("sqltext", "")
                for item in inspect(connection).get_check_constraints(
                    "oauth_authorization_transactions"
                )
            }
            self.assertIn(
                "reauth", checks["ck_oauth_authorization_transactions_purpose"]
            )
            self.assertIn(
                "reauth", checks["ck_oauth_authorization_transactions_correlation"]
            )
            self.assertEqual(len(first["changes"]), 2)
            self.assertEqual(migration.upgrade(connection), {"changes": []})


if __name__ == "__main__":
    unittest.main()
