# app/services/historias_vistas_services.py
"""
Service: historias_vistas_services

Responsabilidad:
- Marcar una historia como vista por un usuario (idempotente).
- Consultar vistas (más adelante).

Reglas:
- Services = lógica/orquestación.
- No acceder a request/response aquí (eso es routers).
"""

from __future__ import annotations

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.historias_models import Historia
from app.models.historias_vistas_models import HistoriaVista


def marcar_historia_como_vista(db: Session, historia_id: int, usuario_id: int) -> HistoriaVista:
    """
    Marca una historia como vista por un usuario (idempotente).

    - Si la historia no existe -> levanta ValueError (router lo transforma en 404).
    - Si ya existe la vista -> devuelve la existente.
    - Si no existe -> crea y devuelve.

    :param db: Session
    :param historia_id: int
    :param usuario_id: int
    :return: HistoriaVista
    """
    # 1) Validar que exista la historia
    historia = db.query(Historia).filter(Historia.id == historia_id).first()
    if not historia:
      raise ValueError("Historia no encontrada")

    # 2) Chequear si ya existe la vista
    existing = (
        db.query(HistoriaVista)
        .filter(HistoriaVista.historia_id == historia_id, HistoriaVista.usuario_id == usuario_id)
        .first()
    )
    if existing:
        return existing

    # 3) Crear vista nueva
    vista = HistoriaVista(historia_id=historia_id, usuario_id=usuario_id)
    db.add(vista)

    try:
        db.commit()
        db.refresh(vista)
        return vista
    except IntegrityError:
        # Si dos requests llegan a la vez, el unique constraint puede disparar acá.
        db.rollback()
        existing = (
            db.query(HistoriaVista)
            .filter(HistoriaVista.historia_id == historia_id, HistoriaVista.usuario_id == usuario_id)
            .first()
        )
        if existing:
            return existing
        raise

