"""Catalogo controlado de capacidades administrativas iniciales."""

MODERATION_REPORTS_READ = "moderation.reports.read"
MODERATION_DECISIONS_WRITE = "moderation.decisions.write"
OPERATIONS_STATUS_READ = "operations.status.read"
OPERATIONS_INCIDENTS_MANAGE = "operations.incidents.manage"

ADMINISTRATIVE_CAPABILITIES = frozenset(
    {
        MODERATION_REPORTS_READ,
        MODERATION_DECISIONS_WRITE,
        OPERATIONS_STATUS_READ,
        OPERATIONS_INCIDENTS_MANAGE,
    }
)


def validate_administrative_capability(capability: str) -> str:
    if capability not in ADMINISTRATIVE_CAPABILITIES:
        raise ValueError(f"Capacidad administrativa desconocida: {capability}")
    return capability
