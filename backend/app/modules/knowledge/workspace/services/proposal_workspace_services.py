"""
proposal_workspace_services.py
------------------------------
Servicios read-only para consultar KnowledgeProposal.
"""

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.modules.knowledge.models.knowledge_proposal_models import KnowledgeProposal
from app.modules.knowledge.workspace.schemas.proposal_workspace_schemas import (
    ProposalDetail,
    ProposalListItem,
    ProposalStats,
)


def _limit_normalizado(limit: int) -> int:
    return max(1, min(int(limit), 500))


def _to_list_item(proposal: KnowledgeProposal) -> ProposalListItem:
    return ProposalListItem(
        id=proposal.id,
        proposal_type=proposal.proposal_type,
        status=proposal.status,
        query=proposal.query,
        term=proposal.term,
        confidence=proposal.confidence,
        dedupe_key=proposal.dedupe_key,
        created_at=proposal.created_at,
        reviewed_at=proposal.reviewed_at,
        applied_at=proposal.applied_at,
    )


def _to_detail(proposal: KnowledgeProposal) -> ProposalDetail:
    return ProposalDetail(
        id=proposal.id,
        proposal_type=proposal.proposal_type,
        status=proposal.status,
        query=proposal.query,
        term=proposal.term,
        confidence=proposal.confidence,
        dedupe_key=proposal.dedupe_key,
        created_at=proposal.created_at,
        reviewed_at=proposal.reviewed_at,
        applied_at=proposal.applied_at,
        taxonomy_node_id=proposal.taxonomy_node_id,
        target_payload_json=proposal.target_payload_json,
        evidence_json=proposal.evidence_json,
        source=proposal.source,
        rejected_reason=proposal.rejected_reason,
        reviewed_by_usuario_id=proposal.reviewed_by_usuario_id,
        applied_by_usuario_id=proposal.applied_by_usuario_id,
    )


def _list_by_status(
    db: Session,
    status: str,
    limit: int,
) -> list[ProposalListItem]:
    rows = (
        db.query(KnowledgeProposal)
        .filter(KnowledgeProposal.status == status)
        .order_by(KnowledgeProposal.created_at.desc(), KnowledgeProposal.id.desc())
        .limit(_limit_normalizado(limit))
        .all()
    )
    return [_to_list_item(proposal) for proposal in rows]


def list_pending_proposals(
    db: Session,
    limit: int = 100,
) -> list[ProposalListItem]:
    return _list_by_status(db, "pending", limit)


def list_approved_proposals(
    db: Session,
    limit: int = 100,
) -> list[ProposalListItem]:
    return _list_by_status(db, "approved", limit)


def list_rejected_proposals(
    db: Session,
    limit: int = 100,
) -> list[ProposalListItem]:
    return _list_by_status(db, "rejected", limit)


def list_applied_proposals(
    db: Session,
    limit: int = 100,
) -> list[ProposalListItem]:
    return _list_by_status(db, "applied", limit)


def proposal_detail(
    db: Session,
    proposal_id: int,
) -> ProposalDetail | None:
    proposal = (
        db.query(KnowledgeProposal)
        .filter(KnowledgeProposal.id == proposal_id)
        .first()
    )
    if proposal is None:
        return None

    return _to_detail(proposal)


def proposal_stats(db: Session) -> ProposalStats:
    status_rows = (
        db.query(KnowledgeProposal.status, func.count(KnowledgeProposal.id))
        .group_by(KnowledgeProposal.status)
        .all()
    )
    type_rows = (
        db.query(KnowledgeProposal.proposal_type, func.count(KnowledgeProposal.id))
        .group_by(KnowledgeProposal.proposal_type)
        .all()
    )
    avg_confidence = db.query(func.avg(KnowledgeProposal.confidence)).scalar()

    status_counts = {status: int(total or 0) for status, total in status_rows}
    by_proposal_type = {
        proposal_type: int(total or 0)
        for proposal_type, total in type_rows
    }

    return ProposalStats(
        pending=status_counts.get("pending", 0),
        approved=status_counts.get("approved", 0),
        rejected=status_counts.get("rejected", 0),
        applied=status_counts.get("applied", 0),
        by_proposal_type=by_proposal_type,
        avg_confidence=float(avg_confidence or 0.0),
    )
