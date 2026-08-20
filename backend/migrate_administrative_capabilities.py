"""Evolucion aditiva e idempotente para capacidades administrativas.

Importar este modulo no modifica la base. Sin la variable de accion, la
ejecucion es solamente de auditoria.
"""

import os
import sys

from sqlalchemy import inspect
from sqlalchemy.exc import SQLAlchemyError

from app.core.database import Base, engine
from app.core.model_registry import import_all_models

TABLE_NAME = "administrative_capability_events"
ACTION_ENV = "FEEDGO_ADMIN_CAPABILITIES_MIGRATION"

import_all_models()


def safe_database_target() -> str:
    host = engine.url.host or "<sin-host>"
    database = engine.url.database or "<sin-base>"
    return f"{engine.dialect.name}://{host}/{database}"


def table_exists(connection) -> bool:
    return TABLE_NAME in inspect(connection).get_table_names()


def upgrade(connection) -> str:
    if table_exists(connection):
        return "already_exists"
    Base.metadata.tables[TABLE_NAME].create(bind=connection, checkfirst=True)
    return "created"


def apply_migration(action: str | None) -> str:
    if action != "upgrade":
        raise ValueError(f"{ACTION_ENV} debe ser 'upgrade'.")
    with engine.begin() as connection:
        return upgrade(connection)


def main() -> int:
    print(f"Destino: {safe_database_target()}")
    with engine.connect() as connection:
        exists = table_exists(connection)
    print(f"Tabla existente: {'si' if exists else 'no'}")

    action = os.environ.get(ACTION_ENV)
    if action is None:
        print("Modo auditoria: esquema no modificado.")
        print(f"Para aplicar, definir {ACTION_ENV}=upgrade.")
        return 0

    try:
        result = apply_migration(action)
    except (SQLAlchemyError, ValueError) as exc:
        print(f"MIGRACION FALLIDA: {exc}", file=sys.stderr)
        return 2
    print(f"MIGRACION OK: {result}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
