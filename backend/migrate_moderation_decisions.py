"""Evolucion idempotente para decisiones y visibilidad de moderacion."""

import os
import sys

from sqlalchemy import inspect, text
from sqlalchemy.exc import SQLAlchemyError

from app.core.database import Base, engine
from app.core.model_registry import import_all_models

ACTION_ENV = "FEEDGO_MODERATION_DECISIONS_MIGRATION"
DECISIONS_TABLE = "moderation_decisions"

import_all_models()


def safe_database_target() -> str:
    return f"{engine.dialect.name}://{engine.url.host or '<sin-host>'}/{engine.url.database or '<sin-base>'}"


def _columns(connection, table: str) -> set[str]:
    return {column["name"] for column in inspect(connection).get_columns(table)}


def _add_column(connection, table: str, name: str, ddl: str) -> bool:
    if name in _columns(connection, table):
        return False
    connection.execute(text(f"ALTER TABLE {table} ADD COLUMN {name} {ddl}"))
    return True


def upgrade(connection) -> list[str]:
    changes: list[str] = []
    if _add_column(connection, "contenido_denuncias", "version", "INTEGER NOT NULL DEFAULT 1"):
        changes.append("contenido_denuncias.version")
    if _add_column(connection, "contenido_denuncias", "resuelta_en", "DATETIME NULL"):
        changes.append("contenido_denuncias.resuelta_en")

    if DECISIONS_TABLE not in inspect(connection).get_table_names():
        Base.metadata.tables[DECISIONS_TABLE].create(bind=connection, checkfirst=True)
        changes.append(DECISIONS_TABLE)

    for table in ("comercios", "publicaciones", "historias"):
        definitions = {
            "moderation_hidden": "BOOLEAN NOT NULL DEFAULT 0",
            "moderation_revision": "INTEGER NOT NULL DEFAULT 0",
            "moderation_hidden_by_decision_id": "INTEGER NULL",
            "moderation_updated_at": "DATETIME NULL",
        }
        for name, ddl in definitions.items():
            if _add_column(connection, table, name, ddl):
                changes.append(f"{table}.{name}")

        fk_name = f"fk_{table}_moderation_hidden_decision"
        foreign_keys = {fk.get("name") for fk in inspect(connection).get_foreign_keys(table)}
        if fk_name not in foreign_keys:
            connection.execute(text(
                f"ALTER TABLE {table} ADD CONSTRAINT {fk_name} "
                "FOREIGN KEY (moderation_hidden_by_decision_id) "
                "REFERENCES moderation_decisions(id) ON DELETE RESTRICT"
            ))
            changes.append(fk_name)
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
