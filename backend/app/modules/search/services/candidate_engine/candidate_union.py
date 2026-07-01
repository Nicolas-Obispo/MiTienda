"""
candidate_union.py
------------------
Utilities for grouping candidate evidence before ranking.
"""

from __future__ import annotations

from typing import Any

from app.modules.search.services.candidate_engine.candidate_types import (
    CandidateEvidence,
    CandidateSet,
)


def _freeze_metadata(value: Any) -> Any:
    if isinstance(value, dict):
        return tuple(
            sorted(
                (key, _freeze_metadata(item))
                for key, item in value.items()
            )
        )

    if isinstance(value, list):
        return tuple(_freeze_metadata(item) for item in value)

    if isinstance(value, tuple):
        return tuple(_freeze_metadata(item) for item in value)

    if isinstance(value, set):
        return tuple(sorted(_freeze_metadata(item) for item in value))

    return value


def _evidence_key(evidence: CandidateEvidence) -> tuple[Any, ...]:
    return (
        evidence.comercio_id,
        evidence.source,
        evidence.reason,
        evidence.matched_entity_type,
        evidence.matched_entity_id,
        evidence.matched_text,
        evidence.confidence,
        _freeze_metadata(evidence.metadata),
    )


def union_candidate_evidence(
    evidences: list[CandidateEvidence],
) -> CandidateSet:
    """
    Group candidate evidence by commerce id without ranking.
    """

    candidates_by_comercio_id: dict[int, list[CandidateEvidence]] = {}
    source_counts: dict[str, int] = {}
    seen: set[tuple[Any, ...]] = set()

    for evidence in evidences:
        key = _evidence_key(evidence)
        if key in seen:
            continue

        seen.add(key)
        candidates_by_comercio_id.setdefault(
            evidence.comercio_id,
            [],
        ).append(evidence)
        source_counts[evidence.source] = source_counts.get(evidence.source, 0) + 1

    return CandidateSet(
        candidates_by_comercio_id=candidates_by_comercio_id,
        source_counts=source_counts,
        total_candidates=len(candidates_by_comercio_id),
    )
