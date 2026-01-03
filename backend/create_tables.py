"""
create_tables.py
----------------
Script para crear todas las tablas de la base de datos.
"""

from app.core.database import engine, Base

# -------------------------
# Importar TODOS los modelos
# -------------------------

# MiTienda
from app.models.productos_models import Producto
from app.models.usuarios_models import Usuario
from app.models.tokens_models import TokenRevocado

# MiPlaza
from app.models.publicaciones_models import Publicacion
from app.models.publicaciones_guardadas_models import PublicacionGuardada
from app.models.likes_publicaciones_models import LikePublicacion
from app.models.comercios_models import Comercio
from app.models.rubros_models import Rubro
from app.models.secciones_models import Seccion
from app.models.historias_models import Historia

print("Creando tablas...")
Base.metadata.create_all(bind=engine)
print("Tablas creadas correctamente.")
