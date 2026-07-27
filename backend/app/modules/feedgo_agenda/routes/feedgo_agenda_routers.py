"""
Rutas privadas de integracion FeedGo-Agenda.
"""

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, ConfigDict, ValidationError
from sqlalchemy.orm import Session

from app.core.auth import obtener_usuario_actual
from app.core.database import get_db
from app.modules.agenda.models.agenda_models import (
    ContextoAgendable,
    ElementoAgenda,
    EstadoElementoAgenda,
    TipoElementoAgenda,
)
from app.modules.agenda.schemas.agenda_schemas import (
    ContextoAgendableResponse,
    ElementoAgendaCambioEstado,
    ElementoAgendaCreate,
    ElementoAgendaFiltros,
    ElementoAgendaResponse,
    ElementoAgendaUpdate,
)
from app.modules.agenda.services.agenda_services import (
    AgendaElementoConflictoConcurrenciaError,
    AgendaIntervaloSolapamientoInvalidoError,
    ContextoAgendableArchivadoError,
    ContextoAgendableNoEncontradoError,
    ElementoAgendaNoEncontradoError,
    actualizar_elemento_agenda,
    crear_elemento_agenda,
    detectar_solapamientos_elemento,
    listar_elementos_agenda,
)
from app.modules.agenda.services.agenda_datetime import datetime_desde_db
from app.modules.feedgo_agenda.services.feedgo_agenda_contextos_services import (
    FeedGoAgendaComercioNoEncontradoError,
    FeedGoAgendaConcurrenciaNoRecuperableError,
    FeedGoAgendaContextoInconsistenteError,
    FeedGoAgendaContextoResultado,
    FeedGoAgendaUsuarioNoPropietarioError,
    listar_elementos_agenda_general_para_usuario,
    obtener_contexto_agenda_para_comercio,
    obtener_o_crear_contexto_agenda_para_comercio,
)
from app.modules.users.models.usuarios_models import Usuario


router = APIRouter(
    prefix="/feedgo-agenda",
    tags=["FeedGo Agenda"],
)


class FeedGoAgendaVinculoResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="forbid")

    id: int
    comercio_id: int
    agenda_contexto_id: int


class FeedGoAgendaContextoResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    vinculo: FeedGoAgendaVinculoResponse
    contexto: ContextoAgendableResponse
    creado: bool


class ElementoAgendaConSolapamientosResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    elemento: ElementoAgendaResponse
    hay_solapamiento: bool
    cantidad_solapamientos: int
    solapamientos: list[ElementoAgendaResponse]


class FeedGoAgendaComercioResumenResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: int
    nombre: str


class ElementoAgendaGeneralResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    comercio: FeedGoAgendaComercioResumenResponse
    contexto: ContextoAgendableResponse
    elemento: ElementoAgendaResponse


def _contexto_response(
    resultado: FeedGoAgendaContextoResultado,
) -> FeedGoAgendaContextoResponse:
    return FeedGoAgendaContextoResponse(
        vinculo=FeedGoAgendaVinculoResponse(
            id=resultado.vinculo.id,
            comercio_id=resultado.vinculo.comercio_id,
            agenda_contexto_id=resultado.vinculo.agenda_contexto_id,
        ),
        contexto=ContextoAgendableResponse(
            id=resultado.contexto.id,
            estado=resultado.contexto.estado,
            created_at=datetime_desde_db(resultado.contexto.created_at),
            updated_at=datetime_desde_db(resultado.contexto.updated_at),
        ),
        creado=resultado.creado,
    )


def _contexto_model_response(contexto: ContextoAgendable) -> ContextoAgendableResponse:
    return ContextoAgendableResponse(
        id=contexto.id,
        estado=contexto.estado,
        created_at=datetime_desde_db(contexto.created_at),
        updated_at=datetime_desde_db(contexto.updated_at),
    )


def _elemento_model_response(elemento: ElementoAgenda) -> ElementoAgendaResponse:
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


def _traducir_error_contexto(exc: Exception) -> HTTPException:
    if isinstance(exc, FeedGoAgendaComercioNoEncontradoError):
        return HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Comercio no encontrado",
        )
    if isinstance(exc, FeedGoAgendaUsuarioNoPropietarioError):
        return HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(exc),
        )
    if isinstance(exc, FeedGoAgendaConcurrenciaNoRecuperableError):
        return HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        )
    if isinstance(exc, FeedGoAgendaContextoInconsistenteError):
        return HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Vinculo FeedGo-Agenda inconsistente",
        )

    return HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="Error interno de Agenda",
    )


def _traducir_error_agenda(exc: Exception) -> HTTPException:
    if isinstance(exc, ContextoAgendableNoEncontradoError):
        return HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contexto de agenda no encontrado",
        )
    if isinstance(exc, ElementoAgendaNoEncontradoError):
        return HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Elemento de agenda no encontrado",
        )
    if isinstance(exc, ContextoAgendableArchivadoError):
        return HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        )
    if isinstance(exc, AgendaElementoConflictoConcurrenciaError):
        return HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        )
    if isinstance(exc, AgendaIntervaloSolapamientoInvalidoError):
        return HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        )

    return HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="Error interno de Agenda",
    )


def _obtener_contexto_existente_o_404(
    db: Session,
    *,
    comercio_id: int,
    usuario_actual: Usuario,
) -> FeedGoAgendaContextoResultado:
    try:
        resultado = obtener_contexto_agenda_para_comercio(
            db,
            comercio_id=comercio_id,
            usuario_autenticado=usuario_actual,
        )
    except (
        FeedGoAgendaComercioNoEncontradoError,
        FeedGoAgendaUsuarioNoPropietarioError,
        FeedGoAgendaConcurrenciaNoRecuperableError,
        FeedGoAgendaContextoInconsistenteError,
    ) as exc:
        raise _traducir_error_contexto(exc)

    if resultado is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contexto de agenda no encontrado",
        )

    return resultado


def _solapamientos_response(
    db: Session,
    *,
    contexto_id: int,
    elemento: ElementoAgendaResponse,
    elemento_id_excluir: int | None,
) -> tuple[bool, int, list[ElementoAgendaResponse]]:
    if (
        elemento.tipo not in (TipoElementoAgenda.evento, TipoElementoAgenda.bloqueo)
        or elemento.estado == EstadoElementoAgenda.cancelado
        or elemento.todo_el_dia
        or elemento.inicio is None
        or elemento.fin is None
    ):
        return False, 0, []

    solapamientos = detectar_solapamientos_elemento(
        db,
        contexto_id=contexto_id,
        inicio=elemento.inicio,
        fin=elemento.fin,
        elemento_id_excluir=elemento_id_excluir,
    )
    return (
        solapamientos.hay_solapamiento,
        solapamientos.cantidad,
        solapamientos.elementos,
    )


@router.get(
    "/mis/elementos",
    response_model=list[ElementoAgendaGeneralResponse],
)
def listar_mis_elementos_endpoint(
    inicio: datetime | None = Query(default=None),
    fin: datetime | None = Query(default=None),
    estado: EstadoElementoAgenda | None = Query(default=None),
    tipo: TipoElementoAgenda | None = Query(default=None),
    comercio_id: int | None = Query(default=None),
    db: Session = Depends(get_db),
    usuario_actual: Usuario = Depends(obtener_usuario_actual),
):
    try:
        filtros = ElementoAgendaFiltros(
            tipo=tipo,
            estado=estado,
            inicio=inicio,
            fin=fin,
            incluir_sin_fecha=True,
        )
    except ValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        )

    resultados = listar_elementos_agenda_general_para_usuario(
        db,
        usuario_autenticado=usuario_actual,
        filtros=filtros,
        comercio_id=comercio_id,
    )

    return [
        ElementoAgendaGeneralResponse(
            comercio=FeedGoAgendaComercioResumenResponse(
                id=resultado.comercio.id,
                nombre=resultado.comercio.nombre,
            ),
            contexto=_contexto_model_response(resultado.contexto),
            elemento=_elemento_model_response(resultado.elemento),
        )
        for resultado in resultados
    ]


@router.post(
    "/comercios/{comercio_id}/contexto",
    response_model=FeedGoAgendaContextoResponse,
)
def obtener_o_crear_contexto_endpoint(
    comercio_id: int,
    db: Session = Depends(get_db),
    usuario_actual: Usuario = Depends(obtener_usuario_actual),
):
    try:
        resultado = obtener_o_crear_contexto_agenda_para_comercio(
            db,
            comercio_id=comercio_id,
            usuario_autenticado=usuario_actual,
        )
    except (
        FeedGoAgendaComercioNoEncontradoError,
        FeedGoAgendaUsuarioNoPropietarioError,
        FeedGoAgendaConcurrenciaNoRecuperableError,
        FeedGoAgendaContextoInconsistenteError,
    ) as exc:
        raise _traducir_error_contexto(exc)

    return _contexto_response(resultado)


@router.get(
    "/comercios/{comercio_id}/contexto",
    response_model=FeedGoAgendaContextoResponse,
)
def obtener_contexto_endpoint(
    comercio_id: int,
    db: Session = Depends(get_db),
    usuario_actual: Usuario = Depends(obtener_usuario_actual),
):
    resultado = _obtener_contexto_existente_o_404(
        db,
        comercio_id=comercio_id,
        usuario_actual=usuario_actual,
    )
    return _contexto_response(resultado)


@router.get(
    "/comercios/{comercio_id}/elementos",
    response_model=list[ElementoAgendaResponse],
)
def listar_elementos_endpoint(
    comercio_id: int,
    inicio: datetime | None = Query(default=None),
    fin: datetime | None = Query(default=None),
    estado: EstadoElementoAgenda | None = Query(default=None),
    tipo: TipoElementoAgenda | None = Query(default=None),
    db: Session = Depends(get_db),
    usuario_actual: Usuario = Depends(obtener_usuario_actual),
):
    resultado = _obtener_contexto_existente_o_404(
        db,
        comercio_id=comercio_id,
        usuario_actual=usuario_actual,
    )
    try:
        filtros = ElementoAgendaFiltros(
            tipo=tipo,
            estado=estado,
            inicio=inicio,
            fin=fin,
            incluir_sin_fecha=True,
        )
        return listar_elementos_agenda(
            db,
            contexto_id=resultado.contexto.id,
            filtros=filtros,
        )
    except ValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        )
    except ContextoAgendableNoEncontradoError as exc:
        raise _traducir_error_agenda(exc)


@router.post(
    "/comercios/{comercio_id}/elementos",
    response_model=ElementoAgendaConSolapamientosResponse,
)
def crear_elemento_endpoint(
    comercio_id: int,
    payload: ElementoAgendaCreate,
    db: Session = Depends(get_db),
    usuario_actual: Usuario = Depends(obtener_usuario_actual),
):
    resultado = _obtener_contexto_existente_o_404(
        db,
        comercio_id=comercio_id,
        usuario_actual=usuario_actual,
    )

    try:
        elemento = crear_elemento_agenda(
            db,
            contexto_id=resultado.contexto.id,
            data=payload,
        )
        hay, cantidad, solapamientos = _solapamientos_response(
            db,
            contexto_id=resultado.contexto.id,
            elemento=elemento,
            elemento_id_excluir=elemento.id,
        )
        db.commit()
        return ElementoAgendaConSolapamientosResponse(
            elemento=elemento,
            hay_solapamiento=hay,
            cantidad_solapamientos=cantidad,
            solapamientos=solapamientos,
        )
    except (
        ContextoAgendableNoEncontradoError,
        ElementoAgendaNoEncontradoError,
        ContextoAgendableArchivadoError,
        AgendaElementoConflictoConcurrenciaError,
        AgendaIntervaloSolapamientoInvalidoError,
    ) as exc:
        db.rollback()
        raise _traducir_error_agenda(exc)
    except Exception:
        db.rollback()
        raise


@router.patch(
    "/comercios/{comercio_id}/elementos/{elemento_id}",
    response_model=ElementoAgendaConSolapamientosResponse,
)
def actualizar_elemento_endpoint(
    comercio_id: int,
    elemento_id: int,
    payload: ElementoAgendaUpdate,
    db: Session = Depends(get_db),
    usuario_actual: Usuario = Depends(obtener_usuario_actual),
):
    resultado = _obtener_contexto_existente_o_404(
        db,
        comercio_id=comercio_id,
        usuario_actual=usuario_actual,
    )

    try:
        elemento = actualizar_elemento_agenda(
            db,
            contexto_id=resultado.contexto.id,
            elemento_id=elemento_id,
            data=payload,
        )
        hay, cantidad, solapamientos = _solapamientos_response(
            db,
            contexto_id=resultado.contexto.id,
            elemento=elemento,
            elemento_id_excluir=elemento.id,
        )
        db.commit()
        return ElementoAgendaConSolapamientosResponse(
            elemento=elemento,
            hay_solapamiento=hay,
            cantidad_solapamientos=cantidad,
            solapamientos=solapamientos,
        )
    except (
        ContextoAgendableNoEncontradoError,
        ElementoAgendaNoEncontradoError,
        ContextoAgendableArchivadoError,
        AgendaElementoConflictoConcurrenciaError,
        AgendaIntervaloSolapamientoInvalidoError,
    ) as exc:
        db.rollback()
        raise _traducir_error_agenda(exc)
    except Exception:
        db.rollback()
        raise


@router.patch(
    "/comercios/{comercio_id}/elementos/{elemento_id}/estado",
    response_model=ElementoAgendaResponse,
)
def cambiar_estado_elemento_endpoint(
    comercio_id: int,
    elemento_id: int,
    payload: ElementoAgendaCambioEstado,
    db: Session = Depends(get_db),
    usuario_actual: Usuario = Depends(obtener_usuario_actual),
):
    resultado = _obtener_contexto_existente_o_404(
        db,
        comercio_id=comercio_id,
        usuario_actual=usuario_actual,
    )

    try:
        elemento = actualizar_elemento_agenda(
            db,
            contexto_id=resultado.contexto.id,
            elemento_id=elemento_id,
            data=ElementoAgendaUpdate(
                version_esperada=payload.version_esperada,
                estado=payload.estado,
            ),
        )
        db.commit()
        return elemento
    except (
        ContextoAgendableNoEncontradoError,
        ElementoAgendaNoEncontradoError,
        ContextoAgendableArchivadoError,
        AgendaElementoConflictoConcurrenciaError,
        AgendaIntervaloSolapamientoInvalidoError,
    ) as exc:
        db.rollback()
        raise _traducir_error_agenda(exc)
    except Exception:
        db.rollback()
        raise
