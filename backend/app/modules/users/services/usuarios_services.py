"""
usuarios_services.py
--------------------
Lógica de negocio para Usuarios.
"""

import re

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from app.modules.users.models.identity_models import PasswordCredential
from app.modules.users.models.usuarios_models import Usuario
from app.modules.users.schemas.usuarios_schemas import UsuarioCreate, UsuarioLogin
from app.modules.users.services import documentos_aceptacion_services
from app.modules.users.services.email_normalization import (
    InvalidEmailError,
    canonicalize_email,
)
from app.modules.users.services.phone_normalization import (
    InvalidPhoneError,
    canonicalize_phone,
)

# Funciones de seguridad
from app.core.security import hash_password, verificar_password

COLOR_FONDO_HEX_RE = re.compile(r"^#[0-9A-Fa-f]{6}$")

# ✔️ IMPORTANTE: ya NO importamos auth aquí
# Cada capa cumple su propia responsabilidad


def crear_usuario(db: Session, usuario: UsuarioCreate) -> Usuario | None:
    email = str(usuario.email)
    email_canonical = canonicalize_email(email)
    existente = (
        db.query(Usuario)
        .filter(Usuario.email_canonical == email_canonical)
        .first()
    )
    if existente:
        return None

    documentos_aceptacion_services.validar_aceptaciones_obligatorias_registro(
        usuario
    )

    hashed = hash_password(usuario.password)

    nuevo_usuario = Usuario(
        email=email,
        email_canonical=email_canonical,
        hashed_password=hashed,
    )

    try:
        db.add(nuevo_usuario)
        db.flush()
        db.add(
            PasswordCredential(
                usuario_id=nuevo_usuario.id,
                password_hash=hashed,
                hash_version="bcrypt",
            )
        )
        documentos_aceptacion_services.crear_evidencias_aceptacion_registro(
            db=db,
            usuario=nuevo_usuario,
        )
        db.commit()
        db.refresh(nuevo_usuario)
    except IntegrityError:
        db.rollback()
        # La restriccion fisica es la autoridad final ante carreras entre altas
        # canonicas equivalentes. No se convierten otros errores de integridad
        # en un falso duplicado.
        existente = (
            db.query(Usuario.id)
            .filter(Usuario.email_canonical == email_canonical)
            .first()
        )
        if existente is not None:
            return None
        raise
    except Exception:
        db.rollback()
        raise

    return nuevo_usuario


def autenticar_usuario(db: Session, data: UsuarioLogin) -> Usuario | None:
    email_canonical = canonicalize_email(str(data.email))
    usuario = (
        db.query(Usuario)
        .filter(Usuario.email_canonical == email_canonical)
        .first()
    )
    if not usuario:
        # Fallback acotado a filas legacy todavia no reparadas. La comparacion
        # reutiliza el owner canonico y no introduce lower/trim paralelos.
        candidatos_legacy = (
            db.query(Usuario)
            .filter(Usuario.email_canonical.is_(None))
            .all()
        )
        coincidencias = []
        for candidato in candidatos_legacy:
            try:
                coincide = canonicalize_email(candidato.email) == email_canonical
            except InvalidEmailError:
                coincide = False
            if coincide:
                coincidencias.append(candidato)
        if len(coincidencias) != 1:
            return None
        usuario = coincidencias[0]

    credencial = db.get(PasswordCredential, usuario.id)
    password_hash = (
        credencial.password_hash
        if credencial is not None
        else usuario.hashed_password
        if usuario.email_canonical is None
        else None
    )

    if password_hash is None or not verificar_password(data.password, password_hash):
        return None

    return usuario


def obtener_usuario_por_id(db: Session, usuario_id: int) -> Usuario | None:
    return db.query(Usuario).filter(Usuario.id == usuario_id).first()


def completar_onboarding_usuario(
    db: Session,
    usuario: Usuario,
    provincia: str,
    ciudad: str
) -> Usuario:
    """
    Completa el onboarding inicial del usuario.

    - Guarda provincia y ciudad
    - Marca onboarding_completo = True
    - No crea usuario nuevo
    - No toca autenticación ni tokens

    Se espera que el usuario ya esté autenticado.
    """

    usuario.provincia = provincia
    usuario.ciudad = ciudad
    usuario.onboarding_completo = True

    db.commit()
    db.refresh(usuario)

    return usuario


def actualizar_perfil_usuario(
    db: Session,
    usuario: Usuario,
    campos: dict
) -> Usuario:
    """
    Actualiza solo los campos editables del perfil personal.

    Campos permitidos:
    - provincia
    - ciudad
    - color_fondo
    - fecha_nacimiento
    - telefono_e164 inicial/no verificado
    """

    campos_permitidos = {
        "provincia",
        "ciudad",
        "color_fondo",
        "fecha_nacimiento",
        "telefono_e164",
    }

    telefono_solicitado = None
    if "telefono_e164" in campos:
        usuario = (
            db.query(Usuario)
            .filter(Usuario.id == usuario.id)
            .with_for_update()
            .populate_existing()
            .one()
        )
    for campo, valor in campos.items():
        if campo not in campos_permitidos:
            continue

        if isinstance(valor, str) and campo != "telefono_e164":
            valor = valor.strip()

        if campo == "color_fondo" and valor is not None:
            if not COLOR_FONDO_HEX_RE.fullmatch(valor):
                raise ValueError("color_fondo debe ser un HEX valido (#RRGGBB)")

        if campo == "telefono_e164":
            try:
                telefono_nuevo = canonicalize_phone(valor) if valor else None
            except InvalidPhoneError as exc:
                raise ValueError("telefono_invalido") from exc

            telefono_actual = usuario.telefono_e164
            if (
                usuario.telefono_verified_at is not None
                and telefono_nuevo != telefono_actual
            ):
                raise ValueError(
                    "telefono_verificado_requiere_reemplazo_seguro"
                )

            if telefono_nuevo != telefono_actual:
                from app.modules.users.models.identity_models import PhoneVerificationChallenge
                from datetime import datetime, timezone
                active_challenges = db.query(PhoneVerificationChallenge).filter(
                    PhoneVerificationChallenge.usuario_id == usuario.id,
                    PhoneVerificationChallenge.consumed_at.is_(None),
                    PhoneVerificationChallenge.revoked_at.is_(None),
                ).with_for_update().all()
                for challenge in active_challenges:
                    challenge.revoked_at = datetime.now(timezone.utc)
                    challenge.invalidation_reason = "administrative"
                usuario.telefono_e164 = telefono_nuevo
                usuario.telefono_verified_at = None
                usuario.telefono_verification_source = None
            telefono_solicitado = telefono_nuevo
            continue

        setattr(usuario, campo, valor)

    try:
        db.commit()
        db.refresh(usuario)
    except IntegrityError as exc:
        db.rollback()
        if telefono_solicitado is not None:
            ocupado = (
                db.query(Usuario.id)
                .filter(
                    Usuario.telefono_e164 == telefono_solicitado,
                    Usuario.id != usuario.id,
                )
                .first()
            )
            if ocupado is not None:
                raise ValueError("telefono_no_disponible") from exc
        raise

    return usuario


def cambiar_modo_usuario(
    db: Session,
    usuario: Usuario,
    nuevo_modo: str
) -> Usuario:
    """
    Cambia el modo activo del usuario.

    Modos permitidos:
    - "usuario"
    - "publicador"

    Reglas:
    - No crea nuevas cuentas
    - No genera nuevos tokens
    - Solo actualiza el estado del usuario autenticado
    """

    modos_permitidos = {"usuario", "publicador"}

    if nuevo_modo not in modos_permitidos:
        raise ValueError("Modo inválido")

    usuario.modo_activo = nuevo_modo

    db.commit()
    db.refresh(usuario)

    return usuario
