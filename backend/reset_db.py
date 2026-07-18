"""
reset_db.py
-----------
Script de utilidad para desarrollo.

Permite:

- eliminar todas las tablas
- recrear todas las tablas
- sincronizar la DB con los modelos actuales

⚠️ SOLO DESARROLLO
⚠️ NUNCA ejecutar en producción
"""

from app.core.database import Base, engine

# ============================================================
# IMPORTANTE:
# Importamos TODOS los modelos para registrar correctamente
# los mappers y relaciones antes de create_all().
# ============================================================

# USERS
from app.modules.users.models.usuarios_models import Usuario
from app.modules.users.models.tokens_models import TokenRevocado

# SPACES
from app.modules.spaces.models.comercios_models import Comercio

# AVAILABILITY
from app.modules.availability.models.horarios_atencion_models import (
    ComercioHorarioAtencion,
)

# PRODUCTS
from app.modules.products.models.productos_models import Producto
from app.modules.products.models.rubros_models import Rubro
from app.modules.products.models.secciones_models import Seccion

# DISCOVERY
from app.modules.discovery.models.taxonomy_models import (
    TaxonomyAssignment,
    TaxonomyNode,
)

# POSTS
from app.modules.posts.models.publicaciones_models import Publicacion

# SOCIAL
from app.modules.social.models.likes_publicaciones_models import (
    LikePublicacion,
)
from app.modules.social.models.publicaciones_guardadas_models import (
    PublicacionGuardada,
)
from app.modules.social.models.seguidores_models import Seguidores

# STORIES
from app.modules.stories.models.historias_models import Historia
from app.modules.stories.models.historias_vistas_models import HistoriaVista
from app.modules.stories.models.historias_likes_models import HistoriaLike

# AI
from app.modules.ai.models.comercios_embeddings_models import (
    ComercioEmbedding,
)
from app.modules.ai.models.usuarios_embeddings_models import (
    UsuarioEmbedding,
)

# ANALYTICS
from app.modules.analytics.models.comercios_metricas_sociales_models import (
    ComercioMetricasSociales,
)
from app.modules.analytics.models.comercios_metricas_snapshots_models import (
    ComercioMetricasSnapshot,
)

print("🧹 Eliminando tablas existentes...")

Base.metadata.drop_all(bind=engine)

print("🧱 Creando tablas nuevas...")

Base.metadata.create_all(bind=engine)

print("✅ Base de datos actualizada correctamente.")
