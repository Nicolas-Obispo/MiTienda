"""
documentos_aceptacion_services.py
---------------------------------
Definicion centralizada de documentos obligatorios y creacion de evidencia.
"""

from dataclasses import dataclass
from datetime import datetime
import hashlib

from sqlalchemy.orm import Session

from app.modules.users.models.usuarios_documentos_aceptaciones_models import (
    UsuarioDocumentoAceptacion,
)
from app.modules.users.models.usuarios_models import Usuario
from app.modules.users.schemas.usuarios_schemas import UsuarioCreate


DOCUMENTO_TERMINOS_CONDICIONES = "terminos_condiciones"
DOCUMENTO_POLITICA_PRIVACIDAD = "politica_privacidad"
DOCUMENTO_VERSION_INICIAL = "v1"
CANAL_REGISTRO_WEB = "web"
METODO_CHECKBOX_EXPLICITO = "checkbox_explicito"
ESTADO_ACEPTADO = "aceptado"


@dataclass(frozen=True)
class DocumentoAceptacionVigente:
    tipo: str
    version: str
    referencia: str


def _referencia_documento(tipo: str, version: str) -> str:
    return f"{tipo}:{version}"


DOCUMENTOS_OBLIGATORIOS_REGISTRO = (
    DocumentoAceptacionVigente(
        tipo=DOCUMENTO_TERMINOS_CONDICIONES,
        version=DOCUMENTO_VERSION_INICIAL,
        referencia=_referencia_documento(
            DOCUMENTO_TERMINOS_CONDICIONES,
            DOCUMENTO_VERSION_INICIAL,
        ),
    ),
    DocumentoAceptacionVigente(
        tipo=DOCUMENTO_POLITICA_PRIVACIDAD,
        version=DOCUMENTO_VERSION_INICIAL,
        referencia=_referencia_documento(
            DOCUMENTO_POLITICA_PRIVACIDAD,
            DOCUMENTO_VERSION_INICIAL,
        ),
    ),
)

DOCUMENTOS_PUBLICOS_URLS = {
    DOCUMENTO_TERMINOS_CONDICIONES: "/terminos-y-condiciones",
    DOCUMENTO_POLITICA_PRIVACIDAD: "/politica-de-privacidad",
}


def listar_documentos_publicos_vigentes() -> list[dict[str, str]]:
    return [
        {
            "tipo": documento.tipo,
            "version": documento.version,
            "referencia": documento.referencia,
            "url": DOCUMENTOS_PUBLICOS_URLS[documento.tipo],
        }
        for documento in DOCUMENTOS_OBLIGATORIOS_REGISTRO
    ]


def validar_aceptaciones_obligatorias_registro(usuario: UsuarioCreate) -> None:
    if usuario.acepta_terminos is not True:
        raise ValueError("Debe aceptar los Terminos y Condiciones.")

    if usuario.acepta_privacidad is not True:
        raise ValueError("Debe aceptar la Politica de Privacidad.")


def crear_evidencias_aceptacion_registro(
    db: Session,
    usuario: Usuario,
    *,
    aceptado_en: datetime | None = None,
) -> list[UsuarioDocumentoAceptacion]:
    aceptado_en = aceptado_en or datetime.utcnow()
    evidencias = []

    for documento in DOCUMENTOS_OBLIGATORIOS_REGISTRO:
        evidencia = UsuarioDocumentoAceptacion(
            usuario_id=usuario.id,
            documento_tipo=documento.tipo,
            documento_version=documento.version,
            aceptado_en=aceptado_en,
            canal=CANAL_REGISTRO_WEB,
            metodo=METODO_CHECKBOX_EXPLICITO,
            estado=ESTADO_ACEPTADO,
            documento_referencia=documento.referencia,
        )
        db.add(evidencia)
        evidencias.append(evidencia)

    return evidencias


def digest_documentos_obligatorios_registro() -> str:
    """Fingerprint estable del set legal que el usuario acepta expresamente."""

    referencias = "\n".join(
        sorted(documento.referencia for documento in DOCUMENTOS_OBLIGATORIOS_REGISTRO)
    )
    return hashlib.sha256(referencias.encode("utf-8")).hexdigest()


def tiene_aceptaciones_obligatorias_vigentes(db: Session, usuario_id: int) -> bool:
    """Evalua las evidencias exigidas por el contrato legal vigente actual."""
    evidencias = (
        db.query(UsuarioDocumentoAceptacion)
        .filter(UsuarioDocumentoAceptacion.usuario_id == usuario_id)
        .all()
    )
    aceptadas = {
        (
            evidencia.documento_tipo,
            evidencia.documento_version,
            evidencia.documento_referencia,
        )
        for evidencia in evidencias
        if evidencia.estado == ESTADO_ACEPTADO
    }
    requeridas = {
        (documento.tipo, documento.version, documento.referencia)
        for documento in DOCUMENTOS_OBLIGATORIOS_REGISTRO
    }
    return requeridas.issubset(aceptadas)
