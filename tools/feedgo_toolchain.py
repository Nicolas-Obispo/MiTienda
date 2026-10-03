"""Resolucion reproducible y adquisicion explicita del toolchain FeedGo."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import platform
import re
import shutil
import stat
import subprocess
import tarfile
from typing import Callable
import zipfile


ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = ROOT / "tools" / "toolchain.json"
CACHE_ROOT = ROOT / ".tools"
RECEIPT_NAME = "install-receipt.json"


class ToolchainError(RuntimeError):
    pass


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _load_manifest(path: Path = MANIFEST_PATH) -> dict:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("schema_version") != 1:
        raise ToolchainError("toolchain_manifest_version_invalid")
    return payload


def _platform_key() -> str:
    machine = platform.machine().lower()
    if machine not in {"amd64", "x86_64"}:
        raise ToolchainError("toolchain_platform_unsupported")
    if os.name == "nt":
        return "windows-x86_64"
    if platform.system().lower() == "linux":
        return "linux-x86_64"
    raise ToolchainError("toolchain_platform_unsupported")


def _uv_contract(manifest_path: Path = MANIFEST_PATH) -> tuple[str, str, dict]:
    manifest = _load_manifest(manifest_path)
    uv = manifest.get("tools", {}).get("uv", {})
    version = uv.get("version")
    key = _platform_key()
    artifact = uv.get("artifacts", {}).get(key)
    if not version or not artifact:
        raise ToolchainError("uv_manifest_contract_missing")
    required = {"archive", "url", "sha256", "executable"}
    official_prefix = f"https://github.com/astral-sh/uv/releases/download/{version}/"
    if (
        set(artifact) != required
        or not re.fullmatch(r"[0-9a-f]{64}", str(artifact["sha256"]))
        or artifact["url"] != official_prefix + artifact["archive"]
    ):
        raise ToolchainError("uv_manifest_contract_invalid")
    return str(version), key, artifact


def _default_uv_path(version: str, platform_key: str, executable: str) -> Path:
    return CACHE_ROOT / "uv" / version / platform_key / executable


def _read_uv_version(executable: Path) -> str:
    completed = subprocess.run(
        [str(executable), "--version"],
        check=True,
        capture_output=True,
        text=True,
    )
    return completed.stdout.strip()


def resolve_uv(
    *,
    manifest_path: Path = MANIFEST_PATH,
    cache_root: Path = CACHE_ROOT,
    environment: dict[str, str] | None = None,
    version_reader: Callable[[Path], str] = _read_uv_version,
) -> str:
    """Resuelve uv sin PATH ni red y exige receipt, hash y version exactos."""
    environment = os.environ if environment is None else environment
    version, platform_key, artifact = _uv_contract(manifest_path)
    default = cache_root / "uv" / version / platform_key / artifact["executable"]
    candidate = Path(environment.get("FEEDGO_UV_BIN", str(default))).resolve()
    receipt_path = candidate.parent / RECEIPT_NAME

    if not candidate.is_file() or not receipt_path.is_file():
        raise ToolchainError("uv_verified_installation_missing")
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    expected_receipt = {
        "schema_version": 1,
        "tool": "uv",
        "version": version,
        "platform": platform_key,
        "archive": artifact["archive"],
        "archive_sha256": artifact["sha256"],
        "executable": artifact["executable"],
    }
    for key, value in expected_receipt.items():
        if receipt.get(key) != value:
            raise ToolchainError("uv_installation_receipt_invalid")
    if receipt.get("executable_sha256") != _sha256(candidate):
        raise ToolchainError("uv_executable_checksum_mismatch")
    reported_version = version_reader(candidate)
    if not re.fullmatch(rf"uv {re.escape(version)}(?: \([^\r\n]+\))?", reported_version):
        raise ToolchainError("uv_version_mismatch")
    return str(candidate)


def _safe_member_name(name: str, expected_executable: str) -> bool:
    path = PurePosixPath(name.replace("\\", "/"))
    return not path.is_absolute() and ".." not in path.parts and path.name == expected_executable


def install_uv_from_archive(
    archive_path: Path,
    *,
    manifest_path: Path = MANIFEST_PATH,
    cache_root: Path = CACHE_ROOT,
) -> Path:
    """Instala desde un archivo local verificado; nunca accede a la red."""
    version, platform_key, artifact = _uv_contract(manifest_path)
    archive_path = archive_path.resolve()
    if archive_path.name != artifact["archive"] or not archive_path.is_file():
        raise ToolchainError("uv_archive_invalid")
    if _sha256(archive_path) != artifact["sha256"]:
        raise ToolchainError("uv_archive_checksum_mismatch")

    destination = cache_root / "uv" / version / platform_key
    executable = destination / artifact["executable"]
    if destination.exists():
        raise ToolchainError("uv_installation_destination_not_empty")
    destination.mkdir(parents=True)
    try:
        if archive_path.suffix == ".zip":
            with zipfile.ZipFile(archive_path) as bundle:
                members = [name for name in bundle.namelist() if _safe_member_name(name, artifact["executable"])]
                if len(members) != 1:
                    raise ToolchainError("uv_archive_layout_invalid")
                with bundle.open(members[0]) as source, executable.open("wb") as target:
                    shutil.copyfileobj(source, target)
        elif archive_path.name.endswith(".tar.gz"):
            with tarfile.open(archive_path, "r:gz") as bundle:
                members = [member for member in bundle.getmembers() if member.isfile() and _safe_member_name(member.name, artifact["executable"])]
                if len(members) != 1:
                    raise ToolchainError("uv_archive_layout_invalid")
                source = bundle.extractfile(members[0])
                if source is None:
                    raise ToolchainError("uv_archive_layout_invalid")
                with source, executable.open("wb") as target:
                    shutil.copyfileobj(source, target)
        else:
            raise ToolchainError("uv_archive_format_invalid")

        executable.chmod(executable.stat().st_mode | stat.S_IXUSR)
        receipt = {
            "schema_version": 1,
            "tool": "uv",
            "version": version,
            "platform": platform_key,
            "archive": artifact["archive"],
            "archive_sha256": artifact["sha256"],
            "executable": artifact["executable"],
            "executable_sha256": _sha256(executable),
        }
        (destination / RECEIPT_NAME).write_text(
            json.dumps(receipt, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
    except Exception:
        shutil.rmtree(destination, ignore_errors=True)
        raise
    return executable
