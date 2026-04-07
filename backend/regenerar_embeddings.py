"""
Script para regenerar embeddings de todos los comercios.

Se ejecuta desde consola:
python regenerar_embeddings.py
"""

# ============================================================
# IMPORTANTE:
# Importamos TODOS los modelos que participan en relaciones
# para que SQLAlchemy registre correctamente los mappers.
# ============================================================

import app.models.usuarios_models
import app.models.rubros_models
import app.models.secciones_models
import app.models.comercios_models
import app.models.comercios_embeddings_models
import app.models.productos_models
import app.models.publicaciones_models
import app.models.historias_models
import app.models.historias_vistas_models
import app.models.likes_publicaciones_models
import app.models.publicaciones_guardadas_models
import app.models.tokens_models

from app.core.database import SessionLocal
from app.models.comercios_models import Comercio
from app.services.comercios_embeddings_services import upsert_embedding_comercio


def main():
    db = SessionLocal()

    comercios = db.query(Comercio).all()

    print(f"\nTotal comercios: {len(comercios)}\n")

    for comercio in comercios:
        print(f"Recalculando embedding -> {comercio.id} - {comercio.nombre}")
        upsert_embedding_comercio(db=db, comercio=comercio)

    db.close()
    print("\nEmbeddings regenerados correctamente.\n")


if __name__ == "__main__":
    main()