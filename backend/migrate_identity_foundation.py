"""Migracion expand-first e idempotente para la identidad base de ETAPA 99.

Importar este modulo no modifica la base. Sin el flag explicito, la ejecucion
realiza solamente el preflight read-only de emails y estado del schema.
"""

from __future__ import annotations

from collections import defaultdict
import os
import sys

from sqlalchemy import inspect, text
from sqlalchemy.exc import SQLAlchemyError

from app.core.database import Base, engine
from app.core.model_registry import import_all_models
from app.modules.users.services.email_normalization import (
    InvalidEmailError,
    canonicalize_email,
)

ACTION_ENV = "FEEDGO_IDENTITY_FOUNDATION_MIGRATION"
NEW_TABLES = (
    "password_credentials",
    "external_identities",
    "feedgo_sessions",
)
USER_COLUMN_DDL = {
    "email_canonical": "VARCHAR(255) NULL",
    "email_verified_at": "DATETIME NULL",
    "email_verification_source": "VARCHAR(32) NULL",
    "fecha_nacimiento": "DATE NULL",
}
EMAIL_CANONICAL_INDEX = "ux_usuarios_email_canonical"

import_all_models()


class IdentityMigrationPreflightError(RuntimeError):
    """El estado actual no permite un backfill automatico seguro."""


def safe_database_target() -> str:
    host = engine.url.host or "<sin-host>"
    database = engine.url.database or "<sin-base>"
    return f"{engine.dialect.name}://{host}/{database}"


def _load_legacy_users(connection):
    return connection.execute(
        text("SELECT id, email, hashed_password FROM usuarios ORDER BY id")
    ).mappings().all()


def preflight(connection) -> dict[str, object]:
    """Audita emails y cualquier backfill parcial sin ejecutar escrituras."""

    inspector = inspect(connection)
    if "usuarios" not in inspector.get_table_names():
        raise IdentityMigrationPreflightError("Falta la tabla usuarios")

    rows = _load_legacy_users(connection)
    canonical_to_ids: dict[str, list[int]] = defaultdict(list)
    invalid_ids: list[int] = []

    for row in rows:
        try:
            canonical = canonicalize_email(row["email"])
        except InvalidEmailError:
            invalid_ids.append(row["id"])
            continue
        canonical_to_ids[canonical].append(row["id"])

    collisions = sorted(
        user_id
        for ids in canonical_to_ids.values()
        if len(ids) > 1
        for user_id in ids
    )
    if invalid_ids or collisions:
        raise IdentityMigrationPreflightError(
            "Preflight bloqueado: "
            f"emails_invalidos_ids={invalid_ids}, "
            f"colisiones_ids={collisions}, "
            "hash_faltante_ids=[]"
        )

    columns = {column["name"] for column in inspector.get_columns("usuarios")}
    pending_canonical_ids: list[int] = []
    if "email_canonical" in columns:
        pending_canonical_ids = connection.execute(
            text(
                "SELECT id FROM usuarios WHERE email_canonical IS NULL "
                "ORDER BY id"
            )
        ).scalars().all()
        persisted = connection.execute(
            text(
                "SELECT id, email, email_canonical FROM usuarios "
                "WHERE email_canonical IS NOT NULL ORDER BY id"
            )
        ).mappings()
        divergent = [
            row["id"]
            for row in persisted
            if row["email_canonical"] != canonicalize_email(row["email"])
        ]
        if divergent:
            raise IdentityMigrationPreflightError(
                f"Email canonical parcial divergente para usuarios={divergent}"
            )

    pending_credential_ids: list[int] = []
    if "password_credentials" in inspector.get_table_names():
        pending_credential_ids = connection.execute(
            text(
                "SELECT u.id FROM usuarios u LEFT JOIN password_credentials p "
                "ON p.usuario_id = u.id WHERE p.usuario_id IS NULL "
                "AND u.hashed_password IS NOT NULL ORDER BY u.id"
            )
        ).scalars().all()
        divergent_credentials = connection.execute(
            text(
                "SELECT u.id FROM usuarios u "
                "JOIN password_credentials p ON p.usuario_id = u.id "
                "WHERE u.hashed_password IS NOT NULL "
                "AND p.password_hash <> u.hashed_password ORDER BY u.id"
            )
        ).scalars().all()
        if divergent_credentials:
            raise IdentityMigrationPreflightError(
                "Credenciales parciales divergentes para usuarios="
                f"{divergent_credentials}"
            )

    return {
        "usuarios": len(rows),
        "canonicos_unicos": len(canonical_to_ids),
        "colisiones": 0,
        "emails_invalidos": 0,
        "email_canonical_pendientes_ids": pending_canonical_ids,
        "password_credentials_pendientes_ids": pending_credential_ids,
    }


def _add_user_columns(connection) -> list[str]:
    inspector = inspect(connection)
    columns = {column["name"] for column in inspector.get_columns("usuarios")}
    changes: list[str] = []
    for name, ddl in USER_COLUMN_DDL.items():
        if name not in columns:
            connection.exec_driver_sql(f"ALTER TABLE usuarios ADD COLUMN {name} {ddl}")
            changes.append(f"usuarios.{name}")
    return changes


def _create_identity_tables(connection) -> list[str]:
    existing = set(inspect(connection).get_table_names())
    changes: list[str] = []
    for name in NEW_TABLES:
        if name not in existing:
            Base.metadata.tables[name].create(bind=connection, checkfirst=True)
            changes.append(name)
    return changes


def _backfill(connection) -> dict[str, int]:
    email_updates = 0
    credential_inserts = 0
    for row in _load_legacy_users(connection):
        canonical = canonicalize_email(row["email"])
        result = connection.execute(
            text(
                "UPDATE usuarios SET email_canonical = :canonical "
                "WHERE id = :usuario_id AND email_canonical IS NULL"
            ),
            {"canonical": canonical, "usuario_id": row["id"]},
        )
        email_updates += result.rowcount

        if not row["hashed_password"]:
            continue
        exists = connection.execute(
            text(
                "SELECT 1 FROM password_credentials "
                "WHERE usuario_id = :usuario_id"
            ),
            {"usuario_id": row["id"]},
        ).first()
        if exists is None:
            connection.execute(
                text(
                    "INSERT INTO password_credentials "
                    "(usuario_id, password_hash, hash_version) "
                    "VALUES (:usuario_id, :password_hash, 'bcrypt')"
                ),
                {
                    "usuario_id": row["id"],
                    "password_hash": row["hashed_password"],
                },
            )
            credential_inserts += 1

    return {
        "emails": email_updates,
        "password_credentials": credential_inserts,
    }


def _ensure_unique_index(connection) -> bool:
    inspector = inspect(connection)
    indexes = {index["name"] for index in inspector.get_indexes("usuarios")}
    uniques = {
        constraint.get("name")
        for constraint in inspector.get_unique_constraints("usuarios")
    }
    if EMAIL_CANONICAL_INDEX in indexes or EMAIL_CANONICAL_INDEX in uniques:
        return False
    connection.exec_driver_sql(
        f"CREATE UNIQUE INDEX {EMAIL_CANONICAL_INDEX} "
        "ON usuarios (email_canonical)"
    )
    return True


def upgrade(connection) -> dict[str, object]:
    audit = preflight(connection)
    changes = _add_user_columns(connection)
    changes.extend(_create_identity_tables(connection))
    backfill = _backfill(connection)
    if _ensure_unique_index(connection):
        changes.append(EMAIL_CANONICAL_INDEX)
    return {"preflight": audit, "changes": changes, "backfill": backfill}


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
    except (IdentityMigrationPreflightError, SQLAlchemyError, ValueError) as exc:
        print(f"MIGRACION FALLIDA: {exc}", file=sys.stderr)
        return 2
    print(f"MIGRACION OK: {result}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
