"""Migracion aditiva de ET99.8-E1 para el purpose OAuth de reautenticacion."""

from __future__ import annotations

import os

from sqlalchemy import inspect

from app.core.database import engine


ACTION_ENV = "FEEDGO_GOOGLE_REAUTH_MIGRATION"
TABLE = "oauth_authorization_transactions"
PURPOSE_CHECK = "ck_oauth_authorization_transactions_purpose"
CORRELATION_CHECK = "ck_oauth_authorization_transactions_correlation"


class GoogleReauthMigrationError(RuntimeError):
    pass


def _replace_check(connection, name: str, expression: str) -> bool:
    checks = {
        item.get("name"): item.get("sqltext", "")
        for item in inspect(connection).get_check_constraints(TABLE)
    }
    current = checks.get(name, "")
    if "reauth" in current:
        return False
    if connection.dialect.name != "mysql":
        raise GoogleReauthMigrationError("google_reauth_constraint_incompatible")
    # MySQL hace commit implícito en DDL. Si una ejecución anterior quedó
    # entre DROP y ADD, la reejecución recupera agregando el check faltante.
    if name in checks:
        connection.exec_driver_sql(f"ALTER TABLE {TABLE} DROP CHECK {name}")
    connection.exec_driver_sql(
        f"ALTER TABLE {TABLE} ADD CONSTRAINT {name} CHECK ({expression})"
    )
    return True


def upgrade(connection) -> dict[str, object]:
    changes: list[str] = []
    if _replace_check(connection, PURPOSE_CHECK, "purpose IN ('signup', 'login', 'link', 'reauth')"):
        changes.append(f"{PURPOSE_CHECK}.reauth")
    correlation = "(purpose IN ('link', 'reauth') AND usuario_id IS NOT NULL AND feedgo_session_id IS NOT NULL) OR (purpose IN ('signup', 'login') AND usuario_id IS NULL AND feedgo_session_id IS NULL)"
    if _replace_check(connection, CORRELATION_CHECK, correlation):
        changes.append(f"{CORRELATION_CHECK}.reauth")
    return {"changes": changes}


def apply_migration(action: str | None) -> dict[str, object]:
    if action != "upgrade":
        raise ValueError(f"{ACTION_ENV} debe ser 'upgrade'.")
    with engine.begin() as connection:
        return upgrade(connection)


if __name__ == "__main__":
    print(apply_migration(os.environ.get(ACTION_ENV)))
