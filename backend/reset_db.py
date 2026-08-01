"""
reset_db.py
-----------
Script destructivo de utilidad exclusiva para desarrollo local.

Importar este modulo no modifica la base de datos.
"""

import argparse
import sys

from app.core.database import Base, engine
from app.core.model_registry import import_all_models

CONFIRMACION_DESTRUCTIVA = "RESET_DB_DROP_ALL"
HOSTS_LOCALES_PERMITIDOS = {"localhost", "127.0.0.1", "::1"}


class ResetDbAbortadoError(RuntimeError):
    pass


def _destino_seguro() -> str:
    host = engine.url.host
    database = engine.url.database

    if not host or not database:
        raise ResetDbAbortadoError("Destino de base de datos ambiguo.")

    return f"{engine.dialect.name}://{host}/{database}"


def _validar_destino_local() -> None:
    host = engine.url.host
    database = engine.url.database

    if not host or not database:
        raise ResetDbAbortadoError("Destino de base de datos ambiguo.")

    if host not in HOSTS_LOCALES_PERMITIDOS:
        raise ResetDbAbortadoError(
            "reset_db.py solo puede ejecutarse contra un host local."
        )


def reset_database(confirmacion: str) -> None:
    if confirmacion != CONFIRMACION_DESTRUCTIVA:
        raise ResetDbAbortadoError(
            f"Confirmacion requerida: {CONFIRMACION_DESTRUCTIVA}"
        )

    _validar_destino_local()
    import_all_models()

    print("ADVERTENCIA: esta operacion elimina todas las tablas y datos.")
    print(f"Destino: {_destino_seguro()}")
    print("Eliminando tablas existentes...")
    Base.metadata.drop_all(bind=engine)
    print("Creando tablas nuevas...")
    Base.metadata.create_all(bind=engine)
    print("Base de datos recreada correctamente.")


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Recrea todas las tablas de una base local de desarrollo."
    )
    parser.add_argument(
        "--confirm",
        required=True,
        help=f"Debe ser exactamente {CONFIRMACION_DESTRUCTIVA}.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    try:
        reset_database(args.confirm)
    except ResetDbAbortadoError as exc:
        print(f"ABORTADO: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
