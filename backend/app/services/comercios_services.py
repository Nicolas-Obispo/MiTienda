"""
comercios_services.py
--------------------
Lógica de negocio para Comercios (MiPlaza).

Este módulo:
- NO maneja HTTP
- NO maneja JWT
- NO accede a headers
- SOLO lógica de negocio

ETAPA 50 (IA v1 - MVP):
- Se agrega modo "smart" para /comercios/activos:
  - smart=False: mantiene el orden inteligente existente (historias/publicaciones)
  - smart=True: aplica ranking keyword (score) SIN IA externa, y pagina sobre ese ranking
"""

from __future__ import annotations

import json
import math

from sqlalchemy import case, or_
from sqlalchemy.orm import Session

from app.models.comercios_embeddings_models import ComercioEmbedding

from app.models.comercios_models import Comercio
from app.models.historias_models import Historia
from app.models.publicaciones_models import Publicacion
from app.models.usuarios_models import Usuario
from app.schemas.comercios_schemas import ComercioCreate, ComercioUpdate
from app.services.comercios_embeddings_services import upsert_embedding_comercio


# ============================================================
# Helpers internos (ETAPA 50 - ranking keyword)
# ============================================================

def _normalizar_texto(valor: str | None) -> str:
    """
    Normaliza texto para comparación.
    MVP: lower + strip. (Sin remover tildes para no meter dependencias)
    """
    if not valor:
        return ""
    return valor.strip().lower()


def _tokenizar(texto: str) -> list[str]:
    """
    Tokenización simple (MVP).
    - Split por espacios
    - Filtra tokens vacíos
    """
    if not texto:
        return []
    return [t for t in texto.split(" ") if t]


def _calcular_score_comercio(
    comercio: Comercio,
    query_normalizada: str,
    tokens: list[str],
    tiene_historias: bool,
    tiene_publicaciones: bool,
) -> int:
    """
    Calcula score ponderado (MVP) SIN IA externa.

    Fuentes:
    - nombre
    - descripcion
    - rubro (si existe relación comercio.rubro.nombre)
    - ciudad / provincia

    Bonus:
    - señales reales (historias/publicaciones) como pequeño impulso,
      manteniendo consistencia con el "orden inteligente" previo.
    """
    score = 0

    nombre = _normalizar_texto(getattr(comercio, "nombre", None))
    descripcion = _normalizar_texto(getattr(comercio, "descripcion", None))
    ciudad = _normalizar_texto(getattr(comercio, "ciudad", None))
    provincia = _normalizar_texto(getattr(comercio, "provincia", None))

    # Rubro (opcional). Si no existe relación, no rompe.
    rubro_nombre = ""
    rubro_obj = getattr(comercio, "rubro", None)
    if rubro_obj is not None:
        rubro_nombre = _normalizar_texto(getattr(rubro_obj, "nombre", None))

    # ---------------------------
    # Query completa (match fuerte)
    # ---------------------------
    if query_normalizada and query_normalizada in nombre:
        score += 100

    if query_normalizada and query_normalizada in descripcion:
        score += 40

    # ---------------------------
    # Tokens (match por palabra)
    # ---------------------------
    for t in tokens:
        # nombre: alto
        if t in nombre:
            score += 20

        # descripcion: medio/bajo
        if t in descripcion:
            score += 8

        # rubro: medio
        if t in rubro_nombre:
            score += 15

        # ubicación: bajo
        if t in ciudad:
            score += 5
        if t in provincia:
            score += 5

    # ---------------------------
    # Bonus por señales reales
    # ---------------------------
    if tiene_historias:
        score += 12  # pequeño boost
    if tiene_publicaciones:
        score += 6   # pequeño boost

    return score

# ============================================================
# Helpers internos (ETAPA 51 - similitud embeddings)
# ============================================================

def _cosine_similarity(a: list[float], b: list[float]) -> float:
    """
    Similaridad coseno entre dos vectores.

    - Devuelve valor en [-1..1]
    - Si algún vector es nulo/degenerado, devuelve -1 para mandarlo al final
    """
    if not a or not b:
        return -1.0

    if len(a) != len(b):
        return -1.0

    dot = 0.0
    na = 0.0
    nb = 0.0

    for i in range(len(a)):
        dot += a[i] * b[i]
        na += a[i] * a[i]
        nb += b[i] * b[i]

    if na <= 0.0 or nb <= 0.0:
        return -1.0

    return dot / (math.sqrt(na) * math.sqrt(nb))

# ============================================================
# Crear comercio
# ============================================================

def crear_comercio(
    db: Session,
    usuario: Usuario,
    data: ComercioCreate
) -> Comercio:
    """
    Crea un comercio asociado al usuario autenticado.

    Reglas:
    - El usuario debe estar en modo 'publicador'
    """

    if usuario.modo_activo != "publicador":
        raise ValueError("El usuario no está en modo publicador")

    comercio = Comercio(
        usuario_id=usuario.id,
        nombre=data.nombre,
        descripcion=data.descripcion,
        portada_url=str(data.portada_url),
        rubro_id=data.rubro_id,
        provincia=data.provincia,
        ciudad=data.ciudad,
        direccion=data.direccion,
        whatsapp=data.whatsapp,
        instagram=data.instagram,
        maps_url=str(data.maps_url) if data.maps_url else None,
    )

    db.add(comercio)
    db.commit()
    db.refresh(comercio)
    upsert_embedding_comercio(db=db, comercio=comercio)

    return comercio


# ============================================================
# Obtener comercio por ID
# ============================================================

def obtener_comercio_por_id(
    db: Session,
    comercio_id: int
) -> Comercio | None:
    return (
        db.query(Comercio)
        .filter(Comercio.id == comercio_id, Comercio.activo == True)
        .first()
    )


# ============================================================
# Listar comercios activos (existente: con filtros ciudad/rubro)
# ============================================================

def listar_comercios(
    db: Session,
    ciudad: str | None = None,
    rubro_id: int | None = None
) -> list[Comercio]:
    query = db.query(Comercio).filter(Comercio.activo == True)

    if ciudad:
        query = query.filter(Comercio.ciudad == ciudad)

    if rubro_id:
        query = query.filter(Comercio.rubro_id == rubro_id)

    return query.all()


# ============================================================
# Listar comercios activos (ETAPA 48: Explorar) + ETAPA 49 + ETAPA 50 (smart)
# ============================================================

    # ============================================================
    # SEMANTIC MODE (ETAPA 51) - embeddings
    # ============================================================
    # Si smart_semantic=True pero no hay query real, no tiene sentido rankear por embeddings.
    # En ese caso, volvemos al modo clásico para mantener UX estable.
    if smart_semantic and q_normalizada:
        # Import local para evitar acoplar imports globales si mañana cambiamos providers
        from app.ai.embedding_factory import get_embedding_provider

        provider = get_embedding_provider()

        # Embedding de la query
        query_texto = _normalizar_texto(q_normalizada)
        query_vector = provider.embed_text(query_texto)

        # Ventana de candidatos (MVP): trae recientes y rankea por similitud
        fetch_size = (offset + limit) * 5
        if fetch_size < 50:
            fetch_size = 50
        if fetch_size > 500:
            fetch_size = 500

        candidatos: list[Comercio] = (
            query
            .order_by(Comercio.id.desc())
            .limit(fetch_size)
            .all()
        )

        if not candidatos:
            return []

        comercio_ids = [c.id for c in candidatos]

        # Traemos embeddings en batch (1 query)
        rows = (
            db.query(ComercioEmbedding.comercio_id, ComercioEmbedding.vector)
            .filter(ComercioEmbedding.comercio_id.in_(comercio_ids))
            .all()
        )

        embeddings_map: dict[int, list[float]] = {}
        for comercio_id, vector_str in rows:
            try:
                embeddings_map[comercio_id] = json.loads(vector_str)
            except Exception:
                # Si hay vector corrupto, lo ignoramos (queda al final)
                continue

        # Scoring por similitud coseno
        scored: list[tuple[float, int, Comercio]] = []
        for c in candidatos:
            vec = embeddings_map.get(c.id)
            sim = _cosine_similarity(query_vector, vec) if vec else -1.0
            scored.append((sim, c.id, c))

        # Orden: similitud DESC, id DESC
        scored.sort(key=lambda x: (x[0], x[1]), reverse=True)

        # Paginado sobre ranking final
        pagina = scored[offset: offset + limit]
        return [item[2] for item in pagina]

def listar_comercios_activos(
    db: Session,
    q: str | None = None,
    smart: bool = False,
    smart_semantic: bool = False,
    limit: int = 20,
    offset: int = 0,
) -> list[Comercio]:
    """
    Lista comercios activos para pantalla Explorar.

    Reglas base:
    - Solo activo=True
    - Soporta q (búsqueda)
    - Soporta paginado (limit/offset)

    Modo clásico (smart=False) - mantiene ETAPA 49:
        1) Comercios con historias primero
        2) Luego comercios con publicaciones
        3) Luego el resto
        4) Dentro de cada grupo: más nuevos primero (id desc)

    Modo smart (smart=True) - ETAPA 50 (IA v1 keyword):
        - Aplica ranking por score usando:
          nombre + descripcion + rubro (si existe) + ciudad/provincia
        - Bonus pequeño por señales reales (historias/publicaciones)
        - Orden final: score DESC, luego id DESC
        - Paginado se aplica sobre el ranking calculado (no sobre SQL directo)

    Nota MVP:
    - "Con historias" = existe al menos 1 historia del comercio.
    - "Con publicaciones" = existe al menos 1 publicación del comercio.
    """

    query = db.query(Comercio).filter(Comercio.activo == True)

    # Normalizamos q (si viene vacía, tratamos como None)
    q_normalizada = ""
    if q:
        q_normalizada = q.strip()
    if not q_normalizada:
        q_normalizada = ""

    # ============================================================
    # SMART MODE (ETAPA 50)
    # ============================================================
    # Si smart=True pero no hay query real, no tiene sentido rankear por keywords.
    # En ese caso, volvemos al modo clásico para mantener UX estable.
    if smart and q_normalizada:
        query_n = _normalizar_texto(q_normalizada)
        tokens = _tokenizar(query_n)

        # Filtro de candidatos (MVP) para no traernos TODO:
        # - buscamos por varios campos, sin depender solo del nombre
        # - es case-insensitive con ilike
        # (Esto NO existe en modo clásico; solo afecta cuando smart=True)
        like = f"%{q_normalizada}%"
        query = query.filter(
            or_(
                Comercio.nombre.ilike(like),
                Comercio.descripcion.ilike(like),
                Comercio.ciudad.ilike(like),
                Comercio.provincia.ilike(like),
            )
        )

        # Ventana de búsqueda para rankear en Python.
        # Traemos más que "limit" para poder reordenar por score.
        # Cap para evitar explosión.
        fetch_size = (offset + limit) * 5
        if fetch_size < 50:
            fetch_size = 50
        if fetch_size > 500:
            fetch_size = 500

        candidatos: list[Comercio] = (
            query
            .order_by(Comercio.id.desc())  # base estable antes de rankear
            .limit(fetch_size)
            .all()
        )

        if not candidatos:
            return []

        # Precomputamos señales (historias/publicaciones) en batch para esta ventana
        comercio_ids = [c.id for c in candidatos]

        comercios_con_historias = set(
            row[0] for row in (
                db.query(Historia.comercio_id)
                .filter(Historia.comercio_id.in_(comercio_ids))
                .distinct()
                .all()
            )
        )

        comercios_con_publicaciones = set(
            row[0] for row in (
                db.query(Publicacion.comercio_id)
                .filter(Publicacion.comercio_id.in_(comercio_ids))
                .distinct()
                .all()
            )
        )

        # Calculamos score y ordenamos
        scored: list[tuple[int, int, Comercio]] = []
        for c in candidatos:
            score = _calcular_score_comercio(
                comercio=c,
                query_normalizada=query_n,
                tokens=tokens,
                tiene_historias=(c.id in comercios_con_historias),
                tiene_publicaciones=(c.id in comercios_con_publicaciones),
            )
            scored.append((score, c.id, c))

        # Orden: score DESC, id DESC
        scored.sort(key=lambda x: (x[0], x[1]), reverse=True)

        # Paginado sobre ranking final
        pagina = scored[offset: offset + limit]

        # Devolvemos solo comercios
        return [item[2] for item in pagina]

    # ============================================================
    # CLÁSICO (ETAPA 48/49) - comportamiento existente
    # ============================================================

    # Búsqueda MVP: por nombre (como estaba)
    if q_normalizada:
        query = query.filter(Comercio.nombre.ilike(f"%{q_normalizada}%"))

    # Flags de actividad (EXISTS correlacionado)
    tiene_historias = (
        db.query(Historia.id)
        .filter(Historia.comercio_id == Comercio.id)
        .exists()
    )

    tiene_publicaciones = (
        db.query(Publicacion.id)
        .filter(Publicacion.comercio_id == Comercio.id)
        .exists()
    )

    # Normalizamos a 1/0 para ordenar
    score_historias = case((tiene_historias, 1), else_=0)
    score_publicaciones = case((tiene_publicaciones, 1), else_=0)

    # Orden inteligente (ETAPA 49)
    query = query.order_by(
        score_historias.desc(),
        score_publicaciones.desc(),
        Comercio.id.desc(),
    )

    # Paginado
    query = query.offset(offset).limit(limit)

    return query.all()


# ============================================================
# Actualizar comercio
# ============================================================

def actualizar_comercio(
    db: Session,
    usuario: Usuario,
    comercio: Comercio,
    data: ComercioUpdate
) -> Comercio:
    """
    Actualiza un comercio.

    Reglas:
    - Solo el dueño puede modificarlo
    """

    if comercio.usuario_id != usuario.id:
        raise PermissionError("No tenés permiso para modificar este comercio")

    for campo, valor in data.dict(exclude_unset=True).items():
        setattr(comercio, campo, valor)

    db.commit()
    db.refresh(comercio)
    upsert_embedding_comercio(db=db, comercio=comercio)

    return comercio


# ============================================================
# Desactivar comercio (soft delete)
# ============================================================

def desactivar_comercio(
    db: Session,
    usuario: Usuario,
    comercio: Comercio
) -> Comercio:
    """
    Desactiva un comercio sin borrarlo físicamente.
    """

    if comercio.usuario_id != usuario.id:
        raise PermissionError("No tenés permiso para desactivar este comercio")

    comercio.activo = False

    db.commit()
    db.refresh(comercio)

    return comercio