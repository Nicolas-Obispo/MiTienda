"""Migracion idempotente del indice de bandeja administrativa de denuncias."""

import os
import sys

from sqlalchemy import inspect, text
from sqlalchemy.exc import SQLAlchemyError

from app.core.database import engine

TABLE_NAME = "contenido_denuncias"
INDEX_NAME = "ix_contenido_denuncias_estado_creado_id"
ACTION_ENV = "FEEDGO_MODERATION_INBOX_INDEX_MIGRATION"


def safe_database_target() -> str:
    host = engine.url.host or "<sin-host>"
    database = engine.url.database or "<sin-base>"
    return f"{engine.dialect.name}://{host}/{database}"


def index_exists(connection) -> bool:
    return INDEX_NAME in {
        index["name"] for index in inspect(connection).get_indexes(TABLE_NAME)
    }


def upgrade(connection) -> str:
    if index_exists(connection):
        return "already_exists"
    connection.execute(
        text(
            f"CREATE INDEX {INDEX_NAME} "
            f"ON {TABLE_NAME} (estado, creado_en, id)"
        )
    )
    return "created"


def apply_migration(action: str | None) -> str:
    if action != "upgrade":
        raise ValueError(f"{ACTION_ENV} debe ser 'upgrade'.")
    with engine.begin() as connection:
        return upgrade(connection)


def main() -> int:
    print(f"Destino: {safe_database_target()}")
    with engine.connect() as connection:
        exists = index_exists(connection)
    print(f"Indice existente: {'si' if exists else 'no'}")

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
