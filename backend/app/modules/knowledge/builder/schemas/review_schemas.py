"""
review_schemas.py
-----------------
Schemas internos para revision de KnowledgeProposal.
"""

from pydantic import BaseModel


class KnowledgeProposalReviewResult(BaseModel):
    id: int
    status: str
    reviewed_by_usuario_id: int | None = None
    rejected_reason: str | None = None
