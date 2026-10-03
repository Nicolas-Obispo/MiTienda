"""Regresion read-only del round-trip MySQL del dataset smoke ET100.3."""

from __future__ import annotations

from datetime import datetime, timezone
import os
import unittest

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from app.core.model_registry import import_all_models
from app.modules.spaces.models.comercios_models import Comercio
from synthetic_data.apply import load_materializer_configuration, require_fixture_secret
from synthetic_data.blueprint import ClockPolicy
from synthetic_data.materializer import certify_materialized_blueprint_read_only
from synthetic_data.scenarios import compile_scenario


@unittest.skipUnless(
    os.environ.get("FEEDGO_STAGE100_MATERIALIZER_DATABASE_URL")
    and os.environ.get("FEEDGO_STAGE100_FIXTURE_SECRET"),
    "requiere credencial materializadora y fixture secret ET100.3",
)
class SyntheticSmokeMySQLRoundTripTests(unittest.TestCase):
    def test_smoke_coordinates_and_fingerprint_survive_real_mysql_round_trip(self):
        import_all_models()
        config = load_materializer_configuration(os.environ)
        fixture_secret = require_fixture_secret(os.environ)
        blueprint = compile_scenario(
            dataset_version="et100.3-v1",
            profile="smoke",
            seed="approved-profile-seed-001",
            clock_policy=ClockPolicy(
                anchor=datetime(2026, 1, 15, 12, 0, tzinfo=timezone.utc)
            ),
        )
        expected = next(
            entity
            for entity in blueprint.entities
            if entity.alias == "commerce.primary"
        )
        engine = create_engine(config.materializer_url, pool_pre_ping=True)
        try:
            with Session(engine) as session:
                commerce = session.scalar(select(Comercio))
                self.assertIsNotNone(commerce)
                self.assertEqual(commerce.latitud, expected.attributes["latitud"])
                self.assertEqual(commerce.longitud, expected.attributes["longitud"])

                certification = certify_materialized_blueprint_read_only(
                    session,
                    blueprint,
                    fixture_secret=fixture_secret,
                )
                self.assertEqual(certification.row_count, 20)
                self.assertEqual(certification.fingerprint, blueprint.fingerprint)
                self.assertFalse(session.new)
                self.assertFalse(session.dirty)
                self.assertFalse(session.deleted)
                session.rollback()
        finally:
            engine.dispose()


if __name__ == "__main__":
    unittest.main()
