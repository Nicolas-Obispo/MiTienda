"""
review_services.py
------------------
Servicios internos para aprobar o rechazar KnowledgeProposal.
"""

from datetime import datetime

from sqlalchemy.orm import Session

from app.modules.knowledge.models.knowledge_proposal_models import KnowledgeProposal


class KnowledgeProposalReviewError(ValueError):
    pass


def _obtener_propuesta_pending(
    db: Session,
    proposal_id: int,
) -> KnowledgeProposal:
    proposal = (
        db.query(KnowledgeProposal)
        .filter(KnowledgeProposal.id == proposal_id)
        .first()
    )
    if proposal is None:
        raise KnowledgeProposalReviewError("KnowledgeProposal no existe")

    if proposal.status != "pending":
        raise KnowledgeProposalReviewError(
            "KnowledgeProposal debe estar pending para revisarse"
        )

    return proposal


def approve_proposal(
    db: Session,
    proposal_id: int,
    reviewed_by_usuario_id: int | None = None,
) -> KnowledgeProposal:
    proposal = _obtener_propuesta_pending(db, proposal_id)
    proposal.status = "approved"
    proposal.reviewed_at = datetime.utcnow()
    proposal.reviewed_by_usuario_id = reviewed_by_usuario_id
    db.commit()
    db.refresh(proposal)
    return proposal


def reject_proposal(
    db: Session,
    proposal_id: int,
    rejected_reason: str | None = None,
    reviewed_by_usuario_id: int | None = None,
) -> KnowledgeProposal:
    proposal = _obtener_propuesta_pending(db, proposal_id)
    proposal.status = "rejected"
    proposal.rejected_reason = rejected_reason
    proposal.reviewed_at = datetime.utcnow()
    proposal.reviewed_by_usuario_id = reviewed_by_usuario_id
    db.commit()
    db.refresh(proposal)
    return proposal
