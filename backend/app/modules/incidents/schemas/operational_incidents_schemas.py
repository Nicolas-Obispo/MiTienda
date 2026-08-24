import re
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.modules.incidents.constants import (
    ACTIONS, COMMUNICATION_STATUSES, EVIDENCE_TYPES, INCIDENT_TYPES,
    LEGAL_ASSESSMENT_STATUSES, PERSONAL_DATA_IMPACTS, RISK_LEVELS, SEVERITIES,
)

OPAQUE_REFERENCE = re.compile(r"^[A-Za-z0-9_.:-]{1,128}$")
SENSITIVE_TEXT = re.compile(r"(?i)(authorization|bearer\s|password\s*[=:]|secret\s*[=:]|api[_-]?key\s*[=:]|eyJ[a-zA-Z0-9_-]{10,})")


def _safe_text(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None
    normalized = value.strip()
    if not normalized or SENSITIVE_TEXT.search(normalized):
        raise ValueError("texto vacio o potencialmente sensible")
    return normalized


class IncidentSource(BaseModel):
    evidence_type: Optional[str] = None
    evidence_reference: Optional[str] = None
    request_id: Optional[str] = None
    correlation_id: Optional[str] = None
    alert_id: Optional[str] = None
    model_config = ConfigDict(extra="forbid")

    @field_validator("evidence_type")
    @classmethod
    def validate_evidence_type(cls, value):
        if value is not None and value not in EVIDENCE_TYPES:
            raise ValueError("evidence_type invalido")
        return value

    @field_validator("evidence_reference", "request_id", "correlation_id", "alert_id")
    @classmethod
    def validate_opaque(cls, value):
        forbidden_markers = ("authorization", "bearer", "password", "secret", "api_key", "apikey", "token")
        forbidden_schemes = ("http:", "https:", "file:", "ftp:", "data:")
        if value is not None and (
            not OPAQUE_REFERENCE.fullmatch(value)
            or SENSITIVE_TEXT.search(value)
            or any(marker in value.lower() for marker in forbidden_markers)
            or value.lower().startswith(forbidden_schemes)
        ):
            raise ValueError("referencia opaca invalida")
        return value

    @model_validator(mode="after")
    def require_type_for_reference(self):
        if self.evidence_reference and not self.evidence_type:
            raise ValueError("evidence_type es obligatorio")
        return self


class OperationalIncidentCreate(BaseModel):
    title: str = Field(min_length=3, max_length=160)
    summary: str = Field(min_length=3, max_length=1200)
    incident_type: str
    severity: str
    owner_usuario_id: int = Field(gt=0)
    operational_deadline_at: Optional[datetime] = None
    source: Optional[IncidentSource] = None
    idempotency_key: str = Field(min_length=8, max_length=64, pattern=r"^[A-Za-z0-9._:-]+$")
    model_config = ConfigDict(extra="forbid")

    @field_validator("title", "summary")
    @classmethod
    def safe_text(cls, value): return _safe_text(value)
    @field_validator("incident_type")
    @classmethod
    def incident_type_valid(cls, value):
        if value not in INCIDENT_TYPES: raise ValueError("incident_type invalido")
        return value
    @field_validator("severity")
    @classmethod
    def severity_valid(cls, value):
        if value not in SEVERITIES: raise ValueError("severity invalida")
        return value


class OperationalIncidentAction(BaseModel):
    action: str
    expected_version: int = Field(ge=1)
    idempotency_key: str = Field(min_length=8, max_length=64, pattern=r"^[A-Za-z0-9._:-]+$")
    summary: str = Field(min_length=3, max_length=1200)
    severity: Optional[str] = None
    owner_usuario_id: Optional[int] = Field(default=None, gt=0)
    operational_deadline_at: Optional[datetime] = None
    residual_risk_level: Optional[str] = None
    residual_risk_summary: Optional[str] = Field(default=None, max_length=1000)
    residual_risk_owner_usuario_id: Optional[int] = Field(default=None, gt=0)
    residual_risk_review_at: Optional[datetime] = None
    legal_assessment_status: Optional[str] = None
    personal_data_impact: Optional[str] = None
    legal_owner_usuario_id: Optional[int] = Field(default=None, gt=0)
    user_communication_status: Optional[str] = None
    authority_communication_status: Optional[str] = None
    legal_deadline_at: Optional[datetime] = None
    source: Optional[IncidentSource] = None
    model_config = ConfigDict(extra="forbid")

    @field_validator("summary", "residual_risk_summary")
    @classmethod
    def safe_text(cls, value): return _safe_text(value)
    @field_validator("action")
    @classmethod
    def action_valid(cls, value):
        if value not in ACTIONS: raise ValueError("action invalida")
        return value
    @field_validator("severity")
    @classmethod
    def severity_valid(cls, value):
        if value is not None and value not in SEVERITIES: raise ValueError("severity invalida")
        return value
    @field_validator("residual_risk_level")
    @classmethod
    def risk_valid(cls, value):
        if value is not None and value not in RISK_LEVELS: raise ValueError("riesgo invalido")
        return value
    @field_validator("legal_assessment_status")
    @classmethod
    def legal_valid(cls, value):
        if value is not None and value not in LEGAL_ASSESSMENT_STATUSES: raise ValueError("estado legal invalido")
        return value
    @field_validator("personal_data_impact")
    @classmethod
    def data_valid(cls, value):
        if value is not None and value not in PERSONAL_DATA_IMPACTS: raise ValueError("impacto de datos invalido")
        return value
    @field_validator("user_communication_status", "authority_communication_status")
    @classmethod
    def communication_valid(cls, value):
        if value is not None and value not in COMMUNICATION_STATUSES: raise ValueError("estado de comunicacion invalido")
        return value


class OperationalIncidentResponse(BaseModel):
    public_id: str
    title: str
    summary_sanitized: str
    incident_type: str
    severity: str
    status: str
    owner_usuario_id: int
    opened_by_usuario_id: int
    version: int
    operational_deadline_at: Optional[datetime]
    residual_risk_level: Optional[str]
    residual_risk_summary: Optional[str]
    residual_risk_owner_usuario_id: Optional[int]
    residual_risk_review_at: Optional[datetime]
    legal_assessment_status: str
    personal_data_impact: str
    legal_owner_usuario_id: Optional[int]
    user_communication_status: str
    authority_communication_status: str
    legal_deadline_at: Optional[datetime]
    opened_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)


class OperationalIncidentEventResponse(BaseModel):
    id: int
    event_type: str
    actor_usuario_id: int
    status_before: Optional[str]
    status_after: str
    severity_before: Optional[str]
    severity_after: str
    owner_before_usuario_id: Optional[int]
    owner_after_usuario_id: int
    safe_summary: str
    evidence_type: Optional[str]
    evidence_reference: Optional[str]
    request_id: Optional[str]
    correlation_id: Optional[str]
    alert_id: Optional[str]
    resulting_incident_version: int
    occurred_at: datetime
    model_config = ConfigDict(from_attributes=True)


class OperationalIncidentListResponse(BaseModel):
    items: list[OperationalIncidentResponse]
    next_cursor: Optional[int] = None


class OperationalIncidentActionResponse(BaseModel):
    incident: OperationalIncidentResponse
    event: OperationalIncidentEventResponse
