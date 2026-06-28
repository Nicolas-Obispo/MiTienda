"""
knowledge_proposal_models.py
----------------------------
Modelo ORM para propuestas revisables de Knowledge.
"""

from sqlalchemy import Column, DateTime, Float, Integer, JSON, String
from sqlalchemy.sql import func

from app.core.database import Base


class KnowledgeProposal(Base):
    __tablename__ = "knowledge_proposals"

    id = Column(Integer, primary_key=True, index=True)

    proposal_type = Column(String(50), nullable=False, index=True)
    status = Column(String(30), nullable=False, default="pending", index=True)
    taxonomy_node_id = Column(Integer, nullable=True, index=True)

    query = Column(String(255), nullable=False, index=True)
    term = Column(String(255), nullable=False, index=True)
    target_payload_json = Column(JSON)
    evidence_json = Column(JSON)
    confidence = Column(Float, nullable=False, default=0.0)
    source = Column(String(80), nullable=False, default="knowledge_evidence")
    dedupe_key = Column(String(500), nullable=False, unique=True, index=True)

    rejected_reason = Column(String(500), nullable=True)
    reviewed_by_usuario_id = Column(Integer, nullable=True)
    applied_by_usuario_id = Column(Integer, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    reviewed_at = Column(DateTime(timezone=True), nullable=True)
    applied_at = Column(DateTime(timezone=True), nullable=True)
