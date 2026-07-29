"""
Validaciones de ownership para recursos pertenecientes a Comercio.

Esta capa no conoce HTTP, roles ni dominios consumidores.
"""

from sqlalchemy.orm import Session

from app.modules.spaces.models.comercios_models import Comercio
from app.modules.users.models.usuarios_models import Usuario


class ComercioNoEncontradoError(ValueError):
    pass


class ComercioUsuarioNoPropietarioError(PermissionError):
    pass


def obtener_comercio_propio_o_error(
    db: Session,
    *,
    comercio_id: int,
    usuario_autenticado: Usuario,
) -> Comercio:
    comercio = db.query(Comercio).filter(Comercio.id == comercio_id).first()
    if comercio is None:
        raise ComercioNoEncontradoError("Comercio no encontrado")

    if comercio.usuario_id != usuario_autenticado.id:
        raise ComercioUsuarioNoPropietarioError(
            "No tenes permiso para administrar este comercio"
        )

    return comercio
