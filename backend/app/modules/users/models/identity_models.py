"""Fundacion aditiva de identidad y sesiones de FeedGo.

Estos modelos no cambian todavia Registro, Login, JWT ni revocacion legacy.
"""

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    UniqueConstraint,
    func,
)

from app.core.database import Base


class PasswordCredential(Base):
    """Credencial opcional por password vinculada a un Usuario FeedGo."""

    __tablename__ = "password_credentials"

    usuario_id = Column(
        Integer,
        ForeignKey("usuarios.id", ondelete="CASCADE"),
        primary_key=True,
    )
    password_hash = Column(String(255), nullable=False)
    hash_version = Column(String(32), nullable=False, server_default="bcrypt")
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )


class ExternalIdentity(Base):
    """Identidad externa validada por backend; Google sera el primer provider."""

    __tablename__ = "external_identities"

    id = Column(Integer, primary_key=True, index=True)
    usuario_id = Column(
        Integer,
        ForeignKey("usuarios.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    provider = Column(String(32), nullable=False)
    provider_subject = Column(String(255), nullable=False)
    provider_email_snapshot = Column(String(255), nullable=True)
    provider_email_verified_snapshot = Column(Boolean, nullable=True)
    linked_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    last_used_at = Column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        UniqueConstraint(
            "provider",
            "provider_subject",
            name="uq_external_identities_provider_subject",
        ),
    )


class FeedGoSession(Base):
    """Sesion emitida por FeedGo, todavia no conectada al JWT legacy."""

    __tablename__ = "feedgo_sessions"

    id = Column(String(64), primary_key=True)
    usuario_id = Column(
        Integer,
        ForeignKey("usuarios.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    authentication_method = Column(String(32), nullable=False)
    external_identity_id = Column(
        Integer,
        ForeignKey("external_identities.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    issued_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    expires_at = Column(DateTime(timezone=True), nullable=False)
    revoked_at = Column(DateTime(timezone=True), nullable=True)
    contract_version = Column(Integer, nullable=False, server_default="1")

    __table_args__ = (
        Index("ix_feedgo_sessions_user_expiry", "usuario_id", "expires_at"),
        Index(
            "ix_feedgo_sessions_user_active",
            "usuario_id",
            "revoked_at",
            "expires_at",
        ),
        CheckConstraint(
            "authentication_method IN ('password', 'google')",
            name="ck_feedgo_sessions_authentication_method",
        ),
        CheckConstraint(
            "contract_version = 1",
            name="ck_feedgo_sessions_contract_version",
        ),
        CheckConstraint(
            "expires_at > issued_at",
            name="ck_feedgo_sessions_expiry",
        ),
        CheckConstraint(
            "revoked_at IS NULL OR revoked_at >= issued_at",
            name="ck_feedgo_sessions_revocation_time",
        ),
    )


class AccountActionToken(Base):
    """Evidencia persistente de un secreto de accion; nunca guarda el secreto."""

    __tablename__ = "account_action_tokens"

    id = Column(Integer, primary_key=True, index=True)
    usuario_id = Column(
        Integer,
        ForeignKey("usuarios.id", ondelete="CASCADE"),
        nullable=False,
    )
    purpose = Column(String(32), nullable=False)
    token_digest = Column(String(64), nullable=False)
    email_canonical_snapshot = Column(String(255), nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    expires_at = Column(DateTime(timezone=True), nullable=False)
    consumed_at = Column(DateTime(timezone=True), nullable=True)
    invalidated_at = Column(DateTime(timezone=True), nullable=True)
    invalidation_reason = Column(String(32), nullable=True)
    issuance_id = Column(String(64), nullable=False)

    __table_args__ = (
        CheckConstraint(
            "purpose IN ('email_verification', 'password_reset')",
            name="ck_account_action_tokens_purpose",
        ),
        CheckConstraint(
            "expires_at > created_at",
            name="ck_account_action_tokens_expiry",
        ),
        CheckConstraint(
            "NOT (consumed_at IS NOT NULL AND invalidated_at IS NOT NULL)",
            name="ck_account_action_tokens_terminal_state",
        ),
        CheckConstraint(
            "invalidation_reason IS NULL OR invalidation_reason IN "
            "('superseded', 'password_changed', 'administrative')",
            name="ck_account_action_tokens_invalidation_reason",
        ),
        CheckConstraint(
            "(invalidated_at IS NULL AND invalidation_reason IS NULL) OR "
            "(invalidated_at IS NOT NULL AND invalidation_reason IS NOT NULL)",
            name="ck_account_action_tokens_invalidation_pair",
        ),
        UniqueConstraint(
            "token_digest",
            name="uq_account_action_tokens_token_digest",
        ),
        UniqueConstraint(
            "issuance_id",
            name="uq_account_action_tokens_issuance_id",
        ),
        Index(
            "ix_account_action_tokens_user_purpose_created",
            "usuario_id",
            "purpose",
            "created_at",
        ),
        Index(
            "ix_account_action_tokens_purpose_expiry",
            "purpose",
            "expires_at",
        ),
    )


class AccountActionRateLimit(Base):
    """Bucket persistente minimo; la logica de limites pertenece a 99.3-D."""

    __tablename__ = "account_action_rate_limits"

    id = Column(Integer, primary_key=True, index=True)
    action = Column(String(32), nullable=False)
    subject_digest = Column(String(64), nullable=False)
    window_started_at = Column(DateTime(timezone=True), nullable=False)
    attempt_count = Column(Integer, nullable=False, server_default="0")
    blocked_until = Column(DateTime(timezone=True), nullable=True)
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    __table_args__ = (
        CheckConstraint(
            "action IN ('email_verification', 'password_reset', 'current_password', "
            "'phone_verification')",
            name="ck_account_action_rate_limits_action",
        ),
        CheckConstraint(
            "attempt_count >= 0",
            name="ck_account_action_rate_limits_attempt_count",
        ),
        UniqueConstraint(
            "action",
            "subject_digest",
            name="uq_account_action_rate_limits_action_subject",
        ),
        Index(
            "ix_account_action_rate_limits_action_blocked",
            "action",
            "blocked_until",
        ),
    )


class PhoneVerificationChallenge(Base):
    """Challenge OTP de baja entropia; nunca persiste el codigo en claro."""

    __tablename__ = "phone_verification_challenges"

    id = Column(String(64), primary_key=True)
    usuario_id = Column(Integer, ForeignKey("usuarios.id", ondelete="CASCADE"), nullable=False)
    phone_e164_snapshot = Column(String(16), nullable=False)
    code_digest = Column(String(64), nullable=False)
    issuance_id = Column(String(64), nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    expires_at = Column(DateTime(timezone=True), nullable=False)
    consumed_at = Column(DateTime(timezone=True), nullable=True)
    revoked_at = Column(DateTime(timezone=True), nullable=True)
    invalidation_reason = Column(String(32), nullable=True)
    failed_attempts = Column(Integer, nullable=False, server_default="0")

    __table_args__ = (
        UniqueConstraint("issuance_id", name="uq_phone_verification_issuance_id"),
        CheckConstraint("expires_at > created_at", name="ck_phone_verification_expiry"),
        CheckConstraint("failed_attempts >= 0 AND failed_attempts <= 5", name="ck_phone_verification_attempts"),
        CheckConstraint("NOT (consumed_at IS NOT NULL AND revoked_at IS NOT NULL)", name="ck_phone_verification_terminal"),
        CheckConstraint("invalidation_reason IS NULL OR invalidation_reason IN ('superseded', 'administrative')", name="ck_phone_verification_reason"),
        CheckConstraint("(revoked_at IS NULL AND invalidation_reason IS NULL) OR (revoked_at IS NOT NULL AND invalidation_reason IS NOT NULL)", name="ck_phone_verification_invalidation_pair"),
        Index("ix_phone_verification_user_created", "usuario_id", "created_at"),
        Index("ix_phone_verification_user_expiry", "usuario_id", "expires_at"),
    )
