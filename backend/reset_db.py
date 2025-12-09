"""
reset_db.py
-----------
Script de utilidad para desarrolladores.

Permite:
- Borrar todas las tablas de la base de datos
- Crear nuevamente todas las tablas según los modelos actuales

⚠️ Usar solo en desarrollo, NUNCA en producción.
"""

from app.core.database import Base, engine
from app.models.productos_models import Producto

print("🧹 Eliminando tablas existentes...")
Base.metadata.drop_all(bind=engine)

print("🧱 Creando tablas nuevas...")
Base.metadata.create_all(bind=engine)

print("✅ Base de datos actualizada correctamente.")
