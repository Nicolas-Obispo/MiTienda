"""
crear_knowledge_proposals.py
----------------------------
Script idempotente para crear la tabla knowledge_proposals.
"""

from app.core.database import engine
from app.modules.knowledge.models.knowledge_proposal_models import KnowledgeProposal


def crear_tabla_knowledge_proposals() -> None:
    KnowledgeProposal.__table__.create(bind=engine, checkfirst=True)


if __name__ == "__main__":
    print("Creando tabla knowledge_proposals...")
    crear_tabla_knowledge_proposals()
    print("Tabla knowledge_proposals lista.")
