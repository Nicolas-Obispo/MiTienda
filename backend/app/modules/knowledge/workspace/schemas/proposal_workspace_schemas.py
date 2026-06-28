"""
proposal_workspace_schemas.py
-----------------------------
Schemas internos para consultar KnowledgeProposal.
"""

from datetime import datetime

from pydantic import BaseModel, Field


class ProposalListItem(BaseModel):
    id: int
    proposal_type: str
    status: str
    query: str
    term: str
    confidence: float
    dedupe_key: str
    created_at: datetime | None = None
    reviewed_at: datetime | None = None
    applied_at: datetime | None = None


class ProposalDetail(ProposalListItem):
    taxonomy_node_id: int | None = None
    target_payload_json: dict | None = None
    evidence_json: dict | None = None
    source: str
    rejected_reason: str | None = None
    reviewed_by_usuario_id: int | None = None
    applied_by_usuario_id: int | None = None


class ProposalStats(BaseModel):
    pending: int = 0
    approved: int = 0
    rejected: int = 0
    applied: int = 0
    by_proposal_type: dict[str, int] = Field(default_factory=dict)
    avg_confidence: float = 0.0
