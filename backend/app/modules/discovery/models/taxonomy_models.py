"""
taxonomy_models.py
------------------
Modelos base del motor de descubrimiento.

La taxonomia clasifica conceptos reutilizables por comercios, productos,
publicaciones, promociones, historias, eventos e IA sin reemplazar los rubros
actuales.
"""

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    JSON,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


class TaxonomyNode(Base):
    __tablename__ = "taxonomy_nodes"

    id = Column(Integer, primary_key=True, index=True)

    parent_id = Column(
        Integer,
        ForeignKey("taxonomy_nodes.id"),
        nullable=True,
        index=True,
    )

    type = Column(String(50), nullable=False, index=True)
    slug = Column(String(120), nullable=False, unique=True, index=True)
    nombre = Column(String(120), nullable=False)
    descripcion = Column(String(500))
    activo = Column(Boolean, nullable=False, default=True, index=True)
    orden = Column(Integer, nullable=False, default=0)
    metadata_json = Column(JSON)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    parent = relationship(
        "TaxonomyNode",
        remote_side=[id],
        back_populates="children",
        lazy="selectin",
    )
    children = relationship(
        "TaxonomyNode",
        back_populates="parent",
        lazy="selectin",
    )
    assignments = relationship(
        "TaxonomyAssignment",
        back_populates="node",
        cascade="all, delete-orphan",
        lazy="selectin",
    )


class TaxonomyAssignment(Base):
    __tablename__ = "taxonomy_assignments"
    __table_args__ = (
        UniqueConstraint(
            "taxonomy_node_id",
            "entity_type",
            "entity_id",
            name="uq_taxonomy_assignment_entity_node",
        ),
    )

    id = Column(Integer, primary_key=True, index=True)

    taxonomy_node_id = Column(
        Integer,
        ForeignKey("taxonomy_nodes.id"),
        nullable=False,
        index=True,
    )

    entity_type = Column(String(50), nullable=False, index=True)
    entity_id = Column(Integer, nullable=False, index=True)
    source = Column(String(50), nullable=False, default="sistema")
    confidence = Column(Float, nullable=False, default=1.0)
    principal = Column(Boolean, nullable=False, default=True, index=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    node = relationship(
        "TaxonomyNode",
        back_populates="assignments",
        lazy="selectin",
    )
