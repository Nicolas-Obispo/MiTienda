"""Contratos del lifecycle DDL fail-closed de ET100.3."""

from __future__ import annotations

from pathlib import Path
import importlib.util
import signal
import sys
from unittest.mock import ANY, Mock, patch
import unittest

from synthetic_data.ddl_lifecycle import (
    CLIENT_READ_TIMEOUT_SECONDS,
    DdlExecutionTracker,
    DdlLifecycleError,
    DdlLifecycleState,
    SERVER_LOCK_WAIT_TIMEOUT_SECONDS,
    _cancel_query_and_confirm,
    execute_ddl_batch,
)


ROOT = Path(__file__).resolve().parents[2]


class _Result:
    def __init__(self, scalar=None, row=None):
        self._scalar = scalar
        self._row = row

    def scalar_one(self):
        return self._scalar

    def first(self):
        return self._row


class _Connection:
    def __init__(self):
        self.transaction = True
        self.commits = 0
        self.rollbacks = 0
        self.closed = False
        self.sql = []

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        self.closed = True

    def exec_driver_sql(self, statement, parameters=None):
        self.sql.append((statement, parameters))
        self.transaction = True
        if statement == "SELECT CONNECTION_ID()":
            return _Result(731)
        return _Result(None)

    def in_transaction(self):
        return self.transaction

    def commit(self):
        self.commits += 1
        self.transaction = False

    def rollback(self):
        self.rollbacks += 1
        self.transaction = False


class _Engine:
    def __init__(self, connection):
        self.connection = connection

    def connect(self):
        return self.connection


class DdlLifecycleContracts(unittest.TestCase):
    def test_runner_timeout_interrupts_then_reaps_direct_child(self):
        tools = ROOT / "tools"
        sys.path.insert(0, str(tools))
        try:
            spec = importlib.util.spec_from_file_location(
                "feedgo_runner_lifecycle_test", tools / "feedgo.py"
            )
            module = importlib.util.module_from_spec(spec)
            assert spec.loader is not None
            spec.loader.exec_module(module)
        finally:
            sys.path.remove(str(tools))

        process = Mock()
        process.wait.side_effect = [
            __import__("subprocess").TimeoutExpired("ddl", 30),
            1,
        ]
        process.returncode = 1
        with patch.object(module.subprocess, "Popen", return_value=process):
            with self.assertRaisesRegex(SystemExit, "runner_timeout"):
                module._run_versioned_ddl([])

        process.send_signal.assert_called_once_with(signal.CTRL_BREAK_EVENT)
        self.assertEqual(process.wait.call_count, 2)
        process.kill.assert_not_called()

    def test_control_channel_kills_exact_query_and_confirms_query_and_locks_gone(self):
        class ControlConnection(_Connection):
            def exec_driver_sql(self, statement, parameters=None):
                self.sql.append((statement, parameters))
                self.transaction = True
                if statement.startswith("SELECT PROCESSLIST_COMMAND"):
                    return _Result(row=None)
                if statement.startswith("SELECT COUNT("):
                    return _Result(scalar=0)
                return _Result()

        killer = ControlConnection()
        observer = ControlConnection()
        confirmed = _cancel_query_and_confirm(
            _Engine(killer),
            _Engine(observer),
            connection_id=559,
            target_database="mitienda_stage100_test",
            timeout_seconds=0.2,
        )
        self.assertTrue(confirmed)
        self.assertEqual(killer.sql, [("KILL QUERY 559", None)])
        self.assertTrue(
            any("LOCK_STATUS IN ('PENDING', 'GRANTED')" in sql for sql, _ in observer.sql)
        )
        self.assertFalse(any(sql.startswith("KILL") for sql, _ in observer.sql))
        self.assertEqual(killer.rollbacks, 1)
        self.assertEqual(observer.rollbacks, 1)

    def test_tracker_preserves_multiplicity_and_dispatch_states(self):
        tracker = DdlExecutionTracker(("DDL A", "DDL A"), str.strip)
        self.assertEqual(tracker.state, DdlLifecycleState.PREPARED)
        tracker.before(" DDL A ")
        self.assertEqual(tracker.state, DdlLifecycleState.DISPATCH_STARTED)
        tracker.after("DDL A")
        self.assertEqual(tracker.state, DdlLifecycleState.PREPARED)
        tracker.before("DDL A")
        tracker.after("DDL A")
        tracker.assert_complete()
        self.assertEqual(tracker.state, DdlLifecycleState.COMPLETED)

    def test_tracker_rejects_added_changed_or_missing_statements(self):
        tracker = DdlExecutionTracker(("DDL A",), str.strip)
        with self.assertRaisesRegex(RuntimeError, "not_allowlisted"):
            tracker.before("DDL B")
        with self.assertRaisesRegex(RuntimeError, "incomplete"):
            tracker.assert_complete()

    def test_success_has_known_connection_and_no_open_transaction_before_ddl(self):
        connection = _Connection()
        callbacks = {}

        def listen(_connection, event_name, callback):
            callbacks[event_name] = callback

        def operation(_connection):
            self.assertFalse(connection.in_transaction())
            callbacks["before_cursor_execute"](
                connection, None, "DDL A", None, None, False
            )
            callbacks["after_cursor_execute"](
                connection, None, "DDL A", None, None, False
            )

        with patch("synthetic_data.ddl_lifecycle.event.listen", side_effect=listen), patch(
            "synthetic_data.ddl_lifecycle.event.remove"
        ):
            evidence = execute_ddl_batch(
                ddl_engine=_Engine(connection),
                killer_engine=_Engine(_Connection()),
                observer_engine=_Engine(_Connection()),
                target_database="mitienda_stage100_test",
                expected_statements=("DDL A",),
                normalize=str.strip,
                operation=operation,
            )

        self.assertEqual(evidence.state, DdlLifecycleState.COMPLETED)
        self.assertEqual(evidence.connection_id, 731)
        self.assertEqual((evidence.dispatched, evidence.completed), (1, 1))
        self.assertEqual(connection.commits, 1)
        self.assertTrue(connection.closed)
        self.assertEqual(
            connection.sql[0],
            (
                "SET SESSION lock_wait_timeout = %s",
                (SERVER_LOCK_WAIT_TIMEOUT_SECONDS,),
            ),
        )

    def test_interrupt_after_dispatch_kills_exact_query_and_returns_unknown(self):
        connection = _Connection()
        callbacks = {}

        def listen(_connection, event_name, callback):
            callbacks[event_name] = callback

        def operation(_connection):
            callbacks["before_cursor_execute"](
                connection, None, "DDL A", None, None, False
            )
            raise KeyboardInterrupt()

        with patch("synthetic_data.ddl_lifecycle.event.listen", side_effect=listen), patch(
            "synthetic_data.ddl_lifecycle.event.remove"
        ), patch(
            "synthetic_data.ddl_lifecycle._cancel_query_and_confirm",
            return_value=True,
        ) as cancel:
            with self.assertRaises(DdlLifecycleError) as caught:
                execute_ddl_batch(
                    ddl_engine=_Engine(connection),
                    killer_engine=_Engine(_Connection()),
                    observer_engine=_Engine(_Connection()),
                    target_database="mitienda_stage100_test",
                    expected_statements=("DDL A",),
                    normalize=str.strip,
                    operation=operation,
                )

        evidence = caught.exception.evidence
        self.assertEqual(evidence.state, DdlLifecycleState.UNKNOWN)
        self.assertEqual(evidence.connection_id, 731)
        self.assertTrue(evidence.cancellation_confirmed)
        cancel.assert_called_once_with(
            ANY,
            ANY,
            connection_id=731,
            target_database="mitienda_stage100_test",
        )
        self.assertTrue(connection.closed)

    def test_runner_invokes_versioned_module_directly_with_outer_timeout(self):
        source = (ROOT / "tools" / "feedgo.py").read_text(encoding="utf-8")
        supervisor = source[
            source.index("def _run_versioned_ddl") : source.index("def versions")
        ]
        bootstrap = source[source.index("def stage100_bootstrap()") :]
        self.assertIn('module: str = "synthetic_data.bootstrap"', supervisor)
        self.assertIn('[_backend_python(), "-m", module, *arguments]', supervisor)
        self.assertIn("CREATE_NEW_PROCESS_GROUP", supervisor)
        self.assertIn("CTRL_BREAK_EVENT", supervisor)
        self.assertIn("process.wait(timeout=DDL_INTERRUPT_GRACE_SECONDS)", supervisor)
        self.assertIn("process.kill()", supervisor)
        self.assertIn("process.wait()", supervisor)
        self.assertIn("_run_versioned_ddl([])", bootstrap)
        self.assertNotIn('[_uv(), "run", "--locked", "python", "-m", "synthetic_data.bootstrap"]', source)
        self.assertGreater(CLIENT_READ_TIMEOUT_SECONDS, SERVER_LOCK_WAIT_TIMEOUT_SECONDS)
        self.assertGreater(30, CLIENT_READ_TIMEOUT_SECONDS)


if __name__ == "__main__":
    unittest.main()
