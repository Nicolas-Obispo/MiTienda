"""Probe local repetible de timing anti-enumeracion para ET99.9-B3.

Usa exclusivamente fixtures sinteticos, SQLite en memoria y correo fake local.
No imprime emails, secretos, hashes ni muestras individuales.
"""

from __future__ import annotations

import json
import math
import statistics
import time
from contextlib import ExitStack
from datetime import datetime, timezone
from unittest.mock import patch

from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import Base, get_db
from app.core.model_registry import import_all_models
from app.core.security import hash_password
from app.modules.communications.providers.email_provider import FakeEmailProvider
from app.modules.users.models.identity_models import (
    AccountActionRateLimit,
    AccountActionToken,
    PasswordCredential,
)
from app.modules.users.models.usuarios_models import Usuario
from app.modules.users.routes.usuarios_routers import router
from app.modules.users.services.password_recovery_services import (
    password_reset_local_limiter,
)


SAMPLES_PER_PATH = 12
REGISTRATION_SAMPLES_PER_PATH = 30


def _summary(values: list[float]) -> dict[str, float | int]:
    ordered = sorted(values)
    median = statistics.median(ordered)
    deviations = [abs(value - median) for value in ordered]
    return {
        "samples": len(ordered),
        "median_ms": round(median, 3),
        "p95_ms": round(ordered[math.ceil(0.95 * len(ordered)) - 1], 3),
        "mad_ms": round(statistics.median(deviations), 3),
        "min_ms": round(ordered[0], 3),
        "max_ms": round(ordered[-1], 3),
    }


def _comparison(first: list[float], second: list[float]) -> dict[str, object]:
    first_median = statistics.median(first)
    second_median = statistics.median(second)
    smaller = max(min(first_median, second_median), 0.001)
    return {
        "median_delta_ms": round(abs(first_median - second_median), 3),
        "median_ratio": round(max(first_median, second_median) / smaller, 3),
        "non_overlapping_ranges": (
            max(first) < min(second) or max(second) < min(first)
        ),
    }


def _measure(operation) -> tuple[float, object]:
    started = time.perf_counter_ns()
    result = operation()
    elapsed_ms = (time.perf_counter_ns() - started) / 1_000_000
    return elapsed_ms, result


def run_probe() -> dict[str, object]:
    import_all_models()
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    session_factory = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=engine,
    )
    Base.metadata.create_all(engine)

    def override_get_db():
        db = session_factory()
        try:
            yield db
        finally:
            db.close()

    app = FastAPI()
    app.include_router(router)
    app.dependency_overrides[get_db] = override_get_db
    client = TestClient(app)
    registration_provider = FakeEmailProvider()
    recovery_provider = FakeEmailProvider()

    password_hash = hash_password("Synthetic1")
    with session_factory.begin() as db:
        db.add(
            Usuario(
                id=1,
                email="synthetic-existing@example.com",
                email_canonical="synthetic-existing@example.com",
                email_verified_at=datetime(2026, 9, 25, tzinfo=timezone.utc),
            )
        )
        db.add(
            PasswordCredential(
                usuario_id=1,
                password_hash=password_hash,
                hash_version="bcrypt",
            )
        )

    patches = (
        patch(
            "app.modules.users.services.account_action_rate_limit_services."
            "settings.ACCOUNT_ACTION_RATE_LIMIT_HMAC_SECRET",
            "enumeration-probe-rate-secret",
        ),
        patch(
            "app.modules.users.services.email_verification_services."
            "build_identity_email_provider",
            return_value=registration_provider,
        ),
        patch(
            "app.modules.users.services.password_recovery_services."
            "build_identity_email_provider",
            return_value=recovery_provider,
        ),
        patch(
            "app.modules.users.services.password_recovery_services."
            "settings.IDENTITY_EMAIL_ENABLED",
            True,
        ),
        patch(
            "app.modules.users.services.password_recovery_services."
            "settings.IDENTITY_EMAIL_PROVIDER",
            "fake",
        ),
        patch(
            "app.modules.communications.services.identity_email_services."
            "settings.IDENTITY_EMAIL_FROM_ADDRESS",
            "identity@example.test",
        ),
        patch(
            "app.modules.communications.services.identity_email_services."
            "settings.IDENTITY_EMAIL_PUBLIC_BASE_URL",
            "https://example.test",
        ),
    )

    login = {"missing": [], "wrong_password": []}
    registration = {"new": [], "existing": []}
    recovery = {"existing": [], "missing": []}
    contracts: dict[str, list[tuple[int, object, str | None]]] = {
        "login": [],
        "registration": [],
        "recovery": [],
    }

    with ExitStack() as stack:
        for item in patches:
            stack.enter_context(item)

        for index in range(SAMPLES_PER_PATH):
            for label, email in (
                ("missing", f"login-missing-{index}@example.com"),
                ("wrong_password", "synthetic-existing@example.com"),
            ):
                with session_factory.begin() as db:
                    db.query(AccountActionRateLimit).delete()
                elapsed, response = _measure(
                    lambda email=email: client.post(
                        "/usuarios/login",
                        json={"email": email, "password": "DefinitelyWrong1"},
                    )
                )
                login[label].append(elapsed)
                contracts["login"].append(
                    (
                        response.status_code,
                        response.json(),
                        response.headers.get("cache-control"),
                    )
                )

        registration_payload = {
            "password": "Synthetic2",
            "acepta_terminos": True,
            "acepta_privacidad": True,
        }
        for index in range(REGISTRATION_SAMPLES_PER_PATH):
            for label, email in (
                ("existing", "synthetic-existing@example.com"),
                ("new", f"registration-new-{index}@example.com"),
            ):
                elapsed, response = _measure(
                    lambda email=email: client.post(
                        "/usuarios/registrar",
                        json=registration_payload | {"email": email},
                    )
                )
                registration[label].append(elapsed)
                contracts["registration"].append(
                    (
                        response.status_code,
                        response.json(),
                        response.headers.get("cache-control"),
                    )
                )

        for index in range(SAMPLES_PER_PATH):
            for label, email in (
                ("missing", f"recovery-missing-{index}@example.com"),
                ("existing", "synthetic-existing@example.com"),
            ):
                with session_factory.begin() as db:
                    db.query(AccountActionRateLimit).delete()
                    db.query(AccountActionToken).delete()
                with password_reset_local_limiter._lock:
                    password_reset_local_limiter._buckets.clear()
                elapsed, response = _measure(
                    lambda email=email: client.post(
                        "/usuarios/password/recuperacion",
                        json={"email": email, "channel": "email"},
                    )
                )
                recovery[label].append(elapsed)
                contracts["recovery"].append(
                    (
                        response.status_code,
                        response.json(),
                        response.headers.get("cache-control"),
                    )
                )

    contract_equivalence = {
        name: len(set((status, json.dumps(body, sort_keys=True), cache) for status, body, cache in values)) == 1
        for name, values in contracts.items()
    }
    result = {
        "methodology": {
            "samples_per_path": {
                "login": SAMPLES_PER_PATH,
                "registration": REGISTRATION_SAMPLES_PER_PATH,
                "recovery": SAMPLES_PER_PATH,
            },
            "order": "alternating",
            "clock": "perf_counter_ns",
            "fixtures": "synthetic_only",
            "transport": "fastapi_testclient_local",
            "email": "fake_in_memory",
        },
        "login": {
            "missing": _summary(login["missing"]),
            "wrong_password": _summary(login["wrong_password"]),
            "comparison": _comparison(login["missing"], login["wrong_password"]),
            "public_contract_equivalent": contract_equivalence["login"],
        },
        "registration": {
            "new": _summary(registration["new"]),
            "existing": _summary(registration["existing"]),
            "comparison": _comparison(registration["new"], registration["existing"]),
            "public_contract_equivalent": contract_equivalence["registration"],
        },
        "recovery": {
            "existing": _summary(recovery["existing"]),
            "missing": _summary(recovery["missing"]),
            "comparison": _comparison(recovery["existing"], recovery["missing"]),
            "public_contract_equivalent": contract_equivalence["recovery"],
        },
    }
    engine.dispose()
    return result


if __name__ == "__main__":
    print(json.dumps(run_probe(), ensure_ascii=True, sort_keys=True))
