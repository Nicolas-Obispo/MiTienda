"""
candidate_generator.py
----------------------
Minimal runner for Candidate Engine sources.
"""

from __future__ import annotations

from collections.abc import Sequence

from sqlalchemy.orm import Session

from app.modules.search.services.candidate_engine.candidate_sources import (
    CandidateSource,
)
from app.modules.search.services.candidate_engine.candidate_registry import (
    get_default_candidate_sources,
)
from app.modules.search.services.candidate_engine.candidate_types import (
    CandidateEvidence,
    CandidateGenerationContext,
    CandidateSet,
)
from app.modules.search.services.candidate_engine.candidate_union import (
    union_candidate_evidence,
)


def generate_candidates(
    context: CandidateGenerationContext,
    db: Session,
    sources: Sequence[CandidateSource] | None = None,
) -> CandidateSet:
    """
    Execute candidate sources and return their unified candidate set.
    """

    selected_sources = (
        list(sources)
        if sources is not None
        else get_default_candidate_sources()
    )
    evidences: list[CandidateEvidence] = []

    for source in selected_sources:
        evidences.extend(source.generate(context=context, db=db))

    return union_candidate_evidence(evidences)
