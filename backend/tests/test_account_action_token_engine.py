import re
import unittest
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

from sqlalchemy import create_engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import Base
from app.core.model_registry import import_all_models
from app.modules.users.models.identity_models import AccountActionToken
from app.modules.users.models.usuarios_models import Usuario
from app.modules.users.services.account_action_token_services import (
    ADMINISTRATIVE,
    EMAIL_VERIFICATION,
    PASSWORD_CHANGED,
    PASSWORD_RESET,
    AccountActionPurposeInvalidError,
    AccountActionInvalidationReasonError,
    AccountActionTokenInvalidError,
    derive_token_state,
    digest_token_secret,
    generate_token_secret,
    invalidate_account_action_tokens,
    issue_account_action_token,
    consume_account_action_token,
)


import_all_models()


class ControlledClock:
    def __init__(self, value: datetime):
        self.value = value

    def __call__(self) -> datetime:
        return self.value


class AccountActionTokenEngineTests(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine(
            "sqlite://",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        db = self.Session()
        db.add(
            Usuario(
                id=1,
                email="Persona@Example.com",
                email_canonical="persona@example.com",
                hashed_password="$2b$test",
            )
        )
        db.commit()
        db.close()
        self.now = datetime(2026, 9, 5, 12, 0, tzinfo=timezone.utc)
        self.clock = ControlledClock(self.now)

    def tearDown(self):
        Base.metadata.drop_all(self.engine)
        self.engine.dispose()

    def issue(self, purpose=EMAIL_VERIFICATION, **kwargs):
        db = self.Session()
        try:
            return issue_account_action_token(
                db=db,
                usuario_id=1,
                purpose=purpose,
                clock=self.clock,
                **kwargs,
            )
        finally:
            db.close()

    def test_secret_is_random_base64url_without_padding_and_has_256_bits(self):
        first = generate_token_secret()
        second = generate_token_secret()
        self.assertNotEqual(first, second)
        self.assertEqual(len(first), 43)
        self.assertRegex(first, re.compile(r"^[A-Za-z0-9_-]+$"))
        self.assertNotIn("=", first)
        with self.assertRaises(ValueError):
            generate_token_secret(entropy_bytes=31)

    def test_digest_is_deterministic_and_safe_error_does_not_echo_secret(self):
        secret = "A" * 43
        self.assertEqual(digest_token_secret(secret), digest_token_secret(secret))
        self.assertEqual(len(digest_token_secret(secret)), 64)
        sensitive = "secreto-no-ascii-ñ"
        with self.assertRaises(AccountActionTokenInvalidError) as raised:
            digest_token_secret(sensitive)
        self.assertNotIn(sensitive, str(raised.exception))
        self.assertNotIn(sensitive, repr(raised.exception))

    def test_database_never_contains_secret(self):
        issued = self.issue(random_bytes=lambda size: b"x" * size)
        db = self.Session()
        token = db.get(AccountActionToken, issued.token_id)
        persisted_strings = [
            value
            for value in (
                token.purpose,
                token.token_digest,
                token.email_canonical_snapshot,
                token.invalidation_reason,
                token.issuance_id,
            )
            if value is not None
        ]
        self.assertTrue(all(issued.secret not in value for value in persisted_strings))
        self.assertEqual(token.token_digest, digest_token_secret(issued.secret))
        db.close()

    def test_ttl_is_exact_for_each_purpose(self):
        verification = self.issue(EMAIL_VERIFICATION)
        reset = self.issue(PASSWORD_RESET)
        self.assertEqual(verification.expires_at - self.now, timedelta(hours=24))
        self.assertEqual(reset.expires_at - self.now, timedelta(minutes=30))

    def test_new_issue_supersedes_only_active_same_purpose(self):
        first = self.issue(EMAIL_VERIFICATION)
        reset = self.issue(PASSWORD_RESET)
        second = self.issue(EMAIL_VERIFICATION)
        db = self.Session()
        first_row = db.get(AccountActionToken, first.token_id)
        reset_row = db.get(AccountActionToken, reset.token_id)
        second_row = db.get(AccountActionToken, second.token_id)
        self.assertEqual(derive_token_state(first_row, now=self.now), "invalidated")
        self.assertEqual(first_row.invalidation_reason, "superseded")
        self.assertEqual(derive_token_state(reset_row, now=self.now), "active")
        self.assertEqual(derive_token_state(second_row, now=self.now), "active")
        db.close()

    def test_wrong_purpose_is_rejected_without_consuming(self):
        issued = self.issue(EMAIL_VERIFICATION)
        db = self.Session()
        with self.assertRaises(AccountActionTokenInvalidError):
            consume_account_action_token(
                db=db,
                secret=issued.secret,
                purpose=PASSWORD_RESET,
                clock=self.clock,
            )
        db.close()
        db = self.Session()
        self.assertEqual(derive_token_state(db.get(AccountActionToken, issued.token_id), now=self.now), "active")
        db.close()
        with self.assertRaises(AccountActionPurposeInvalidError):
            self.issue("other")

    def test_expired_consumed_and_invalidated_are_rejected(self):
        expired = self.issue(PASSWORD_RESET)
        self.clock.value = self.now + timedelta(minutes=30)
        db = self.Session()
        with self.assertRaises(AccountActionTokenInvalidError):
            consume_account_action_token(
                db=db, secret=expired.secret, purpose=PASSWORD_RESET, clock=self.clock
            )
        db.close()

        self.clock.value = self.now
        consumed = self.issue(EMAIL_VERIFICATION)
        db = self.Session()
        consume_account_action_token(
            db=db, secret=consumed.secret, purpose=EMAIL_VERIFICATION, clock=self.clock
        )
        with self.assertRaises(AccountActionTokenInvalidError):
            consume_account_action_token(
                db=db, secret=consumed.secret, purpose=EMAIL_VERIFICATION, clock=self.clock
            )
        db.close()

        invalidated = self.issue(PASSWORD_RESET)
        db = self.Session()
        invalidate_account_action_tokens(
            db=db,
            usuario_id=1,
            purpose=PASSWORD_RESET,
            reason=ADMINISTRATIVE,
            clock=self.clock,
        )
        with self.assertRaises(AccountActionTokenInvalidError):
            consume_account_action_token(
                db=db, secret=invalidated.secret, purpose=PASSWORD_RESET, clock=self.clock
            )
        db.close()

    def test_snapshot_mismatch_is_rejected(self):
        issued = self.issue()
        db = self.Session()
        db.get(Usuario, 1).email_canonical = "nuevo@example.com"
        db.commit()
        with self.assertRaises(AccountActionTokenInvalidError):
            consume_account_action_token(
                db=db,
                secret=issued.secret,
                purpose=EMAIL_VERIFICATION,
                clock=self.clock,
            )
        self.assertIsNone(db.get(AccountActionToken, issued.token_id).consumed_at)
        db.close()

    def test_consumption_has_only_one_winner(self):
        issued = self.issue()
        db = self.Session()
        consumed = consume_account_action_token(
            db=db, secret=issued.secret, purpose=EMAIL_VERIFICATION, clock=self.clock
        )
        self.assertEqual(derive_token_state(consumed, now=self.now), "consumed")
        with self.assertRaises(AccountActionTokenInvalidError):
            consume_account_action_token(
                db=db, secret=issued.secret, purpose=EMAIL_VERIFICATION, clock=self.clock
            )
        db.close()

    def test_rollback_restores_previous_token_when_new_insert_fails(self):
        first = self.issue(issuance_id_factory=lambda: "same-issuance")
        with self.assertRaises(IntegrityError):
            self.issue(issuance_id_factory=lambda: "same-issuance")
        db = self.Session()
        token = db.get(AccountActionToken, first.token_id)
        self.assertEqual(derive_token_state(token, now=self.now), "active")
        self.assertIsNone(token.invalidation_reason)
        self.assertEqual(db.query(AccountActionToken).count(), 1)
        db.close()

    def test_password_changed_and_administrative_invalidation(self):
        first = self.issue(PASSWORD_RESET)
        db = self.Session()
        self.assertEqual(
            invalidate_account_action_tokens(
                db=db,
                usuario_id=1,
                purpose=PASSWORD_RESET,
                reason=PASSWORD_CHANGED,
                clock=self.clock,
            ),
            1,
        )
        self.assertEqual(db.get(AccountActionToken, first.token_id).invalidation_reason, PASSWORD_CHANGED)
        db.close()

        second = self.issue(EMAIL_VERIFICATION)
        db = self.Session()
        self.assertEqual(
            invalidate_account_action_tokens(
                db=db,
                usuario_id=1,
                purpose=EMAIL_VERIFICATION,
                reason=ADMINISTRATIVE,
                clock=self.clock,
            ),
            1,
        )
        self.assertEqual(db.get(AccountActionToken, second.token_id).invalidation_reason, ADMINISTRATIVE)
        db.close()

        db = self.Session()
        with self.assertRaises(AccountActionInvalidationReasonError):
            invalidate_account_action_tokens(
                db=db,
                usuario_id=1,
                purpose=EMAIL_VERIFICATION,
                reason="other",
                clock=self.clock,
            )
        db.close()

    def test_all_states_are_derived_and_never_persisted(self):
        active = self.issue(EMAIL_VERIFICATION)
        expired = self.issue(PASSWORD_RESET)
        db = self.Session()
        active_row = db.get(AccountActionToken, active.token_id)
        expired_row = db.get(AccountActionToken, expired.token_id)
        self.assertEqual(derive_token_state(active_row, now=self.now), "active")
        self.assertEqual(
            derive_token_state(expired_row, now=self.now + timedelta(minutes=30)),
            "expired",
        )
        self.assertNotIn("status", AccountActionToken.__table__.columns)
        db.close()

    def test_secret_is_not_logged_or_exposed_by_invalid_error(self):
        secret = "S" * 43
        with patch("logging.Logger._log") as logger:
            db = self.Session()
            with self.assertRaises(AccountActionTokenInvalidError) as raised:
                consume_account_action_token(
                    db=db,
                    secret=secret,
                    purpose=EMAIL_VERIFICATION,
                    clock=self.clock,
                )
            db.close()
        logger.assert_not_called()
        self.assertNotIn(secret, str(raised.exception))
        self.assertNotIn(secret, repr(raised.exception))


if __name__ == "__main__":
    unittest.main()
