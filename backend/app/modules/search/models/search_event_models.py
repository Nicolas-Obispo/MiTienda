"""
search_event_models.py
----------------------
Modelo ORM para eventos de busqueda.
"""

from sqlalchemy import Boolean, Column, DateTime, Float, Integer, JSON, String
from sqlalchemy.sql import func

from app.core.database import Base


class SearchEvent(Base):
    __tablename__ = "search_events"

    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)

    endpoint = Column(String(120), nullable=False, index=True)
    query_original = Column(String(255))
    query_normalizada = Column(String(255), index=True)
    modo_busqueda = Column(String(50), nullable=False, index=True)

    smart = Column(Boolean, nullable=False, default=False)
    smart_semantic = Column(Boolean, nullable=False, default=False)
    limit = Column(Integer, nullable=False, default=20)
    offset = Column(Integer, nullable=False, default=0)
    radio_km = Column(Float)
    has_location = Column(Boolean, nullable=False, default=False, index=True)

    result_count = Column(Integer, nullable=False, default=0)
    no_results = Column(Boolean, nullable=False, default=False, index=True)

    taxonomy_node_ids_json = Column(JSON)
    rubro_ids_json = Column(JSON)
    comercio_result_ids_json = Column(JSON)
    metadata_json = Column(JSON)
