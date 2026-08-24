import base64
import binascii
import json
from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import and_, or_
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
from app.modules.notifications.services.operational_notification_services import (
    enqueue_report_created,
)


class RecursoDenunciableNoEncontradoError(Exception):
    pass


class DenunciaNoEncontradaError(ValueError):
    pass


class CursorDenunciasInvalidoError(ValueError):
    pass


@dataclass(frozen=True)
class PaginaDenuncias:
    items: list[ContenidoDenuncia]
    next_cursor: str | None
    has_more: bool


@dataclass(frozen=True)
class RecursoDenunciadoActual:
    disponible: bool
    ruta_publica: str | None
    moderation_hidden: bool
    moderation_revision: int
    moderation_hidden_by_decision_id: int | None


def _encode_denuncias_cursor(denuncia: ContenidoDenuncia) -> str:
    payload = json.dumps(
        {
            "v": 1,
            "creado_en": denuncia.creado_en.isoformat(),
            "id": denuncia.id,
        },
        separators=(",", ":"),
    ).encode("utf-8")
    return base64.urlsafe_b64encode(payload).decode("ascii").rstrip("=")


def _decode_denuncias_cursor(cursor: str) -> tuple[datetime, int]:
    try:
        padding = "=" * (-len(cursor) % 4)
        payload = json.loads(
            base64.b64decode(
                cursor + padding,
                altchars=b"-_",
                validate=True,
            ).decode("utf-8")
        )
        if payload.get("v") != 1:
            raise ValueError
        creado_en = datetime.fromisoformat(payload["creado_en"])
        denuncia_id = int(payload["id"])
        if denuncia_id <= 0:
            raise ValueError
        return creado_en, denuncia_id
    except (
        binascii.Error,
        KeyError,
        TypeError,
        ValueError,
        UnicodeDecodeError,
        json.JSONDecodeError,
    ) as exc:
        raise CursorDenunciasInvalidoError("Cursor de denuncias invalido") from exc


def listar_denuncias_administrativas(
    *,
    db: Session,
    limit: int,
    cursor: str | None = None,
    estado: str | None = None,
    recurso_tipo: str | None = None,
    recurso_id: int | None = None,
    motivo: str | None = None,
    desde: datetime | None = None,
    hasta: datetime | None = None,
) -> PaginaDenuncias:
    query = db.query(ContenidoDenuncia)

    if estado is not None:
        query = query.filter(ContenidoDenuncia.estado == estado)
    if recurso_tipo is not None:
        query = query.filter(ContenidoDenuncia.recurso_tipo == recurso_tipo)
    if recurso_id is not None:
        query = query.filter(ContenidoDenuncia.recurso_id == recurso_id)
    if motivo is not None:
        query = query.filter(ContenidoDenuncia.motivo == motivo)
    if desde is not None:
        query = query.filter(ContenidoDenuncia.creado_en >= desde)
    if hasta is not None:
        query = query.filter(ContenidoDenuncia.creado_en < hasta)
    if cursor is not None:
        cursor_created_at, cursor_id = _decode_denuncias_cursor(cursor)
        query = query.filter(
            or_(
                ContenidoDenuncia.creado_en < cursor_created_at,
                and_(
                    ContenidoDenuncia.creado_en == cursor_created_at,
                    ContenidoDenuncia.id < cursor_id,
                ),
            )
        )

    rows = (
        query.order_by(
            ContenidoDenuncia.creado_en.desc(),
            ContenidoDenuncia.id.desc(),
        )
        .limit(limit + 1)
        .all()
    )
    has_more = len(rows) > limit
    items = rows[:limit]
    next_cursor = (
        _encode_denuncias_cursor(items[-1])
        if has_more and items
        else None
    )
    return PaginaDenuncias(
        items=items,
        next_cursor=next_cursor,
        has_more=has_more,
    )


def obtener_denuncia_administrativa(
    *,
    db: Session,
    denuncia_id: int,
) -> ContenidoDenuncia:
    denuncia = db.get(ContenidoDenuncia, denuncia_id)
    if denuncia is None:
        raise DenunciaNoEncontradaError("Denuncia no encontrada")
    return denuncia


def obtener_disponibilidad_actual_recurso_denunciado(
    *,
    db: Session,
    recurso_tipo: str,
    recurso_id: int,
) -> RecursoDenunciadoActual:
    recurso = None
    if recurso_tipo == RECURSO_TIPO_COMERCIO:
        recurso = db.get(Comercio, recurso_id)
        disponible = bool(recurso and recurso.activo and not recurso.moderation_hidden)
        ruta_publica = f"/comercios/{recurso_id}" if disponible else None
    elif recurso_tipo == RECURSO_TIPO_PUBLICACION:
        recurso = (
            db.query(Publicacion)
            .join(Comercio, Publicacion.comercio_id == Comercio.id)
            .filter(
                Publicacion.id == recurso_id,
            )
            .first()
        )
        disponible = bool(recurso and recurso.is_activa and not recurso.moderation_hidden and recurso.comercio.activo and not recurso.comercio.moderation_hidden)
        ruta_publica = f"/publicaciones/{recurso_id}" if disponible else None
    elif recurso_tipo == RECURSO_TIPO_HISTORIA:
        recurso = (
            db.query(Historia)
            .join(Comercio, Historia.comercio_id == Comercio.id)
            .filter(
                Historia.id == recurso_id,
            )
            .first()
        )
        disponible = bool(recurso and recurso.is_activa and not recurso.moderation_hidden and recurso.comercio.activo and not recurso.comercio.moderation_hidden)
        # El frontend actual no posee una ruta publica de detalle de Historia.
        ruta_publica = None
    else:
        disponible = False
        ruta_publica = None

    return RecursoDenunciadoActual(
        disponible=disponible,
        ruta_publica=ruta_publica,
        moderation_hidden=bool(recurso.moderation_hidden) if recurso else False,
        moderation_revision=int(recurso.moderation_revision or 0) if recurso else 0,
        moderation_hidden_by_decision_id=recurso.moderation_hidden_by_decision_id if recurso else None,
    )


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
        db.flush()
        enqueue_report_created(db=db, report=denuncia)
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
                Comercio.moderation_hidden.is_(False),
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
                Publicacion.moderation_hidden.is_(False),
                Comercio.activo.is_(True),
                Comercio.moderation_hidden.is_(False),
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
                Historia.moderation_hidden.is_(False),
                Comercio.activo.is_(True),
                Comercio.moderation_hidden.is_(False),
            )
            .first()
        )
    else:
        recurso = None

    if recurso is None:
        raise RecursoDenunciableNoEncontradoError()
