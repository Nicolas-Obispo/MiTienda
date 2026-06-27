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

ETAPA 53.1:
- Se mejora smart_semantic=True para que rankee sobre un pool amplio de comercios activos
  sin depender del filtro previo por nombre.
"""

from __future__ import annotations

import json
import math

from sqlalchemy import case, or_
from sqlalchemy.orm import Session, selectinload

from app.modules.ai.models.comercios_embeddings_models import ComercioEmbedding
from app.modules.discovery.services.taxonomy_assignment_services import (
    sincronizar_assignments_comercio_desde_rubros,
)
from app.modules.spaces.models.comercios_models import Comercio
from app.modules.stories.models.historias_models import Historia
from app.modules.posts.models.publicaciones_models import Publicacion
from app.modules.users.models.usuarios_models import Usuario
from app.modules.spaces.schemas.comercios_schemas import ComercioCreate, ComercioUpdate
from app.modules.ai.services.comercios_embeddings_services import upsert_embedding_comercio
from app.modules.products.services.rubros_services import obtener_rubro_por_id


class RubroInvalidoError(ValueError):
    pass


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


_INTENCIONES_BUSQUEDA_V2 = {
    "pizza": [
        "pizza",
        "pizzeria",
        "pizzería",
        "comida",
        "gastronomia",
        "gastronomía",
        "restaurante",
        "delivery",
        "cena",
        "kiosco",
    ],
    "hamburguesa": [
        "hamburguesa",
        "comida",
        "gastronomia",
        "gastronomía",
        "restaurante",
        "fast food",
        "cena",
    ],
    "ropa": [
        "ropa",
        "indumentaria",
        "moda",
        "boutique",
        "calzado",
        "tienda de ropa",
    ],
    "zapatos": [
        "zapatos",
        "zapato",
        "zapatillas",
        "zapatilla",
        "calzado",
        "zapateria",
        "zapatería",
        "tienda de ropa",
        "deportes",
    ],
    "zapatillas": [
        "zapatillas",
        "zapatilla",
        "zapatos",
        "calzado",
        "zapateria",
        "zapatería",
        "deportes",
    ],
    "calzado": [
        "calzado",
        "zapatos",
        "zapatillas",
        "zapateria",
        "zapatería",
        "tienda de ropa",
        "deportes",
    ],
    "deportes": [
        "deportes",
        "deportivo",
        "deportiva",
        "deportivas",
        "zapatillas deportivas",
    ],
    "deportivo": [
        "deportes",
        "deportivo",
        "deportiva",
        "deportivas",
        "zapatillas deportivas",
    ],
    "revestimientos": [
        "revestimientos",
        "revestimiento",
        "construccion",
        "construcción",
        "obra",
        "materiales",
        "hogar y construccion",
        "hogar y construcción",
        "servicios de construccion",
        "servicios de construcción",
    ],
    "construccion": [
        "construccion",
        "construcción",
        "obra",
        "materiales",
        "revestimientos",
        "hogar y construccion",
        "hogar y construcción",
        "servicios de construccion",
        "servicios de construcción",
    ],
    "construcción": [
        "construccion",
        "construcción",
        "obra",
        "materiales",
        "revestimientos",
        "hogar y construccion",
        "hogar y construcción",
        "servicios de construccion",
        "servicios de construcción",
    ],
    "obra": [
        "obra",
        "construccion",
        "construcción",
        "materiales",
        "revestimientos",
        "servicios de construccion",
        "servicios de construcción",
    ],
    "materiales": [
        "materiales",
        "construccion",
        "construcción",
        "obra",
        "revestimientos",
        "servicios de construccion",
        "servicios de construcción",
    ],
    "cafe": [
        "cafe",
        "café",
        "cafeteria",
        "cafetería",
        "desayuno",
        "merienda",
        "gastronomia",
        "gastronomía",
    ],
    "café": [
        "cafe",
        "café",
        "cafeteria",
        "cafetería",
        "desayuno",
        "merienda",
        "gastronomia",
        "gastronomía",
    ],
    "cerveza": [
        "cerveza",
        "bar",
        "bebida",
        "salida",
        "gastronomia",
        "gastronomía",
    ],
    "helado": [
        "helado",
        "heladeria",
        "heladería",
        "postre",
        "gastronomia",
        "gastronomía",
    ],
}


_INTENCION_A_FAMILIA_V2 = {
    "pizza": "gastronomia",
    "hamburguesa": "gastronomia",
    "cafe": "gastronomia",
    "café": "gastronomia",
    "cerveza": "gastronomia",
    "helado": "gastronomia",
    "ropa": "moda",
    "zapatos": "moda_calzado",
    "zapatillas": "moda_calzado",
    "calzado": "moda_calzado",
    "deportes": "deportes",
    "deportivo": "deportes",
    "revestimientos": "construccion",
    "construccion": "construccion",
    "construcción": "construccion",
    "obra": "construccion",
    "materiales": "construccion",
}


_FAMILIAS_INTENCION_V2 = {
    "gastronomia": [
        "gastronomia",
        "gastronomía",
        "kiosco",
        "comida",
        "bebida",
        "bar",
        "restaurante",
        "pizzeria",
        "pizzería",
        "cafeteria",
        "cafetería",
        "heladeria",
        "heladería",
    ],
    "moda": [
        "ropa",
        "tienda de ropa",
        "indumentaria",
        "moda",
        "boutique",
        "calzado",
        "zapateria",
        "zapatería",
    ],
    "moda_calzado": [
        "ropa",
        "tienda de ropa",
        "indumentaria",
        "moda",
        "boutique",
        "calzado",
        "zapatos",
        "zapato",
        "zapatillas",
        "zapatilla",
        "zapateria",
        "zapatería",
        "deportes",
    ],
    "deportes": [
        "deportes",
        "deportivo",
        "deportiva",
        "deportivas",
        "zapatillas deportivas",
    ],
    "construccion": [
        "construccion",
        "construcción",
        "hogar y construccion",
        "hogar y construcción",
        "servicios de construccion",
        "servicios de construcción",
        "revestimientos",
        "revestimiento",
        "obra",
        "materiales",
    ],
}


def _normalizar_lista_terminos(terminos: list[str]) -> list[str]:
    resultado: list[str] = []
    vistos: set[str] = set()

    for termino in terminos:
        termino_normalizado = _normalizar_texto(termino)

        if termino_normalizado and termino_normalizado not in vistos:
            resultado.append(termino_normalizado)
            vistos.add(termino_normalizado)

    return resultado


def _obtener_familia_intencion(q: str) -> str | None:
    q_normalizada = _normalizar_texto(q)

    if not q_normalizada:
        return None

    if q_normalizada in _INTENCION_A_FAMILIA_V2:
        return _INTENCION_A_FAMILIA_V2[q_normalizada]

    for token in _tokenizar(q_normalizada):
        if token in _INTENCION_A_FAMILIA_V2:
            return _INTENCION_A_FAMILIA_V2[token]

    return None


def _terminos_familia_intencion(q: str) -> list[str]:
    familia = _obtener_familia_intencion(q)

    if not familia:
        return []

    return _normalizar_lista_terminos(_FAMILIAS_INTENCION_V2.get(familia, []))


def _expandir_intencion_busqueda(q: str) -> list[str]:
    """
    Expande consultas cortas a terminos de intencion controlados.

    La expansion vive en backend para mantener React como capa de UI/cache.
    Si no hay match, conserva la busqueda original.
    """
    q_normalizada = _normalizar_texto(q)

    if not q_normalizada:
        return []

    terminos: list[str] = [q_normalizada]

    for token in _tokenizar(q_normalizada):
        terminos.extend(_INTENCIONES_BUSQUEDA_V2.get(token, []))

    if q_normalizada in _INTENCIONES_BUSQUEDA_V2:
        terminos.extend(_INTENCIONES_BUSQUEDA_V2[q_normalizada])

    resultado = _normalizar_lista_terminos(terminos)
    return resultado or [q_normalizada]


def _tiene_intencion_conocida(q: str) -> bool:
    return _obtener_familia_intencion(q) is not None


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

def _calcular_distancia_km(
    lat_origen: float,
    lng_origen: float,
    lat_destino: float | None,
    lng_destino: float | None,
) -> float | None:
    if lat_destino is None or lng_destino is None:
        return None

    radio_tierra_km = 6371.0

    lat1 = math.radians(lat_origen)
    lng1 = math.radians(lng_origen)
    lat2 = math.radians(lat_destino)
    lng2 = math.radians(lng_destino)

    dlat = lat2 - lat1
    dlng = lng2 - lng1

    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(lat1) * math.cos(lat2) * math.sin(dlng / 2) ** 2
    )

    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    return round(radio_tierra_km * c, 2)

def _aplicar_distancia_y_radio(
    comercios: list[Comercio],
    lat: float | None,
    lng: float | None,
    radio_km: float | None = None,
) -> list[Comercio]:
    if lat is None or lng is None:
        return comercios

    resultado: list[Comercio] = []

    for comercio in comercios:
        distancia = _calcular_distancia_km(
            lat_origen=lat,
            lng_origen=lng,
            lat_destino=getattr(comercio, "latitud", None),
            lng_destino=getattr(comercio, "longitud", None),
        )

        comercio.distancia_km = distancia

        if distancia is None:
            resultado.append(comercio)
            continue

        if radio_km is not None and distancia > radio_km:
            continue

        resultado.append(comercio)

    return resultado


def _distancia_sort_value(comercio: Comercio) -> float:
    distancia = getattr(comercio, "distancia_km", None)

    if distancia is None:
        return 999999.0

    return distancia


def _validar_rubro_activo(db: Session, rubro_id: int) -> None:
    if not obtener_rubro_por_id(db, rubro_id):
        raise RubroInvalidoError("Rubro no encontrado o inactivo")


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

    _validar_rubro_activo(db, data.rubro_id)

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
    sincronizar_assignments_comercio_desde_rubros(
        db=db,
        comercio_id=comercio.id,
        rubro_id_principal=comercio.rubro_id,
        rubro_ids_secundarios=data.rubro_secundario_ids,
    )
    db.commit()
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
        .options(selectinload(Comercio.rubro))
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
    query = (
        db.query(Comercio)
        .options(selectinload(Comercio.rubro))
        .filter(Comercio.activo == True)
    )

    if ciudad:
        query = query.filter(Comercio.ciudad == ciudad)

    if rubro_id:
        query = query.filter(Comercio.rubro_id == rubro_id)

    return query.all()


# ============================================================
# Listar comercios activos (ETAPA 48: Explorar) + ETAPA 49 + ETAPA 50 (smart)
# + ETAPA 53.1 (smart_semantic sin filtro previo por nombre)
# ============================================================

def listar_comercios_activos(
    db: Session,
    q: str | None = None,
    smart: bool = False,
    smart_semantic: bool = False,
    lat: float | None = None,
    lng: float | None = None,
    radio_km: float | None = None,
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

    Modo smart_semantic (ETAPA 53.1):
        - Usa embeddings para rankear comercios activos
        - NO depende del filtro previo por nombre
        - Orden final: similitud DESC, luego id DESC
        - Paginado se aplica sobre el ranking calculado

    Nota MVP:
    - "Con historias" = existe al menos 1 historia del comercio.
    - "Con publicaciones" = existe al menos 1 publicación del comercio.
    """

    query = (
        db.query(Comercio)
        .options(selectinload(Comercio.rubro))
        .filter(Comercio.activo == True)
    )

    # Normalizamos q (si viene vacía, tratamos como cadena vacía)
    q_normalizada = ""
    if q:
        q_normalizada = q.strip()
    if not q_normalizada:
        q_normalizada = ""

    # ============================================================
    # SEMANTIC MODE (ETAPA 53.2 - primer híbrido)
    # ============================================================
    # Si smart_semantic=True pero no hay query real, no tiene sentido rankear por embeddings.
    # En ese caso, volvemos al modo clásico para mantener UX estable.
    if smart_semantic and q_normalizada:
        from app.modules.ai.core.embedding_factory import get_embedding_provider
        from app.modules.ai.services.rubros_embeddings_services import (
            detectar_rubros_por_query,
        )
        from app.modules.discovery.services.discovery_retrieval_services import (
            recuperar_nodos_discovery,
        )
        from app.modules.discovery.services.taxonomy_search_services import (
            buscar_rubro_ids_asignados_a_nodos_taxonomia,
        )
        from app.modules.discovery.models.taxonomy_models import TaxonomyAssignment

        provider = get_embedding_provider()

        # Embedding de la query enriquecida por intencion.
        query_texto = _normalizar_texto(q_normalizada)
        terminos_intencion = _expandir_intencion_busqueda(query_texto)
        tiene_intencion_conocida = _tiene_intencion_conocida(query_texto)
        terminos_filtro_intencion = _terminos_familia_intencion(query_texto)
        query_texto_embedding = " ".join(terminos_intencion)
        query_vector = provider.embed_text(query_texto_embedding)
        nodos_discovery = recuperar_nodos_discovery(
            db,
            query_texto,
            limit=10,
        )
        node_ids_discovery = [node.node_id for node in nodos_discovery]
        rubro_ids_discovery = buscar_rubro_ids_asignados_a_nodos_taxonomia(
            db,
            node_ids_discovery,
        )
        comercio_ids_discovery = set()
        if node_ids_discovery:
            comercio_ids_discovery = {
                comercio_id
                for (comercio_id,) in (
                    db.query(TaxonomyAssignment.entity_id)
                    .filter(TaxonomyAssignment.taxonomy_node_id.in_(node_ids_discovery))
                    .filter(TaxonomyAssignment.entity_type == "comercio")
                    .all()
                )
            }
        rubros_detectados = detectar_rubros_por_query(db, query_texto)
        rubro_ids_detectados = list(
            {
                *[rubro.rubro_id for rubro in rubros_detectados],
                *rubro_ids_discovery,
            }
        )

        # NO filtramos por nombre:
        # usamos un pool amplio de comercios activos y rankeamos por similitud.
        fetch_size = (offset + limit) * 5
        if fetch_size < 50:
            fetch_size = 50
        if fetch_size > 500:
            fetch_size = 500

        query_candidatos = query
        if rubro_ids_detectados or comercio_ids_discovery:
            query_candidatos = query_candidatos.filter(
                or_(
                    Comercio.rubro_id.in_(rubro_ids_detectados),
                    Comercio.id.in_(comercio_ids_discovery),
                )
            )

        candidatos: list[Comercio] = (
            query_candidatos
            .order_by(Comercio.id.desc())
            .limit(fetch_size)
            .all()
        )

        if (rubro_ids_detectados or comercio_ids_discovery) and not candidatos:
            candidatos = (
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

        # Señales reales en batch para este pool
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

        # Tokens de la query expandida para bonus simples.
        tokens = _tokenizar(query_texto_embedding)

        # Scoring híbrido inicial:
        # - similitud embeddings como base
        # - bonus textual por nombre/descripcion
        # - bonus pequeño por historias/publicaciones
        scored: list[tuple[float, int, Comercio]] = []
        for c in candidatos:
            vec = embeddings_map.get(c.id)
            sim = _cosine_similarity(query_vector, vec) if vec else -1.0

            nombre = _normalizar_texto(getattr(c, "nombre", None))
            descripcion = _normalizar_texto(getattr(c, "descripcion", None))
            rubro_nombre = ""
            rubro_obj = getattr(c, "rubro", None)
            if rubro_obj is not None:
                rubro_nombre = _normalizar_texto(
                    getattr(rubro_obj, "nombre", None)
                )

            texto_relevancia = " ".join(
                parte for parte in [nombre, descripcion, rubro_nombre] if parte
            )

            if (
                tiene_intencion_conocida
                and terminos_filtro_intencion
                and not any(
                    termino in texto_relevancia
                    for termino in terminos_filtro_intencion
                )
            ):
                continue

            bonus_textual = 0.0

            # Match fuerte de query original.
            if query_texto and query_texto in nombre:
                bonus_textual += 0.35
            if query_texto and query_texto in descripcion:
                bonus_textual += 0.20
            if query_texto and query_texto in rubro_nombre:
                bonus_textual += 0.25

            # Match por intencion expandida, incluyendo rubro.
            for termino in terminos_intencion:
                if termino == query_texto:
                    continue

                if termino in nombre:
                    bonus_textual += 0.18
                if termino in descripcion:
                    bonus_textual += 0.10
                if termino in rubro_nombre:
                    bonus_textual += 0.16

            # Match por tokens
            for t in tokens:
                if t in nombre:
                    bonus_textual += 0.08
                if t in descripcion:
                    bonus_textual += 0.04
                if t in rubro_nombre:
                    bonus_textual += 0.06

            bonus_senales = 0.0
            if c.id in comercios_con_historias:
                bonus_senales += 0.03
            if c.id in comercios_con_publicaciones:
                bonus_senales += 0.02

            score_total = sim + bonus_textual + bonus_senales
            scored.append((score_total, c.id, c))

        comercios_rankeados = [item[2] for item in scored]

        comercios_rankeados = _aplicar_distancia_y_radio(
            comercios=comercios_rankeados,
            lat=lat,
            lng=lng,
            radio_km=radio_km,
        )

        # Orden: score_total DESC, distancia ASC, id DESC
        score_por_id = {item[2].id: item[0] for item in scored}
        comercios_rankeados.sort(
            key=lambda c: (
                score_por_id.get(c.id, -999999.0),
                -_distancia_sort_value(c),
                c.id,
            ),
            reverse=True,
        )

        # Paginado sobre ranking final
        pagina = comercios_rankeados[offset: offset + limit]
        return pagina

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

        comercios_rankeados = [item[2] for item in scored]

        comercios_rankeados = _aplicar_distancia_y_radio(
            comercios=comercios_rankeados,
            lat=lat,
            lng=lng,
            radio_km=radio_km,
        )

        # Orden: score DESC, distancia ASC, id DESC
        score_por_id = {item[2].id: item[0] for item in scored}

        comercios_rankeados.sort(
            key=lambda c: (
                score_por_id.get(c.id, -999999),
                -_distancia_sort_value(c),
                c.id,
            ),
            reverse=True,
        )

        # Paginado sobre ranking final
        pagina = comercios_rankeados[offset: offset + limit]

        return pagina

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

    comercios = query.all()

    comercios = _aplicar_distancia_y_radio(
        comercios=comercios,
        lat=lat,
        lng=lng,
        radio_km=radio_km,
    )

    if lat is not None and lng is not None:
        comercios.sort(
            key=lambda c: (
                _distancia_sort_value(c),
                -c.id,
            )
        )

    return comercios


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

    payload = data.dict(exclude_unset=True)
    sincronizar_assignments = (
        "rubro_id" in payload or "rubro_secundario_ids" in payload
    )
    rubro_secundario_ids = payload.get("rubro_secundario_ids")

    for campo, valor in payload.items():
        if campo == "rubro_secundario_ids":
            continue

        if campo == "rubro_id":
            _validar_rubro_activo(db, valor)

        setattr(comercio, campo, valor)

    db.commit()
    db.refresh(comercio)
    if sincronizar_assignments:
        sincronizar_assignments_comercio_desde_rubros(
            db=db,
            comercio_id=comercio.id,
            rubro_id_principal=comercio.rubro_id,
            rubro_ids_secundarios=rubro_secundario_ids,
        )
        db.commit()
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
