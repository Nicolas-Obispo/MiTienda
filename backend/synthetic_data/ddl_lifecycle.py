"""Lifecycle fail-closed para DDL destructivo/controlado de ET100.3."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from enum import Enum
import time
from typing import Callable, Iterable

from sqlalchemy import event
from sqlalchemy.engine import Connection, Engine
from sqlalchemy.exc import DBAPIError


SERVER_LOCK_WAIT_TIMEOUT_SECONDS = 5
CLIENT_READ_TIMEOUT_SECONDS = 10
CANCELLATION_CONFIRM_TIMEOUT_SECONDS = 5.0


class DdlLifecycleState(str, Enum):
    PREPARED = "prepared"
    DISPATCH_STARTED = "dispatch_started"
    COMPLETED = "completed"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class DdlLifecycleEvidence:
    state: DdlLifecycleState
    connection_id: int
    dispatched: int
    completed: int
    current_statement: str | None
    cancellation_confirmed: bool


class DdlLifecycleError(RuntimeError):
    def __init__(self, code: str, evidence: DdlLifecycleEvidence):
        super().__init__(code)
        self.evidence = evidence


class DdlExecutionTracker:
    """Valida el multiconjunto y conserva evidencia antes/después del dispatch."""

    def __init__(self, statements: Iterable[str], normalize: Callable[[str], str]):
        self._remaining = Counter(statements)
        self._normalize = normalize
        self.state = DdlLifecycleState.PREPARED
        self.dispatched = 0
        self.completed = 0
        self.current_statement: str | None = None

    def before(self, statement: str) -> None:
        normalized = self._normalize(statement)
        if self._remaining[normalized] <= 0:
            raise RuntimeError("stage100_ddl_statement_not_allowlisted")
        self._remaining[normalized] -= 1
        self.dispatched += 1
        self.current_statement = normalized
        self.state = DdlLifecycleState.DISPATCH_STARTED

    def after(self, statement: str) -> None:
        normalized = self._normalize(statement)
        if normalized != self.current_statement:
            raise RuntimeError("stage100_ddl_completion_mismatch")
        self.completed += 1
        self.current_statement = None
        if self.completed == self.dispatched and self._remaining.total() == 0:
            self.state = DdlLifecycleState.COMPLETED
        else:
            self.state = DdlLifecycleState.PREPARED

    def assert_complete(self) -> None:
        if (
            self._remaining.total() != 0
            or self.dispatched != self.completed
            or self.state is not DdlLifecycleState.COMPLETED
        ):
            raise RuntimeError("stage100_ddl_execution_incomplete")


def _dbapi_code(exc: BaseException) -> int | None:
    original = getattr(exc, "orig", None)
    args = getattr(original, "args", ())
    return args[0] if args and isinstance(args[0], int) else None


def _cancel_query_and_confirm(
    killer_engine: Engine,
    observer_engine: Engine,
    *,
    connection_id: int,
    target_database: str,
    timeout_seconds: float = CANCELLATION_CONFIRM_TIMEOUT_SECONDS,
) -> bool:
    """Cancela sólo la query conocida y demuestra ausencia de query/locks."""

    if not target_database:
        raise ValueError("stage100_ddl_target_database_missing")
    with killer_engine.connect() as killer:
        try:
            killer.exec_driver_sql(f"KILL QUERY {int(connection_id)}")
        except DBAPIError as exc:
            # 1094: el thread ya terminó; la confirmación inferior decide.
            if _dbapi_code(exc) != 1094:
                raise
        if killer.in_transaction():
            killer.rollback()

    with observer_engine.connect() as observer:
        deadline = time.monotonic() + timeout_seconds
        while time.monotonic() < deadline:
            row = observer.exec_driver_sql(
                "SELECT PROCESSLIST_COMMAND FROM performance_schema.threads "
                "WHERE PROCESSLIST_ID = %s",
                (connection_id,),
            ).first()
            locks = int(
                observer.exec_driver_sql(
                    "SELECT COUNT(ml.OWNER_THREAD_ID) "
                    "FROM performance_schema.metadata_locks ml "
                    "JOIN performance_schema.threads t "
                    "ON t.THREAD_ID = ml.OWNER_THREAD_ID "
                    "WHERE t.PROCESSLIST_ID = %s "
                    "AND ml.LOCK_STATUS IN ('PENDING', 'GRANTED')",
                    (connection_id,),
                ).scalar_one()
            )
            if (row is None or str(row[0]).lower() != "query") and locks == 0:
                if observer.in_transaction():
                    observer.rollback()
                return True
            time.sleep(0.1)
        if observer.in_transaction():
            observer.rollback()
        return False


def execute_ddl_batch(
    *,
    ddl_engine: Engine,
    killer_engine: Engine,
    observer_engine: Engine,
    target_database: str,
    expected_statements: tuple[str, ...],
    normalize: Callable[[str], str],
    operation: Callable[[Connection], None],
) -> DdlLifecycleEvidence:
    """Ejecuta una sola fase DDL; nunca reintenta un resultado ambiguo."""

    tracker = DdlExecutionTracker(expected_statements, normalize)
    connection_id = -1
    cancellation_confirmed = False

    with ddl_engine.connect() as connection:
        connection.exec_driver_sql(
            "SET SESSION lock_wait_timeout = %s",
            (SERVER_LOCK_WAIT_TIMEOUT_SECONDS,),
        )
        connection_id = int(
            connection.exec_driver_sql("SELECT CONNECTION_ID()").scalar_one()
        )
        if connection.in_transaction():
            connection.commit()
        if connection.in_transaction():
            raise DdlLifecycleError(
                "stage100_ddl_transaction_open_before_dispatch",
                DdlLifecycleEvidence(
                    state=DdlLifecycleState.PREPARED,
                    connection_id=connection_id,
                    dispatched=0,
                    completed=0,
                    current_statement=None,
                    cancellation_confirmed=False,
                ),
            )

        def before(_conn, _cursor, statement, _parameters, _context, _many):
            tracker.before(statement)

        def after(_conn, _cursor, statement, _parameters, _context, _many):
            tracker.after(statement)

        event.listen(connection, "before_cursor_execute", before)
        event.listen(connection, "after_cursor_execute", after)
        try:
            operation(connection)
            tracker.assert_complete()
        except BaseException as exc:
            # BaseException incluye errores DBAPI y señales; nunca hay retry.
            outstanding = tracker.dispatched > tracker.completed
            if outstanding:
                try:
                    cancellation_confirmed = _cancel_query_and_confirm(
                        killer_engine,
                        observer_engine,
                        connection_id=connection_id,
                        target_database=target_database,
                    )
                except BaseException:
                    # La falla del canal de control no puede convertir un
                    # resultado ambiguo en reintento ni ocultar su estado.
                    cancellation_confirmed = False
            tracker.state = DdlLifecycleState.UNKNOWN
            evidence = DdlLifecycleEvidence(
                state=tracker.state,
                connection_id=connection_id,
                dispatched=tracker.dispatched,
                completed=tracker.completed,
                current_statement=tracker.current_statement,
                cancellation_confirmed=cancellation_confirmed,
            )
            raise DdlLifecycleError("stage100_ddl_result_unknown", evidence) from exc
        finally:
            event.remove(connection, "before_cursor_execute", before)
            event.remove(connection, "after_cursor_execute", after)
            if connection.in_transaction():
                connection.rollback()

    return DdlLifecycleEvidence(
        state=DdlLifecycleState.COMPLETED,
        connection_id=connection_id,
        dispatched=tracker.dispatched,
        completed=tracker.completed,
        current_statement=None,
        cancellation_confirmed=False,
    )
