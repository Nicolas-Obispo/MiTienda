"""
search_event_services.py
------------------------
Registro best-effort de eventos de busqueda.
"""

from typing import Any

from sqlalchemy.orm import Session, sessionmaker

from app.modules.search.models.search_event_models import SearchEvent


_MAX_IDS = 20


def _normalizar_query(query: str | None) -> str:
    if not query:
        return ""
    return query.strip().lower()


def _limitar_ids(ids: list[int] | set[int] | tuple[int, ...] | None) -> list[int]:
    resultado: list[int] = []
    vistos: set[int] = set()

    for item in ids or []:
        try:
            item_id = int(item)
        except (TypeError, ValueError):
            continue

        if item_id in vistos:
            continue

        resultado.append(item_id)
        vistos.add(item_id)

        if len(resultado) >= _MAX_IDS:
            break

    return resultado


def _metadata_simple(metadata: dict[str, Any] | None) -> dict[str, Any]:
    resultado: dict[str, Any] = {}

    for key, value in (metadata or {}).items():
        if isinstance(value, (str, int, float, bool)) or value is None:
            resultado[key] = value
        elif isinstance(value, list):
            resultado[key] = [
                item
                for item in value[:_MAX_IDS]
                if isinstance(item, (str, int, float, bool)) or item is None
            ]

    return resultado


def _modo_busqueda(
    *,
    smart: bool,
    smart_semantic: bool,
    query_normalizada: str,
) -> str:
    if smart_semantic and query_normalizada:
        return "smart_semantic"
    if smart and query_normalizada:
        return "smart"
    return "classic"


def build_search_event_from_comercios_activos(
    *,
    query_original: str | None,
    smart: bool,
    smart_semantic: bool,
    limit: int,
    offset: int,
    radio_km: float | None,
    has_location: bool,
    result_count: int,
    taxonomy_node_ids: list[int] | set[int] | tuple[int, ...] | None = None,
    rubro_ids: list[int] | set[int] | tuple[int, ...] | None = None,
    comercio_result_ids: list[int] | set[int] | tuple[int, ...] | None = None,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    query_normalizada = _normalizar_query(query_original)

    return {
        "endpoint": "/comercios/activos",
        "query_original": query_original or "",
        "query_normalizada": query_normalizada,
        "modo_busqueda": _modo_busqueda(
            smart=smart,
            smart_semantic=smart_semantic,
            query_normalizada=query_normalizada,
        ),
        "smart": bool(smart),
        "smart_semantic": bool(smart_semantic),
        "limit": int(limit),
        "offset": int(offset),
        "radio_km": radio_km,
        "has_location": bool(has_location),
        "result_count": int(result_count),
        "no_results": int(result_count) == 0,
        "taxonomy_node_ids_json": _limitar_ids(taxonomy_node_ids),
        "rubro_ids_json": _limitar_ids(rubro_ids),
        "comercio_result_ids_json": _limitar_ids(comercio_result_ids),
        "metadata_json": _metadata_simple(metadata),
    }


def registrar_search_event_best_effort(
    db: Session,
    payload: dict[str, Any],
) -> None:
    try:
        bind = db.get_bind()
        SearchEventSession = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=bind,
        )
        event_db = SearchEventSession()
        try:
            event_db.add(SearchEvent(**payload))
            event_db.commit()
        except Exception:
            event_db.rollback()
        finally:
            event_db.close()
    except Exception:
        return
