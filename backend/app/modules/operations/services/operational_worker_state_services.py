"""Estado local, volatil y sanitizado del worker de correo operativo."""

from __future__ import annotations

import json
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from app.core.config import settings


STATE_VERSION = 1


def worker_state_path() -> Path:
    configured = settings.OPERATIONAL_EMAIL_WORKER_STATE_FILE
    if configured and configured.strip():
        return Path(configured).expanduser().resolve()
    return Path(tempfile.gettempdir()) / "feedgo-operational-email-worker-state.json"


def publish_worker_state(status: str) -> None:
    if status not in {"active", "stopped"}:
        raise ValueError("operational_worker_state_invalid")
    path = worker_state_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(f"{path.suffix}.{os.getpid()}.tmp")
    payload = {
        "version": STATE_VERSION,
        "status": status,
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    temporary.write_text(json.dumps(payload, separators=(",", ":")), encoding="utf-8")
    temporary.replace(path)


def read_sanitized_worker_state(*, now: datetime | None = None) -> dict[str, object]:
    if not (settings.ADMIN_EMAIL_ENABLED and settings.OPERATIONAL_EMAIL_DISPATCHER_ENABLED):
        return {"status": "disabled", "scope": "local_runtime", "volatile": True}
    status = "stopped"
    try:
        payload = json.loads(worker_state_path().read_text(encoding="utf-8"))
        updated_at = datetime.fromisoformat(payload["updated_at"])
        if updated_at.tzinfo is None:
            updated_at = updated_at.replace(tzinfo=timezone.utc)
        age = ((now or datetime.now(timezone.utc)) - updated_at).total_seconds()
        freshness_limit = max(
            settings.OPERATIONAL_EMAIL_WORKER_HEARTBEAT_TTL_SECONDS,
            settings.OPERATIONAL_EMAIL_POLL_INTERVAL_SECONDS * 3 + 5,
        )
        if (
            payload.get("version") == STATE_VERSION
            and payload.get("status") == "active"
            and 0 <= age <= freshness_limit
        ):
            status = "active"
    except (OSError, ValueError, TypeError, KeyError, json.JSONDecodeError):
        status = "stopped"
    return {"status": status, "scope": "local_runtime", "volatile": True}
