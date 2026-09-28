"""Ejecutor read-only y opt-in del preflight AUTH-LEGACY-01 L1."""

from __future__ import annotations

import json
import os

from app.core.database import SessionLocal, engine
from app.core.model_registry import import_all_models


import_all_models()

from app.modules.users.services.legacy_password_preflight_services import (
    PREFLIGHT_PASS,
    preflight_legacy_password_credentials,
)


ACTION_ENV = "FEEDGO_LEGACY_PASSWORD_PREFLIGHT"


def safe_database_target() -> str:
    host = engine.url.host or "<sin-host>"
    database = engine.url.database or "<sin-base>"
    return f"{engine.dialect.name}://{host}/{database}"


def main() -> int:
    if os.environ.get(ACTION_ENV) != "read_only":
        raise ValueError(f"{ACTION_ENV} debe ser 'read_only'.")
    db = SessionLocal()
    try:
        report = preflight_legacy_password_credentials(db)
    finally:
        db.close()
    print(json.dumps({"target": safe_database_target(), "report": report.safe_summary()}))
    return 0 if report.status == PREFLIGHT_PASS else 2


if __name__ == "__main__":
    raise SystemExit(main())
