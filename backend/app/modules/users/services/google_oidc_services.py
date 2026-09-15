"""Owner protocolario Google OIDC basado en Authlib.

El modulo no conoce Usuario ni FeedGoSession. Los tokens del provider viven
solo durante el canje y la validacion de este owner.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import hmac
from typing import Any, Callable
from urllib.parse import urlsplit

from authlib.integrations.httpx_client import AsyncOAuth2Client
from authlib.integrations.starlette_client import OAuth

from app.core.config import Settings, settings
from app.modules.users.services.oauth_authorization_transaction_services import (
    OAuthAuthorizationMaterial,
)


GOOGLE_PROVIDER = "google"
GOOGLE_SCOPES = "openid email"
GOOGLE_ALLOWED_ID_TOKEN_ALGORITHMS = ("RS256",)


class GoogleOidcError(RuntimeError):
    def __init__(self, code: str):
        super().__init__(code)
        self.code = code


@dataclass(frozen=True)
class GoogleOidcConfiguration:
    client_id: str
    client_secret: str
    discovery_url: str
    allowed_issuer: str
    redirect_uri: str
    public_base_url: str
    frontend_result_path: str
    timeout_seconds: float
    result_handle_ttl_seconds: int


@dataclass(frozen=True)
class GoogleOidcIdentity:
    subject: str
    email: str
    email_verified: bool


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _https_url(value: Any) -> bool:
    if not isinstance(value, str):
        return False
    parsed = urlsplit(value)
    return (
        parsed.scheme == "https"
        and bool(parsed.netloc)
        and parsed.username is None
        and parsed.password is None
        and not parsed.fragment
    )


def google_oidc_configuration(
    source: Settings = settings,
) -> GoogleOidcConfiguration:
    """Construye configuracion solo cuando Google fue habilitado explicitamente."""

    if not source.GOOGLE_IDENTITY_ENABLED:
        raise GoogleOidcError("google_identity_disabled")
    values = (
        source.GOOGLE_OIDC_CLIENT_ID,
        source.GOOGLE_OIDC_CLIENT_SECRET,
        source.GOOGLE_OIDC_REDIRECT_URI,
        source.GOOGLE_OIDC_PUBLIC_BASE_URL,
        source.ACCOUNT_ACTION_RATE_LIMIT_HMAC_SECRET,
    )
    if any(not isinstance(value, str) or not value.strip() for value in values):
        raise GoogleOidcError("google_oidc_configuration_invalid")
    if source.ACCOUNT_ACTION_RATE_LIMIT_HMAC_SECRET in {
        source.SECRET_KEY,
        source.RESEND_API_KEY,
        source.IDENTITY_RESEND_API_KEY,
    }:
        raise GoogleOidcError("google_oidc_configuration_invalid")
    redirect = urlsplit(source.GOOGLE_OIDC_REDIRECT_URI or "")
    public_base = urlsplit(source.GOOGLE_OIDC_PUBLIC_BASE_URL or "")
    result_path = source.GOOGLE_OIDC_FRONTEND_RESULT_PATH
    if (
        source.GOOGLE_OIDC_DISCOVERY_URL
        != "https://accounts.google.com/.well-known/openid-configuration"
        or source.GOOGLE_OIDC_ALLOWED_ISSUER != "https://accounts.google.com"
        or not _https_url(source.GOOGLE_OIDC_REDIRECT_URI)
        or not _https_url(source.GOOGLE_OIDC_PUBLIC_BASE_URL)
        or redirect.path != "/usuarios/google/callback"
        or redirect.query
        or public_base.path not in {"", "/"}
        or public_base.query
        or not result_path.startswith("/")
        or result_path.startswith("//")
        or "\\" in result_path
        or urlsplit(result_path).query
        or urlsplit(result_path).fragment
    ):
        raise GoogleOidcError("google_oidc_configuration_invalid")
    return GoogleOidcConfiguration(
        client_id=source.GOOGLE_OIDC_CLIENT_ID.strip(),
        client_secret=source.GOOGLE_OIDC_CLIENT_SECRET.strip(),
        discovery_url=source.GOOGLE_OIDC_DISCOVERY_URL,
        allowed_issuer=source.GOOGLE_OIDC_ALLOWED_ISSUER,
        redirect_uri=source.GOOGLE_OIDC_REDIRECT_URI,
        public_base_url=source.GOOGLE_OIDC_PUBLIC_BASE_URL.rstrip("/"),
        frontend_result_path=source.GOOGLE_OIDC_FRONTEND_RESULT_PATH,
        timeout_seconds=source.GOOGLE_OIDC_TIMEOUT_SECONDS,
        result_handle_ttl_seconds=source.GOOGLE_OIDC_RESULT_HANDLE_TTL_SECONDS,
    )


class GoogleOidcOwner:
    """Authorization Code + PKCE y validacion OIDC delegada a Authlib."""

    def __init__(
        self,
        configuration: GoogleOidcConfiguration,
        *,
        remote_app: Any | None = None,
        clock: Callable[[], datetime] = utc_now,
        oauth_client_class=AsyncOAuth2Client,
    ) -> None:
        self.configuration = configuration
        self._clock = clock
        self._oauth_client_class = oauth_client_class
        if remote_app is None:
            oauth = OAuth()
            remote_app = oauth.register(
                name="google",
                client_id=configuration.client_id,
                client_secret=configuration.client_secret,
                server_metadata_url=configuration.discovery_url,
                client_kwargs={
                    "scope": GOOGLE_SCOPES,
                    "timeout": configuration.timeout_seconds,
                },
            )
        self._remote_app = remote_app

    async def _metadata(self) -> dict[str, Any]:
        try:
            metadata = dict(await self._remote_app.load_server_metadata())
        except Exception as exc:
            raise GoogleOidcError("google_oidc_provider_unavailable") from exc
        required_urls = (
            metadata.get("authorization_endpoint"),
            metadata.get("token_endpoint"),
            metadata.get("jwks_uri"),
        )
        if (
            metadata.get("issuer") != self.configuration.allowed_issuer
            or any(not _https_url(value) for value in required_urls)
            or "RS256" not in metadata.get("id_token_signing_alg_values_supported", [])
        ):
            raise GoogleOidcError("google_oidc_metadata_invalid")
        # El discovery nunca amplia los algoritmos aceptados por FeedGo.
        metadata["id_token_signing_alg_values_supported"] = list(
            GOOGLE_ALLOWED_ID_TOKEN_ALGORITHMS
        )
        if hasattr(self._remote_app, "server_metadata"):
            self._remote_app.server_metadata.update(metadata)
        return metadata

    async def create_authorization_url(
        self,
        material: OAuthAuthorizationMaterial,
    ) -> str:
        metadata = await self._metadata()
        async with self._oauth_client_class(
            client_id=self.configuration.client_id,
            client_secret=self.configuration.client_secret,
            scope=GOOGLE_SCOPES,
            redirect_uri=self.configuration.redirect_uri,
            code_challenge_method="S256",
            token_endpoint_auth_method="client_secret_post",
            timeout=self.configuration.timeout_seconds,
        ) as client:
            url, returned_state = client.create_authorization_url(
                metadata["authorization_endpoint"],
                state=material.state,
                nonce=material.nonce,
                code_challenge=material.pkce_challenge,
                code_challenge_method="S256",
                response_type="code",
                scope=GOOGLE_SCOPES,
            )
        if not hmac.compare_digest(returned_state, material.state):
            raise GoogleOidcError("google_oidc_state_generation_failed")
        return url

    async def exchange_and_validate(
        self,
        *,
        code: str,
        pkce_verifier: str,
        expected_nonce_digest: str,
    ) -> GoogleOidcIdentity:
        if not code or not pkce_verifier or len(expected_nonce_digest) != 64:
            raise GoogleOidcError("google_oidc_callback_invalid")
        metadata = await self._metadata()
        try:
            async with self._oauth_client_class(
                client_id=self.configuration.client_id,
                client_secret=self.configuration.client_secret,
                scope=GOOGLE_SCOPES,
                redirect_uri=self.configuration.redirect_uri,
                code_challenge_method="S256",
                token_endpoint_auth_method="client_secret_post",
                timeout=self.configuration.timeout_seconds,
            ) as client:
                token = await client.fetch_token(
                    metadata["token_endpoint"],
                    grant_type="authorization_code",
                    code=code,
                    code_verifier=pkce_verifier,
                    redirect_uri=self.configuration.redirect_uri,
                )
            if not isinstance(token.get("id_token"), str):
                raise GoogleOidcError("google_oidc_token_invalid")
            claims = await self._remote_app.parse_id_token(
                token,
                nonce=None,
                claims_options={
                    "iss": {"values": [self.configuration.allowed_issuer]},
                    "aud": {"values": [self.configuration.client_id]},
                },
                leeway=0,
            )
        except GoogleOidcError:
            raise
        except Exception as exc:
            raise GoogleOidcError("google_oidc_token_invalid") from exc

        now_epoch = int(self._clock().astimezone(timezone.utc).timestamp())
        nonce = claims.get("nonce")
        subject = claims.get("sub")
        email = claims.get("email")
        audience = claims.get("aud")
        audience_is_valid = (
            isinstance(audience, str)
            and bool(audience)
            or isinstance(audience, list)
            and bool(audience)
            and all(isinstance(item, str) and bool(item) for item in audience)
        )
        audiences = audience if isinstance(audience, list) else [audience]
        if (
            claims.get("iss") != self.configuration.allowed_issuer
            or not audience_is_valid
            or self.configuration.client_id not in audiences
            or (claims.get("azp") is not None and claims.get("azp") != self.configuration.client_id)
            or isinstance(claims.get("exp"), bool)
            or not isinstance(claims.get("exp"), (int, float))
            or claims["exp"] <= now_epoch
            or isinstance(claims.get("iat"), bool)
            or not isinstance(claims.get("iat"), (int, float))
            or claims["iat"] > now_epoch
            or not isinstance(nonce, str)
            or not hmac.compare_digest(
                hashlib.sha256(nonce.encode("utf-8")).hexdigest(),
                expected_nonce_digest,
            )
            or not isinstance(subject, str)
            or not subject.strip()
            or len(subject) > 255
            or not isinstance(email, str)
            or not email.strip()
            or len(email) > 255
            or claims.get("email_verified") is not True
        ):
            raise GoogleOidcError("google_oidc_claims_invalid")
        return GoogleOidcIdentity(
            subject=subject,
            email=email,
            email_verified=True,
        )
