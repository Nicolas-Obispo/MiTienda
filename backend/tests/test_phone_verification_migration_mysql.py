import unittest

from sqlalchemy import inspect

from app.core.database import Base
from app.core.model_registry import import_all_models
from app.modules.users.models.identity_models import (
    AccountActionRateLimit,
    PhoneVerificationChallenge,
)
from app.modules.users.models.usuarios_models import Usuario
from migrate_phone_verification_challenges import upgrade
from tests.mysql_stage97_test_support import isolated_mysql_test_engine

import_all_models()


class PhoneVerificationMigrationMySQLTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.engine, _ = isolated_mysql_test_engine()

    @classmethod
    def tearDownClass(cls):
        cls.engine.dispose()

    def setUp(self):
        Base.metadata.drop_all(self.engine)
        Usuario.__table__.create(self.engine)
        AccountActionRateLimit.__table__.create(self.engine)

    def _upgrade(self):
        with self.engine.begin() as connection:
            return upgrade(connection)

    def _assert_complete(self):
        inspector = inspect(self.engine)
        self.assertEqual(
            {column["name"] for column in inspector.get_columns("phone_verification_challenges")},
            {column.name for column in PhoneVerificationChallenge.__table__.columns},
        )
        names = {index["name"] for index in inspector.get_indexes("phone_verification_challenges")}
        self.assertIn("ix_phone_verification_user_created", names)
        self.assertIn("ix_phone_verification_user_expiry", names)
        self.assertTrue(inspector.get_foreign_keys("phone_verification_challenges"))

    def test_clean_and_second_run(self):
        self.assertIn("phone_verification_challenges", self._upgrade()["changes"])
        self._assert_complete()
        self.assertEqual(self._upgrade()["changes"], [])

    def test_recovers_id_and_user_only(self):
        with self.engine.begin() as connection:
            connection.exec_driver_sql(
                "CREATE TABLE phone_verification_challenges ("
                "id VARCHAR(64) PRIMARY KEY, usuario_id INT NOT NULL)"
            )
        self.assertTrue(self._upgrade()["changes"])
        self._assert_complete()
        self.assertEqual(self._upgrade()["changes"], [])

    def test_recovers_some_columns(self):
        with self.engine.begin() as connection:
            connection.exec_driver_sql(
                "CREATE TABLE phone_verification_challenges ("
                "id VARCHAR(64) PRIMARY KEY, usuario_id INT NOT NULL, "
                "phone_e164_snapshot VARCHAR(16) NOT NULL, "
                "code_digest VARCHAR(64) NOT NULL)"
            )
        self.assertTrue(self._upgrade()["changes"])
        self._assert_complete()


if __name__ == "__main__":
    unittest.main()
