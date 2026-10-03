"""Provision focal de la credencial observadora ET100.3."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import secrets

from sqlalchemy import create_engine
from sqlalchemy.engine import URL, make_url
from sqlalchemy.exc import DBAPIError

from .target_guard import (
    load_target_configuration,
    validate_control_connection,
    validate_control_grants,
)


CONTROL_USERNAME = "feedgo_stage100_control"
CONTROL_HOST = "localhost"
PROVISION_GATE = "FEEDGO_STAGE100_PROVISION_CONTROL"


class ControlProvisionError(RuntimeError):
    pass


def _dbapi_code(exc: DBAPIError) -> int | None:
    args = getattr(exc.orig, "args", ())
    return args[0] if args and isinstance(args[0], int) else None


def _must_be_denied(connection, statement: str, codes: set[int]) -> None:
    try:
        connection.exec_driver_sql(statement).all()
    except DBAPIError as exc:
        if _dbapi_code(exc) in codes:
            if connection.in_transaction():
                connection.rollback()
            return
        raise ControlProvisionError("stage100_control_unexpected_denial") from exc
    raise ControlProvisionError("stage100_control_forbidden_operation_allowed")


def _server_url(raw_url: str) -> URL:
    source = make_url(raw_url)
    if source.drivername != "mysql+pymysql" or source.host not in {
        "localhost",
        "127.0.0.1",
        "::1",
    }:
        raise ControlProvisionError("stage100_control_admin_target_invalid")
    return URL.create(
        drivername=source.drivername,
        username=source.username,
        password=source.password,
        host=source.host,
        port=source.port,
        database=None,
    )


def provision(secret_path: Path) -> dict[str, object]:
    if os.environ.get(PROVISION_GATE) != "apply":
        raise ControlProvisionError("stage100_control_provision_opt_in_missing")
    admin = os.environ.get("FEEDGO_STAGE100_ADMIN_DATABASE_URL", "")
    if not admin:
        raise ControlProvisionError("stage100_control_admin_url_missing")

    payload = json.loads(secret_path.read_text(encoding="utf-8"))
    if any(key.startswith("FEEDGO_STAGE100_CONTROL_") for key in payload):
        raise ControlProvisionError("stage100_control_secret_already_present")

    password = secrets.token_urlsafe(48)
    engine = create_engine(_server_url(admin))
    try:
        with engine.connect() as connection:
            if connection.exec_driver_sql("SELECT DATABASE()").scalar_one() is not None:
                raise ControlProvisionError("stage100_control_admin_database_selected")
            current = str(connection.exec_driver_sql("SELECT CURRENT_USER()").scalar_one())
            if current != "root@localhost":
                raise ControlProvisionError("stage100_control_admin_identity_invalid")
            exists = int(
                connection.exec_driver_sql(
                    "SELECT COUNT(*) FROM mysql.user WHERE User = %s AND Host = %s",
                    (CONTROL_USERNAME, CONTROL_HOST),
                ).scalar_one()
            )
            if exists:
                raise ControlProvisionError("stage100_control_account_already_exists")

            connection.exec_driver_sql(
                "CREATE USER 'feedgo_stage100_control'@'localhost' "
                "IDENTIFIED BY %s WITH MAX_USER_CONNECTIONS 2 "
                "PASSWORD EXPIRE NEVER ACCOUNT UNLOCK",
                (password,),
            )
            connection.exec_driver_sql(
                "GRANT SELECT (`THREAD_ID`, `PROCESSLIST_ID`, `PROCESSLIST_COMMAND`) "
                "ON `performance_schema`.`threads` "
                "TO 'feedgo_stage100_control'@'localhost'"
            )
            connection.exec_driver_sql(
                "GRANT SELECT (`OWNER_THREAD_ID`, `LOCK_STATUS`) "
                "ON `performance_schema`.`metadata_locks` "
                "TO 'feedgo_stage100_control'@'localhost'"
            )
            rows = connection.exec_driver_sql(
                "SHOW GRANTS FOR 'feedgo_stage100_control'@'localhost'"
            ).all()
            grants = [str(row[0]) for row in rows]
            validate_control_grants(grants)
    except Exception as exc:
        if isinstance(exc, ControlProvisionError):
            raise
        raise ControlProvisionError("stage100_control_provision_failed") from exc
    finally:
        engine.dispose()

    control_url = URL.create(
        drivername="mysql+pymysql",
        username=CONTROL_USERNAME,
        password=password,
        host="localhost",
        database=None,
    ).render_as_string(hide_password=False)
    payload["FEEDGO_STAGE100_CONTROL_DATABASE_URL"] = control_url
    payload["FEEDGO_STAGE100_CONTROL_USER"] = CONTROL_USERNAME
    secret_path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return {"status": "PASS", "username": CONTROL_USERNAME, "grants": 2}


def verify(secret_path: Path) -> dict[str, object]:
    payload = json.loads(secret_path.read_text(encoding="utf-8"))
    config = load_target_configuration(payload)
    control_engine = create_engine(config.control_url)
    reset_engine = create_engine(_server_url(config.reset_url))
    try:
        with reset_engine.connect() as reset, control_engine.connect() as control:
            validate_control_connection(
                control,
                configured_url=config.control_url,
                expected_username=config.control_username,
            )
            effective_grants = [
                str(row[0]) for row in control.exec_driver_sql("SHOW GRANTS").all()
            ]
            control.exec_driver_sql(
                "SELECT THREAD_ID, PROCESSLIST_ID, PROCESSLIST_COMMAND "
                "FROM performance_schema.threads LIMIT 1"
            ).all()
            control.exec_driver_sql(
                "SELECT OWNER_THREAD_ID, LOCK_STATUS "
                "FROM performance_schema.metadata_locks LIMIT 1"
            ).all()
            _must_be_denied(
                control,
                "SELECT PROCESSLIST_INFO FROM performance_schema.threads LIMIT 1",
                {1143},
            )
            _must_be_denied(
                control,
                "SELECT OBJECT_SCHEMA FROM performance_schema.metadata_locks LIMIT 1",
                {1143},
            )
            _must_be_denied(
                control,
                "SELECT 1 FROM `mitienda`.`usuarios` LIMIT 0",
                {1044, 1142},
            )
            target_present = int(
                reset.exec_driver_sql(
                    "SELECT COUNT(*) FROM information_schema.SCHEMATA "
                    "WHERE SCHEMA_NAME = %s",
                    ("mitienda_stage100_test",),
                ).scalar_one()
            ) == 1
            if target_present:
                _must_be_denied(
                    control,
                    "SELECT 1 FROM `mitienda_stage100_test`."
                    "`et1003_ddl_lifecycle_probe` LIMIT 0",
                    {1044, 1142},
                )
            _must_be_denied(
                control,
                "CREATE TABLE `mitienda_stage100_test`."
                "`et1003_control_forbidden` (`id` INTEGER)",
                {1044, 1142},
            )
            reset_id = int(reset.exec_driver_sql("SELECT CONNECTION_ID()").scalar_one())
            _must_be_denied(control, f"KILL QUERY {reset_id}", {1095})
            roles = str(control.exec_driver_sql("SELECT CURRENT_ROLE()").scalar_one())
            user_privileges = {
                str(row[0]).upper()
                for row in control.exec_driver_sql(
                    "SELECT PRIVILEGE_TYPE FROM information_schema.USER_PRIVILEGES "
                    "WHERE GRANTEE = %s",
                    (f"'{config.control_username}'@'localhost'",),
                ).all()
            }
            if roles not in {"NONE", ""} or user_privileges not in (set(), {"USAGE"}):
                raise ControlProvisionError("stage100_control_global_privilege_detected")
            if control.in_transaction():
                control.rollback()
            if reset.in_transaction():
                reset.rollback()
    finally:
        control_engine.dispose()
        reset_engine.dispose()
    return {
        "status": "PASS",
        "allowed_column_sets": 2,
        "forbidden_columns_denied": True,
        "mitienda_denied": True,
        "stage100_data_denied": True if target_present else "target_absent",
        "ddl_denied": True,
        "kill_denied": True,
        "global_privileges": 0,
        "roles": 0,
        "effective_grants": effective_grants,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--secrets-file", required=True, type=Path)
    parser.add_argument("--verify", action="store_true")
    args = parser.parse_args()
    try:
        result = verify(args.secrets_file) if args.verify else provision(args.secrets_file)
    except ControlProvisionError as exc:
        print(json.dumps({"status": "FAIL", "error": str(exc)}, sort_keys=True))
        return 1
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
