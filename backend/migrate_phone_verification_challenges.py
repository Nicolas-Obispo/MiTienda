"""Migracion aditiva, idempotente y recuperable de challenges OTP."""
from __future__ import annotations
import os
from sqlalchemy import inspect
from app.core.database import engine
from app.core.model_registry import import_all_models

import_all_models()

from app.modules.users.models.identity_models import PhoneVerificationChallenge

ACTION_ENV = "FEEDGO_PHONE_VERIFICATION_MIGRATION"

COLUMNS = {
    "phone_e164_snapshot": "VARCHAR(16) NOT NULL",
    "code_digest": "VARCHAR(64) NOT NULL",
    "issuance_id": "VARCHAR(64) NOT NULL",
    "created_at": "DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP",
    "expires_at": "DATETIME NOT NULL",
    "consumed_at": "DATETIME NULL",
    "revoked_at": "DATETIME NULL",
    "invalidation_reason": "VARCHAR(32) NULL",
    "failed_attempts": "INT NOT NULL DEFAULT 0",
}

CHECKS = {
    "ck_phone_verification_expiry": "expires_at > created_at",
    "ck_phone_verification_attempts": "failed_attempts >= 0 AND failed_attempts <= 5",
    "ck_phone_verification_terminal": "NOT (consumed_at IS NOT NULL AND revoked_at IS NOT NULL)",
    "ck_phone_verification_reason": "invalidation_reason IS NULL OR invalidation_reason IN ('superseded', 'administrative')",
    "ck_phone_verification_invalidation_pair": "(revoked_at IS NULL AND invalidation_reason IS NULL) OR (revoked_at IS NOT NULL AND invalidation_reason IS NOT NULL)",
}

INDEXES = {
    "ix_phone_verification_user_created": ("usuario_id", "created_at"),
    "ix_phone_verification_user_expiry": ("usuario_id", "expires_at"),
}


def _ensure_partial_table(connection):
    changes = []
    inspector = inspect(connection)
    present = {column["name"] for column in inspector.get_columns("phone_verification_challenges")}
    required_base = {"id", "usuario_id"}
    if not required_base.issubset(present):
        raise RuntimeError("phone_verification_partial_base_incompatible")
    for name, ddl in COLUMNS.items():
        if name not in present:
            connection.exec_driver_sql(
                f"ALTER TABLE phone_verification_challenges ADD COLUMN {name} {ddl}"
            )
            changes.append(f"phone_verification_challenges.{name}")

    inspector = inspect(connection)
    foreign_keys = inspector.get_foreign_keys("phone_verification_challenges")
    has_user_fk = any(
        fk.get("constrained_columns") == ["usuario_id"]
        and fk.get("referred_table") == "usuarios"
        and fk.get("referred_columns") == ["id"]
        for fk in foreign_keys
    )
    if not has_user_fk:
        connection.exec_driver_sql(
            "ALTER TABLE phone_verification_challenges ADD CONSTRAINT "
            "fk_phone_verification_usuario FOREIGN KEY (usuario_id) "
            "REFERENCES usuarios(id) ON DELETE CASCADE"
        )
        changes.append("fk_phone_verification_usuario")

    inspector = inspect(connection)
    unique_columns = {
        tuple(item.get("column_names") or [])
        for item in inspector.get_unique_constraints("phone_verification_challenges")
    }
    unique_columns.update(
        tuple(item.get("column_names") or [])
        for item in inspector.get_indexes("phone_verification_challenges")
        if item.get("unique")
    )
    if ("issuance_id",) not in unique_columns:
        connection.exec_driver_sql(
            "CREATE UNIQUE INDEX uq_phone_verification_issuance_id "
            "ON phone_verification_challenges (issuance_id)"
        )
        changes.append("uq_phone_verification_issuance_id")

    inspector = inspect(connection)
    existing_indexes = {
        item.get("name"): tuple(item.get("column_names") or [])
        for item in inspector.get_indexes("phone_verification_challenges")
    }
    for name, columns in INDEXES.items():
        if existing_indexes.get(name) != columns:
            column_sql = ", ".join(columns)
            connection.exec_driver_sql(
                f"CREATE INDEX {name} ON phone_verification_challenges ({column_sql})"
            )
            changes.append(name)

    if connection.dialect.name == "mysql":
        existing_checks = {
            item.get("name")
            for item in inspect(connection).get_check_constraints(
                "phone_verification_challenges"
            )
        }
        for name, expression in CHECKS.items():
            if name not in existing_checks:
                connection.exec_driver_sql(
                    "ALTER TABLE phone_verification_challenges "
                    f"ADD CONSTRAINT {name} CHECK ({expression})"
                )
                changes.append(name)
    return changes

def upgrade(connection):
    inspector = inspect(connection); changes=[]
    if "phone_verification_challenges" not in inspector.get_table_names():
        PhoneVerificationChallenge.__table__.create(connection)
        changes.append("phone_verification_challenges")
    else:
        changes.extend(_ensure_partial_table(connection))
    if connection.dialect.name == "mysql":
        checks = {c.get("name"): c.get("sqltext", "") for c in inspect(connection).get_check_constraints("account_action_rate_limits")}
        sql = checks.get("ck_account_action_rate_limits_action", "")
        if "phone_verification" not in sql:
            connection.exec_driver_sql("ALTER TABLE account_action_rate_limits DROP CHECK ck_account_action_rate_limits_action")
            connection.exec_driver_sql("ALTER TABLE account_action_rate_limits ADD CONSTRAINT ck_account_action_rate_limits_action CHECK (action IN ('email_verification','password_reset','current_password','phone_verification'))")
            changes.append("ck_account_action_rate_limits_action")
    return {"changes": changes, "backfill": 0}

def apply_migration(action):
    if action != "upgrade": raise ValueError(f"{ACTION_ENV} debe ser 'upgrade'.")
    with engine.begin() as connection: return upgrade(connection)

if __name__ == "__main__":
    print(apply_migration(os.environ.get(ACTION_ENV)))
