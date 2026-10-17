"""Offline review/design proofs, with no official source text or real execution.

Positive Boolean fixtures prove only the shape of the future activation gate.
Negative cases ensure those fixtures cannot manufacture closure or approval for
the retained real-rules design. Source anchors are compared as metadata only.
"""
from contextlib import ExitStack, redirect_stdout
from dataclasses import FrozenInstanceError
import io
from itertools import product
import json
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch

from evidence.contracts import deterministic_json
from gameplay_rules.errors import GameplayContractError
from gameplay_rules.execution_design import build_design_package, load_design_package
from gameplay_rules.execution_design.__main__ import main
from gameplay_rules.execution_design.builder import build_capability_matrix, build_profile_design
from gameplay_rules.execution_design.contracts import (
    FoundationalProjectionReview, RealRulesActivationGateDesign,
    RealRulesCapabilityMatrix, RealRulesExecutionProfileDesign,
    RealRulesExecutionReadiness,
)
from gameplay_rules.execution_design.gates import (
    RuleGateEvidence, assess_activation, closure_findings,
    evaluate_activation_requirements, evaluate_rule_gate, review_rule,
)
from gameplay_rules.execution_design.package import package_manifest
from gameplay_rules.projection import FoundationalProjection


ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "reference-reviews/gameplay-rules-execution-profile-design"
PROJECTION = ROOT / "reference-reviews/gameplay-rules-foundational-projection"
ROOTS = {
    "projection_root": PROJECTION,
    "artifact_review_root": ROOT / "reference-reviews/gameplay-rules-artifact-verification",
    "source_root": ROOT / "reference-reviews/gameplay-rules-source-versioning",
    "discovery_root": ROOT / "reference-reviews/gameplay-rules-release-discovery-closure",
}
REFERENCES = (
    "101.1", "101.2", "101.2a", "101.3", "102.1", "102.2", "108.1",
    "108.3", "108.4", "108.4a", "109.1", "109.3", "109.4", "110.1",
    "110.2", "110.2a", "400.1", "400.2", "400.3", "400.7",
)
PROJECTION_PACKAGE_ID = "sha256:22740145cf0ec457e0b297eba5ebed3d58054b6d16179bdd738a4f5ccc5463ea"
PROJECTION_ID = "sha256:98bfd574c774a48aaaab4753eb8eb864dc7242effa011568f2ebf59c6a9ce6f7"
ARTIFACT_HASH = "sha256:8d860e451f20f38865b725b42d82feb714c725373dd8f3b32b8652b3eeb070ca"
OTHER_HASH = "sha256:" + "f" * 64
PARTIAL = {"102.1", "102.2", "109.1", "109.3", "110.1", "400.1"}
EXCEPTIONS = {
    "109.4": {"109.4" + suffix for suffix in "abcdefg"},
    "400.7": {"400.7" + suffix for suffix in "abcdefghijkm"},
}
REQUIREMENTS = (
    "source_artifact_verified", "projection_package_verified", "projection_review_complete",
    "runtime_used_rules_ready", "dependency_closure_satisfied", "exception_closure_satisfied",
    "semantic_primitives_implemented", "capability_matrix_matches_implementation",
    "exact_rules_release_pinned", "deterministic_test_vectors_passed", "explicit_owner_activation",
)
RECORD_TYPES = {
    "projection-review.json": FoundationalProjectionReview,
    "capability-matrix.json": RealRulesCapabilityMatrix,
    "execution-profile-design.json": RealRulesExecutionProfileDesign,
    "activation-gates.json": RealRulesActivationGateDesign,
    "readiness.json": RealRulesExecutionReadiness,
}


def body(record):
    value = record.to_dict()
    return {key: value[key] for key in record.BODY_FIELDS}


def write_package(directory, records):
    """Rehash an authored test mutation to distinguish integrity from review."""
    raw = {name: (record.serialize() + "\n").encode("utf-8")
           for name, record in records.items()}
    for name, data in raw.items():
        (directory / name).write_bytes(data)
    manifest = package_manifest(records, raw)
    (directory / "manifest.json").write_text(deterministic_json(manifest) + "\n", encoding="utf-8")


class ExecutionDesignFixture(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.records = load_design_package(PACKAGE, **ROOTS)
        cls.review = cls.records["projection-review.json"]
        cls.matrix = cls.records["capability-matrix.json"]
        cls.design = cls.records["execution-profile-design.json"]
        cls.activation = cls.records["activation-gates.json"]
        cls.readiness = cls.records["readiness.json"]
        cls.projection = FoundationalProjection.from_json((PROJECTION / "projection.json").read_bytes())
        cls.rows = {row["rule_reference"]: row for row in cls.review.to_dict()["rules"]}
        cls.capabilities = {row["capability_id"]: row for row in cls.matrix.to_dict()["capabilities"]}


class ExecutionDesignContractTests(ExecutionDesignFixture):
    def test_exact_merged_projection_identity_and_twenty_ordered_review_rows(self):
        value = self.review.to_dict()
        self.assertEqual(value["projection_package_id"], PROJECTION_PACKAGE_ID)
        self.assertEqual(value["projection_id"], PROJECTION_ID)
        self.assertEqual(tuple(self.rows), REFERENCES)
        self.assertEqual(len(value["rules"]), 20)
        self.assertEqual(value["review_status"], "REVIEWED_FOR_EXECUTION_DESIGN")
        self.assertEqual(value["source_binding"], {
            "artifact_hash": ARTIFACT_HASH, "byte_length": 977752,
            "effective_date": "2026-09-25",
            "verification_result_id": "sha256:6289f9e138c248f33b950842fd079f9dc9d4be431a9ac8dc1effb4a18ec502b3",
            "correspondence_review_id": "sha256:7332e6517b1b28085bbee1fa76b8ecbc9cbe4148e261452449a308ba348d9def",
        })

    def test_review_copies_exact_source_anchors_without_changing_original_projection(self):
        original = (PROJECTION / "projection.json").read_bytes()
        sources = {row["rule_reference"]: row for row in self.projection.to_dict()["rules"]}
        for reference, row in self.rows.items():
            with self.subTest(reference=reference):
                self.assertEqual(row["source_anchor"], sources[reference]["source_anchor"])
                self.assertEqual(row["projection_id"], PROJECTION_ID)
                self.assertNotIn("paraphrase", row)
                self.assertEqual(set(row["source_anchor"]), {
                    "rule_reference", "artifact_hash", "byte_start", "byte_end",
                    "line_number", "span_sha256", "span_policy",
                })
        build_design_package(**ROOTS)
        self.assertEqual((PROJECTION / "projection.json").read_bytes(), original)

    def test_five_record_types_roundtrip_deterministically_and_are_deeply_immutable(self):
        for name, cls in RECORD_TYPES.items():
            with self.subTest(record=name):
                record = self.records[name]
                self.assertIsInstance(record, cls)
                self.assertEqual(cls.create(body(record)), record)
                self.assertEqual(cls.from_json(record.serialize()), record)
                self.assertEqual(record.serialize(), deterministic_json(record.to_dict()))
                self.assertIs(record.verify(), record)
                with self.assertRaises((FrozenInstanceError, AttributeError, TypeError)):
                    record._payload = {}
                with self.assertRaises(TypeError):
                    record._payload["execution_authorized"] = True
        value = self.review.to_dict()
        value["rules"][0]["source_anchor"]["byte_start"] = -1
        self.assertGreaterEqual(self.review.rules[0]["source_anchor"]["byte_start"], 0)
        with self.assertRaises(TypeError):
            self.review.rules[0]["source_anchor"]["byte_start"] = -1
        with self.assertRaises(AttributeError):
            self.review.rules[0]["blockers"].append("Caller mutation")

    def test_record_identity_changes_with_explicit_version_or_authored_design_input(self):
        for mutation in ("version", "limitations"):
            value = body(self.design)
            if mutation == "version":
                value["design_version"] = "real-rules-execution-profile-design-v2"
            else:
                value["limitations"].append("Original structural fixture limitation.")
            with self.subTest(mutation=mutation):
                changed = RealRulesExecutionProfileDesign.create(value)
                self.assertNotEqual(changed.identity, self.design.identity)
                self.assertEqual(changed, RealRulesExecutionProfileDesign.create(value))
                self.assertFalse(changed.real_rules_executable)
                self.assertEqual(changed.status, "DESIGN_ONLY")

    def test_identity_tampering_duplicate_keys_nonfinite_and_unknown_fields_fail_closed(self):
        for name, cls in RECORD_TYPES.items():
            record = self.records[name]
            tampered = record.to_dict()
            tampered[cls.ID_FIELD] = OTHER_HASH
            with self.subTest(record=name, mutation="identity"), self.assertRaises(GameplayContractError):
                cls.from_dict(tampered)
            raw = record.serialize()
            malformed = (
                '{"game_id":"magic",' + raw[1:],
                raw.replace('"game_id":"magic"', '"game_id":NaN'),
                raw.replace('"game_id":"magic"', '"game_id":Infinity'),
                b"\xff", "[]", "null",
            )
            for index, data in enumerate(malformed):
                with self.subTest(record=name, mutation=index), self.assertRaises(GameplayContractError):
                    cls.from_json(data)
            value = body(record)
            value["official_source_text"] = "Original unapproved fixture field."
            with self.subTest(record=name, mutation="unknown"), self.assertRaises(GameplayContractError):
                cls.create(value)

    def test_no_record_can_claim_owner_approval_or_execution_authorization(self):
        forbidden = {
            "design_only": False, "real_rules_executable": True, "execution_authorized": True,
            "projection_authorized": True, "owner_execution_approval": "GRANTED",
            "source_policy_clearance": "granted", "source_body_retained": True,
        }
        for name, cls in RECORD_TYPES.items():
            for field, replacement in forbidden.items():
                value = self.records[name].to_dict()
                value[field] = replacement
                with self.subTest(record=name, flag=field), self.assertRaises(GameplayContractError):
                    cls.from_dict(value)
                value = body(self.records[name])
                value[field] = replacement
                with self.subTest(record=name, create_flag=field), self.assertRaises(GameplayContractError):
                    cls.create(value)

    def test_rule_allowlist_cannot_expand_reorder_duplicate_or_omit_reviews(self):
        for mutation in ("extra", "replace", "reorder", "duplicate", "omit"):
            value = body(self.review)
            if mutation == "extra":
                value["rules"].append(value["rules"][0])
            elif mutation == "replace":
                value["rules"][0]["rule_reference"] = "104.3a"
            elif mutation == "reorder":
                value["rules"][:2] = reversed(value["rules"][:2])
            elif mutation == "duplicate":
                value["rules"][1] = value["rules"][0]
            else:
                value["rules"].pop()
            with self.subTest(mutation=mutation), self.assertRaises(GameplayContractError):
                FoundationalProjectionReview.create(value)

    def test_execution_positive_rows_and_approved_review_status_cannot_be_created(self):
        for field, replacement in (("execution_ready", True), ("implementation_now_safe", True),
                                   ("execution_readiness", "READY_FOR_EXECUTION")):
            value = body(self.review)
            value["rules"][4][field] = replacement
            with self.subTest(field=field), self.assertRaises(GameplayContractError):
                FoundationalProjectionReview.create(value)
        value = body(self.review)
        value["review_status"] = "APPROVED_FOR_EXECUTION"
        with self.assertRaises(GameplayContractError):
            FoundationalProjectionReview.create(value)

    def test_nested_claims_cannot_invent_approval_primitives_permissions_or_runtime_objects(self):
        mutations = (
            (self.review, ("execution_readiness_findings", "execution_approval"), "GRANTED"),
            (self.review, ("execution_readiness_findings", "available_real_primitives"), ["fixture_primitive"]),
            (self.review, ("execution_readiness_findings", "execution_ready_rules"), ["102.1"]),
            (self.matrix, ("coverage_policy", "real_execution_primitives_available"), ["fixture_primitive"]),
            (self.design, ("projection_approval_requirements", "execution_approval"), "GRANTED"),
            (self.design, ("projection_approval_requirements", "explicit_owner_activation_required"), False),
            (self.design, ("source_evidence_requirements", "broader_source_content_permissions"), "GRANTED"),
            (self.design, ("source_evidence_requirements", "external_txt_required_for_design"), True),
            (self.design, ("capability_coverage", "available_execution_capabilities"), ["players"]),
            (self.design, ("capability_coverage", "none_is_activated"), False),
            (self.design, ("future_snapshot_design", "snapshot_instantiated"), True),
            (self.design, ("proof_trace_design", "result_instantiated"), True),
        )
        for record, (section, field), replacement in mutations:
            value = body(record)
            value[section][field] = replacement
            with self.subTest(record=record.SCHEMA, section=section, field=field), \
                 self.assertRaises(GameplayContractError):
                type(record).create(value)


class PerRuleExecutionReadinessTests(ExecutionDesignFixture):
    def test_all_twenty_readiness_rows_are_reproducible_and_none_is_executable(self):
        for reference in REFERENCES:
            with self.subTest(reference=reference):
                row = review_rule(self.projection, reference)
                self.assertEqual(row, self.rows[reference])
                self.assertEqual(row, review_rule(self.projection, reference))
                self.assertEqual(row["execution_readiness"],
                                 "PARTIALLY_READY" if reference in PARTIAL else "BLOCKED")
                self.assertFalse(row["execution_ready"])
                self.assertFalse(row["implementation_now_safe"])
                self.assertTrue(row["explanation"])
                self.assertTrue(row["blockers"])
        self.assertEqual(self.readiness.to_dict()["per_rule_states"], {
            ref: "PARTIALLY_READY" if ref in PARTIAL else "BLOCKED" for ref in REFERENCES
        })

    def test_empty_known_graph_is_not_proof_of_complete_semantic_closure(self):
        for reference in PARTIAL:
            with self.subTest(reference=reference):
                row = self.rows[reference]
                self.assertEqual(row["known_dependency_closure"], "CLOSED")
                self.assertEqual(row["known_exception_closure"], "CLOSED")
                self.assertEqual(row["dependency_closure"], "UNKNOWN")
                self.assertEqual(row["exception_closure"], "UNKNOWN")
                self.assertTrue(row["state_model_relevance"])
                self.assertTrue(row["required_semantic_primitives"])
                self.assertFalse(row["execution_ready"])

    def test_required_unresolved_dependencies_block_their_actual_projected_rules(self):
        required = {"101.1": "104.3a", "101.2a": "113.10", "108.3": "407",
                    "108.4": "112.2", "110.2": "111.2"}
        for reference, dependency in required.items():
            with self.subTest(reference=reference):
                row = self.rows[reference]
                self.assertIn(dependency, row["unresolved_dependencies"])
                self.assertIn("BLOCKED_BY_DEPENDENCY", row["semantic_roles"])
                self.assertEqual(row["dependency_closure"], "OPEN")
                self.assertEqual(row["execution_readiness"], "BLOCKED")
                decision = evaluate_rule_gate(self.projection, reference, RuleGateEvidence())
                self.assertIn("UNRESOLVED_DEPENDENCY:" + dependency, decision["blockers"])
                self.assertFalse(decision["execution_ready"])

    def test_precedence_cycle_terminates_and_propagates_unresolved_ability_boundary(self):
        parent = closure_findings(self.projection, "101.2")
        child = closure_findings(self.projection, "101.2a")
        self.assertIn("101.2a", parent["prerequisite_rules"])
        self.assertIn("101.2", child["prerequisite_rules"])
        for findings in (parent, child):
            self.assertEqual(findings["unresolved_dependencies"], ["113.10"])
            self.assertEqual(findings["dependency_closure"], "OPEN")
            self.assertEqual(findings["known_exception_closure"], "OPEN")
            self.assertEqual(findings["exception_closure"], "OPEN")
        self.assertIn("real_ability_modification_boundary_v1", self.rows["101.2"]["required_semantic_primitives"])

    def test_golden_rule_remains_blocked_by_exception_and_card_text_semantic_boundary(self):
        row = self.rows["101.1"]
        self.assertIn("104.3a", row["unresolved_dependencies"])
        self.assertIn("real_card_text_semantics_v1", row["unsupported_required_semantic_primitives"])
        self.assertIn("PRECEDENCE_SEMANTIC", row["semantic_roles"])
        self.assertIn("BLOCKED_BY_EXCEPTION_SET", row["semantic_roles"])
        self.assertEqual(row["known_exception_closure"], "OPEN")
        self.assertEqual(row["exception_closure"], "OPEN")
        self.assertFalse(row["execution_ready"])

    def test_unprojected_exception_families_block_even_baseline_runtime_queries(self):
        for reference, expected in EXCEPTIONS.items():
            with self.subTest(reference=reference):
                row = self.rows[reference]
                self.assertEqual(set(row["unprojected_exceptions"]), expected)
                self.assertEqual(row["exception_closure"], "OPEN")
                self.assertEqual(row["execution_readiness"], "BLOCKED")
                self.assertIn("BLOCKED_BY_EXCEPTION_SET", row["semantic_roles"])
                decision = evaluate_rule_gate(self.projection, reference, RuleGateEvidence())
                self.assertTrue({"UNPROJECTED_EXCEPTION:" + ref for ref in expected}
                                <= set(decision["blockers"]))
        self.assertNotIn("400.7l", self.rows["400.7"]["unprojected_exceptions"])

    def test_controller_fallback_inherits_incomplete_ownership_and_control(self):
        row = self.rows["108.4a"]
        self.assertTrue({"108.3", "108.4"} <= set(row["prerequisite_rules"]))
        self.assertTrue({"407", "112.2", "111.2"} <= set(row["unresolved_dependencies"]))
        self.assertEqual(row["execution_readiness"], "BLOCKED")

    def test_108_1_is_authority_only_and_never_a_gameplay_primitive(self):
        row = self.rows["108.1"]
        self.assertEqual(row["semantic_roles"], ["REFERENCE_ONLY"])
        self.assertEqual(row["direct_runtime_relevance"], "NONE")
        self.assertFalse(row["state_model_relevance"])
        self.assertEqual(row["required_semantic_primitives"], [])
        self.assertIn("REFERENCE_AUTHORITY_NEVER_GAMEPLAY_BEHAVIOR", row["blockers"])
        self.assertFalse(row["execution_ready"])

    def test_instruction_entry_visibility_and_destination_boundaries_remain_incomplete(self):
        expected = {
            "101.3": "real_instruction_feasibility_evaluation_v1",
            "110.2a": "real_structured_effect_instruction_descriptor_v1",
            "400.2": "real_object_visibility_evaluation_v1",
            "400.3": "real_proposed_move_descriptor_v1",
        }
        for reference, primitive in expected.items():
            with self.subTest(reference=reference):
                self.assertIn(primitive, self.rows[reference]["unsupported_required_semantic_primitives"])
                self.assertTrue(self.rows[reference]["unknown_semantic_contexts"])
                self.assertEqual(self.rows[reference]["execution_readiness"], "BLOCKED")

    def test_only_the_selected_projected_rules_are_valid_gate_inputs(self):
        for reference in ("104.3a", "111.2", "407", "109.4a", "400.7m", "601", "latest"):
            with self.subTest(reference=reference), self.assertRaises(GameplayContractError):
                review_rule(self.projection, reference)
        with self.assertRaises(GameplayContractError):
            closure_findings(self.projection.to_dict(), "102.1")

    def test_rule_gate_requires_review_anchors_and_pinned_release_independently(self):
        default = evaluate_rule_gate(self.projection, "102.1", RuleGateEvidence())
        self.assertTrue({"PROJECTION_REVIEW_MISSING", "SOURCE_ANCHOR_VERIFICATION_MISSING"}
                        <= set(default["blockers"]))
        evidence = RuleGateEvidence(source_release="2026-10-01", source_anchor_verified=True,
                                    projection_review_complete=True)
        decision = evaluate_rule_gate(self.projection, "102.1", evidence, review=self.review)
        self.assertIn("INCOMPATIBLE_RULES_RELEASE", decision["blockers"])
        self.assertNotIn("PROJECTION_REVIEW_MISSING", decision["blockers"])
        self.assertNotIn("SOURCE_ANCHOR_VERIFICATION_MISSING", decision["blockers"])
        self.assertFalse(decision["execution_ready"])
        forged_value = body(self.review)
        forged_value["rules"][4]["source_anchor"]["span_sha256"] = OTHER_HASH
        forged_review = FoundationalProjectionReview.create(forged_value)
        decision = evaluate_rule_gate(self.projection, "102.1", evidence, review=forged_review)
        self.assertIn("PROJECTION_REVIEW_MISSING", decision["blockers"])

    def test_claimed_closed_dependencies_and_implemented_primitives_cannot_override_real_blockers(self):
        for reference in ("101.1", "101.2a", "109.4", "400.7", "102.1"):
            row = self.rows[reference]
            evidence = RuleGateEvidence(source_anchor_verified=True, projection_review_complete=True,
                dependency_closure="CLOSED", exception_closure="CLOSED",
                implemented_primitives=row["required_semantic_primitives"])
            with self.subTest(reference=reference):
                decision = evaluate_rule_gate(self.projection, reference, evidence, review=self.review)
                self.assertFalse(decision["execution_ready"])
                self.assertEqual(decision["decision"], "DENIED_DESIGN_ONLY")
                self.assertTrue(set(row["blockers"]) <= set(decision["blockers"]))
                self.assertEqual(decision["dependency_closure"], row["dependency_closure"])
                self.assertEqual(decision["exception_closure"], row["exception_closure"])

    def test_unknown_capabilities_and_unknown_exception_closure_never_produce_legality(self):
        evidence = RuleGateEvidence(unknown_capabilities=["result_relevant_unmodeled_context"])
        decision = evaluate_rule_gate(self.projection, "102.1", evidence)
        self.assertIn("UNKNOWN_CAPABILITY:result_relevant_unmodeled_context", decision["blockers"])
        self.assertIn("EXCEPTION_CLOSURE_EVIDENCE_UNKNOWN", decision["blockers"])
        self.assertFalse(decision["execution_ready"])
        self.assertNotIn(decision["decision"], {"LEGAL", "ILLEGAL"})
        self.assertEqual(self.design.epistemic_policy["unresolved_or_unmodeled_result"], "INDETERMINATE_OR_UNSUPPORTED")
        self.assertFalse(self.design.epistemic_policy["definitive_legality_without_closure"])

    def test_rule_evidence_is_strict_and_immutable_and_not_a_raw_boolean_bypass(self):
        for arguments in ({"source_anchor_verified": 1}, {"projection_review_complete": "yes"},
                          {"source_release": "latest"}, {"dependency_closure": "READY"},
                          {"implemented_primitives": ["x", "x"]}, {"unknown_capabilities": [None]}):
            with self.subTest(arguments=arguments), self.assertRaises(GameplayContractError):
                RuleGateEvidence(**arguments)
        evidence = RuleGateEvidence(implemented_primitives=["fixture_primitive"])
        self.assertEqual(evidence.implemented_primitives, ("fixture_primitive",))
        with self.assertRaises(FrozenInstanceError):
            evidence.source_anchor_verified = True
        with self.assertRaises(GameplayContractError):
            evaluate_rule_gate(self.projection, "102.1", {})


class CapabilityAndActivationTests(ExecutionDesignFixture):
    def test_capability_matrix_covers_required_dimensions_without_inflating_support(self):
        self.assertEqual(set(self.capabilities), {
            "players", "opponent_relationship", "object_taxonomy", "characteristics_vocabulary",
            "ownership", "control", "permanent_identity", "zone_taxonomy", "zone_visibility",
            "zone_destination", "zone_change_identity", "rule_precedence", "impossible_instructions",
            "source_authority",
        })
        self.assertEqual(len(self.capabilities), 14)
        for name, capability in self.capabilities.items():
            with self.subTest(capability=name):
                self.assertTrue(capability["supporting_rules"])
                self.assertTrue(set(capability["supporting_rules"]) <= set(REFERENCES))
                self.assertFalse(capability["implementation_primitive_available"])
                self.assertFalse(capability["execution_supported"])
                self.assertIn(capability["dependency_closure"], {"OPEN", "UNKNOWN"})
                self.assertIn(capability["exception_closure"], {"OPEN", "UNKNOWN"})
        self.assertEqual(self.capabilities["source_authority"]["semantic_roles"], ["REFERENCE_ONLY"])
        self.assertEqual(self.design.capability_coverage["available_execution_capabilities"], ())

    def test_capability_design_cannot_gain_support_merely_from_projected_rules(self):
        for field in ("execution_supported", "implementation_primitive_available"):
            value = body(self.matrix)
            value["capabilities"][0][field] = True
            with self.subTest(field=field), self.assertRaises(GameplayContractError):
                RealRulesCapabilityMatrix.create(value)
        for capability, exception_family in (("control", "109.4"), ("zone_change_identity", "400.7")):
            self.assertTrue(EXCEPTIONS[exception_family] <= set(self.capabilities[capability]["blocking_references"]))
            self.assertEqual(self.capabilities[capability]["execution_readiness"], "BLOCKED")

    def test_structural_activation_requires_every_one_of_eleven_strict_boolean_conditions(self):
        fixture = {name: True for name in REQUIREMENTS}
        result = evaluate_activation_requirements(fixture)
        self.assertTrue(result["requirements_satisfied"])
        self.assertTrue(result["activation_denied"])
        self.assertEqual(result["status"], "DENIED_DESIGN_ONLY")
        for missing in REQUIREMENTS:
            conditions = dict(fixture, **{missing: False})
            with self.subTest(missing=missing):
                result = evaluate_activation_requirements(conditions)
                self.assertFalse(result["requirements_satisfied"])
                self.assertEqual(result["failed_requirements"], [missing])
                self.assertTrue(result["activation_denied"])
        self.assertEqual(tuple(self.activation.requirements), REQUIREMENTS)

    def test_activation_gate_rejects_omitted_unknown_and_truthy_nonboolean_conditions(self):
        fixture = {name: True for name in REQUIREMENTS}
        malformed = [dict(fixture, extra=True), {key: value for key, value in fixture.items()
                                                if key != "explicit_owner_activation"}]
        malformed += [dict(fixture, explicit_owner_activation=value) for value in (1, "true", None, [])]
        for conditions in malformed:
            with self.subTest(conditions=conditions), self.assertRaises(GameplayContractError):
                evaluate_activation_requirements(conditions)

    def test_every_structural_boolean_combination_is_conjunctive_and_denies_activation(self):
        satisfied = 0
        for values in product((False, True), repeat=len(REQUIREMENTS)):
            result = evaluate_activation_requirements(dict(zip(REQUIREMENTS, values)))
            self.assertEqual(result["requirements_satisfied"], all(values))
            self.assertEqual(result["failed_requirements"],
                             [key for key, value in zip(REQUIREMENTS, values) if not value])
            self.assertTrue(result["activation_denied"])
            self.assertEqual(result["status"], "DENIED_DESIGN_ONLY")
            satisfied += result["requirements_satisfied"]
        self.assertEqual(satisfied, 1)

    def test_real_activation_derives_absent_closure_primitives_vectors_and_owner_approval(self):
        conditions, assessment = assess_activation(self.projection, self.review, self.matrix, self.design)
        self.assertEqual(conditions, self.activation.to_dict()["current_evidence"])
        self.assertEqual(assessment, self.activation.to_dict()["assessment"])
        self.assertTrue(conditions["source_artifact_verified"])
        self.assertTrue(conditions["projection_package_verified"])
        self.assertTrue(conditions["projection_review_complete"])
        for missing in ("runtime_used_rules_ready", "dependency_closure_satisfied",
                        "exception_closure_satisfied", "semantic_primitives_implemented",
                        "deterministic_test_vectors_passed", "explicit_owner_activation"):
            with self.subTest(missing=missing):
                self.assertFalse(conditions[missing])
                self.assertIn(missing, assessment["failed_requirements"])
        self.assertFalse(assessment["requirements_satisfied"])
        self.assertTrue(assessment["activation_denied"])

    def test_all_true_claims_cannot_manufacture_real_activation_evidence(self):
        actual, _ = assess_activation(self.projection, self.review, self.matrix, self.design)
        claimed, result = assess_activation(self.projection, self.review, self.matrix, self.design,
                                           claimed_conditions={name: True for name in REQUIREMENTS})
        self.assertEqual(claimed, actual)
        self.assertFalse(result["requirements_satisfied"])
        self.assertTrue(result["activation_denied"])
        withheld = {name: True for name in REQUIREMENTS}
        withheld["projection_review_complete"] = False
        reduced, result = assess_activation(self.projection, self.review, self.matrix, self.design,
                                           claimed_conditions=withheld)
        self.assertFalse(reduced["projection_review_complete"])
        self.assertIn("projection_review_complete", result["failed_requirements"])

    def test_activation_requires_typed_identity_bound_review_matrix_and_design(self):
        for index, replacement in ((1, None), (1, self.review.to_dict()),
                                   (2, self.matrix.to_dict()), (3, self.design.to_dict())):
            arguments = [self.projection, self.review, self.matrix, self.design]
            arguments[index] = replacement
            with self.subTest(index=index), self.assertRaises(GameplayContractError):
                assess_activation(*arguments)
        matrix_body = body(self.matrix)
        matrix_body["projection_review_id"] = OTHER_HASH
        other_matrix = RealRulesCapabilityMatrix.create(matrix_body)
        with self.assertRaises(GameplayContractError):
            assess_activation(self.projection, self.review, other_matrix, self.design)
        with self.assertRaises(GameplayContractError):
            build_profile_design(self.review, other_matrix)
        design_body = body(self.design)
        design_body["required_rule_set_id"] = OTHER_HASH
        design_body["proof_trace_design"]["required_rule_set_id"] = OTHER_HASH
        wrong_rule_set = RealRulesExecutionProfileDesign.create(design_body)
        with self.assertRaises(GameplayContractError):
            assess_activation(self.projection, self.review, self.matrix, wrong_rule_set)
        review_body = body(self.review)
        review_body["rules"][0]["source_anchor"]["span_sha256"] = OTHER_HASH
        forged_review = FoundationalProjectionReview.create(review_body)
        forged_matrix = build_capability_matrix(forged_review)
        forged_design = build_profile_design(forged_review, forged_matrix)
        with self.assertRaises(GameplayContractError):
            assess_activation(self.projection, forged_review, forged_matrix, forged_design)

    def test_retained_readiness_is_blocked_and_next_milestone_only_recommended(self):
        self.assertEqual(self.readiness.overall_execution_readiness, "BLOCKED")
        self.assertEqual(self.readiness.readiness_code, "REAL_EXECUTION_PROFILE_NOT_READY")
        self.assertEqual(set(self.readiness.unresolved_dependencies), {"104.3a", "111.2", "112.2", "113.10", "407"})
        self.assertEqual(set(self.readiness.unprojected_exceptions), set.union(*EXCEPTIONS.values()))
        self.assertEqual(len(self.readiness.unprojected_exceptions), 19)
        self.assertEqual(self.readiness.next_milestone["candidate"], "Foundational Dependency & Exception Projection")
        self.assertFalse(self.readiness.next_milestone["authorized"])


class ProfileVersionAndProofDesignTests(ExecutionDesignFixture):
    def test_profile_target_and_future_snapshot_are_separate_explicit_inactive_contracts(self):
        self.assertEqual(self.design.target_profile_id, "magic-comprehensive-rules-20260925-v1")
        self.assertEqual(self.design.target_label, "DESIGN_TARGET_NOT_EXECUTABLE")
        self.assertEqual(self.design.status, "DESIGN_ONLY")
        compatibility = self.design.engine_compatibility_target
        self.assertEqual(compatibility["observed_execution_profile"], "fictional-two-player-v1")
        self.assertEqual(compatibility["observed_engine_contract"], "gameplay-kernel-v1")
        self.assertEqual(compatibility["target_engine_contract"], "gameplay-real-rules-kernel-v1")
        self.assertFalse(compatibility["compatible_with_current_runtime"])
        self.assertEqual(compatibility["target_implementation_status"], "NOT_IMPLEMENTED")
        self.assertFalse(self.design.future_snapshot_design["snapshot_instantiated"])
        self.assertEqual(self.design.future_snapshot_design["proposed_schema"], "gameplay-real-rules-snapshot-v1")

    def test_future_snapshot_requires_source_projection_review_closure_primitive_and_replay_bindings(self):
        self.assertTrue({
            "exact_source_release", "artifact_hash", "artifact_verification_id",
            "artifact_correspondence_review_id", "projection_package_id", "projection_id",
            "design_review_id", "execution_approval_review_id", "execution_profile_id",
            "engine_contract_version", "rule_set_id", "primitive_registry_id_and_version",
            "capability_matrix_id", "closure_assessment_id", "deterministic_test_vector_evidence_id",
            "owner_activation_receipt_id",
        } <= set(self.design.future_snapshot_design["required_bindings"]))
        self.assertEqual(self.design.required_projection_review_id, self.review.identity)
        self.assertIsNone(self.design.required_execution_approval_review_id)

    def test_proof_trace_binds_exact_source_projection_review_and_rule_set_without_real_result(self):
        trace = self.design.proof_trace_design
        self.assertEqual(trace["source_artifact_hash"], ARTIFACT_HASH)
        self.assertEqual(trace["projection_id"], PROJECTION_ID)
        self.assertEqual(trace["projection_review_id"], self.review.identity)
        self.assertEqual(trace["required_rule_set_id"], self.design.required_rule_set_id)
        self.assertEqual(trace["anchor_binding"], "EXACT_RETAINED_SOURCE_ANCHORS")
        self.assertEqual(trace["unsupported_policy"], "INDETERMINATE_OR_UNSUPPORTED")
        self.assertFalse(trace["result_instantiated"])
        self.assertEqual(tuple(trace["chain"]), (
            "future_LegalityResult", "versioned_executable_primitive", "required_rule_set_id",
            "projection_review_id", "reviewed_projection_rule_reference", "exact_source_anchor",
            "official_artifact_hash_and_release",
        ))
        for field in ("source_artifact_hash", "projection_id", "projection_review_id", "required_rule_set_id"):
            value = body(self.design)
            value["proof_trace_design"][field] = OTHER_HASH
            with self.subTest(field=field), self.assertRaises(GameplayContractError):
                RealRulesExecutionProfileDesign.create(value)

    def test_release_updates_require_new_revisions_and_cannot_mutate_pinned_replays(self):
        self.assertEqual(self.design.source_binding["effective_date"], "2026-09-25")
        policy = self.design.release_update_policy
        self.assertFalse(policy["implicit_latest_allowed"])
        self.assertFalse(policy["mutation_allowed"])
        self.assertFalse(policy["cross_profile_fallback"])
        self.assertEqual(policy["old_replays"], "PINNED_IMMUTABLE_IDENTITIES")
        self.assertTrue({"new_artifact_identity", "new_projection_identities", "new_projection_reviews",
                         "new_real_execution_profile_revision", "new_activation_authorization"}
                        <= set(policy["new_release_requires"]))
        for alias in ("magic-current", "magic-latest", "fictional-two-player-v1"):
            value = body(self.design)
            value["target_profile_id"] = alias
            with self.subTest(alias=alias), self.assertRaises(GameplayContractError):
                RealRulesExecutionProfileDesign.create(value)
        value = body(self.design)
        value["source_binding"]["effective_date"] = "2026-10-01"
        with self.assertRaises(GameplayContractError):
            RealRulesExecutionProfileDesign.create(value)


class ExecutionDesignPackageTests(ExecutionDesignFixture):
    def test_retained_package_is_canonical_and_rebuilds_identically_from_metadata(self):
        rebuilt = build_design_package(**ROOTS)
        self.assertEqual(set(rebuilt), set(RECORD_TYPES))
        self.assertEqual({path.name for path in PACKAGE.iterdir()}, set(RECORD_TYPES) | {"manifest.json"})
        self.assertEqual(rebuilt, self.records)
        for name, record in rebuilt.items():
            self.assertEqual((PACKAGE / name).read_bytes(), (record.serialize() + "\n").encode("utf-8"))
        raw = {name: (PACKAGE / name).read_bytes() for name in RECORD_TYPES}
        manifest = package_manifest(rebuilt, raw)
        self.assertEqual((PACKAGE / "manifest.json").read_bytes(),
                         (deterministic_json(manifest) + "\n").encode("utf-8"))
        self.assertEqual(manifest["canonical_base"], "90ce520be8b0319111ca74fdb385b01de522523a")

    def test_build_and_load_need_no_network_source_txt_real_snapshot_or_legality_result(self):
        with ExitStack() as stack:
            for target in ("socket.socket", "gameplay_rules.source_evidence.artifacts.verify_local_artifact",
                           "gameplay_rules.projection.source.build_projection",
                           "gameplay_rules.models.GameplayRulesSnapshot.create",
                           "gameplay_rules.models.LegalityResult.create"):
                stack.enter_context(patch(target, side_effect=AssertionError("Forbidden design dependency")))
            rebuilt = build_design_package(**ROOTS)
            loaded = load_design_package(PACKAGE, **ROOTS)
        self.assertEqual(rebuilt, loaded)
        self.assertFalse(self.design.source_evidence_requirements["external_txt_required_for_design"])
        self.assertTrue(self.design.source_evidence_requirements["offline_design_reproducible"])

    def test_package_integrity_rejects_changed_missing_extra_symlink_and_oversized_files(self):
        for mutation in ("changed", "missing", "extra", "symlink", "oversized"):
            with self.subTest(mutation=mutation), tempfile.TemporaryDirectory(prefix="mtglab-design-test-") as temporary:
                directory = Path(temporary) / "package"
                shutil.copytree(PACKAGE, directory)
                target = directory / "readiness.json"
                if mutation == "changed":
                    target.write_bytes(target.read_bytes().replace(b"BLOCKED", b"READY!!", 1))
                elif mutation == "missing":
                    target.unlink()
                elif mutation == "extra":
                    (directory / "private-source.txt").write_text("Original private fixture sentinel.")
                elif mutation == "symlink":
                    target.unlink()
                    target.symlink_to(PACKAGE / "readiness.json")
                else:
                    target.write_bytes(b" " * 128001)
                with self.assertRaises(GameplayContractError) as caught:
                    load_design_package(directory, **ROOTS)
                self.assertNotIn(str(directory), str(caught.exception))
                self.assertNotIn("Original private fixture sentinel", str(caught.exception))

    def test_coherently_rehashed_anchor_substitution_still_fails_projection_correspondence(self):
        records = dict(self.records)
        value = body(self.review)
        value["rules"][0]["source_anchor"]["span_sha256"] = OTHER_HASH
        records["projection-review.json"] = FoundationalProjectionReview.create(value)
        with tempfile.TemporaryDirectory(prefix="mtglab-design-rehash-") as temporary:
            directory = Path(temporary)
            write_package(directory, records)
            with self.assertRaises(GameplayContractError):
                load_design_package(directory, **ROOTS)

    def test_coherent_new_design_revision_and_cross_record_rehash_are_not_the_retained_review(self):
        records = dict(self.records)
        design_value = body(self.design)
        design_value["design_version"] = "real-rules-execution-profile-design-v2"
        records["execution-profile-design.json"] = RealRulesExecutionProfileDesign.create(design_value)
        activation_value = body(self.activation)
        activation_value["profile_design_id"] = records["execution-profile-design.json"].identity
        records["activation-gates.json"] = RealRulesActivationGateDesign.create(activation_value)
        readiness_value = body(self.readiness)
        readiness_value["profile_design_id"] = records["execution-profile-design.json"].identity
        readiness_value["activation_gate_design_id"] = records["activation-gates.json"].identity
        records["readiness.json"] = RealRulesExecutionReadiness.create(readiness_value)
        with tempfile.TemporaryDirectory(prefix="mtglab-design-revision-") as temporary:
            directory = Path(temporary)
            write_package(directory, records)
            with self.assertRaises(GameplayContractError):
                load_design_package(directory, **ROOTS)

    def test_manifest_rejects_duplicate_keys_nonfinite_and_unexpected_fields(self):
        raw = (PACKAGE / "manifest.json").read_text()
        mutations = (
            '{"reviewed_rule_count":20,' + raw[1:],
            raw.replace('"reviewed_rule_count":20', '"reviewed_rule_count":NaN'),
            raw.replace('"reviewed_rule_count":20', '"reviewed_rule_count":Infinity'),
            '{"unexpected":"fixture",' + raw[1:],
        )
        for index, mutation in enumerate(mutations):
            with self.subTest(index=index), tempfile.TemporaryDirectory(prefix="mtglab-design-manifest-") as temporary:
                directory = Path(temporary) / "package"
                shutil.copytree(PACKAGE, directory)
                (directory / "manifest.json").write_text(mutation)
                with self.assertRaises(GameplayContractError):
                    load_design_package(directory, **ROOTS)

    def test_cli_success_is_integrity_only_and_bad_package_error_is_sanitized(self):
        def arguments(directory):
            result = [str(directory)]
            for key, value in ROOTS.items():
                result.extend(["--" + key.replace("_", "-"), str(value)])
            return result

        output = io.StringIO()
        with redirect_stdout(output):
            exit_code = main(arguments(PACKAGE))
        self.assertEqual(exit_code, 0)
        result = json.loads(output.getvalue())
        self.assertEqual(result["status"], "VERIFIED_DESIGN_PACKAGE_INTEGRITY")
        self.assertEqual(result["projection_review_id"], self.review.identity)
        self.assertEqual(result["execution_profile_design_id"], self.design.identity)
        self.assertEqual(result["rules_reviewed"], 20)
        self.assertTrue(result["activation_denied"])
        self.assertFalse(result["source_txt_required"])
        self.assertFalse(result["real_rules_executable"])
        with tempfile.TemporaryDirectory(prefix="mtglab-private-sentinel-") as temporary:
            directory = Path(temporary)
            (directory / "manifest.json").write_text("Original private fixture body sentinel")
            output = io.StringIO()
            with redirect_stdout(output):
                exit_code = main(arguments(directory))
            self.assertEqual(exit_code, 1)
            result = json.loads(output.getvalue())
            self.assertEqual(result, {"error": "EXECUTION_DESIGN_VERIFICATION_BLOCKED",
                                      "real_rules_executable": False, "activation_denied": True})
            self.assertNotIn(str(directory), output.getvalue())
            self.assertNotIn("Original private fixture body sentinel", output.getvalue())


if __name__ == "__main__":
    unittest.main()
