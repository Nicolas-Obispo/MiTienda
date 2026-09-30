import json
from pathlib import Path
import tomllib
import unittest


ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "backend"


class SupplyChainContractTests(unittest.TestCase):
    def test_python_runtime_and_uv_contract_are_pinned(self):
        self.assertEqual((BACKEND / ".python-version").read_text().strip(), "3.13.15")
        pyproject = tomllib.loads((BACKEND / "pyproject.toml").read_text())
        self.assertEqual(pyproject["project"]["requires-python"], ">=3.13,<3.14")
        self.assertEqual(pyproject["tool"]["uv"]["required-version"], "==0.12.19")
        self.assertTrue((BACKEND / "uv.lock").is_file())
        self.assertFalse((BACKEND / "requirements.txt").exists())

    def test_backend_profiles_are_explicit(self):
        pyproject = tomllib.loads((BACKEND / "pyproject.toml").read_text())
        dependencies = pyproject["project"]["dependencies"]
        self.assertIn("PyJWT==2.15.1", dependencies)
        self.assertFalse(any("python-jose" in item.lower() for item in dependencies))
        self.assertIn("sentence-transformers==5.2.3", pyproject["project"]["optional-dependencies"]["embeddings"])
        self.assertEqual(pyproject["tool"]["uv"]["default-groups"], [])
        self.assertIn("coverage==7.16.2", pyproject["dependency-groups"]["test"])
        self.assertIn("pip-audit==2.10.1", pyproject["dependency-groups"]["security"])

    def test_vulnerable_legacy_jwt_stack_is_absent_from_lock(self):
        lock = (BACKEND / "uv.lock").read_text().lower()
        self.assertNotIn('name = "python-jose"', lock)
        self.assertNotIn('name = "ecdsa"', lock)

    def test_node_and_npm_contract_are_pinned(self):
        package = json.loads((ROOT / "frontend" / "package.json").read_text())
        self.assertEqual((ROOT / ".node-version").read_text().strip(), "24.21.0")
        self.assertEqual(package["packageManager"], "npm@12.1.0")
        self.assertEqual(package["engines"], {"node": "24.21.0", "npm": "12.1.0"})
        self.assertEqual(
            package["devDependencies"]["@cyclonedx/cyclonedx-npm"], "6.0.1"
        )
        self.assertEqual(
            package["allowScripts"],
            {
                "@parcel/watcher": True,
                "esbuild": True,
                "fsevents": False,
                "libxmljs2": False,
            },
        )

    def test_sanitized_configuration_keeps_external_services_off(self):
        example = (BACKEND / ".env.example").read_text()
        self.assertIn("GOOGLE_IDENTITY_ENABLED=false", example)
        self.assertIn("EMAIL_PROVIDER=disabled", example)
        self.assertIn("IDENTITY_EMAIL_PROVIDER=disabled", example)
        self.assertNotIn("backend/.env\n", example)

    def test_generated_evidence_is_not_versioned(self):
        ignore = (ROOT / ".gitignore").read_text()
        self.assertIn("artifacts/", ignore)
        self.assertIn(".coverage", ignore)


if __name__ == "__main__":
    unittest.main()
