from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.modules.moderation.models.contenido_denuncias_models import (
    ContenidoDenuncia,
)
from app.modules.moderation.constants import (
    ESTADO_DENUNCIA_RECIBIDA,
    RECURSO_TIPO_COMERCIO,
    RECURSO_TIPO_HISTORIA,
    RECURSO_TIPO_PUBLICACION,
)
from app.modules.posts.models.publicaciones_models import Publicacion
from app.modules.spaces.models.comercios_models import Comercio
from app.modules.stories.models.historias_models import Historia
from app.modules.users.models.usuarios_models import Usuario


class RecursoDenunciableNoEncontradoError(Exception):
    pass


def crear_denuncia_contenido(
    *,
    db: Session,
    payload,
    usuario: Usuario,
) -> tuple[ContenidoDenuncia, bool]:
    _validar_recurso_denunciable(
        db=db,
        recurso_tipo=payload.recurso_tipo,
        recurso_id=payload.recurso_id,
    )

    denuncia_existente = _obtener_denuncia_existente(
        db=db,
        usuario_id=usuario.id,
        recurso_tipo=payload.recurso_tipo,
        recurso_id=payload.recurso_id,
        motivo=payload.motivo,
    )
    if denuncia_existente is not None:
        return denuncia_existente, False

    denuncia = ContenidoDenuncia(
        usuario_id=usuario.id,
        recurso_tipo=payload.recurso_tipo,
        recurso_id=payload.recurso_id,
        motivo=payload.motivo,
        detalle=payload.detalle,
        estado=ESTADO_DENUNCIA_RECIBIDA,
    )

    try:
        db.add(denuncia)
        db.commit()
        db.refresh(denuncia)
    except IntegrityError:
        db.rollback()
        denuncia_existente = _obtener_denuncia_existente(
            db=db,
            usuario_id=usuario.id,
            recurso_tipo=payload.recurso_tipo,
            recurso_id=payload.recurso_id,
            motivo=payload.motivo,
        )
        if denuncia_existente is not None:
            return denuncia_existente, False
        raise
    except Exception:
        db.rollback()
        raise

    return denuncia, True


def _obtener_denuncia_existente(
    *,
    db: Session,
    usuario_id: int,
    recurso_tipo: str,
    recurso_id: int,
    motivo: str,
) -> ContenidoDenuncia | None:
    return (
        db.query(ContenidoDenuncia)
        .filter(
            ContenidoDenuncia.usuario_id == usuario_id,
            ContenidoDenuncia.recurso_tipo == recurso_tipo,
            ContenidoDenuncia.recurso_id == recurso_id,
            ContenidoDenuncia.motivo == motivo,
        )
        .first()
    )


def _validar_recurso_denunciable(
    *,
    db: Session,
    recurso_tipo: str,
    recurso_id: int,
) -> None:
    if recurso_tipo == RECURSO_TIPO_COMERCIO:
        recurso = (
            db.query(Comercio)
            .filter(
                Comercio.id == recurso_id,
                Comercio.activo.is_(True),
            )
            .first()
        )
    elif recurso_tipo == RECURSO_TIPO_PUBLICACION:
        recurso = (
            db.query(Publicacion)
            .join(Comercio, Publicacion.comercio_id == Comercio.id)
            .filter(
                Publicacion.id == recurso_id,
                Publicacion.is_activa.is_(True),
                Comercio.activo.is_(True),
            )
            .first()
        )
    elif recurso_tipo == RECURSO_TIPO_HISTORIA:
        recurso = (
            db.query(Historia)
            .join(Comercio, Historia.comercio_id == Comercio.id)
            .filter(
                Historia.id == recurso_id,
                Historia.is_activa.is_(True),
                Comercio.activo.is_(True),
            )
            .first()
        )
    else:
        recurso = None

    if recurso is None:
        raise RecursoDenunciableNoEncontradoError()
