SEVERITIES = frozenset({"sev1_critical", "sev2_high", "sev3_medium", "sev4_low"})
SEVERITY_DEFINITIONS = {
    "sev1_critical": "seguridad, datos o indisponibilidad critica",
    "sev2_high": "funcion critica o degradacion grave",
    "sev3_medium": "impacto parcial con alternativa",
    "sev4_low": "impacto bajo y acotado",
}
INCIDENT_TYPES = frozenset({"availability", "security", "privacy", "data_integrity", "dependency", "storage_media", "configuration", "other"})
STATUSES = frozenset({"open", "investigating", "contained", "resolved", "reviewed"})
RISK_LEVELS = frozenset({"none", "low", "medium", "high", "critical"})
LEGAL_ASSESSMENT_STATUSES = frozenset({"pending", "not_required", "required", "completed"})
PERSONAL_DATA_IMPACTS = frozenset({"unknown", "none", "suspected", "confirmed"})
COMMUNICATION_STATUSES = frozenset({"pending", "not_required", "required", "completed"})
EVIDENCE_TYPES = frozenset({"alert", "request", "correlation", "backup_evidence", "restore_evidence", "health_check", "log_event", "other_reference"})
ACTIONS = frozenset({"start_investigation", "record_finding", "contain", "resolve", "review", "reopen", "change_severity", "assign_owner", "record_legal_assessment", "record_evidence_reference"})

TRANSITIONS = {
    "start_investigation": ({"open"}, "investigating"),
    "contain": ({"investigating"}, "contained"),
    "resolve": ({"investigating", "contained"}, "resolved"),
    "review": ({"resolved"}, "reviewed"),
    "reopen": ({"contained", "resolved"}, "investigating"),
}
