from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class EmailMessage:
    recipient: str
    sender: str
    subject: str
    body: str
    idempotency_key: str


class EmailProvider(Protocol):
    def send(self, message: EmailMessage) -> str: ...


class EmailDeliveryError(RuntimeError):
    def __init__(self, safe_code: str, *, retryable: bool):
        super().__init__(safe_code)
        self.safe_code = safe_code
        self.retryable = retryable


class FakeEmailProvider:
    """Provider sin red para tests; nunca se selecciona como envio real automatico."""

    def __init__(self, failure: EmailDeliveryError | None = None):
        self.failure = failure
        self.messages: list[EmailMessage] = []

    def send(self, message: EmailMessage) -> str:
        if self.failure is not None:
            raise self.failure
        self.messages.append(message)
        return f"fake:{len(self.messages)}"
