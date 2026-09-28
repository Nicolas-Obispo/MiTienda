import os
import unittest

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

import repair_email_canonical as repair
from app.core.database import Base
from app.core.model_registry import import_all_models
from tests.mysql_stage97_test_support import isolated_mysql_test_engine


import_all_models()


@unittest.skipUnless(
    os.environ.get("FEEDGO_STAGE97_TEST_DATABASE_URL"),
    "requiere FEEDGO_STAGE97_TEST_DATABASE_URL aislada",
)
class EmailCanonicalRepairMySQLTests(unittest.TestCase):
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

    def add_user(
        self,
        user_id: int,
        email: str,
        *,
        canonical: str | None = None,
        legacy_hash: str | None = None,
    ) -> None:
        with self.engine.begin() as connection:
            connection.execute(
                text(
                    "INSERT INTO usuarios "
                    "(id, email, email_canonical, hashed_password, "
                    "modo_activo, onboarding_completo) "
                    "VALUES (:id, :email, :canonical, :legacy_hash, "
                    "'usuario', 0)"
                ),
                {
                    "id": user_id,
                    "email": email,
                    "canonical": canonical,
                    "legacy_hash": legacy_hash,
                },
            )

    def test_apply_is_idempotent_and_preserves_credentials(self):
        self.add_user(1, "One@Example.COM", legacy_hash="$2b$12$legacy-one")
        self.add_user(2, "Two@Example.COM", legacy_hash="$2b$12$legacy-two")
        with self.engine.begin() as connection:
            connection.execute(
                text(
                    "INSERT INTO password_credentials "
                    "(usuario_id, password_hash, hash_version) "
                    "VALUES (1, :password_hash, 'bcrypt')"
                ),
                {"password_hash": "$2b$12$credential-one"},
            )
            users_before = connection.execute(
                text(
                    "SELECT id, email, hashed_password FROM usuarios ORDER BY id"
                )
            ).all()
            credentials_before = connection.execute(
                text(
                    "SELECT usuario_id, password_hash, hash_version "
                    "FROM password_credentials ORDER BY usuario_id"
                )
            ).all()

        first = repair._apply_transaction(
            self.engine,
            expected_database="mitienda_stage97_test",
        )
        second = repair._apply_transaction(
            self.engine,
            expected_database="mitienda_stage97_test",
        )

        with self.engine.connect() as connection:
            canonical = connection.execute(
                text("SELECT email_canonical FROM usuarios ORDER BY id")
            ).scalars().all()
            users_after = connection.execute(
                text(
                    "SELECT id, email, hashed_password FROM usuarios ORDER BY id"
                )
            ).all()
            credentials_after = connection.execute(
                text(
                    "SELECT usuario_id, password_hash, hash_version "
                    "FROM password_credentials ORDER BY usuario_id"
                )
            ).all()

        self.assertEqual(first.updated, 2)
        self.assertEqual(second.updated, 0)
        self.assertEqual(canonical, ["one@example.com", "two@example.com"])
        self.assertEqual(users_after, users_before)
        self.assertEqual(credentials_after, credentials_before)

    def test_update_failure_rolls_back_complete_transaction(self):
        self.add_user(1, "one@example.com")
        self.add_user(2, "two@example.com")
        with self.engine.begin() as connection:
            connection.exec_driver_sql(
                "CREATE TRIGGER fail_second_canonical_update "
                "BEFORE UPDATE ON usuarios FOR EACH ROW "
                "BEGIN IF NEW.id = 2 THEN "
                "SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'forced failure'; "
                "END IF; END"
            )

        with self.assertRaises(SQLAlchemyError):
            repair._apply_transaction(
                self.engine,
                expected_database="mitienda_stage97_test",
            )

        with self.engine.connect() as connection:
            canonical = connection.execute(
                text("SELECT email_canonical FROM usuarios ORDER BY id")
            ).scalars().all()
        self.assertEqual(canonical, [None, None])


if __name__ == "__main__":
    unittest.main()
