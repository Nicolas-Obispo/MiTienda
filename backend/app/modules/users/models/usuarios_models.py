"""
usuarios_models.py
-------------------
Modelo ORM para la tabla 'usuarios'.

Este modelo es compartido entre MiTienda y MiPlaza.
Los campos agregados para MiPlaza fueron diseñados
para no romper compatibilidad con usuarios existentes.
"""

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    Date,
    DateTime,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

from app.core.database import Base


class Usuario(Base):
    __tablename__ = "usuarios"

    # -----------------------------
    # Campos existentes (MiTienda)
    # -----------------------------
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, nullable=False)

    # ETAPA 99 expand-first: permanece nullable hasta que Registro/Login migren
    # al nuevo owner. La unicidad ignora NULL durante la transicion.
    email_canonical = Column(String(255), nullable=True)
    email_verified_at = Column(DateTime(timezone=True), nullable=True)
    email_verification_source = Column(String(32), nullable=True)

    # Contraseña hasheada (NO se modifica)
    hashed_password = Column(String(255), nullable=False)

    # -----------------------------
    # Campos agregados para MiPlaza
    # -----------------------------

    # URL de la foto de perfil (ETAPA 49)
    # Nullable para no romper usuarios existentes
    avatar_url = Column(String(255), nullable=True)

    # Color de fondo personalizable del perfil
    # Formato esperado: HEX #RRGGBB
    color_fondo = Column(String(7), nullable=True)

    # Modo activo del usuario dentro de la plataforma
    # Valores esperados:
    # - "usuario"     → consumidor
    # - "publicador"  → comerciante / servicio
    # Default seguro para usuarios existentes
    modo_activo = Column(String(20), nullable=False, default="usuario")

    # Indica si el usuario completó el onboarding inicial
    # (selección de provincia y ciudad)
    onboarding_completo = Column(Boolean, nullable=False, default=False)

    # Ubicación base del usuario (descubrimiento local)
    # Son opcionales para no romper registros existentes
    provincia = Column(String(100), nullable=True)
    ciudad = Column(String(100), nullable=True)

    # Dato privado. No forma parte del registro inicial ni de respuestas
    # publicas. La edad se deriva en backend y nunca se persiste.
    fecha_nacimiento = Column(Date, nullable=True)

    # Contacto privado de identidad. Su presencia no implica verificacion ni
    # disponibilidad de SMS/WhatsApp.
    telefono_e164 = Column(String(16), nullable=True)
    telefono_verified_at = Column(DateTime(timezone=True), nullable=True)
    telefono_verification_source = Column(String(32), nullable=True)

    __table_args__ = (
        UniqueConstraint(
            "email_canonical",
            name="ux_usuarios_email_canonical",
        ),
        UniqueConstraint(
            "telefono_e164",
            name="ux_usuarios_telefono_e164",
        ),
        CheckConstraint(
            "(telefono_verified_at IS NULL AND telefono_verification_source IS NULL) "
            "OR (telefono_verified_at IS NOT NULL AND "
            "telefono_verification_source IS NOT NULL)",
            name="ck_usuarios_telefono_verification_pair",
        ),
    )

    # -------------------------
    # Likes en publicaciones
    # -------------------------
    likes_publicaciones = relationship(
        "LikePublicacion",
        back_populates="usuario",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    # -------------------------
    # Publicaciones guardadas
    # -------------------------
    # Relación con publicaciones que el usuario guardó
    # Uso personal (no social)
    publicaciones_guardadas = relationship(
        "PublicacionGuardada",
        back_populates="usuario",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    # -------------------------
    # Vistas de historias (ETAPA 43)
    # -------------------------
    historias_vistas = relationship(
        "HistoriaVista",
        lazy="selectin",
        cascade="all, delete-orphan",
    )
