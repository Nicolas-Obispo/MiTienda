"""Helpers de tests para autenticar exclusivamente mediante FeedGoSession."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Callable

import jwt
from sqlalchemy.orm import Session

from app.core.auth import crear_token_jwt_versionado
from app.core.config import settings
from app.modules.users.services.feedgo_session_services import (
    PASSWORD,
    create_feedgo_session,
)


def issue_versioned_test_token(
    session_factory: Callable[[], Session],
    *,
    usuario_id: int,
    sid: str | None = None,
) -> str:
    """Crea una sesion persistida y emite su bearer productivo versionado."""

    db = session_factory()
    try:
        session_kwargs = {
            "usuario_id": usuario_id,
            "authentication_method": PASSWORD,
            "ttl": timedelta(hours=1),
        }
        if sid is not None:
            session_kwargs["sid_factory"] = lambda: sid
        session = create_feedgo_session(db, **session_kwargs)
        token = crear_token_jwt_versionado(
            usuario_id=usuario_id,
            sid=session.id,
            issued_at=session.issued_at,
            expires_at=session.expires_at,
        )
        db.commit()
        return token
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def encode_legacy_test_token(*, usuario_id: int) -> str:
    """Fabrica un bearer legacy exclusivamente para contratos negativos."""

    return jwt.encode(
        {
            "sub": str(usuario_id),
            "exp": datetime.now(timezone.utc) + timedelta(minutes=5),
        },
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM,
    )
