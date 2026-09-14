from datetime import datetime, timedelta, timezone
import unittest
from unittest.mock import patch

from fastapi import HTTPException, Request

from app.modules.communications.providers.email_provider import EmailMessage
from app.modules.communications.routes.local_identity_mailbox_routers import (
    require_local_fake_mailbox,
)
from app.modules.communications.services.local_identity_mailbox import (
    LocalIdentityMailboxProvider,
)
from app.modules.communications.services.identity_email_services import (
    build_identity_action_link,
)


class LocalIdentityMailboxTests(unittest.TestCase):
    def _request(self, host="127.0.0.1"):
        return Request({"type": "http", "client": (host, 50000)})

    def _message(self, marker):
        return EmailMessage(
            recipient="person@example.test",
            sender="identity@example.test",
            subject="FeedGo",
            body=f"https://localhost/verificar-email#token={marker}",
            idempotency_key=marker,
        )

    def test_mailbox_is_memory_only_bounded_and_expires(self):
        now = datetime(2026, 9, 5, tzinfo=timezone.utc)
        clock = lambda: now
        provider = LocalIdentityMailboxProvider(ttl_seconds=60, max_messages=2, clock=clock)
        provider.send(self._message("one"))
        provider.send(self._message("two"))
        provider.send(self._message("three"))
        self.assertEqual([item.body.rsplit("=", 1)[-1] for item in provider.list_messages()], ["three", "two"])
        now += timedelta(seconds=61)
        self.assertEqual(provider.list_messages(), [])
        self.assertEqual(provider.messages, [])

    def test_clear_discards_all_sensitive_messages(self):
        provider = LocalIdentityMailboxProvider(ttl_seconds=60, max_messages=2)
        provider.send(self._message("secret"))
        provider.clear_messages()
        self.assertEqual(provider.list_messages(), [])
        self.assertEqual(provider.messages, [])

    def test_guard_requires_every_local_fake_condition(self):
        values = {
            "RUNTIME_ENVIRONMENT": "local",
            "IDENTITY_FAKE_MAILBOX_ENABLED": True,
            "IDENTITY_EMAIL_ENABLED": True,
            "IDENTITY_EMAIL_PROVIDER": "fake",
            "IDENTITY_EMAIL_PUBLIC_BASE_URL": "http://localhost:5173",
        }
        with patch.multiple("app.modules.communications.routes.local_identity_mailbox_routers.settings", **values):
            require_local_fake_mailbox(self._request())
            with self.assertRaises(HTTPException):
                require_local_fake_mailbox(self._request("203.0.113.10"))

        for key in values:
            changed = dict(values)
            changed[key] = False if isinstance(values[key], bool) else (
                "resend" if key == "IDENTITY_EMAIL_PROVIDER" else "https://feedgo.example"
            )
            with patch.multiple("app.modules.communications.routes.local_identity_mailbox_routers.settings", **changed):
                with self.assertRaises(HTTPException) as caught:
                    require_local_fake_mailbox(self._request())
                self.assertEqual(caught.exception.status_code, 404)

    def test_mailbox_is_inaccessible_in_production_even_with_fake_configuration(self):
        values = {
            "RUNTIME_ENVIRONMENT": "production",
            "IDENTITY_FAKE_MAILBOX_ENABLED": True,
            "IDENTITY_EMAIL_ENABLED": True,
            "IDENTITY_EMAIL_PROVIDER": "fake",
            "IDENTITY_EMAIL_PUBLIC_BASE_URL": "https://feedgo.example",
        }
        with patch.multiple("app.modules.communications.routes.local_identity_mailbox_routers.settings", **values):
            with self.assertRaises(HTTPException) as caught:
                require_local_fake_mailbox(self._request())
        self.assertEqual(caught.exception.status_code, 404)

    def test_http_action_links_are_allowed_only_for_opt_in_loopback_fake(self):
        values = {
            "RUNTIME_ENVIRONMENT": "local",
            "IDENTITY_FAKE_MAILBOX_ENABLED": True,
            "IDENTITY_EMAIL_ENABLED": True,
            "IDENTITY_EMAIL_PROVIDER": "fake",
        }
        with patch.multiple("app.modules.communications.services.identity_email_services.settings", **values):
            link = build_identity_action_link(
                purpose="email_verification",
                secret="temporary-secret",
                public_base_url="http://localhost:5173",
            )
            self.assertEqual(link, "http://localhost:5173/verificar-email#token=temporary-secret")
            with self.assertRaises(ValueError):
                build_identity_action_link(
                    purpose="email_verification",
                    secret="temporary-secret",
                    public_base_url="http://feedgo.example",
                )


if __name__ == "__main__":
    unittest.main()
