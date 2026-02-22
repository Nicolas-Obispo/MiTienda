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

    Regla:
    - No depende del motor IA (solo arma texto)
    - Mantener estable para evitar cambios bruscos en embeddings
    """
    partes: List[str] = []

    # Datos principales
    if getattr(comercio, "nombre", None):
        partes.append(str(comercio.nombre))
    if getattr(comercio, "descripcion", None):
        partes.append(str(comercio.descripcion))

    # Ubicación
    if getattr(comercio, "ciudad", None):
        partes.append(str(comercio.ciudad))
    if getattr(comercio, "provincia", None):
        partes.append(str(comercio.provincia))

    # Rubro (si existe relación)
    rubro_obj = getattr(comercio, "rubro", None)
    if rubro_obj is not None and getattr(rubro_obj, "nombre", None):
        partes.append(str(rubro_obj.nombre))

    # Unificamos en un solo texto
    return " | ".join([p.strip() for p in partes if p and p.strip()])


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