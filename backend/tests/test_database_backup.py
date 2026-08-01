import gzip
import io
import json
import os
import tempfile
import time
import unittest
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from app.core import database_backup


def _fake_engine():
    return SimpleNamespace(
        dialect=SimpleNamespace(name="mysql"),
        url=SimpleNamespace(host="localhost", database="mitienda"),
    )


class _SuccessfulDumpProcess:
    def __init__(self, command, stdout, stderr, shell):
        self.command = command
        self.stdout_arg = stdout
        self.stdout = io.BytesIO(b"-- dump sql\nCREATE TABLE usuarios (id int);\n")
        self.stderr = stderr
        self.shell = shell

    def wait(self):
        return 0


class _FailedDumpProcess:
    def __init__(self, command, stdout, stderr, shell):
        self.command = command
        self.stdout_arg = stdout
        self.stdout = io.BytesIO(b"partial sql\n")
        self.stderr = stderr
        self.shell = shell

    def wait(self):
        self.stderr.write(b"access denied")
        return 1


class CapturingPopenFactory:
    def __init__(self, process_class=_SuccessfulDumpProcess):
        self.process_class = process_class
        self.calls = []

    def __call__(self, command, stdout, stderr, shell):
        process = self.process_class(command, stdout, stderr, shell)
        self.calls.append(process)
        return process


class DatabaseBackupTests(unittest.TestCase):
    def _config(self, tmpdir: str) -> database_backup.BackupConfig:
        defaults_file = Path(tmpdir) / "mysql.cnf"
        defaults_file.write_text("[client]\nuser=test\npassword=secret\n", encoding="utf-8")
        return database_backup.BackupConfig(
            output_dir=Path(tmpdir) / "backups",
            defaults_extra_file=defaults_file,
            retention_days=14,
            keep_last=10,
        )

    def test_build_mysqldump_command_no_incluye_password_y_usa_single_transaction(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            config = self._config(tmpdir)
            with patch.object(database_backup, "engine", _fake_engine()):
                command = database_backup._build_mysqldump_command(config)

        self.assertEqual(command[0], "mysqldump")
        self.assertIn("--single-transaction", command)
        self.assertIn("--quick", command)
        self.assertIn("--routines", command)
        self.assertIn("--events", command)
        self.assertNotIn("--databases", command)
        self.assertIn("mitienda", command)
        self.assertFalse(any("secret" in item for item in command))

    def test_run_backup_crea_gzip_manifest_hash_y_metricas(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            config = self._config(tmpdir)
            popen_factory = CapturingPopenFactory()
            fixed_now = datetime(2026, 8, 1, 12, 0, 0, tzinfo=timezone.utc)

            with patch.object(database_backup, "engine", _fake_engine()):
                manifest = database_backup.run_backup(
                    config,
                    now=fixed_now,
                    popen_factory=popen_factory,
                    counts_provider=lambda: {"usuarios": 1},
                    engine_version_provider=lambda: "8.0-test",
                )

            backup_path = Path(manifest.backup_file)
            manifest_path = backup_path.with_suffix(backup_path.suffix + ".json")

            self.assertTrue(backup_path.exists())
            self.assertTrue(manifest_path.exists())
            self.assertGreater(manifest.size_bytes, 0)
            self.assertEqual(manifest.sha256, database_backup._sha256_file(backup_path))
            self.assertEqual(manifest.database, "mitienda")
            self.assertEqual(manifest.host, "localhost")
            self.assertEqual(manifest.format_version, 1)
            self.assertEqual(manifest.provider, "mysqldump")
            self.assertEqual(manifest.storage_provider, "local")
            self.assertEqual(manifest.database_engine, "mysql")
            self.assertEqual(manifest.engine_version, "8.0-test")
            self.assertEqual(manifest.backup_type, "logical_full")
            self.assertEqual(manifest.checksum_algorithm, "sha256")
            self.assertEqual(manifest.checksum, manifest.sha256)
            self.assertTrue(manifest.single_transaction)
            self.assertFalse(manifest.database_statements)
            self.assertTrue(manifest.restore_target_required)
            self.assertEqual(
                manifest.restore_requirements["target_database_pattern"],
                "feedgo_restore_tmp_<nombre>",
            )
            self.assertIsNone(manifest.binlog_coordinates)
            self.assertEqual(manifest.critical_table_counts, {"usuarios": 1})
            self.assertEqual(manifest.external_copy, "prepared_not_implemented")
            self.assertEqual(manifest.result, "ok")
            self.assertEqual(len(popen_factory.calls), 1)
            self.assertFalse(popen_factory.calls[0].shell)
            self.assertEqual(popen_factory.calls[0].stdout_arg, database_backup.subprocess.PIPE)

            with gzip.open(backup_path, "rb") as backup_file:
                self.assertIn(b"CREATE TABLE usuarios", backup_file.read())

            metadata = json.loads(manifest_path.read_text(encoding="utf-8"))
            self.assertEqual(metadata["format_version"], 1)
            self.assertEqual(metadata["provider"], "mysqldump")
            self.assertEqual(metadata["storage_provider"], "local")
            self.assertEqual(metadata["sha256"], manifest.sha256)
            self.assertEqual(metadata["checksum"], manifest.sha256)
            self.assertFalse(metadata["database_statements"])
            self.assertTrue(metadata["restore_target_required"])
            self.assertEqual(metadata["critical_table_counts"], {"usuarios": 1})

    def test_run_backup_fallido_elimina_archivo_parcial(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            config = self._config(tmpdir)
            popen_factory = CapturingPopenFactory(_FailedDumpProcess)
            fixed_now = datetime(2026, 8, 1, 12, 0, 0, tzinfo=timezone.utc)

            with patch.object(database_backup, "engine", _fake_engine()):
                with self.assertRaises(database_backup.BackupExecutionError):
                    database_backup.run_backup(
                        config,
                        now=fixed_now,
                        popen_factory=popen_factory,
                        counts_provider=lambda: {"usuarios": 1},
                        engine_version_provider=lambda: "8.0-test",
                    )

            self.assertEqual(list((Path(tmpdir) / "backups").glob("*.sql.gz")), [])

    def test_provider_escribe_gzip_desde_stdout_pipe_realista(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            config = self._config(tmpdir)
            provider = database_backup.MySQLDumpBackupProvider()
            backup_path = Path(tmpdir) / "backup.sql.gz"
            popen_factory = CapturingPopenFactory()

            with patch.object(database_backup, "engine", _fake_engine()):
                provider.create_backup(config, backup_path, popen_factory)

            self.assertTrue(backup_path.exists())
            self.assertEqual(popen_factory.calls[0].stdout_arg, database_backup.subprocess.PIPE)
            with gzip.open(backup_path, "rb") as backup_file:
                self.assertIn(b"CREATE TABLE usuarios", backup_file.read())

    def test_config_from_env_requiere_defaults_file(self):
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(database_backup.BackupConfigurationError):
                database_backup.config_from_env()

    def test_config_from_env_usa_variables_sin_secretos(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            defaults_file = Path(tmpdir) / "mysql.cnf"
            defaults_file.write_text("[client]\nuser=test\n", encoding="utf-8")
            output_dir = Path(tmpdir) / "out"

            with patch.dict(
                os.environ,
                {
                    "FEEDGO_MYSQL_DEFAULTS_FILE": str(defaults_file),
                    "FEEDGO_BACKUP_DIR": str(output_dir),
                    "FEEDGO_BACKUP_RETENTION_DAYS": "7",
                    "FEEDGO_BACKUP_KEEP_LAST": "3",
                    "FEEDGO_MYSQLDUMP_BIN": "mysqldump-test",
                },
                clear=True,
            ):
                config = database_backup.config_from_env()

        self.assertEqual(config.output_dir, output_dir)
        self.assertEqual(config.defaults_extra_file, defaults_file)
        self.assertEqual(config.retention_days, 7)
        self.assertEqual(config.keep_last, 3)
        self.assertEqual(config.mysqldump_bin, "mysqldump-test")

    def test_rotate_backups_respeta_keep_last(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            files = []
            for index in range(4):
                backup = output_dir / f"backup_{index}.sql.gz"
                backup.write_bytes(b"backup")
                backup.with_suffix(backup.suffix + ".json").write_text(
                    "{}",
                    encoding="utf-8",
                )
                timestamp = time.time() + index
                os.utime(backup, (timestamp, timestamp))
                os.utime(backup.with_suffix(backup.suffix + ".json"), (timestamp, timestamp))
                files.append(backup)

            deleted = database_backup.rotate_backups(
                output_dir,
                retention_days=365,
                keep_last=2,
            )

            remaining = sorted(output_dir.glob("*.sql.gz"))
            self.assertEqual(len(deleted), 2)
            self.assertEqual(len(remaining), 2)
            self.assertTrue(files[2].exists())
            self.assertTrue(files[3].exists())

    def test_seleccion_provider_y_storage_conocidos(self):
        backup_provider = database_backup.get_backup_provider("mysqldump")
        storage = database_backup.get_backup_storage("local")

        self.assertIsInstance(backup_provider, database_backup.MySQLDumpBackupProvider)
        self.assertIsInstance(storage, database_backup.LocalBackupStorage)

    def test_provider_o_storage_desconocido_rechaza_configuracion(self):
        with self.assertRaises(database_backup.BackupProviderNotFoundError):
            database_backup.get_backup_provider("rds_snapshot")

        with self.assertRaises(database_backup.BackupProviderNotFoundError):
            database_backup.get_backup_storage("s3")

    def test_storage_local_escribe_manifest_versionado(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            backup_path = Path(tmpdir) / "backup.sql.gz"
            backup_path.write_bytes(b"backup")
            manifest = database_backup.BackupManifest(
                format_version=1,
                provider="mysqldump",
                storage_provider="local",
                database_engine="mysql",
                engine_version="8.0-test",
                backup_type="logical_full",
                database="mitienda",
                host="localhost",
                started_at_utc="2026-08-01T12:00:00+00:00",
                finished_at_utc="2026-08-01T12:00:01+00:00",
                duration_seconds=1,
                backup_file=str(backup_path),
                size_bytes=6,
                checksum_algorithm="sha256",
                checksum="abc",
                sha256="abc",
                compression="gzip",
                tool="mysqldump",
                consistent=True,
                single_transaction=True,
                routines=True,
                events=True,
                database_statements=False,
                restore_target_required=True,
                restore_requirements={"compression": "gzip"},
                binlog_coordinates=None,
                critical_table_counts={"usuarios": 1},
                external_copy="prepared_not_implemented",
                result="ok",
            )

            manifest_path = database_backup.LocalBackupStorage().write_manifest(
                backup_path,
                manifest,
            )

            metadata = json.loads(manifest_path.read_text(encoding="utf-8"))
            self.assertEqual(metadata["format_version"], 1)
            self.assertEqual(metadata["provider"], "mysqldump")
            self.assertEqual(metadata["storage_provider"], "local")


if __name__ == "__main__":
    unittest.main()
