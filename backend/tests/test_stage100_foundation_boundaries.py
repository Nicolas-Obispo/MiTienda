"""Contratos focales de frontera aprobados al inicio de ET100.3."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
import zipfile

from sqlalchemy.engine import make_url

from synthetic_data.target_guard import (
    CredentialRole,
    EXPECTED_DATABASE,
    Stage100TargetGuardError,
    load_target_configuration,
    validate_control_grants,
    validate_control_target,
    validate_configured_target,
    validate_distinct_credentials,
    validate_grants,
    validate_live_connection,
)


ROOT = Path(__file__).resolve().parents[2]
TOOLS = ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

from feedgo_toolchain import (  # noqa: E402
    ToolchainError,
    install_uv_from_archive,
    resolve_uv,
)


class _Result:
    def __init__(self, *, scalar=None, rows=None):
        self._scalar = scalar
        self._rows = rows

    def scalar_one(self):
        return self._scalar

    def all(self):
        return self._rows


class _Connection:
    def __init__(self, username: str, grants: list[str], database: str = EXPECTED_DATABASE):
        self.username = username
        self.grants = grants
        self.database = database

    def exec_driver_sql(self, statement: str):
        if statement == "SELECT DATABASE()":
            return _Result(scalar=self.database)
        if statement == "SELECT CURRENT_USER()":
            return _Result(scalar=f"{self.username}@localhost")
        if statement == "SHOW GRANTS":
            return _Result(rows=[(grant,) for grant in self.grants])
        raise AssertionError(statement)


def _grants(username: str, privileges: str) -> list[str]:
    return [
        f"GRANT USAGE ON *.* TO `{username}`@`localhost`",
        f"GRANT {privileges} ON `{EXPECTED_DATABASE}`.* TO `{username}`@`localhost`",
    ]


class Stage100TargetGuardTests(unittest.TestCase):
    def test_approved_configuration_is_exact_and_uses_distinct_identities(self):
        environment = {
            "FEEDGO_STAGE100_MATERIALIZER_DATABASE_URL": (
                f"mysql+pymysql://stage100_materializer:secret@localhost/{EXPECTED_DATABASE}"
            ),
            "FEEDGO_STAGE100_RESET_DATABASE_URL": (
                f"mysql+pymysql://stage100_reset:secret@localhost/{EXPECTED_DATABASE}"
            ),
            "FEEDGO_STAGE100_MATERIALIZER_USER": "stage100_materializer",
            "FEEDGO_STAGE100_RESET_USER": "stage100_reset",
            "FEEDGO_STAGE100_CONTROL_DATABASE_URL": (
                "mysql+pymysql://stage100_control:secret@localhost/"
            ),
            "FEEDGO_STAGE100_CONTROL_USER": "stage100_control",
        }
        config = load_target_configuration(environment)
        self.assertEqual(config.materializer_url.database, EXPECTED_DATABASE)
        self.assertEqual(config.reset_url.database, EXPECTED_DATABASE)
        self.assertIn(config.control_url.database, (None, ""))

    def test_control_target_and_column_grants_are_exact(self):
        url = validate_control_target(
            "mysql+pymysql://stage100_control:secret@localhost/",
            expected_username="stage100_control",
        )
        self.assertIn(url.database, (None, ""))
        validate_control_grants(
            [
                "GRANT USAGE ON *.* TO `stage100_control`@`localhost`",
                "GRANT SELECT (`THREAD_ID`, `PROCESSLIST_ID`, `PROCESSLIST_COMMAND`) "
                "ON `performance_schema`.`threads` TO `stage100_control`@`localhost`",
                "GRANT SELECT (`OWNER_THREAD_ID`, `LOCK_STATUS`) ON "
                "`performance_schema`.`metadata_locks` TO "
                "`stage100_control`@`localhost`",
            ]
        )

    def test_control_rejects_table_wide_global_admin_and_application_grants(self):
        base = ["GRANT USAGE ON *.* TO `stage100_control`@`localhost`"]
        bad = (
            base + ["GRANT SELECT ON `performance_schema`.`threads` TO `stage100_control`@`localhost`"],
            base + ["GRANT PROCESS ON *.* TO `stage100_control`@`localhost`"],
            base + ["GRANT SELECT ON `mitienda`.* TO `stage100_control`@`localhost`"],
        )
        for grants in bad:
            with self.subTest(grants=grants), self.assertRaises(Stage100TargetGuardError):
                validate_control_grants(grants)

    def test_mitienda_arbitrary_test_remote_and_driver_are_rejected(self):
        invalid_urls = [
            "mysql+pymysql://user:secret@localhost/mitienda",
            "mysql+pymysql://user:secret@localhost/other_test",
            f"mysql+pymysql://user:secret@db.example.invalid/{EXPECTED_DATABASE}",
            f"sqlite:///{EXPECTED_DATABASE}",
            f"mysql+pymysql://user@localhost/{EXPECTED_DATABASE}",
            f"mysql+pymysql://user:secret@localhost/{EXPECTED_DATABASE}?init_command=SELECT+1",
        ]
        for raw_url in invalid_urls:
            with self.subTest(raw_url=raw_url):
                with self.assertRaises(Stage100TargetGuardError):
                    validate_configured_target(
                        raw_url,
                        role=CredentialRole.MATERIALIZER,
                        expected_username="user",
                    )

    def test_credentials_must_be_distinct(self):
        url = make_url(f"mysql+pymysql://same:secret@localhost/{EXPECTED_DATABASE}")
        with self.assertRaisesRegex(
            Stage100TargetGuardError, "stage100_credentials_must_be_distinct"
        ):
            validate_distinct_credentials(url, url)

    def test_materializer_grants_are_minimal_and_mitienda_is_inaccessible(self):
        validate_grants(
            _grants("materializer", "SELECT, INSERT, UPDATE, DELETE"),
            role=CredentialRole.MATERIALIZER,
        )
        forbidden = _grants("materializer", "SELECT, INSERT, UPDATE, DELETE") + [
            "GRANT SELECT ON `mitienda`.* TO `materializer`@`localhost`"
        ]
        with self.assertRaisesRegex(Stage100TargetGuardError, "stage100_grant_scope_invalid"):
            validate_grants(forbidden, role=CredentialRole.MATERIALIZER)

    def test_reset_grants_are_ddl_only_and_limited_to_isolated_database(self):
        validate_grants(
            _grants("resetter", "CREATE, DROP, ALTER, INDEX, REFERENCES"),
            role=CredentialRole.RESET,
        )
        excessive = _grants(
            "resetter", "CREATE, DROP, ALTER, INDEX, REFERENCES, SELECT"
        )
        with self.assertRaisesRegex(Stage100TargetGuardError, "stage100_grants_not_minimal"):
            validate_grants(excessive, role=CredentialRole.RESET)

    def test_global_privileges_grant_option_roles_and_wrong_database_are_rejected(self):
        bad_sets = [
            ["GRANT ALL PRIVILEGES ON *.* TO `user`@`localhost`"],
            ["GRANT SELECT ON *.* TO `user`@`localhost`"],
            _grants("user", "SELECT, INSERT, UPDATE, DELETE")[:-1]
            + [
                f"GRANT SELECT, INSERT, UPDATE, DELETE ON `{EXPECTED_DATABASE}`.* "
                "TO `user`@`localhost` WITH GRANT OPTION"
            ],
            ["GRANT `some_role`@`%` TO `user`@`localhost`"],
            _grants("user", "SELECT, INSERT, UPDATE, DELETE")
            + ["GRANT SELECT ON `other`.* TO `user`@`localhost`"],
        ]
        for grants in bad_sets:
            with self.subTest(grants=grants):
                with self.assertRaises(Stage100TargetGuardError):
                    validate_grants(grants, role=CredentialRole.MATERIALIZER)

    def test_live_connection_requires_selected_database_identity_and_grants(self):
        url = make_url(
            f"mysql+pymysql://materializer:secret@localhost/{EXPECTED_DATABASE}"
        )
        connection = _Connection(
            "materializer",
            _grants("materializer", "SELECT, INSERT, UPDATE, DELETE"),
        )
        result = validate_live_connection(
            connection,
            configured_url=url,
            role=CredentialRole.MATERIALIZER,
            expected_username="materializer",
        )
        self.assertEqual(result.database, EXPECTED_DATABASE)

        for bad_connection in (
            _Connection("materializer", connection.grants, database="mitienda"),
            _Connection("other", connection.grants),
        ):
            with self.assertRaises(Stage100TargetGuardError):
                validate_live_connection(
                    bad_connection,
                    configured_url=url,
                    role=CredentialRole.MATERIALIZER,
                    expected_username="materializer",
                )


class UvToolchainBoundaryTests(unittest.TestCase):
    def _write_manifest(self, root: Path, archive: Path, digest: str) -> Path:
        manifest = {
            "schema_version": 1,
            "tools": {
                "uv": {
                    "version": "0.12.19",
                    "artifacts": {
                        "windows-x86_64": {
                            "archive": archive.name,
                            "url": "https://github.com/astral-sh/uv/releases/download/0.12.19/"
                            + archive.name,
                            "sha256": digest,
                            "executable": "uv.exe",
                        }
                    },
                }
            },
        }
        path = root / "toolchain.json"
        path.write_text(json.dumps(manifest), encoding="utf-8")
        return path

    @unittest.skipUnless(sys.platform == "win32", "fixture focal Windows")
    def test_explicit_archive_install_and_verified_resolution(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            archive = root / "uv-test.zip"
            with zipfile.ZipFile(archive, "w") as bundle:
                bundle.writestr("uv-x86_64-pc-windows-msvc/uv.exe", b"synthetic-uv")
            digest = hashlib.sha256(archive.read_bytes()).hexdigest()
            manifest = self._write_manifest(root, archive, digest)
            cache = root / "cache"

            executable = install_uv_from_archive(
                archive, manifest_path=manifest, cache_root=cache
            )
            resolved = resolve_uv(
                manifest_path=manifest,
                cache_root=cache,
                environment={},
                version_reader=lambda _: "uv 0.12.19",
            )
            self.assertEqual(Path(resolved), executable.resolve())

    @unittest.skipUnless(sys.platform == "win32", "fixture focal Windows")
    def test_missing_receipt_bad_archive_checksum_and_binary_tamper_fail_closed(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            archive = root / "uv-test.zip"
            with zipfile.ZipFile(archive, "w") as bundle:
                bundle.writestr("bundle/uv.exe", b"synthetic-uv")
            digest = hashlib.sha256(archive.read_bytes()).hexdigest()
            manifest = self._write_manifest(root, archive, digest)
            cache = root / "cache"

            with self.assertRaisesRegex(ToolchainError, "uv_verified_installation_missing"):
                resolve_uv(
                    manifest_path=manifest,
                    cache_root=cache,
                    environment={},
                    version_reader=lambda _: "uv 0.12.19",
                )

            archive.write_bytes(archive.read_bytes() + b"tamper")
            with self.assertRaisesRegex(ToolchainError, "uv_archive_checksum_mismatch"):
                install_uv_from_archive(archive, manifest_path=manifest, cache_root=cache)

    @unittest.skipUnless(sys.platform == "win32", "fixture focal Windows")
    def test_override_still_requires_receipt_checksum_and_exact_version(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            archive = root / "uv-test.zip"
            with zipfile.ZipFile(archive, "w") as bundle:
                bundle.writestr("bundle/uv.exe", b"synthetic-uv")
            digest = hashlib.sha256(archive.read_bytes()).hexdigest()
            manifest = self._write_manifest(root, archive, digest)
            cache = root / "cache"
            executable = install_uv_from_archive(
                archive, manifest_path=manifest, cache_root=cache
            )

            with self.assertRaisesRegex(ToolchainError, "uv_version_mismatch"):
                resolve_uv(
                    manifest_path=manifest,
                    cache_root=root / "unused",
                    environment={"FEEDGO_UV_BIN": str(executable)},
                    version_reader=lambda _: "uv 9.9.9",
                )

            executable.write_bytes(b"tampered")
            with self.assertRaisesRegex(ToolchainError, "uv_executable_checksum_mismatch"):
                resolve_uv(
                    manifest_path=manifest,
                    cache_root=root / "unused",
                    environment={"FEEDGO_UV_BIN": str(executable)},
                    version_reader=lambda _: "uv 0.12.19",
                )

    @unittest.skipUnless(sys.platform == "win32", "fixture focal Windows")
    def test_official_uv_version_metadata_is_accepted_without_version_drift(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            archive = root / "uv-test.zip"
            with zipfile.ZipFile(archive, "w") as bundle:
                bundle.writestr("bundle/uv.exe", b"synthetic-uv")
            digest = hashlib.sha256(archive.read_bytes()).hexdigest()
            manifest = self._write_manifest(root, archive, digest)
            cache = root / "cache"
            install_uv_from_archive(archive, manifest_path=manifest, cache_root=cache)

            resolved = resolve_uv(
                manifest_path=manifest,
                cache_root=cache,
                environment={},
                version_reader=lambda _: (
                    "uv 0.12.19 (bea138450 2026-09-24 x86_64-pc-windows-msvc)"
                ),
            )
            self.assertTrue(Path(resolved).is_file())

    def test_production_manifest_pins_official_archives_and_sha256(self):
        manifest = json.loads((TOOLS / "toolchain.json").read_text(encoding="utf-8"))
        uv = manifest["tools"]["uv"]
        self.assertEqual(uv["version"], "0.12.19")
        self.assertEqual(
            uv["artifacts"]["windows-x86_64"]["sha256"],
            "6dbb02d79e419522f1c500f0adb1cddcff0cda7d59b0d66ea7f5e3b4a1b2f5f0",
        )
        self.assertEqual(
            uv["artifacts"]["linux-x86_64"]["sha256"],
            "23bf5552d220e0842b65c862097b2ebaeba0064b74eda5e565e77fd25969d8c8",
        )
        self.assertTrue(
            all(
                artifact["url"].startswith(
                    "https://github.com/astral-sh/uv/releases/download/0.12.19/"
                )
                for artifact in uv["artifacts"].values()
            )
        )
        node = manifest["tools"]["node"]
        self.assertEqual(node["version"], "24.21.0")
        self.assertEqual(node["npm_version"], "12.1.0")
        self.assertEqual(
            node["artifacts"]["windows-x86_64"]["sha256"],
            "158f7685b44de51f6c0df1d153526cbcd3e1bc739a8dfc607721cef75de9e541",
        )
        self.assertEqual(
            node["npm"]["integrity"],
            "sha512-Fyhu62pNx70YCs/5+dEmJQTFVmSKwvo5CA0qvBkGDRpob42MJ6G2RQ2tdxeKM4nYnIZDqkYAxEgqtoejn9QGtQ==",
        )

    def test_runner_does_not_fall_back_to_path_or_implement_network_downloads(self):
        runner = (TOOLS / "feedgo.py").read_text(encoding="utf-8")
        resolver = (TOOLS / "feedgo_toolchain.py").read_text(encoding="utf-8")
        self.assertNotIn('_binary("FEEDGO_UV_BIN", "uv")', runner)
        self.assertNotIn("urllib", resolver)
        self.assertNotIn("requests", resolver)
        self.assertNotIn("httpx", resolver)


if __name__ == "__main__":
    unittest.main()
