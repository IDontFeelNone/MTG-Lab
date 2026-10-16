"""Fictional tests of one explicit catalog/mechanical/role/comparison chain."""
import copy
import hashlib
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch

from card_intelligence.comparison import ContextualCardComparisonPilot, comparison_explanation
from card_intelligence.mechanics import MechanicalCardIntelligence
from card_intelligence.roles import FunctionalRolePilot
from card_intelligence_attachment_fixture import (
    CARD_IDS, SOURCE_NAME, attach_fixture, write_mechanical_source)
from legacy_profile_fixture import read, save
from query import CanonicalQueryEngine
from reasoning import ReasoningContextBuilder
from repository.legacy_profile import OPERATIONS
from repository.snapshots import SnapshotError
from role_comparison_attachment_fixture import build_role_comparison_fixture
from semantic import CanonicalSemanticQueryEngine, SemanticRequest


def fingerprints(root):
    return {p.relative_to(root).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in Path(root).rglob("*") if p.is_file()}


class RoleComparisonAttachmentTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.original = tempfile.TemporaryDirectory(prefix="fictional-role-original-")
        cls.addClassCleanup(cls.original.cleanup)
        cls.original_root = Path(cls.original.name)
        cls.original_fixture = build_role_comparison_fixture(cls.original_root)

    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="fictional-role-integration-")
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name) / "fixture"
        shutil.copytree(self.original_root, self.root)
        self.fixture = copy.deepcopy(self.original_fixture)
        for key, value in self.fixture.items():
            if isinstance(value, Path):
                self.fixture[key] = self.root / value.relative_to(self.original_root)
        self.attachment = attach_fixture(self.fixture)
        self.expected = self.fixture["control"]["query_snapshot_id"]

    def mechanical(self):
        return MechanicalCardIntelligence.from_attachment(self.attachment,
            data_root=self.fixture["mechanical_data"],
            source_directory=self.fixture["source_directory"],
            expected_query_snapshot_id=self.expected)

    def roles(self, mechanical=None):
        return FunctionalRolePilot.from_mechanical(mechanical if mechanical is not None else self.mechanical(),
            plan_path=self.fixture["role_plan"], vocabulary_path=self.fixture["vocabulary"])

    def comparison(self, roles=None):
        return ContextualCardComparisonPilot.from_roles(roles if roles is not None else self.roles(),
                                                        plan_path=self.fixture["comparison_plan"])

    def legacy_roles(self):
        return FunctionalRolePilot(self.fixture["catalog"] / "data",
            plan_path=self.fixture["role_plan"], vocabulary_path=self.fixture["vocabulary"])

    def legacy_comparison(self):
        return ContextualCardComparisonPilot(self.fixture["catalog"] / "data",
            plan_path=self.fixture["comparison_plan"], role_plan_path=self.fixture["role_plan"],
            role_vocabulary_path=self.fixture["vocabulary"])

    def assert_chain_blocks(self, roles, comparison=None):
        calls = [roles.verify_inputs, lambda: roles.catalog_binding,
                 lambda: roles.dossier(CARD_IDS[0]), roles.report, roles.comparison,
                 lambda: roles.reasoning_context(CARD_IDS[0])]
        if comparison is not None:
            calls += [comparison.verify_inputs, lambda: comparison.catalog_binding,
                      comparison.dossier, comparison.decision_inputs, comparison.reasoning_context]
        for call in calls:
            with self.subTest(operation=call):
                with self.assertRaises(ValueError):
                    call()

    def test_one_query_chain_reuses_exact_instances_without_constructors(self):
        mechanical = self.mechanical()
        with patch.object(MechanicalCardIntelligence, "__init__", side_effect=AssertionError("second mechanical")), \
                patch.object(CanonicalQueryEngine, "__init__", side_effect=AssertionError("ambient query")), \
                patch.object(CanonicalSemanticQueryEngine, "__init__", side_effect=AssertionError("second semantic query")), \
                patch.object(ReasoningContextBuilder, "__init__", side_effect=AssertionError("second context builder")), \
                patch.object(MechanicalCardIntelligence, "from_attachment", side_effect=AssertionError("second attachment")):
            roles = self.roles(mechanical)
            with patch.object(FunctionalRolePilot, "__init__", side_effect=AssertionError("second role pilot")):
                comparison = self.comparison(roles)
                handoff = comparison.reasoning_context()
        self.assertIs(roles.mechanical, mechanical)
        self.assertIs(comparison.roles, roles)
        self.assertIs(comparison.roles.mechanical.query, mechanical.query)
        self.assertIs(mechanical.context_builder._semantic._query, mechanical.query)
        self.assertEqual(roles.plan["canonical_snapshot_id"], self.expected)
        self.assertEqual(comparison.plan["canonical_snapshot_id"], self.expected)
        self.assertTrue(all(c["canonical_snapshot_id"] == self.expected for c in handoff["canonical_contexts"]))

    def test_plain_dict_path_and_duck_typed_mechanical_are_rejected(self):
        from types import SimpleNamespace
        for invalid in ({}, self.fixture["catalog"], SimpleNamespace(query=self.mechanical().query)):
            with self.subTest(invalid=type(invalid).__name__):
                with self.assertRaises((TypeError, ValueError)):
                    self.roles(invalid)

    def test_actual_legacy_mechanical_is_not_accepted_as_attached(self):
        with self.assertRaises(ValueError):
            self.roles(MechanicalCardIntelligence(self.fixture["catalog"] / "data"))

    def test_comparison_requires_actual_attachment_backed_roles(self):
        for invalid in ({}, self.fixture["role_plan"], self.legacy_roles()):
            with self.subTest(invalid=type(invalid).__name__):
                with self.assertRaises((TypeError, ValueError)):
                    ContextualCardComparisonPilot.from_roles(invalid,
                        plan_path=self.fixture["comparison_plan"])

    def test_legacy_role_and_comparison_artifact_bytes_unchanged(self):
        roles, comparison = self.roles(), self.comparison()
        legacy_roles, legacy_comparison = self.legacy_roles(), self.legacy_comparison()
        self.assertIsNone(legacy_roles.catalog_binding)
        self.assertIsNone(legacy_comparison.catalog_binding)
        self.assertEqual(roles.plan_identity, legacy_roles.plan_identity)
        self.assertEqual(roles.vocabulary_identity, legacy_roles.vocabulary_identity)
        self.assertEqual(roles.report(), legacy_roles.report())
        self.assertEqual(roles.comparison(), legacy_roles.comparison())
        for card_id in roles.cards:
            self.assertEqual(roles.dossier(card_id), legacy_roles.dossier(card_id))
        self.assertEqual(roles.reasoning_context(CARD_IDS[0]).to_json(),
                         legacy_roles.reasoning_context(CARD_IDS[0]).to_json())
        self.assertEqual(comparison.dossier().to_json(), legacy_comparison.dossier().to_json())
        self.assertEqual(comparison.decision_inputs(), legacy_comparison.decision_inputs())
        self.assertEqual(comparison.reasoning_context(), legacy_comparison.reasoning_context())
        self.assertEqual(comparison_explanation(comparison.dossier()),
                         comparison_explanation(legacy_comparison.dossier()))

    def test_pending_roles_never_become_approved_facts(self):
        roles = self.roles()
        report = roles.report()
        self.assertEqual(report["pilot_card_count"], 10)
        self.assertEqual(report["candidate_count"], 10)
        for card_id in roles.cards:
            dossier = roles.dossier(card_id)
            self.assertEqual(dossier["schema_version"], "functional-role-dossier-v1")
            self.assertEqual(dossier["review_status"], "requires_review")
            self.assertFalse(any(dossier["protection_boundary"].values()))
            for candidate in dossier["role_candidates"]:
                self.assertEqual(candidate["review"], {"status": "requires_review",
                    "human_attestation": None, "canonical_admission": False})
                self.assertEqual(candidate["prominence"]["status"], "unknown")
        self.assertFalse(hasattr(roles, "approve"))

    def test_comparison_preserves_abstain_null_selection_unknown_review_and_limitations(self):
        comparison = self.comparison()
        dossier = comparison.dossier().to_dict()
        recommendation = dossier["decision_intelligence"]["reasoning_context"]["recommendation"]
        self.assertEqual(recommendation["outcome"], "abstain")
        self.assertIsNone(recommendation["selected_alternative_id"])
        self.assertTrue(recommendation["abstention_reasons"])
        self.assertEqual(dossier["context"]["format_legality"]["status"], "unknown")
        self.assertIn("verified_rules_timing", dossier["unsupported_dimensions"])
        self.assertIn("competitive_superiority", dossier["unsupported_dimensions"])
        self.assertIn("combo_strength", dossier["unsupported_dimensions"])
        self.assertFalse(any(dossier["protection_boundary"].values()))
        for analysis in comparison.decision_inputs()["analyses"]:
            self.assertEqual(analysis["metrics"][0]["metric_id"], "human_reviewed_context_match")
            self.assertEqual(analysis["metrics"][0]["state"], "unknown")

    def test_catalog_binding_is_separate_defensive_and_read_only(self):
        mechanical = self.mechanical()
        roles = self.roles(mechanical)
        comparison = self.comparison(roles)
        for instance in (roles, comparison):
            self.assertEqual(instance.catalog_binding, mechanical.catalog_binding)
            binding = instance.catalog_binding
            binding["production_eligible"] = True
            binding["permissions"][OPERATIONS[0]] = "ESTABLISHED"
            self.assertFalse(instance.catalog_binding["production_eligible"])
            self.assertEqual(instance.catalog_binding["permissions"][OPERATIONS[0]], "NOT_ESTABLISHED")
            with self.assertRaises(AttributeError):
                instance.catalog_binding = binding
        self.assertNotEqual(roles.catalog_binding["profile_id"], mechanical.snapshot_id)
        self.assertNotEqual(roles.catalog_binding["closure_id"], mechanical.source["manifest_bytes_sha256"])
        self.assertNotIn("catalog_binding", roles.dossier(CARD_IDS[0]))
        self.assertNotIn("catalog_binding", comparison.dossier().to_dict())

    def test_catalog_selected_byte_drift_blocks_whole_chain(self):
        roles = self.roles()
        comparison = self.comparison(roles)
        path = self.fixture["catalog"] / "data/canonical/state.json"
        path.write_bytes(path.read_bytes() + b" ")
        self.assert_chain_blocks(roles, comparison)

    def test_mechanical_source_drift_blocks_independently(self):
        roles = self.roles()
        comparison = self.comparison(roles)
        path = self.fixture["source_directory"] / SOURCE_NAME
        path.write_bytes(path.read_bytes() + b" ")
        self.attachment.verify_unchanged()
        self.assert_chain_blocks(roles, comparison)

    def test_role_plan_byte_drift_blocks_even_when_json_semantics_unchanged(self):
        roles = self.roles()
        comparison = self.comparison(roles)
        path = self.fixture["role_plan"]
        path.write_bytes(path.read_bytes() + b" ")
        self.assert_chain_blocks(roles, comparison)

    def test_vocabulary_byte_drift_blocks_even_when_json_semantics_unchanged(self):
        roles = self.roles()
        comparison = self.comparison(roles)
        path = self.fixture["vocabulary"]
        path.write_bytes(path.read_bytes() + b" ")
        self.assert_chain_blocks(roles, comparison)

    def test_comparison_plan_byte_drift_blocks_all_comparison_outputs(self):
        comparison = self.comparison()
        path = self.fixture["comparison_plan"]
        path.write_bytes(path.read_bytes() + b" ")
        comparison.roles.verify_inputs()
        for call in (comparison.verify_inputs, lambda: comparison.catalog_binding,
                     comparison.dossier, comparison.decision_inputs, comparison.reasoning_context):
            with self.assertRaises(ValueError):
                call()

    def test_initial_role_cross_snapshot_mismatch_fails_without_legacy_fallback(self):
        plan = read(self.fixture["role_plan"])
        plan["canonical_snapshot_id"] = "sha256:" + "0" * 64
        save(self.fixture["role_plan"], plan)
        mechanical = self.mechanical()
        with patch.object(MechanicalCardIntelligence, "__init__", side_effect=AssertionError("fallback")):
            with self.assertRaises(ValueError):
                self.roles(mechanical)

    def test_initial_role_dossier_mismatch_fails(self):
        plan = read(self.fixture["role_plan"])
        plan["cards"][0]["mechanical_dossier_id"] = "sha256:" + "0" * 64
        save(self.fixture["role_plan"], plan)
        with self.assertRaises(ValueError):
            self.roles()

    def test_missing_mechanical_source_cannot_become_a_role_proposal(self):
        rows = [row for row in self.fixture["rows"] if row["oracle_id"] != CARD_IDS[0]]
        write_mechanical_source(self.fixture["source_directory"], rows)
        mechanical = self.mechanical()
        self.assertEqual(mechanical.dossier(CARD_IDS[0]).to_dict()["source"]["resolution"], "missing")
        with self.assertRaises(ValueError):
            self.roles(mechanical)

    def test_ambiguous_mechanical_source_cannot_become_a_role_proposal(self):
        rows = copy.deepcopy(self.fixture["rows"])
        rows.append({**rows[0], "id": "original-fictional-second-assertion"})
        write_mechanical_source(self.fixture["source_directory"], rows)
        mechanical = self.mechanical()
        self.assertEqual(mechanical.dossier(CARD_IDS[0]).to_dict()["source"]["resolution"], "ambiguous")
        with self.assertRaises(ValueError):
            self.roles(mechanical)

    def test_initial_vocabulary_identity_mismatch_fails(self):
        vocabulary = read(self.fixture["vocabulary"])
        vocabulary["vocabulary_id"] = "another-fictional-vocabulary"
        save(self.fixture["vocabulary"], vocabulary)
        with self.assertRaises(ValueError):
            self.roles()

    def test_missing_initial_plan_vocabulary_or_comparison_dependency_is_safe_failure(self):
        mechanical = self.mechanical()
        roles = self.roles(mechanical)
        for key in ("role_plan", "vocabulary", "comparison_plan"):
            path = self.fixture[key]
            original = path.read_bytes()
            path.unlink()  # Only an original fictional disposable fixture.
            try:
                with self.subTest(dependency=key):
                    with self.assertRaisesRegex(ValueError, "dependency unavailable") as caught:
                        self.comparison(roles) if key == "comparison_plan" else self.roles(mechanical)
                    self.assertNotIn(str(self.root), str(caught.exception))
            finally:
                path.write_bytes(original)

    def test_deleted_bound_role_plan_vocabulary_and_comparison_dependencies_fail_closed(self):
        roles = self.roles()
        comparison = self.comparison(roles)
        for key in ("role_plan", "vocabulary", "comparison_plan"):
            path = self.fixture[key]
            original = path.read_bytes()
            path.unlink()  # Only an original fictional disposable fixture.
            try:
                with self.subTest(dependency=key):
                    if key == "comparison_plan":
                        with self.assertRaises(ValueError):
                            comparison.dossier()
                    else:
                        self.assert_chain_blocks(roles, comparison)
            finally:
                path.write_bytes(original)

    def test_initial_comparison_cross_snapshot_mismatch_fails(self):
        plan = read(self.fixture["comparison_plan"])
        plan["canonical_snapshot_id"] = "sha256:" + "0" * 64
        save(self.fixture["comparison_plan"], plan)
        with self.assertRaises(ValueError):
            self.comparison()

    def test_initial_comparison_changed_role_dossier_fails(self):
        plan = read(self.fixture["comparison_plan"])
        plan["cards"][0]["role_dossier_id"] = "sha256:" + "0" * 64
        save(self.fixture["comparison_plan"], plan)
        with self.assertRaises(ValueError):
            self.comparison()

    def test_role_construction_cannot_bind_plan_bytes_replaced_after_parse(self):
        original = FunctionalRolePilot._build
        changed = False

        def replace_after_build(instance, card_id):
            nonlocal changed
            result = original(instance, card_id)
            if not changed:
                changed = True
                path = self.fixture["role_plan"]
                path.write_bytes(path.read_bytes() + b" ")
            return result

        mechanical = self.mechanical()
        with patch.object(FunctionalRolePilot, "_build", replace_after_build):
            with self.assertRaises(ValueError):
                self.roles(mechanical)
        self.assertTrue(changed)

    def test_comparison_construction_cannot_bind_plan_bytes_replaced_after_parse(self):
        original = ContextualCardComparisonPilot._build

        def replace_after_build(instance):
            result = original(instance)
            path = self.fixture["comparison_plan"]
            path.write_bytes(path.read_bytes() + b" ")
            return result

        roles = self.roles()
        with patch.object(ContextualCardComparisonPilot, "_build", replace_after_build):
            with self.assertRaises(ValueError):
                self.comparison(roles)

    def test_replacing_mechanical_with_equivalent_instance_is_not_silent_rebinding(self):
        roles = self.roles()
        comparison = self.comparison(roles)
        roles.mechanical = self.mechanical()
        self.assert_chain_blocks(roles, comparison)

    def test_replacing_roles_with_equivalent_instance_is_not_silent_rebinding(self):
        comparison = self.comparison()
        comparison.roles = self.roles(comparison.roles.mechanical)
        with self.assertRaises(ValueError):
            comparison.dossier()

    def test_query_root_retargeting_blocks(self):
        roles = self.roles()
        comparison = self.comparison(roles)
        roles.mechanical.query.data_root = self.root / "unrelated-data"
        self.assert_chain_blocks(roles, comparison)

    def test_role_plan_retargeting_to_identical_bytes_is_not_rebinding(self):
        roles = self.roles()
        comparison = self.comparison(roles)
        replacement = self.root / "replacement-plan.json"
        replacement.write_bytes(self.fixture["role_plan"].read_bytes())
        roles.plan_path = replacement
        self.assert_chain_blocks(roles, comparison)

    def test_reasoning_query_retargeting_blocks(self):
        roles = self.roles()
        comparison = self.comparison(roles)
        roles.mechanical.context_builder._semantic._query = self.mechanical().query
        self.assert_chain_blocks(roles, comparison)

    def test_live_role_plan_and_vocabulary_mutation_are_rejected(self):
        for attribute, key, value in (("plan", "prepared_at", "2026-10-17T00:00:00Z"),
                                      ("vocabulary", "vocabulary_id", "changed")):
            roles = self.roles()
            setattr(roles, attribute, {**getattr(roles, attribute), key: value})
            with self.subTest(attribute=attribute):
                self.assert_chain_blocks(roles)

    def test_live_comparison_plan_mutation_is_rejected(self):
        comparison = self.comparison()
        comparison.plan = {**comparison.plan, "prepared_at": "2026-10-17T00:00:00Z"}
        with self.assertRaises(ValueError):
            comparison.reasoning_context()

    def test_malformed_live_role_plan_fails_with_explicit_domain_error(self):
        roles = self.roles()
        comparison = self.comparison(roles)
        roles.plan = None
        self.assert_chain_blocks(roles, comparison)

    def test_cached_role_dossiers_cannot_be_replaced(self):
        roles = self.roles()
        comparison = self.comparison(roles)
        roles._dossiers = {}
        self.assert_chain_blocks(roles, comparison)

    def test_cached_comparison_subjects_cannot_be_replaced(self):
        comparison = self.comparison()
        comparison.cards = []
        with self.assertRaises(ValueError):
            comparison.dossier()

    def test_tier_b_semantic_and_audit_capabilities_stay_blocked(self):
        comparison = self.comparison()
        query = comparison.roles.mechanical.query
        semantic = comparison.roles.mechanical.context_builder._semantic
        with patch.object(Path, "read_bytes", side_effect=AssertionError("excluded I/O")):
            for call in (lambda: query.related(CARD_IDS[0], "promotion_audits"),
                         lambda: semantic.execute(SemanticRequest("validation_statistics", {})),
                         lambda: semantic.execute(SemanticRequest("list_validation", {"state": "rejected"}))):
                with self.subTest(operation=call):
                    with self.assertRaises(SnapshotError) as caught:
                        call()
                    self.assertEqual(caught.exception.code, "unsupported_capability")
        self.assertEqual(comparison.dossier().to_dict()["canonical_snapshot_id"], self.expected)

    def test_chain_is_read_only_and_has_no_network_or_provider_fallback(self):
        before = fingerprints(self.root)
        with patch("socket.create_connection", side_effect=AssertionError("network")), \
                patch("urllib.request.urlopen", side_effect=AssertionError("provider lookup")):
            comparison = self.comparison()
            comparison.roles.report()
            comparison.roles.reasoning_context(CARD_IDS[0])
            comparison.reasoning_context()
            comparison_explanation(comparison.dossier())
        self.assertEqual(fingerprints(self.root), before)


if __name__ == "__main__":
    unittest.main()
