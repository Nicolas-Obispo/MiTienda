"""
create_tables.py
----------------
Script para crear todas las tablas de la base de datos.
"""

from app.core.database import engine, Base

# Importar modelos para que SQLAlchemy los reconozca
from app.models.productos_models import Producto
from app.models.usuarios_models import Usuario
from app.models.tokens_models import TokenRevocado  # 🔥 ESTE FALTABA

print("Creando tablas...")
Base.metadata.create_all(bind=engine)
print("Tablas creadas correctamente.")
