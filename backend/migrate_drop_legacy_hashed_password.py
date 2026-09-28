"""Contract migration that removes ``usuarios.hashed_password``.

PasswordCredential must already be the exclusive password authority. The
default mode is read-only; applying the DROP requires an explicit opt-in and an
exact local target.
"""

from __future__ import annotations

from dataclasses import dataclass
import json
import os
from pathlib import Path
import sys

from sqlalchemy import inspect, text
from sqlalchemy.engine import Connection, Engine
from sqlalchemy.exc import SQLAlchemyError

from app.core.database import engine
from app.core.database_restore import is_official_restore_database_name


ACTION_ENV = "FEEDGO_DROP_LEGACY_HASHED_PASSWORD"
APPLY_ACTION = "apply"
EXPECTED_DRIVER = "mysql+pymysql"
EXPECTED_HOST = "localhost"
ALLOWED_DATABASES = frozenset({"mitienda", "mitienda_stage97_test"})
USERS_TABLE = "usuarios"
CREDENTIALS_TABLE = "password_credentials"
COLUMN = "hashed_password"
BACKEND_ROOT = Path(__file__).resolve().parent


class HashedPasswordCleanupError(RuntimeError):
    """The duplicate legacy password column cannot be removed safely."""


@dataclass(frozen=True)
class HashedPasswordCleanupPlan:
    status: str
    already_applied: bool
    total_users: int
    total_password_accounts: int
    credential_total: int
    dual_equivalent: int
    legacy_only: int
    divergent: int
    invalid: int
    missing_email_canonical: int
    blockers: tuple[str, ...]

    def safe_summary(self) -> dict[str, object]:
        return {
            "status": self.status,
            "already_applied": self.already_applied,
            "total_users": self.total_users,
            "total_password_accounts": self.total_password_accounts,
            "credential_total": self.credential_total,
            "dual_equivalent": self.dual_equivalent,
            "legacy_only": self.legacy_only,
            "divergent": self.divergent,
            "invalid": self.invalid,
            "missing_email_canonical": self.missing_email_canonical,
            "blockers": list(self.blockers),
        }


@dataclass(frozen=True)
class HashedPasswordCleanupResult:
    status: str
    dropped: int
    before: dict[str, object]
    after: dict[str, object]

    def safe_summary(self) -> dict[str, object]:
        return {
            "status": self.status,
            "dropped": self.dropped,
            "before": self.before,
            "after": self.after,
        }


def safe_database_target(target_engine: Engine = engine) -> str:
    url = target_engine.url
    return f"{url.drivername}://{url.host or '<sin-host>'}/{url.database or '<sin-base>'}"


def validate_apply_target(target_engine: Engine = engine) -> str:
    url = target_engine.url
    if (
        url.drivername != EXPECTED_DRIVER
        or url.host != EXPECTED_HOST
        or (
            url.database not in ALLOWED_DATABASES
            and not is_official_restore_database_name(url.database)
        )
    ):
        raise HashedPasswordCleanupError("hashed_password_cleanup_target_invalid")
    return str(url.database)


def _runtime_contract_blockers() -> list[str]:
    app_root = BACKEND_ROOT / "app"
    for path in app_root.rglob("*.py"):
        if path in {
            app_root / "core" / "database_backup.py",
            app_root / "core" / "database_restore.py",
        }:
            continue
        if "hashed_password" in path.read_text(encoding="utf-8"):
            return ["hashed_password_cleanup_runtime_reference"]
    return []


def _post_transition_plan(connection: Connection) -> HashedPasswordCleanupPlan:
    inspector = inspect(connection)
    tables = set(inspector.get_table_names())
    if not {USERS_TABLE, CREDENTIALS_TABLE}.issubset(tables):
        raise HashedPasswordCleanupError("hashed_password_cleanup_schema_incompatible")
    columns = {item["name"] for item in inspector.get_columns(USERS_TABLE)}
    if COLUMN in columns:
        raise HashedPasswordCleanupError("hashed_password_cleanup_postcheck_failed")
    aggregate = connection.execute(
        text(
            "SELECT (SELECT COUNT(*) FROM usuarios) AS total_users, "
            "(SELECT COUNT(*) FROM password_credentials) AS credential_total, "
            "(SELECT COUNT(*) FROM usuarios WHERE email_canonical IS NULL) AS missing_email_canonical, "
            "(SELECT COUNT(*) FROM password_credentials WHERE password_hash IS NULL OR password_hash = '') AS invalid"
        )
    ).mappings().one()
    blockers = _runtime_contract_blockers()
    missing = int(aggregate["missing_email_canonical"] or 0)
    invalid = int(aggregate["invalid"] or 0)
    if missing:
        blockers.append("hashed_password_cleanup_email_canonical_incomplete")
    if invalid:
        blockers.append("hashed_password_cleanup_invalid_credential")
    return HashedPasswordCleanupPlan(
        status="BLOCK" if blockers else "PASS",
        already_applied=True,
        total_users=int(aggregate["total_users"] or 0),
        total_password_accounts=int(aggregate["credential_total"] or 0),
        credential_total=int(aggregate["credential_total"] or 0),
        dual_equivalent=0,
        legacy_only=0,
        divergent=0,
        invalid=invalid,
        missing_email_canonical=missing,
        blockers=tuple(blockers),
    )


def preflight_hashed_password_cleanup(
    connection: Connection,
) -> HashedPasswordCleanupPlan:
    inspector = inspect(connection)
    tables = set(inspector.get_table_names())
    if not {USERS_TABLE, CREDENTIALS_TABLE}.issubset(tables):
        raise HashedPasswordCleanupError("hashed_password_cleanup_schema_incompatible")
    columns = {item["name"] for item in inspector.get_columns(USERS_TABLE)}
    if COLUMN not in columns:
        return _post_transition_plan(connection)
    aggregate = connection.execute(
        text(
            "SELECT COUNT(*) AS total_users, "
            "SUM(u.hashed_password IS NOT NULL OR p.usuario_id IS NOT NULL) AS total_password_accounts, "
            "COUNT(p.usuario_id) AS credential_total, "
            "SUM(u.hashed_password IS NOT NULL AND p.usuario_id IS NOT NULL AND u.hashed_password = p.password_hash) AS dual_equivalent, "
            "SUM(u.hashed_password IS NOT NULL AND p.usuario_id IS NULL) AS legacy_only, "
            "SUM(u.hashed_password IS NOT NULL AND p.usuario_id IS NOT NULL AND u.hashed_password <> p.password_hash) AS divergent, "
            "SUM((p.usuario_id IS NOT NULL AND (p.password_hash IS NULL OR p.password_hash = '')) OR "
            "    (u.hashed_password IS NULL AND p.usuario_id IS NULL)) AS invalid, "
            "SUM(u.email_canonical IS NULL) AS missing_email_canonical "
            "FROM usuarios u LEFT JOIN password_credentials p ON p.usuario_id = u.id"
        )
    ).mappings().one()
    values = {key: int(value or 0) for key, value in aggregate.items()}
    blockers = _runtime_contract_blockers()
    for key, code in (
        ("legacy_only", "hashed_password_cleanup_legacy_only"),
        ("divergent", "hashed_password_cleanup_divergent"),
        ("invalid", "hashed_password_cleanup_invalid"),
        ("missing_email_canonical", "hashed_password_cleanup_email_canonical_incomplete"),
    ):
        if values[key]:
            blockers.append(code)
    if values["credential_total"] != values["total_password_accounts"]:
        blockers.append("hashed_password_cleanup_classification_incomplete")
    return HashedPasswordCleanupPlan(
        status="BLOCK" if blockers else "PASS",
        already_applied=False,
        blockers=tuple(dict.fromkeys(blockers)),
        **values,
    )


def drop_legacy_hashed_password(connection: Connection) -> HashedPasswordCleanupResult:
    before = preflight_hashed_password_cleanup(connection)
    if before.status != "PASS":
        raise HashedPasswordCleanupError("hashed_password_cleanup_preflight_blocked")
    if before.already_applied:
        return HashedPasswordCleanupResult(
            status="PASS", dropped=0, before=before.safe_summary(), after=before.safe_summary()
        )
    preserved = {
        "usuarios": before.total_users,
        "password_credentials": before.credential_total,
    }
    connection.exec_driver_sql("ALTER TABLE usuarios DROP COLUMN hashed_password")
    after = _post_transition_plan(connection)
    if after.status != "PASS" or {
        "usuarios": after.total_users,
        "password_credentials": after.credential_total,
    } != preserved:
        raise HashedPasswordCleanupError("hashed_password_cleanup_postcheck_failed")
    return HashedPasswordCleanupResult(
        status="PASS", dropped=1, before=before.safe_summary(), after=after.safe_summary()
    )


def apply_cleanup(action: str | None, *, target_engine: Engine = engine):
    if action != APPLY_ACTION:
        raise HashedPasswordCleanupError(f"{ACTION_ENV}_must_equal_{APPLY_ACTION}")
    database = validate_apply_target(target_engine)
    with target_engine.begin() as connection:
        selected = connection.exec_driver_sql("SELECT DATABASE()").scalar_one()
        if selected != database:
            raise HashedPasswordCleanupError("hashed_password_cleanup_database_mismatch")
        return drop_legacy_hashed_password(connection)


def main() -> int:
    try:
        action = os.environ.get(ACTION_ENV)
        if action is None:
            with engine.connect() as connection:
                result = preflight_hashed_password_cleanup(connection).safe_summary()
            print(json.dumps({"target": safe_database_target(), "mode": "read_only", "report": result}))
            return 0 if result["status"] == "PASS" else 2
        result = apply_cleanup(action)
        print(json.dumps({"target": safe_database_target(), "mode": APPLY_ACTION, "report": result.safe_summary()}))
        return 0
    except HashedPasswordCleanupError as exc:
        print(json.dumps({"status": "BLOCK", "blockers": [str(exc)]}), file=sys.stderr)
        return 2
    except SQLAlchemyError:
        print(json.dumps({"status": "BLOCK", "blockers": ["hashed_password_cleanup_database_error"]}), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
