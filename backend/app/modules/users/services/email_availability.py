"""Disponibilidad publica minima de email y mitigacion local de abuso."""

from collections import defaultdict, deque
from threading import Lock
from time import monotonic
from typing import Callable

from sqlalchemy.orm import Session

from app.modules.users.models.usuarios_models import Usuario
from app.modules.users.services.email_normalization import canonicalize_email


class EmailAvailabilityRateLimiter:
    """Ventana deslizante por cliente, acotada al proceso actual."""

    def __init__(
        self,
        limit: int = 30,
        window_seconds: int = 60,
        clock: Callable[[], float] = monotonic,
    ) -> None:
        self.limit = limit
        self.window_seconds = window_seconds
        self._clock = clock
        self._events: dict[str, deque[float]] = defaultdict(deque)
        self._lock = Lock()

    def allow(self, client_key: str) -> bool:
        now = self._clock()
        threshold = now - self.window_seconds
        with self._lock:
            events = self._events[client_key]
            while events and events[0] <= threshold:
                events.popleft()
            if len(events) >= self.limit:
                return False
            events.append(now)
            return True

    def reset(self) -> None:
        """Aisla tests; no forma parte del contrato HTTP."""

        with self._lock:
            self._events.clear()


email_availability_rate_limiter = EmailAvailabilityRateLimiter()


def is_email_available(db: Session, email: str) -> bool:
    """Consulta solamente existencia mediante el owner canonico backend."""

    canonical = canonicalize_email(email)
    existing = (
        db.query(Usuario.id)
        .filter(Usuario.email_canonical == canonical)
        .first()
    )
    return existing is None
