"""
proposal_schemas.py
-------------------
Schemas internos para propuestas revisables de Knowledge.
"""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


ProposalType = Literal[
    "add_search_term",
    "add_synonym",
    "add_related_term",
    "create_specialty",
    "improve_ranking_signal",
]

ProposalStatus = Literal["pending", "approved", "rejected", "applied"]


class KnowledgeProposalCandidate(BaseModel):
    proposal_type: ProposalType
    taxonomy_node_id: int | None = None
    query: str
    term: str
    target_payload_json: dict = Field(default_factory=dict)
    evidence_json: dict = Field(default_factory=dict)
    confidence: float = Field(ge=0.0, le=1.0)
    source: str = "knowledge_evidence"
    dedupe_key: str


class KnowledgeProposalRead(BaseModel):
    id: int
    proposal_type: str
    status: ProposalStatus
    taxonomy_node_id: int | None = None
    query: str
    term: str
    target_payload_json: dict | None = None
    evidence_json: dict | None = None
    confidence: float
    source: str
    dedupe_key: str
    rejected_reason: str | None = None
    reviewed_by_usuario_id: int | None = None
    applied_by_usuario_id: int | None = None
    created_at: datetime | None = None
    reviewed_at: datetime | None = None
    applied_at: datetime | None = None
