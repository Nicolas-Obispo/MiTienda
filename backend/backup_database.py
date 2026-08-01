"""
backup_database.py
------------------
Ejecuta el procedimiento oficial de backup MySQL.

No incluir credenciales en este archivo. Usar FEEDGO_MYSQL_DEFAULTS_FILE.
"""

import sys

from app.core.database_backup import (
    BackupConfigurationError,
    BackupExecutionError,
    config_from_env,
    run_backup,
)


def main() -> int:
    try:
        manifest = run_backup(config_from_env())
    except (BackupConfigurationError, BackupExecutionError) as exc:
        print(f"BACKUP FALLIDO: {exc}", file=sys.stderr)
        return 2

    print("BACKUP OK")
    print(f"Archivo: {manifest.backup_file}")
    print(f"Tamano bytes: {manifest.size_bytes}")
    print(f"SHA-256: {manifest.sha256}")
    print(f"Duracion segundos: {manifest.duration_seconds}")
    print("Copia externa: preparada, no implementada")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
