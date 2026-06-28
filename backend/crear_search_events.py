"""
crear_search_events.py
----------------------
Script idempotente para crear la tabla search_events.
"""

from app.core.database import Base, engine
from app.modules.search.models.search_event_models import SearchEvent


def crear_tabla_search_events() -> None:
    SearchEvent.__table__.create(bind=engine, checkfirst=True)


if __name__ == "__main__":
    print("Creando tabla search_events...")
    crear_tabla_search_events()
    print("Tabla search_events lista.")
