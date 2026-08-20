from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.auth import obtener_usuario_actual
from app.core.database import get_db
from app.modules.administration.schemas.administration_schemas import (
    MyAdministrativeCapabilitiesResponse,
)
from app.modules.administration.services.administrative_authorization_services import (
    list_active_administrative_capabilities,
)
from app.modules.users.models.usuarios_models import Usuario

router = APIRouter(prefix="/administracion", tags=["Administracion"])


@router.get(
    "/me/capacidades",
    response_model=MyAdministrativeCapabilitiesResponse,
)
def get_my_administrative_capabilities(
    db: Session = Depends(get_db),
    usuario_actual: Usuario = Depends(obtener_usuario_actual),
):
    capacidades = list_active_administrative_capabilities(
        db,
        usuario_id=usuario_actual.id,
    )
    return {
        "es_operador": bool(capacidades),
        "capacidades": capacidades,
    }
