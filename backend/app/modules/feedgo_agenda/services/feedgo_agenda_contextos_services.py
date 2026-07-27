"""
Servicios internos de integracion entre FeedGo y Agenda.

Esta capa conoce Comercio y ContextoAgendable. Agenda core permanece
independiente de FeedGo.
"""

from dataclasses import dataclass

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.modules.agenda.models.agenda_models import ContextoAgendable, ElementoAgenda
from app.modules.agenda.repositories import agenda_repositories
from app.modules.agenda.schemas.agenda_schemas import ElementoAgendaFiltros
from app.modules.agenda.services import agenda_services
from app.modules.agenda.services.agenda_datetime import datetime_para_db
from app.modules.feedgo_agenda.models.feedgo_agenda_contextos_models import (
    FeedGoAgendaContexto,
)
from app.modules.feedgo_agenda.repositories import (
    feedgo_agenda_contextos_repositories as feedgo_agenda_repo,
)
from app.modules.spaces.models.comercios_models import Comercio
from app.modules.users.models.usuarios_models import Usuario


UNIQUE_COMERCIO_ID = "uq_feedgo_agenda_contextos_comercio_id"
MYSQL_DUPLICATE_ENTRY = "1062"


class FeedGoAgendaComercioNoEncontradoError(ValueError):
    pass


class FeedGoAgendaUsuarioNoPropietarioError(PermissionError):
    pass


class FeedGoAgendaContextoInconsistenteError(RuntimeError):
    pass


class FeedGoAgendaConcurrenciaNoRecuperableError(RuntimeError):
    pass


@dataclass(frozen=True)
class FeedGoAgendaContextoResultado:
    vinculo: FeedGoAgendaContexto
    contexto: ContextoAgendable
    creado: bool


@dataclass(frozen=True)
class FeedGoAgendaElementoGeneralResultado:
    comercio: Comercio
    contexto: ContextoAgendable
    elemento: ElementoAgenda


def obtener_contexto_agenda_para_comercio(
    db: Session,
    *,
    comercio_id: int,
    usuario_autenticado: Usuario,
) -> FeedGoAgendaContextoResultado | None:
    _obtener_comercio_propio_o_error(
        db,
        comercio_id=comercio_id,
        usuario_autenticado=usuario_autenticado,
    )
    vinculo = feedgo_agenda_repo.obtener_vinculo_por_comercio_id(db, comercio_id)
    if vinculo is None:
        return None

    return _resultado_desde_vinculo(db, vinculo=vinculo, creado=False)


def obtener_o_crear_contexto_agenda_para_comercio(
    db: Session,
    *,
    comercio_id: int,
    usuario_autenticado: Usuario,
) -> FeedGoAgendaContextoResultado:
    _obtener_comercio_propio_o_error(
        db,
        comercio_id=comercio_id,
        usuario_autenticado=usuario_autenticado,
    )
    vinculo = feedgo_agenda_repo.obtener_vinculo_por_comercio_id(db, comercio_id)
    if vinculo is not None:
        return _resultado_desde_vinculo(db, vinculo=vinculo, creado=False)

    try:
        contexto_response = agenda_services.crear_contexto_agendable(db)
        vinculo = feedgo_agenda_repo.crear_vinculo_feedgo_agenda(
            db,
            comercio_id=comercio_id,
            agenda_contexto_id=contexto_response.id,
        )
        contexto = _obtener_contexto_vinculado_o_error(
            db,
            agenda_contexto_id=vinculo.agenda_contexto_id,
        )
        db.commit()
        db.refresh(vinculo)
        db.refresh(contexto)
        return FeedGoAgendaContextoResultado(
            vinculo=vinculo,
            contexto=contexto,
            creado=True,
        )
    except IntegrityError as exc:
        if _es_carrera_por_comercio_id(exc):
            db.rollback()
            return _recuperar_carrera_por_comercio_id(
                db,
                comercio_id=comercio_id,
            )

        db.rollback()
        raise
    except Exception:
        db.rollback()
        raise


def listar_elementos_agenda_general_para_usuario(
    db: Session,
    *,
    usuario_autenticado: Usuario,
    filtros: ElementoAgendaFiltros,
    comercio_id: int | None = None,
) -> list[FeedGoAgendaElementoGeneralResultado]:
    rows = feedgo_agenda_repo.listar_elementos_agenda_general_por_usuario(
        db,
        usuario_id=usuario_autenticado.id,
        comercio_id=comercio_id,
        tipo=filtros.tipo,
        estado=filtros.estado,
        inicio=datetime_para_db(filtros.inicio),
        fin=datetime_para_db(filtros.fin),
        incluir_sin_fecha=filtros.incluir_sin_fecha,
    )

    return [
        FeedGoAgendaElementoGeneralResultado(
            comercio=comercio,
            contexto=contexto,
            elemento=elemento,
        )
        for comercio, contexto, elemento in rows
    ]


def _obtener_comercio_propio_o_error(
    db: Session,
    *,
    comercio_id: int,
    usuario_autenticado: Usuario,
) -> Comercio:
    comercio = db.query(Comercio).filter(Comercio.id == comercio_id).first()
    if comercio is None:
        raise FeedGoAgendaComercioNoEncontradoError("Comercio no encontrado")

    if comercio.usuario_id != usuario_autenticado.id:
        raise FeedGoAgendaUsuarioNoPropietarioError(
            "No tenes permiso para acceder a la agenda de este comercio"
        )

    return comercio


def _resultado_desde_vinculo(
    db: Session,
    *,
    vinculo: FeedGoAgendaContexto,
    creado: bool,
) -> FeedGoAgendaContextoResultado:
    contexto = _obtener_contexto_vinculado_o_error(
        db,
        agenda_contexto_id=vinculo.agenda_contexto_id,
    )
    return FeedGoAgendaContextoResultado(
        vinculo=vinculo,
        contexto=contexto,
        creado=creado,
    )


def _obtener_contexto_vinculado_o_error(
    db: Session,
    *,
    agenda_contexto_id: int,
) -> ContextoAgendable:
    contexto = agenda_repositories.obtener_contexto_por_id(db, agenda_contexto_id)
    if contexto is None:
        raise FeedGoAgendaContextoInconsistenteError(
            "El vinculo FeedGo-Agenda referencia un contexto inexistente"
        )

    return contexto


def _recuperar_carrera_por_comercio_id(
    db: Session,
    *,
    comercio_id: int,
) -> FeedGoAgendaContextoResultado:
    vinculo = feedgo_agenda_repo.obtener_vinculo_por_comercio_id(db, comercio_id)
    if vinculo is None:
        raise FeedGoAgendaConcurrenciaNoRecuperableError(
            "No se pudo recuperar el contexto creado por la solicitud concurrente"
        )

    return _resultado_desde_vinculo(db, vinculo=vinculo, creado=False)


def _es_carrera_por_comercio_id(exc: IntegrityError) -> bool:
    texto_error = " ".join(str(arg) for arg in getattr(exc.orig, "args", ()))
    if not texto_error:
        texto_error = str(exc)

    return MYSQL_DUPLICATE_ENTRY in texto_error and UNIQUE_COMERCIO_ID in texto_error
