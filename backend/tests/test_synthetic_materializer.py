"""Contratos focales del materializador transaccional ET100.3."""

from __future__ import annotations

from datetime import datetime, timezone
import unittest
from unittest.mock import patch

from sqlalchemy import ForeignKey, Integer, String, UniqueConstraint, create_engine, event, func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column

from synthetic_data.blueprint import BlueprintBuilder, BlueprintContext, ClockPolicy
from synthetic_data.materializer import (
    CommitGuardSession,
    InternalTransactionMutationError,
    MaterializationError,
    certify_materialized_blueprint_read_only,
    materialize_blueprint,
    validate_materialization_contract,
)
from synthetic_data.scenarios import compile_scenario
from app.core.database import Base
from app.core.model_registry import import_all_models


ANCHOR = datetime(2026, 1, 15, 12, 0, tzinfo=timezone.utc)


class TestBase(DeclarativeBase):
    pass


class Parent(TestBase):
    __tablename__ = "test_parents"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(40), nullable=False, unique=True)
    featured_child_id: Mapped[int | None] = mapped_column(Integer, nullable=True)


class Child(TestBase):
    __tablename__ = "test_children"
    __table_args__ = (UniqueConstraint("name", name="uq_test_child_name"),)
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    parent_id: Mapped[int] = mapped_column(ForeignKey("test_parents.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(40), nullable=False)


REGISTRY = {"test_parents": Parent, "test_children": Child}


def _context(profile: str = "contract") -> BlueprintContext:
    return BlueprintContext(
        dataset_version="v1",
        profile=profile,
        seed="materializer-contract-seed",
        clock_policy=ClockPolicy(anchor=ANCHOR),
    )


def _related_blueprint(*, duplicate_child_names: bool = False):
    builder = BlueprintBuilder(_context())
    builder.add_entity(
        alias="parent.primary",
        entity_type="test_parents",
        attributes={"name": "parent", "featured_child_id": None},
    )
    builder.add_entity(
        alias="child.first",
        entity_type="test_children",
        attributes={"name": "duplicate" if duplicate_child_names else "first"},
    )
    builder.add_entity(
        alias="child.second",
        entity_type="test_children",
        attributes={"name": "duplicate" if duplicate_child_names else "second"},
    )
    builder.add_relation(
        alias="link.child.first.parent",
        relation_type="child_of",
        source_alias="child.first",
        target_alias="parent.primary",
        attributes={
            "source_field": "parent_id",
            "target_field": "featured_child_id",
        },
    )
    builder.add_relation(
        alias="link.child.second.parent",
        relation_type="child_of",
        source_alias="child.second",
        target_alias="parent.primary",
        attributes={"source_field": "parent_id"},
    )
    return builder.build()


class SyntheticMaterializerTests(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine("sqlite+pysqlite:///:memory:")
        TestBase.metadata.create_all(self.engine)

    def tearDown(self):
        self.engine.dispose()

    def test_aliases_dependency_order_and_single_external_commit(self):
        commits = []
        def record_commit(_session):
            commits.append("commit")

        event.listen(Session, "after_commit", record_commit)
        try:
            with Session(self.engine) as session:
                blueprint = _related_blueprint()
                result = materialize_blueprint(
                    session,
                    blueprint,
                    fixture_secret="local-fixture-secret-not-runtime",
                    model_registry=REGISTRY,
                )

                self.assertEqual(result.row_count, 3)
                self.assertEqual(result.fingerprint, result.reconstructed_fingerprint)
                self.assertEqual(result.dependency_layers[0], ("parent.primary",))
                self.assertEqual(
                    set(result.dependency_layers[1]), {"child.first", "child.second"}
                )
                self.assertEqual(set(result.physical_ids), {
                    "parent.primary", "child.first", "child.second"
                })
                self.assertNotEqual(
                    result.physical_ids["child.first"], result.physical_ids["child.second"]
                )
                parent = session.scalar(select(Parent))
                children = session.scalars(select(Child).order_by(Child.name)).all()
                self.assertEqual({child.parent_id for child in children}, {parent.id})
                self.assertEqual(parent.featured_child_id, result.physical_ids["child.first"])
            self.assertEqual(commits, ["commit"])
        finally:
            event.remove(Session, "after_commit", record_commit)

    def test_rollback_is_total_when_a_layer_flush_fails(self):
        with Session(self.engine) as session:
            with self.assertRaises(IntegrityError):
                materialize_blueprint(
                    session,
                    _related_blueprint(duplicate_child_names=True),
                    fixture_secret="local-fixture-secret-not-runtime",
                    model_registry=REGISTRY,
                )
            self.assertFalse(session.in_transaction())

        with Session(self.engine) as verification:
            self.assertEqual(len(verification.scalars(select(Parent)).all()), 0)
            self.assertEqual(len(verification.scalars(select(Child)).all()), 0)

    def test_fingerprint_divergence_before_commit_rolls_back_every_layer(self):
        with Session(self.engine) as session:
            def corrupt_logical_value(_session, _context, _instances):
                for instance in session.new:
                    if isinstance(instance, Child) and instance.name == "first":
                        instance.name = "tampered"

            event.listen(session, "before_flush", corrupt_logical_value)
            try:
                with self.assertRaisesRegex(
                    MaterializationError, "reconstruction_mismatch"
                ):
                    materialize_blueprint(
                        session,
                        _related_blueprint(),
                        fixture_secret="local-fixture-secret-not-runtime",
                        model_registry=REGISTRY,
                    )
            finally:
                event.remove(session, "before_flush", corrupt_logical_value)

        with Session(self.engine) as verification:
            self.assertEqual(len(verification.scalars(select(Parent)).all()), 0)
            self.assertEqual(len(verification.scalars(select(Child)).all()), 0)

    def test_transaction_preflight_failure_happens_inside_uow_and_rolls_back(self):
        observed = []
        with Session(self.engine) as session:
            def reject(guarded):
                observed.append(guarded.in_transaction())
                raise MaterializationError("synthetic_preflight_rejected")

            with self.assertRaisesRegex(MaterializationError, "preflight_rejected"):
                materialize_blueprint(
                    session,
                    _related_blueprint(),
                    fixture_secret="local-fixture-secret-not-runtime",
                    model_registry=REGISTRY,
                    transaction_preflight=reject,
                )
            self.assertEqual(observed, [True])
            self.assertFalse(session.in_transaction())

        with Session(self.engine) as verification:
            self.assertEqual(len(verification.scalars(select(Parent)).all()), 0)
            self.assertEqual(len(verification.scalars(select(Child)).all()), 0)

    def test_precommit_certification_failure_rolls_back_materialized_rows(self):
        observed = []
        with Session(self.engine) as session:
            def reject(guarded):
                observed.append(guarded.in_transaction())
                self.assertEqual(len(guarded.scalars(select(Parent)).all()), 1)
                self.assertEqual(len(guarded.scalars(select(Child)).all()), 2)
                raise MaterializationError("synthetic_precommit_rejected")

            with self.assertRaisesRegex(MaterializationError, "precommit_rejected"):
                materialize_blueprint(
                    session,
                    _related_blueprint(),
                    fixture_secret="local-fixture-secret-not-runtime",
                    model_registry=REGISTRY,
                    transaction_precommit=reject,
                )
            self.assertEqual(observed, [True])
            self.assertFalse(session.in_transaction())

        with Session(self.engine) as verification:
            self.assertEqual(len(verification.scalars(select(Parent)).all()), 0)
            self.assertEqual(len(verification.scalars(select(Child)).all()), 0)

    def test_precommit_reconstruction_expires_identity_map_after_last_flush(self):
        with Session(self.engine) as session:
            with patch.object(
                session, "expire_all", wraps=session.expire_all
            ) as expire_all:
                result = materialize_blueprint(
                    session,
                    _related_blueprint(),
                    fixture_secret="local-fixture-secret-not-runtime",
                    model_registry=REGISTRY,
                )

            expire_all.assert_called_once_with()
            self.assertEqual(result.fingerprint, result.reconstructed_fingerprint)

    def test_owner_cannot_commit_rollback_or_close_outer_session(self):
        with Session(self.engine) as session:
            guarded = CommitGuardSession(session)
            for operation in (guarded.commit, guarded.rollback, guarded.close):
                with self.assertRaises(InternalTransactionMutationError):
                    operation()
            self.assertFalse(session.in_transaction())

    def test_requires_clean_session_and_fixture_secret(self):
        with Session(self.engine) as session:
            session.begin()
            with self.assertRaisesRegex(MaterializationError, "transaction_clean"):
                materialize_blueprint(
                    session,
                    _related_blueprint(),
                    fixture_secret="fixture-secret",
                    model_registry=REGISTRY,
                )
            session.rollback()
            with self.assertRaisesRegex(MaterializationError, "fixture_secret_required"):
                materialize_blueprint(
                    session,
                    _related_blueprint(),
                    fixture_secret="",
                    model_registry=REGISTRY,
                )

    def test_head_smoke_and_functional_contracts_are_fully_mapped(self):
        expected = {"smoke": 20, "functional": 93}
        for profile, row_count in expected.items():
            with self.subTest(profile=profile):
                blueprint = compile_scenario(
                    dataset_version="v1",
                    profile=profile,
                    seed="materializer-contract-seed",
                    clock_policy=ClockPolicy(anchor=ANCHOR),
                )
                layers = validate_materialization_contract(blueprint)
                self.assertEqual(len(blueprint.entities), row_count)
                self.assertEqual(
                    {alias for layer in layers for alias in layer},
                    {entity.alias for entity in blueprint.entities},
                )


class SyntheticHeadScenarioMaterializationTests(unittest.TestCase):
    def test_smoke_and_functional_materialize_atomically_on_ephemeral_sqlite(self):
        import_all_models()
        for profile, expected_rows in (("smoke", 20), ("functional", 93)):
            with self.subTest(profile=profile):
                engine = create_engine("sqlite+pysqlite:///:memory:")
                try:
                    Base.metadata.create_all(engine)
                    blueprint = compile_scenario(
                        dataset_version="v1",
                        profile=profile,
                        seed="materializer-head-contract-seed",
                        clock_policy=ClockPolicy(anchor=ANCHOR),
                    )
                    with Session(engine) as session:
                        result = materialize_blueprint(
                            session,
                            blueprint,
                            fixture_secret="local-fixture-secret-not-runtime",
                        )
                        self.assertEqual(result.row_count, expected_rows)
                        self.assertEqual(
                            result.fingerprint, result.reconstructed_fingerprint
                        )
                        tables = {entity.entity_type for entity in blueprint.entities}
                        registry = {
                            mapper.local_table.name: mapper.class_
                            for mapper in Base.registry.mappers
                        }
                        persisted = sum(
                            session.scalar(
                                select(func.count()).select_from(registry[table])
                            )
                            for table in tables
                        )
                        self.assertEqual(persisted, expected_rows)
                    with Session(engine) as certification_session:
                        certification = certify_materialized_blueprint_read_only(
                            certification_session,
                            blueprint,
                            fixture_secret="local-fixture-secret-not-runtime",
                        )
                        self.assertEqual(certification.row_count, expected_rows)
                        self.assertEqual(
                            certification.fingerprint, blueprint.fingerprint
                        )
                        self.assertTrue(certification_session.in_transaction())
                        certification_session.rollback()
                finally:
                    engine.dispose()


if __name__ == "__main__":
    unittest.main()
