from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.modules.administration.capabilities import OPERATIONS_INCIDENTS_MANAGE
from app.modules.administration.dependencies import require_administrative_capability
from app.modules.incidents.constants import SEVERITIES, STATUSES
from app.modules.incidents.schemas.operational_incidents_schemas import (
    OperationalIncidentAction, OperationalIncidentActionResponse,
    OperationalIncidentCreate, OperationalIncidentEventResponse,
    OperationalIncidentListResponse, OperationalIncidentResponse,
)
from app.modules.incidents.services.operational_incidents_services import (
    IncidentConflictError, IncidentNotFoundError, IncidentOwnerInvalidError,
    apply_incident_action, create_incident, get_incident, list_incident_events,
    list_incidents,
)

router = APIRouter(prefix="/administracion/incidentes", tags=["Incidentes operativos"])
operator_dependency = require_administrative_capability(OPERATIONS_INCIDENTS_MANAGE)


@router.post("", response_model=OperationalIncidentActionResponse, status_code=status.HTTP_201_CREATED)
def open_incident(payload: OperationalIncidentCreate, response: Response, db: Session = Depends(get_db), operator=Depends(operator_dependency)):
    try:
        incident, event, created = create_incident(db=db, actor_usuario_id=operator.id, payload=payload)
    except IncidentOwnerInvalidError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except IncidentConflictError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    if not created: response.status_code = status.HTTP_200_OK
    return {"incident": incident, "event": event}


@router.get("", response_model=OperationalIncidentListResponse)
def get_incidents(
    limit: int = Query(default=20, ge=1, le=100), cursor: int | None = Query(default=None, gt=0),
    incident_status: str | None = Query(default=None, alias="status"), severity: str | None = None,
    owner_usuario_id: int | None = Query(default=None, gt=0), db: Session = Depends(get_db),
    _operator=Depends(operator_dependency),
):
    if incident_status is not None and incident_status not in STATUSES: raise HTTPException(status_code=422, detail="status invalido")
    if severity is not None and severity not in SEVERITIES: raise HTTPException(status_code=422, detail="severity invalida")
    items, next_cursor = list_incidents(db=db, limit=limit, cursor=cursor, status=incident_status, severity=severity, owner_usuario_id=owner_usuario_id)
    return {"items": items, "next_cursor": next_cursor}


@router.get("/{public_id}", response_model=OperationalIncidentResponse)
def get_incident_detail(public_id: str, db: Session = Depends(get_db), _operator=Depends(operator_dependency)):
    try: return get_incident(db=db, public_id=public_id)
    except IncidentNotFoundError as exc: raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/{public_id}/eventos", response_model=list[OperationalIncidentEventResponse])
def get_incident_timeline(public_id: str, db: Session = Depends(get_db), _operator=Depends(operator_dependency)):
    try: incident = get_incident(db=db, public_id=public_id)
    except IncidentNotFoundError as exc: raise HTTPException(status_code=404, detail=str(exc)) from exc
    return list_incident_events(db=db, incident_id=incident.id)


@router.post("/{public_id}/acciones", response_model=OperationalIncidentActionResponse, status_code=status.HTTP_201_CREATED)
def act_on_incident(public_id: str, payload: OperationalIncidentAction, db: Session = Depends(get_db), operator=Depends(operator_dependency)):
    try:
        incident, event = apply_incident_action(db=db, public_id=public_id, actor_usuario_id=operator.id, payload=payload)
        return {"incident": incident, "event": event}
    except IncidentNotFoundError as exc: raise HTTPException(status_code=404, detail=str(exc)) from exc
    except IncidentOwnerInvalidError as exc: raise HTTPException(status_code=422, detail=str(exc)) from exc
    except IncidentConflictError as exc: raise HTTPException(status_code=409, detail=str(exc)) from exc
