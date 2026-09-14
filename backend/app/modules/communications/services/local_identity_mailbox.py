"""Bandeja efimera local para validar EmailProvider sin red ni persistencia."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import threading
from typing import Callable

from app.modules.communications.providers.email_provider import (
    EmailMessage,
    FakeEmailProvider,
)


Clock = Callable[[], datetime]


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


@dataclass(frozen=True)
class LocalIdentityMailboxMessage:
    message_id: int
    created_at: datetime
    expires_at: datetime
    recipient: str
    subject: str
    body: str


class LocalIdentityMailboxProvider(FakeEmailProvider):
    """FakeEmailProvider acotado por TTL y capacidad; nunca persiste mensajes."""

    def __init__(self, *, ttl_seconds: int, max_messages: int, clock: Clock = utc_now):
        if ttl_seconds < 1 or max_messages < 1:
            raise ValueError("local_identity_mailbox_limits_invalid")
        super().__init__()
        self._ttl = timedelta(seconds=ttl_seconds)
        self._max_messages = max_messages
        self._clock = clock
        self._lock = threading.Lock()
        self._next_id = 1
        self._records: list[LocalIdentityMailboxMessage] = []

    def _purge(self, now: datetime) -> None:
        while self._records and self._records[0].expires_at <= now:
            self._records.pop(0)
            if self.messages:
                self.messages.pop(0)

    def send(self, message: EmailMessage) -> str:
        now = self._clock()
        with self._lock:
            self._purge(now)
            record = LocalIdentityMailboxMessage(
                message_id=self._next_id,
                created_at=now,
                expires_at=now + self._ttl,
                recipient=message.recipient,
                subject=message.subject,
                body=message.body,
            )
            self._next_id += 1
            self._records.append(record)
            self._records = self._records[-self._max_messages :]
            # Conserva compatibilidad observable del Fake existente sin dejar
            # crecer indefinidamente su lista publica.
            self.messages.append(message)
            self.messages = self.messages[-self._max_messages :]
            return f"fake:{record.message_id}"

    def list_messages(self) -> list[LocalIdentityMailboxMessage]:
        with self._lock:
            self._purge(self._clock())
            return list(reversed(self._records))

    def clear_messages(self) -> None:
        with self._lock:
            self._records.clear()
            self.messages.clear()
