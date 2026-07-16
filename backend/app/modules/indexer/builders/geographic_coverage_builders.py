"""Builder del bloque Cobertura Geografica."""

from app.modules.indexer.models.index_block_models import GeographicCoverageBlock
from app.modules.indexer.models.source_snapshot_models import CommerceSourceSnapshot


class GeographicCoverageBuilder:
    """Construye el bloque Cobertura Geografica desde snapshot de comercio."""

    def build(self, *, commerce: CommerceSourceSnapshot) -> GeographicCoverageBlock:
        """Construye cobertura geografica base sin calcular distancia."""

        return GeographicCoverageBlock(
            province=commerce.provincia,
            city=commerce.ciudad,
            address_public=commerce.direccion,
            latitude=commerce.latitud,
            longitude=commerce.longitud,
            coverage_mode="base_location",
        )
