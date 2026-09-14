"""Adapters de entrega del unico motor de recuperacion de password."""

from __future__ import annotations

from typing import Protocol

EMAIL = "email"
SMS = "sms"
WHATSAPP = "whatsapp"
RECOVERY_CHANNELS = frozenset({EMAIL, SMS, WHATSAPP})


class RecoveryDeliveryUnavailable(RuntimeError):
    """Estado interno; nunca se expone desde el endpoint publico."""


class RecoveryDeliveryAdapter(Protocol):
    channel: str

    def deliver(self, **kwargs) -> None: ...


class DisabledRecoveryDeliveryAdapter:
    def __init__(self, channel: str):
        self.channel = channel

    def deliver(self, **kwargs) -> None:
        raise RecoveryDeliveryUnavailable(f"recovery_{self.channel}_disabled")


def phone_channel_enabled(channel: str) -> bool:
    """Disponibilidad infraestructural; no prueba identidad ni pertenencia."""
    if channel in {SMS, WHATSAPP}:
        # No existe adapter comercial aprobado en ET99.5-E. La configuracion
        # por si sola nunca convierte un canal en disponible.
        return False
    return False


def build_phone_recovery_adapter(channel: str) -> RecoveryDeliveryAdapter:
    # ET99.5-E no contiene providers comerciales reales.
    return DisabledRecoveryDeliveryAdapter(channel)
