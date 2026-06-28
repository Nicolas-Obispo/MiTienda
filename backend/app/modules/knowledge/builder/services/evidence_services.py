"""
evidence_services.py
--------------------
Servicios read-only que convierten analytics en evidencia estructurada.
"""

from datetime import datetime

from sqlalchemy.orm import Session

from app.modules.knowledge.analytics.services.search_event_analytics_services import (
    discovery_failures,
    top_queries,
    top_queries_no_results,
)
from app.modules.knowledge.builder.schemas.evidence_schemas import (
    CoverageGapEvidence,
    KnowledgeEvidenceBase,
    SearchTermEvidence,
    SpecialtyEvidence,
)


def _limit_normalizado(limit: int) -> int:
    return max(1, min(int(limit), 200))


def _clamp(valor: float) -> float:
    return max(0.0, min(float(valor), 1.0))


def _frequency_score(total: int) -> float:
    return _clamp(total / 10)


def _no_results_score(no_results_count: int, total: int) -> float:
    if total <= 0:
        return 0.0
    return _clamp(no_results_count / total)


def _low_coverage_score(avg_result_count: float) -> float:
    if avg_result_count >= 5:
        return 0.0
    return _clamp((5 - avg_result_count) / 5)


def _strength(confidence: float) -> str:
    if confidence < 0.40:
        return "noise"
    if confidence < 0.65:
        return "weak"
    if confidence < 0.80:
        return "candidate"
    return "priority"


def _metrics(
    *,
    total: int,
    avg_result_count: float,
    no_results_count: int,
) -> dict:
    return {
        "total": int(total),
        "avg_result_count": round(float(avg_result_count), 4),
        "no_results_count": int(no_results_count),
        "no_results_rate": round(_no_results_score(no_results_count, total), 4),
    }


def _search_term_confidence(
    *,
    total: int,
    avg_result_count: float,
    no_results_count: int,
) -> float:
    return _clamp(
        0.45 * _frequency_score(total)
        + 0.35 * _low_coverage_score(avg_result_count)
        + 0.20 * _no_results_score(no_results_count, total)
    )


def _no_results_confidence(
    *,
    total: int,
    no_results_count: int,
) -> float:
    return _clamp(
        0.45 * _frequency_score(total)
        + 0.55 * _no_results_score(no_results_count, total)
    )


def _low_coverage_confidence(
    *,
    total: int,
    avg_result_count: float,
    no_results_count: int,
) -> float:
    return _clamp(
        0.35 * _frequency_score(total)
        + 0.45 * _low_coverage_score(avg_result_count)
        + 0.20 * _no_results_score(no_results_count, total)
    )


def build_search_term_evidence(
    db: Session,
    since: datetime | None = None,
    limit: int = 50,
) -> list[SearchTermEvidence]:
    evidencias: list[SearchTermEvidence] = []

    for item in top_queries(db, since=since, limit=_limit_normalizado(limit)):
        confidence = _search_term_confidence(
            total=item.total,
            avg_result_count=item.avg_result_count,
            no_results_count=item.no_results_count,
        )
        evidencias.append(
            SearchTermEvidence(
                query=item.query_normalizada,
                confidence=confidence,
                strength=_strength(confidence),
                reason="Query frecuente con potencial para enriquecer search_terms.",
                metrics=_metrics(
                    total=item.total,
                    avg_result_count=item.avg_result_count,
                    no_results_count=item.no_results_count,
                ),
            )
        )

    return evidencias


def build_low_coverage_evidence(
    db: Session,
    since: datetime | None = None,
    limit: int = 50,
) -> list[CoverageGapEvidence]:
    evidencias: list[CoverageGapEvidence] = []

    for item in discovery_failures(db, since=since, limit=_limit_normalizado(limit)):
        confidence = _low_coverage_confidence(
            total=item.total,
            avg_result_count=item.avg_result_count,
            no_results_count=item.no_results_count,
        )
        evidencias.append(
            CoverageGapEvidence(
                query=item.query_normalizada,
                confidence=confidence,
                strength=_strength(confidence),
                reason=(
                    "Query con baja cobertura en SearchEvent V1; "
                    "RankingEvidence fuerte requiere SearchSession, clicks o conversiones."
                ),
                metrics=_metrics(
                    total=item.total,
                    avg_result_count=item.avg_result_count,
                    no_results_count=item.no_results_count,
                ),
            )
        )

    return evidencias


def build_no_results_evidence(
    db: Session,
    since: datetime | None = None,
    limit: int = 50,
) -> list[SpecialtyEvidence]:
    evidencias: list[SpecialtyEvidence] = []

    for item in top_queries_no_results(db, since=since, limit=_limit_normalizado(limit)):
        confidence = _no_results_confidence(
            total=item.total,
            no_results_count=item.total_no_results,
        )
        evidencias.append(
            SpecialtyEvidence(
                query=item.query_normalizada,
                confidence=confidence,
                strength=_strength(confidence),
                reason="Query con no-results recurrentes; evaluar nuevo termino o especialidad.",
                metrics={
                    "total": item.total,
                    "no_results_count": item.total_no_results,
                    "no_results_rate": round(
                        _no_results_score(item.total_no_results, item.total),
                        4,
                    ),
                },
            )
        )

    return evidencias


def build_knowledge_evidence(
    db: Session,
    since: datetime | None = None,
    limit: int = 50,
) -> list[KnowledgeEvidenceBase]:
    limit_normalizado = _limit_normalizado(limit)
    evidencias: list[KnowledgeEvidenceBase] = []

    evidencias.extend(
        build_no_results_evidence(db, since=since, limit=limit_normalizado)
    )
    evidencias.extend(
        build_low_coverage_evidence(db, since=since, limit=limit_normalizado)
    )
    evidencias.extend(
        build_search_term_evidence(db, since=since, limit=limit_normalizado)
    )

    evidencias.sort(
        key=lambda item: (
            item.confidence,
            item.metrics.get("total", 0),
            item.query,
        ),
        reverse=True,
    )
    return evidencias[:limit_normalizado]
