"""
Candidate Engine contracts.

Internal types used by candidate generation before ranking.
"""

from app.modules.search.services.candidate_engine.candidate_types import (
    CandidateEvidence,
    CandidateGenerationContext,
    CandidateSet,
)
from app.modules.search.services.candidate_engine.candidate_sources import (
    AssignmentCandidateSource,
    CandidateSource,
    ComercioNombreCandidateSource,
    DiscoveryCandidateSource,
    EspecialidadCandidateSource,
    PublicacionCandidateSource,
    RubroCandidateSource,
)
from app.modules.search.services.candidate_engine.candidate_generator import (
    generate_candidates,
)
from app.modules.search.services.candidate_engine.candidate_registry import (
    get_default_candidate_sources,
)
from app.modules.search.services.candidate_engine.candidate_union import (
    union_candidate_evidence,
)

__all__ = [
    "CandidateEvidence",
    "CandidateGenerationContext",
    "CandidateSet",
    "AssignmentCandidateSource",
    "CandidateSource",
    "ComercioNombreCandidateSource",
    "DiscoveryCandidateSource",
    "EspecialidadCandidateSource",
    "PublicacionCandidateSource",
    "RubroCandidateSource",
    "generate_candidates",
    "get_default_candidate_sources",
    "union_candidate_evidence",
]
