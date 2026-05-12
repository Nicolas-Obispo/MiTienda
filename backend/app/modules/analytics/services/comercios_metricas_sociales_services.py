"""
comercios_metricas_sociales_services.py
---------------------------------------
Servicios centrales para sincronizar métricas
sociales persistentes de los espacios.
"""

from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import date

from app.modules.analytics.models.comercios_metricas_sociales_models import (
    ComercioMetricasSociales,
)

from app.modules.analytics.models.comercios_metricas_snapshots_models import (
    ComercioMetricasSnapshot,
)

from app.modules.social.models.seguidores_models import Seguidores
from app.modules.posts.models.publicaciones_models import Publicacion
from app.modules.social.models.likes_publicaciones_models import LikePublicacion
from app.modules.social.models.publicaciones_guardadas_models import (
    PublicacionGuardada,
)

from app.modules.stories.models.historias_models import Historia
from app.modules.stories.models.historias_vistas_models import HistoriaVista
from app.modules.stories.models.historias_likes_models import HistoriaLike


# =========================================================
# OBTENER O CREAR MÉTRICAS
# =========================================================

def obtener_o_crear_metricas(
    db: Session,
    comercio_id: int,
):
    """
    Obtiene las métricas persistentes del comercio.

    Si no existen, las crea automáticamente.
    """

    metricas = (
        db.query(ComercioMetricasSociales)
        .filter(
            ComercioMetricasSociales.comercio_id == comercio_id
        )
        .first()
    )

    if metricas:
        return metricas

    metricas = ComercioMetricasSociales(
        comercio_id=comercio_id,
    )

    db.add(metricas)
    db.commit()
    db.refresh(metricas)

    return metricas


# =========================================================
# RECALCULAR MÉTRICAS COMPLETAS
# =========================================================

def recalcular_metricas_comercio(
    db: Session,
    comercio_id: int,
):
    """
    Recalcula TODAS las métricas sociales del espacio.

    Fuente de verdad:
    base de datos real.
    """

    metricas = obtener_o_crear_metricas(
        db=db,
        comercio_id=comercio_id,
    )

    # -------------------------------------------------
    # Seguidores
    # -------------------------------------------------

    total_seguidores = (
        db.query(Seguidores)
        .filter(
            Seguidores.comercio_id == comercio_id
        )
        .count()
    )

    # -------------------------------------------------
    # Publicaciones
    # -------------------------------------------------

    publicaciones_ids = (
        db.query(Publicacion.id)
        .filter(
            Publicacion.comercio_id == comercio_id
        )
        .all()
    )

    publicaciones_ids = [
        item[0]
        for item in publicaciones_ids
    ]

    total_publicaciones = len(publicaciones_ids)

    # -------------------------------------------------
    # Likes publicaciones
    # -------------------------------------------------

    total_likes_publicaciones = 0

    if publicaciones_ids:
        total_likes_publicaciones = (
            db.query(LikePublicacion)
            .filter(
                LikePublicacion.publicacion_id.in_(
                    publicaciones_ids
                )
            )
            .count()
        )

    # -------------------------------------------------
    # Guardados publicaciones
    # -------------------------------------------------

    total_guardados_publicaciones = 0

    if publicaciones_ids:
        total_guardados_publicaciones = (
            db.query(PublicacionGuardada)
            .filter(
                PublicacionGuardada.publicacion_id.in_(
                    publicaciones_ids
                )
            )
            .count()
        )

    # -------------------------------------------------
    # Historias
    # -------------------------------------------------

    historias_ids = (
        db.query(Historia.id)
        .filter(
            Historia.comercio_id == comercio_id
        )
        .all()
    )

    historias_ids = [
        item[0]
        for item in historias_ids
    ]

    total_historias = len(historias_ids)

    # -------------------------------------------------
    # Vistas historias
    # -------------------------------------------------

    total_vistas_historias = 0

    if historias_ids:
        total_vistas_historias = (
            db.query(HistoriaVista)
            .filter(
                HistoriaVista.historia_id.in_(
                    historias_ids
                )
            )
            .count()
        )

    # -------------------------------------------------
    # Likes historias
    # -------------------------------------------------

    total_likes_historias = 0

    if historias_ids:
        total_likes_historias = (
            db.query(HistoriaLike)
            .filter(
                HistoriaLike.historia_id.in_(
                    historias_ids
                )
            )
            .count()
        )

    # -------------------------------------------------
    # Persistencia final
    # -------------------------------------------------

    metricas.total_seguidores = total_seguidores

    metricas.total_publicaciones = total_publicaciones

    metricas.total_likes_publicaciones = (
        total_likes_publicaciones
    )

    metricas.total_guardados_publicaciones = (
        total_guardados_publicaciones
    )

    metricas.total_historias = total_historias

    metricas.total_vistas_historias = (
        total_vistas_historias
    )

    metricas.total_likes_historias = (
        total_likes_historias
    )

    db.commit()
    db.refresh(metricas)

    return metricas
# =========================================================
# SNAPSHOT DIARIO
# =========================================================

def generar_snapshot_metricas_comercio(
    db: Session,
    comercio_id: int,
):
    """
    Genera o actualiza snapshot diario
    de métricas sociales del espacio.

    Evita duplicados por fecha.
    """

    # ---------------------------------------------
    # Recalculamos métricas reales actuales
    # ---------------------------------------------

    metricas = recalcular_metricas_comercio(
        db=db,
        comercio_id=comercio_id,
    )

    hoy = date.today()

    # ---------------------------------------------
    # Buscar snapshot existente del día
    # ---------------------------------------------

    snapshot = (
        db.query(ComercioMetricasSnapshot)
        .filter(
            ComercioMetricasSnapshot.comercio_id == comercio_id,
            ComercioMetricasSnapshot.fecha == hoy,
        )
        .first()
    )

    # ---------------------------------------------
    # Crear si no existe
    # ---------------------------------------------

    if not snapshot:
        snapshot = ComercioMetricasSnapshot(
            comercio_id=comercio_id,
            fecha=hoy,
        )

        db.add(snapshot)

    # ---------------------------------------------
    # Actualizar métricas
    # ---------------------------------------------

    snapshot.total_seguidores = metricas.total_seguidores

    snapshot.total_publicaciones = (
        metricas.total_publicaciones
    )

    snapshot.total_likes_publicaciones = (
        metricas.total_likes_publicaciones
    )

    snapshot.total_guardados_publicaciones = (
        metricas.total_guardados_publicaciones
    )

    snapshot.total_historias = (
        metricas.total_historias
    )

    snapshot.total_vistas_historias = (
        metricas.total_vistas_historias
    )

    snapshot.total_likes_historias = (
        metricas.total_likes_historias
    )

    db.commit()
    db.refresh(snapshot)

    return snapshot

# =========================================================
# COMPARACIÓN DE MÉTRICAS
# =========================================================

def obtener_comparacion_metricas_comercio(
    db: Session,
    comercio_id: int,
):
    """
    Compara snapshot actual vs snapshot anterior.

    Base para:
    - tendencias
    - crecimiento
    - insights
    - analytics reales
    """

    snapshots = (
        db.query(ComercioMetricasSnapshot)
        .filter(
            ComercioMetricasSnapshot.comercio_id == comercio_id
        )
        .order_by(
            ComercioMetricasSnapshot.fecha.desc()
        )
        .limit(2)
        .all()
    )

    # -------------------------------------------------
    # Si no hay snapshots suficientes
    # -------------------------------------------------

    if not snapshots:
        return {
            "has_data": False,
        }

    actual = snapshots[0]

    anterior = snapshots[1] if len(snapshots) > 1 else None

    # -------------------------------------------------
    # Helper
    # -------------------------------------------------

    def construir_resultado(valor_actual, valor_anterior):
        valor_anterior = valor_anterior or 0

        delta = valor_actual - valor_anterior

        porcentaje = 0

        if valor_anterior > 0:
            porcentaje = round(
                (delta / valor_anterior) * 100,
                2,
            )

        return {
            "actual": valor_actual,
            "anterior": valor_anterior,
            "delta": delta,
            "porcentaje": porcentaje,
        }

    # -------------------------------------------------
    # Resultado final
    # -------------------------------------------------

    return {
        "has_data": True,

        "fecha_actual": actual.fecha,

        "fecha_anterior": (
            anterior.fecha if anterior else None
        ),

        "seguidores": construir_resultado(
            actual.total_seguidores,
            anterior.total_seguidores if anterior else 0,
        ),

        "publicaciones": construir_resultado(
            actual.total_publicaciones,
            anterior.total_publicaciones if anterior else 0,
        ),

        "likes_publicaciones": construir_resultado(
            actual.total_likes_publicaciones,
            anterior.total_likes_publicaciones if anterior else 0,
        ),

        "guardados_publicaciones": construir_resultado(
            actual.total_guardados_publicaciones,
            anterior.total_guardados_publicaciones if anterior else 0,
        ),

        "historias": construir_resultado(
            actual.total_historias,
            anterior.total_historias if anterior else 0,
        ),

        "vistas_historias": construir_resultado(
            actual.total_vistas_historias,
            anterior.total_vistas_historias if anterior else 0,
        ),

        "likes_historias": construir_resultado(
            actual.total_likes_historias,
            anterior.total_likes_historias if anterior else 0,
        ),
    }