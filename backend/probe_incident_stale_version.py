"""Prueba local controlada del conflicto de version de Incidentes.

El comando usa exclusivamente endpoints existentes, no reintenta requests y
nunca imprime autenticacion, payloads ni cuerpos de error.
"""

import argparse
import json
import sys
import uuid
from dataclasses import dataclass
from typing import Protocol
from urllib.error import HTTPError
from urllib.parse import urlparse
from urllib.request import Request, urlopen

from app.core.auth import crear_token_jwt


DEFAULT_BASE_URL = "http://127.0.0.1:8000"


class ProbeTransport(Protocol):
    def request(self, method: str, path: str, *, token: str,
                body: dict | None = None) -> tuple[int, object | None]: ...


class LocalHttpTransport:
    def __init__(self, base_url: str):
        parsed = urlparse(base_url)
        if parsed.scheme not in {"http", "https"} or parsed.hostname not in {
            "127.0.0.1", "localhost", "::1",
        }:
            raise ValueError("incident_probe_loopback_required")
        self.base_url = base_url.rstrip("/")

    def request(self, method: str, path: str, *, token: str,
                body: dict | None = None) -> tuple[int, object | None]:
        encoded = json.dumps(body).encode("utf-8") if body is not None else None
        request = Request(
            f"{self.base_url}{path}",
            data=encoded,
            method=method,
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
                "User-Agent": "FeedGo-Incident-Probe/1.0",
            },
        )
        try:
            with urlopen(request, timeout=10) as response:  # nosec B310: loopback validated
                raw = response.read()
                return response.status, json.loads(raw) if raw else None
        except HTTPError as exc:
            # El cuerpo externo se descarta deliberadamente.
            exc.close()
            return exc.code, None


@dataclass(frozen=True)
class ProbeResult:
    stale_action_status: int
    final_version: int
    rejected_event_absent: bool


def run_stale_version_probe(*, transport: ProbeTransport, token: str,
                            operator_usuario_id: int,
                            probe_id: str | None = None) -> ProbeResult:
    identifier = probe_id or uuid.uuid4().hex
    opened_status, opened = transport.request(
        "POST",
        "/administracion/incidentes",
        token=token,
        body={
            "title": "Fixture aislado de concurrencia 97.6",
            "summary": "Expediente sintetico para demostrar version obsoleta.",
            "incident_type": "availability",
            "severity": "sev3_medium",
            "owner_usuario_id": operator_usuario_id,
            "idempotency_key": f"stale-probe-open-{identifier}",
        },
    )
    if opened_status != 201 or not isinstance(opened, dict):
        raise RuntimeError("incident_probe_open_failed")
    public_id = opened.get("incident", {}).get("public_id")
    if not isinstance(public_id, str):
        raise RuntimeError("incident_probe_identifier_missing")

    legal_status, _ = transport.request(
        "POST",
        f"/administracion/incidentes/{public_id}/acciones",
        token=token,
        body={
            "action": "record_legal_assessment",
            "expected_version": 1,
            "idempotency_key": f"stale-probe-legal-{identifier}",
            "summary": "Evaluacion legal sintetica de la prueba controlada.",
            "legal_assessment_status": "not_required",
            "personal_data_impact": "none",
            "user_communication_status": "not_required",
            "authority_communication_status": "not_required",
        },
    )
    if legal_status != 201:
        raise RuntimeError("incident_probe_legal_step_failed")

    stale_status, _ = transport.request(
        "POST",
        f"/administracion/incidentes/{public_id}/acciones",
        token=token,
        body={
            "action": "record_finding",
            "expected_version": 1,
            "idempotency_key": f"stale-probe-rejected-{identifier}",
            "summary": "Accion sintetica con version congelada obsoleta.",
        },
    )
    detail_status, detail = transport.request(
        "GET", f"/administracion/incidentes/{public_id}", token=token,
    )
    events_status, events = transport.request(
        "GET", f"/administracion/incidentes/{public_id}/eventos", token=token,
    )
    if detail_status != 200 or not isinstance(detail, dict):
        raise RuntimeError("incident_probe_detail_failed")
    if events_status != 200 or not isinstance(events, list):
        raise RuntimeError("incident_probe_timeline_failed")

    result = ProbeResult(
        stale_action_status=stale_status,
        final_version=detail.get("version"),
        rejected_event_absent=all(
            event.get("event_type") != "record_finding" for event in events
        ),
    )
    if result != ProbeResult(409, 2, True):
        raise RuntimeError("incident_probe_contract_not_demonstrated")
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Demuestra una unica colision 409 por version obsoleta",
    )
    parser.add_argument("--run", action="store_true", required=True)
    parser.add_argument("--usuario-id", type=int, required=True)
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL)
    args = parser.parse_args(argv)
    if args.usuario_id <= 0:
        print("probe=blocked reason=invalid_operator", file=sys.stderr)
        return 2
    try:
        transport = LocalHttpTransport(args.base_url)
        token = crear_token_jwt({"sub": str(args.usuario_id)})
        result = run_stale_version_probe(
            transport=transport,
            token=token,
            operator_usuario_id=args.usuario_id,
        )
    except Exception:
        print("probe=failed result=sanitized", file=sys.stderr)
        return 1
    print("probe=approved")
    print(f"stale_action_status={result.stale_action_status}")
    print(f"final_version={result.final_version}")
    print(f"rejected_event_absent={str(result.rejected_event_absent).lower()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
