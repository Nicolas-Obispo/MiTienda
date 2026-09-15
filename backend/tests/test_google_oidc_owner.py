import asyncio
from datetime import datetime, timezone
from urllib.parse import parse_qs, urlsplit
import unittest
from unittest.mock import AsyncMock

from authlib.integrations.httpx_client import AsyncOAuth2Client
from authlib.jose import JsonWebKey, jwt

from app.core.config import Settings
from app.modules.users.services.google_oidc_services import (
    GoogleOidcConfiguration,
    GoogleOidcError,
    GoogleOidcOwner,
    google_oidc_configuration,
)
from app.modules.users.services.oauth_authorization_transaction_services import (
    OAuthAuthorizationMaterial,
)


NOW = datetime.now(timezone.utc).replace(microsecond=0)


class FakeRemote:
    def __init__(self, claims=None, error=None, metadata=None):
        self.claims = claims or {}
        self.error = error
        self.server_metadata = {}
        self._metadata = metadata or {
            "issuer": "https://accounts.google.com",
            "authorization_endpoint": "https://accounts.google.com/o/oauth2/v2/auth",
            "token_endpoint": "https://oauth2.googleapis.com/token",
            "jwks_uri": "https://www.googleapis.com/oauth2/v3/certs",
            "id_token_signing_alg_values_supported": ["RS256"],
        }
        self.parse_calls = []

    async def load_server_metadata(self):
        return self._metadata

    async def parse_id_token(self, token, **kwargs):
        self.parse_calls.append((token, kwargs))
        if self.error:
            raise self.error
        return self.claims


class FakeOAuthClient:
    token = {"access_token": "ephemeral", "id_token": "signed-id-token"}
    last_kwargs = None
    fetch_kwargs = None

    def __init__(self, **kwargs):
        type(self).last_kwargs = kwargs

    async def __aenter__(self):
        return self

    async def __aexit__(self, *_):
        return False

    async def fetch_token(self, endpoint, **kwargs):
        type(self).fetch_kwargs = (endpoint, kwargs)
        return dict(type(self).token)


def config():
    return GoogleOidcConfiguration(
        client_id="feedgo-client",
        client_secret="test-secret",
        discovery_url="https://accounts.google.com/.well-known/openid-configuration",
        allowed_issuer="https://accounts.google.com",
        redirect_uri="https://api.feedgo.test/usuarios/google/callback",
        public_base_url="https://feedgo.test",
        frontend_result_path="/auth/google/resultado",
        timeout_seconds=5,
        result_handle_ttl_seconds=120,
    )


def material():
    return OAuthAuthorizationMaterial(
        transaction_id="tx",
        state="state-value",
        nonce="nonce-value",
        pkce_challenge="pkce-challenge",
        expires_at=NOW,
    )


def valid_claims(**overrides):
    values = {
        "iss": "https://accounts.google.com",
        "aud": "feedgo-client",
        "azp": "feedgo-client",
        "exp": int(NOW.timestamp()) + 300,
        "iat": int(NOW.timestamp()),
        "nonce": "nonce-value",
        "sub": "google-subject",
        "email": "person@example.com",
        "email_verified": True,
    }
    values.update(overrides)
    return values


class GoogleOidcOwnerTests(unittest.TestCase):
    def test_config_is_disabled_by_default_and_enabled_configuration_is_fail_closed(self):
        self.assertFalse(Settings.model_fields["GOOGLE_IDENTITY_ENABLED"].default)
        source = Settings(
            _env_file=None,
            DATABASE_URL="sqlite://",
            SECRET_KEY="test",
            ALGORITHM="HS256",
            ACCESS_TOKEN_EXPIRE_MINUTES=60,
        )
        with self.assertRaises(GoogleOidcError):
            google_oidc_configuration(source)
        with self.assertRaises(ValueError):
            Settings(
                _env_file=None,
                DATABASE_URL="sqlite://",
                SECRET_KEY="test",
                ALGORITHM="HS256",
                ACCESS_TOKEN_EXPIRE_MINUTES=60,
                GOOGLE_IDENTITY_ENABLED=True,
            )

    def test_complete_https_configuration_is_accepted(self):
        source = Settings(
            _env_file=None,
            DATABASE_URL="sqlite://",
            SECRET_KEY="jwt-test-secret",
            ALGORITHM="HS256",
            ACCESS_TOKEN_EXPIRE_MINUTES=60,
            ACCOUNT_ACTION_RATE_LIMIT_HMAC_SECRET="rate-limit-test-secret",
            GOOGLE_IDENTITY_ENABLED=True,
            GOOGLE_OIDC_CLIENT_ID="feedgo-client",
            GOOGLE_OIDC_CLIENT_SECRET="google-test-secret",
            GOOGLE_OIDC_REDIRECT_URI=(
                "https://api.feedgo.test/usuarios/google/callback"
            ),
            GOOGLE_OIDC_PUBLIC_BASE_URL="https://feedgo.test",
        )
        self.assertEqual(google_oidc_configuration(source).client_id, "feedgo-client")

    def test_result_handle_ttl_cannot_exceed_two_minutes(self):
        with self.assertRaises(ValueError):
            Settings(
                _env_file=None,
                DATABASE_URL="sqlite://",
                SECRET_KEY="jwt-test-secret",
                ALGORITHM="HS256",
                ACCESS_TOKEN_EXPIRE_MINUTES=60,
                GOOGLE_OIDC_RESULT_HANDLE_TTL_SECONDS=121,
            )

    def test_http_redirect_is_rejected_when_google_is_enabled(self):
        with self.assertRaises(ValueError):
            Settings(
                _env_file=None,
                DATABASE_URL="sqlite://",
                SECRET_KEY="jwt-test-secret",
                ALGORITHM="HS256",
                ACCESS_TOKEN_EXPIRE_MINUTES=60,
                ACCOUNT_ACTION_RATE_LIMIT_HMAC_SECRET="rate-limit-test-secret",
                GOOGLE_IDENTITY_ENABLED=True,
                GOOGLE_OIDC_CLIENT_ID="feedgo-client",
                GOOGLE_OIDC_CLIENT_SECRET="google-test-secret",
                GOOGLE_OIDC_REDIRECT_URI=(
                    "http://api.feedgo.test/usuarios/google/callback"
                ),
                GOOGLE_OIDC_PUBLIC_BASE_URL="https://feedgo.test",
            )

    def test_url_credentials_are_rejected_when_google_is_enabled(self):
        with self.assertRaises(ValueError):
            Settings(
                _env_file=None,
                DATABASE_URL="sqlite://",
                SECRET_KEY="jwt-test-secret",
                ALGORITHM="HS256",
                ACCESS_TOKEN_EXPIRE_MINUTES=60,
                ACCOUNT_ACTION_RATE_LIMIT_HMAC_SECRET="rate-limit-test-secret",
                GOOGLE_IDENTITY_ENABLED=True,
                GOOGLE_OIDC_CLIENT_ID="feedgo-client",
                GOOGLE_OIDC_CLIENT_SECRET="google-test-secret",
                GOOGLE_OIDC_REDIRECT_URI=(
                    "https://user:password@api.feedgo.test/usuarios/google/callback"
                ),
                GOOGLE_OIDC_PUBLIC_BASE_URL="https://feedgo.test",
            )

    def test_authorization_url_uses_exact_scope_state_nonce_redirect_and_pkce_s256(self):
        owner = GoogleOidcOwner(config(), remote_app=FakeRemote())
        url = asyncio.run(owner.create_authorization_url(material()))
        query = parse_qs(urlsplit(url).query)
        self.assertEqual(query["scope"], ["openid email"])
        self.assertEqual(query["state"], ["state-value"])
        self.assertEqual(query["nonce"], ["nonce-value"])
        self.assertEqual(query["code_challenge"], ["pkce-challenge"])
        self.assertEqual(query["code_challenge_method"], ["S256"])
        self.assertEqual(
            query["redirect_uri"],
            ["https://api.feedgo.test/usuarios/google/callback"],
        )

    def test_default_authlib_remote_uses_async_oauth2_client(self):
        owner = GoogleOidcOwner(config())
        self.assertIs(owner._remote_app.client_cls, AsyncOAuth2Client)

    def test_token_exchange_uses_pkce_and_validates_verified_claims(self):
        remote = FakeRemote(valid_claims())
        owner = GoogleOidcOwner(
            config(),
            remote_app=remote,
            oauth_client_class=FakeOAuthClient,
            clock=lambda: NOW,
        )
        identity = asyncio.run(
            owner.exchange_and_validate(
                code="authorization-code",
                pkce_verifier="verifier",
                expected_nonce_digest=(
                    "efb4e26c3deb3dd5e04408769d1b6b371ae1e7acbe1e32332550b06f784780f2"
                ),
            )
        )
        self.assertEqual(identity.subject, "google-subject")
        endpoint, kwargs = FakeOAuthClient.fetch_kwargs
        self.assertEqual(endpoint, "https://oauth2.googleapis.com/token")
        self.assertEqual(kwargs["code_verifier"], "verifier")
        self.assertEqual(kwargs["redirect_uri"], config().redirect_uri)
        self.assertEqual(remote.parse_calls[0][1]["leeway"], 0)
        self.assertIsNone(remote.parse_calls[0][1]["nonce"])

    def test_invalid_signature_or_algorithm_from_authlib_is_rejected(self):
        for error in (ValueError("bad signature"), ValueError("unsupported alg")):
            owner = GoogleOidcOwner(
                config(),
                remote_app=FakeRemote(error=error),
                oauth_client_class=FakeOAuthClient,
                clock=lambda: NOW,
            )
            with self.assertRaises(GoogleOidcError):
                asyncio.run(
                    owner.exchange_and_validate(
                        code="code",
                        pkce_verifier="verifier",
                        expected_nonce_digest="0" * 64,
                    )
                )

    def test_authlib_rejects_bad_signature_and_unexpected_algorithm_cryptographically(self):
        valid_key = JsonWebKey.generate_key(
            "RSA", 2048, is_private=True, options={"kid": "valid-key"}
        )
        other_key = JsonWebKey.generate_key(
            "RSA", 2048, is_private=True, options={"kid": "valid-key"}
        )
        remote_owner = GoogleOidcOwner(
            config(),
            oauth_client_class=FakeOAuthClient,
            clock=lambda: NOW,
        )
        metadata = FakeRemote()._metadata
        remote_owner._remote_app.load_server_metadata = AsyncMock(return_value=metadata)
        remote_owner._remote_app.fetch_jwk_set = AsyncMock(
            return_value={"keys": [valid_key.as_dict(is_private=False)]}
        )
        expected_nonce = (
            "efb4e26c3deb3dd5e04408769d1b6b371ae1e7acbe1e32332550b06f784780f2"
        )
        for encoded in (
            jwt.encode(
                {"alg": "RS256", "kid": "valid-key"},
                valid_claims(),
                other_key.as_dict(is_private=True),
            ).decode("ascii"),
            jwt.encode(
                {"alg": "HS256"},
                valid_claims(),
                b"test-signing-key-with-sufficient-length",
            ).decode("ascii"),
        ):
            with self.subTest(header=encoded.split(".", 1)[0]):
                FakeOAuthClient.token = {
                    "access_token": "ephemeral",
                    "id_token": encoded,
                }
                with self.assertRaises(GoogleOidcError):
                    asyncio.run(
                        remote_owner.exchange_and_validate(
                            code="code",
                            pkce_verifier="verifier",
                            expected_nonce_digest=expected_nonce,
                        )
                    )
        FakeOAuthClient.token = {
            "access_token": "ephemeral",
            "id_token": "signed-id-token",
        }

    def test_authlib_accepts_a_valid_rs256_id_token(self):
        key = JsonWebKey.generate_key(
            "RSA", 2048, is_private=True, options={"kid": "valid-key"}
        )
        owner = GoogleOidcOwner(
            config(),
            oauth_client_class=FakeOAuthClient,
            clock=lambda: NOW,
        )
        owner._remote_app.load_server_metadata = AsyncMock(
            return_value=FakeRemote()._metadata
        )
        owner._remote_app.fetch_jwk_set = AsyncMock(
            return_value={"keys": [key.as_dict(is_private=False)]}
        )
        FakeOAuthClient.token = {
            "access_token": "ephemeral",
            "id_token": jwt.encode(
                {"alg": "RS256", "kid": "valid-key"},
                valid_claims(),
                key.as_dict(is_private=True),
            ).decode("ascii"),
        }
        identity = asyncio.run(
            owner.exchange_and_validate(
                code="code",
                pkce_verifier="verifier",
                expected_nonce_digest=(
                    "efb4e26c3deb3dd5e04408769d1b6b371ae1e7acbe1e32332550b06f784780f2"
                ),
            )
        )
        self.assertEqual(identity.subject, "google-subject")
        FakeOAuthClient.token = {
            "access_token": "ephemeral",
            "id_token": "signed-id-token",
        }

    def test_all_required_oidc_claim_failures_are_rejected(self):
        bad_claims = (
            {"iss": "https://issuer.invalid"},
            {"aud": "other-client"},
            {"aud": ["feedgo-client", 123]},
            {"azp": "other-client"},
            {"exp": int(NOW.timestamp())},
            {"iat": int(NOW.timestamp()) + 1},
            {"nonce": "wrong"},
            {"sub": ""},
            {"email": ""},
            {"email_verified": False},
        )
        expected_nonce = (
            "efb4e26c3deb3dd5e04408769d1b6b371ae1e7acbe1e32332550b06f784780f2"
        )
        for overrides in bad_claims:
            with self.subTest(overrides=overrides):
                owner = GoogleOidcOwner(
                    config(),
                    remote_app=FakeRemote(valid_claims(**overrides)),
                    oauth_client_class=FakeOAuthClient,
                    clock=lambda: NOW,
                )
                with self.assertRaises(GoogleOidcError):
                    asyncio.run(
                        owner.exchange_and_validate(
                            code="code",
                            pkce_verifier="verifier",
                            expected_nonce_digest=expected_nonce,
                        )
                    )

    def test_discovery_cannot_expand_allowed_algorithm_or_issuer(self):
        metadata = FakeRemote()._metadata | {
            "id_token_signing_alg_values_supported": ["HS256"]
        }
        owner = GoogleOidcOwner(config(), remote_app=FakeRemote(metadata=metadata))
        with self.assertRaises(GoogleOidcError):
            asyncio.run(owner.create_authorization_url(material()))


if __name__ == "__main__":
    unittest.main()
