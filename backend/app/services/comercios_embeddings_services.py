"""
comercios_embeddings_services.py
-------------------------------
Dominio: embeddings asociados a Comercios (IA v2).

Este service:
- NO maneja HTTP
- NO maneja JWT
- SOLO lógica de negocio relacionada a embeddings de comercio

Importante (arquitectura):
- Usa la capa técnica reusable app/ai (EmbeddingProvider + factory)
- Persiste en BD en tabla comercios_embeddings
- No acopla el motor IA al dominio (provider intercambiable)
"""

from __future__ import annotations

import json
from typing import List

from sqlalchemy.orm import Session

from app.ai.embedding_factory import get_embedding_provider
from app.models.comercios_models import Comercio
from app.models.comercios_embeddings_models import ComercioEmbedding


# ============================================================
# Helpers internos
# ============================================================

def _build_texto_comercio(comercio: Comercio) -> str:
    """
    Construye un texto representativo del comercio para embeddings.

    Reglas:
    - No depende del motor IA (solo arma texto)
    - Mantener estructura estable para evitar cambios bruscos en embeddings
    - Usar etiquetas semánticas simples para dar más contexto al modelo
    """
    partes: List[str] = []

    nombre = str(getattr(comercio, "nombre", "") or "").strip()
    descripcion = str(getattr(comercio, "descripcion", "") or "").strip()
    ciudad = str(getattr(comercio, "ciudad", "") or "").strip()
    provincia = str(getattr(comercio, "provincia", "") or "").strip()
    direccion = str(getattr(comercio, "direccion", "") or "").strip()

    rubro_nombre = ""
    rubro_obj = getattr(comercio, "rubro", None)
    if rubro_obj is not None and getattr(rubro_obj, "nombre", None):
        rubro_nombre = str(rubro_obj.nombre).strip()

    # ---------------------------
    # Identidad principal
    # ---------------------------
    if nombre:
        partes.append(f"nombre del comercio: {nombre}")

    if rubro_nombre:
        partes.append(f"rubro del comercio: {rubro_nombre}")

    if descripcion:
        partes.append(f"descripción del comercio: {descripcion}")

    # ---------------------------
    # Ubicación
    # ---------------------------
    if ciudad:
        partes.append(f"ciudad: {ciudad}")

    if provincia:
        partes.append(f"provincia: {provincia}")

    if direccion:
        partes.append(f"dirección: {direccion}")

    # ---------------------------
    # Texto resumen adicional
    # ---------------------------
    resumen_partes: List[str] = []

    if nombre:
        resumen_partes.append(nombre)

    if rubro_nombre:
        resumen_partes.append(f"es un comercio del rubro {rubro_nombre}")

    if descripcion:
        resumen_partes.append(descripcion)

    if ciudad and provincia:
        resumen_partes.append(f"ubicado en {ciudad}, {provincia}")
    elif ciudad:
        resumen_partes.append(f"ubicado en {ciudad}")
    elif provincia:
        resumen_partes.append(f"ubicado en {provincia}")

    if direccion:
        resumen_partes.append(f"dirección {direccion}")

    if resumen_partes:
        partes.append("resumen: " + ". ".join(resumen_partes))

    # Unificamos en un solo texto estable
    return " | ".join([p for p in partes if p])


def _serializar_vector(vector: List[float]) -> str:
    """
    Serializa vector para guardarlo en TEXT.

    Elegimos JSON para:
    - ser legible
    - portable
    - compatible con cualquier provider
    """
    return json.dumps(vector)


def _deserializar_vector(vector_str: str) -> List[float]:
    """
    Deserializa vector desde TEXT (JSON).
    """
    return json.loads(vector_str)


# ============================================================
# API de dominio
# ============================================================

def upsert_embedding_comercio(
    db: Session,
    comercio: Comercio,
    model_version: int = 1,
) -> ComercioEmbedding:
    """
    Crea o actualiza el embedding asociado al comercio.

    - Usa el provider configurado (settings.EMBEDDINGS_PROVIDER)
    - Persiste en BD (tabla comercios_embeddings)
    """

    provider = get_embedding_provider()

    texto = _build_texto_comercio(comercio)
    vector = provider.embed_text(texto)
    vector_str = _serializar_vector(vector)

    existente = (
        db.query(ComercioEmbedding)
        .filter(ComercioEmbedding.comercio_id == comercio.id)
        .first()
    )

    if existente:
        existente.vector = vector_str
        existente.model_version = model_version
        db.commit()
        db.refresh(existente)
        return existente

    nuevo = ComercioEmbedding(
        comercio_id=comercio.id,
        vector=vector_str,
        model_version=model_version,
    )
    db.add(nuevo)
    db.commit()
    db.refresh(nuevo)
    return nuevo


def obtener_embedding_comercio(
    db: Session,
    comercio_id: int,
) -> ComercioEmbedding | None:
    """
    Devuelve el embedding persistido (si existe).
    """
    return (
        db.query(ComercioEmbedding)
        .filter(ComercioEmbedding.comercio_id == comercio_id)
        .first()
    )


def obtener_vector_embedding_comercio(
    db: Session,
    comercio_id: int,
) -> List[float] | None:
    """
    Devuelve el vector (deserializado) para cálculos de similitud.
    """
    emb = obtener_embedding_comercio(db=db, comercio_id=comercio_id)
    if not emb:
        return None
    return _deserializar_vector(emb.vector)