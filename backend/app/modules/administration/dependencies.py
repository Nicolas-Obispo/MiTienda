from collections.abc import Callable

from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.auth import obtener_usuario_actual
from app.core.database import get_db
from app.modules.administration.capabilities import validate_administrative_capability
from app.modules.administration.services.administrative_authorization_services import (
    user_has_administrative_capability,
)
from app.modules.users.models.usuarios_models import Usuario


def require_administrative_capability(
    capability: str,
) -> Callable[..., Usuario]:
    required_capability = validate_administrative_capability(capability)

    def dependency(
        db: Session = Depends(get_db),
        usuario_actual: Usuario = Depends(obtener_usuario_actual),
    ) -> Usuario:
        if not user_has_administrative_capability(
            db,
            usuario_id=usuario_actual.id,
            capability=required_capability,
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No autorizado",
            )
        return usuario_actual

    return dependency
