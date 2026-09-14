"""Migracion aditiva e idempotente del telefono privado de ET99.5-A."""

from __future__ import annotations

import os
import sys

from sqlalchemy import inspect
from sqlalchemy.exc import SQLAlchemyError

from app.core.database import engine


ACTION_ENV = "FEEDGO_PRIVATE_PHONE_MIGRATION"
USER_COLUMN_DDL = {
    "telefono_e164": "VARCHAR(16) NULL",
    "telefono_verified_at": "DATETIME NULL",
    "telefono_verification_source": "VARCHAR(32) NULL",
}
PHONE_UNIQUE = "ux_usuarios_telefono_e164"
VERIFICATION_PAIR_CHECK = "ck_usuarios_telefono_verification_pair"


class PrivatePhoneMigrationError(RuntimeError):
    """El schema no permite aplicar la expansion de forma segura."""


def safe_database_target() -> str:
    host = engine.url.host or "<sin-host>"
    database = engine.url.database or "<sin-base>"
    return f"{engine.dialect.name}://{host}/{database}"


def preflight(connection) -> dict[str, object]:
    inspector = inspect(connection)
    if "usuarios" not in inspector.get_table_names():
        raise PrivatePhoneMigrationError("Falta la tabla usuarios")
    columns = {column["name"] for column in inspector.get_columns("usuarios")}
    phone_columns = set(USER_COLUMN_DDL) & columns
    return {
        "telefono_columnas_presentes": sorted(phone_columns),
        "usuarios_modificados": 0,
    }


def _add_columns(connection) -> list[str]:
    columns = {
        column["name"] for column in inspect(connection).get_columns("usuarios")
    }
    changes = []
    for name, ddl in USER_COLUMN_DDL.items():
        if name not in columns:
            connection.exec_driver_sql(f"ALTER TABLE usuarios ADD COLUMN {name} {ddl}")
            changes.append(f"usuarios.{name}")
    return changes


def _ensure_unique(connection) -> bool:
    inspector = inspect(connection)
    unique_columns = {
        tuple(index.get("column_names") or [])
        for index in inspector.get_indexes("usuarios")
        if index.get("unique")
    }
    unique_columns.update(
        tuple(constraint.get("column_names") or [])
        for constraint in inspector.get_unique_constraints("usuarios")
    )
    if ("telefono_e164",) in unique_columns:
        return False
    connection.exec_driver_sql(
        f"CREATE UNIQUE INDEX {PHONE_UNIQUE} ON usuarios (telefono_e164)"
    )
    return True


def _ensure_verification_pair_check(connection) -> bool:
    if connection.dialect.name == "sqlite":
        # SQLite no permite agregar CHECK a una tabla existente. La migracion
        # productiva es MySQL; SQLite conserva la validacion mediante metadata.
        return False
    names = {
        constraint.get("name")
        for constraint in inspect(connection).get_check_constraints("usuarios")
    }
    if VERIFICATION_PAIR_CHECK in names:
        return False
    connection.exec_driver_sql(
        f"ALTER TABLE usuarios ADD CONSTRAINT {VERIFICATION_PAIR_CHECK} CHECK ("
        "(telefono_verified_at IS NULL AND telefono_verification_source IS NULL) "
        "OR (telefono_verified_at IS NOT NULL AND "
        "telefono_verification_source IS NOT NULL))"
    )
    return True


def _validate_verification_pairs(connection) -> None:
    inconsistent = connection.exec_driver_sql(
        "SELECT COUNT(*) FROM usuarios WHERE "
        "(telefono_verified_at IS NULL) <> "
        "(telefono_verification_source IS NULL)"
    ).scalar_one()
    if inconsistent:
        raise PrivatePhoneMigrationError(
            "Existen estados telefonicos parciales incompatibles"
        )


def upgrade(connection) -> dict[str, object]:
    audit = preflight(connection)
    changes = _add_columns(connection)
    _validate_verification_pairs(connection)
    if _ensure_unique(connection):
        changes.append(PHONE_UNIQUE)
    if _ensure_verification_pair_check(connection):
        changes.append(VERIFICATION_PAIR_CHECK)
    return {"preflight": audit, "changes": changes, "backfill": 0}


def apply_migration(action: str | None) -> dict[str, object]:
    if action != "upgrade":
        raise ValueError(f"{ACTION_ENV} debe ser 'upgrade'.")
    with engine.begin() as connection:
        return upgrade(connection)


def main() -> int:
    print(f"Destino: {safe_database_target()}")
    action = os.environ.get(ACTION_ENV)
    try:
        if action is None:
            with engine.connect() as connection:
                result = preflight(connection)
            print(f"Preflight OK: {result}")
            print("Modo auditoria: esquema y datos no modificados.")
            print(f"Para aplicar, definir {ACTION_ENV}=upgrade.")
            return 0
        result = apply_migration(action)
    except (PrivatePhoneMigrationError, SQLAlchemyError, ValueError) as exc:
        print(f"MIGRACION FALLIDA: {exc}", file=sys.stderr)
        return 2
    print(f"MIGRACION OK: {result}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
