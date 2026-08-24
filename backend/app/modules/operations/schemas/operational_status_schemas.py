from typing import Literal

from pydantic import BaseModel, ConfigDict


class StrictSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")


class SafeHealthCheck(StrictSchema):
    component: str
    status: str
    message: str


class SafeHealthSummary(StrictSchema):
    liveness: str
    readiness: str
    components: list[SafeHealthCheck]


class SafeEvidenceStatus(StrictSchema):
    status: str
    meaning: str


class SafeMetricAggregate(StrictSchema):
    name: str
    value: float
    sample_count: int


class SafeAlertEvent(StrictSchema):
    alert_id: str
    rule_name: str
    severity: str
    status: str
    triggered_at_utc: str
    message: str


class OperationalEmailWorkerStatus(StrictSchema):
    status: Literal["active", "stopped", "disabled"]
    scope: Literal["local_runtime"]
    volatile: Literal[True]


class OperationalStatusResponse(StrictSchema):
    generated_at: str
    scope: Literal["process_local"]
    volatile: Literal[True]
    historical: Literal[False]
    global_status: Literal[False]
    health: SafeHealthSummary
    recovery_evidence: dict[str, SafeEvidenceStatus]
    operational_email_worker: OperationalEmailWorkerStatus
    aggregates: list[SafeMetricAggregate]
    alerts: list[SafeAlertEvent]


class AssetIntegrity(StrictSchema):
    kind: Literal["none", "local_upload", "external", "invalid"]
    status: Literal["not_applicable", "present", "missing", "not_verified", "invalid_reference"]


class IntegrityIssue(StrictSchema):
    code: Literal["local_asset_missing", "invalid_asset_reference"]
    severity: Literal["warning"]


class ResourceIntegrityResponse(StrictSchema):
    checked_at: str
    resource_type: Literal["comercio", "publicacion", "historia"]
    resource_id: int
    lifecycle: str
    moderation_hidden: bool
    publicly_eligible: bool
    asset: AssetIntegrity
    issues: list[IntegrityIssue]
