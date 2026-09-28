"""Reparacion focal e idempotente de ``usuarios.email_canonical``.

El modo por defecto ejecuta solamente el preflight. Aplicar cambios requiere
un opt-in explicito y un target local exacto. Este modulo no consulta ni
modifica credenciales, hashes, sesiones o contratos legacy.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
import json
import os
import sys

from sqlalchemy import inspect, text
from sqlalchemy.engine import Connection, Engine
from sqlalchemy.exc import SQLAlchemyError

from app.core.database import engine
from app.modules.users.services.email_normalization import (
    InvalidEmailError,
    canonicalize_email,
)


ACTION_ENV = "FEEDGO_EMAIL_CANONICAL_REPAIR"
APPLY_ACTION = "apply"
EXPECTED_DRIVER = "mysql+pymysql"
EXPECTED_HOST = "localhost"
EXPECTED_DATABASE = "mitienda"
USERS_TABLE = "usuarios"
REQUIRED_COLUMNS = frozenset({"id", "email", "email_canonical"})


class CanonicalEmailRepairError(RuntimeError):
    """La reparacion no puede continuar de forma segura."""


@dataclass(frozen=True)
class CanonicalEmailUpdate:
    usuario_id: int
    canonical: str


@dataclass(frozen=True)
class CanonicalEmailRepairPlan:
    status: str
    total_users: int
    pending: int
    invalid_source: int
    collision_groups: int
    collision_rows: int
    persisted_divergent: int
    blockers: tuple[str, ...]
    updates: tuple[CanonicalEmailUpdate, ...] = field(repr=False)

    def safe_summary(self) -> dict[str, object]:
        return {
            "status": self.status,
            "total_users": self.total_users,
            "pending": self.pending,
            "invalid_source": self.invalid_source,
            "collision_groups": self.collision_groups,
            "collision_rows": self.collision_rows,
            "persisted_divergent": self.persisted_divergent,
            "blockers": list(self.blockers),
        }


@dataclass(frozen=True)
class CanonicalEmailRepairResult:
    status: str
    updated: int
    before: dict[str, object]
    after: dict[str, object]

    def safe_summary(self) -> dict[str, object]:
        return {
            "status": self.status,
            "updated": self.updated,
            "before": self.before,
            "after": self.after,
        }


def safe_database_target(target_engine: Engine = engine) -> str:
    host = target_engine.url.host or "<sin-host>"
    database = target_engine.url.database or "<sin-base>"
    return f"{target_engine.url.drivername}://{host}/{database}"


def _has_unique_canonical(inspector) -> bool:
    unique_columns = {
        tuple(item.get("column_names") or ())
        for item in inspector.get_unique_constraints(USERS_TABLE)
    }
    unique_columns.update(
        tuple(item.get("column_names") or ())
        for item in inspector.get_indexes(USERS_TABLE)
        if item.get("unique")
    )
    return ("email_canonical",) in unique_columns


def preflight_email_canonical_repair(
    connection: Connection,
) -> CanonicalEmailRepairPlan:
    """Construye un plan agregado sin modificar datos ni exponer identidades."""

    inspector = inspect(connection)
    if USERS_TABLE not in inspector.get_table_names():
        raise CanonicalEmailRepairError("canonical_repair_users_table_missing")

    columns = {item["name"] for item in inspector.get_columns(USERS_TABLE)}
    if not REQUIRED_COLUMNS.issubset(columns):
        raise CanonicalEmailRepairError("canonical_repair_schema_incompatible")
    if not _has_unique_canonical(inspector):
        raise CanonicalEmailRepairError(
            "canonical_repair_unique_constraint_missing"
        )

    rows = connection.execute(
        text(
            "SELECT id, email, email_canonical FROM usuarios "
            "ORDER BY id"
        )
    ).mappings().all()

    invalid_source = 0
    persisted_divergent = 0
    canonical_counts: Counter[str] = Counter()
    updates: list[CanonicalEmailUpdate] = []

    for row in rows:
        try:
            canonical = canonicalize_email(row["email"])
        except InvalidEmailError:
            invalid_source += 1
            continue

        canonical_counts[canonical] += 1
        persisted = row["email_canonical"]
        if persisted is None:
            updates.append(
                CanonicalEmailUpdate(
                    usuario_id=row["id"],
                    canonical=canonical,
                )
            )
        elif persisted != canonical:
            persisted_divergent += 1

    collision_sizes = [count for count in canonical_counts.values() if count > 1]
    blockers: list[str] = []
    if invalid_source:
        blockers.append("canonical_repair_invalid_source")
    if collision_sizes:
        blockers.append("canonical_repair_collision")
    if persisted_divergent:
        blockers.append("canonical_repair_persisted_divergent")

    return CanonicalEmailRepairPlan(
        status="BLOCK" if blockers else "PASS",
        total_users=len(rows),
        pending=len(updates),
        invalid_source=invalid_source,
        collision_groups=len(collision_sizes),
        collision_rows=sum(collision_sizes),
        persisted_divergent=persisted_divergent,
        blockers=tuple(blockers),
        updates=tuple(updates),
    )


def repair_email_canonical(connection: Connection) -> CanonicalEmailRepairResult:
    """Aplica un plan valido dentro de la transaccion provista."""

    before = preflight_email_canonical_repair(connection)
    if before.status != "PASS":
        raise CanonicalEmailRepairError("canonical_repair_preflight_blocked")

    updated = 0
    for item in before.updates:
        result = connection.execute(
            text(
                "UPDATE usuarios SET email_canonical = :canonical "
                "WHERE id = :usuario_id AND email_canonical IS NULL"
            ),
            {"canonical": item.canonical, "usuario_id": item.usuario_id},
        )
        if result.rowcount != 1:
            raise CanonicalEmailRepairError("canonical_repair_target_changed")
        updated += 1

    after = preflight_email_canonical_repair(connection)
    if after.status != "PASS" or after.pending != 0:
        raise CanonicalEmailRepairError("canonical_repair_postcheck_failed")

    return CanonicalEmailRepairResult(
        status="PASS",
        updated=updated,
        before=before.safe_summary(),
        after=after.safe_summary(),
    )


def validate_apply_target(target_engine: Engine = engine) -> None:
    url = target_engine.url
    if (
        url.drivername != EXPECTED_DRIVER
        or url.host != EXPECTED_HOST
        or url.database != EXPECTED_DATABASE
    ):
        raise CanonicalEmailRepairError("canonical_repair_target_invalid")


def _apply_transaction(
    target_engine: Engine,
    *,
    expected_database: str | None = None,
) -> CanonicalEmailRepairResult:
    with target_engine.begin() as connection:
        if expected_database is not None:
            current_database = connection.exec_driver_sql(
                "SELECT DATABASE()"
            ).scalar_one()
            if current_database != expected_database:
                raise CanonicalEmailRepairError(
                    "canonical_repair_database_mismatch"
                )
        return repair_email_canonical(connection)


def apply_repair(
    action: str | None,
    *,
    target_engine: Engine = engine,
) -> CanonicalEmailRepairResult:
    if action != APPLY_ACTION:
        raise CanonicalEmailRepairError(
            f"{ACTION_ENV}_must_equal_{APPLY_ACTION}"
        )
    validate_apply_target(target_engine)
    return _apply_transaction(
        target_engine,
        expected_database=EXPECTED_DATABASE,
    )


def _safe_error(code: str) -> dict[str, object]:
    return {"status": "BLOCK", "blockers": [code]}


def main() -> int:
    action = os.environ.get(ACTION_ENV)
    try:
        if action is None:
            with engine.connect() as connection:
                plan = preflight_email_canonical_repair(connection)
            payload = {
                "target": safe_database_target(),
                "mode": "read_only",
                "report": plan.safe_summary(),
            }
            print(json.dumps(payload))
            return 0 if plan.status == "PASS" else 2

        result = apply_repair(action)
        print(
            json.dumps(
                {
                    "target": safe_database_target(),
                    "mode": APPLY_ACTION,
                    "report": result.safe_summary(),
                }
            )
        )
        return 0
    except CanonicalEmailRepairError as exc:
        print(json.dumps(_safe_error(str(exc))), file=sys.stderr)
        return 2
    except SQLAlchemyError:
        print(
            json.dumps(_safe_error("canonical_repair_database_error")),
            file=sys.stderr,
        )
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
