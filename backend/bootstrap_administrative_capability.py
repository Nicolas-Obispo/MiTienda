"""Bootstrap local auditado de capacidades administrativas.

Importar este modulo no modifica la base. Grant/revoke son acciones explicitas
y requieren usuario, capacidad y motivo.
"""

import argparse
import sys

from sqlalchemy.exc import SQLAlchemyError

from app.core.database import SessionLocal, engine
from app.modules.administration.capabilities import ADMINISTRATIVE_CAPABILITIES
from app.modules.administration.services.administrative_authorization_services import (
    BOOTSTRAP_SOURCE,
    AdministrativeUserNotFoundError,
    record_administrative_capability_change,
)


def safe_database_target() -> str:
    host = engine.url.host or "<sin-host>"
    database = engine.url.database or "<sin-base>"
    return f"{engine.dialect.name}://{host}/{database}"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Otorga o revoca una capacidad administrativa auditada.",
    )
    parser.add_argument("action", choices=("grant", "revoke"))
    parser.add_argument("--usuario-id", type=int, required=True)
    parser.add_argument(
        "--capacidad",
        required=True,
        choices=sorted(ADMINISTRATIVE_CAPABILITIES),
    )
    parser.add_argument("--motivo", required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    print(f"Destino: {safe_database_target()}")

    db = SessionLocal()
    try:
        event, changed = record_administrative_capability_change(
            db,
            usuario_id=args.usuario_id,
            capability=args.capacidad,
            action=args.action,
            source=BOOTSTRAP_SOURCE,
            reason=args.motivo,
        )
    except (AdministrativeUserNotFoundError, SQLAlchemyError, ValueError) as exc:
        db.rollback()
        print(f"BOOTSTRAP FALLIDO: {exc}", file=sys.stderr)
        return 2
    finally:
        db.close()

    if not changed:
        print("Sin cambios: el estado solicitado ya estaba vigente.")
        return 0

    print(f"BOOTSTRAP OK: evento {event.id} registrado.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
