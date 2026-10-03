"""Prueba live autocontenida del lifecycle DDL de ET100.3.

Sólo opera sobre ``mitienda_stage100_test`` y crea una tabla sonda vacía.
No forma parte del bootstrap ni puede apuntar a otra database.
"""

from __future__ import annotations

from dataclasses import asdict
import argparse
import json
from pathlib import Path
import time

from sqlalchemy import create_engine, inspect
from sqlalchemy.engine import URL

from .bootstrap import (
    CREATE_DATABASE_SQL,
    _assert_mitienda_denied,
    _control_engine,
    _normalize_sql,
    _privilege_inventory,
    _read_only_connection,
    _server_engine,
    _selected_engine,
    _unexpected_objects,
    _validate_privilege_inventory,
)
from .ddl_lifecycle import DdlLifecycleError, DdlLifecycleState, execute_ddl_batch
from .target_guard import (
    CredentialRole,
    EXPECTED_DATABASE,
    load_target_configuration,
    validate_control_connection,
    validate_live_connection,
    validate_pre_schema_connection,
)


PROBE_TABLE = "et1003_ddl_lifecycle_probe"
CREATE_TABLE_SQL = (
    f"CREATE TABLE `{PROBE_TABLE}` (`id` INTEGER NOT NULL, PRIMARY KEY (`id`)) "
    "ENGINE=InnoDB"
)
DROP_TABLE_SQL = f"DROP TABLE `{PROBE_TABLE}`"
DROP_DATABASE_SQL = f"DROP DATABASE `{EXPECTED_DATABASE}`"


class ProbeError(RuntimeError):
    pass


def _load_secret_environment(path: Path) -> dict[str, str]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    required = {
        "FEEDGO_STAGE100_MATERIALIZER_DATABASE_URL",
        "FEEDGO_STAGE100_MATERIALIZER_USER",
        "FEEDGO_STAGE100_RESET_DATABASE_URL",
        "FEEDGO_STAGE100_RESET_USER",
        "FEEDGO_STAGE100_CONTROL_DATABASE_URL",
        "FEEDGO_STAGE100_CONTROL_USER",
    }
    if set(payload) != required or not all(isinstance(payload[key], str) for key in required):
        raise ProbeError("stage100_probe_secret_contract_invalid")
    return payload


def _server_url(url: URL) -> URL:
    return URL.create(
        drivername=url.drivername,
        username=url.username,
        password=url.password,
        host=url.host,
        port=url.port,
        database=None,
        query=url.query,
    )


def _database_exists(connection) -> bool:
    return (
        connection.exec_driver_sql(
            "SELECT COUNT(*) FROM information_schema.SCHEMATA WHERE SCHEMA_NAME = %s",
            (EXPECTED_DATABASE,),
        ).scalar_one()
        == 1
    )


def _execute_one(*, ddl_engine, killer_engine, observer_engine, statement: str):
    return execute_ddl_batch(
        ddl_engine=ddl_engine,
        killer_engine=killer_engine,
        observer_engine=observer_engine,
        target_database=EXPECTED_DATABASE,
        expected_statements=(statement,),
        normalize=_normalize_sql,
        operation=lambda connection: connection.exec_driver_sql(statement),
    )


def _assert_no_other_own_sessions(engine) -> None:
    with _read_only_connection(engine) as connection:
        current_id = int(connection.exec_driver_sql("SELECT CONNECTION_ID()").scalar_one())
        others = [row for row in connection.exec_driver_sql("SHOW PROCESSLIST").all() if int(row[0]) != current_id]
        if others:
            raise ProbeError("stage100_probe_residual_own_sessions")


def _certify_known_connections_gone(config, connection_ids: set[int]) -> tuple[int, int]:
    observer = _control_engine(config)
    try:
        with _read_only_connection(observer) as connection:
            validate_control_connection(
                connection,
                configured_url=config.control_url,
                expected_username=config.control_username,
            )
            if not connection_ids:
                return 0, 0
            placeholders = ", ".join(["%s"] * len(connection_ids))
            values = tuple(sorted(connection_ids))
            sessions = int(
                connection.exec_driver_sql(
                    "SELECT COUNT(PROCESSLIST_ID) FROM performance_schema.threads "
                    f"WHERE PROCESSLIST_ID IN ({placeholders})",
                    values,
                ).scalar_one()
            )
            locks = int(
                connection.exec_driver_sql(
                    "SELECT COUNT(ml.OWNER_THREAD_ID) "
                    "FROM performance_schema.metadata_locks ml "
                    "JOIN performance_schema.threads t "
                    "ON t.THREAD_ID = ml.OWNER_THREAD_ID "
                    f"WHERE t.PROCESSLIST_ID IN ({placeholders}) "
                    "AND ml.LOCK_STATUS IN ('PENDING', 'GRANTED')",
                    values,
                ).scalar_one()
            )
            return sessions, locks
    finally:
        observer.dispose()


def cleanup_current_probe_state(secret_path: Path) -> dict[str, object]:
    config = load_target_configuration(_load_secret_environment(secret_path))
    known_ids: set[int] = set()

    server = _server_engine(config)
    try:
        with _read_only_connection(server) as connection:
            validate_pre_schema_connection(
                connection,
                configured_url=config.reset_url,
                expected_username=config.reset_username,
            )
            _validate_privilege_inventory(
                _privilege_inventory(connection), role=CredentialRole.RESET
            )
            _assert_mitienda_denied(connection)
            if not _database_exists(connection):
                raise ProbeError("stage100_probe_cleanup_target_missing")
    finally:
        server.dispose()

    reset = _selected_engine(config.reset_url)
    materializer = _selected_engine(config.materializer_url)
    observer = _control_engine(config)
    try:
        with _read_only_connection(reset) as reset_connection:
            validate_live_connection(
                reset_connection,
                configured_url=config.reset_url,
                role=CredentialRole.RESET,
                expected_username=config.reset_username,
            )
            _assert_mitienda_denied(reset_connection)
        with _read_only_connection(materializer) as materializer_connection:
            validate_live_connection(
                materializer_connection,
                configured_url=config.materializer_url,
                role=CredentialRole.MATERIALIZER,
                expected_username=config.materializer_username,
            )
            _assert_mitienda_denied(materializer_connection)
            inspector = inspect(materializer_connection)
            if inspector.get_table_names() != [PROBE_TABLE]:
                raise ProbeError("stage100_probe_cleanup_tables_mismatch")
            if any(_unexpected_objects(materializer_connection, inspector).values()):
                raise ProbeError("stage100_probe_cleanup_objects_unexpected")
            if int(
                materializer_connection.exec_driver_sql(
                    f"SELECT COUNT(*) FROM `{PROBE_TABLE}`"
                ).scalar_one()
            ) != 0:
                raise ProbeError("stage100_probe_cleanup_data_present")
        with _read_only_connection(observer) as observer_connection:
            validate_control_connection(
                observer_connection,
                configured_url=config.control_url,
                expected_username=config.control_username,
            )
            _assert_mitienda_denied(observer_connection)
    finally:
        reset.dispose()
        materializer.dispose()
        observer.dispose()

    # Cada cuenta sin PROCESS sólo ve sus propias sesiones: ninguna conexión
    # adicional puede quedar viva antes del DROP.
    reset_server = _server_engine(config)
    materializer_server = create_engine(_server_url(config.materializer_url))
    control_server = _control_engine(config)
    try:
        _assert_no_other_own_sessions(reset_server)
        _assert_no_other_own_sessions(materializer_server)
        _assert_no_other_own_sessions(control_server)
    finally:
        reset_server.dispose()
        materializer_server.dispose()
        control_server.dispose()

    ddl = _server_engine(config, ddl=True)
    killer = _server_engine(config)
    observer = _control_engine(config)
    try:
        evidence = _execute_one(
            ddl_engine=ddl,
            killer_engine=killer,
            observer_engine=observer,
            statement=DROP_DATABASE_SQL,
        )
        known_ids.add(evidence.connection_id)
    finally:
        ddl.dispose()
        killer.dispose()
        observer.dispose()
    if evidence.state is not DdlLifecycleState.COMPLETED:
        raise ProbeError("stage100_probe_cleanup_ddl_incomplete")

    post = _server_engine(config)
    try:
        with _read_only_connection(post) as connection:
            if _database_exists(connection):
                raise ProbeError("stage100_probe_cleanup_failed")
            _assert_mitienda_denied(connection)
    finally:
        post.dispose()
    sessions, locks = _certify_known_connections_gone(config, known_ids)
    if sessions or locks:
        raise ProbeError("stage100_probe_cleanup_residual_lifecycle")
    result = asdict(evidence)
    result["state"] = evidence.state.value
    return {
        "status": "PASS",
        "database_present": False,
        "tables_removed": 1,
        "rows_removed": 0,
        "residual_sessions": sessions,
        "residual_metadata_locks": locks,
        "lifecycle": result,
    }


def run_probe(secret_path: Path) -> dict[str, object]:
    config = load_target_configuration(_load_secret_environment(secret_path))
    server = _server_engine(config)
    try:
        with _read_only_connection(server) as connection:
            validate_pre_schema_connection(
                connection,
                configured_url=config.reset_url,
                expected_username=config.reset_username,
            )
            _validate_privilege_inventory(
                _privilege_inventory(connection), role=CredentialRole.RESET
            )
            _assert_mitienda_denied(connection)
            if _database_exists(connection):
                raise ProbeError("stage100_probe_target_must_be_absent")
    finally:
        server.dispose()

    materializer_server = create_engine(_server_url(config.materializer_url))
    try:
        with _read_only_connection(materializer_server) as connection:
            if connection.exec_driver_sql("SELECT DATABASE()").scalar_one() is not None:
                raise ProbeError("stage100_probe_materializer_database_selected")
            current = str(connection.exec_driver_sql("SELECT CURRENT_USER()").scalar_one())
            if current != f"{config.materializer_username}@localhost":
                raise ProbeError("stage100_probe_materializer_identity_mismatch")
            _validate_privilege_inventory(
                _privilege_inventory(connection), role=CredentialRole.MATERIALIZER
            )
            _assert_mitienda_denied(connection)
    finally:
        materializer_server.dispose()

    created = False
    cancellation = None
    elapsed = None
    cleanup = None
    holder_engine = None
    holder = None
    known_ids: set[int] = set()
    try:
        create_engine_ddl = _server_engine(config, ddl=True)
        create_killer = _server_engine(config)
        create_observer = _control_engine(config)
        try:
            create_evidence = _execute_one(
                ddl_engine=create_engine_ddl,
                killer_engine=create_killer,
                observer_engine=create_observer,
                statement=CREATE_DATABASE_SQL,
            )
        finally:
            create_engine_ddl.dispose()
            create_killer.dispose()
            create_observer.dispose()
        if create_evidence.state is not DdlLifecycleState.COMPLETED:
            raise ProbeError("stage100_probe_create_database_incomplete")
        known_ids.add(create_evidence.connection_id)
        created = True

        reset_ddl = _selected_engine(config.reset_url, ddl=True)
        reset_killer = _server_engine(config)
        reset_observer = _control_engine(config)
        try:
            table_evidence = _execute_one(
                ddl_engine=reset_ddl,
                killer_engine=reset_killer,
                observer_engine=reset_observer,
                statement=CREATE_TABLE_SQL,
            )
        finally:
            reset_ddl.dispose()
            reset_killer.dispose()
            reset_observer.dispose()
        if table_evidence.state is not DdlLifecycleState.COMPLETED:
            raise ProbeError("stage100_probe_create_table_incomplete")
        known_ids.add(table_evidence.connection_id)

        holder_engine = _selected_engine(config.materializer_url)
        holder = holder_engine.connect()
        known_ids.add(int(holder.exec_driver_sql("SELECT CONNECTION_ID()").scalar_one()))
        validate_live_connection(
            holder,
            configured_url=config.materializer_url,
            role=CredentialRole.MATERIALIZER,
            expected_username=config.materializer_username,
        )
        holder.exec_driver_sql(f"SELECT * FROM `{PROBE_TABLE}`").all()

        drop_engine = _selected_engine(config.reset_url, ddl=True)
        drop_killer = _server_engine(config)
        drop_observer = _control_engine(config)
        started = time.monotonic()
        try:
            try:
                _execute_one(
                    ddl_engine=drop_engine,
                    killer_engine=drop_killer,
                    observer_engine=drop_observer,
                    statement=DROP_TABLE_SQL,
                )
                raise ProbeError("stage100_probe_lock_did_not_block")
            except DdlLifecycleError as exc:
                elapsed = time.monotonic() - started
                cancellation = exc.evidence
                known_ids.add(cancellation.connection_id)
        finally:
            drop_engine.dispose()
            drop_killer.dispose()
            drop_observer.dispose()

        if (
            cancellation is None
            or cancellation.state is not DdlLifecycleState.UNKNOWN
            or cancellation.dispatched != 1
            or cancellation.completed != 0
            or not cancellation.cancellation_confirmed
            or elapsed is None
            or not 4.0 <= elapsed <= 15.0
        ):
            raise ProbeError("stage100_probe_cancellation_contract_failed")

        # El DROP fallido no puede ejecutarse luego: la tabla debe seguir ahí.
        verify_engine = _selected_engine(config.materializer_url)
        try:
            with _read_only_connection(verify_engine) as connection:
                if PROBE_TABLE not in inspect(connection).get_table_names():
                    raise ProbeError("stage100_probe_drop_executed_after_cancel")
        finally:
            verify_engine.dispose()
    finally:
        if holder is not None:
            if holder.in_transaction():
                holder.rollback()
            holder.close()
        if holder_engine is not None:
            holder_engine.dispose()

        # Limpieza exclusiva de los objetos creados por esta sonda. Sólo se
        # ejecuta si la cancelación quedó inequívocamente confirmada.
        if created and (cancellation is None or cancellation.cancellation_confirmed):
            cleanup_ddl = _server_engine(config, ddl=True)
            cleanup_killer = _server_engine(config)
            cleanup_observer = _control_engine(config)
            try:
                cleanup = _execute_one(
                    ddl_engine=cleanup_ddl,
                    killer_engine=cleanup_killer,
                    observer_engine=cleanup_observer,
                    statement=DROP_DATABASE_SQL,
                )
                known_ids.add(cleanup.connection_id)
            finally:
                cleanup_ddl.dispose()
                cleanup_killer.dispose()
                cleanup_observer.dispose()

    if cancellation is None or cleanup is None:
        raise ProbeError("stage100_probe_incomplete")

    final_engine = _server_engine(config)
    try:
        with _read_only_connection(final_engine) as connection:
            if _database_exists(connection):
                raise ProbeError("stage100_probe_cleanup_failed")
    finally:
        final_engine.dispose()

    residual, locks = _certify_known_connections_gone(config, known_ids)
    reset_server = _server_engine(config)
    materializer_server = create_engine(_server_url(config.materializer_url))
    control_server = _control_engine(config)
    try:
        _assert_no_other_own_sessions(reset_server)
        _assert_no_other_own_sessions(materializer_server)
        _assert_no_other_own_sessions(control_server)
    finally:
        reset_server.dispose()
        materializer_server.dispose()
        control_server.dispose()

    if residual or locks:
        raise ProbeError("stage100_probe_residual_sessions_or_locks")

    cancellation_dict = asdict(cancellation)
    cancellation_dict["state"] = cancellation.state.value
    cleanup_dict = asdict(cleanup)
    cleanup_dict["state"] = cleanup.state.value
    return {
        "status": "PASS",
        "target": EXPECTED_DATABASE,
        "lock_wait_elapsed_seconds": round(float(elapsed), 3),
        "cancellation": cancellation_dict,
        "cleanup": cleanup_dict,
        "residual_sessions": residual,
        "residual_metadata_locks": locks,
        "database_present": False,
        "retry_count": 0,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--secrets-file", required=True, type=Path)
    parser.add_argument("--cleanup-current", action="store_true")
    args = parser.parse_args()
    try:
        result = (
            cleanup_current_probe_state(args.secrets_file)
            if args.cleanup_current
            else run_probe(args.secrets_file)
        )
    except Exception as exc:
        print(json.dumps({"status": "FAIL", "error": str(exc)}, sort_keys=True))
        return 1
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
