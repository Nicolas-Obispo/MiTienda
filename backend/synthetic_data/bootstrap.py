"""Bootstrap one-shot y fail-closed del schema MySQL aislado de ET100.3."""

from __future__ import annotations

from collections import Counter
from contextlib import contextmanager
from dataclasses import asdict, dataclass
import argparse
import hashlib
import json
import os
import re
from typing import Iterable

from sqlalchemy import create_engine, create_mock_engine, inspect
from sqlalchemy.engine import Connection, Engine, URL
from sqlalchemy.engine.interfaces import Dialect
from sqlalchemy.exc import DBAPIError

from app.core.database import Base
from app.core.model_registry import import_all_models
from check_database_schema import check_schema, schema_result_to_dict

from .target_guard import (
    CredentialRole,
    EXPECTED_DATABASE,
    ROLE_PRIVILEGES,
    Stage100TargetGuardError,
    Stage100TargetConfiguration,
    load_target_configuration,
    validate_control_connection,
    validate_live_connection,
    validate_pre_schema_connection,
)
from .ddl_lifecycle import (
    CLIENT_READ_TIMEOUT_SECONDS,
    DdlLifecycleError,
    execute_ddl_batch,
)


BOOTSTRAP_GATE = "FEEDGO_STAGE100_BOOTSTRAP"
BOOTSTRAP_GATE_VALUE = "apply"
EXPECTED_TABLE_COUNT = 39
EXPECTED_CREATE_TABLE_COUNT = 39
EXPECTED_CREATE_INDEX_COUNT = 115
EXPECTED_DDL_COUNT = 154
EXPECTED_CHARSET = "utf8mb4"
EXPECTED_COLLATION = "utf8mb4_unicode_ci"
CREATE_DATABASE_SQL = (
    "CREATE DATABASE `mitienda_stage100_test` "
    "CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
)


class Stage100BootstrapError(RuntimeError):
    """El bootstrap no puede continuar sin ampliar o reparar estado."""


@dataclass(frozen=True)
class DdlPlan:
    statements: tuple[str, ...]
    create_tables: int
    create_indexes: int
    sha256: str


@dataclass(frozen=True)
class BootstrapEvidence:
    status: str
    database_created: bool
    schema_created: bool
    ddl_executed: int
    ddl_plan_sha256: str
    tables: int
    all_tables_empty: bool
    charset: str
    collation: str
    schema_check: dict[str, object]
    ddl_lifecycles: tuple[dict[str, object], ...]


@dataclass(frozen=True)
class BootstrapPreflightEvidence:
    status: str
    database_state: str
    ddl_plan_sha256: str
    create_tables: int
    create_indexes: int
    target: str
    blockers: tuple[str, ...] = ()


def _normalize_sql(statement: str) -> str:
    return re.sub(r"\s+", " ", statement).strip().rstrip(";")


def canonicalize_ddl_statements(statements: Iterable[str]) -> tuple[str, ...]:
    """Canonicaliza sólo la evidencia; no altera el orden operativo del DDL."""

    return tuple(sorted(_normalize_sql(statement) for statement in statements))


def fingerprint_ddl_statements(statements: Iterable[str]) -> str:
    """Fingerprint determinista del multiconjunto exacto de sentencias DDL."""

    canonical = canonicalize_ddl_statements(statements)
    serialized = json.dumps(
        canonical,
        ensure_ascii=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(serialized).hexdigest()


def render_head_ddl_plan(dialect: Dialect) -> DdlPlan:
    """Renderiza HEAD con el dialecto MySQL ya inicializado del executor."""

    import_all_models()
    statements: list[str] = []

    def capture(sql, *_args, **_kwargs):
        statements.append(_normalize_sql(str(sql.compile(dialect=dialect))))

    engine = create_mock_engine("mysql+pymysql://", capture)
    engine._dialect = dialect
    Base.metadata.create_all(engine, checkfirst=False)
    create_tables = sum(item.upper().startswith("CREATE TABLE ") for item in statements)
    create_indexes = sum(
        item.upper().startswith(("CREATE INDEX ", "CREATE UNIQUE INDEX "))
        for item in statements
    )
    if (
        len(Base.metadata.tables) != EXPECTED_TABLE_COUNT
        or len(statements) != EXPECTED_DDL_COUNT
        or create_tables != EXPECTED_CREATE_TABLE_COUNT
        or create_indexes != EXPECTED_CREATE_INDEX_COUNT
        or any(
            not item.upper().startswith(
                ("CREATE TABLE ", "CREATE INDEX ", "CREATE UNIQUE INDEX ")
            )
            for item in statements
        )
    ):
        raise Stage100BootstrapError("stage100_bootstrap_ddl_plan_unexpected")
    return DdlPlan(
        statements=tuple(statements),
        create_tables=create_tables,
        create_indexes=create_indexes,
        sha256=fingerprint_ddl_statements(statements),
    )


def _server_engine(config: Stage100TargetConfiguration, *, ddl: bool = False) -> Engine:
    reset_url = config.reset_url
    server_url = URL.create(
        drivername=reset_url.drivername,
        username=reset_url.username,
        password=reset_url.password,
        host=reset_url.host,
        port=reset_url.port,
        database=None,
        query=reset_url.query,
    )
    connect_args = {"read_timeout": CLIENT_READ_TIMEOUT_SECONDS} if ddl else {}
    return create_engine(server_url, echo=False, connect_args=connect_args)


def _selected_engine(url, *, ddl: bool = False) -> Engine:
    connect_args = {"read_timeout": CLIENT_READ_TIMEOUT_SECONDS} if ddl else {}
    return create_engine(url, echo=False, connect_args=connect_args)


def _control_engine(config: Stage100TargetConfiguration) -> Engine:
    return create_engine(config.control_url, echo=False)


@contextmanager
def _read_only_connection(engine: Engine):
    """Aísla cada pre/postcheck y lo termina con rollback explícito."""

    connection = engine.connect()
    try:
        yield connection
    finally:
        if connection.in_transaction():
            connection.rollback()
        connection.close()


def _database_metadata(connection: Connection) -> tuple[str, str] | None:
    row = connection.exec_driver_sql(
        "SELECT DEFAULT_CHARACTER_SET_NAME, DEFAULT_COLLATION_NAME "
        "FROM information_schema.SCHEMATA WHERE SCHEMA_NAME = %s",
        (EXPECTED_DATABASE,),
    ).first()
    if row is None:
        return None
    return str(row[0]), str(row[1])


def _validate_database_metadata(value: tuple[str, str] | None) -> tuple[str, str]:
    if value is None:
        raise Stage100BootstrapError("stage100_bootstrap_database_missing")
    charset, collation = value
    if charset != EXPECTED_CHARSET or collation != EXPECTED_COLLATION:
        raise Stage100BootstrapError("stage100_bootstrap_database_charset_mismatch")
    return charset, collation


def _assert_mitienda_denied(connection: Connection) -> None:
    try:
        connection.exec_driver_sql("SELECT 1 FROM `mitienda`.`usuarios` LIMIT 0").all()
    except DBAPIError as exc:
        code = getattr(exc.orig, "args", (None,))[0]
        if code in {1044, 1142}:
            return
        raise Stage100BootstrapError("stage100_mitienda_denial_not_proven") from exc
    raise Stage100BootstrapError("stage100_mitienda_accessible")


def _unexpected_objects(connection: Connection, inspector) -> dict[str, list[str]]:
    objects = {"views": sorted(inspector.get_view_names())}
    for key, table, schema_column, name_column in (
        ("triggers", "TRIGGERS", "TRIGGER_SCHEMA", "TRIGGER_NAME"),
        ("routines", "ROUTINES", "ROUTINE_SCHEMA", "ROUTINE_NAME"),
        ("events", "EVENTS", "EVENT_SCHEMA", "EVENT_NAME"),
    ):
        rows = connection.exec_driver_sql(
            f"SELECT {name_column} FROM information_schema.{table} "
            f"WHERE {schema_column} = %s ORDER BY {name_column}",
            (EXPECTED_DATABASE,),
        ).all()
        objects[key] = [str(row[0]) for row in rows]
    return objects


def _assert_no_unexpected_objects(objects: dict[str, list[str]]) -> None:
    if any(objects.values()):
        raise Stage100BootstrapError("stage100_bootstrap_unexpected_schema_objects")


def _table_counts(connection: Connection, table_names: Iterable[str]) -> dict[str, int]:
    preparer = connection.dialect.identifier_preparer
    return {
        table: int(
            connection.exec_driver_sql(
                f"SELECT COUNT(*) FROM {preparer.quote(table)}"
            ).scalar_one()
        )
        for table in sorted(table_names)
    }


def _privilege_inventory(connection: Connection) -> dict[str, list[tuple[str, ...]]]:
    current_user = str(connection.exec_driver_sql("SELECT CURRENT_USER()").scalar_one())
    username, host = current_user.split("@", 1)
    grantee = f"'{username}'@'{host}'"
    result: dict[str, list[tuple[str, ...]]] = {}
    queries = {
        "schema": (
            "SELECT TABLE_SCHEMA, PRIVILEGE_TYPE FROM information_schema.SCHEMA_PRIVILEGES "
            "WHERE GRANTEE = %s ORDER BY TABLE_SCHEMA, PRIVILEGE_TYPE"
        ),
        "user": (
            "SELECT PRIVILEGE_TYPE FROM information_schema.USER_PRIVILEGES "
            "WHERE GRANTEE = %s ORDER BY PRIVILEGE_TYPE"
        ),
        "table": (
            "SELECT TABLE_SCHEMA, TABLE_NAME, PRIVILEGE_TYPE "
            "FROM information_schema.TABLE_PRIVILEGES WHERE GRANTEE = %s "
            "ORDER BY TABLE_SCHEMA, TABLE_NAME, PRIVILEGE_TYPE"
        ),
        "column": (
            "SELECT TABLE_SCHEMA, TABLE_NAME, COLUMN_NAME, PRIVILEGE_TYPE "
            "FROM information_schema.COLUMN_PRIVILEGES WHERE GRANTEE = %s "
            "ORDER BY TABLE_SCHEMA, TABLE_NAME, COLUMN_NAME, PRIVILEGE_TYPE"
        ),
    }
    for key, query in queries.items():
        result[key] = [tuple(str(value) for value in row) for row in connection.exec_driver_sql(query, (grantee,)).all()]
    return result


def _validate_privilege_inventory(
    inventory: dict[str, list[tuple[str, ...]]], *, role: CredentialRole
) -> None:
    schema = {(row[0], row[1].upper()) for row in inventory["schema"]}
    expected = {(EXPECTED_DATABASE, privilege) for privilege in ROLE_PRIVILEGES[role]}
    user = {row[0].upper() for row in inventory["user"]}
    if schema != expected or user not in (set(), {"USAGE"}):
        raise Stage100BootstrapError("stage100_bootstrap_privilege_inventory_mismatch")
    if inventory["table"] or inventory["column"]:
        raise Stage100BootstrapError("stage100_bootstrap_privilege_inventory_excessive")


def _certify_identity(connection: Connection, *, config, role: CredentialRole, username: str) -> None:
    validate_live_connection(
        connection,
        configured_url=config,
        role=role,
        expected_username=username,
    )
    _validate_privilege_inventory(_privilege_inventory(connection), role=role)
    _assert_mitienda_denied(connection)


def _create_head_schema(connection: Connection, plan: DdlPlan) -> int:
    # La allowlist, multiplicidad y estados de dispatch pertenecen al owner
    # versionado ddl_lifecycle; aquí sólo se emite el plan ya certificado.
    Base.metadata.create_all(bind=connection, checkfirst=False)
    return len(plan.statements)


def classify_existing_schema(
    *,
    tables: set[str],
    schema_ok: bool | None,
    counts: dict[str, int],
    unexpected_objects: dict[str, list[str]],
) -> str:
    """Clasifica sin reparar: sólo vacío o HEAD exacto vacío son aceptables."""

    _assert_no_unexpected_objects(unexpected_objects)
    if not tables:
        if schema_ok is not None or counts:
            raise Stage100BootstrapError("stage100_bootstrap_empty_state_ambiguous")
        return "empty"
    if schema_ok is True and set(counts) == tables and not any(counts.values()):
        return "exact_empty"
    raise Stage100BootstrapError("stage100_bootstrap_existing_schema_not_empty_or_exact")


def _inspect_existing_schema(materializer_connection: Connection):
    inspector = inspect(materializer_connection)
    tables = set(inspector.get_table_names())
    objects = _unexpected_objects(materializer_connection, inspector)
    if not tables:
        state = classify_existing_schema(
            tables=tables,
            schema_ok=None,
            counts={},
            unexpected_objects=objects,
        )
        return state, tables, None, {}
    schema = check_schema(inspector=inspector, metadata=Base.metadata)
    counts = _table_counts(materializer_connection, tables)
    state = classify_existing_schema(
        tables=tables,
        schema_ok=schema.ok,
        counts=counts,
        unexpected_objects=objects,
    )
    return state, tables, schema, counts


def preflight_stage100() -> BootstrapPreflightEvidence:
    """Ejecuta únicamente metadata/SELECT y devuelve el estado pre-bootstrap."""

    config = load_target_configuration()
    server_engine = _server_engine(config)
    database_metadata = None
    try:
        with _read_only_connection(server_engine) as server_connection:
            validate_pre_schema_connection(
                server_connection,
                configured_url=config.reset_url,
                expected_username=config.reset_username,
            )
            _validate_privilege_inventory(
                _privilege_inventory(server_connection), role=CredentialRole.RESET
            )
            _assert_mitienda_denied(server_connection)
            plan = render_head_ddl_plan(server_connection.dialect)
            database_metadata = _database_metadata(server_connection)
    finally:
        server_engine.dispose()

    state = "absent"
    control_engine = _control_engine(config)
    try:
        with _read_only_connection(control_engine) as control_connection:
            validate_control_connection(
                control_connection,
                configured_url=config.control_url,
                expected_username=config.control_username,
            )
            _assert_mitienda_denied(control_connection)
    finally:
        control_engine.dispose()

    if database_metadata is not None:
        _validate_database_metadata(database_metadata)
        reset_engine = _selected_engine(config.reset_url)
        materializer_engine = _selected_engine(config.materializer_url)
        try:
            with _read_only_connection(reset_engine) as reset_connection, _read_only_connection(
                materializer_engine
            ) as materializer_connection:
                _certify_identity(
                    reset_connection,
                    config=config.reset_url,
                    role=CredentialRole.RESET,
                    username=config.reset_username,
                )
                _certify_identity(
                    materializer_connection,
                    config=config.materializer_url,
                    role=CredentialRole.MATERIALIZER,
                    username=config.materializer_username,
                )
                try:
                    state, _tables, _schema, _counts = _inspect_existing_schema(
                        materializer_connection
                    )
                except Stage100BootstrapError as exc:
                    return BootstrapPreflightEvidence(
                        status="BLOCKED",
                        database_state="partial_or_unexpected",
                        ddl_plan_sha256=plan.sha256,
                        create_tables=plan.create_tables,
                        create_indexes=plan.create_indexes,
                        target=EXPECTED_DATABASE,
                        blockers=(str(exc),),
                    )
        finally:
            reset_engine.dispose()
            materializer_engine.dispose()

    return BootstrapPreflightEvidence(
        status="PASS",
        database_state=state,
        ddl_plan_sha256=plan.sha256,
        create_tables=plan.create_tables,
        create_indexes=plan.create_indexes,
        target=EXPECTED_DATABASE,
    )


def bootstrap_stage100(*, apply: bool) -> BootstrapEvidence:
    if apply and os.environ.get(BOOTSTRAP_GATE) != BOOTSTRAP_GATE_VALUE:
        raise Stage100BootstrapError("stage100_bootstrap_opt_in_missing")

    config = load_target_configuration()
    import_all_models()
    database_created = False
    schema_created = False
    ddl_executed = 0
    ddl_lifecycles: list[dict[str, object]] = []

    # Fase 1: todos los prechecks son read-only y sus transacciones quedan
    # cerradas antes de abrir una conexión dedicada al DDL.
    server_engine = _server_engine(config)
    try:
        with _read_only_connection(server_engine) as server_connection:
            validate_pre_schema_connection(
                server_connection,
                configured_url=config.reset_url,
                expected_username=config.reset_username,
            )
            _validate_privilege_inventory(
                _privilege_inventory(server_connection), role=CredentialRole.RESET
            )
            _assert_mitienda_denied(server_connection)
            plan = render_head_ddl_plan(server_connection.dialect)
            database_metadata = _database_metadata(server_connection)
    finally:
        server_engine.dispose()

    if database_metadata is None:
        if not apply:
            raise Stage100BootstrapError("stage100_bootstrap_apply_required")
        ddl_engine = _server_engine(config, ddl=True)
        killer_engine = _server_engine(config)
        observer_engine = _control_engine(config)
        try:
            lifecycle = execute_ddl_batch(
                ddl_engine=ddl_engine,
                killer_engine=killer_engine,
                observer_engine=observer_engine,
                target_database=EXPECTED_DATABASE,
                expected_statements=(CREATE_DATABASE_SQL,),
                normalize=_normalize_sql,
                operation=lambda connection: connection.exec_driver_sql(
                    CREATE_DATABASE_SQL
                ),
            )
            item = asdict(lifecycle)
            item["state"] = lifecycle.state.value
            ddl_lifecycles.append(item)
            database_created = True
        finally:
            ddl_engine.dispose()
            killer_engine.dispose()
            observer_engine.dispose()

    # La certificación del CREATE usa una conexión completamente nueva.
    server_post_engine = _server_engine(config)
    try:
        with _read_only_connection(server_post_engine) as server_connection:
            charset, collation = _validate_database_metadata(
                _database_metadata(server_connection)
            )
    finally:
        server_post_engine.dispose()

    # Fase 2: inspección read-only del schema seleccionado; ambas conexiones
    # se cierran antes del primer CREATE TABLE/INDEX.
    reset_engine = _selected_engine(config.reset_url)
    materializer_engine = _selected_engine(config.materializer_url)
    try:
        with _read_only_connection(reset_engine) as reset_connection, _read_only_connection(
            materializer_engine
        ) as materializer_connection:
            execution_plan = render_head_ddl_plan(reset_connection.dialect)
            if (
                execution_plan.sha256 != plan.sha256
                or Counter(execution_plan.statements) != Counter(plan.statements)
            ):
                raise Stage100BootstrapError(
                    "stage100_bootstrap_execution_plan_mismatch"
                )
            _certify_identity(
                reset_connection,
                config=config.reset_url,
                role=CredentialRole.RESET,
                username=config.reset_username,
            )
            _certify_identity(
                materializer_connection,
                config=config.materializer_url,
                role=CredentialRole.MATERIALIZER,
                username=config.materializer_username,
            )
            state, tables, schema, counts = _inspect_existing_schema(materializer_connection)
            if state not in {"empty", "exact_empty"}:
                raise Stage100BootstrapError("stage100_bootstrap_state_invalid")
    finally:
        reset_engine.dispose()
        materializer_engine.dispose()

    if state == "empty":
        if not apply:
            raise Stage100BootstrapError("stage100_bootstrap_apply_required")
        ddl_engine = _selected_engine(config.reset_url, ddl=True)
        killer_engine = _server_engine(config)
        observer_engine = _control_engine(config)
        try:
            def create_schema(connection: Connection) -> None:
                live_plan = render_head_ddl_plan(connection.dialect)
                if (
                    live_plan.sha256 != execution_plan.sha256
                    or Counter(live_plan.statements)
                    != Counter(execution_plan.statements)
                ):
                    raise Stage100BootstrapError(
                        "stage100_bootstrap_execution_plan_mismatch"
                    )
                _create_head_schema(connection, live_plan)

            lifecycle = execute_ddl_batch(
                ddl_engine=ddl_engine,
                killer_engine=killer_engine,
                observer_engine=observer_engine,
                target_database=EXPECTED_DATABASE,
                expected_statements=execution_plan.statements,
                normalize=_normalize_sql,
                operation=create_schema,
            )
            ddl_executed = lifecycle.completed
            item = asdict(lifecycle)
            item["state"] = lifecycle.state.value
            ddl_lifecycles.append(item)
            schema_created = True
        finally:
            ddl_engine.dispose()
            killer_engine.dispose()
            observer_engine.dispose()

    # Fase 3: postchecks sólo con engines/conexiones nuevas.
    post_engine = _selected_engine(config.materializer_url)
    try:
        with _read_only_connection(post_engine) as post_connection:
            _certify_identity(
                post_connection,
                config=config.materializer_url,
                role=CredentialRole.MATERIALIZER,
                username=config.materializer_username,
            )
            metadata = _validate_database_metadata(_database_metadata(post_connection))
            post_inspector = inspect(post_connection)
            tables = set(post_inspector.get_table_names())
            _assert_no_unexpected_objects(
                _unexpected_objects(post_connection, post_inspector)
            )
            schema = check_schema(inspector=post_inspector, metadata=Base.metadata)
            if not schema.ok or len(tables) != EXPECTED_TABLE_COUNT:
                raise Stage100BootstrapError(
                    "stage100_bootstrap_postcheck_schema_mismatch"
                )
            counts = _table_counts(post_connection, tables)
            if any(counts.values()):
                raise Stage100BootstrapError(
                    "stage100_bootstrap_postcheck_data_present"
                )
            charset, collation = metadata
    finally:
        post_engine.dispose()

    return BootstrapEvidence(
        status="PASS",
        database_created=database_created,
        schema_created=schema_created,
        ddl_executed=ddl_executed + int(database_created),
        ddl_plan_sha256=execution_plan.sha256,
        tables=len(tables),
        all_tables_empty=not any(counts.values()),
        charset=charset,
        collation=collation,
        schema_check=schema_result_to_dict(schema),
        ddl_lifecycles=tuple(ddl_lifecycles),
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--preflight", action="store_true")
    args = parser.parse_args()
    try:
        evidence = preflight_stage100() if args.preflight else bootstrap_stage100(apply=True)
    except DdlLifecycleError as exc:
        lifecycle = asdict(exc.evidence)
        lifecycle["state"] = exc.evidence.state.value
        print(
            json.dumps(
                {"status": "FAIL", "error": str(exc), "ddl_lifecycle": lifecycle},
                sort_keys=True,
            )
        )
        return 1
    except (Stage100BootstrapError, Stage100TargetGuardError) as exc:
        print(json.dumps({"status": "FAIL", "error": str(exc)}, sort_keys=True))
        return 1
    print(json.dumps(asdict(evidence), sort_keys=True))
    return 0 if evidence.status == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
