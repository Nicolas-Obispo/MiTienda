"""
Procedimiento operativo de backup MySQL.

Este modulo prepara y ejecuta backups mediante mysqldump sin almacenar
credenciales en codigo.
"""

from __future__ import annotations

import gzip
import hashlib
import json
import os
import subprocess
import tempfile
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Protocol

from sqlalchemy import text

from app.core.database import engine
from app.core.operation_metrics import (
    METRIC_BACKUP_RUN_COUNT,
    METRIC_BACKUP_RUN_DURATION_MS,
    increment_counter,
    record_duration,
)

DEFAULT_BACKUP_DIR = Path("backups/mysql")
DEFAULT_RETENTION_DAYS = 14
DEFAULT_KEEP_LAST = 10
CRITICAL_TABLES = (
    "usuarios",
    "comercios",
    "publicaciones",
    "historias",
    "usuarios_documentos_aceptaciones",
    "contenido_denuncias",
    "agenda_contextos_agendables",
    "agenda_elementos",
    "feedgo_agenda_contextos",
    "comercios_horarios_atencion",
    "publicaciones_guardadas",
    "seguidores",
    "tokens_revocados",
)


class BackupConfigurationError(RuntimeError):
    pass


class BackupExecutionError(RuntimeError):
    pass


class BackupProviderNotFoundError(BackupConfigurationError):
    pass


@dataclass(frozen=True)
class BackupConfig:
    output_dir: Path
    defaults_extra_file: Path
    retention_days: int = DEFAULT_RETENTION_DAYS
    keep_last: int = DEFAULT_KEEP_LAST
    mysqldump_bin: str = "mysqldump"
    provider: str = "mysqldump"
    storage_provider: str = "local"


@dataclass(frozen=True)
class BackupManifest:
    format_version: int
    provider: str
    storage_provider: str
    database_engine: str
    engine_version: str
    backup_type: str
    database: str
    host: str
    started_at_utc: str
    finished_at_utc: str
    duration_seconds: float
    backup_file: str
    size_bytes: int
    checksum_algorithm: str
    checksum: str
    sha256: str
    compression: str
    tool: str
    consistent: bool
    single_transaction: bool
    routines: bool
    events: bool
    database_statements: bool
    restore_target_required: bool
    restore_requirements: dict[str, object]
    binlog_coordinates: dict[str, str] | None
    critical_table_counts: dict[str, int]
    external_copy: str
    result: str


class BackupProvider(Protocol):
    name: str
    database_engine: str
    backup_type: str

    def create_backup(
        self,
        config: BackupConfig,
        backup_path: Path,
        popen_factory,
    ) -> None:
        ...


class BackupStorage(Protocol):
    name: str

    def backup_file_path(
        self,
        config: BackupConfig,
        now: datetime | None = None,
    ) -> Path:
        ...

    def write_manifest(self, backup_path: Path, manifest: BackupManifest) -> Path:
        ...

    def rotate(
        self,
        output_dir: Path,
        retention_days: int,
        keep_last: int,
    ) -> list[Path]:
        ...


class MySQLDumpBackupProvider:
    name = "mysqldump"
    database_engine = "mysql"
    backup_type = "logical_full"

    def create_backup(
        self,
        config: BackupConfig,
        backup_path: Path,
        popen_factory,
    ) -> None:
        command = _build_mysqldump_command(config)
        try:
            with tempfile.TemporaryFile() as stderr_file:
                process = popen_factory(
                    command,
                    stdout=subprocess.PIPE,
                    stderr=stderr_file,
                    shell=False,
                )
                if process.stdout is None:
                    raise BackupExecutionError("mysqldump no expuso stdout.")

                with gzip.open(backup_path, "wb") as compressed_file:
                    for chunk in iter(lambda: process.stdout.read(1024 * 1024), b""):
                        compressed_file.write(chunk)

                returncode = process.wait()
                stderr_file.seek(0)
                stderr = stderr_file.read()
        except OSError as exc:
            backup_path.unlink(missing_ok=True)
            raise BackupExecutionError(f"No se pudo ejecutar mysqldump: {exc}") from exc

        if returncode != 0:
            backup_path.unlink(missing_ok=True)
            error_output = stderr.decode("utf-8", errors="replace") if stderr else ""
            raise BackupExecutionError(
                "mysqldump fallo sin completar el backup. "
                + error_output.strip()
            )


class LocalBackupStorage:
    name = "local"

    def backup_file_path(
        self,
        config: BackupConfig,
        now: datetime | None = None,
    ) -> Path:
        return _backup_file_path(config, now=now)

    def write_manifest(self, backup_path: Path, manifest: BackupManifest) -> Path:
        return _write_manifest(backup_path, manifest)

    def rotate(
        self,
        output_dir: Path,
        retention_days: int,
        keep_last: int,
    ) -> list[Path]:
        return rotate_backups(output_dir, retention_days, keep_last)


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _timestamp_for_filename(now: datetime) -> str:
    return now.strftime("%Y%m%dT%H%M%SZ")


def _safe_database_name() -> str:
    database = engine.url.database
    if not database:
        raise BackupConfigurationError("Base de datos no configurada.")
    return database


def _safe_host() -> str:
    host = engine.url.host
    if not host:
        raise BackupConfigurationError("Host de base de datos no configurado.")
    return host


def _database_engine_version() -> str:
    with engine.connect() as connection:
        result = connection.execute(text("SELECT VERSION()"))
        return str(result.scalar_one())


def _validate_config(config: BackupConfig) -> None:
    if not config.defaults_extra_file:
        raise BackupConfigurationError("Falta defaults_extra_file.")

    if not config.defaults_extra_file.exists():
        raise BackupConfigurationError(
            "El archivo seguro de credenciales MySQL no existe."
        )

    if config.retention_days < 1:
        raise BackupConfigurationError("retention_days debe ser mayor a cero.")

    if config.keep_last < 1:
        raise BackupConfigurationError("keep_last debe ser mayor a cero.")


def _build_mysqldump_command(config: BackupConfig) -> list[str]:
    database = _safe_database_name()
    host = _safe_host()
    return [
        config.mysqldump_bin,
        f"--defaults-extra-file={config.defaults_extra_file}",
        f"--host={host}",
        "--single-transaction",
        "--quick",
        "--routines",
        "--events",
        database,
    ]


def _backup_file_path(config: BackupConfig, now: datetime | None = None) -> Path:
    timestamp = _timestamp_for_filename(now or _utc_now())
    database = _safe_database_name()
    return config.output_dir / f"{database}_{timestamp}.sql.gz"


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _write_manifest(path: Path, manifest: BackupManifest) -> Path:
    manifest_path = path.with_suffix(path.suffix + ".json")
    manifest_path.write_text(
        json.dumps(asdict(manifest), indent=2, sort_keys=True),
        encoding="utf-8",
    )
    return manifest_path


def collect_critical_table_counts(table_names=CRITICAL_TABLES) -> dict[str, int]:
    counts: dict[str, int] = {}
    with engine.connect() as connection:
        for table_name in table_names:
            if table_name not in engine.dialect.identifier_preparer.reserved_words:
                quoted_name = engine.dialect.identifier_preparer.quote(table_name)
            else:
                quoted_name = engine.dialect.identifier_preparer.quote(table_name)
            result = connection.execute(text(f"SELECT COUNT(*) FROM {quoted_name}"))
            counts[table_name] = int(result.scalar_one())
    return counts


def rotate_backups(output_dir: Path, retention_days: int, keep_last: int) -> list[Path]:
    backups = sorted(
        output_dir.glob("*.sql.gz"),
        key=lambda item: item.stat().st_mtime,
        reverse=True,
    )
    cutoff = time.time() - (retention_days * 24 * 60 * 60)
    to_delete: list[Path] = []
    for index, backup in enumerate(backups):
        if index >= keep_last or backup.stat().st_mtime < cutoff:
            to_delete.append(backup)

    deleted: list[Path] = []
    for backup in to_delete:
        manifest = backup.with_suffix(backup.suffix + ".json")
        backup.unlink(missing_ok=True)
        manifest.unlink(missing_ok=True)
        deleted.append(backup)

    return deleted


def get_backup_provider(name: str) -> BackupProvider:
    if name == MySQLDumpBackupProvider.name:
        return MySQLDumpBackupProvider()
    raise BackupProviderNotFoundError(f"Backup provider desconocido: {name}")


def get_backup_storage(name: str) -> BackupStorage:
    if name == LocalBackupStorage.name:
        return LocalBackupStorage()
    raise BackupProviderNotFoundError(f"Backup storage desconocido: {name}")


class BackupService:
    def __init__(self, provider: BackupProvider, storage: BackupStorage):
        self.provider = provider
        self.storage = storage

    def run(
        self,
        config: BackupConfig,
        now: datetime | None = None,
        popen_factory=subprocess.Popen,
        counts_provider: Callable[[], dict[str, int]] = collect_critical_table_counts,
        engine_version_provider: Callable[[], str] = _database_engine_version,
    ) -> BackupManifest:
        _validate_config(config)
        config.output_dir.mkdir(parents=True, exist_ok=True)

        started = _utc_now()
        backup_path = self.storage.backup_file_path(config, now=now or started)
        try:
            self.provider.create_backup(config, backup_path, popen_factory)
        except Exception:
            increment_counter(
                METRIC_BACKUP_RUN_COUNT,
                tags={"provider": self.provider.name, "result": "failed"},
            )
            raise

        finished = _utc_now()
        sha256 = _sha256_file(backup_path)
        size_bytes = backup_path.stat().st_size
        critical_table_counts = counts_provider()

        manifest = BackupManifest(
            format_version=1,
            provider=self.provider.name,
            storage_provider=self.storage.name,
            database_engine=self.provider.database_engine,
            engine_version=engine_version_provider(),
            backup_type=self.provider.backup_type,
            database=_safe_database_name(),
            host=_safe_host(),
            started_at_utc=started.isoformat(),
            finished_at_utc=finished.isoformat(),
            duration_seconds=round((finished - started).total_seconds(), 3),
            backup_file=str(backup_path),
            size_bytes=size_bytes,
            checksum_algorithm="sha256",
            checksum=sha256,
            sha256=sha256,
            compression="gzip",
            tool=self.provider.name,
            consistent=True,
            single_transaction=True,
            routines=True,
            events=True,
            database_statements=False,
            restore_target_required=True,
            restore_requirements={
                "compression": "gzip",
                "database_statements": False,
                "requires_empty_database": True,
                "restore_target_required": True,
                "target_database_pattern": "feedgo_restore_tmp_<nombre>",
            },
            binlog_coordinates=None,
            critical_table_counts=critical_table_counts,
            external_copy="prepared_not_implemented",
            result="ok",
        )
        self.storage.write_manifest(backup_path, manifest)
        self.storage.rotate(
            config.output_dir,
            retention_days=config.retention_days,
            keep_last=config.keep_last,
        )
        increment_counter(
            METRIC_BACKUP_RUN_COUNT,
            tags={"provider": self.provider.name, "result": manifest.result},
        )
        record_duration(
            METRIC_BACKUP_RUN_DURATION_MS,
            manifest.duration_seconds * 1000,
            tags={"provider": self.provider.name, "result": manifest.result},
        )
        return manifest


def run_backup(
    config: BackupConfig,
    now: datetime | None = None,
    popen_factory=subprocess.Popen,
    counts_provider=collect_critical_table_counts,
    engine_version_provider=_database_engine_version,
) -> BackupManifest:
    service = BackupService(
        provider=get_backup_provider(config.provider),
        storage=get_backup_storage(config.storage_provider),
    )
    return service.run(
        config,
        now=now,
        popen_factory=popen_factory,
        counts_provider=counts_provider,
        engine_version_provider=engine_version_provider,
    )


def config_from_env() -> BackupConfig:
    defaults_file = os.environ.get("FEEDGO_MYSQL_DEFAULTS_FILE")
    if not defaults_file:
        raise BackupConfigurationError(
            "Definir FEEDGO_MYSQL_DEFAULTS_FILE con la ruta al archivo seguro "
            "de credenciales MySQL."
        )

    output_dir = Path(os.environ.get("FEEDGO_BACKUP_DIR", str(DEFAULT_BACKUP_DIR)))
    retention_days = int(os.environ.get("FEEDGO_BACKUP_RETENTION_DAYS", "14"))
    keep_last = int(os.environ.get("FEEDGO_BACKUP_KEEP_LAST", "10"))
    mysqldump_bin = os.environ.get("FEEDGO_MYSQLDUMP_BIN", "mysqldump")

    return BackupConfig(
        output_dir=output_dir,
        defaults_extra_file=Path(defaults_file),
        retention_days=retention_days,
        keep_last=keep_last,
        mysqldump_bin=mysqldump_bin,
    )
