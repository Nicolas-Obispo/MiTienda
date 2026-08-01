"""
restore_database.py
-------------------
Ejecuta el procedimiento oficial de restore MySQL sobre una base temporal.

No sobrescribe la base runtime configurada. No elimina la base temporal salvo
que se invoque explicitamente el modo de limpieza.
"""

import os
import sys

from app.core.database_restore import (
    DROP_CONFIRMATION,
    RestoreConfigurationError,
    RestoreExecutionError,
    RestoreValidationError,
    config_from_env,
    drop_temporary_restore_database,
    restore_backup,
)


def main() -> int:
    cleanup_target = os.environ.get("FEEDGO_RESTORE_CLEANUP_DATABASE")
    if cleanup_target:
        try:
            drop_temporary_restore_database(
                cleanup_target,
                os.environ.get("FEEDGO_RESTORE_CLEANUP_CONFIRMATION"),
            )
        except (RestoreConfigurationError, RestoreValidationError) as exc:
            print(f"LIMPIEZA FALLIDA: {exc}", file=sys.stderr)
            return 2
        print(f"LIMPIEZA OK: {cleanup_target}")
        return 0

    try:
        result = restore_backup(config_from_env())
    except (RestoreConfigurationError, RestoreExecutionError, RestoreValidationError) as exc:
        print(f"RESTORE FALLIDO: {exc}", file=sys.stderr)
        return 2

    print("RESTORE OK")
    print(f"Base temporal: {result.evidence.target_database}")
    print(f"Evidencia: {result.evidence_file}")
    print(f"Duracion segundos: {result.evidence.duration_seconds}")
    print("Limpieza: no ejecutada")
    print(
        "Para limpiar, definir FEEDGO_RESTORE_CLEANUP_DATABASE y "
        f"FEEDGO_RESTORE_CLEANUP_CONFIRMATION={DROP_CONFIRMATION}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
