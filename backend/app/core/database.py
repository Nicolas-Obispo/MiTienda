"""
database.py
-----------
Módulo responsable de crear la conexión con la base de datos usando SQLAlchemy.

Incluye:
- Motor de conexión (engine)
- Sesiones (SessionLocal)
- Base para modelos ORM
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from app.core.config import settings

# Crear la URL de conexión usando nuestras configuraciones
DATABASE_URL = settings.DATABASE_URL

# Motor de base de datos
engine = create_engine(
    DATABASE_URL,
    echo=False  # Cambiar a True para ver las consultas SQL en consola
)

# Sesiones de base de datos
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base que usarán los modelos ORM
Base = declarative_base()


# Dependencia para obtener una sesión de base de datos
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
