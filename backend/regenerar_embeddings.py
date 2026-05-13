"""
Script para regenerar embeddings de todos los espacios.

Se ejecuta desde consola:

python regenerar_embeddings.py
"""

# ============================================================
# IMPORTANTE:
# Importamos TODOS los modelos relacionados para que
# SQLAlchemy registre correctamente los mappers.
# ============================================================

# USERS
import app.modules.users.models.usuarios_models
import app.modules.users.models.tokens_models

# SPACES
import app.modules.spaces.models.comercios_models

# PRODUCTS
import app.modules.products.models.productos_models
import app.modules.products.models.rubros_models
import app.modules.products.models.secciones_models

# POSTS
import app.modules.posts.models.publicaciones_models

# STORIES
import app.modules.stories.models.historias_models
import app.modules.stories.models.historias_vistas_models
import app.modules.stories.models.historias_likes_models

# SOCIAL
import app.modules.social.models.likes_publicaciones_models
import app.modules.social.models.publicaciones_guardadas_models
import app.modules.social.models.seguidores_models

# AI
import app.modules.ai.models.comercios_embeddings_models
import app.modules.ai.models.usuarios_embeddings_models

from app.core.database import SessionLocal

from app.modules.spaces.models.comercios_models import Comercio

from app.modules.ai.services.comercios_embeddings_services import (
    upsert_embedding_comercio,
)


def main():
    db = SessionLocal()

    comercios = db.query(Comercio).all()

    print(f"\nTotal espacios: {len(comercios)}\n")

    for comercio in comercios:
        print(
            f"Recalculando embedding -> "
            f"{comercio.id} - {comercio.nombre}"
        )

        upsert_embedding_comercio(
            db=db,
            comercio=comercio,
        )

    db.close()

    print("\nEmbeddings regenerados correctamente.\n")


if __name__ == "__main__":
    main()