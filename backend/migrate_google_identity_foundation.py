"""Migracion aditiva de ET99.8-B: Google-only y transacciones OAuth one-use."""

from __future__ import annotations

import os

from sqlalchemy import inspect

from app.core.database import Base, engine
from app.core.model_registry import import_all_models


ACTION_ENV = "FEEDGO_GOOGLE_IDENTITY_FOUNDATION_MIGRATION"
USER_TABLE = "usuarios"
TRANSACTION_TABLE = "oauth_authorization_transactions"
EXTERNAL_IDENTITY_TABLE = "external_identities"
EXTERNAL_IDENTITY_UNIQUE = "uq_external_identities_usuario_provider"

TRANSACTION_COLUMNS = {
    "provider": "VARCHAR(32) NOT NULL",
    "purpose": "VARCHAR(32) NOT NULL",
    "state_digest": "VARCHAR(64) NOT NULL",
    "nonce_digest": "VARCHAR(64) NOT NULL",
    "pkce_verifier": "VARCHAR(128) NULL",
    "pkce_challenge": "VARCHAR(128) NOT NULL",
    "usuario_id": "INTEGER NULL",
    "feedgo_session_id": "VARCHAR(64) NULL",
    "return_to": "VARCHAR(512) NULL",
    "legal_document_set_digest": "VARCHAR(64) NULL",
    "legal_accepted_at": "DATETIME NULL",
    "created_at": "DATETIME NOT NULL",
    "expires_at": "DATETIME NOT NULL",
    "consumed_at": "DATETIME NULL",
    "invalidated_at": "DATETIME NULL",
    "invalidation_reason": "VARCHAR(32) NULL",
}
TRANSACTION_UNIQUES = {
    "uq_oauth_authorization_transactions_state": ("state_digest",),
    "uq_oauth_authorization_transactions_nonce": ("nonce_digest",),
}
TRANSACTION_INDEXES = {
    "ix_oauth_authorization_transactions_provider_purpose_expiry": (
        "provider", "purpose", "expires_at"
    ),
    "ix_oauth_authorization_transactions_user_purpose_created": (
        "usuario_id", "purpose", "created_at"
    ),
}
TRANSACTION_CHECKS = {
    "ck_oauth_authorization_transactions_purpose": "purpose IN ('signup', 'login', 'link', 'reauth')",
    "ck_oauth_authorization_transactions_expiry": "expires_at > created_at",
    "ck_oauth_authorization_transactions_terminal_state": (
        "NOT (consumed_at IS NOT NULL AND invalidated_at IS NOT NULL)"
    ),
    "ck_oauth_authorization_transactions_invalidation_reason": (
        "invalidation_reason IS NULL OR invalidation_reason IN "
        "('expired', 'superseded', 'administrative', 'session_invalid')"
    ),
    "ck_oauth_authorization_transactions_invalidation_pair": (
        "(invalidated_at IS NULL AND invalidation_reason IS NULL) OR "
        "(invalidated_at IS NOT NULL AND invalidation_reason IS NOT NULL)"
    ),
    "ck_oauth_authorization_transactions_pkce_lifecycle": (
        "(consumed_at IS NULL AND invalidated_at IS NULL AND pkce_verifier IS NOT NULL) "
        "OR ((consumed_at IS NOT NULL OR invalidated_at IS NOT NULL) "
        "AND pkce_verifier IS NULL)"
    ),
    "ck_oauth_authorization_transactions_correlation": (
        "(purpose IN ('link', 'reauth') AND usuario_id IS NOT NULL AND feedgo_session_id IS NOT NULL) "
        "OR (purpose IN ('signup', 'login') AND usuario_id IS NULL "
        "AND feedgo_session_id IS NULL)"
    ),
    "ck_oauth_authorization_transactions_legal_pair": (
        "(legal_document_set_digest IS NULL AND legal_accepted_at IS NULL) OR "
        "(purpose = 'signup' AND legal_document_set_digest IS NOT NULL "
        "AND legal_accepted_at IS NOT NULL)"
    ),
}

import_all_models()


class GoogleIdentityFoundationMigrationError(RuntimeError):
    pass


def _unique_column_sets(connection, table: str) -> set[tuple[str, ...]]:
    inspector = inspect(connection)
    values = {
        tuple(item.get("column_names") or [])
        for item in inspector.get_unique_constraints(table)
    }
    values.update(
        tuple(item.get("column_names") or [])
        for item in inspector.get_indexes(table)
        if item.get("unique")
    )
    return values


def _ensure_hashed_password_nullable(connection, changes: list[str]) -> None:
    columns = {item["name"]: item for item in inspect(connection).get_columns(USER_TABLE)}
    if "hashed_password" not in columns:
        raise GoogleIdentityFoundationMigrationError("usuarios_hashed_password_missing")
    if columns["hashed_password"].get("nullable"):
        return
    if connection.dialect.name == "mysql":
        connection.exec_driver_sql(
            "ALTER TABLE usuarios MODIFY COLUMN hashed_password VARCHAR(255) NULL"
        )
    elif connection.dialect.name == "postgresql":
        connection.exec_driver_sql(
            "ALTER TABLE usuarios ALTER COLUMN hashed_password DROP NOT NULL"
        )
    else:
        raise GoogleIdentityFoundationMigrationError(
            "hashed_password_nullable_requires_mysql_or_postgresql"
        )
    changes.append("usuarios.hashed_password_nullable")


def _ensure_external_identity_user_provider_unique(connection, changes: list[str]) -> None:
    if EXTERNAL_IDENTITY_TABLE not in inspect(connection).get_table_names():
        raise GoogleIdentityFoundationMigrationError("external_identities_missing")
    if ("usuario_id", "provider") in _unique_column_sets(connection, EXTERNAL_IDENTITY_TABLE):
        return
    duplicates = connection.exec_driver_sql(
        "SELECT usuario_id, provider FROM external_identities "
        "GROUP BY usuario_id, provider HAVING COUNT(*) > 1 LIMIT 1"
    ).first()
    if duplicates is not None:
        raise GoogleIdentityFoundationMigrationError(
            "external_identity_user_provider_duplicates"
        )
    connection.exec_driver_sql(
        "CREATE UNIQUE INDEX uq_external_identities_usuario_provider "
        "ON external_identities (usuario_id, provider)"
    )
    changes.append(EXTERNAL_IDENTITY_UNIQUE)


def _ensure_transaction_table(connection, changes: list[str]) -> None:
    if TRANSACTION_TABLE not in inspect(connection).get_table_names():
        Base.metadata.tables[TRANSACTION_TABLE].create(bind=connection, checkfirst=True)
        changes.append(TRANSACTION_TABLE)
        return
    if connection.dialect.name not in {"mysql", "postgresql"}:
        raise GoogleIdentityFoundationMigrationError(
            "oauth_authorization_transactions_partial_requires_mysql_or_postgresql"
        )
    inspector = inspect(connection)
    columns = {item["name"] for item in inspector.get_columns(TRANSACTION_TABLE)}
    if "id" not in columns:
        raise GoogleIdentityFoundationMigrationError("oauth_authorization_transactions_partial_base_incompatible")
    missing = [name for name in TRANSACTION_COLUMNS if name not in columns]
    if missing:
        row_count = connection.exec_driver_sql(
            "SELECT COUNT(*) FROM oauth_authorization_transactions"
        ).scalar_one()
        if row_count:
            raise GoogleIdentityFoundationMigrationError(
                "oauth_authorization_transactions_partial_data_incompatible"
            )
        for name in missing:
            connection.exec_driver_sql(
                f"ALTER TABLE oauth_authorization_transactions ADD COLUMN "
                f"{name} {TRANSACTION_COLUMNS[name]}"
            )
            changes.append(f"{TRANSACTION_TABLE}.{name}")

    refreshed_columns = {
        item["name"]: item
        for item in inspect(connection).get_columns(TRANSACTION_TABLE)
    }
    if not refreshed_columns["pkce_verifier"].get("nullable"):
        if connection.dialect.name == "mysql":
            connection.exec_driver_sql(
                "ALTER TABLE oauth_authorization_transactions MODIFY COLUMN "
                "pkce_verifier VARCHAR(128) NULL"
            )
        else:
            connection.exec_driver_sql(
                "ALTER TABLE oauth_authorization_transactions ALTER COLUMN "
                "pkce_verifier DROP NOT NULL"
            )
        changes.append("oauth_authorization_transactions.pkce_verifier_nullable")

    cleared = connection.exec_driver_sql(
        "UPDATE oauth_authorization_transactions SET pkce_verifier = NULL "
        "WHERE pkce_verifier IS NOT NULL "
        "AND (consumed_at IS NOT NULL OR invalidated_at IS NOT NULL)"
    ).rowcount
    if cleared:
        changes.append("oauth_authorization_transactions.terminal_pkce_verifiers_cleared")
    invalid_rows = connection.exec_driver_sql(
        "SELECT COUNT(*) FROM oauth_authorization_transactions WHERE "
        "purpose NOT IN ('signup', 'login', 'link', 'reauth') OR expires_at <= created_at OR "
        "(consumed_at IS NOT NULL AND invalidated_at IS NOT NULL) OR "
        "((invalidated_at IS NULL) <> (invalidation_reason IS NULL)) OR "
        "(consumed_at IS NULL AND invalidated_at IS NULL AND pkce_verifier IS NULL) OR "
        "(purpose IN ('link', 'reauth') AND (usuario_id IS NULL OR feedgo_session_id IS NULL)) OR "
        "(purpose IN ('signup', 'login') AND "
        "(usuario_id IS NOT NULL OR feedgo_session_id IS NOT NULL))"
    ).scalar_one()
    if invalid_rows:
        raise GoogleIdentityFoundationMigrationError(
            "oauth_authorization_transactions_existing_rows_incompatible"
        )

    inspector = inspect(connection)
    foreign_keys = inspector.get_foreign_keys(TRANSACTION_TABLE)
    has_user_fk = any(
        item.get("constrained_columns") == ["usuario_id"]
        and item.get("referred_table") == USER_TABLE
        and item.get("referred_columns") == ["id"]
        for item in foreign_keys
    )
    if not has_user_fk:
        connection.exec_driver_sql(
            "ALTER TABLE oauth_authorization_transactions ADD CONSTRAINT "
            "fk_oauth_authorization_transactions_usuario FOREIGN KEY (usuario_id) "
            "REFERENCES usuarios(id) ON DELETE CASCADE"
        )
        changes.append("fk_oauth_authorization_transactions_usuario")
    has_session_fk = any(
        item.get("constrained_columns") == ["feedgo_session_id"]
        and item.get("referred_table") == "feedgo_sessions"
        and item.get("referred_columns") == ["id"]
        for item in foreign_keys
    )
    if not has_session_fk:
        connection.exec_driver_sql(
            "ALTER TABLE oauth_authorization_transactions ADD CONSTRAINT "
            "fk_oauth_authorization_transactions_feedgo_session FOREIGN KEY "
            "(feedgo_session_id) REFERENCES feedgo_sessions(id) ON DELETE CASCADE"
        )
        changes.append("fk_oauth_authorization_transactions_feedgo_session")

    uniques = _unique_column_sets(connection, TRANSACTION_TABLE)
    for name, fields in TRANSACTION_UNIQUES.items():
        if fields not in uniques:
            connection.exec_driver_sql(
                f"CREATE UNIQUE INDEX {name} ON {TRANSACTION_TABLE} "
                f"({', '.join(fields)})"
            )
            changes.append(name)
    indexes = {
        item.get("name"): tuple(item.get("column_names") or [])
        for item in inspect(connection).get_indexes(TRANSACTION_TABLE)
    }
    for name, fields in TRANSACTION_INDEXES.items():
        if indexes.get(name) != fields:
            connection.exec_driver_sql(
                f"CREATE INDEX {name} ON {TRANSACTION_TABLE} ({', '.join(fields)})"
            )
            changes.append(name)
    existing_checks = {
        item.get("name")
        for item in inspect(connection).get_check_constraints(TRANSACTION_TABLE)
    }
    for name, expression in TRANSACTION_CHECKS.items():
        if name not in existing_checks:
            connection.exec_driver_sql(
                f"ALTER TABLE {TRANSACTION_TABLE} ADD CONSTRAINT {name} "
                f"CHECK ({expression})"
            )
            changes.append(name)


def upgrade(connection) -> dict[str, object]:
    tables = set(inspect(connection).get_table_names())
    if USER_TABLE not in tables:
        raise GoogleIdentityFoundationMigrationError("usuarios_missing")
    changes: list[str] = []
    _ensure_hashed_password_nullable(connection, changes)
    _ensure_external_identity_user_provider_unique(connection, changes)
    _ensure_transaction_table(connection, changes)
    return {"changes": changes}


def apply_migration(action: str | None) -> dict[str, object]:
    if action != "upgrade":
        raise ValueError(f"{ACTION_ENV} debe ser 'upgrade'.")
    with engine.begin() as connection:
        return upgrade(connection)


if __name__ == "__main__":
    print(apply_migration(os.environ.get(ACTION_ENV)))
