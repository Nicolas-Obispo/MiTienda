"""Guardas fail-closed para el MySQL aislado de ET100.3.

Este modulo no crea conexiones ni ejecuta DDL/DML. Valida configuracion,
identidad efectiva y grants antes de que futuros comandos sinteticos puedan
operar sobre la base aislada aprobada.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import os
import re
from typing import Iterable, Protocol

from sqlalchemy.engine import Connection, URL, make_url


EXPECTED_DATABASE = "mitienda_stage100_test"
LOCAL_HOSTS = frozenset({"localhost", "127.0.0.1", "::1"})


class CredentialRole(str, Enum):
    MATERIALIZER = "materializer"
    RESET = "reset"
    CONTROL = "control"


ROLE_PRIVILEGES = {
    CredentialRole.MATERIALIZER: frozenset({"SELECT", "INSERT", "UPDATE", "DELETE"}),
    CredentialRole.RESET: frozenset({"CREATE", "DROP", "ALTER", "INDEX", "REFERENCES"}),
}

CONTROL_COLUMNS = {
    "performance_schema.threads": frozenset(
        {"THREAD_ID", "PROCESSLIST_ID", "PROCESSLIST_COMMAND"}
    ),
    "performance_schema.metadata_locks": frozenset(
        {"OWNER_THREAD_ID", "LOCK_STATUS"}
    ),
}


class Stage100TargetGuardError(RuntimeError):
    """La frontera aislada de ET100.3 no pudo demostrarse."""


@dataclass(frozen=True)
class ValidatedTarget:
    role: CredentialRole
    database: str
    username: str


@dataclass(frozen=True)
class Stage100TargetConfiguration:
    materializer_url: URL
    reset_url: URL
    materializer_username: str
    reset_username: str
    control_url: URL
    control_username: str


class ScalarResult(Protocol):
    def scalar_one(self) -> object: ...


_GRANT_RE = re.compile(
    r"^GRANT\s+(?P<privileges>.+?)\s+ON\s+(?P<scope>.+?)\s+TO\s+",
    re.IGNORECASE,
)


def validate_configured_target(
    raw_url: str,
    *,
    role: CredentialRole,
    expected_username: str,
) -> URL:
    """Valida el target configurado sin conectarse ni revelar secretos."""
    if not raw_url or not expected_username:
        raise Stage100TargetGuardError("stage100_target_configuration_missing")

    try:
        url = make_url(raw_url)
    except Exception as exc:  # SQLAlchemy expone distintos errores por formato.
        raise Stage100TargetGuardError("stage100_target_url_invalid") from exc

    if url.drivername != "mysql+pymysql":
        raise Stage100TargetGuardError("stage100_target_driver_invalid")
    if url.host not in LOCAL_HOSTS:
        raise Stage100TargetGuardError("stage100_target_host_invalid")
    if url.database != EXPECTED_DATABASE:
        raise Stage100TargetGuardError("stage100_target_database_invalid")
    if url.query:
        raise Stage100TargetGuardError("stage100_target_query_not_allowed")
    if not url.username or url.password is None or url.username != expected_username:
        raise Stage100TargetGuardError("stage100_target_identity_invalid")
    if role not in ROLE_PRIVILEGES:
        raise Stage100TargetGuardError("stage100_target_role_invalid")
    return url


def validate_distinct_credentials(
    *urls: URL,
) -> None:
    usernames = [url.username for url in urls]
    if any(not username for username in usernames):
        raise Stage100TargetGuardError("stage100_target_identity_invalid")
    if len(set(usernames)) != len(usernames):
        raise Stage100TargetGuardError("stage100_credentials_must_be_distinct")


def validate_control_target(raw_url: str, *, expected_username: str) -> URL:
    if not raw_url or not expected_username:
        raise Stage100TargetGuardError("stage100_control_configuration_missing")
    try:
        url = make_url(raw_url)
    except Exception as exc:
        raise Stage100TargetGuardError("stage100_control_url_invalid") from exc
    if (
        url.drivername != "mysql+pymysql"
        or url.host not in LOCAL_HOSTS
        or url.database not in (None, "")
        or url.query
        or url.username != expected_username
        or url.password is None
    ):
        raise Stage100TargetGuardError("stage100_control_target_invalid")
    return url


def load_target_configuration(
    environment: dict[str, str] | None = None,
) -> Stage100TargetConfiguration:
    """Carga las dos credenciales sin imprimir ni conservar URLs crudas."""
    environment = os.environ if environment is None else environment
    materializer_username = environment.get("FEEDGO_STAGE100_MATERIALIZER_USER", "")
    reset_username = environment.get("FEEDGO_STAGE100_RESET_USER", "")
    control_username = environment.get("FEEDGO_STAGE100_CONTROL_USER", "")
    materializer_url = validate_configured_target(
        environment.get("FEEDGO_STAGE100_MATERIALIZER_DATABASE_URL", ""),
        role=CredentialRole.MATERIALIZER,
        expected_username=materializer_username,
    )
    reset_url = validate_configured_target(
        environment.get("FEEDGO_STAGE100_RESET_DATABASE_URL", ""),
        role=CredentialRole.RESET,
        expected_username=reset_username,
    )
    control_url = validate_control_target(
        environment.get("FEEDGO_STAGE100_CONTROL_DATABASE_URL", ""),
        expected_username=control_username,
    )
    validate_distinct_credentials(materializer_url, reset_url, control_url)
    return Stage100TargetConfiguration(
        materializer_url=materializer_url,
        reset_url=reset_url,
        materializer_username=materializer_username,
        reset_username=reset_username,
        control_url=control_url,
        control_username=control_username,
    )


def _normalize_scope(scope: str) -> str:
    return scope.replace("`", "").strip()


def _parse_privileges(value: str) -> frozenset[str]:
    privileges = frozenset(part.strip().upper() for part in value.split(","))
    if not privileges or "ALL PRIVILEGES" in privileges or "GRANT OPTION" in privileges:
        raise Stage100TargetGuardError("stage100_grants_excessive")
    return privileges


def validate_grants(grants: Iterable[str], *, role: CredentialRole) -> None:
    """Exige el conjunto exacto de privilegios y rechaza cualquier otro scope."""
    required = ROLE_PRIVILEGES[role]
    observed: set[str] = set()
    saw_usage = False
    saw_target = False

    for raw_grant in grants:
        grant = str(raw_grant).strip()
        if "WITH GRANT OPTION" in grant.upper():
            raise Stage100TargetGuardError("stage100_grants_excessive")
        match = _GRANT_RE.match(grant)
        if not match:
            raise Stage100TargetGuardError("stage100_grant_shape_invalid")
        privileges = _parse_privileges(match.group("privileges"))
        scope = _normalize_scope(match.group("scope"))

        if scope == "*.*" and privileges == frozenset({"USAGE"}):
            saw_usage = True
            continue
        if scope != f"{EXPECTED_DATABASE}.*":
            raise Stage100TargetGuardError("stage100_grant_scope_invalid")
        saw_target = True
        observed.update(privileges)

    if not saw_usage or not saw_target or frozenset(observed) != required:
        raise Stage100TargetGuardError("stage100_grants_not_minimal")


_CONTROL_GRANT_RE = re.compile(
    r"^GRANT\s+SELECT\s+\((?P<columns>[^)]+)\)\s+ON\s+"
    r"(?P<scope>.+?)\s+TO\s+",
    re.IGNORECASE,
)


def validate_control_grants(grants: Iterable[str]) -> None:
    observed: dict[str, frozenset[str]] = {}
    saw_usage = False
    for raw_grant in grants:
        grant = str(raw_grant).strip()
        upper = grant.upper()
        if any(
            forbidden in upper
            for forbidden in (
                "GRANT OPTION",
                "CONNECTION_ADMIN",
                "SUPER",
                "PROCESS ON",
            )
        ):
            raise Stage100TargetGuardError("stage100_control_grants_excessive")
        generic = _GRANT_RE.match(grant)
        if generic:
            privileges = _parse_privileges(generic.group("privileges"))
            scope = _normalize_scope(generic.group("scope"))
            if scope == "*.*" and privileges == frozenset({"USAGE"}):
                saw_usage = True
                continue
        match = _CONTROL_GRANT_RE.match(grant)
        if not match:
            raise Stage100TargetGuardError("stage100_control_grant_shape_invalid")
        scope = _normalize_scope(match.group("scope"))
        columns = frozenset(
            item.replace("`", "").strip().upper()
            for item in match.group("columns").split(",")
        )
        if scope not in CONTROL_COLUMNS or scope in observed:
            raise Stage100TargetGuardError("stage100_control_grant_scope_invalid")
        observed[scope] = columns
    if not saw_usage or observed != CONTROL_COLUMNS:
        raise Stage100TargetGuardError("stage100_control_grants_not_minimal")


def validate_control_connection(
    connection: Connection, *, configured_url: URL, expected_username: str
) -> ValidatedTarget:
    if connection.exec_driver_sql("SELECT DATABASE()").scalar_one() is not None:
        raise Stage100TargetGuardError("stage100_control_database_must_be_null")
    current_user = str(connection.exec_driver_sql("SELECT CURRENT_USER()").scalar_one())
    if (
        current_user != f"{expected_username}@localhost"
        or configured_url.username != expected_username
    ):
        raise Stage100TargetGuardError("stage100_control_identity_mismatch")
    rows = connection.exec_driver_sql("SHOW GRANTS").all()
    validate_control_grants(str(row[0]) for row in rows)
    return ValidatedTarget(
        role=CredentialRole.CONTROL,
        database="",
        username=expected_username,
    )


def validate_live_connection(
    connection: Connection,
    *,
    configured_url: URL,
    role: CredentialRole,
    expected_username: str,
) -> ValidatedTarget:
    """Comprueba DB seleccionada, identidad efectiva y grants reales."""
    selected = connection.exec_driver_sql("SELECT DATABASE()").scalar_one()
    if selected != EXPECTED_DATABASE or selected != configured_url.database:
        raise Stage100TargetGuardError("stage100_selected_database_mismatch")

    current_user = str(connection.exec_driver_sql("SELECT CURRENT_USER()").scalar_one())
    if (
        current_user != f"{expected_username}@localhost"
        or configured_url.username != expected_username
    ):
        raise Stage100TargetGuardError("stage100_effective_identity_mismatch")

    rows = connection.exec_driver_sql("SHOW GRANTS").all()
    grants = [str(row[0]) for row in rows]
    validate_grants(grants, role=role)
    return ValidatedTarget(role=role, database=EXPECTED_DATABASE, username=expected_username)


def validate_pre_schema_connection(
    connection: Connection,
    *,
    configured_url: URL,
    expected_username: str,
) -> ValidatedTarget:
    """Valida la identidad reset antes de que exista la database seleccionable."""

    if configured_url.database != EXPECTED_DATABASE:
        raise Stage100TargetGuardError("stage100_target_database_invalid")
    selected = connection.exec_driver_sql("SELECT DATABASE()").scalar_one()
    if selected is not None:
        raise Stage100TargetGuardError("stage100_pre_schema_database_must_be_null")
    current_user = str(connection.exec_driver_sql("SELECT CURRENT_USER()").scalar_one())
    if (
        current_user != f"{expected_username}@localhost"
        or configured_url.username != expected_username
    ):
        raise Stage100TargetGuardError("stage100_effective_identity_mismatch")
    rows = connection.exec_driver_sql("SHOW GRANTS").all()
    validate_grants((str(row[0]) for row in rows), role=CredentialRole.RESET)
    return ValidatedTarget(
        role=CredentialRole.RESET,
        database=EXPECTED_DATABASE,
        username=expected_username,
    )
