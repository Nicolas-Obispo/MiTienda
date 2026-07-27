"""
Servicios internos del nucleo Agenda.

Los servicios concentran reglas de negocio y control transaccional. El
repositorio solo ejecuta operaciones ORM.
"""

from dataclasses import dataclass
from datetime import datetime

from sqlalchemy.orm import Session

from app.modules.agenda.models.agenda_models import (
    ContextoAgendable,
    ElementoAgenda,
    EstadoContextoAgendable,
    EstadoElementoAgenda,
)
from app.modules.agenda.repositories import agenda_repositories as repo
from app.modules.agenda.schemas.agenda_schemas import (
    ContextoAgendableResponse,
    ElementoAgendaCambioEstado,
    ElementoAgendaCreate,
    ElementoAgendaFiltros,
    ElementoAgendaResponse,
    ElementoAgendaUpdate,
)
from app.modules.agenda.services.agenda_datetime import (
    datetime_desde_db,
    datetime_para_db,
)


class ContextoAgendableNoEncontradoError(ValueError):
    pass


class ContextoAgendableArchivadoError(ValueError):
    pass


class ElementoAgendaNoEncontradoError(ValueError):
    pass


class AgendaElementoConflictoConcurrenciaError(RuntimeError):
    pass


class AgendaIntervaloSolapamientoInvalidoError(ValueError):
    pass


@dataclass(frozen=True)
class SolapamientosAgendaResultado:
    hay_solapamiento: bool
    cantidad: int
    elementos: list[ElementoAgendaResponse]


def _contexto_response(contexto: ContextoAgendable) -> ContextoAgendableResponse:
    return ContextoAgendableResponse(
        id=contexto.id,
        estado=contexto.estado,
        created_at=datetime_desde_db(contexto.created_at),
        updated_at=datetime_desde_db(contexto.updated_at),
    )


def _elemento_response(elemento: ElementoAgenda) -> ElementoAgendaResponse:
    return ElementoAgendaResponse(
        id=elemento.id,
        contexto_id=elemento.contexto_id,
        tipo=elemento.tipo,
        estado=elemento.estado,
        version=elemento.version,
        titulo=elemento.titulo,
        descripcion=elemento.descripcion,
        inicio=datetime_desde_db(elemento.inicio),
        fin=datetime_desde_db(elemento.fin),
        todo_el_dia=elemento.todo_el_dia,
        created_at=datetime_desde_db(elemento.created_at),
        updated_at=datetime_desde_db(elemento.updated_at),
    )


def _obtener_contexto_o_error(
    db: Session,
    contexto_id: int,
) -> ContextoAgendable:
    contexto = repo.obtener_contexto_por_id(db, contexto_id)
    if contexto is None:
        raise ContextoAgendableNoEncontradoError("Contexto agendable no encontrado")

    return contexto


def _asegurar_contexto_modificable(contexto: ContextoAgendable) -> None:
    if contexto.estado == EstadoContextoAgendable.archivado:
        raise ContextoAgendableArchivadoError(
            "No se puede modificar un contexto agendable archivado"
        )


def _obtener_elemento_o_error(
    db: Session,
    *,
    contexto_id: int,
    elemento_id: int,
) -> ElementoAgenda:
    elemento = repo.obtener_elemento_por_id_y_contexto(
        db,
        contexto_id=contexto_id,
        elemento_id=elemento_id,
    )
    if elemento is None:
        raise ElementoAgendaNoEncontradoError("Elemento de agenda no encontrado")

    return elemento


def _payload_elemento_para_db(data: ElementoAgendaCreate) -> dict:
    return {
        "tipo": data.tipo,
        "titulo": data.titulo,
        "descripcion": data.descripcion,
        "inicio": datetime_para_db(data.inicio),
        "fin": datetime_para_db(data.fin),
        "todo_el_dia": data.todo_el_dia,
    }


def _revalidar_update_combinado(
    elemento: ElementoAgenda,
    cambios: dict,
) -> dict:
    combinado = {
        "tipo": cambios.get("tipo", elemento.tipo),
        "titulo": cambios.get("titulo", elemento.titulo),
        "descripcion": cambios.get("descripcion", elemento.descripcion),
        "inicio": cambios.get("inicio", datetime_desde_db(elemento.inicio)),
        "fin": cambios.get("fin", datetime_desde_db(elemento.fin)),
        "todo_el_dia": cambios.get("todo_el_dia", elemento.todo_el_dia),
    }
    validado = ElementoAgendaCreate(**combinado)
    payload = _payload_elemento_para_db(validado)
    payload["version_esperada"] = cambios["version_esperada"]

    if "estado" in cambios:
        payload["estado"] = cambios["estado"]

    return payload


def crear_contexto_agendable(db: Session) -> ContextoAgendableResponse:
    contexto = repo.crear_contexto(db)
    return _contexto_response(contexto)


def archivar_contexto_agendable(
    db: Session,
    contexto_id: int,
) -> ContextoAgendableResponse:
    return _cambiar_estado_contexto(
        db,
        contexto_id=contexto_id,
        estado=EstadoContextoAgendable.archivado,
    )


def reactivar_contexto_agendable(
    db: Session,
    contexto_id: int,
) -> ContextoAgendableResponse:
    return _cambiar_estado_contexto(
        db,
        contexto_id=contexto_id,
        estado=EstadoContextoAgendable.activo,
    )


def _cambiar_estado_contexto(
    db: Session,
    *,
    contexto_id: int,
    estado: EstadoContextoAgendable,
) -> ContextoAgendableResponse:
    contexto = _obtener_contexto_o_error(db, contexto_id)
    repo.cambiar_estado_contexto(db, contexto, estado)
    return _contexto_response(contexto)


def crear_elemento_agenda(
    db: Session,
    contexto_id: int,
    data: ElementoAgendaCreate,
) -> ElementoAgendaResponse:
    contexto = _obtener_contexto_o_error(db, contexto_id)
    _asegurar_contexto_modificable(contexto)

    elemento = repo.crear_elemento(
        db,
        contexto_id=contexto_id,
        **_payload_elemento_para_db(data),
    )
    return _elemento_response(elemento)


def obtener_elemento_agenda(
    db: Session,
    *,
    contexto_id: int,
    elemento_id: int,
) -> ElementoAgendaResponse:
    _obtener_contexto_o_error(db, contexto_id)
    elemento = _obtener_elemento_o_error(
        db,
        contexto_id=contexto_id,
        elemento_id=elemento_id,
    )
    return _elemento_response(elemento)


def listar_elementos_agenda(
    db: Session,
    *,
    contexto_id: int,
    filtros: ElementoAgendaFiltros | None = None,
) -> list[ElementoAgendaResponse]:
    _obtener_contexto_o_error(db, contexto_id)
    filtros = filtros or ElementoAgendaFiltros(incluir_sin_fecha=True)

    inicio = datetime_para_db(filtros.inicio)
    fin = datetime_para_db(filtros.fin)

    elementos = repo.listar_elementos_por_contexto(
        db,
        contexto_id=contexto_id,
        tipo=filtros.tipo,
        estado=filtros.estado,
        inicio=inicio,
        fin=fin,
        todo_el_dia=filtros.todo_el_dia,
        incluir_sin_fecha=filtros.incluir_sin_fecha,
    )
    return [_elemento_response(elemento) for elemento in elementos]


def detectar_solapamientos_elemento(
    db: Session,
    *,
    contexto_id: int,
    inicio: datetime,
    fin: datetime,
    elemento_id_excluir: int | None = None,
) -> SolapamientosAgendaResultado:
    _obtener_contexto_o_error(db, contexto_id)
    inicio_db = datetime_para_db(inicio)
    fin_db = datetime_para_db(fin)

    if inicio_db is None or fin_db is None or fin_db <= inicio_db:
        raise AgendaIntervaloSolapamientoInvalidoError(
            "El intervalo de solapamiento requiere inicio y fin validos"
        )

    elementos = repo.buscar_solapamientos_elemento(
        db,
        contexto_id=contexto_id,
        inicio=inicio_db,
        fin=fin_db,
        elemento_id_excluir=elemento_id_excluir,
    )
    elementos_response = [_elemento_response(elemento) for elemento in elementos]

    return SolapamientosAgendaResultado(
        hay_solapamiento=bool(elementos_response),
        cantidad=len(elementos_response),
        elementos=elementos_response,
    )


def actualizar_elemento_agenda(
    db: Session,
    *,
    contexto_id: int,
    elemento_id: int,
    data: ElementoAgendaUpdate,
) -> ElementoAgendaResponse:
    contexto = _obtener_contexto_o_error(db, contexto_id)
    _asegurar_contexto_modificable(contexto)
    elemento = _obtener_elemento_o_error(
        db,
        contexto_id=contexto_id,
        elemento_id=elemento_id,
    )
    cambios = data.model_dump(exclude_unset=True)
    payload = _revalidar_update_combinado(elemento, cambios)

    elemento = repo.actualizar_elemento(db, elemento, payload)
    if elemento is None:
        raise AgendaElementoConflictoConcurrenciaError(
            "El elemento de agenda fue modificado por otra operacion"
        )

    return _elemento_response(elemento)


def completar_elemento_agenda(
    db: Session,
    *,
    contexto_id: int,
    elemento_id: int,
    version_esperada: int,
) -> ElementoAgendaResponse:
    return _cambiar_estado_elemento(
        db,
        contexto_id=contexto_id,
        elemento_id=elemento_id,
        data=ElementoAgendaCambioEstado(
            estado=EstadoElementoAgenda.completado,
            version_esperada=version_esperada,
        ),
    )


def cancelar_elemento_agenda(
    db: Session,
    *,
    contexto_id: int,
    elemento_id: int,
    version_esperada: int,
) -> ElementoAgendaResponse:
    return _cambiar_estado_elemento(
        db,
        contexto_id=contexto_id,
        elemento_id=elemento_id,
        data=ElementoAgendaCambioEstado(
            estado=EstadoElementoAgenda.cancelado,
            version_esperada=version_esperada,
        ),
    )


def _cambiar_estado_elemento(
    db: Session,
    *,
    contexto_id: int,
    elemento_id: int,
    data: ElementoAgendaCambioEstado,
) -> ElementoAgendaResponse:
    contexto = _obtener_contexto_o_error(db, contexto_id)
    _asegurar_contexto_modificable(contexto)
    elemento = _obtener_elemento_o_error(
        db,
        contexto_id=contexto_id,
        elemento_id=elemento_id,
    )
    elemento = repo.cambiar_estado_elemento(
        db,
        elemento,
        data.estado,
        data.version_esperada,
    )
    if elemento is None:
        raise AgendaElementoConflictoConcurrenciaError(
            "El elemento de agenda fue modificado por otra operacion"
        )

    return _elemento_response(elemento)
