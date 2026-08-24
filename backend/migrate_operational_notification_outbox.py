"""Evolucion idempotente para la outbox de avisos administrativos."""

import os
import sys

from sqlalchemy import inspect
from sqlalchemy.exc import SQLAlchemyError

from app.core.database import Base, engine
from app.core.model_registry import import_all_models

ACTION_ENV = "FEEDGO_OPERATIONAL_NOTIFICATION_OUTBOX_MIGRATION"
TABLE_NAME = "operational_notification_outbox"

import_all_models()


def safe_database_target() -> str:
    return f"{engine.dialect.name}://{engine.url.host or '<sin-host>'}/{engine.url.database or '<sin-base>'}"


def upgrade(connection) -> list[str]:
    changes: list[str] = []
    inspector = inspect(connection)
    if TABLE_NAME not in set(inspector.get_table_names()):
        Base.metadata.tables[TABLE_NAME].create(bind=connection, checkfirst=True)
        return [TABLE_NAME]

    columns = {column["name"] for column in inspector.get_columns(TABLE_NAME)}
    additions = {
        "lease_expires_at": "DATETIME NULL",
        "claimed_by": "VARCHAR(80) NULL",
        "suppressed_at": "DATETIME NULL",
        "suppressed_by": "VARCHAR(80) NULL",
        "suppression_reason": "VARCHAR(80) NULL",
    }
    for name, ddl in additions.items():
        if name not in columns:
            connection.exec_driver_sql(f"ALTER TABLE {TABLE_NAME} ADD COLUMN {name} {ddl}")
            changes.append(name)

    inspector = inspect(connection)
    indexes = {index["name"] for index in inspector.get_indexes(TABLE_NAME)}
    index_name = "ix_operational_notification_outbox_dispatch"
    if index_name not in indexes:
        connection.exec_driver_sql(
            f"CREATE INDEX {index_name} ON {TABLE_NAME} "
            "(status, next_attempt_at, lease_expires_at, id)"
        )
        changes.append(index_name)
    return changes


def apply_migration(action: str | None) -> list[str]:
    if action != "upgrade":
        raise ValueError(f"{ACTION_ENV} debe ser 'upgrade'.")
    with engine.begin() as connection:
        return upgrade(connection)


def main() -> int:
    print(f"Destino: {safe_database_target()}")
    action = os.environ.get(ACTION_ENV)
    if action is None:
        print("Modo auditoria: esquema no modificado.")
        print(f"Para aplicar, definir {ACTION_ENV}=upgrade.")
        return 0
    try:
        changes = apply_migration(action)
    except (SQLAlchemyError, ValueError) as exc:
        print(f"MIGRACION FALLIDA: {exc}", file=sys.stderr)
        return 2
    print("MIGRACION OK: " + (", ".join(changes) if changes else "already_exists"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
