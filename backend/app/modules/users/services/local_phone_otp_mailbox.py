"""Bandeja efímera local para inspeccionar OTP fake sin persistencia."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import threading
from typing import Callable


Clock = Callable[[], datetime]


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


@dataclass(frozen=True)
class LocalPhoneOtpMailboxMessage:
    message_id: int
    created_at: datetime
    expires_at: datetime
    phone_e164: str
    code: str
    issuance_id: str


class LocalPhoneOtpMailboxDelivery:
    """Delivery fake local, acotado y sólo en memoria de proceso."""

    def __init__(self, *, ttl_seconds: int, max_messages: int, clock: Clock = utc_now):
        if ttl_seconds < 1 or max_messages < 1:
            raise ValueError("local_phone_otp_mailbox_limits_invalid")
        self._ttl = timedelta(seconds=ttl_seconds)
        self._max_messages = max_messages
        self._clock = clock
        self._lock = threading.Lock()
        self._next_id = 1
        self._records: list[LocalPhoneOtpMailboxMessage] = []

    def _purge(self, now: datetime) -> None:
        while self._records and self._records[0].expires_at <= now:
            self._records.pop(0)

    def send(self, *, phone_e164: str, code: str, issuance_id: str) -> None:
        now = self._clock()
        with self._lock:
            self._purge(now)
            self._records.append(
                LocalPhoneOtpMailboxMessage(
                    message_id=self._next_id,
                    created_at=now,
                    expires_at=now + self._ttl,
                    phone_e164=phone_e164,
                    code=code,
                    issuance_id=issuance_id,
                )
            )
            self._next_id += 1
            self._records = self._records[-self._max_messages :]

    def list_messages(self) -> list[LocalPhoneOtpMailboxMessage]:
        with self._lock:
            self._purge(self._clock())
            return list(reversed(self._records))

    def clear_messages(self) -> None:
        with self._lock:
            self._records.clear()
