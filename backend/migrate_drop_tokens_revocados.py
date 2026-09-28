"""Contract migration for the retired legacy JWT blacklist.

The default mode is read-only. Applying the DROP requires an explicit opt-in
and an exact local database target. Historical migrations and backups are not
rewritten by this module.
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


ACTION_ENV = "FEEDGO_DROP_TOKENS_REVOCADOS"
APPLY_ACTION = "apply"
EXPECTED_DRIVER = "mysql+pymysql"
EXPECTED_HOST = "localhost"
ALLOWED_DATABASES = frozenset({"mitienda", "mitienda_stage97_test"})
TABLE = "tokens_revocados"
REQUIRED_COLUMNS = frozenset(
    {"id", "token", "usuario_id", "fecha_revocado", "expira_en"}
)
PRESERVED_TABLES = ("usuarios", "password_credentials", "feedgo_sessions")
BACKEND_ROOT = Path(__file__).resolve().parent


class TokensRevocadosCleanupError(RuntimeError):
    """The legacy blacklist cannot be removed safely."""


@dataclass(frozen=True)
class TokensRevocadosCleanupPlan:
    status: str
    already_applied: bool
    rows: int
    expired: int
    expiry_unknown: int
    not_yet_expired: int
    inbound_foreign_keys: int
    blockers: tuple[str, ...]

    def safe_summary(self) -> dict[str, object]:
        return {
            "status": self.status,
            "already_applied": self.already_applied,
            "rows": self.rows,
            "expired": self.expired,
            "expiry_unknown": self.expiry_unknown,
            "not_yet_expired": self.not_yet_expired,
            "inbound_foreign_keys": self.inbound_foreign_keys,
            "blockers": list(self.blockers),
        }


@dataclass(frozen=True)
class TokensRevocadosCleanupResult:
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
        raise TokensRevocadosCleanupError("tokens_cleanup_target_invalid")
    return str(url.database)


def _runtime_contract_blockers() -> list[str]:
    blockers: list[str] = []
    app_root = BACKEND_ROOT / "app"
    forbidden = ("TokenRevocado", "tokens_revocados")
    for path in app_root.rglob("*.py"):
        if path in {
            app_root / "core" / "database_backup.py",
            app_root / "core" / "database_restore.py",
        }:
            continue
        source = path.read_text(encoding="utf-8")
        if any(item in source for item in forbidden):
            blockers.append("tokens_cleanup_runtime_reference")
            break
    return blockers


def _inbound_foreign_keys(inspector) -> int:
    count = 0
    for table_name in inspector.get_table_names():
        if table_name == TABLE:
            continue
        for foreign_key in inspector.get_foreign_keys(table_name):
            if foreign_key.get("referred_table") == TABLE:
                count += 1
    return count


def _preserved_counts(connection: Connection) -> dict[str, int]:
    inspector = inspect(connection)
    tables = set(inspector.get_table_names())
    if not set(PRESERVED_TABLES).issubset(tables):
        raise TokensRevocadosCleanupError("tokens_cleanup_schema_incompatible")
    return {
        table: int(connection.execute(text(f"SELECT COUNT(*) FROM {table}")).scalar_one())
        for table in PRESERVED_TABLES
    }


def preflight_tokens_revocados_cleanup(
    connection: Connection,
) -> TokensRevocadosCleanupPlan:
    inspector = inspect(connection)
    tables = set(inspector.get_table_names())
    if TABLE not in tables:
        blockers = _runtime_contract_blockers()
        return TokensRevocadosCleanupPlan(
            status="BLOCK" if blockers else "PASS",
            already_applied=True,
            rows=0,
            expired=0,
            expiry_unknown=0,
            not_yet_expired=0,
            inbound_foreign_keys=0,
            blockers=tuple(blockers),
        )
    columns = {item["name"] for item in inspector.get_columns(TABLE)}
    if not REQUIRED_COLUMNS.issubset(columns):
        raise TokensRevocadosCleanupError("tokens_cleanup_schema_incompatible")

    inbound = _inbound_foreign_keys(inspector)
    current_time = "UTC_TIMESTAMP()" if connection.dialect.name == "mysql" else "CURRENT_TIMESTAMP"
    aggregate = connection.execute(
        text(
            "SELECT COUNT(*) AS rows_total, "
            "SUM(expira_en IS NULL) AS expiry_unknown, "
            f"SUM(expira_en IS NOT NULL AND expira_en <= {current_time}) AS expired, "
            f"SUM(expira_en IS NOT NULL AND expira_en > {current_time}) AS not_yet_expired "
            "FROM tokens_revocados"
        )
    ).mappings().one()
    rows = int(aggregate["rows_total"] or 0)
    expiry_unknown = int(aggregate["expiry_unknown"] or 0)
    expired = int(aggregate["expired"] or 0)
    not_yet_expired = int(aggregate["not_yet_expired"] or 0)
    blockers = _runtime_contract_blockers()
    if inbound:
        blockers.append("tokens_cleanup_inbound_foreign_keys")
    if expiry_unknown:
        blockers.append("tokens_cleanup_expiry_unknown")
    if not_yet_expired:
        blockers.append("tokens_cleanup_unexpired_rows")
    if rows != expired:
        blockers.append("tokens_cleanup_classification_incomplete")
    return TokensRevocadosCleanupPlan(
        status="BLOCK" if blockers else "PASS",
        already_applied=False,
        rows=rows,
        expired=expired,
        expiry_unknown=expiry_unknown,
        not_yet_expired=not_yet_expired,
        inbound_foreign_keys=inbound,
        blockers=tuple(dict.fromkeys(blockers)),
    )


def drop_tokens_revocados(connection: Connection) -> TokensRevocadosCleanupResult:
    before = preflight_tokens_revocados_cleanup(connection)
    if before.status != "PASS":
        raise TokensRevocadosCleanupError("tokens_cleanup_preflight_blocked")
    if before.already_applied:
        return TokensRevocadosCleanupResult(
            status="PASS", dropped=0, before=before.safe_summary(), after=before.safe_summary()
        )
    preserved = _preserved_counts(connection)
    connection.exec_driver_sql("DROP TABLE tokens_revocados")
    after = preflight_tokens_revocados_cleanup(connection)
    if not after.already_applied or _preserved_counts(connection) != preserved:
        raise TokensRevocadosCleanupError("tokens_cleanup_postcheck_failed")
    return TokensRevocadosCleanupResult(
        status="PASS", dropped=1, before=before.safe_summary(), after=after.safe_summary()
    )


def apply_cleanup(action: str | None, *, target_engine: Engine = engine):
    if action != APPLY_ACTION:
        raise TokensRevocadosCleanupError(f"{ACTION_ENV}_must_equal_{APPLY_ACTION}")
    database = validate_apply_target(target_engine)
    with target_engine.begin() as connection:
        selected = connection.exec_driver_sql("SELECT DATABASE()").scalar_one()
        if selected != database:
            raise TokensRevocadosCleanupError("tokens_cleanup_database_mismatch")
        return drop_tokens_revocados(connection)


def main() -> int:
    try:
        action = os.environ.get(ACTION_ENV)
        if action is None:
            with engine.connect() as connection:
                result = preflight_tokens_revocados_cleanup(connection).safe_summary()
            print(json.dumps({"target": safe_database_target(), "mode": "read_only", "report": result}))
            return 0 if result["status"] == "PASS" else 2
        result = apply_cleanup(action)
        print(json.dumps({"target": safe_database_target(), "mode": APPLY_ACTION, "report": result.safe_summary()}))
        return 0
    except TokensRevocadosCleanupError as exc:
        print(json.dumps({"status": "BLOCK", "blockers": [str(exc)]}), file=sys.stderr)
        return 2
    except SQLAlchemyError:
        print(json.dumps({"status": "BLOCK", "blockers": ["tokens_cleanup_database_error"]}), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
