"""
candidate_registry.py
---------------------
Central registry for default Candidate Engine sources.
"""

from __future__ import annotations

from app.modules.search.services.candidate_engine.candidate_sources import (
    AssignmentCandidateSource,
    CandidateSource,
    ComercioNombreCandidateSource,
    DiscoveryCandidateSource,
    EspecialidadCandidateSource,
    PublicacionCandidateSource,
    RubroCandidateSource,
)


def get_default_candidate_sources() -> list[CandidateSource]:
    return [
        ComercioNombreCandidateSource(),
        PublicacionCandidateSource(),
        EspecialidadCandidateSource(),
        AssignmentCandidateSource(),
        RubroCandidateSource(),
        DiscoveryCandidateSource(),
    ]
