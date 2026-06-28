"""
search_event_analytics_services.py
----------------------------------
Servicios read-only para analizar SearchEvent.
"""

from datetime import datetime

from sqlalchemy import case, func
from sqlalchemy.orm import Session

from app.modules.knowledge.analytics.schemas.search_event_analytics_schemas import (
    DiscoveryFailureItem,
    QueryAnalyticsItem,
    QueryNoResultsItem,
    QuerySummary,
)
from app.modules.search.models.search_event_models import SearchEvent


def _limit_normalizado(limit: int) -> int:
    return max(1, min(int(limit), 200))


def _query_base(db: Session, since: datetime | None = None):
    query = db.query(SearchEvent).filter(SearchEvent.query_normalizada != "")
    if since is not None:
        query = query.filter(SearchEvent.created_at >= since)
    return query


def top_queries(
    db: Session,
    since: datetime | None = None,
    limit: int = 50,
) -> list[QueryAnalyticsItem]:
    limit_normalizado = _limit_normalizado(limit)
    no_results_count = func.sum(case((SearchEvent.no_results == True, 1), else_=0))

    rows = (
        _query_base(db, since)
        .with_entities(
            SearchEvent.query_normalizada,
            func.count(SearchEvent.id).label("total"),
            func.avg(SearchEvent.result_count).label("avg_result_count"),
            no_results_count.label("no_results_count"),
        )
        .group_by(SearchEvent.query_normalizada)
        .order_by(func.count(SearchEvent.id).desc(), SearchEvent.query_normalizada.asc())
        .limit(limit_normalizado)
        .all()
    )

    return [
        QueryAnalyticsItem(
            query_normalizada=query_normalizada,
            total=int(total or 0),
            avg_result_count=float(avg_result_count or 0.0),
            no_results_count=int(total_no_results or 0),
        )
        for query_normalizada, total, avg_result_count, total_no_results in rows
    ]


def top_queries_no_results(
    db: Session,
    since: datetime | None = None,
    limit: int = 50,
) -> list[QueryNoResultsItem]:
    limit_normalizado = _limit_normalizado(limit)
    total_count = func.count(SearchEvent.id)
    no_results_count = func.sum(case((SearchEvent.no_results == True, 1), else_=0))

    rows = (
        _query_base(db, since)
        .with_entities(
            SearchEvent.query_normalizada,
            no_results_count.label("total_no_results"),
            total_count.label("total"),
        )
        .group_by(SearchEvent.query_normalizada)
        .having(no_results_count > 0)
        .order_by(no_results_count.desc(), total_count.desc(), SearchEvent.query_normalizada.asc())
        .limit(limit_normalizado)
        .all()
    )

    return [
        QueryNoResultsItem(
            query_normalizada=query_normalizada,
            total_no_results=int(total_no_results or 0),
            total=int(total or 0),
        )
        for query_normalizada, total_no_results, total in rows
    ]


def discovery_failures(
    db: Session,
    since: datetime | None = None,
    limit: int = 50,
) -> list[DiscoveryFailureItem]:
    limit_normalizado = _limit_normalizado(limit)
    total_count = func.count(SearchEvent.id)
    no_results_count = func.sum(case((SearchEvent.no_results == True, 1), else_=0))
    avg_result_count = func.avg(SearchEvent.result_count)

    rows = (
        _query_base(db, since)
        .with_entities(
            SearchEvent.query_normalizada,
            total_count.label("total"),
            no_results_count.label("no_results_count"),
            avg_result_count.label("avg_result_count"),
        )
        .group_by(SearchEvent.query_normalizada)
        .having((no_results_count > 0) | (avg_result_count < 2))
        .order_by(no_results_count.desc(), total_count.desc(), SearchEvent.query_normalizada.asc())
        .limit(limit_normalizado)
        .all()
    )

    return [
        DiscoveryFailureItem(
            query_normalizada=query_normalizada,
            total=int(total or 0),
            no_results_count=int(total_no_results or 0),
            avg_result_count=float(avg_results or 0.0),
        )
        for query_normalizada, total, total_no_results, avg_results in rows
    ]


def query_summary(
    db: Session,
    query_normalizada: str,
) -> QuerySummary:
    query = (query_normalizada or "").strip().lower()
    no_results_count = func.sum(case((SearchEvent.no_results == True, 1), else_=0))

    row = (
        db.query(
            func.count(SearchEvent.id).label("total"),
            func.avg(SearchEvent.result_count).label("avg_result_count"),
            no_results_count.label("no_results_count"),
            func.min(SearchEvent.created_at).label("first_seen_at"),
            func.max(SearchEvent.created_at).label("last_seen_at"),
        )
        .filter(SearchEvent.query_normalizada == query)
        .one()
    )

    return QuerySummary(
        query_normalizada=query,
        total=int(row.total or 0),
        avg_result_count=float(row.avg_result_count or 0.0),
        no_results_count=int(row.no_results_count or 0),
        first_seen_at=row.first_seen_at,
        last_seen_at=row.last_seen_at,
    )
