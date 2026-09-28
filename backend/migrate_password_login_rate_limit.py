"""Expande de forma aditiva el owner persistente para login password.

No crea tablas de identidad ni modifica usuarios, credenciales o hashes.
"""

from __future__ import annotations

import os
import re

from sqlalchemy import inspect

from app.core.database import engine


ACTION_ENV = "FEEDGO_PASSWORD_LOGIN_RATE_LIMIT_MIGRATION"
TABLE = "account_action_rate_limits"
CHECK_NAME = "ck_account_action_rate_limits_action"
INDEX_NAME = "ix_account_action_rate_limits_action_updated"

FOUNDATION_ACTIONS = frozenset(
    {"email_verification", "password_reset", "current_password"}
)
PHONE_ACTIONS = FOUNDATION_ACTIONS | {"phone_verification"}
GOOGLE_ACTIONS = PHONE_ACTIONS | {"google_oauth"}
DESIRED_ACTIONS = GOOGLE_ACTIONS | {"password_login"}
KNOWN_ACTION_SETS = frozenset(
    {FOUNDATION_ACTIONS, PHONE_ACTIONS, GOOGLE_ACTIONS, DESIRED_ACTIONS}
)


class PasswordLoginRateLimitMigrationError(RuntimeError):
    pass


def _actions_from_check(expression: str) -> frozenset[str]:
    return frozenset(re.findall(r"'([^']+)'", expression or ""))


def _existing_actions(connection) -> frozenset[str]:
    values = connection.exec_driver_sql(
        "SELECT DISTINCT action FROM account_action_rate_limits"
    ).scalars()
    return frozenset(value for value in values if value is not None)


def _ensure_action_check(connection, changes: list[str]) -> None:
    inspector = inspect(connection)
    checks = {
        item.get("name"): item.get("sqltext", "")
        for item in inspector.get_check_constraints(TABLE)
    }
    expression = checks.get(CHECK_NAME)
    if expression is None:
        if any("action" in str(sqltext).lower() for sqltext in checks.values()):
            raise PasswordLoginRateLimitMigrationError(
                "account_action_rate_limit_check_unexpected"
            )
        if not _existing_actions(connection).issubset(DESIRED_ACTIONS):
            raise PasswordLoginRateLimitMigrationError(
                "account_action_rate_limit_rows_incompatible"
            )
        connection.exec_driver_sql(
            "ALTER TABLE account_action_rate_limits ADD CONSTRAINT "
            "ck_account_action_rate_limits_action CHECK (action IN "
            "('email_verification','password_reset','current_password',"
            "'phone_verification','google_oauth','password_login'))"
        )
        changes.append(CHECK_NAME)
        return

    actions = _actions_from_check(expression)
    if actions == DESIRED_ACTIONS:
        return
    if actions not in KNOWN_ACTION_SETS:
        raise PasswordLoginRateLimitMigrationError(
            "account_action_rate_limit_check_unexpected"
        )
    if not _existing_actions(connection).issubset(DESIRED_ACTIONS):
        raise PasswordLoginRateLimitMigrationError(
            "account_action_rate_limit_rows_incompatible"
        )
    connection.exec_driver_sql(
        "ALTER TABLE account_action_rate_limits "
        "DROP CHECK ck_account_action_rate_limits_action, "
        "ADD CONSTRAINT ck_account_action_rate_limits_action CHECK (action IN "
        "('email_verification','password_reset','current_password',"
        "'phone_verification','google_oauth','password_login'))"
    )
    changes.append(CHECK_NAME)


def _ensure_cleanup_index(connection, changes: list[str]) -> None:
    indexes = inspect(connection).get_indexes(TABLE)
    for item in indexes:
        columns = tuple(item.get("column_names") or ())
        if columns == ("action", "updated_at"):
            return
        if item.get("name") == INDEX_NAME:
            raise PasswordLoginRateLimitMigrationError(
                "account_action_rate_limit_cleanup_index_unexpected"
            )
    connection.exec_driver_sql(
        "CREATE INDEX ix_account_action_rate_limits_action_updated "
        "ON account_action_rate_limits (action, updated_at)"
    )
    changes.append(INDEX_NAME)


def upgrade(connection) -> dict[str, object]:
    if connection.dialect.name != "mysql":
        raise PasswordLoginRateLimitMigrationError(
            "password_login_rate_limit_migration_requires_mysql"
        )
    inspector = inspect(connection)
    if TABLE not in inspector.get_table_names():
        raise PasswordLoginRateLimitMigrationError(
            "account_action_rate_limits_missing"
        )
    columns = {column["name"] for column in inspector.get_columns(TABLE)}
    required = {
        "id",
        "action",
        "subject_digest",
        "window_started_at",
        "attempt_count",
        "blocked_until",
        "updated_at",
    }
    if not required.issubset(columns):
        raise PasswordLoginRateLimitMigrationError(
            "account_action_rate_limits_schema_incompatible"
        )

    changes: list[str] = []
    _ensure_action_check(connection, changes)
    _ensure_cleanup_index(connection, changes)
    return {"changes": changes}


def apply_migration(action: str | None) -> dict[str, object]:
    if action != "upgrade":
        raise ValueError(f"{ACTION_ENV} debe ser 'upgrade'.")
    with engine.begin() as connection:
        return upgrade(connection)


if __name__ == "__main__":
    print(apply_migration(os.environ.get(ACTION_ENV)))
