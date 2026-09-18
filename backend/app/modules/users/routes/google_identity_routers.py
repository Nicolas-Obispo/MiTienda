"""Endpoints backend para Google OIDC login, signup y linking explicito."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from urllib.parse import urlencode

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response
from fastapi.responses import RedirectResponse
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.auth import crear_token_jwt_versionado, obtener_contexto_usuario_actual
from app.core.config import settings
from app.core.database import get_db
from app.modules.users.models.identity_models import FeedGoSession
from app.modules.users.schemas.google_identity_schemas import (
    GoogleAuthorizationStartRequest,
    GoogleAuthorizationStartResponse,
    GoogleLinkAuthorizationStartRequest,
    GoogleSessionExchangeRequest,
    GoogleSessionExchangeResponse,
)
from app.modules.users.services.documentos_aceptacion_services import (
    digest_documentos_obligatorios_registro,
)
from app.modules.users.services.google_identity_services import (
    GoogleIdentityError,
    google_signup_collision_exists,
    process_google_identity,
)
from app.modules.users.services.account_action_rate_limit_services import (
    record_authentication_method_management,
    record_google_oauth_authorization,
)
from app.modules.users.services.authentication_method_services import (
    AuthenticationMethodError,
    ensure_google_link_available,
    google_link_collision_exists,
    link_google_identity,
    require_recent_reauthentication,
)
from app.modules.users.services.google_oidc_services import (
    GOOGLE_PROVIDER,
    GoogleOidcError,
    GoogleOidcOwner,
    google_oidc_configuration,
)
from app.modules.users.services.oauth_authorization_transaction_services import (
    OAUTH_PURPOSE_LOGIN,
    OAUTH_PURPOSE_LINK,
    OAUTH_PURPOSE_SIGNUP,
    OAuthAuthorizationTransactionError,
    claim_oauth_authorization_transaction_by_state,
    create_oauth_authorization_transaction,
)
from app.modules.users.services.oauth_session_delivery_services import (
    AUTHENTICATION_UNAVAILABLE,
    OAuthSessionDeliveryError,
    create_oauth_session_delivery,
    consume_oauth_session_delivery,
)


router = APIRouter(prefix="/usuarios/google", tags=["Google identity"])
NO_STORE = {"Cache-Control": "private, no-store"}
ALLOWED_PURPOSES = frozenset(
    {OAUTH_PURPOSE_LOGIN, OAUTH_PURPOSE_SIGNUP, OAUTH_PURPOSE_LINK}
)


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def build_google_oidc_owner() -> GoogleOidcOwner:
    return GoogleOidcOwner(google_oidc_configuration())


def _safe_http_error(status_code: int, code: str) -> HTTPException:
    return HTTPException(
        status_code=status_code,
        detail={"public_code": code},
        headers=NO_STORE,
    )


def _authentication_method_http_error(exc: AuthenticationMethodError) -> HTTPException:
    status_by_code = {
        "recent_reauthentication_required": 403,
        "authentication_method_already_exists": 409,
        "google_link_unavailable": 409,
        "authentication_method_operation_unavailable": 409,
    }
    return _safe_http_error(status_by_code.get(exc.code, 409), exc.code)


@router.post(
    "/authorization",
    response_model=GoogleAuthorizationStartResponse,
)
async def start_google_authorization(
    payload: GoogleAuthorizationStartRequest,
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
):
    response.headers.update(NO_STORE)
    client_key = request.client.host if request.client else "unknown"
    try:
        google_oidc_configuration()
        owner = build_google_oidc_owner()
    except GoogleOidcError:
        raise _safe_http_error(503, "google_identity_unavailable") from None
    if payload.purpose == OAUTH_PURPOSE_SIGNUP:
        if payload.acepta_terminos is not True or payload.acepta_privacidad is not True:
            raise _safe_http_error(400, "google_signup_legal_acceptance_required")
        legal_digest = digest_documentos_obligatorios_registro()
        legal_accepted_at = utc_now()
    else:
        if payload.acepta_terminos or payload.acepta_privacidad:
            raise _safe_http_error(400, "google_oauth_purpose_invalid")
        legal_digest = None
        legal_accepted_at = None

    rate_limit = record_google_oauth_authorization(
        db,
        client_host=client_key,
        limit_per_hour=settings.GOOGLE_OAUTH_PUBLIC_RATE_LIMIT_PER_HOUR,
    )
    # El bucket es una UoW independiente: una caida del provider no debe
    # revertirlo ni mantener su lock durante discovery/HTTP externo.
    db.commit()
    if not rate_limit.allowed:
        raise HTTPException(
            status_code=429,
            detail={"public_code": "google_oauth_rate_limited"},
            headers=NO_STORE
            | {"Retry-After": str(rate_limit.retry_after_seconds or 3600)},
        )

    try:
        material = create_oauth_authorization_transaction(
            db,
            provider=GOOGLE_PROVIDER,
            purpose=payload.purpose,
            return_to=payload.return_to,
            legal_document_set_digest=legal_digest,
            legal_accepted_at=legal_accepted_at,
            ttl=timedelta(seconds=settings.GOOGLE_OAUTH_TRANSACTION_TTL_SECONDS),
        )
        authorization_url = await owner.create_authorization_url(material)
        db.commit()
    except OAuthAuthorizationTransactionError:
        db.rollback()
        raise _safe_http_error(400, "google_authorization_invalid") from None
    except GoogleOidcError as exc:
        db.rollback()
        status = 503 if exc.code in {
            "google_identity_disabled",
            "google_oidc_configuration_invalid",
            "google_oidc_provider_unavailable",
        } else 400
        raise _safe_http_error(status, "google_identity_unavailable") from None
    except Exception:
        db.rollback()
        raise
    return GoogleAuthorizationStartResponse(
        authorization_url=authorization_url,
        expires_at=material.expires_at,
    )


@router.post(
    "/link/authorization",
    response_model=GoogleAuthorizationStartResponse,
)
async def start_google_link_authorization(
    payload: GoogleLinkAuthorizationStartRequest,
    response: Response,
    db: Session = Depends(get_db),
    auth_context=Depends(obtener_contexto_usuario_actual),
):
    response.headers.update(NO_STORE)
    usuario_id = auth_context.usuario.id
    sid = (
        auth_context.token.sid
        if auth_context.token.contract == "versioned"
        else None
    )
    try:
        google_oidc_configuration()
        owner = build_google_oidc_owner()
        require_recent_reauthentication(
            db,
            usuario_id=usuario_id,
            feedgo_session_id=sid,
        )
        ensure_google_link_available(db, usuario_id=usuario_id)
        rate_limit = record_authentication_method_management(
            db,
            usuario_id=usuario_id,
            limit_per_hour=settings.GOOGLE_OAUTH_LINK_RATE_LIMIT_PER_HOUR,
        )
        db.commit()
        if not rate_limit.allowed:
            raise HTTPException(
                status_code=429,
                detail={"public_code": "authentication_method_rate_limited"},
                headers=NO_STORE
                | {"Retry-After": str(rate_limit.retry_after_seconds or 3600)},
            )

        # Revalida despues de la UoW del rate limit para cerrar TOCTOU.
        require_recent_reauthentication(
            db,
            usuario_id=usuario_id,
            feedgo_session_id=sid,
        )
        ensure_google_link_available(db, usuario_id=usuario_id)
        material = create_oauth_authorization_transaction(
            db,
            provider=GOOGLE_PROVIDER,
            purpose=OAUTH_PURPOSE_LINK,
            usuario_id=usuario_id,
            feedgo_session_id=sid,
            return_to=payload.return_to,
            ttl=timedelta(seconds=settings.GOOGLE_OAUTH_TRANSACTION_TTL_SECONDS),
        )
        authorization_url = await owner.create_authorization_url(material)
        db.commit()
    except AuthenticationMethodError as exc:
        db.rollback()
        raise _authentication_method_http_error(exc) from None
    except OAuthAuthorizationTransactionError:
        db.rollback()
        raise _safe_http_error(400, "google_authorization_invalid") from None
    except GoogleOidcError:
        db.rollback()
        raise _safe_http_error(503, "google_identity_unavailable") from None
    except HTTPException:
        raise
    except Exception:
        db.rollback()
        raise
    return GoogleAuthorizationStartResponse(
        authorization_url=authorization_url,
        expires_at=material.expires_at,
    )


@router.get("/callback")
async def google_callback(
    state: str = Query(min_length=20, max_length=256),
    code: str | None = Query(default=None, min_length=1, max_length=2048),
    error: str | None = Query(default=None, max_length=128),
    db: Session = Depends(get_db),
):
    try:
        configuration = google_oidc_configuration()
        claim = claim_oauth_authorization_transaction_by_state(
            db,
            state=state,
            provider=GOOGLE_PROVIDER,
            allowed_purposes=ALLOWED_PURPOSES,
        )
        db.commit()
    except OAuthAuthorizationTransactionError:
        db.commit()
        raise _safe_http_error(400, "google_callback_invalid") from None
    except (GoogleOidcError, GoogleIdentityError):
        db.rollback()
        raise _safe_http_error(503, "google_identity_unavailable") from None

    if error is not None or code is None:
        raise _safe_http_error(400, "google_callback_invalid")
    try:
        identity = await build_google_oidc_owner().exchange_and_validate(
            code=code,
            pkce_verifier=claim.pkce_verifier,
            expected_nonce_digest=claim.nonce_digest,
        )
        if claim.purpose == OAUTH_PURPOSE_LINK:
            link_google_identity(db, claim=claim, identity=identity)
            db.commit()
            destination = (
                f"{configuration.public_base_url}{claim.return_to or '/perfil'}"
            )
            return RedirectResponse(destination, status_code=303, headers=NO_STORE)
        result = process_google_identity(
            db,
            claim=claim,
            identity=identity,
            session_ttl=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
            result_ttl=timedelta(
                seconds=configuration.result_handle_ttl_seconds
            ),
        )
        db.commit()
    except AuthenticationMethodError as exc:
        db.rollback()
        raise _authentication_method_http_error(exc) from None
    except (GoogleOidcError, GoogleIdentityError):
        db.rollback()
        raise _safe_http_error(400, "google_callback_invalid") from None
    except IntegrityError:
        # UNIQUE(provider, subject) y email canonical deciden carreras. Todos
        # los perdedores reciben el mismo resultado opaco, sin enumeracion.
        db.rollback()
        if claim.purpose == OAUTH_PURPOSE_LINK:
            if (
                claim.usuario_id is None
                or not google_link_collision_exists(
                    db,
                    usuario_id=claim.usuario_id,
                    provider_subject=identity.subject,
                )
            ):
                raise
            raise _safe_http_error(409, "google_link_unavailable") from None
        if claim.purpose != OAUTH_PURPOSE_SIGNUP or not google_signup_collision_exists(
            db, identity=identity
        ):
            raise
        delivery = create_oauth_session_delivery(
            db,
            transaction_id=claim.transaction_id,
            outcome=AUTHENTICATION_UNAVAILABLE,
            return_to=claim.return_to,
            ttl=timedelta(seconds=configuration.result_handle_ttl_seconds),
        )
        db.commit()
        delivery_handle = delivery.handle
    except Exception:
        db.rollback()
        raise
    else:
        delivery_handle = result.delivery.handle

    destination = (
        f"{configuration.public_base_url}{configuration.frontend_result_path}?"
        f"{urlencode({'handle': delivery_handle})}"
    )
    return RedirectResponse(destination, status_code=303, headers=NO_STORE)


@router.post(
    "/session",
    response_model=GoogleSessionExchangeResponse,
)
def exchange_google_session(
    payload: GoogleSessionExchangeRequest,
    response: Response,
    db: Session = Depends(get_db),
):
    response.headers.update(NO_STORE)
    try:
        google_oidc_configuration()
    except GoogleOidcError:
        raise _safe_http_error(503, "google_identity_unavailable") from None
    try:
        delivery = consume_oauth_session_delivery(db, handle=payload.handle)
        if delivery.outcome == AUTHENTICATION_UNAVAILABLE:
            db.commit()
            return GoogleSessionExchangeResponse(
                status="action_required",
                return_to=delivery.return_to,
            )
        feedgo_session = db.get(FeedGoSession, delivery.feedgo_session_id)
        if feedgo_session is None:
            raise OAuthSessionDeliveryError("invalid_result_handle")
        token = crear_token_jwt_versionado(
            usuario_id=delivery.usuario_id,
            sid=feedgo_session.id,
            issued_at=feedgo_session.issued_at,
            expires_at=feedgo_session.expires_at,
        )
        db.commit()
    except OAuthSessionDeliveryError:
        db.commit()
        raise _safe_http_error(400, "google_session_result_invalid") from None
    return GoogleSessionExchangeResponse(
        status="authenticated",
        token=token,
        usuario_id=delivery.usuario_id,
        return_to=delivery.return_to,
    )
