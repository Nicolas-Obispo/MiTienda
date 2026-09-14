"""Migracion aditiva e idempotente para la fundacion de ETAPA 99.3-A.

Importar este modulo no modifica la base. La aplicacion exige un flag explicito
y no crea tokens, limites, evidencia de verificacion ni backfills.
"""

from __future__ import annotations

import os
import sys

from sqlalchemy import inspect
from sqlalchemy.exc import SQLAlchemyError

from app.core.database import Base, engine
from app.core.model_registry import import_all_models

ACTION_ENV = "FEEDGO_ACCOUNT_ACTION_FOUNDATION_MIGRATION"
NEW_TABLES = (
    "account_action_tokens",
    "account_action_rate_limits",
)

import_all_models()


class AccountActionMigrationPreflightError(RuntimeError):
    """El schema existente no permite una expansion automatica segura."""


def safe_database_target() -> str:
    host = engine.url.host or "<sin-host>"
    database = engine.url.database or "<sin-base>"
    return f"{engine.dialect.name}://{host}/{database}"


def _expected_columns(table_name: str) -> set[str]:
    return set(Base.metadata.tables[table_name].columns.keys())


def preflight(connection) -> dict[str, object]:
    """Comprueba dependencias y tablas parciales sin escribir."""

    inspector = inspect(connection)
    existing = set(inspector.get_table_names())
    if "usuarios" not in existing:
        raise AccountActionMigrationPreflightError("Falta la tabla usuarios")

    for table_name in NEW_TABLES:
        if table_name not in existing:
            continue
        actual = {column["name"] for column in inspector.get_columns(table_name)}
        expected = _expected_columns(table_name)
        if actual != expected:
            raise AccountActionMigrationPreflightError(
                f"Schema parcial incompatible en {table_name}: "
                f"faltantes={sorted(expected - actual)}, "
                f"extra={sorted(actual - expected)}"
            )

        model = Base.metadata.tables[table_name]
        required_indexes = {index.name for index in model.indexes if index.name}
        actual_indexes = {
            index["name"] for index in inspector.get_indexes(table_name)
        }
        missing_indexes = required_indexes - actual_indexes
        required_uniques = {
            constraint.name
            for constraint in model.constraints
            if constraint.__class__.__name__ == "UniqueConstraint"
            and constraint.name
        }
        actual_uniques = {
            constraint.get("name")
            for constraint in inspector.get_unique_constraints(table_name)
        }
        missing_uniques = required_uniques - actual_uniques
        required_checks = {
            constraint.name
            for constraint in model.constraints
            if constraint.__class__.__name__ == "CheckConstraint"
            and constraint.name
        }
        actual_checks = {
            constraint.get("name")
            for constraint in inspector.get_check_constraints(table_name)
        }
        missing_checks = required_checks - actual_checks
        if missing_indexes or missing_uniques or missing_checks:
            raise AccountActionMigrationPreflightError(
                f"Constraints parciales incompatibles en {table_name}: "
                f"indices_faltantes={sorted(missing_indexes)}, "
                f"uniques_faltantes={sorted(missing_uniques)}, "
                f"checks_faltantes={sorted(missing_checks)}"
            )

    return {
        "usuarios_presente": True,
        "tablas_presentes": sorted(existing.intersection(NEW_TABLES)),
        "tablas_pendientes": sorted(set(NEW_TABLES) - existing),
    }


def upgrade(connection) -> dict[str, object]:
    audit = preflight(connection)
    existing = set(inspect(connection).get_table_names())
    changes: list[str] = []
    for table_name in NEW_TABLES:
        if table_name not in existing:
            Base.metadata.tables[table_name].create(bind=connection, checkfirst=True)
            changes.append(table_name)
    return {"preflight": audit, "changes": changes, "backfill": {}}


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
            print("Modo auditoria: schema y datos no modificados.")
            print(f"Para aplicar, definir {ACTION_ENV}=upgrade.")
            return 0
        result = apply_migration(action)
    except (AccountActionMigrationPreflightError, SQLAlchemyError, ValueError) as exc:
        print(f"MIGRACION FALLIDA: {exc}", file=sys.stderr)
        return 2
    print(f"MIGRACION OK: {result}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
