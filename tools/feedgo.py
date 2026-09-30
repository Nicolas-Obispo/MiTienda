"""Portable, auditable task runner for FeedGo development validation."""

from __future__ import annotations

import argparse
import os
from pathlib import Path
import shutil
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
FRONTEND = ROOT / "frontend"
EXPECTED_PYTHON = (3, 13, 15)
EXPECTED_NODE = "v24.21.0"
EXPECTED_NPM = "12.1.0"


def _validate_python() -> None:
    if sys.version_info[:3] != EXPECTED_PYTHON:
        raise SystemExit(
            f"python_version_mismatch:{sys.version_info.major}."
            f"{sys.version_info.minor}.{sys.version_info.micro}"
        )


def _binary(environment_name: str, default: str) -> str:
    value = os.environ.get(environment_name, default)
    resolved = shutil.which(value) if not Path(value).is_file() else value
    if not resolved:
        raise SystemExit(f"required_binary_missing:{environment_name}")
    return str(resolved)


def _run(command: list[str], *, cwd: Path = ROOT, capture: bool = False) -> str:
    completed = subprocess.run(
        command,
        cwd=cwd,
        check=True,
        text=True,
        capture_output=capture,
        env=os.environ.copy(),
    )
    return completed.stdout.strip() if capture else ""


def versions() -> None:
    _validate_python()
    node = _run([_binary("FEEDGO_NODE_BIN", "node"), "--version"], capture=True)
    npm = _run([_binary("FEEDGO_NPM_BIN", "npm"), "--version"], capture=True)
    if node != EXPECTED_NODE:
        raise SystemExit(f"node_version_mismatch:{node}")
    if npm != EXPECTED_NPM:
        raise SystemExit(f"npm_version_mismatch:{npm}")
    print(f"python={'.'.join(map(str, EXPECTED_PYTHON))} node={node} npm={npm}")


def backend_sync(*, embeddings: bool, tooling: bool) -> None:
    command = [_binary("FEEDGO_UV_BIN", "uv"), "sync", "--locked"]
    if not tooling:
        command.append("--no-default-groups")
    else:
        command.extend(["--group", "test", "--group", "security"])
    if embeddings:
        command.extend(["--extra", "embeddings"])
    _run(command, cwd=BACKEND)


def backend_compile() -> None:
    _run(
        [_binary("FEEDGO_UV_BIN", "uv"), "run", "--locked", "python", "-m", "compileall", "app", "main.py"],
        cwd=BACKEND,
    )


def backend_test() -> None:
    _run(
        [
            _binary("FEEDGO_UV_BIN", "uv"),
            "run",
            "--locked",
            "--group",
            "test",
            "--extra",
            "embeddings",
            "python",
            "-m",
            "unittest",
            "discover",
            "-s",
            "tests",
        ],
        cwd=BACKEND,
    )


def backend_coverage() -> None:
    uv = _binary("FEEDGO_UV_BIN", "uv")
    _run(
        [uv, "run", "--locked", "--group", "test", "--extra", "embeddings", "coverage", "erase"],
        cwd=BACKEND,
    )
    _run(
        [
            uv,
            "run",
            "--locked",
            "--group",
            "test",
            "--extra",
            "embeddings",
            "coverage",
            "run",
            "--branch",
            "-m",
            "unittest",
            "discover",
            "-s",
            "tests",
        ],
        cwd=BACKEND,
    )
    _run(
        [uv, "run", "--locked", "--group", "test", "--extra", "embeddings", "coverage", "report"],
        cwd=BACKEND,
    )


def frontend_ci() -> None:
    _run([_binary("FEEDGO_NPM_BIN", "npm"), "ci"], cwd=FRONTEND)


def frontend_check() -> None:
    npm = _binary("FEEDGO_NPM_BIN", "npm")
    _run([npm, "run", "lint"], cwd=FRONTEND)
    _run([npm, "run", "build"], cwd=FRONTEND)


def main() -> None:
    _validate_python()
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("versions")
    sync = subparsers.add_parser("backend-sync")
    sync.add_argument("--embeddings", action="store_true")
    sync.add_argument("--tooling", action="store_true")
    subparsers.add_parser("backend-compile")
    subparsers.add_parser("backend-test")
    subparsers.add_parser("backend-coverage")
    subparsers.add_parser("frontend-ci")
    subparsers.add_parser("frontend-check")
    args = parser.parse_args()
    if args.command == "versions":
        versions()
    elif args.command == "backend-sync":
        backend_sync(embeddings=args.embeddings, tooling=args.tooling)
    elif args.command == "backend-compile":
        backend_compile()
    elif args.command == "backend-test":
        backend_test()
    elif args.command == "backend-coverage":
        backend_coverage()
    elif args.command == "frontend-ci":
        frontend_ci()
    elif args.command == "frontend-check":
        frontend_check()


if __name__ == "__main__":
    main()
