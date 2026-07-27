"""
Repositorio ORM del nucleo Agenda.

Este modulo no decide reglas de negocio. Solo encapsula persistencia y consultas.
"""

from datetime import datetime

from sqlalchemy import and_, or_
from sqlalchemy.orm import Session

from app.modules.agenda.models.agenda_models import (
    ContextoAgendable,
    ElementoAgenda,
    EstadoContextoAgendable,
    EstadoElementoAgenda,
    TipoElementoAgenda,
)


def crear_contexto(db: Session) -> ContextoAgendable:
    contexto = ContextoAgendable()
    db.add(contexto)
    db.flush()
    return contexto


def obtener_contexto_por_id(
    db: Session,
    contexto_id: int,
) -> ContextoAgendable | None:
    return (
        db.query(ContextoAgendable)
        .filter(ContextoAgendable.id == contexto_id)
        .first()
    )


def existe_contexto(db: Session, contexto_id: int) -> bool:
    return (
        db.query(ContextoAgendable.id)
        .filter(ContextoAgendable.id == contexto_id)
        .first()
        is not None
    )


def cambiar_estado_contexto(
    db: Session,
    contexto: ContextoAgendable,
    estado: EstadoContextoAgendable,
) -> ContextoAgendable:
    contexto.estado = estado
    db.flush()
    return contexto


def crear_elemento(
    db: Session,
    *,
    contexto_id: int,
    tipo: TipoElementoAgenda,
    titulo: str,
    descripcion: str | None,
    inicio: datetime | None,
    fin: datetime | None,
    todo_el_dia: bool,
) -> ElementoAgenda:
    elemento = ElementoAgenda(
        contexto_id=contexto_id,
        tipo=tipo,
        titulo=titulo,
        descripcion=descripcion,
        inicio=inicio,
        fin=fin,
        todo_el_dia=todo_el_dia,
    )
    db.add(elemento)
    db.flush()
    return elemento


def obtener_elemento_por_id_y_contexto(
    db: Session,
    *,
    contexto_id: int,
    elemento_id: int,
) -> ElementoAgenda | None:
    return (
        db.query(ElementoAgenda)
        .filter(
            ElementoAgenda.contexto_id == contexto_id,
            ElementoAgenda.id == elemento_id,
        )
        .first()
    )


def listar_elementos_por_contexto(
    db: Session,
    *,
    contexto_id: int,
    tipo: TipoElementoAgenda | None = None,
    estado: EstadoElementoAgenda | None = None,
    inicio: datetime | None = None,
    fin: datetime | None = None,
    todo_el_dia: bool | None = None,
    incluir_sin_fecha: bool = False,
) -> list[ElementoAgenda]:
    query = db.query(ElementoAgenda).filter(ElementoAgenda.contexto_id == contexto_id)

    if tipo is not None:
        query = query.filter(ElementoAgenda.tipo == tipo)

    if estado is not None:
        query = query.filter(ElementoAgenda.estado == estado)

    if todo_el_dia is not None:
        query = query.filter(ElementoAgenda.todo_el_dia == todo_el_dia)

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
            and_(ElementoAgenda.fin.is_(None), ElementoAgenda.inicio >= inicio),
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
            ElementoAgenda.id.asc(),
        )
        .all()
    )


def buscar_solapamientos_elemento(
    db: Session,
    *,
    contexto_id: int,
    inicio: datetime,
    fin: datetime,
    elemento_id_excluir: int | None = None,
) -> list[ElementoAgenda]:
    query = db.query(ElementoAgenda).filter(
        ElementoAgenda.contexto_id == contexto_id,
        ElementoAgenda.estado != EstadoElementoAgenda.cancelado,
        ElementoAgenda.tipo.in_(
            [
                TipoElementoAgenda.bloqueo,
                TipoElementoAgenda.evento,
            ]
        ),
        ElementoAgenda.todo_el_dia.is_(False),
        ElementoAgenda.inicio.isnot(None),
        ElementoAgenda.fin.isnot(None),
        ElementoAgenda.inicio < fin,
        ElementoAgenda.fin > inicio,
    )

    if elemento_id_excluir is not None:
        query = query.filter(ElementoAgenda.id != elemento_id_excluir)

    return (
        query.order_by(
            ElementoAgenda.inicio.asc(),
            ElementoAgenda.fin.asc(),
            ElementoAgenda.id.asc(),
        )
        .all()
    )


def actualizar_elemento(
    db: Session,
    elemento: ElementoAgenda,
    campos: dict,
) -> ElementoAgenda | None:
    version_esperada = campos.pop("version_esperada")
    filas_actualizadas = (
        db.query(ElementoAgenda)
        .filter(
            ElementoAgenda.id == elemento.id,
            ElementoAgenda.contexto_id == elemento.contexto_id,
            ElementoAgenda.version == version_esperada,
        )
        .update(
            {
                **campos,
                "version": ElementoAgenda.version + 1,
            },
            synchronize_session=False,
        )
    )
    db.flush()
    if filas_actualizadas == 0:
        return None

    db.refresh(elemento)
    return elemento


def cambiar_estado_elemento(
    db: Session,
    elemento: ElementoAgenda,
    estado: EstadoElementoAgenda,
    version_esperada: int,
) -> ElementoAgenda | None:
    return actualizar_elemento(
        db,
        elemento,
        {
            "estado": estado,
            "version_esperada": version_esperada,
        },
    )
