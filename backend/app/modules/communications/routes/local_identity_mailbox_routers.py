"""Router local-only para inspeccionar correo fake de identidad."""

from ipaddress import ip_address
from urllib.parse import urlsplit

from fastapi import APIRouter, HTTPException, Request, Response

from app.core.config import settings
from app.modules.communications.services.email_provider_factory import (
    get_local_identity_mailbox_provider,
)


router = APIRouter(prefix="/__dev/identity-email", tags=["Local development"])


def _is_loopback(value: str | None) -> bool:
    if not value:
        return False
    try:
        return ip_address(value).is_loopback
    except ValueError:
        return value.lower() == "localhost"


def require_local_fake_mailbox(request: Request) -> None:
    public_host = urlsplit(settings.IDENTITY_EMAIL_PUBLIC_BASE_URL or "").hostname
    client_host = request.client.host if request.client else None
    enabled = (
        settings.RUNTIME_ENVIRONMENT.strip().lower() in {"local", "development", "test"}
        and settings.IDENTITY_FAKE_MAILBOX_ENABLED
        and settings.IDENTITY_EMAIL_ENABLED
        and settings.IDENTITY_EMAIL_PROVIDER.strip().lower() == "fake"
        and _is_loopback(public_host)
        and _is_loopback(client_host)
    )
    if not enabled:
        # No revela que el harness exista cuando no esta habilitado localmente.
        raise HTTPException(status_code=404, detail="Not Found")


@router.get("/messages")
def list_local_identity_messages(request: Request, response: Response):
    require_local_fake_mailbox(request)
    response.headers["Cache-Control"] = "no-store"
    return {"messages": get_local_identity_mailbox_provider().list_messages()}


@router.delete("/messages", status_code=204)
def clear_local_identity_messages(request: Request, response: Response):
    require_local_fake_mailbox(request)
    get_local_identity_mailbox_provider().clear_messages()
    response.headers["Cache-Control"] = "no-store"
    return response
