"""
comercios_analytics_services.py
-------------------------------
Motor de analytics e insights para espacios de MiPlaza.

Esta capa NO reemplaza las métricas sociales.
Usa métricas reales y snapshots para construir:
- métricas derivadas
- lectura de rendimiento
- insights automáticos
- recomendaciones accionables

Objetivo:
ser una capa escalable similar a analytics de apps de primer nivel.
"""
from sqlalchemy.orm import Session

from app.modules.analytics.services.comercios_metricas_sociales_services import (
    recalcular_metricas_comercio,
    obtener_comparacion_metricas_comercio,
)


def calcular_porcentaje_seguro(
    numerador: int,
    denominador: int,
):
    """
    Calcula un porcentaje evitando división por cero.
    """

    if not denominador or denominador <= 0:
        return 0

    return round((numerador / denominador) * 100, 2)


def calcular_promedio_seguro(
    total: int,
    cantidad: int,
):
    """
    Calcula un promedio evitando división por cero.
    """

    if not cantidad or cantidad <= 0:
        return 0

    return round(total / cantidad, 2)


def obtener_analytics_espacio(
    db: Session,
    comercio_id: int,
):
    """
    Construye analytics completos del espacio.

    Fuente de verdad:
    - métricas sociales persistentes
    - snapshots históricos
    - base real
    """

    metricas = recalcular_metricas_comercio(
        db=db,
        comercio_id=comercio_id,
    )

    comparacion = obtener_comparacion_metricas_comercio(
        db=db,
        comercio_id=comercio_id,
    )

    total_interacciones_publicaciones = (
        metricas.total_likes_publicaciones
        + metricas.total_guardados_publicaciones
    )

    engagement_publicaciones = calcular_porcentaje_seguro(
        numerador=total_interacciones_publicaciones,
        denominador=metricas.total_publicaciones,
    )

    promedio_likes_por_publicacion = calcular_promedio_seguro(
        total=metricas.total_likes_publicaciones,
        cantidad=metricas.total_publicaciones,
    )

    promedio_guardados_por_publicacion = calcular_promedio_seguro(
        total=metricas.total_guardados_publicaciones,
        cantidad=metricas.total_publicaciones,
    )

    promedio_vistas_por_historia = calcular_promedio_seguro(
        total=metricas.total_vistas_historias,
        cantidad=metricas.total_historias,
    )

    promedio_likes_por_historia = calcular_promedio_seguro(
        total=metricas.total_likes_historias,
        cantidad=metricas.total_historias,
    )

    space_score = round(
        (
            (metricas.total_seguidores * 5)
            + (metricas.total_publicaciones * 3)
            + (metricas.total_likes_publicaciones * 2)
            + (metricas.total_guardados_publicaciones * 4)
            + (metricas.total_historias * 1)
            + (metricas.total_vistas_historias * 1)
            + (metricas.total_likes_historias * 2)
            + (engagement_publicaciones * 1.5)
        ),
        2,
    )

    insights = []

    insights.append({
        "tipo": "resumen",
        "titulo": "Resumen del rendimiento",
        "descripcion": "Tu espacio ya tiene actividad registrada en MiPlaza.",
        "accion_recomendada": "Usá estas métricas para detectar qué contenido genera más interés.",
    })

    if metricas.total_historias == 0:
        insights.append({
            "tipo": "recomendacion",
            "titulo": "Todavía no estás usando historias",
            "descripcion": "Las historias ayudan a mantener visible tu espacio.",
            "accion_recomendada": "Publicá una historia mostrando productos, novedades o promociones.",
        })

    if metricas.total_historias > 0 and promedio_vistas_por_historia >= 3:
        insights.append({
            "tipo": "positivo",
            "titulo": "Tus historias están generando vistas",
            "descripcion": "Las personas están mirando el contenido temporal de tu espacio.",
            "accion_recomendada": "Usá historias para mostrar novedades rápidas y llamados a la acción.",
        })

    if metricas.total_publicaciones == 0:
        insights.append({
            "tipo": "recomendacion",
            "titulo": "Tu espacio todavía no tiene publicaciones",
            "descripcion": "Las publicaciones son la base visible de tu perfil.",
            "accion_recomendada": "Creá una primera publicación clara con imagen, descripción y propuesta.",
        })

    if metricas.total_publicaciones > 0 and promedio_guardados_por_publicacion > promedio_likes_por_publicacion:
        insights.append({
            "tipo": "positivo",
            "titulo": "Tus publicaciones parecen útiles",
            "descripcion": "Tenés más guardados que likes, señal de contenido que la gente quiere volver a ver.",
            "accion_recomendada": "Repetí formatos informativos, promociones o catálogos simples.",
        })

    if metricas.total_publicaciones > 0 and total_interacciones_publicaciones == 0:
        insights.append({
            "tipo": "alerta",
            "titulo": "Tus publicaciones todavía no generan interacción",
            "descripcion": "Hay publicaciones visibles, pero sin likes ni guardados.",
            "accion_recomendada": "Probá mejorar imagen, descripción y llamado a la acción.",
        })

    if metricas.total_seguidores == 0:
        insights.append({
            "tipo": "recomendacion",
            "titulo": "Todavía no tenés seguidores",
            "descripcion": "Los seguidores ayudan a construir una audiencia recurrente.",
            "accion_recomendada": "Compartí tu perfil y mantené actividad con historias y publicaciones.",
        })

    return {
        "comercio_id": comercio_id,
        "metricas": {
            "total_seguidores": metricas.total_seguidores,
            "total_publicaciones": metricas.total_publicaciones,
            "total_likes_publicaciones": metricas.total_likes_publicaciones,
            "total_guardados_publicaciones": metricas.total_guardados_publicaciones,
            "total_historias": metricas.total_historias,
            "total_vistas_historias": metricas.total_vistas_historias,
            "total_likes_historias": metricas.total_likes_historias,
        },
        "metricas_derivadas": {
            "engagement_publicaciones": engagement_publicaciones,
            "promedio_likes_por_publicacion": promedio_likes_por_publicacion,
            "promedio_guardados_por_publicacion": promedio_guardados_por_publicacion,
            "promedio_vistas_por_historia": promedio_vistas_por_historia,
            "promedio_likes_por_historia": promedio_likes_por_historia,
        },

        "score": {
            "space_score": space_score,
            "nivel": (
                "alto"
                if space_score >= 250
                else "medio"
                if space_score >= 100
                else "inicial"
            ),
        },

        "comparacion": comparacion,
        "insights": insights,
    }
