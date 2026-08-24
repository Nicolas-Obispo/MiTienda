from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.orm import Session

from app.core.auth import obtener_usuario_actual
from app.core.database import get_db
from app.modules.moderation.schemas.contenido_denuncias_schemas import (
    ContenidoDenunciaAdminDetailResponse,
    ContenidoDenunciaAdminListResponse,
    ContenidoDenunciaCreate,
    ContenidoDenunciaResponse,
    ModerationDecisionCreate,
    ModerationDecisionResponse,
)
from app.modules.moderation.services.contenido_denuncias_services import (
    CursorDenunciasInvalidoError,
    DenunciaNoEncontradaError,
    RecursoDenunciableNoEncontradoError,
    crear_denuncia_contenido,
    listar_denuncias_administrativas,
    obtener_denuncia_administrativa,
    obtener_disponibilidad_actual_recurso_denunciado,
)
from app.modules.administration.capabilities import MODERATION_DECISIONS_WRITE, MODERATION_REPORTS_READ
from app.modules.administration.dependencies import require_administrative_capability
from app.modules.moderation.constants import (
    ESTADO_DENUNCIA_RECIBIDA,
    ESTADOS_DENUNCIA,
    MOTIVOS_DENUNCIA,
    RECURSOS_DENUNCIABLES,
)


router = APIRouter(prefix="/moderacion", tags=["Moderacion"])


def _validate_admin_filters(
    *,
    estado: str | None,
    recurso_tipo: str | None,
    recurso_id: int | None,
    motivo: str | None,
    desde: datetime | None,
    hasta: datetime | None,
) -> None:
    if estado is not None and estado not in ESTADOS_DENUNCIA:
        raise HTTPException(status_code=422, detail="estado invalido")
    if recurso_tipo is not None and recurso_tipo not in RECURSOS_DENUNCIABLES:
        raise HTTPException(status_code=422, detail="recurso_tipo invalido")
    if motivo is not None and motivo not in MOTIVOS_DENUNCIA:
        raise HTTPException(status_code=422, detail="motivo invalido")
    if recurso_id is not None and recurso_tipo is None:
        raise HTTPException(
            status_code=422,
            detail="recurso_tipo es obligatorio al filtrar por recurso_id",
        )
    if desde is not None and hasta is not None and desde >= hasta:
        raise HTTPException(status_code=422, detail="rango temporal invalido")


@router.get(
    "/denuncias",
    response_model=ContenidoDenunciaAdminListResponse,
)
def listar_denuncias_endpoint(
    limit: int = Query(default=20, ge=1, le=50),
    cursor: str | None = Query(default=None, min_length=1, max_length=500),
    estado: str | None = None,
    recurso_tipo: str | None = None,
    recurso_id: int | None = Query(default=None, gt=0),
    motivo: str | None = None,
    desde: datetime | None = None,
    hasta: datetime | None = None,
    db: Session = Depends(get_db),
    _operador=Depends(
        require_administrative_capability(MODERATION_REPORTS_READ)
    ),
):
    _validate_admin_filters(
        estado=estado,
        recurso_tipo=recurso_tipo,
        recurso_id=recurso_id,
        motivo=motivo,
        desde=desde,
        hasta=hasta,
    )
    try:
        pagina = listar_denuncias_administrativas(
            db=db,
            limit=limit,
            cursor=cursor,
            estado=estado,
            recurso_tipo=recurso_tipo,
            recurso_id=recurso_id,
            motivo=motivo,
            desde=desde,
            hasta=hasta,
        )
    except CursorDenunciasInvalidoError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    return {
        "items": [
            {
                "id": denuncia.id,
                "recurso_tipo": denuncia.recurso_tipo,
                "recurso_id": denuncia.recurso_id,
                "motivo": denuncia.motivo,
                "estado": denuncia.estado,
                "creado_en": denuncia.creado_en,
                "tiene_detalle": bool(denuncia.detalle),
            }
            for denuncia in pagina.items
        ],
        "next_cursor": pagina.next_cursor,
        "has_more": pagina.has_more,
    }


@router.get(
    "/denuncias/{denuncia_id}",
    response_model=ContenidoDenunciaAdminDetailResponse,
)
def obtener_denuncia_endpoint(
    denuncia_id: int,
    db: Session = Depends(get_db),
    _operador=Depends(
        require_administrative_capability(MODERATION_REPORTS_READ)
    ),
):
    try:
        denuncia = obtener_denuncia_administrativa(
            db=db,
            denuncia_id=denuncia_id,
        )
    except DenunciaNoEncontradaError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    recurso_actual = obtener_disponibilidad_actual_recurso_denunciado(
        db=db,
        recurso_tipo=denuncia.recurso_tipo,
        recurso_id=denuncia.recurso_id,
    )
    return {
        "id": denuncia.id,
        "recurso_tipo": denuncia.recurso_tipo,
        "recurso_id": denuncia.recurso_id,
        "motivo": denuncia.motivo,
        "detalle": denuncia.detalle,
        "estado": denuncia.estado,
        "creado_en": denuncia.creado_en,
        "version": denuncia.version,
        "recurso_actual": {
            "disponible": recurso_actual.disponible,
            "ruta_publica": recurso_actual.ruta_publica,
            "moderation_hidden": recurso_actual.moderation_hidden,
            "moderation_revision": recurso_actual.moderation_revision,
            "moderation_hidden_by_decision_id": recurso_actual.moderation_hidden_by_decision_id,
        },
    }


@router.get(
    "/denuncias/{denuncia_id}/decisiones",
    response_model=list[ModerationDecisionResponse],
)
def listar_decisiones_endpoint(
    denuncia_id: int,
    db: Session = Depends(get_db),
    _operador=Depends(require_administrative_capability(MODERATION_REPORTS_READ)),
):
    from app.modules.moderation.services.moderation_decisions_services import (
        ModerationDecisionNotFoundError,
        list_moderation_decisions,
    )
    try:
        return list_moderation_decisions(db=db, denuncia_id=denuncia_id)
    except ModerationDecisionNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post(
    "/denuncias/{denuncia_id}/decisiones",
    response_model=ModerationDecisionResponse,
    status_code=status.HTTP_201_CREATED,
)
def crear_decision_endpoint(
    denuncia_id: int,
    payload: ModerationDecisionCreate,
    db: Session = Depends(get_db),
    operador=Depends(require_administrative_capability(MODERATION_DECISIONS_WRITE)),
):
    from app.modules.moderation.services.moderation_decisions_services import (
        ModerationDecisionConflictError,
        ModerationDecisionNotFoundError,
        ModerationResourceNotFoundError,
        create_moderation_decision,
    )
    try:
        return create_moderation_decision(
            db=db,
            denuncia_id=denuncia_id,
            operador_usuario_id=operador.id,
            payload=payload,
        )
    except (ModerationDecisionNotFoundError, ModerationResourceNotFoundError) as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ModerationDecisionConflictError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.post(
    "/denuncias",
    response_model=ContenidoDenunciaResponse,
    status_code=status.HTTP_201_CREATED,
)
def crear_denuncia_endpoint(
    payload: ContenidoDenunciaCreate,
    response: Response,
    db: Session = Depends(get_db),
    usuario_actual=Depends(obtener_usuario_actual),
):
    try:
        denuncia, creada = crear_denuncia_contenido(
            db=db,
            payload=payload,
            usuario=usuario_actual,
        )
    except RecursoDenunciableNoEncontradoError:
        raise HTTPException(status_code=404, detail="Recurso no denunciable")

    if not creada:
        response.status_code = status.HTTP_200_OK

    return denuncia
