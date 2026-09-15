"""Migracion aditiva de ET99.8-C para entrega one-use de sesion OAuth."""

from __future__ import annotations

import os

from sqlalchemy import inspect

from app.core.database import Base, engine
from app.core.model_registry import import_all_models
import migrate_google_identity_foundation as foundation


ACTION_ENV = "FEEDGO_GOOGLE_OIDC_MIGRATION"
RESULT_TABLE = "oauth_session_delivery_handles"
RATE_LIMIT_TABLE = "account_action_rate_limits"

import_all_models()


class GoogleOidcMigrationError(RuntimeError):
    pass


def _ensure_result_table(connection, changes: list[str]) -> None:
    tables = set(inspect(connection).get_table_names())
    if RESULT_TABLE not in tables:
        Base.metadata.tables[RESULT_TABLE].create(bind=connection, checkfirst=True)
        changes.append(RESULT_TABLE)
        return

    expected_columns = set(Base.metadata.tables[RESULT_TABLE].columns.keys())
    actual_columns = {
        column["name"] for column in inspect(connection).get_columns(RESULT_TABLE)
    }
    schema_is_compatible = actual_columns == expected_columns
    inspector = inspect(connection)
    unique_sets = {
        tuple(item.get("column_names") or [])
        for item in inspector.get_unique_constraints(RESULT_TABLE)
    }
    unique_sets.update(
        tuple(item.get("column_names") or [])
        for item in inspector.get_indexes(RESULT_TABLE)
        if item.get("unique")
    )
    expected_uniques = {("handle_digest",), ("transaction_id",)}
    check_names = {
        item.get("name") for item in inspector.get_check_constraints(RESULT_TABLE)
    }
    expected_checks = {
        constraint.name
        for constraint in Base.metadata.tables[RESULT_TABLE].constraints
        if constraint.__class__.__name__ == "CheckConstraint"
    }
    foreign_keys = inspector.get_foreign_keys(RESULT_TABLE)
    referenced_tables = {item.get("referred_table") for item in foreign_keys}
    constraints_are_compatible = (
        expected_uniques.issubset(unique_sets)
        and expected_checks.issubset(check_names)
        and {"oauth_authorization_transactions", "usuarios", "feedgo_sessions"}.issubset(
            referenced_tables
        )
    )
    if schema_is_compatible and constraints_are_compatible:
        return

    # MySQL puede dejar una tabla parcial tras un DDL interrumpido. Sólo se
    # reconstruye cuando está vacía: nunca se descartan resultados OAuth.
    if connection.dialect.name != "mysql":
        raise GoogleOidcMigrationError("oauth_session_delivery_schema_incompatible")
    row_count = connection.exec_driver_sql(
        "SELECT COUNT(*) FROM oauth_session_delivery_handles"
    ).scalar_one()
    if row_count:
        raise GoogleOidcMigrationError("oauth_session_delivery_schema_incompatible")
    connection.exec_driver_sql("DROP TABLE oauth_session_delivery_handles")
    Base.metadata.tables[RESULT_TABLE].create(bind=connection, checkfirst=True)
    changes.append(f"{RESULT_TABLE}.recovered")


def _ensure_google_oauth_rate_limit_action(connection, changes: list[str]) -> None:
    checks = {
        item.get("name"): item.get("sqltext", "")
        for item in inspect(connection).get_check_constraints(RATE_LIMIT_TABLE)
    }
    expression = checks.get("ck_account_action_rate_limits_action", "")
    if "google_oauth" in expression:
        return
    if connection.dialect.name != "mysql":
        raise GoogleOidcMigrationError("google_oauth_rate_limit_check_requires_mysql")
    if "ck_account_action_rate_limits_action" not in checks:
        raise GoogleOidcMigrationError("account_action_rate_limit_check_missing")
    connection.exec_driver_sql(
        "ALTER TABLE account_action_rate_limits "
        "DROP CHECK ck_account_action_rate_limits_action"
    )
    connection.exec_driver_sql(
        "ALTER TABLE account_action_rate_limits ADD CONSTRAINT "
        "ck_account_action_rate_limits_action CHECK (action IN "
        "('email_verification','password_reset','current_password',"
        "'phone_verification','google_oauth'))"
    )
    changes.append("ck_account_action_rate_limits_action.google_oauth")


def upgrade(connection) -> dict[str, object]:
    foundation_result = foundation.upgrade(connection)
    changes = list(foundation_result["changes"])
    _ensure_google_oauth_rate_limit_action(connection, changes)
    _ensure_result_table(connection, changes)
    return {"changes": changes}


def apply_migration(action: str | None) -> dict[str, object]:
    if action != "upgrade":
        raise ValueError(f"{ACTION_ENV} debe ser 'upgrade'.")
    with engine.begin() as connection:
        return upgrade(connection)


if __name__ == "__main__":
    print(apply_migration(os.environ.get(ACTION_ENV)))
