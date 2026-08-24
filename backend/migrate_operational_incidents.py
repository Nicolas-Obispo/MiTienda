"""Evolucion idempotente para el expediente durable de incidentes."""

import os
import sys

from sqlalchemy import inspect
from sqlalchemy.exc import SQLAlchemyError

from app.core.database import Base, engine
from app.core.model_registry import import_all_models

ACTION_ENV = "FEEDGO_OPERATIONAL_INCIDENTS_MIGRATION"
TABLES = ("operational_incidents", "operational_incident_events")

import_all_models()


def safe_database_target() -> str:
    return f"{engine.dialect.name}://{engine.url.host or '<sin-host>'}/{engine.url.database or '<sin-base>'}"


def upgrade(connection) -> list[str]:
    changes = []
    existing = set(inspect(connection).get_table_names())
    for table_name in TABLES:
        if table_name not in existing:
            Base.metadata.tables[table_name].create(bind=connection, checkfirst=True)
            changes.append(table_name)
            existing.add(table_name)
    return changes


def apply_migration(action: str | None) -> list[str]:
    if action != "upgrade": raise ValueError(f"{ACTION_ENV} debe ser 'upgrade'.")
    with engine.begin() as connection: return upgrade(connection)


def main() -> int:
    print(f"Destino: {safe_database_target()}")
    action = os.environ.get(ACTION_ENV)
    if action is None:
        print("Modo auditoria: esquema no modificado.")
        print(f"Para aplicar, definir {ACTION_ENV}=upgrade.")
        return 0
    try: changes = apply_migration(action)
    except (SQLAlchemyError, ValueError) as exc:
        print(f"MIGRACION FALLIDA: {exc}", file=sys.stderr); return 2
    print("MIGRACION OK: " + (", ".join(changes) if changes else "already_exists"))
    return 0


if __name__ == "__main__": raise SystemExit(main())
