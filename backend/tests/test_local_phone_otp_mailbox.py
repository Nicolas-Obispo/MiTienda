from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from fastapi import HTTPException, Request, Response

from app.modules.users.routes.local_phone_otp_mailbox_routers import (
    require_local_phone_otp_mailbox,
)
from app.modules.users.routes.usuarios_routers import (
    confirmar_verificacion_telefono,
    solicitar_verificacion_telefono,
)
from app.modules.users.schemas.usuarios_schemas import PhoneVerificationConfirmRequest
from app.modules.users.services.local_phone_otp_mailbox import (
    LocalPhoneOtpMailboxDelivery,
)


class LocalPhoneOtpMailboxTests(unittest.TestCase):
    def _request(self, host="127.0.0.1"):
        return Request({"type": "http", "client": (host, 50000)})

    def test_mailbox_is_memory_only_bounded_and_expires(self):
        now = datetime(2026, 9, 7, tzinfo=timezone.utc)
        provider = LocalPhoneOtpMailboxDelivery(
            ttl_seconds=60, max_messages=2, clock=lambda: now
        )
        provider.send(phone_e164="+5491111111111", code="111111", issuance_id="one")
        provider.send(phone_e164="+5491222222222", code="222222", issuance_id="two")
        provider.send(phone_e164="+5491333333333", code="333333", issuance_id="three")
        self.assertEqual(
            [message.code for message in provider.list_messages()],
            ["333333", "222222"],
        )
        now += timedelta(seconds=61)
        self.assertEqual(provider.list_messages(), [])

    def test_guard_requires_local_opt_in_and_loopback(self):
        values = {
            "RUNTIME_ENVIRONMENT": "local",
            "PHONE_OTP_FAKE_MAILBOX_ENABLED": True,
        }
        target = "app.modules.users.routes.local_phone_otp_mailbox_routers.settings"
        with patch.multiple(target, **values):
            require_local_phone_otp_mailbox(self._request())
            with self.assertRaises(HTTPException) as caught:
                require_local_phone_otp_mailbox(self._request("203.0.113.10"))
            self.assertEqual(caught.exception.status_code, 404)

        for key in values:
            changed = dict(values)
            changed[key] = False if isinstance(values[key], bool) else "production"
            with patch.multiple(target, **changed):
                with self.assertRaises(HTTPException) as caught:
                    require_local_phone_otp_mailbox(self._request())
                self.assertEqual(caught.exception.status_code, 404)

    def test_otp_endpoints_mark_private_responses_no_store(self):
        request = self._request()
        db = Mock()
        user = SimpleNamespace(id=7)
        values = {
            "RUNTIME_ENVIRONMENT": "local",
            "PHONE_OTP_FAKE_MAILBOX_ENABLED": True,
        }
        with patch.multiple(
            "app.modules.users.routes.local_phone_otp_mailbox_routers.settings",
            **values,
        ), patch(
            "app.modules.users.routes.usuarios_routers.issue_phone_challenge",
            return_value="challenge-id",
        ):
            response = Response()
            result = solicitar_verificacion_telefono(
                request=request,
                response=response,
                db=db,
                usuario_actual=user,
            )
            self.assertEqual(result, {"challenge_id": "challenge-id", "status": "sent"})
            self.assertEqual(response.headers["cache-control"], "private, no-store")

        with patch(
            "app.modules.users.routes.usuarios_routers.confirm_phone_challenge"
        ):
            response = Response()
            result = confirmar_verificacion_telefono(
                payload=PhoneVerificationConfirmRequest(
                    challenge_id="x" * 20, code="123456"
                ),
                response=response,
                db=db,
                usuario_actual=user,
            )
            self.assertEqual(result, {"status": "verified"})
            self.assertEqual(response.headers["cache-control"], "private, no-store")


if __name__ == "__main__":
    unittest.main()
