"""Migracion aditiva e idempotente del contrato FeedGoSession de ET99.4-A."""

from __future__ import annotations

from sqlalchemy import inspect

from app.core.database import engine


TABLE = "feedgo_sessions"
ACTIVE_INDEX = "ix_feedgo_sessions_user_active"
CHECKS = {
    "ck_feedgo_sessions_authentication_method":
        "authentication_method IN ('password', 'google')",
    "ck_feedgo_sessions_contract_version": "contract_version = 1",
    "ck_feedgo_sessions_expiry": "expires_at > issued_at",
    "ck_feedgo_sessions_revocation_time":
        "revoked_at IS NULL OR revoked_at >= issued_at",
}


class FeedGoSessionMigrationError(RuntimeError):
    pass


def preflight(connection) -> dict[str, int]:
    inspector = inspect(connection)
    if TABLE not in inspector.get_table_names():
        raise FeedGoSessionMigrationError("Falta feedgo_sessions")
    invalid = connection.exec_driver_sql(
        "SELECT COUNT(*) FROM feedgo_sessions WHERE "
        "authentication_method NOT IN ('password', 'google') "
        "OR contract_version <> 1 OR expires_at <= issued_at "
        "OR (revoked_at IS NOT NULL AND revoked_at < issued_at) "
        "OR (authentication_method = 'password' AND external_identity_id IS NOT NULL) "
        "OR (authentication_method = 'google' AND external_identity_id IS NULL)"
    ).scalar_one()
    if invalid:
        raise FeedGoSessionMigrationError(
            f"Preflight bloqueado: sesiones incompatibles={invalid}"
        )
    return {"sessions": connection.exec_driver_sql(
        "SELECT COUNT(*) FROM feedgo_sessions"
    ).scalar_one(), "invalid": 0}


def upgrade(connection) -> dict[str, object]:
    audit = preflight(connection)
    inspector = inspect(connection)
    changes: list[str] = []
    indexes = {item["name"] for item in inspector.get_indexes(TABLE)}
    if ACTIVE_INDEX not in indexes:
        connection.exec_driver_sql(
            f"CREATE INDEX {ACTIVE_INDEX} ON {TABLE} "
            "(usuario_id, revoked_at, expires_at)"
        )
        changes.append(ACTIVE_INDEX)

    # SQLite no soporta ADD CONSTRAINT. Sus tests crean el contrato final desde
    # metadata; la migracion real de FeedGo es MySQL.
    if connection.dialect.name != "sqlite":
        existing = {
            item.get("name") for item in inspect(connection).get_check_constraints(TABLE)
        }
        for name, expression in CHECKS.items():
            if name not in existing:
                connection.exec_driver_sql(
                    f"ALTER TABLE {TABLE} ADD CONSTRAINT {name} CHECK ({expression})"
                )
                changes.append(name)
    return {"preflight": audit, "changes": changes}


def apply_migration() -> dict[str, object]:
    with engine.begin() as connection:
        return upgrade(connection)


if __name__ == "__main__":
    print(apply_migration())
