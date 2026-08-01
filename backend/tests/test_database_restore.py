import gzip
import hashlib
import io
import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from check_database_schema import SchemaCheckResult
from app.core.operation_metrics import (
    METRIC_RESTORE_RUN_COUNT,
    METRIC_RESTORE_RUN_DURATION_MS,
    local_metrics_sink,
)
from app.core import database_restore


def _fake_engine(database="mitienda"):
    return SimpleNamespace(
        dialect=SimpleNamespace(
            name="mysql",
            identifier_preparer=SimpleNamespace(quote=lambda value: f"`{value}`"),
        ),
        url=SimpleNamespace(
            host="localhost",
            database=database,
            set=lambda **kwargs: SimpleNamespace(
                host="localhost",
                database=kwargs.get("database", database),
            ),
        ),
    )


class DatabaseRestoreTests(unittest.TestCase):
    def setUp(self):
        local_metrics_sink.clear()

    def tearDown(self):
        local_metrics_sink.clear()

    def _config(
        self,
        tmpdir: str,
        content: bytes = b"CREATE TABLE usuarios (id int);\n",
        manifest_updates: dict | None = None,
        target_database: str = "feedgo_restore_tmp_test",
        gzip_valid: bool = True,
    ) -> database_restore.RestoreConfig:
        root = Path(tmpdir)
        backup_file = root / "backup.sql.gz"
        if gzip_valid:
            with gzip.open(backup_file, "wb") as file:
                file.write(content)
        else:
            backup_file.write_bytes(content)

        sha256 = hashlib.sha256(backup_file.read_bytes()).hexdigest()
        manifest = {
            "backup_file": str(backup_file),
            "compression": "gzip",
            "critical_table_counts": {"usuarios": 1},
            "database": "mitienda",
            "database_statements": False,
            "restore_target_required": True,
            "sha256": sha256,
        }
        if manifest_updates:
            manifest.update(manifest_updates)

        manifest_file = root / "backup.sql.gz.json"
        manifest_file.write_text(json.dumps(manifest), encoding="utf-8")

        defaults_file = root / "mysql.cnf"
        defaults_file.write_text("[client]\nuser=test\n", encoding="utf-8")

        return database_restore.RestoreConfig(
            backup_file=backup_file,
            manifest_file=manifest_file,
            target_database=target_database,
            defaults_extra_file=defaults_file,
            evidence_dir=root / "evidence",
        )

    def _patch_successful_side_effects(self):
        schema_ok = SchemaCheckResult(
            metadata_count=1,
            physical_count=1,
            missing_tables=[],
            extra_tables=[],
            column_differences={},
        )
        return [
            patch.object(database_restore, "engine", _fake_engine()),
            patch.object(database_restore, "_database_exists", return_value=False),
            patch.object(database_restore, "_create_database"),
            patch.object(database_restore, "_run_mysql_restore"),
            patch.object(database_restore, "_run_schema_check", return_value=schema_ok),
            patch.object(
                database_restore,
                "_collect_restored_counts",
                return_value={"usuarios": 1},
            ),
        ]

    def test_checksum_incorrecto_rechaza_restore(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            config = self._config(tmpdir, manifest_updates={"sha256": "bad"})
            with patch.object(database_restore, "engine", _fake_engine()):
                with self.assertRaises(database_restore.RestoreExecutionError):
                    database_restore.restore_backup(config)

        self.assertIn(
            METRIC_RESTORE_RUN_COUNT,
            [sample.name for sample in local_metrics_sink.snapshot()],
        )

    def test_gzip_invalido_rechaza_restore(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            config = self._config(tmpdir, content=b"not gzip", gzip_valid=False)
            with patch.object(database_restore, "engine", _fake_engine()):
                with self.assertRaises(database_restore.RestoreExecutionError):
                    database_restore.restore_backup(config)

    def test_destino_prohibido_rechaza_mitienda(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            config = self._config(tmpdir, target_database="mitienda")
            with patch.object(database_restore, "engine", _fake_engine()):
                with self.assertRaises(database_restore.RestoreExecutionError):
                    database_restore.restore_backup(config)

    def test_destino_existente_aborta(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            config = self._config(tmpdir)
            schema_ok = SchemaCheckResult(1, 1, [], [], {})
            with patch.object(database_restore, "engine", _fake_engine()), \
                patch.object(database_restore, "_database_exists", return_value=True), \
                patch.object(database_restore, "_run_schema_check", return_value=schema_ok):
                with self.assertRaises(database_restore.RestoreExecutionError):
                    database_restore.restore_backup(config)

    def test_fallo_creacion_aborta(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            config = self._config(tmpdir)
            with patch.object(database_restore, "engine", _fake_engine()), \
                patch.object(database_restore, "_database_exists", return_value=False), \
                patch.object(
                    database_restore,
                    "_create_database",
                    side_effect=database_restore.RestoreExecutionError("create failed"),
                ):
                with self.assertRaises(database_restore.RestoreExecutionError):
                    database_restore.restore_backup(config)

    def test_fallo_restore_aborta(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            config = self._config(tmpdir)
            with patch.object(database_restore, "engine", _fake_engine()), \
                patch.object(database_restore, "_database_exists", return_value=False), \
                patch.object(database_restore, "_create_database"), \
                patch.object(
                    database_restore,
                    "_run_mysql_restore",
                    side_effect=database_restore.RestoreExecutionError("restore failed"),
                ):
                with self.assertRaises(database_restore.RestoreExecutionError):
                    database_restore.restore_backup(config)

    def test_schema_diferente_aborta(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            config = self._config(tmpdir)
            schema_bad = SchemaCheckResult(1, 0, ["usuarios"], [], {})
            with patch.object(database_restore, "engine", _fake_engine()), \
                patch.object(database_restore, "_database_exists", return_value=False), \
                patch.object(database_restore, "_create_database"), \
                patch.object(database_restore, "_run_mysql_restore"), \
                patch.object(database_restore, "_run_schema_check", return_value=schema_bad):
                with self.assertRaises(database_restore.RestoreExecutionError):
                    database_restore.restore_backup(config)

    def test_conteos_criticos_diferentes_aborta(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            config = self._config(tmpdir)
            schema_ok = SchemaCheckResult(1, 1, [], [], {})
            with patch.object(database_restore, "engine", _fake_engine()), \
                patch.object(database_restore, "_database_exists", return_value=False), \
                patch.object(database_restore, "_create_database"), \
                patch.object(database_restore, "_run_mysql_restore"), \
                patch.object(database_restore, "_run_schema_check", return_value=schema_ok), \
                patch.object(
                    database_restore,
                    "_collect_restored_counts",
                    return_value={"usuarios": 2},
                ):
                with self.assertRaises(database_restore.RestoreExecutionError):
                    database_restore.restore_backup(config)

    def test_restore_correcto_genera_evidencia(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            config = self._config(tmpdir)
            patches = self._patch_successful_side_effects()
            with patches[0], patches[1], patches[2] as create_database, patches[3] as run_mysql, patches[4], patches[5]:
                result = database_restore.restore_backup(config)

            self.assertEqual(result.evidence.result, "ok")
            self.assertTrue(result.evidence.schema_ok)
            self.assertTrue(result.evidence.counts_ok)
            self.assertTrue(result.evidence_file.exists())
            create_database.assert_called_once_with("feedgo_restore_tmp_test")
            run_mysql.assert_called_once()
            metric_names = [sample.name for sample in local_metrics_sink.snapshot()]
            self.assertIn(METRIC_RESTORE_RUN_COUNT, metric_names)
            self.assertIn(METRIC_RESTORE_RUN_DURATION_MS, metric_names)

    def test_restore_provider_conocido_y_desconocido(self):
        provider = database_restore.get_restore_provider("mysql_client")

        self.assertIsInstance(provider, database_restore.MySQLClientRestoreProvider)

        with self.assertRaises(database_restore.RestoreProviderNotFoundError):
            database_restore.get_restore_provider("rds_snapshot")

    def test_provider_envia_sql_descomprimido_por_stdin_pipe(self):
        class FakeStdin(io.BytesIO):
            def close(self):
                self.closed_called = True

        class FakeMysqlProcess:
            def __init__(self, command, stdin, stdout, stderr, shell):
                self.command = command
                self.stdin_arg = stdin
                self.stdout_arg = stdout
                self.stderr = stderr
                self.shell = shell
                self.stdin = FakeStdin()

            def wait(self):
                return 0

        calls = []

        def popen_factory(command, stdin, stdout, stderr, shell):
            process = FakeMysqlProcess(command, stdin, stdout, stderr, shell)
            calls.append(process)
            return process

        with tempfile.TemporaryDirectory() as tmpdir:
            config = self._config(
                tmpdir,
                content=b"CREATE TABLE usuarios (id int);\nINSERT INTO usuarios VALUES (1);\n",
            )
            with patch.object(database_restore, "engine", _fake_engine()):
                database_restore.MySQLClientRestoreProvider().restore(
                    config,
                    popen_factory=popen_factory,
                )

        self.assertEqual(len(calls), 1)
        self.assertEqual(calls[0].stdin_arg, database_restore.subprocess.PIPE)
        self.assertEqual(calls[0].stdout_arg, database_restore.subprocess.DEVNULL)
        self.assertFalse(calls[0].shell)
        self.assertIn(b"CREATE TABLE usuarios", calls[0].stdin.getvalue())
        self.assertIn(b"INSERT INTO usuarios", calls[0].stdin.getvalue())

    def test_restore_acepta_manifest_versionado_neutral(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            config = self._config(
                tmpdir,
                manifest_updates={
                    "format_version": 1,
                    "provider": "mysqldump",
                    "storage_provider": "local",
                    "database_engine": "mysql",
                    "engine_version": "8.0-test",
                    "backup_type": "logical_full",
                    "checksum_algorithm": "sha256",
                    "checksum": None,
                    "restore_requirements": {
                        "compression": "gzip",
                        "database_statements": False,
                        "restore_target_required": True,
                        "requires_empty_database": True,
                    },
                    "binlog_coordinates": None,
                },
            )
            manifest = json.loads(config.manifest_file.read_text(encoding="utf-8"))
            manifest["checksum"] = manifest.pop("sha256")
            manifest.pop("compression")
            manifest.pop("database_statements")
            manifest.pop("restore_target_required")
            config.manifest_file.write_text(json.dumps(manifest), encoding="utf-8")

            patches = self._patch_successful_side_effects()
            with patches[0], patches[1], patches[2], patches[3], patches[4], patches[5]:
                result = database_restore.restore_backup(config)

            self.assertEqual(result.evidence.result, "ok")

    def test_limpieza_explicita_requiere_confirmacion(self):
        with patch.object(database_restore, "engine", _fake_engine()), \
            patch.object(database_restore, "_drop_database") as drop_database:
            with self.assertRaises(database_restore.RestoreValidationError):
                database_restore.drop_temporary_restore_database(
                    "feedgo_restore_tmp_test",
                    confirmation=None,
                )

            database_restore.drop_temporary_restore_database(
                "feedgo_restore_tmp_test",
                confirmation=database_restore.DROP_CONFIRMATION,
            )

        drop_database.assert_called_once_with("feedgo_restore_tmp_test")


if __name__ == "__main__":
    unittest.main()
