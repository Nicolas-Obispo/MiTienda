import io
import json
import os
import unittest
from contextlib import redirect_stdout
from unittest.mock import patch

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.exc import SQLAlchemyError

import repair_email_canonical as repair
from app.core.model_registry import import_all_models
from app.modules.users.models.identity_models import PasswordCredential
from app.modules.users.models.usuarios_models import Usuario


import_all_models()


class EmailCanonicalRepairTests(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine("sqlite://")
        Usuario.__table__.create(self.engine)
        PasswordCredential.__table__.create(self.engine)

    def tearDown(self):
        self.engine.dispose()

    def add_user(
        self,
        user_id: int,
        email: str | None,
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

    def add_credential(self, user_id: int, password_hash: str) -> None:
        with self.engine.begin() as connection:
            connection.execute(
                text(
                    "INSERT INTO password_credentials "
                    "(usuario_id, password_hash, hash_version) "
                    "VALUES (:usuario_id, :password_hash, 'bcrypt')"
                ),
                {"usuario_id": user_id, "password_hash": password_hash},
            )

    def user_rows(self):
        with self.engine.connect() as connection:
            return connection.execute(
                text(
                    "SELECT id, email, email_canonical, hashed_password "
                    "FROM usuarios ORDER BY id"
                )
            ).all()

    def credential_rows(self):
        with self.engine.connect() as connection:
            return connection.execute(
                text(
                    "SELECT usuario_id, password_hash, hash_version "
                    "FROM password_credentials ORDER BY usuario_id"
                )
            ).all()

    def preflight(self):
        with self.engine.connect() as connection:
            return repair.preflight_email_canonical_repair(connection)

    def apply(self):
        return repair._apply_transaction(self.engine)

    def test_zero_pending_is_successful_noop(self):
        self.add_user(1, "person@example.com", canonical="person@example.com")

        result = self.apply()

        self.assertEqual(result.status, "PASS")
        self.assertEqual(result.updated, 0)
        self.assertEqual(result.after["pending"], 0)

    def test_one_valid_pending_is_canonicalized(self):
        self.add_user(1, " Person@Example.COM ")

        result = self.apply()

        self.assertEqual(result.updated, 1)
        self.assertEqual(
            self.user_rows()[0].email_canonical,
            "person@example.com",
        )

    def test_multiple_valid_pending_are_canonicalized(self):
        self.add_user(1, "One@Example.COM")
        self.add_user(2, "Two@Example.COM")

        result = self.apply()

        self.assertEqual(result.updated, 2)
        self.assertEqual(
            [row.email_canonical for row in self.user_rows()],
            ["one@example.com", "two@example.com"],
        )

    def test_second_execution_is_idempotent(self):
        self.add_user(1, "Person@Example.COM")

        first = self.apply()
        second = self.apply()

        self.assertEqual(first.updated, 1)
        self.assertEqual(second.updated, 0)

    def test_invalid_source_blocks_all_updates(self):
        self.add_user(1, "valid@example.com")
        self.add_user(2, "not-an-email")

        plan = self.preflight()
        with self.assertRaisesRegex(
            repair.CanonicalEmailRepairError,
            "canonical_repair_preflight_blocked",
        ):
            self.apply()

        self.assertEqual(plan.status, "BLOCK")
        self.assertEqual(plan.invalid_source, 1)
        self.assertEqual(
            [row.email_canonical for row in self.user_rows()],
            [None, None],
        )

    def test_missing_source_blocks(self):
        nullable_engine = create_engine("sqlite://")
        try:
            with nullable_engine.begin() as connection:
                connection.exec_driver_sql(
                    "CREATE TABLE usuarios ("
                    "id INTEGER PRIMARY KEY, "
                    "email VARCHAR(255) NULL, "
                    "email_canonical VARCHAR(255) NULL, "
                    "CONSTRAINT ux_usuarios_email_canonical "
                    "UNIQUE (email_canonical))"
                )
                connection.exec_driver_sql(
                    "INSERT INTO usuarios (id, email, email_canonical) "
                    "VALUES (1, NULL, NULL)"
                )
            with nullable_engine.connect() as connection:
                plan = repair.preflight_email_canonical_repair(connection)
            self.assertEqual(plan.status, "BLOCK")
            self.assertEqual(plan.invalid_source, 1)
        finally:
            nullable_engine.dispose()

    def test_canonical_collision_blocks_all_updates(self):
        self.add_user(1, "Person@Example.COM")
        self.add_user(2, "person@example.com")

        plan = self.preflight()
        with self.assertRaisesRegex(
            repair.CanonicalEmailRepairError,
            "canonical_repair_preflight_blocked",
        ):
            self.apply()

        self.assertEqual(plan.status, "BLOCK")
        self.assertEqual(plan.collision_groups, 1)
        self.assertEqual(plan.collision_rows, 2)
        self.assertEqual(
            [row.email_canonical for row in self.user_rows()],
            [None, None],
        )

    def test_persisted_divergent_canonical_blocks(self):
        self.add_user(1, "person@example.com", canonical="other@example.com")

        plan = self.preflight()

        self.assertEqual(plan.status, "BLOCK")
        self.assertEqual(plan.persisted_divergent, 1)
        with self.assertRaisesRegex(
            repair.CanonicalEmailRepairError,
            "canonical_repair_preflight_blocked",
        ):
            self.apply()

    def test_update_failure_rolls_back_every_pending_row(self):
        self.add_user(1, "one@example.com")
        self.add_user(2, "two@example.com")
        with self.engine.begin() as connection:
            connection.exec_driver_sql(
                "CREATE TRIGGER fail_second_canonical_update "
                "BEFORE UPDATE OF email_canonical ON usuarios "
                "WHEN NEW.id = 2 BEGIN "
                "SELECT RAISE(ABORT, 'forced update failure'); END"
            )

        with self.assertRaises(SQLAlchemyError):
            self.apply()

        self.assertEqual(
            [row.email_canonical for row in self.user_rows()],
            [None, None],
        )

    def test_email_and_legacy_hash_are_preserved(self):
        legacy_hash = "$2b$12$legacy-hash-value"
        self.add_user(
            1,
            " Person@Example.COM ",
            legacy_hash=legacy_hash,
        )

        before = self.user_rows()
        self.apply()
        after = self.user_rows()

        self.assertEqual(after[0].email, before[0].email)
        self.assertEqual(after[0].hashed_password, before[0].hashed_password)

    def test_does_not_create_password_credential(self):
        self.add_user(1, "person@example.com", legacy_hash="$2b$12$legacy")

        self.apply()

        self.assertEqual(self.credential_rows(), [])

    def test_existing_password_credential_is_unchanged(self):
        self.add_user(1, "person@example.com", legacy_hash="$2b$12$legacy")
        self.add_credential(1, "$2b$12$credential")
        before = self.credential_rows()

        self.apply()

        self.assertEqual(self.credential_rows(), before)

    def test_safe_report_does_not_expose_pii_or_internal_plan(self):
        raw_email = "Sensitive.Person@Example.COM"
        self.add_user(77, raw_email, legacy_hash="$2b$12$sensitive-hash")

        plan = self.preflight()
        output = json.dumps(plan.safe_summary())

        self.assertNotIn(raw_email, output)
        self.assertNotIn("sensitive.person@example.com", output)
        self.assertNotIn("77", output)
        self.assertNotIn("sensitive-hash", output)
        self.assertNotIn("updates", output)

    def test_apply_rejects_incorrect_target_before_transaction(self):
        with patch.object(repair, "_apply_transaction") as transaction:
            with self.assertRaisesRegex(
                repair.CanonicalEmailRepairError,
                "canonical_repair_target_invalid",
            ):
                repair.apply_repair(repair.APPLY_ACTION, target_engine=self.engine)

        transaction.assert_not_called()

    def test_launcher_default_is_read_only_and_sanitized(self):
        raw_email = "Person@Example.COM"
        self.add_user(1, raw_email)
        output = io.StringIO()
        with (
            patch.dict(os.environ, {}, clear=True),
            patch.object(repair, "engine", self.engine),
            redirect_stdout(output),
        ):
            exit_code = repair.main()

        payload = json.loads(output.getvalue())
        self.assertEqual(exit_code, 0)
        self.assertEqual(payload["mode"], "read_only")
        self.assertEqual(payload["report"]["pending"], 1)
        self.assertIsNone(self.user_rows()[0].email_canonical)
        self.assertNotIn(raw_email, output.getvalue())
        self.assertNotIn("person@example.com", output.getvalue())

    def test_unique_canonical_contract_is_required(self):
        unsafe_engine = create_engine("sqlite://")
        try:
            with unsafe_engine.begin() as connection:
                connection.exec_driver_sql(
                    "CREATE TABLE usuarios ("
                    "id INTEGER PRIMARY KEY, "
                    "email VARCHAR(255) NOT NULL, "
                    "email_canonical VARCHAR(255) NULL)"
                )
            with unsafe_engine.connect() as connection:
                with self.assertRaisesRegex(
                    repair.CanonicalEmailRepairError,
                    "canonical_repair_unique_constraint_missing",
                ):
                    repair.preflight_email_canonical_repair(connection)
        finally:
            unsafe_engine.dispose()

    def test_repair_does_not_create_or_remove_tables(self):
        self.add_user(1, "person@example.com")
        with self.engine.connect() as connection:
            tables_before = set(inspect(connection).get_table_names())

        self.apply()

        with self.engine.connect() as connection:
            tables_after = set(inspect(connection).get_table_names())
        self.assertEqual(tables_after, tables_before)


if __name__ == "__main__":
    unittest.main()
