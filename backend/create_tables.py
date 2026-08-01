"""
create_tables.py
----------------
Script para crear tablas faltantes de forma aditiva.

Importar este modulo no modifica la base de datos.
"""

from app.core.database import Base, engine
from app.core.model_registry import import_all_models


def main() -> None:
    import_all_models()

    print("Creando tablas faltantes...")
    Base.metadata.create_all(bind=engine)
    print("Tablas creadas correctamente.")


if __name__ == "__main__":
    main()
