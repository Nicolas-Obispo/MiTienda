"""
candidate_types.py
------------------
Internal contracts for the Candidate Engine.

These structures model search candidate evidence only. They do not rank,
score, hydrate, paginate, or query data sources by themselves.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class CandidateEvidence:
    """
    Evidence explaining why a commerce entered the candidate pool.
    """

    comercio_id: int
    source: str
    reason: str
    matched_entity_type: str
    matched_entity_id: int | None = None
    matched_text: str | None = None
    confidence: float | None = None
    metadata: dict[str, Any] | None = None


@dataclass
class CandidateSet:
    """
    Candidate evidence grouped by commerce id.
    """

    candidates_by_comercio_id: dict[int, list[CandidateEvidence]] = field(
        default_factory=dict
    )
    source_counts: dict[str, int] = field(default_factory=dict)
    total_candidates: int = 0


@dataclass(frozen=True)
class CandidateGenerationContext:
    """
    Shared context passed to candidate sources.
    """

    query_original: str
    query_normalizada: str
    terminos_expandidos: list[str] = field(default_factory=list)
    familia_intencion: str | None = None
    discovery_nodes: list[Any] = field(default_factory=list)
    limit_por_fuente: int = 50
