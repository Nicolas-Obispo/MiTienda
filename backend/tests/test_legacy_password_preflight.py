import ast
import io
import json
import os
import subprocess
import sys
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import Mock, patch

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.database import Base
from app.core.model_registry import import_all_models
from app.core.security import hash_password
from app.modules.users.models.identity_models import PasswordCredential
from app.modules.users.models.usuarios_models import Usuario
from app.modules.users.services.legacy_password_preflight_services import (
    PREFLIGHT_BLOCK,
    PREFLIGHT_PASS,
    LegacyPasswordPreflightBlocked,
    LegacyPasswordPreflightReport,
    preflight_legacy_password_credentials,
    require_legacy_password_preflight_pass,
)


import_all_models()

import preflight_legacy_password_credentials as preflight_launcher


BACKEND_ROOT = Path(__file__).resolve().parents[1]


class LegacyPasswordPreflightTests(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine("sqlite://")
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)

    def tearDown(self):
        Base.metadata.drop_all(self.engine)
        self.engine.dispose()

    def add_user(
        self,
        user_id: int,
        *,
        legacy_hash: str | None = None,
        credential_hash: str | None = None,
        hash_version: str = "bcrypt",
        canonical: str | None = None,
    ) -> None:
        db = self.Session()
        db.add(
            Usuario(
                id=user_id,
                email=f"person-{user_id}@example.com",
                email_canonical=canonical or f"person-{user_id}@example.com",
                hashed_password=legacy_hash,
            )
        )
        if credential_hash is not None:
            db.add(
                PasswordCredential(
                    usuario_id=user_id,
                    password_hash=credential_hash,
                    hash_version=hash_version,
                )
            )
        db.commit()
        db.close()

    def report(self):
        db = self.Session()
        try:
            return preflight_legacy_password_credentials(db)
        finally:
            db.close()

    def test_without_password_is_allowed(self):
        self.add_user(1)
        report = self.report()
        self.assertEqual(report.status, PREFLIGHT_PASS)
        self.assertEqual(report.without_password, 1)
        self.assertEqual(report.total_password_accounts, 0)

    def test_credential_only_is_allowed(self):
        credential_hash = hash_password("Password1")
        self.add_user(1, credential_hash=credential_hash)
        report = self.report()
        self.assertEqual(report.status, PREFLIGHT_PASS)
        self.assertEqual(report.credential_only, 1)

    def test_dual_equivalent_is_allowed(self):
        password_hash = hash_password("Password1")
        self.add_user(1, legacy_hash=password_hash, credential_hash=password_hash)
        report = self.report()
        self.assertEqual(report.status, PREFLIGHT_PASS)
        self.assertEqual(report.dual_equivalent, 1)

    def test_legacy_only_is_candidate_not_blocker(self):
        self.add_user(1, legacy_hash=hash_password("Password1"))
        report = self.report()
        self.assertEqual(report.status, PREFLIGHT_PASS)
        self.assertEqual(report.legacy_only, 1)

    def test_dual_divergence_blocks_without_exposing_hashes(self):
        legacy_hash = hash_password("Password1")
        credential_hash = hash_password("Different2")
        self.add_user(1, legacy_hash=legacy_hash, credential_hash=credential_hash)
        report = self.report()
        self.assertEqual(report.status, PREFLIGHT_BLOCK)
        self.assertEqual(report.divergent, 1)
        self.assertIn("credential_hash_divergence", report.blockers)
        safe_output = json.dumps(report.safe_summary())
        self.assertNotIn(legacy_hash, safe_output)
        self.assertNotIn(credential_hash, safe_output)

    def test_invalid_hash_blocks(self):
        self.add_user(1, legacy_hash="not-a-bcrypt-hash")
        report = self.report()
        self.assertEqual(report.status, PREFLIGHT_BLOCK)
        self.assertEqual(report.invalid, 1)
        self.assertIn("invalid_password_credential_state", report.blockers)

    def test_mixed_population_has_complete_aggregated_classification(self):
        equivalent = hash_password("Password1")
        self.add_user(1)
        self.add_user(2, credential_hash=hash_password("Password1"))
        self.add_user(3, legacy_hash=equivalent, credential_hash=equivalent)
        self.add_user(4, legacy_hash=hash_password("Password1"))
        self.add_user(
            5,
            legacy_hash=hash_password("Password1"),
            credential_hash=hash_password("Different2"),
        )
        report = self.report()
        self.assertEqual(report.total_users, 5)
        self.assertEqual(report.total_password_accounts, 4)
        self.assertTrue(report.classification_complete)
        self.assertEqual(report.without_password, 1)
        self.assertEqual(report.credential_only, 1)
        self.assertEqual(report.dual_equivalent, 1)
        self.assertEqual(report.legacy_only, 1)
        self.assertEqual(report.divergent, 1)

    def test_missing_canonical_blocks_future_transition(self):
        self.add_user(1, legacy_hash=hash_password("Password1"), canonical="")
        db = self.Session()
        db.get(Usuario, 1).email_canonical = None
        db.commit()
        db.close()
        report = self.report()
        self.assertEqual(report.status, PREFLIGHT_BLOCK)
        self.assertEqual(report.missing_email_canonical, 1)
        self.assertEqual(report.legacy_only_missing_email_canonical, 1)
        self.assertEqual(report.legacy_only_with_email_canonical, 0)
        self.assertIn("email_canonical_incomplete", report.blockers)

    def test_missing_canonical_is_partitioned_by_credential_state(self):
        equivalent = hash_password("Password1")
        self.add_user(1, legacy_hash=hash_password("Password1"))
        self.add_user(2, legacy_hash=equivalent, credential_hash=equivalent)
        self.add_user(3, credential_hash=hash_password("Password1"))
        db = self.Session()
        db.get(Usuario, 2).email_canonical = None
        db.get(Usuario, 3).email_canonical = None
        db.commit()
        db.close()

        report = self.report()

        self.assertEqual(report.status, PREFLIGHT_BLOCK)
        self.assertEqual(report.missing_email_canonical, 2)
        self.assertEqual(report.legacy_only, 1)
        self.assertEqual(report.legacy_only_missing_email_canonical, 0)
        self.assertEqual(report.legacy_only_with_email_canonical, 1)
        self.assertEqual(report.dual_equivalent_missing_email_canonical, 1)
        self.assertEqual(report.credential_only_missing_email_canonical, 1)
        self.assertEqual(report.without_password_missing_email_canonical, 0)
        self.assertEqual(report.divergent_missing_email_canonical, 0)
        self.assertEqual(report.invalid_missing_email_canonical, 0)

    def test_read_failure_is_fail_closed(self):
        db = Mock()
        db.query.side_effect = RuntimeError("database unavailable")
        report = preflight_legacy_password_credentials(db)
        self.assertEqual(report.status, PREFLIGHT_BLOCK)
        self.assertFalse(report.classification_complete)
        self.assertEqual(report.blockers, ("preflight_read_error",))
        with self.assertRaises(LegacyPasswordPreflightBlocked):
            require_legacy_password_preflight_pass(report)


class LegacyPasswordPreflightLauncherTests(unittest.TestCase):
    def test_launcher_bootstraps_complete_mapper_graph_in_clean_process(self):
        probe = (
            "import preflight_legacy_password_credentials; "
            "from sqlalchemy.orm import configure_mappers; "
            "configure_mappers()"
        )
        result = subprocess.run(
            [sys.executable, "-B", "-c", probe],
            cwd=BACKEND_ROOT,
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )

        self.assertEqual(
            result.returncode,
            0,
            msg=f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}",
        )

    def test_launcher_requires_explicit_read_only_opt_in(self):
        with (
            patch.dict(os.environ, {}, clear=True),
            patch.object(preflight_launcher, "SessionLocal") as session_factory,
        ):
            with self.assertRaisesRegex(ValueError, "debe ser 'read_only'"):
                preflight_launcher.main()

        session_factory.assert_not_called()

    def test_launcher_executes_preflight_and_emits_only_safe_aggregates(self):
        session = Mock()
        report = LegacyPasswordPreflightReport(
            status=PREFLIGHT_PASS,
            total_users=4,
            total_password_accounts=3,
            without_password=1,
            credential_only=1,
            dual_equivalent=1,
            legacy_only=1,
            divergent=0,
            invalid=0,
            missing_email_canonical=0,
            classification_complete=True,
            blockers=(),
        )
        output = io.StringIO()
        with (
            patch.dict(
                os.environ,
                {preflight_launcher.ACTION_ENV: "read_only"},
                clear=True,
            ),
            patch.object(preflight_launcher, "SessionLocal", return_value=session),
            patch.object(
                preflight_launcher,
                "preflight_legacy_password_credentials",
                return_value=report,
            ) as preflight,
            patch.object(
                preflight_launcher,
                "safe_database_target",
                return_value="mysql://localhost/isolated_test",
            ),
            redirect_stdout(output),
        ):
            exit_code = preflight_launcher.main()

        payload = json.loads(output.getvalue())
        self.assertEqual(exit_code, 0)
        self.assertEqual(payload["report"], report.safe_summary())
        self.assertEqual(payload["target"], "mysql://localhost/isolated_test")
        preflight.assert_called_once_with(session)
        session.close.assert_called_once_with()
        serialized = output.getvalue().lower()
        for forbidden in (
            "password_hash",
            "hashed_password",
            "person@example.com",
            "@",
            "usuario_id",
            "database_url",
            "secret",
        ):
            self.assertNotIn(forbidden, serialized)

    def test_launcher_read_error_remains_fail_closed_and_sanitized(self):
        session = Mock()
        session.query.side_effect = RuntimeError("sensitive internal detail")
        output = io.StringIO()
        with (
            patch.dict(
                os.environ,
                {preflight_launcher.ACTION_ENV: "read_only"},
                clear=True,
            ),
            patch.object(preflight_launcher, "SessionLocal", return_value=session),
            patch.object(
                preflight_launcher,
                "safe_database_target",
                return_value="mysql://localhost/isolated_test",
            ),
            redirect_stdout(output),
        ):
            exit_code = preflight_launcher.main()

        payload = json.loads(output.getvalue())
        self.assertEqual(exit_code, 2)
        self.assertEqual(payload["report"]["status"], PREFLIGHT_BLOCK)
        self.assertEqual(payload["report"]["blockers"], ["preflight_read_error"])
        self.assertFalse(payload["report"]["classification_complete"])
        self.assertNotIn("sensitive internal detail", output.getvalue())
        session.close.assert_called_once_with()

    def test_l1_execution_path_contains_no_database_write_operations(self):
        forbidden_calls = {
            "add",
            "add_all",
            "bulk_insert_mappings",
            "bulk_save_objects",
            "bulk_update_mappings",
            "commit",
            "create_all",
            "delete",
            "drop_all",
            "execute",
            "exec_driver_sql",
            "flush",
            "merge",
        }
        observed: set[str] = set()
        for relative_path in (
            "preflight_legacy_password_credentials.py",
            "app/modules/users/services/legacy_password_preflight_services.py",
        ):
            source = (BACKEND_ROOT / relative_path).read_text(encoding="utf-8")
            tree = ast.parse(source)
            observed.update(
                node.func.attr
                for node in ast.walk(tree)
                if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
            )

        self.assertTrue(forbidden_calls.isdisjoint(observed))


if __name__ == "__main__":
    unittest.main()
