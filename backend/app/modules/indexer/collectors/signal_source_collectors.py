"""Collectors de senales agregadas para el Indexador."""

from sqlalchemy.orm import Session

from app.modules.analytics.models.comercios_metricas_sociales_models import (
    ComercioMetricasSociales,
)
from app.modules.indexer.models.source_snapshot_models import SignalSourceSnapshot


class SignalSourceCollector:
    """Obtiene senales agregadas disponibles sin recalcular ni rankear."""

    source_name = "signals"

    def collect(self, db: Session, *, commerce_id: int) -> SignalSourceSnapshot:
        """Devuelve un snapshot de senales consolidadas existentes."""

        metricas = (
            db.query(ComercioMetricasSociales)
            .filter(ComercioMetricasSociales.comercio_id == commerce_id)
            .first()
        )
        if metricas is None:
            return SignalSourceSnapshot(
                source_name=self.source_name,
                metrics={},
                activity={},
                warnings=["metricas_sociales_no_disponibles"],
            )

        return SignalSourceSnapshot(
            source_name=self.source_name,
            metrics={
                "total_seguidores": metricas.total_seguidores,
                "total_publicaciones": metricas.total_publicaciones,
                "total_likes_publicaciones": metricas.total_likes_publicaciones,
                "total_guardados_publicaciones": metricas.total_guardados_publicaciones,
                "total_historias": metricas.total_historias,
                "total_vistas_historias": metricas.total_vistas_historias,
                "total_likes_historias": metricas.total_likes_historias,
            },
            activity={
                "updated_at": (
                    metricas.updated_at.isoformat() if metricas.updated_at else None
                ),
            },
        )
