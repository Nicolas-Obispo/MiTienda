"""Reset tecnico, destructivo y fail-closed del laboratorio ET100.3."""

from __future__ import annotations

from collections import Counter
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import json
import os

from sqlalchemy import inspect
from sqlalchemy.engine import Connection
from sqlalchemy.orm import Session

from app.core.database import Base
from app.core.model_registry import import_all_models
from check_database_schema import check_schema

from .apply import (
    _certify_post_apply,
    SyntheticApplyError,
    require_fixture_secret,
)
from .blueprint import BlueprintContractError, ClockPolicy
from .bootstrap import (
    CREATE_DATABASE_SQL,
    EXPECTED_CREATE_INDEX_COUNT,
    EXPECTED_CREATE_TABLE_COUNT,
    EXPECTED_TABLE_COUNT,
    DdlPlan,
    Stage100BootstrapError,
    _assert_mitienda_denied,
    _assert_no_unexpected_objects,
    _certify_identity,
    _control_engine,
    _create_head_schema,
    _database_metadata,
    _inspect_existing_schema,
    _normalize_sql,
    _privilege_inventory,
    _read_only_connection,
    _selected_engine,
    _server_engine,
    _table_counts,
    _unexpected_objects,
    _validate_database_metadata,
    _validate_privilege_inventory,
    render_head_ddl_plan,
)
from .ddl_lifecycle import DdlLifecycleError, DdlLifecycleEvidence, execute_ddl_batch
from .materializer import MaterializationError, certify_materialized_blueprint_read_only
from .scenarios import compile_scenario
from .target_guard import (
    CredentialRole,
    EXPECTED_DATABASE,
    Stage100TargetConfiguration,
    Stage100TargetGuardError,
    load_target_configuration,
    validate_control_connection,
    validate_pre_schema_connection,
)


SYNTHETIC_RESET_GATE = "FEEDGO_STAGE100_SYNTHETIC_RESET"
SYNTHETIC_RESET_GATE_VALUE = "apply"
EXPECTED_SMOKE_FINGERPRINT = (
    "270e49fbb75c5dfb28baa98e4e888370b551cb88ac7707f56afad5e934ddb8cb"
)
EXPECTED_DDL_PLAN_SHA256 = (
    "27758f1f0794d9fa04daf38de2dd23096d11af8858119adbb517a3383e091322"
)
DROP_DATABASE_SQL = "DROP DATABASE `mitienda_stage100_test`"
POSTCONDITION = "HEAD_EMPTY_PASS"


class SyntheticResetError(RuntimeError):
    """El reset no puede iniciarse o su resultado no pudo certificarse."""


@dataclass(frozen=True)
class SyntheticResetEvidence:
    status: str
    target: str
    previous_profile: str
    previous_rows: int
    previous_fingerprint: str
    ddl_plan_sha256: str
    drop: dict[str, object]
    create_database: dict[str, object]
    create_schema: dict[str, object]
    tables: int
    all_tables_empty: bool
    postcondition: str


def _lifecycle_dict(evidence: DdlLifecycleEvidence) -> dict[str, object]:
    item = asdict(evidence)
    item["state"] = evidence.state.value
    return item


def _expected_smoke_blueprint():
    blueprint = compile_scenario(
        dataset_version="et100.3-v1",
        profile="smoke",
        seed="approved-profile-seed-001",
        clock_policy=ClockPolicy(
            anchor=datetime(2026, 1, 15, 12, 0, tzinfo=timezone.utc)
        ),
    )
    if blueprint.fingerprint != EXPECTED_SMOKE_FINGERPRINT:
        raise SyntheticResetError("synthetic_reset_expected_fingerprint_drift")
    return blueprint


def _validate_plan(plan: DdlPlan) -> None:
    if (
        plan.sha256 != EXPECTED_DDL_PLAN_SHA256
        or plan.create_tables != EXPECTED_CREATE_TABLE_COUNT
        or plan.create_indexes != EXPECTED_CREATE_INDEX_COUNT
        or len(plan.statements)
        != EXPECTED_CREATE_TABLE_COUNT + EXPECTED_CREATE_INDEX_COUNT
    ):
        raise SyntheticResetError("synthetic_reset_ddl_plan_mismatch")


def _certify_server_and_observer(config: Stage100TargetConfiguration) -> DdlPlan:
    server_engine = _server_engine(config)
    try:
        with _read_only_connection(server_engine) as connection:
            validate_pre_schema_connection(
                connection,
                configured_url=config.reset_url,
                expected_username=config.reset_username,
            )
            _validate_privilege_inventory(
                _privilege_inventory(connection), role=CredentialRole.RESET
            )
            _assert_mitienda_denied(connection)
            if _database_metadata(connection) is None:
                raise SyntheticResetError("synthetic_reset_database_missing")
            plan = render_head_ddl_plan(connection.dialect)
            _validate_plan(plan)
    finally:
        server_engine.dispose()

    control_engine = _control_engine(config)
    try:
        with _read_only_connection(control_engine) as connection:
            validate_control_connection(
                connection,
                configured_url=config.control_url,
                expected_username=config.control_username,
            )
            _assert_mitienda_denied(connection)
    finally:
        control_engine.dispose()
    return plan


def _certify_current_smoke(
    config: Stage100TargetConfiguration,
    *,
    fixture_secret: str,
    blueprint,
) -> None:
    reset_engine = _selected_engine(config.reset_url)
    materializer_engine = _selected_engine(config.materializer_url)
    try:
        with _read_only_connection(reset_engine) as reset_connection:
            _certify_identity(
                reset_connection,
                config=config.reset_url,
                role=CredentialRole.RESET,
                username=config.reset_username,
            )
        with Session(materializer_engine) as session:
            connection = session.connection()
            _certify_post_apply(connection, config=config, blueprint=blueprint)
            certification = certify_materialized_blueprint_read_only(
                session,
                blueprint,
                fixture_secret=fixture_secret,
            )
            if (
                certification.profile != "smoke"
                or certification.row_count != 20
                or certification.fingerprint != EXPECTED_SMOKE_FINGERPRINT
            ):
                raise SyntheticResetError("synthetic_reset_current_smoke_mismatch")
            session.rollback()
    finally:
        reset_engine.dispose()
        materializer_engine.dispose()


def _run_ddl_phase(
    config: Stage100TargetConfiguration,
    *,
    selected_database: bool,
    statements: tuple[str, ...],
    operation,
) -> DdlLifecycleEvidence:
    ddl_engine = (
        _selected_engine(config.reset_url, ddl=True)
        if selected_database
        else _server_engine(config, ddl=True)
    )
    killer_engine = _server_engine(config)
    observer_engine = _control_engine(config)
    try:
        return execute_ddl_batch(
            ddl_engine=ddl_engine,
            killer_engine=killer_engine,
            observer_engine=observer_engine,
            target_database=EXPECTED_DATABASE,
            expected_statements=statements,
            normalize=_normalize_sql,
            operation=operation,
        )
    finally:
        ddl_engine.dispose()
        killer_engine.dispose()
        observer_engine.dispose()


def _certify_database_absent(config: Stage100TargetConfiguration) -> None:
    server_engine = _server_engine(config)
    control_engine = _control_engine(config)
    try:
        with _read_only_connection(server_engine) as connection:
            validate_pre_schema_connection(
                connection,
                configured_url=config.reset_url,
                expected_username=config.reset_username,
            )
            _validate_privilege_inventory(
                _privilege_inventory(connection), role=CredentialRole.RESET
            )
            _assert_mitienda_denied(connection)
            if _database_metadata(connection) is not None:
                raise SyntheticResetError("synthetic_reset_drop_postcheck_failed")
        with _read_only_connection(control_engine) as connection:
            validate_control_connection(
                connection,
                configured_url=config.control_url,
                expected_username=config.control_username,
            )
            _assert_mitienda_denied(connection)
    finally:
        server_engine.dispose()
        control_engine.dispose()


def _certify_database_empty(
    config: Stage100TargetConfiguration,
    *,
    plan: DdlPlan,
) -> DdlPlan:
    reset_engine = _selected_engine(config.reset_url)
    materializer_engine = _selected_engine(config.materializer_url)
    control_engine = _control_engine(config)
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
            _validate_database_metadata(_database_metadata(materializer_connection))
            live_plan = render_head_ddl_plan(reset_connection.dialect)
            _validate_plan(live_plan)
            if (
                live_plan.sha256 != plan.sha256
                or Counter(live_plan.statements) != Counter(plan.statements)
            ):
                raise SyntheticResetError("synthetic_reset_execution_plan_mismatch")
            state, _tables, _schema, _counts = _inspect_existing_schema(
                materializer_connection
            )
            if state != "empty":
                raise SyntheticResetError("synthetic_reset_recreated_database_not_empty")
        with _read_only_connection(control_engine) as connection:
            validate_control_connection(
                connection,
                configured_url=config.control_url,
                expected_username=config.control_username,
            )
            _assert_mitienda_denied(connection)
        return live_plan
    finally:
        reset_engine.dispose()
        materializer_engine.dispose()
        control_engine.dispose()


def _certify_head_empty(config: Stage100TargetConfiguration) -> tuple[int, bool]:
    reset_engine = _selected_engine(config.reset_url)
    materializer_engine = _selected_engine(config.materializer_url)
    control_engine = _control_engine(config)
    try:
        with _read_only_connection(reset_engine) as reset_connection:
            _certify_identity(
                reset_connection,
                config=config.reset_url,
                role=CredentialRole.RESET,
                username=config.reset_username,
            )
        with _read_only_connection(materializer_engine) as connection:
            _certify_identity(
                connection,
                config=config.materializer_url,
                role=CredentialRole.MATERIALIZER,
                username=config.materializer_username,
            )
            _validate_database_metadata(_database_metadata(connection))
            inspector = inspect(connection)
            tables = set(inspector.get_table_names())
            _assert_no_unexpected_objects(_unexpected_objects(connection, inspector))
            schema = check_schema(inspector=inspector, metadata=Base.metadata)
            counts = _table_counts(connection, tables)
            if (
                not schema.ok
                or tables != set(Base.metadata.tables)
                or len(tables) != EXPECTED_TABLE_COUNT
                or set(counts) != tables
                or any(counts.values())
            ):
                raise SyntheticResetError("synthetic_reset_head_empty_postcheck_failed")
        with _read_only_connection(control_engine) as connection:
            validate_control_connection(
                connection,
                configured_url=config.control_url,
                expected_username=config.control_username,
            )
            _assert_mitienda_denied(connection)
    finally:
        reset_engine.dispose()
        materializer_engine.dispose()
        control_engine.dispose()
    return len(tables), not any(counts.values())


def reset_synthetic_lab(
    *, environment: dict[str, str] | None = None
) -> SyntheticResetEvidence:
    environment = os.environ if environment is None else environment
    if environment.get(SYNTHETIC_RESET_GATE) != SYNTHETIC_RESET_GATE_VALUE:
        raise SyntheticResetError("synthetic_reset_opt_in_missing")

    config = load_target_configuration(environment)
    fixture_secret = require_fixture_secret(environment)
    import_all_models()
    blueprint = _expected_smoke_blueprint()
    plan = _certify_server_and_observer(config)
    _certify_current_smoke(
        config,
        fixture_secret=fixture_secret,
        blueprint=blueprint,
    )

    drop = _run_ddl_phase(
        config,
        selected_database=False,
        statements=(DROP_DATABASE_SQL,),
        operation=lambda connection: connection.exec_driver_sql(DROP_DATABASE_SQL),
    )
    _certify_database_absent(config)

    create_database = _run_ddl_phase(
        config,
        selected_database=False,
        statements=(CREATE_DATABASE_SQL,),
        operation=lambda connection: connection.exec_driver_sql(CREATE_DATABASE_SQL),
    )
    execution_plan = _certify_database_empty(config, plan=plan)

    def create_schema(connection: Connection) -> None:
        live_plan = render_head_ddl_plan(connection.dialect)
        _validate_plan(live_plan)
        if (
            live_plan.sha256 != execution_plan.sha256
            or Counter(live_plan.statements) != Counter(execution_plan.statements)
        ):
            raise SyntheticResetError("synthetic_reset_execution_plan_mismatch")
        _create_head_schema(connection, live_plan)

    create_schema_evidence = _run_ddl_phase(
        config,
        selected_database=True,
        statements=execution_plan.statements,
        operation=create_schema,
    )
    tables, all_empty = _certify_head_empty(config)

    return SyntheticResetEvidence(
        status="PASS",
        target=EXPECTED_DATABASE,
        previous_profile="smoke",
        previous_rows=20,
        previous_fingerprint=EXPECTED_SMOKE_FINGERPRINT,
        ddl_plan_sha256=execution_plan.sha256,
        drop=_lifecycle_dict(drop),
        create_database=_lifecycle_dict(create_database),
        create_schema=_lifecycle_dict(create_schema_evidence),
        tables=tables,
        all_tables_empty=all_empty,
        postcondition=POSTCONDITION,
    )


def main() -> int:
    try:
        evidence = reset_synthetic_lab()
    except DdlLifecycleError as exc:
        lifecycle = _lifecycle_dict(exc.evidence)
        print(
            json.dumps(
                {"status": "FAIL", "error": str(exc), "ddl_lifecycle": lifecycle},
                sort_keys=True,
            )
        )
        return 1
    except (
        Stage100BootstrapError,
        Stage100TargetGuardError,
        SyntheticApplyError,
        BlueprintContractError,
        MaterializationError,
        SyntheticResetError,
    ) as exc:
        print(json.dumps({"status": "FAIL", "error": str(exc)}, sort_keys=True))
        return 1
    print(json.dumps(asdict(evidence), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
