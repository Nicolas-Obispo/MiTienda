"""
migrate_comercios_location_visibility.py
----------------------------------------
Migracion aditiva para comercios.mostrar_direccion_publicamente.

Importar este modulo no modifica la base. La ejecucion directa audita por
defecto y solo aplica upgrade o downgrade con una accion explicita.
"""

from __future__ import annotations

import os
import sys

from sqlalchemy import inspect, text

from app.core.database import engine


COLUMN_NAME = "mostrar_direccion_publicamente"
ACTION_ENV = "FEEDGO_LOCATION_VISIBILITY_MIGRATION"


class LocationVisibilityMigrationError(RuntimeError):
    pass


def safe_database_target() -> str:
    host = engine.url.host or "<sin-host>"
    database = engine.url.database or "<sin-base>"
    return f"{engine.dialect.name}://{host}/{database}"


def column_exists(connection) -> bool:
    return COLUMN_NAME in {
        column["name"] for column in inspect(connection).get_columns("comercios")
    }


def upgrade(connection) -> str:
    if column_exists(connection):
        return "already_exists"

    connection.execute(
        text(
            "ALTER TABLE comercios "
            "ADD COLUMN mostrar_direccion_publicamente "
            "BOOLEAN NOT NULL DEFAULT TRUE"
        )
    )
    return "created"


def downgrade(connection) -> str:
    if not column_exists(connection):
        return "already_absent"

    connection.execute(
        text(
            "ALTER TABLE comercios "
            "DROP COLUMN mostrar_direccion_publicamente"
        )
    )
    return "dropped"


def apply_migration(action: str | None) -> str:
    if action not in {"upgrade", "downgrade"}:
        raise LocationVisibilityMigrationError(
            f"{ACTION_ENV} debe ser 'upgrade' o 'downgrade'."
        )

    with engine.begin() as connection:
        if action == "upgrade":
            return upgrade(connection)
        return downgrade(connection)


def main() -> int:
    print(f"Destino: {safe_database_target()}")
    with engine.connect() as connection:
        exists = column_exists(connection)
    print(f"Columna existente: {'si' if exists else 'no'}")

    action = os.environ.get(ACTION_ENV)
    if action is None:
        print("Modo auditoria: esquema no modificado.")
        print(f"Para aplicar, definir {ACTION_ENV}=upgrade o downgrade.")
        return 0

    try:
        result = apply_migration(action)
    except LocationVisibilityMigrationError as exc:
        print(f"MIGRACION FALLIDA: {exc}", file=sys.stderr)
        return 2

    print(f"MIGRACION OK: {result}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
