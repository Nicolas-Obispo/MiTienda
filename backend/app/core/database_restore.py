"""
Procedimiento operativo de restore MySQL.

El restore siempre apunta a una base temporal controlada y nunca sobrescribe la
base runtime configurada.
"""

from __future__ import annotations

import gzip
import hashlib
import json
import os
import re
import subprocess
import tempfile
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Protocol

from sqlalchemy import create_engine, inspect, text

from app.core.database import Base, engine
from app.core.model_registry import import_all_models
from app.core.operation_metrics import (
    METRIC_RESTORE_RUN_COUNT,
    METRIC_RESTORE_RUN_DURATION_MS,
    increment_counter,
    record_duration,
)
from check_database_schema import SchemaCheckResult, check_schema

RESTORE_DATABASE_PATTERN = re.compile(r"^feedgo_restore_tmp_[a-z0-9_]+$")
DROP_CONFIRMATION = "DROP_RESTORE_TEMP_DB"
DEFAULT_EVIDENCE_DIR = Path("restore_tmp/evidence")


class RestoreConfigurationError(RuntimeError):
    pass


class RestoreValidationError(RuntimeError):
    pass


class RestoreExecutionError(RuntimeError):
    pass


class RestoreProviderNotFoundError(RestoreConfigurationError):
    pass


@dataclass(frozen=True)
class RestoreConfig:
    backup_file: Path
    manifest_file: Path
    target_database: str
    defaults_extra_file: Path
    evidence_dir: Path = DEFAULT_EVIDENCE_DIR
    mysql_bin: str = "mysql"
    provider: str = "mysql_client"


@dataclass(frozen=True)
class RestoreEvidence:
    target_database: str
    backup_file: str
    manifest_file: str
    started_at_utc: str
    finished_at_utc: str
    duration_seconds: float
    schema_ok: bool
    counts_ok: bool
    expected_counts: dict[str, int]
    restored_counts: dict[str, int]
    result: str
    errors: list[str]
    cleanup: str


@dataclass(frozen=True)
class RestoreResult:
    evidence: RestoreEvidence
    evidence_file: Path
    schema_result: SchemaCheckResult


class RestoreProvider(Protocol):
    name: str

    def restore(
        self,
        config: RestoreConfig,
        popen_factory,
    ) -> None:
        ...


class MySQLClientRestoreProvider:
    name = "mysql_client"

    def restore(
        self,
        config: RestoreConfig,
        popen_factory,
    ) -> None:
        _run_mysql_restore(config, popen_factory=popen_factory)


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _safe_host() -> str:
    host = engine.url.host
    if not host:
        raise RestoreConfigurationError("Host de base de datos no configurado.")
    return host


def _runtime_database() -> str:
    database = engine.url.database
    if not database:
        raise RestoreConfigurationError("Base de datos runtime no configurada.")
    return database


def _validate_target_database(target_database: str) -> None:
    if target_database == _runtime_database():
        raise RestoreValidationError("El destino runtime esta prohibido.")

    if not RESTORE_DATABASE_PATTERN.fullmatch(target_database):
        raise RestoreValidationError(
            "El destino debe ser una base temporal feedgo_restore_tmp_<nombre>."
        )


def _load_manifest(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise RestoreValidationError("El manifiesto de backup no existe.")

    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise RestoreValidationError("El manifiesto de backup no es JSON valido.") from exc


def _manifest_restore_requirement(
    manifest: dict[str, Any],
    key: str,
    fallback_key: str | None = None,
):
    restore_requirements = manifest.get("restore_requirements")
    if isinstance(restore_requirements, dict) and key in restore_requirements:
        return restore_requirements[key]
    return manifest.get(fallback_key or key)


def _validate_manifest_for_restore(manifest: dict[str, Any]) -> None:
    compression = _manifest_restore_requirement(manifest, "compression")
    if compression != "gzip":
        raise RestoreValidationError("El backup no declara compresion gzip.")

    database_statements = _manifest_restore_requirement(manifest, "database_statements")
    if database_statements is not False:
        raise RestoreValidationError(
            "El manifiesto no garantiza ausencia de sentencias CREATE/USE DATABASE."
        )

    restore_target_required = _manifest_restore_requirement(
        manifest,
        "restore_target_required",
    )
    if restore_target_required is not True:
        raise RestoreValidationError("El manifiesto no exige destino de restore.")

    if not isinstance(manifest.get("critical_table_counts"), dict):
        raise RestoreValidationError("El manifiesto no contiene conteos criticos.")

    if not manifest.get("sha256") and not manifest.get("checksum"):
        raise RestoreValidationError("El manifiesto no contiene SHA-256.")


def _validate_backup_file(backup_file: Path, manifest: dict[str, Any]) -> None:
    if not backup_file.exists():
        raise RestoreValidationError("El archivo de backup no existe.")

    actual_sha = _sha256_file(backup_file)
    expected_sha = manifest.get("sha256") or manifest.get("checksum")
    if actual_sha != expected_sha:
        raise RestoreValidationError("El SHA-256 del backup no coincide.")

    try:
        with gzip.open(backup_file, "rb") as file:
            file.read(1)
    except OSError as exc:
        raise RestoreValidationError("El archivo no es gzip valido.") from exc


def _validate_config(config: RestoreConfig) -> dict[str, Any]:
    _validate_target_database(config.target_database)

    if not config.defaults_extra_file.exists():
        raise RestoreConfigurationError(
            "El archivo seguro de credenciales MySQL no existe."
        )

    manifest = _load_manifest(config.manifest_file)
    _validate_manifest_for_restore(manifest)
    _validate_backup_file(config.backup_file, manifest)
    return manifest


def _database_exists(target_database: str) -> bool:
    with engine.connect() as connection:
        result = connection.execute(
            text("SELECT SCHEMA_NAME FROM INFORMATION_SCHEMA.SCHEMATA "
                 "WHERE SCHEMA_NAME = :database"),
            {"database": target_database},
        )
        return result.first() is not None


def _create_database(target_database: str) -> None:
    quoted = engine.dialect.identifier_preparer.quote(target_database)
    statement = text(
        f"CREATE DATABASE {quoted} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
    )
    with engine.connect().execution_options(isolation_level="AUTOCOMMIT") as connection:
        connection.execute(statement)


def _drop_database(target_database: str) -> None:
    quoted = engine.dialect.identifier_preparer.quote(target_database)
    with engine.connect().execution_options(isolation_level="AUTOCOMMIT") as connection:
        connection.execute(text(f"DROP DATABASE {quoted}"))


def _build_mysql_restore_command(config: RestoreConfig) -> list[str]:
    return [
        config.mysql_bin,
        f"--defaults-extra-file={config.defaults_extra_file}",
        f"--host={_safe_host()}",
        config.target_database,
    ]


def _run_mysql_restore(
    config: RestoreConfig,
    popen_factory=subprocess.Popen,
) -> None:
    command = _build_mysql_restore_command(config)
    try:
        with tempfile.TemporaryFile() as stderr_file:
            process = popen_factory(
                command,
                stdin=subprocess.PIPE,
                stdout=subprocess.DEVNULL,
                stderr=stderr_file,
                shell=False,
            )
            if process.stdin is None:
                raise RestoreExecutionError("mysql no expuso stdin.")

            with gzip.open(config.backup_file, "rb") as sql_stream:
                for chunk in iter(lambda: sql_stream.read(1024 * 1024), b""):
                    process.stdin.write(chunk)

            process.stdin.close()
            returncode = process.wait()
            stderr_file.seek(0)
            stderr = stderr_file.read()
    except OSError as exc:
        raise RestoreExecutionError(f"No se pudo ejecutar mysql: {exc}") from exc

    if returncode != 0:
        error_output = stderr.decode("utf-8", errors="replace") if stderr else ""
        raise RestoreExecutionError(
            "mysql fallo durante el restore. " + error_output.strip()
        )


def _target_engine(target_database: str):
    return create_engine(engine.url.set(database=target_database), echo=False)


def _run_schema_check(target_database: str) -> SchemaCheckResult:
    import_all_models()
    target_engine = _target_engine(target_database)
    try:
        return check_schema(inspector=inspect(target_engine), metadata=Base.metadata)
    finally:
        target_engine.dispose()


def _collect_restored_counts(
    target_database: str,
    table_names: list[str],
) -> dict[str, int]:
    target_engine = _target_engine(target_database)
    counts: dict[str, int] = {}
    try:
        with target_engine.connect() as connection:
            for table_name in table_names:
                quoted = target_engine.dialect.identifier_preparer.quote(table_name)
                result = connection.execute(text(f"SELECT COUNT(*) FROM {quoted}"))
                counts[table_name] = int(result.scalar_one())
    finally:
        target_engine.dispose()
    return counts


def _write_evidence(config: RestoreConfig, evidence: RestoreEvidence) -> Path:
    config.evidence_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.fromisoformat(evidence.finished_at_utc).strftime(
        "%Y%m%dT%H%M%SZ"
    )
    evidence_path = config.evidence_dir / (
        f"{config.target_database}_{timestamp}_restore.json"
    )
    evidence_path.write_text(
        json.dumps(asdict(evidence), indent=2, sort_keys=True),
        encoding="utf-8",
    )
    return evidence_path


def get_restore_provider(name: str) -> RestoreProvider:
    if name == MySQLClientRestoreProvider.name:
        return MySQLClientRestoreProvider()
    raise RestoreProviderNotFoundError(f"Restore provider desconocido: {name}")


class RestoreService:
    def __init__(self, provider: RestoreProvider):
        self.provider = provider

    def restore(
        self,
        config: RestoreConfig,
        popen_factory=subprocess.Popen,
    ) -> RestoreResult:
        started = _utc_now()
        errors: list[str] = []
        schema_result = SchemaCheckResult(0, 0, [], [], {})
        expected_counts: dict[str, int] = {}
        restored_counts: dict[str, int] = {}

        try:
            manifest = _validate_config(config)
            expected_counts = {
                str(table): int(count)
                for table, count in manifest["critical_table_counts"].items()
            }

            if _database_exists(config.target_database):
                raise RestoreExecutionError("La base temporal destino ya existe.")

            _create_database(config.target_database)
            self.provider.restore(config, popen_factory=popen_factory)

            schema_result = _run_schema_check(config.target_database)
            if not schema_result.ok:
                raise RestoreExecutionError("El schema restaurado no coincide.")

            restored_counts = _collect_restored_counts(
                config.target_database,
                sorted(expected_counts.keys()),
            )
            if restored_counts != expected_counts:
                raise RestoreExecutionError("Los conteos criticos no coinciden.")

            result = "ok"
        except Exception as exc:
            result = "failed"
            errors.append(str(exc))
            finished = _utc_now()
            evidence = RestoreEvidence(
                target_database=config.target_database,
                backup_file=str(config.backup_file),
                manifest_file=str(config.manifest_file),
                started_at_utc=started.isoformat(),
                finished_at_utc=finished.isoformat(),
                duration_seconds=round((finished - started).total_seconds(), 3),
                schema_ok=schema_result.ok,
                counts_ok=bool(expected_counts) and restored_counts == expected_counts,
                expected_counts=expected_counts,
                restored_counts=restored_counts,
                result=result,
                errors=errors,
                cleanup="not_requested",
            )
            _write_evidence(config, evidence)
            increment_counter(
                METRIC_RESTORE_RUN_COUNT,
                tags={"provider": self.provider.name, "result": result},
            )
            record_duration(
                METRIC_RESTORE_RUN_DURATION_MS,
                evidence.duration_seconds * 1000,
                tags={"provider": self.provider.name, "result": result},
            )
            raise RestoreExecutionError(str(exc)) from exc

        finished = _utc_now()
        evidence = RestoreEvidence(
            target_database=config.target_database,
            backup_file=str(config.backup_file),
            manifest_file=str(config.manifest_file),
            started_at_utc=started.isoformat(),
            finished_at_utc=finished.isoformat(),
            duration_seconds=round((finished - started).total_seconds(), 3),
            schema_ok=schema_result.ok,
            counts_ok=restored_counts == expected_counts,
            expected_counts=expected_counts,
            restored_counts=restored_counts,
            result=result,
            errors=errors,
            cleanup="not_requested",
        )
        evidence_path = _write_evidence(config, evidence)
        increment_counter(
            METRIC_RESTORE_RUN_COUNT,
            tags={"provider": self.provider.name, "result": result},
        )
        record_duration(
            METRIC_RESTORE_RUN_DURATION_MS,
            evidence.duration_seconds * 1000,
            tags={"provider": self.provider.name, "result": result},
        )
        return RestoreResult(evidence, evidence_path, schema_result)


def restore_backup(
    config: RestoreConfig,
    popen_factory=subprocess.Popen,
) -> RestoreResult:
    service = RestoreService(provider=get_restore_provider(config.provider))
    return service.restore(config, popen_factory=popen_factory)


def drop_temporary_restore_database(
    target_database: str,
    confirmation: str | None,
) -> None:
    _validate_target_database(target_database)
    if confirmation != DROP_CONFIRMATION:
        raise RestoreValidationError("Confirmacion explicita invalida.")
    _drop_database(target_database)


def config_from_env() -> RestoreConfig:
    backup_file = os.environ.get("FEEDGO_RESTORE_BACKUP_FILE")
    manifest_file = os.environ.get("FEEDGO_RESTORE_MANIFEST_FILE")
    target_database = os.environ.get("FEEDGO_RESTORE_TARGET_DATABASE")
    defaults_file = os.environ.get("FEEDGO_MYSQL_DEFAULTS_FILE")

    missing = [
        name
        for name, value in [
            ("FEEDGO_RESTORE_BACKUP_FILE", backup_file),
            ("FEEDGO_RESTORE_MANIFEST_FILE", manifest_file),
            ("FEEDGO_RESTORE_TARGET_DATABASE", target_database),
            ("FEEDGO_MYSQL_DEFAULTS_FILE", defaults_file),
        ]
        if not value
    ]
    if missing:
        raise RestoreConfigurationError(
            "Faltan variables requeridas: " + ", ".join(missing)
        )

    evidence_dir = Path(os.environ.get("FEEDGO_RESTORE_EVIDENCE_DIR", "restore_tmp/evidence"))
    mysql_bin = os.environ.get("FEEDGO_MYSQL_BIN", "mysql")

    return RestoreConfig(
        backup_file=Path(backup_file),
        manifest_file=Path(manifest_file),
        target_database=target_database,
        defaults_extra_file=Path(defaults_file),
        evidence_dir=evidence_dir,
        mysql_bin=mysql_bin,
    )
