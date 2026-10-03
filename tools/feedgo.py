"""Portable, auditable task runner for FeedGo development validation."""

from __future__ import annotations

import argparse
import os
from pathlib import Path
import signal
import shutil
import subprocess
import sys

from feedgo_toolchain import ToolchainError, install_uv_from_archive, resolve_uv


ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
FRONTEND = ROOT / "frontend"
EXPECTED_PYTHON = (3, 13, 15)
EXPECTED_NODE = "v24.21.0"
EXPECTED_NPM = "12.1.0"
LOCAL_NODE_ROOT = ROOT / ".tools" / "node" / "24.21.0" / "node-v24.21.0-win-x64"
DDL_RUNNER_TIMEOUT_SECONDS = 30
DDL_INTERRUPT_GRACE_SECONDS = 15


def _uv() -> str:
    try:
        return resolve_uv()
    except ToolchainError as exc:
        raise SystemExit(str(exc)) from exc


def _node() -> str:
    local = LOCAL_NODE_ROOT / "node.exe"
    default = str(local) if local.is_file() else "node"
    return _binary("FEEDGO_NODE_BIN", default)


def _npm() -> str:
    local = LOCAL_NODE_ROOT / "npm.cmd"
    default = str(local) if local.is_file() else "npm"
    return _binary("FEEDGO_NPM_BIN", default)


def _backend_python() -> str:
    relative = Path("Scripts/python.exe") if os.name == "nt" else Path("bin/python")
    candidate = BACKEND / ".venv" / relative
    if not candidate.is_file():
        raise SystemExit("backend_locked_environment_missing")
    return str(candidate)


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


def _run(
    command: list[str],
    *,
    cwd: Path = ROOT,
    capture: bool = False,
    timeout: int | None = None,
) -> str:
    try:
        completed = subprocess.run(
            command,
            cwd=cwd,
            check=True,
            text=True,
            capture_output=capture,
            env=os.environ.copy(),
            timeout=timeout,
        )
    except subprocess.TimeoutExpired as exc:
        raise SystemExit("feedgo_task_timeout") from exc
    return completed.stdout.strip() if capture else ""


def _run_versioned_ddl(
    arguments: list[str], *, module: str = "synthetic_data.bootstrap"
) -> None:
    """Supervisa el módulo DDL directo y permite su cancelación controlada."""

    creationflags = subprocess.CREATE_NEW_PROCESS_GROUP if os.name == "nt" else 0
    process = subprocess.Popen(
        [_backend_python(), "-m", module, *arguments],
        cwd=BACKEND,
        env=os.environ.copy(),
        creationflags=creationflags,
    )
    timed_out = False
    try:
        process.wait(timeout=DDL_RUNNER_TIMEOUT_SECONDS)
    except subprocess.TimeoutExpired:
        timed_out = True
        interrupt = signal.CTRL_BREAK_EVENT if os.name == "nt" else signal.SIGINT
        process.send_signal(interrupt)
        try:
            process.wait(timeout=DDL_INTERRUPT_GRACE_SECONDS)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait()
            raise SystemExit("stage100_ddl_forced_termination_after_unconfirmed_cancel")
    except KeyboardInterrupt:
        interrupt = signal.CTRL_BREAK_EVENT if os.name == "nt" else signal.SIGINT
        process.send_signal(interrupt)
        try:
            process.wait(timeout=DDL_INTERRUPT_GRACE_SECONDS)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait()
        raise

    if timed_out:
        raise SystemExit("stage100_ddl_runner_timeout")
    if process.returncode:
        raise subprocess.CalledProcessError(process.returncode, process.args)


def versions() -> None:
    _validate_python()
    node = _run([_node(), "--version"], capture=True)
    npm = _run([_npm(), "--version"], capture=True)
    if node != EXPECTED_NODE:
        raise SystemExit(f"node_version_mismatch:{node}")
    if npm != EXPECTED_NPM:
        raise SystemExit(f"npm_version_mismatch:{npm}")
    print(f"python={'.'.join(map(str, EXPECTED_PYTHON))} node={node} npm={npm}")


def backend_sync(*, embeddings: bool, tooling: bool) -> None:
    command = [_uv(), "sync", "--locked"]
    if not tooling:
        command.append("--no-default-groups")
    else:
        command.extend(["--group", "test", "--group", "security"])
    if embeddings:
        command.extend(["--extra", "embeddings"])
    _run(command, cwd=BACKEND)


def backend_compile() -> None:
    _run(
        [_uv(), "run", "--locked", "python", "-m", "compileall", "app", "main.py"],
        cwd=BACKEND,
    )


def backend_test() -> None:
    _run(
        [
            _uv(),
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
    uv = _uv()
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
    _run([_npm(), "ci"], cwd=FRONTEND)


def frontend_check() -> None:
    npm = _npm()
    _run([npm, "run", "lint"], cwd=FRONTEND)
    _run([npm, "run", "build"], cwd=FRONTEND)


def toolchain_install_uv(archive: str) -> None:
    try:
        installed = install_uv_from_archive(Path(archive))
    except ToolchainError as exc:
        raise SystemExit(str(exc)) from exc
    print(f"uv_installed={installed}")


def toolchain_verify_uv() -> None:
    print(f"uv={_uv()}")


def stage100_bootstrap() -> None:
    _run_versioned_ddl([])


def stage100_bootstrap_preflight() -> None:
    _run_versioned_ddl(["--preflight"])


def synthetic_reset() -> None:
    _run_versioned_ddl([], module="synthetic_data.reset")


def synthetic_apply(
    *, profile: str, seed: str, dataset_version: str,
    clock_policy: str, clock_anchor: str,
) -> None:
    _run(
        [
            _backend_python(),
            "-m",
            "synthetic_data.apply",
            "--profile",
            profile,
            "--seed",
            seed,
            "--dataset-version",
            dataset_version,
            "--clock-policy",
            clock_policy,
            "--clock-anchor",
            clock_anchor,
        ],
        cwd=BACKEND,
    )


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
    install_uv = subparsers.add_parser("toolchain-install-uv")
    install_uv.add_argument("--archive", required=True)
    subparsers.add_parser("toolchain-verify-uv")
    subparsers.add_parser("stage100-bootstrap")
    subparsers.add_parser("stage100-bootstrap-preflight")
    subparsers.add_parser("synthetic-reset")
    apply = subparsers.add_parser("synthetic-apply")
    apply.add_argument("--profile", required=True, choices=("smoke", "functional"))
    apply.add_argument("--seed", required=True)
    apply.add_argument("--dataset-version", required=True)
    apply.add_argument("--clock-policy", required=True, choices=("fixed_utc_v1",))
    apply.add_argument("--clock-anchor", required=True)
    validate = subparsers.add_parser("synthetic-validate")
    validate.add_argument("--source", required=True, choices=("blueprint", "mysql"))
    validate.add_argument(
        "--profile", required=True, choices=("smoke", "functional", "representative")
    )
    validate.add_argument("--seed", required=True)
    validate.add_argument("--dataset-version", required=True)
    validate.add_argument("--clock-policy", required=True, choices=("fixed_utc_v1",))
    validate.add_argument("--clock-anchor", required=True)
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
    elif args.command == "toolchain-install-uv":
        toolchain_install_uv(args.archive)
    elif args.command == "toolchain-verify-uv":
        toolchain_verify_uv()
    elif args.command == "stage100-bootstrap":
        stage100_bootstrap()
    elif args.command == "stage100-bootstrap-preflight":
        stage100_bootstrap_preflight()
    elif args.command == "synthetic-reset":
        synthetic_reset()
    elif args.command == "synthetic-apply":
        synthetic_apply(
            profile=args.profile,
            seed=args.seed,
            dataset_version=args.dataset_version,
            clock_policy=args.clock_policy,
            clock_anchor=args.clock_anchor,
        )
    elif args.command == "synthetic-validate":
        _run(
            [
                _backend_python(),
                "-m",
                "synthetic_data.validation",
                "--source",
                args.source,
                "--profile",
                args.profile,
                "--seed",
                args.seed,
                "--dataset-version",
                args.dataset_version,
                "--clock-policy",
                args.clock_policy,
                "--clock-anchor",
                args.clock_anchor,
            ],
            cwd=BACKEND,
        )


if __name__ == "__main__":
    main()
