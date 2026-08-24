import io
from pathlib import Path
import signal
import threading
import unittest
from contextlib import redirect_stderr, redirect_stdout
from unittest.mock import patch

from app.core.config import settings
from run_feedgo_local import (
    build_commands,
    install_shutdown_handlers,
    install_smoke_stop_watcher,
    supervise,
)


class FakeProcess:
    def __init__(self, exit_code=None):
        self.exit_code = exit_code
        self.stopped = False
        self.killed = False

    def poll(self):
        return self.exit_code if not self.stopped else 0

    def terminate(self):
        self.stopped = True

    def send_signal(self, _signal):
        self.stopped = True

    def wait(self, timeout=None):
        return 0

    def kill(self):
        self.killed = True
        self.stopped = True


class FeedGoLocalLauncherTests(unittest.TestCase):
    def setUp(self):
        self.original = (settings.ADMIN_EMAIL_ENABLED, settings.OPERATIONAL_EMAIL_DISPATCHER_ENABLED)

    def tearDown(self):
        settings.ADMIN_EMAIL_ENABLED, settings.OPERATIONAL_EMAIL_DISPATCHER_ENABLED = self.original

    def test_single_launcher_builds_separate_api_and_worker_processes_when_enabled(self):
        settings.ADMIN_EMAIL_ENABLED = True
        settings.OPERATIONAL_EMAIL_DISPATCHER_ENABLED = True
        commands = build_commands(host="127.0.0.1", port=8000)
        self.assertEqual([name for name, _ in commands], ["api", "operational_email_worker"])
        self.assertIn("uvicorn", commands[0][1])
        self.assertIn("run_operational_email_worker.py", commands[1][1])
        self.assertNotEqual(commands[0][1], commands[1][1])

    def test_existing_powershell_entrypoint_runs_launcher_from_backend_directory(self):
        script = (Path(__file__).resolve().parents[1] / "activate.ps1").read_text(encoding="utf-8")
        self.assertIn("param([switch]$Run)", script)
        self.assertIn("Push-Location $PSScriptRoot", script)
        self.assertIn("run_feedgo_local.py", script)

    def test_disabled_worker_starts_only_api_and_reports_disabled_by_contract(self):
        settings.ADMIN_EMAIL_ENABLED = False
        settings.OPERATIONAL_EMAIL_DISPATCHER_ENABLED = False
        self.assertEqual([name for name, _ in build_commands(host="127.0.0.1", port=8000)], ["api"])

    def test_partial_failure_is_visible_and_stops_sibling(self):
        api = FakeProcess()
        worker = FakeProcess(exit_code=2)
        processes = iter([api, worker])
        output = io.StringIO()
        with redirect_stderr(output):
            result = supervise(
                [("api", ["api"]), ("operational_email_worker", ["worker"])],
                popen_factory=lambda _command: next(processes),
                poll_interval_seconds=0,
            )
        self.assertEqual(result, 1)
        self.assertTrue(api.stopped)
        self.assertIn("component=operational_email_worker status=failed exit_code=2", output.getvalue())

    def test_api_failure_is_visible_and_stops_worker(self):
        api = FakeProcess(exit_code=1)
        worker = FakeProcess()
        processes = iter([api, worker])
        output = io.StringIO()
        with redirect_stderr(output):
            result = supervise(
                [("api", ["api"]), ("operational_email_worker", ["worker"])],
                popen_factory=lambda _command: next(processes),
                poll_interval_seconds=0,
            )
        self.assertEqual(result, 1)
        self.assertTrue(worker.stopped)
        self.assertIn("component=api status=failed exit_code=1", output.getvalue())

    def test_controlled_shutdown_stops_all_children_without_orphans(self):
        api, worker = FakeProcess(), FakeProcess()
        processes = iter([api, worker])
        stop_event = threading.Event()
        stop_event.set()
        output = io.StringIO()
        with redirect_stdout(output):
            result = supervise(
                [("api", ["api"]), ("operational_email_worker", ["worker"])],
                popen_factory=lambda _command: next(processes),
                stop_event=stop_event,
            )
        self.assertEqual(result, 0)
        self.assertTrue(api.stopped and worker.stopped)
        self.assertIn("launcher=stopped children=clean", output.getvalue())

    def test_second_spawn_failure_stops_first_process(self):
        api = FakeProcess()
        calls = 0

        def spawn(_command):
            nonlocal calls
            calls += 1
            if calls == 2:
                raise OSError("private detail")
            return api

        output = io.StringIO()
        with redirect_stderr(output):
            result = supervise(
                [("api", ["api"]), ("operational_email_worker", ["worker"])],
                popen_factory=spawn,
            )
        self.assertEqual(result, 1)
        self.assertTrue(api.stopped)
        self.assertNotIn("private detail", output.getvalue())

    def test_windows_break_signal_requests_controlled_shutdown(self):
        stop_event = threading.Event()
        registered = {}
        with patch("run_feedgo_local.signal.signal", side_effect=lambda key, handler: registered.setdefault(key, handler)):
            install_shutdown_handlers(stop_event)
        self.assertIn(signal.SIGINT, registered)
        if hasattr(signal, "SIGBREAK"):
            self.assertIn(signal.SIGBREAK, registered)
            registered[signal.SIGBREAK](signal.SIGBREAK, None)
            self.assertTrue(stop_event.is_set())

    def test_explicit_smoke_stop_file_requests_shutdown_without_network_control(self):
        import tempfile
        with tempfile.TemporaryDirectory() as directory:
            stop_path = Path(directory) / "stop"
            stop_event = threading.Event()
            with patch.dict("os.environ", {"FEEDGO_LOCAL_LAUNCHER_SMOKE_STOP_FILE": str(stop_path)}):
                watcher = install_smoke_stop_watcher(stop_event)
                stop_path.touch()
                self.assertTrue(stop_event.wait(1))
                watcher.join(timeout=1)


if __name__ == "__main__":
    unittest.main()
