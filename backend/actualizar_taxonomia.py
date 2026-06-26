"""
actualizar_taxonomia.py
-----------------------
Crea y sincroniza la base inicial del motor de descubrimiento.

Es idempotente:
- crea taxonomy_nodes y taxonomy_assignments si faltan.
- crea/actualiza nodos base por slug.
- mapea rubros actuales.
- crea assignments para comercios actuales segun comercio.rubro_id.
"""

import app.modules.users.models.usuarios_models
import app.modules.users.models.tokens_models
import app.modules.spaces.models.comercios_models
import app.modules.products.models.productos_models
import app.modules.products.models.rubros_models
import app.modules.products.models.secciones_models
import app.modules.posts.models.publicaciones_models
import app.modules.social.models.likes_publicaciones_models
import app.modules.social.models.publicaciones_guardadas_models
import app.modules.social.models.seguidores_models
import app.modules.stories.models.historias_models
import app.modules.stories.models.historias_vistas_models
import app.modules.stories.models.historias_likes_models
import app.modules.ai.models.comercios_embeddings_models
import app.modules.ai.models.usuarios_embeddings_models
import app.modules.analytics.models.comercios_metricas_sociales_models
import app.modules.analytics.models.comercios_metricas_snapshots_models
import app.modules.discovery.models.taxonomy_models

from app.core.database import SessionLocal, engine
from app.modules.discovery.models.taxonomy_models import (
    TaxonomyAssignment,
    TaxonomyNode,
)
from app.modules.discovery.services.taxonomy_seed_services import (
    asegurar_taxonomia_base,
)


def crear_tablas_taxonomia() -> None:
    TaxonomyNode.__table__.create(bind=engine, checkfirst=True)
    TaxonomyAssignment.__table__.create(bind=engine, checkfirst=True)


def actualizar_taxonomia() -> None:
    crear_tablas_taxonomia()

    db = SessionLocal()
    try:
        result = asegurar_taxonomia_base(db)
        assignments = result.assignments

        print("Taxonomia actualizada.")
        print(f"Nodos creados: {result.nodos_creados}")
        print(f"Nodos actualizados: {result.nodos_actualizados}")
        print(f"Nodos existentes sin cambios: {result.nodos_existentes}")

        if assignments:
            print(f"Rubros mapeados: {assignments.rubros_mapeados}")
            print(
                "Assignments de rubros creados: "
                f"{assignments.rubro_assignments_creados}"
            )
            print(
                "Assignments de rubros existentes: "
                f"{assignments.rubro_assignments_existentes}"
            )
            print(f"Comercios asignados: {assignments.comercios_asignados}")
            print(
                "Assignments de comercios creados: "
                f"{assignments.comercio_assignments_creados}"
            )
            print(
                "Assignments de comercios existentes: "
                f"{assignments.comercio_assignments_existentes}"
            )
    finally:
        db.close()


if __name__ == "__main__":
    actualizar_taxonomia()
