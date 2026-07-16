"""Builder del bloque Perfil Publico."""

from app.modules.indexer.models.index_block_models import PublicProfileBlock
from app.modules.indexer.models.source_snapshot_models import CommerceSourceSnapshot


class PublicProfileBuilder:
    """Construye el bloque Perfil Publico desde snapshot de comercio."""

    def build(self, *, commerce: CommerceSourceSnapshot) -> PublicProfileBlock:
        """Construye Perfil Publico sin datos privados."""

        return PublicProfileBlock(
            display_name=commerce.nombre,
            description=commerce.descripcion,
            public_location_label=self._public_location_label(commerce),
            public_media_refs=[],
        )

    @staticmethod
    def _public_location_label(commerce: CommerceSourceSnapshot) -> str | None:
        parts = [
            part.strip()
            for part in (commerce.ciudad, commerce.provincia)
            if part and part.strip()
        ]
        if not parts:
            return None
        return ", ".join(parts)
