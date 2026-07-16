"""Collectors de fuente Comercio para el Indexador."""

from sqlalchemy.orm import Session

from app.modules.indexer.models.source_snapshot_models import CommerceSourceSnapshot
from app.modules.spaces.models.comercios_models import Comercio


class CommerceSourceCollector:
    """Obtiene datos base del comercio desde la fuente oficial disponible."""

    source_name = "commerce"

    def collect(self, db: Session, *, commerce_id: int) -> CommerceSourceSnapshot | None:
        """Devuelve un snapshot del comercio sin exponer el modelo fisico."""

        comercio = db.query(Comercio).filter(Comercio.id == commerce_id).first()
        if comercio is None:
            return None

        return CommerceSourceSnapshot(
            source_name=self.source_name,
            commerce_id=comercio.id,
            nombre=comercio.nombre,
            descripcion=comercio.descripcion,
            activo=bool(comercio.activo),
            provincia=comercio.provincia,
            ciudad=comercio.ciudad,
            direccion=comercio.direccion,
            latitud=comercio.latitud,
            longitud=comercio.longitud,
            rubro_id=comercio.rubro_id,
            created_at=comercio.created_at,
            updated_at=comercio.updated_at,
        )
