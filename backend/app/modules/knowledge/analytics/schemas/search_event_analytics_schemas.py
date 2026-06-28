"""
search_event_analytics_schemas.py
---------------------------------
Schemas internos para analytics read-only sobre SearchEvent.
"""

from datetime import datetime

from pydantic import BaseModel


class QueryAnalyticsItem(BaseModel):
    query_normalizada: str
    total: int
    avg_result_count: float
    no_results_count: int


class QueryNoResultsItem(BaseModel):
    query_normalizada: str
    total_no_results: int
    total: int


class QuerySummary(BaseModel):
    query_normalizada: str
    total: int
    avg_result_count: float
    no_results_count: int
    first_seen_at: datetime | None = None
    last_seen_at: datetime | None = None


class DiscoveryFailureItem(BaseModel):
    query_normalizada: str
    total: int
    no_results_count: int
    avg_result_count: float
