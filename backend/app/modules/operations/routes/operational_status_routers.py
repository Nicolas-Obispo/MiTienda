from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.modules.administration.capabilities import OPERATIONS_STATUS_READ
from app.modules.administration.dependencies import require_administrative_capability
from app.modules.operations.schemas.operational_status_schemas import OperationalStatusResponse, ResourceIntegrityResponse
from app.modules.operations.services.operational_status_services import (
    OperationalResourceNotFoundError,
    build_operational_status,
    inspect_resource_integrity,
)


router = APIRouter(prefix="/administracion/operaciones", tags=["Administracion - Operaciones"])
status_reader = require_administrative_capability(OPERATIONS_STATUS_READ)


@router.get("/estado", response_model=OperationalStatusResponse)
def get_operational_status(_operator=Depends(status_reader)):
    return build_operational_status()


@router.get("/recursos/{resource_type}/{resource_id}/integridad", response_model=ResourceIntegrityResponse)
def get_resource_integrity(
    resource_type: str,
    resource_id: int,
    db: Session = Depends(get_db),
    _operator=Depends(status_reader),
):
    try:
        return inspect_resource_integrity(db, resource_type=resource_type, resource_id=resource_id)
    except OperationalResourceNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Recurso no encontrado") from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail="Tipo de recurso no soportado") from exc
