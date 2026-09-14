"""Router local-only para inspeccionar OTP entregados por el fake."""

from ipaddress import ip_address

from fastapi import APIRouter, HTTPException, Request, Response

from app.core.config import settings
from app.modules.users.services.local_phone_otp_mailbox import (
    LocalPhoneOtpMailboxDelivery,
)


router = APIRouter(prefix="/__dev/phone-otp", tags=["Local development"])

_local_phone_otp_mailbox: LocalPhoneOtpMailboxDelivery | None = None
_LOCAL_RUNTIME_ENVIRONMENTS = frozenset({"local", "development", "dev", "test"})


def _is_loopback(value: str | None) -> bool:
    if not value:
        return False
    try:
        return ip_address(value).is_loopback
    except ValueError:
        return value.lower() == "localhost"


def get_local_phone_otp_mailbox() -> LocalPhoneOtpMailboxDelivery:
    global _local_phone_otp_mailbox
    if _local_phone_otp_mailbox is None:
        _local_phone_otp_mailbox = LocalPhoneOtpMailboxDelivery(
            ttl_seconds=settings.PHONE_OTP_FAKE_MAILBOX_TTL_SECONDS,
            max_messages=settings.PHONE_OTP_FAKE_MAILBOX_MAX_MESSAGES,
        )
    return _local_phone_otp_mailbox


def require_local_phone_otp_mailbox(request: Request) -> None:
    client_host = request.client.host if request.client else None
    enabled = (
        settings.RUNTIME_ENVIRONMENT.strip().lower() in _LOCAL_RUNTIME_ENVIRONMENTS
        and settings.PHONE_OTP_FAKE_MAILBOX_ENABLED
        and _is_loopback(client_host)
    )
    if not enabled:
        raise HTTPException(status_code=404, detail="Not Found")


@router.get("/messages")
def list_local_phone_otp_messages(request: Request, response: Response):
    require_local_phone_otp_mailbox(request)
    response.headers["Cache-Control"] = "private, no-store"
    return {"messages": get_local_phone_otp_mailbox().list_messages()}


@router.delete("/messages", status_code=204)
def clear_local_phone_otp_messages(request: Request, response: Response):
    require_local_phone_otp_mailbox(request)
    get_local_phone_otp_mailbox().clear_messages()
    response.headers["Cache-Control"] = "private, no-store"
    return response
