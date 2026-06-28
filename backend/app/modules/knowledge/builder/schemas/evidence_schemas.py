"""
evidence_schemas.py
-------------------
Schemas internos para evidencia de Knowledge Builder.
"""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


EvidenceStrength = Literal["noise", "weak", "candidate", "priority"]


class KnowledgeEvidenceBase(BaseModel):
    evidence_type: str
    query: str
    confidence: float = Field(ge=0.0, le=1.0)
    strength: EvidenceStrength
    reason: str
    metrics: dict = Field(default_factory=dict)
    source: str = "search_event_analytics"
    generated_at: datetime = Field(default_factory=datetime.utcnow)


class SearchTermEvidence(KnowledgeEvidenceBase):
    evidence_type: Literal["search_term"] = "search_term"


class SynonymEvidence(KnowledgeEvidenceBase):
    evidence_type: Literal["synonym"] = "synonym"


class RelatedTermEvidence(KnowledgeEvidenceBase):
    evidence_type: Literal["related_term"] = "related_term"


class SpecialtyEvidence(KnowledgeEvidenceBase):
    evidence_type: Literal["specialty"] = "specialty"


class CoverageGapEvidence(KnowledgeEvidenceBase):
    evidence_type: Literal["coverage_gap"] = "coverage_gap"


class RankingEvidence(KnowledgeEvidenceBase):
    evidence_type: Literal["ranking"] = "ranking"
