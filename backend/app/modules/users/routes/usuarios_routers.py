"""
usuarios_routers.py
-------------------
Rutas HTTP relacionadas a Usuarios.
"""

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from sqlalchemy.orm import Session

# DB
from app.core.database import get_db

# Schemas
from app.modules.users.schemas.usuarios_schemas import (
    UsuarioCreate,
    UsuarioLogin,
    UsuarioResponse,
    UsuarioMeResponse,
    UsuarioPublicResponse,
    UsuarioOnboarding,
    UsuarioPerfilUpdate,
    UsuarioCambioModo,
    UsuarioAvatarUpdate,  # ETAPA 49
    DocumentoPublicoVigenteResponse,
    EmailAvailabilityRequest,
    EmailAvailabilityResponse,
    EmailVerificationConfirmRequest,
    EmailVerificationResponse,
    UsuarioRegistrationResponse,
    PasswordRecoveryRequest,
    PasswordRecoveryResponse,
    PasswordResetRequest,
    PasswordResetResponse,
    AuthenticatedPasswordChangeRequest,
    AuthenticatedPasswordChangeResponse,
    PhoneVerificationIssueResponse,
    PhoneVerificationConfirmRequest,
    PhoneVerificationConfirmResponse,
)
from app.modules.users.services.documentos_aceptacion_services import (
    listar_documentos_publicos_vigentes,
)
from app.modules.users.services.commercial_capabilities_services import (
    derive_commercial_readiness,
)
from app.modules.users.services.phone_verification_services import (
    PhoneVerificationError,
    confirm_phone_challenge,
    issue_phone_challenge,
)
from app.modules.users.routes.local_phone_otp_mailbox_routers import (
    get_local_phone_otp_mailbox,
    require_local_phone_otp_mailbox,
)

# Autenticación y seguridad
from fastapi.security import HTTPAuthorizationCredentials
from app.core.auth import (
    obtener_usuario_actual,
    obtener_contexto_usuario_actual,
    crear_token_jwt_versionado,
    bearer_scheme,
    validar_token_para_logout,
)
from datetime import datetime, timedelta
from app.core.config import settings

# Modelo para logout
from app.modules.users.models.tokens_models import TokenRevocado

# Services
from app.modules.users.services.usuarios_services import (
    crear_usuario,
    autenticar_usuario,
    obtener_usuario_por_id,
    actualizar_perfil_usuario,
    completar_onboarding_usuario,
    cambiar_modo_usuario,
)
from app.modules.users.services.email_availability import (
    email_availability_rate_limiter,
    is_email_available,
)
from app.modules.users.services.email_verification_services import (
    EmailVerificationError,
    confirm_email_verification,
    send_email_verification,
    send_registration_verification,
)
from app.modules.users.services.password_recovery_services import (
    PUBLIC_RECOVERY_MESSAGE,
    PasswordResetError,
    request_password_recovery,
    reset_password_with_token,
)
from app.modules.users.services.authenticated_password_services import (
    AuthenticatedPasswordChangeError,
    change_authenticated_password,
)
from app.modules.users.services.feedgo_session_services import (
    PASSWORD,
    create_feedgo_session,
    revoke_feedgo_session,
)


# ------------------------------------------------------------------
# 🔧 Router
# ------------------------------------------------------------------
router = APIRouter(
    prefix="/usuarios",
    tags=["Usuarios"]
)


# =============================================================
#  REGISTRAR USUARIO
# =============================================================
@router.post("/registrar", response_model=UsuarioRegistrationResponse)
def registrar_usuario_endpoint(
    payload: UsuarioCreate,
    response: Response,
    db: Session = Depends(get_db),
):
    usuario = crear_usuario(db, payload)

    if usuario is None:
        raise HTTPException(status_code=409, detail="No se pudo completar el registro")

    delivery = send_registration_verification(db=db, usuario=usuario)
    response.headers["Cache-Control"] = "no-store"
    return UsuarioResponse.model_validate(usuario).model_dump() | {
        "email_verification_status": delivery.status,
    }


@router.post(
    "/email-verificacion/confirmar",
    response_model=EmailVerificationResponse,
)
def confirmar_email_verificacion_endpoint(
    payload: EmailVerificationConfirmRequest,
    response: Response,
    db: Session = Depends(get_db),
):
    try:
        confirm_email_verification(db=db, secret=payload.token)
    except EmailVerificationError:
        raise HTTPException(
            status_code=400,
            detail={"code": "email_verification_link_invalid"},
            headers={"Cache-Control": "no-store"},
        ) from None
    response.headers["Cache-Control"] = "no-store"
    return EmailVerificationResponse(status="verified")


@router.post(
    "/me/email-verificacion/reenvio",
    response_model=EmailVerificationResponse,
)
def reenviar_email_verificacion_endpoint(
    response: Response,
    db: Session = Depends(get_db),
    usuario_actual=Depends(obtener_usuario_actual),
):
    try:
        result = send_email_verification(db=db, usuario=usuario_actual)
    except EmailVerificationError as exc:
        status_code = 429 if exc.code == "email_verification_rate_limited" else 503
        headers = {"Cache-Control": "no-store"}
        if exc.retry_after_seconds is not None:
            headers["Retry-After"] = str(exc.retry_after_seconds)
        raise HTTPException(
            status_code=status_code,
            detail={"code": exc.code},
            headers=headers,
        ) from None
    response.headers["Cache-Control"] = "no-store"
    return EmailVerificationResponse(status=result.status)


@router.post(
    "/password/recuperacion",
    response_model=PasswordRecoveryResponse,
)
def recuperar_password_endpoint(
    payload: PasswordRecoveryRequest,
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
):
    client_host = request.client.host if request.client else "unknown"
    request_password_recovery(
        db=db,
        email=payload.email,
        client_host=client_host,
        channel=payload.channel,
    )
    response.headers["Cache-Control"] = "no-store"
    return PasswordRecoveryResponse(message=PUBLIC_RECOVERY_MESSAGE)


@router.post(
    "/password/restablecer",
    response_model=PasswordResetResponse,
)
def restablecer_password_endpoint(
    payload: PasswordResetRequest,
    response: Response,
    db: Session = Depends(get_db),
):
    try:
        reset_password_with_token(
            db=db,
            secret=payload.token,
            new_password=payload.new_password,
        )
    except PasswordResetError:
        raise HTTPException(
            status_code=400,
            detail={"code": "password_reset_link_invalid"},
            headers={"Cache-Control": "no-store"},
        ) from None
    response.headers["Cache-Control"] = "no-store"
    return PasswordResetResponse(status="password_updated")


@router.patch(
    "/me/password",
    response_model=AuthenticatedPasswordChangeResponse,
)
def cambiar_password_autenticado_endpoint(
    payload: AuthenticatedPasswordChangeRequest,
    response: Response,
    db: Session = Depends(get_db),
    auth_context=Depends(obtener_contexto_usuario_actual),
):
    try:
        change_authenticated_password(
            db=db,
            usuario=auth_context.usuario,
            current_password=payload.current_password,
            new_password=payload.new_password,
            current_session_sid=(
                auth_context.token.sid
                if auth_context.token.contract == "versioned"
                else None
            ),
        )
    except AuthenticatedPasswordChangeError as exc:
        status_code = 429 if exc.code == "current_password_rate_limited" else 400
        raise HTTPException(
            status_code=status_code,
            detail={"code": exc.code},
            headers={"Cache-Control": "no-store"},
        ) from None
    response.headers["Cache-Control"] = "no-store"
    return AuthenticatedPasswordChangeResponse(status="password_updated")


# =============================================================
#  LOGIN (AUTENTICACIÓN)
# =============================================================
@router.post("/login")
def login_endpoint(payload: UsuarioLogin, db: Session = Depends(get_db)):
    usuario = autenticar_usuario(db, payload)

    if not usuario:
        raise HTTPException(status_code=401, detail="Credenciales inválidas")

    try:
        feedgo_session = create_feedgo_session(
            db,
            usuario_id=usuario.id,
            authentication_method=PASSWORD,
            ttl=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
            contract_version=settings.JWT_CONTRACT_VERSION,
        )
        token = crear_token_jwt_versionado(
            usuario_id=usuario.id,
            sid=feedgo_session.id,
            issued_at=feedgo_session.issued_at,
            expires_at=feedgo_session.expires_at,
        )
        db.commit()
    except Exception:
        db.rollback()
        raise

    return {
        "mensaje": "Inicio de sesión exitoso ✅",
        "token": token,
        "usuario_id": usuario.id
    }


# =============================================================
#  LOGOUT (REVOCAR TOKEN)
# =============================================================
@router.post("/logout", summary="Cerrar sesión (logout real)")
def logout_endpoint(
    credenciales: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: Session = Depends(get_db)
):
    if credenciales is None or not credenciales.credentials:
        raise HTTPException(status_code=401, detail="Not authenticated")

    token = credenciales.credentials
    context = validar_token_para_logout(token, db)
    try:
        if context.contract == "versioned":
            revoke_feedgo_session(
                db,
                sid=context.sid,
                usuario_id=context.usuario_id,
            )
        else:
            db.add(TokenRevocado(
                token=token,
                usuario_id=context.usuario_id,
                expira_en=(
                    datetime.utcfromtimestamp(context.expires_at)
                    if context.expires_at is not None else None
                ),
            ))
        db.commit()
    except Exception:
        db.rollback()
        raise

    return {"mensaje": "Logout exitoso. El token fue revocado."}


# =============================================================
#  PERFIL DEL USUARIO AUTENTICADO
# =============================================================
def _usuario_me_response(db: Session, usuario) -> dict:
    readiness = derive_commercial_readiness(db, usuario)
    status = readiness.profile_status
    return UsuarioResponse.model_validate(usuario).model_dump() | {
        "perfil_completo": status.perfil_completo,
        "campos_perfil_faltantes": list(status.campos_perfil_faltantes),
        "capabilities": {
            "puede_crear_espacio": readiness.capabilities.puede_crear_espacio,
            "puede_administrar_espacios": (
                readiness.capabilities.puede_administrar_espacios
            ),
            "puede_publicar_en_espacios": (
                readiness.capabilities.puede_publicar_en_espacios
            ),
        },
        "pendientes_comerciales": list(readiness.pendientes_comerciales),
    }


@router.get("/me", response_model=UsuarioMeResponse)
def obtener_mi_perfil(
    response: Response,
    db: Session = Depends(get_db),
    usuario_actual=Depends(obtener_usuario_actual),
):
    response.headers["Cache-Control"] = "no-store, private"
    return _usuario_me_response(db, usuario_actual)


@router.post("/me/telefono-verificacion/reenvio", response_model=PhoneVerificationIssueResponse)
def solicitar_verificacion_telefono(
    request: Request,
    response: Response,
    db: Session = Depends(get_db), usuario_actual=Depends(obtener_usuario_actual),
):
    require_local_phone_otp_mailbox(request)
    response.headers["Cache-Control"] = "private, no-store"
    try:
        challenge_id = issue_phone_challenge(
            db=db,
            usuario_id=usuario_actual.id,
            delivery=get_local_phone_otp_mailbox(),
        )
        db.commit()
        return {"challenge_id": challenge_id, "status": "sent"}
    except PhoneVerificationError as exc:
        db.rollback()
        raise HTTPException(
            status_code=400,
            detail=str(exc),
            headers={"Cache-Control": "private, no-store"},
        )


@router.post("/me/telefono-verificacion/confirmar", response_model=PhoneVerificationConfirmResponse)
def confirmar_verificacion_telefono(
    payload: PhoneVerificationConfirmRequest,
    response: Response,
    db: Session = Depends(get_db), usuario_actual=Depends(obtener_usuario_actual),
):
    response.headers["Cache-Control"] = "private, no-store"
    try:
        confirm_phone_challenge(
            db=db, usuario_id=usuario_actual.id,
            challenge_id=payload.challenge_id, code=payload.code,
        )
        db.commit()
        return {"status": "verified"}
    except PhoneVerificationError as exc:
        # Los intentos fallidos forman parte del estado de seguridad.
        db.commit()
        raise HTTPException(
            status_code=400,
            detail=str(exc),
            headers={"Cache-Control": "private, no-store"},
        )


@router.post(
    "/email-disponibilidad",
    response_model=EmailAvailabilityResponse,
    summary="Comprobar disponibilidad de email para registro",
)
def email_disponibilidad_endpoint(
    payload: EmailAvailabilityRequest,
    request: Request,
    db: Session = Depends(get_db),
):
    # No se aceptan headers reenviados como identidad del cliente sin un proxy
    # confiable configurado. Tampoco se registra el email consultado.
    client_key = request.client.host if request.client else "unknown"
    if not email_availability_rate_limiter.allow(client_key):
        raise HTTPException(
            status_code=429,
            detail="Demasiadas solicitudes. Intenta nuevamente mas tarde.",
            headers={"Retry-After": "60"},
        )
    return EmailAvailabilityResponse(
        disponible=is_email_available(db, str(payload.email))
    )


# =============================================================
#  ACTUALIZAR PERFIL DEL USUARIO AUTENTICADO
# =============================================================
@router.patch(
    "/me",
    response_model=UsuarioMeResponse,
    summary="Actualizar perfil basico del usuario autenticado"
)
def actualizar_mi_perfil(
    payload: UsuarioPerfilUpdate,
    response: Response,
    db: Session = Depends(get_db),
    usuario_actual=Depends(obtener_usuario_actual),
):
    campos = payload.model_dump(exclude_unset=True)

    try:
        actualizado = actualizar_perfil_usuario(
            db=db,
            usuario=usuario_actual,
            campos=campos
        )
        response.headers["Cache-Control"] = "no-store, private"
        return _usuario_me_response(db, actualizado)
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e),
            headers={"Cache-Control": "no-store, private"},
        )


@router.get(
    "/documentos-vigentes",
    response_model=list[DocumentoPublicoVigenteResponse],
    summary="Documentos publicos vigentes para registro",
)
def documentos_publicos_vigentes_endpoint():
    return listar_documentos_publicos_vigentes()


# =============================================================
#  ACTUALIZAR AVATAR DEL USUARIO (ETAPA 49)
# =============================================================
@router.put(
    "/me/avatar",
    response_model=UsuarioResponse,
    summary="Actualizar foto de perfil (avatar) del usuario autenticado"
)
def actualizar_avatar_endpoint(
    payload: UsuarioAvatarUpdate,
    db: Session = Depends(get_db),
    usuario_actual=Depends(obtener_usuario_actual),
):
    """
    Actualiza el avatar del usuario autenticado.

    Flujo esperado:
    1) El frontend sube imagen a /media/upload (JWT requerido)
    2) /media/upload devuelve { url }
    3) El frontend llama a este endpoint con avatar_url = url
    4) Se persiste en BD y se devuelve el usuario actualizado
    """

    avatar_url_normalizada = payload.avatar_url.strip()
    if not avatar_url_normalizada:
        raise HTTPException(status_code=400, detail="avatar_url no puede ser vacío")

    usuario_actual.avatar_url = avatar_url_normalizada
    db.commit()
    db.refresh(usuario_actual)

    return usuario_actual


# =============================================================
#  OBTENER USUARIO POR ID
# =============================================================
@router.get("/{usuario_id}", response_model=UsuarioPublicResponse)
def obtener_usuario_endpoint(usuario_id: int, db: Session = Depends(get_db)):
    usuario = obtener_usuario_por_id(db, usuario_id)

    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    return usuario


# =============================================================
#  ONBOARDING DEL USUARIO
# =============================================================
@router.post(
    "/onboarding",
    response_model=UsuarioResponse,
    summary="Completar onboarding inicial del usuario"
)
def completar_onboarding_endpoint(
    payload: UsuarioOnboarding,
    db: Session = Depends(get_db),
    usuario_actual=Depends(obtener_usuario_actual)
):
    """
    Completa el onboarding del usuario autenticado.

    - Guarda provincia y ciudad
    - Marca onboarding_completo = True
    - Devuelve el usuario actualizado
    """

    usuario_actualizado = completar_onboarding_usuario(
        db=db,
        usuario=usuario_actual,
        provincia=payload.provincia,
        ciudad=payload.ciudad
    )

    return usuario_actualizado


# =============================================================
#  CAMBIO DE MODO (USUARIO ↔ PUBLICADOR)
# =============================================================
@router.post(
    "/modo",
    response_model=UsuarioResponse,
    summary="Cambiar modo activo del usuario"
)
def cambiar_modo_endpoint(
    payload: UsuarioCambioModo,
    db: Session = Depends(get_db),
    usuario_actual=Depends(obtener_usuario_actual)
):
    """
    Permite cambiar el modo activo del usuario autenticado.

    - No genera nuevo token
    - No crea cuentas nuevas
    - Solo actualiza estado interno
    """

    try:
        usuario_actualizado = cambiar_modo_usuario(
            db=db,
            usuario=usuario_actual,
            nuevo_modo=payload.modo
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return usuario_actualizado
