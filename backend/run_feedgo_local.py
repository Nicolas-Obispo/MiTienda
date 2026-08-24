"""Launcher local supervisado para API y worker operativo FeedGo."""

from __future__ import annotations

import argparse
import os
import signal
import subprocess
import sys
import threading
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Sequence

from app.core.config import settings
from app.modules.operations.services.operational_worker_state_services import publish_worker_state


BACKEND_DIR = Path(__file__).resolve().parent


@dataclass
class ManagedProcess:
    name: str
    process: subprocess.Popen


def worker_is_enabled() -> bool:
    return bool(settings.ADMIN_EMAIL_ENABLED and settings.OPERATIONAL_EMAIL_DISPATCHER_ENABLED)


def build_commands(*, host: str, port: int) -> list[tuple[str, list[str]]]:
    commands = [
        ("api", [sys.executable, "-m", "uvicorn", "main:app", "--host", host, "--port", str(port)]),
    ]
    if worker_is_enabled():
        commands.append(("operational_email_worker", [sys.executable, "run_operational_email_worker.py", "--run"]))
    return commands


def spawn_process(command: Sequence[str]) -> subprocess.Popen:
    options: dict[str, object] = {"cwd": str(BACKEND_DIR)}
    if os.name == "nt":
        options["creationflags"] = subprocess.CREATE_NEW_PROCESS_GROUP
    else:
        options["start_new_session"] = True
    return subprocess.Popen(list(command), **options)


def stop_process(process: subprocess.Popen, *, timeout_seconds: float = 10.0) -> None:
    if process.poll() is not None:
        return
    try:
        if os.name == "nt" and hasattr(signal, "CTRL_BREAK_EVENT"):
            process.send_signal(signal.CTRL_BREAK_EVENT)
        else:
            process.terminate()
        process.wait(timeout=timeout_seconds)
    except (OSError, subprocess.TimeoutExpired):
        process.kill()
        process.wait(timeout=timeout_seconds)


def mark_worker_stopped_safely() -> None:
    try:
        publish_worker_state("stopped")
    except Exception:
        pass


def supervise(
    commands: list[tuple[str, list[str]]],
    *,
    popen_factory: Callable[[Sequence[str]], subprocess.Popen] = spawn_process,
    stop_event: threading.Event | None = None,
    poll_interval_seconds: float = 0.2,
) -> int:
    requested_stop = stop_event or threading.Event()
    managed: list[ManagedProcess] = []
    try:
        for name, command in commands:
            process = popen_factory(command)
            managed.append(ManagedProcess(name=name, process=process))
            print(f"component={name} status=started")
        while not requested_stop.is_set():
            for item in managed:
                exit_code = item.process.poll()
                if exit_code is not None:
                    # En Windows el evento de consola puede observarse primero
                    # en el hijo y unas milésimas después en el supervisor.
                    requested_stop.wait(0.2)
                    if requested_stop.is_set():
                        return 0
                    print(
                        f"component={item.name} status=failed exit_code={exit_code}",
                        file=sys.stderr,
                    )
                    return 1
            requested_stop.wait(poll_interval_seconds)
        return 0
    except Exception:
        print("launcher=status_failed detail=sanitized", file=sys.stderr)
        return 1
    finally:
        for item in reversed(managed):
            stop_process(item.process)
        if any(item.name == "operational_email_worker" for item in managed):
            mark_worker_stopped_safely()
        if managed:
            print("launcher=stopped children=clean")


def install_shutdown_handlers(stop_event: threading.Event) -> None:
    def request_shutdown(_signum, _frame):
        stop_event.set()

    signal.signal(signal.SIGINT, request_shutdown)
    if hasattr(signal, "SIGTERM"):
        signal.signal(signal.SIGTERM, request_shutdown)
    if hasattr(signal, "SIGBREAK"):
        signal.signal(signal.SIGBREAK, request_shutdown)


def install_smoke_stop_watcher(stop_event: threading.Event) -> threading.Thread | None:
    raw_path = os.environ.get("FEEDGO_LOCAL_LAUNCHER_SMOKE_STOP_FILE", "").strip()
    if not raw_path:
        return None
    stop_path = Path(raw_path).resolve()

    def watch() -> None:
        while not stop_event.wait(0.1):
            if stop_path.is_file():
                stop_event.set()
                return

    thread = threading.Thread(target=watch, name="feedgo-local-smoke-stop", daemon=True)
    thread.start()
    return thread


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Inicia FeedGo local con procesos supervisados")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args(argv)
    if not 1 <= args.port <= 65535:
        print("launcher=blocked reason=invalid_port", file=sys.stderr)
        return 2
    stop_event = threading.Event()
    install_shutdown_handlers(stop_event)
    install_smoke_stop_watcher(stop_event)
    commands = build_commands(host=args.host, port=args.port)
    print(f"operational_email_worker={'enabled' if worker_is_enabled() else 'disabled'}")
    return supervise(commands, stop_event=stop_event)


if __name__ == "__main__":
    raise SystemExit(main())
