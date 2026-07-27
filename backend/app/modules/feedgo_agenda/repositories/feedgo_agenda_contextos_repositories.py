"""
Repositorio ORM de la integracion FeedGo-Agenda.

Este modulo encapsula consultas y persistencia del vinculo. No aplica reglas
de negocio, permisos, creacion de contextos ni control transaccional.
"""

from datetime import datetime

from sqlalchemy import and_, or_
from sqlalchemy.orm import Session

from app.modules.agenda.models.agenda_models import (
    ContextoAgendable,
    ElementoAgenda,
    EstadoElementoAgenda,
    TipoElementoAgenda,
)
from app.modules.feedgo_agenda.models.feedgo_agenda_contextos_models import (
    FeedGoAgendaContexto,
)
from app.modules.spaces.models.comercios_models import Comercio


def obtener_vinculo_por_id(
    db: Session,
    vinculo_id: int,
) -> FeedGoAgendaContexto | None:
    return (
        db.query(FeedGoAgendaContexto)
        .filter(FeedGoAgendaContexto.id == vinculo_id)
        .first()
    )


def obtener_vinculo_por_comercio_id(
    db: Session,
    comercio_id: int,
) -> FeedGoAgendaContexto | None:
    return (
        db.query(FeedGoAgendaContexto)
        .filter(FeedGoAgendaContexto.comercio_id == comercio_id)
        .first()
    )


def obtener_vinculo_por_agenda_contexto_id(
    db: Session,
    agenda_contexto_id: int,
) -> FeedGoAgendaContexto | None:
    return (
        db.query(FeedGoAgendaContexto)
        .filter(FeedGoAgendaContexto.agenda_contexto_id == agenda_contexto_id)
        .first()
    )


def existe_vinculo_por_comercio_id(
    db: Session,
    comercio_id: int,
) -> bool:
    return (
        db.query(FeedGoAgendaContexto.id)
        .filter(FeedGoAgendaContexto.comercio_id == comercio_id)
        .first()
        is not None
    )


def existe_vinculo_por_agenda_contexto_id(
    db: Session,
    agenda_contexto_id: int,
) -> bool:
    return (
        db.query(FeedGoAgendaContexto.id)
        .filter(FeedGoAgendaContexto.agenda_contexto_id == agenda_contexto_id)
        .first()
        is not None
    )


def crear_vinculo_feedgo_agenda(
    db: Session,
    *,
    comercio_id: int,
    agenda_contexto_id: int,
) -> FeedGoAgendaContexto:
    vinculo = FeedGoAgendaContexto(
        comercio_id=comercio_id,
        agenda_contexto_id=agenda_contexto_id,
    )
    db.add(vinculo)
    db.flush()
    return vinculo


def listar_elementos_agenda_general_por_usuario(
    db: Session,
    *,
    usuario_id: int,
    comercio_id: int | None = None,
    tipo: TipoElementoAgenda | None = None,
    estado: EstadoElementoAgenda | None = None,
    inicio: datetime | None = None,
    fin: datetime | None = None,
    incluir_sin_fecha: bool = False,
) -> list[tuple[Comercio, ContextoAgendable, ElementoAgenda]]:
    query = (
        db.query(Comercio, ContextoAgendable, ElementoAgenda)
        .join(
            FeedGoAgendaContexto,
            FeedGoAgendaContexto.comercio_id == Comercio.id,
        )
        .join(
            ContextoAgendable,
            ContextoAgendable.id == FeedGoAgendaContexto.agenda_contexto_id,
        )
        .join(
            ElementoAgenda,
            ElementoAgenda.contexto_id == ContextoAgendable.id,
        )
        .filter(Comercio.usuario_id == usuario_id)
    )

    if comercio_id is not None:
        query = query.filter(Comercio.id == comercio_id)

    if tipo is not None:
        query = query.filter(ElementoAgenda.tipo == tipo)

    if estado is not None:
        query = query.filter(ElementoAgenda.estado == estado)

    if inicio is not None and fin is not None:
        con_fecha = or_(
            and_(
                ElementoAgenda.inicio.isnot(None),
                ElementoAgenda.fin.isnot(None),
                ElementoAgenda.inicio < fin,
                ElementoAgenda.fin > inicio,
            ),
            and_(
                ElementoAgenda.inicio.isnot(None),
                ElementoAgenda.fin.is_(None),
                ElementoAgenda.inicio >= inicio,
                ElementoAgenda.inicio < fin,
            ),
        )
        query = query.filter(
            or_(con_fecha, ElementoAgenda.inicio.is_(None))
            if incluir_sin_fecha
            else con_fecha
        )
    elif inicio is not None:
        con_fecha = or_(
            and_(ElementoAgenda.fin.isnot(None), ElementoAgenda.fin > inicio),
            and_(
                ElementoAgenda.fin.is_(None),
                ElementoAgenda.inicio >= inicio,
            ),
        )
        query = query.filter(
            or_(con_fecha, ElementoAgenda.inicio.is_(None))
            if incluir_sin_fecha
            else con_fecha
        )
    elif fin is not None:
        con_fecha = ElementoAgenda.inicio < fin
        query = query.filter(
            or_(con_fecha, ElementoAgenda.inicio.is_(None))
            if incluir_sin_fecha
            else con_fecha
        )
    elif not incluir_sin_fecha:
        query = query.filter(ElementoAgenda.inicio.isnot(None))

    return (
        query.order_by(
            ElementoAgenda.inicio.is_(None).asc(),
            ElementoAgenda.inicio.asc(),
            Comercio.nombre.asc(),
            ElementoAgenda.id.asc(),
        )
        .all()
    )
