"""
add_comercios_rubro_fk.py
-------------------------
Prepara la alineacion fisica de la FK comercios.rubro_id -> rubros.id.

Importar este modulo no modifica la base. La ejecucion directa audita por
defecto y solo aplica el ALTER con confirmacion explicita.
"""

from __future__ import annotations

import os
import sys

from sqlalchemy import text

from app.core.database import engine


FK_NAME = "fk_comercios_rubro"
APPLY_CONFIRMATION = "ADD_COMERCIOS_RUBRO_FK"


class SchemaAlignmentError(RuntimeError):
    pass


def safe_database_target() -> str:
    host = engine.url.host or "<sin-host>"
    database = engine.url.database or "<sin-base>"
    return f"{engine.dialect.name}://{host}/{database}"


def fk_exists(connection) -> bool:
    result = connection.execute(
        text(
            """
            SELECT COUNT(*)
            FROM information_schema.KEY_COLUMN_USAGE
            WHERE TABLE_SCHEMA = DATABASE()
              AND TABLE_NAME = 'comercios'
              AND CONSTRAINT_NAME = :fk_name
              AND COLUMN_NAME = 'rubro_id'
              AND REFERENCED_TABLE_NAME = 'rubros'
              AND REFERENCED_COLUMN_NAME = 'id'
            """
        ),
        {"fk_name": FK_NAME},
    )
    return int(result.scalar_one()) > 0


def count_orphans(connection) -> int:
    result = connection.execute(
        text(
            """
            SELECT COUNT(*)
            FROM comercios c
            LEFT JOIN rubros r ON r.id = c.rubro_id
            WHERE c.rubro_id IS NOT NULL
              AND r.id IS NULL
            """
        )
    )
    return int(result.scalar_one())


def audit_alignment() -> tuple[bool, int]:
    with engine.connect() as connection:
        return fk_exists(connection), count_orphans(connection)


def apply_alignment(confirmation: str | None) -> str:
    if confirmation != APPLY_CONFIRMATION:
        raise SchemaAlignmentError("Confirmacion explicita invalida.")

    with engine.connect().execution_options(isolation_level="AUTOCOMMIT") as connection:
        exists = fk_exists(connection)
        orphans = count_orphans(connection)

        if orphans:
            raise SchemaAlignmentError(
                f"No se puede crear la FK: existen {orphans} comercios huerfanos."
            )

        if exists:
            return "already_exists"

        connection.execute(
            text(
                f"""
                ALTER TABLE comercios
                ADD CONSTRAINT {FK_NAME}
                FOREIGN KEY (rubro_id)
                REFERENCES rubros(id)
                """
            )
        )
        return "created"


def main() -> int:
    print(f"Destino: {safe_database_target()}")

    exists, orphans = audit_alignment()
    print(f"FK existente: {'si' if exists else 'no'}")
    print(f"Comercios huerfanos por rubro: {orphans}")

    if orphans:
        print("ABORTADO: resolver huerfanos antes de crear la FK.", file=sys.stderr)
        return 2

    confirmation = os.environ.get("FEEDGO_SCHEMA_ALIGN_CONFIRMATION")
    if confirmation != APPLY_CONFIRMATION:
        print("Modo auditoria: ALTER no ejecutado.")
        print(
            "Para aplicar, definir "
            f"FEEDGO_SCHEMA_ALIGN_CONFIRMATION={APPLY_CONFIRMATION}"
        )
        return 0

    try:
        result = apply_alignment(confirmation)
    except SchemaAlignmentError as exc:
        print(f"ALINEACION FALLIDA: {exc}", file=sys.stderr)
        return 2

    print(f"ALINEACION OK: {result}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
