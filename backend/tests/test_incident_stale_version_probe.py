import io
import unittest
from contextlib import redirect_stderr, redirect_stdout
from unittest.mock import patch

from probe_incident_stale_version import (
    LocalHttpTransport,
    ProbeResult,
    main,
    run_stale_version_probe,
)


class FakeProbeTransport:
    def __init__(self):
        self.calls = []

    def request(self, method, path, *, token, body=None):
        self.calls.append((method, path, token, body))
        if method == "POST" and path == "/administracion/incidentes":
            return 201, {"incident": {"public_id": "INC-SYNTHETIC"}}
        if method == "POST" and body["action"] == "record_legal_assessment":
            return 201, {"incident": {"version": 2}}
        if method == "POST" and body["action"] == "record_finding":
            return 409, None
        if method == "GET" and path.endswith("/eventos"):
            return 200, [
                {"event_type": "opened"},
                {"event_type": "record_legal_assessment"},
            ]
        if method == "GET":
            return 200, {"version": 2}
        raise AssertionError("unexpected fake request")


class IncidentStaleVersionProbeTests(unittest.TestCase):
    def test_probe_freezes_version_one_and_sends_one_rejected_action(self):
        transport = FakeProbeTransport()
        result = run_stale_version_probe(
            transport=transport,
            token="memory-only-token",
            operator_usuario_id=32,
            probe_id="fixed-test",
        )
        stale = [call for call in transport.calls if call[3] and call[3].get("action") == "record_finding"]
        self.assertEqual(len(stale), 1)
        self.assertEqual(stale[0][3]["expected_version"], 1)
        self.assertEqual(result, ProbeResult(409, 2, True))

    def test_probe_advances_only_with_legal_assessment_before_stale_action(self):
        transport = FakeProbeTransport()
        run_stale_version_probe(
            transport=transport,
            token="memory-only-token",
            operator_usuario_id=32,
            probe_id="fixed-order",
        )
        actions = [call[3]["action"] for call in transport.calls if call[3] and "action" in call[3]]
        self.assertEqual(actions, ["record_legal_assessment", "record_finding"])

    def test_transport_rejects_non_loopback_targets(self):
        with self.assertRaisesRegex(ValueError, "loopback"):
            LocalHttpTransport("https://example.com")

    def test_cli_output_is_sanitized(self):
        output, errors = io.StringIO(), io.StringIO()
        with patch("probe_incident_stale_version.crear_token_jwt", return_value="private-jwt"), patch(
            "probe_incident_stale_version.LocalHttpTransport",
        ), patch(
            "probe_incident_stale_version.run_stale_version_probe",
            return_value=ProbeResult(409, 2, True),
        ), redirect_stdout(output), redirect_stderr(errors):
            result = main(["--run", "--usuario-id", "32"])
        serialized = output.getvalue() + errors.getvalue()
        self.assertEqual(result, 0)
        self.assertNotIn("private-jwt", serialized)
        self.assertNotIn("usuario-id", serialized)
        self.assertEqual(
            serialized.splitlines(),
            [
                "probe=approved",
                "stale_action_status=409",
                "final_version=2",
                "rejected_event_absent=true",
            ],
        )


if __name__ == "__main__":
    unittest.main()
