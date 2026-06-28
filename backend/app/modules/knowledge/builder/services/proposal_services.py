"""
proposal_services.py
--------------------
Servicios internos para crear propuestas pending desde evidencia.
"""

from datetime import datetime

from sqlalchemy.orm import Session

from app.modules.knowledge.builder.schemas.evidence_schemas import (
    KnowledgeEvidenceBase,
)
from app.modules.knowledge.builder.schemas.proposal_schemas import (
    KnowledgeProposalCandidate,
)
from app.modules.knowledge.builder.services.evidence_services import (
    build_knowledge_evidence,
)
from app.modules.knowledge.models.knowledge_proposal_models import KnowledgeProposal


_ACTIVE_STATUSES = {"pending", "approved", "applied"}
_MIN_QUERY_LENGTH = 3


def _normalizar_texto(valor: str | None) -> str:
    if not valor:
        return ""
    return valor.strip().lower()


def build_dedupe_key(
    proposal_type: str,
    taxonomy_node_id: int | None,
    term_or_query: str,
) -> str:
    node_key = str(taxonomy_node_id) if taxonomy_node_id is not None else "none"
    term_key = _normalizar_texto(term_or_query)
    return f"{proposal_type}:{node_key}:{term_key}"


def _proposal_type_from_evidence(evidence: KnowledgeEvidenceBase) -> str | None:
    if evidence.evidence_type == "search_term":
        return "add_search_term"
    if evidence.evidence_type == "synonym":
        return "add_synonym"
    if evidence.evidence_type == "related_term":
        return "add_related_term"
    if evidence.evidence_type == "specialty":
        return "create_specialty"
    if evidence.evidence_type == "ranking":
        return "improve_ranking_signal"
    if evidence.evidence_type == "coverage_gap":
        return "add_search_term"
    return None


def proposal_from_evidence(
    evidence: KnowledgeEvidenceBase,
) -> KnowledgeProposalCandidate | None:
    if evidence.strength not in {"candidate", "priority"}:
        return None

    query = _normalizar_texto(evidence.query)
    if len(query) < _MIN_QUERY_LENGTH:
        return None

    proposal_type = _proposal_type_from_evidence(evidence)
    if proposal_type is None:
        return None

    term = query
    dedupe_key = build_dedupe_key(
        proposal_type=proposal_type,
        taxonomy_node_id=None,
        term_or_query=term,
    )

    return KnowledgeProposalCandidate(
        proposal_type=proposal_type,
        taxonomy_node_id=None,
        query=query,
        term=term,
        target_payload_json={
            "term": term,
            "evidence_type": evidence.evidence_type,
        },
        evidence_json=evidence.model_dump(mode="json"),
        confidence=evidence.confidence,
        source=evidence.source,
        dedupe_key=dedupe_key,
    )


def _dedupe_keys_existentes(
    db: Session,
    dedupe_keys: list[str],
) -> set[str]:
    if not dedupe_keys:
        return set()

    rows = (
        db.query(KnowledgeProposal.dedupe_key)
        .filter(KnowledgeProposal.dedupe_key.in_(dedupe_keys))
        .filter(KnowledgeProposal.status.in_(_ACTIVE_STATUSES))
        .all()
    )
    return {dedupe_key for (dedupe_key,) in rows}


def generate_pending_proposals_from_evidence(
    db: Session,
    since: datetime | None = None,
    limit: int = 50,
) -> list[KnowledgeProposal]:
    evidencias = build_knowledge_evidence(db, since=since, limit=limit)
    candidates = [
        candidate
        for evidence in evidencias
        if (candidate := proposal_from_evidence(evidence)) is not None
    ]

    dedupe_keys_existentes = _dedupe_keys_existentes(
        db,
        [candidate.dedupe_key for candidate in candidates],
    )

    propuestas: list[KnowledgeProposal] = []
    dedupe_keys_nuevas: set[str] = set()

    for candidate in candidates:
        if candidate.dedupe_key in dedupe_keys_existentes:
            continue
        if candidate.dedupe_key in dedupe_keys_nuevas:
            continue

        propuesta = KnowledgeProposal(
            proposal_type=candidate.proposal_type,
            status="pending",
            taxonomy_node_id=candidate.taxonomy_node_id,
            query=candidate.query,
            term=candidate.term,
            target_payload_json=candidate.target_payload_json,
            evidence_json=candidate.evidence_json,
            confidence=candidate.confidence,
            source=candidate.source,
            dedupe_key=candidate.dedupe_key,
        )
        db.add(propuesta)
        propuestas.append(propuesta)
        dedupe_keys_nuevas.add(candidate.dedupe_key)

    if propuestas:
        db.commit()
        for propuesta in propuestas:
            db.refresh(propuesta)

    return propuestas
