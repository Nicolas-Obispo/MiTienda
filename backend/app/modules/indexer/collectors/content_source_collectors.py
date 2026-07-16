"""Collectors de contenido para el Indexador."""

from sqlalchemy.orm import Session

from app.modules.indexer.models.source_snapshot_models import (
    ContentSourceSnapshot,
    PublicationSourceSnapshot,
    StorySourceSnapshot,
)
from app.modules.posts.services.publicaciones_services import (
    listar_publicaciones_por_comercio,
)
from app.modules.stories.services.historias_services import (
    listar_historias_activas_por_comercio,
)


class ContentSourceCollector:
    """Obtiene publicaciones e historias activas de un comercio."""

    source_name = "content"

    def collect(self, db: Session, *, commerce_id: int) -> ContentSourceSnapshot:
        """Devuelve un snapshot de contenido publico utilizable."""

        publicaciones = listar_publicaciones_por_comercio(
            db,
            comercio_id=commerce_id,
        )
        historias = listar_historias_activas_por_comercio(
            db,
            comercio_id=commerce_id,
            usuario_id=None,
        )

        return ContentSourceSnapshot(
            source_name=self.source_name,
            publications=[
                PublicationSourceSnapshot(
                    id=publicacion.id,
                    comercio_id=publicacion.comercio_id,
                    titulo=publicacion.titulo,
                    descripcion=publicacion.descripcion,
                    imagen_url=publicacion.imagen_url,
                    is_activa=bool(publicacion.is_activa),
                    created_at=publicacion.created_at,
                    updated_at=publicacion.updated_at,
                )
                for publicacion in publicaciones
            ],
            stories=[
                StorySourceSnapshot(
                    id=historia.id,
                    comercio_id=historia.comercio_id,
                    publicacion_id=historia.publicacion_id,
                    media_url=historia.media_url,
                    is_activa=bool(historia.is_activa),
                    expira_en=historia.expira_en,
                    created_at=historia.created_at,
                    updated_at=historia.updated_at,
                )
                for historia in historias
            ],
        )
