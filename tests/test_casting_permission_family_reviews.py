"""Incremental permission explanation, relationship provenance and closed scope."""
from copy import deepcopy
from pathlib import Path
import unittest

from gameplay_rules.errors import GameplayContractError
from gameplay_rules.casting_permission_family import package
from gameplay_rules.casting_permission_family import reviews

ROOT = Path(__file__).resolve().parents[1]
REVIEW_ROOT = ROOT / "reference-reviews"


class CastingPermissionFamilyReviewTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.records = package.load_package(REVIEW_ROOT / package.PACKAGE_NAME, review_root=REVIEW_ROOT)
        cls.current = package.current_view(cls.records)
        cls.view = cls.current["records"]

    def test_inventory_arithmetic_is_derived_from_disjoint_actual_components(self):
        composite = self.view["composite-coverage.json"]["findings"]
        components = composite["projection_components"]
        prior = [ref for component in components[:-1] for ref in component["projected_references"]]
        new = components[-1]["projected_references"]
        all_references = prior + new
        self.assertEqual((len(prior), len(set(prior)), len(components[:-1])), (93, 93, 14))
        self.assertEqual(new, list(reviews.FAMILY))
        self.assertFalse(set(prior).intersection(new))
        self.assertEqual((len(all_references), len(set(all_references)), len(components)), (100, 100, 15))
        self.assertEqual(len({row["projection_id"] for row in components}), 15)
        self.assertEqual(set(prior), set(package.retained_binding()["rule_bindings"]))
        self.assertEqual(components[-1]["package_id"], self.current["package_id"])
        for key, value in (("stage_coverage", "9/9"), ("parent_proposal_range_coverage", "4/4"),
                ("single_activated_import_coverage", "8/8"), ("i_preceding_range_source_coverage", "8/8")):
            self.assertEqual(composite[key], value)
        self.assertEqual(composite["complete_601_3_family_coverage"], "7/7")
        self.assertIs(composite["broad_601_complete"], False)
        self.assertEqual(composite["additional_rules_projected"], [])

    def test_each_new_rule_and_anchor_has_its_actual_own_package_binding(self):
        projection = self.records["projection.json"]
        rules = {row["rule_reference"]: row for row in projection["rules"]}
        rows = self.view["source-correspondence.json"]["findings"]["new_rule_bindings"]
        self.assertEqual([row["rule_reference"] for row in rows], list(reviews.FAMILY))
        for row in rows:
            rule = rules[row["rule_reference"]]
            self.assertEqual(row["package_id"], self.current["package_id"])
            self.assertEqual(row["projection_id"], projection["projection_id"])
            self.assertEqual(row["rule_id"], rule["rule_id"])
            self.assertEqual(row["anchor_identity"], rule["source_anchor"]["anchor_id"])
            self.assertEqual(row["source_anchor"], rule["source_anchor"])
            self.assertNotIn("package_binding", row)
        self.assertEqual(len({row["rule_id"] for row in rows}), 7)
        self.assertEqual(len({row["anchor_identity"] for row in rows}), 7)

    def test_inventory_is_frozen_before_bodies_and_preflight_does_not_expand(self):
        scope = self.view["scope-preflight.json"]["findings"]
        inventory = scope["source_selection"]
        self.assertEqual(inventory["ordered_allowlist"], list(reviews.FAMILY))
        self.assertEqual(inventory["unit_count"], 7)
        self.assertIs(inventory["inventory_frozen_before_body_inspection"], True)
        self.assertEqual(inventory["following_sibling_boundary"], {
            "rule_reference": "601.4", "physical_line": 2501, "body_inspected": False})
        preflight = scope["preflight"]
        self.assertEqual(preflight["conclusion"], "PASSED")
        self.assertEqual(preflight["stop_code_if_insufficient"], "CASTING_PERMISSION_FAMILY_SCOPE_INSUFFICIENT")
        self.assertEqual(preflight["literal_citations"], {ref: [] for ref in reviews.FAMILY})
        self.assertEqual(preflight["literal_ranges"], {ref: [] for ref in reviews.FAMILY})
        self.assertEqual(preflight["additional_source_units_required"], [])
        self.assertEqual(preflight["additional_source_units_admitted"], [])
        self.assertIs(preflight["neighbor_or_outgoing_reference_bodies_inspected"], False)
        correspondence = self.view["source-correspondence.json"]["findings"]
        self.assertIs(correspondence["offline_metadata_validation_is_fresh_source_verification"], False)
        self.assertIs(correspondence["fictional_fixtures_supply_source_authority"], False)
        self.assertEqual(correspondence["hosted_missing_artifact_means"], "EXPLICIT_SOURCE_DEPENDENT_SKIP")
        self.assertIs(correspondence["historical_marker_observation"]["prior_body_or_child_inventory_verification"], False)

    def test_permission_contributions_keep_beginning_choice_cost_and_characteristic_limits(self):
        assessment = self.view["permission-assessment.json"]["findings"]
        rows = assessment["incremental_contributions"]
        self.assertEqual([row["reference"] for row in rows], list(reviews.FAMILY))
        for row in rows:
            self.assertTrue(row["bounded_fact"])
            self.assertTrue(row["required_Card_effect_state_evidence"])
            self.assertEqual(row["actual_proposed_spell_legality"], "UNKNOWN_OR_UNSUPPORTED")
        limits = assessment["conditional_limits"]
        for value in limits.values():
            self.assertIs(value, False)
        self.assertIn("replace", rows[5]["bounded_fact"])
        self.assertIn("continuous effects", rows[5]["bounded_fact"])
        self.assertIn("can look", rows[6]["bounded_fact"])
        self.assertIn("one compatible set", assessment["choice_consistency"])
        context = assessment["retained_context"]
        self.assertEqual(context["procedure_map"]["package_id"], reviews.PR207_PACKAGE)
        self.assertEqual(context["procedure_map"]["stage_source_coverage"], "9/9")
        self.assertIs(context["procedure_map"]["map_repeated"], False)
        for key, reference in (("permission_to_begin_and_ordered_procedure", "601.2"),
                ("legality_checkpoint", "601.2e"), ("completion", "601.2i")):
            expected = {"rule_reference": reference, **package.retained_binding()["rule_bindings"][reference]}
            self.assertEqual(context[key], expected)
        self.assertIs(assessment["permission_or_legality_evaluator_created"], False)

    def test_authored_cases_have_assumptions_evidence_limits_and_no_runtime_authority(self):
        assessment = self.view["permission-assessment.json"]["findings"]
        cases = assessment["authored_explanatory_cases"]
        self.assertEqual(len(cases), 5)
        covered = set()
        for case in cases:
            self.assertTrue(case["hypothetical_assumptions"])
            self.assertTrue(case["applicable_rule_evidence"])
            self.assertTrue(case["bounded_conclusion"])
            self.assertTrue(case["missing_or_unresolved"])
            covered.update(row["rule_reference"] for row in case["applicable_rule_evidence"])
        self.assertTrue(set(reviews.FAMILY).issubset(covered))
        self.assertIs(assessment["real_Card_or_Oracle_data_used"], False)
        self.assertIs(assessment["official_examples_retained"], False)
        self.assertIs(assessment["scenario_system_created"], False)

    def test_parent_reference_resolution_is_individual_and_e_overlap_is_not_a_citation(self):
        relationships = self.view["relationship-reassessment.json"]["findings"]
        parent = relationships["parent_reference_reassessment"]
        self.assertEqual((parent["origin"], parent["target"]), ("601.2", "601.3"))
        self.assertEqual(parent["relationship"], "RETAINED_LITERAL_REFERENCE")
        self.assertEqual((parent["historical_status"], parent["current_status"]),
            ("UNRESOLVED", "DIRECT_REFERENCE_RESOLVED"))
        self.assertEqual(parent["resolution_level"], "INDIVIDUAL_TARGET_SOURCE_COVERAGE_ONLY")
        self.assertEqual(parent["semantic_closure"], "OPEN")
        self.assertIs(parent["individual_reference_resolution_implies_family_or_semantic_closure"], False)
        self.assertIs(parent["historical_record_unchanged"], True)
        checkpoint = relationships["checkpoint_overlap"]
        self.assertIs(checkpoint["literal_601_2e_to_601_3_citation"], False)
        self.assertEqual(checkpoint["actual_literal_601_2e_reference"], {"target": "733", "status": "UNRESOLVED"})
        structure = relationships["family_structure"]
        self.assertEqual([row["rule_reference"] for row in structure["children"]], list(reviews.FAMILY[1:]))
        self.assertIs(structure["literal_parent_citations_invented"], False)

    def test_activation_import_completion_and_historical_self_bindings_remain_separate(self):
        relationships = self.view["relationship-reassessment.json"]["findings"]
        preserved = relationships["retained_ranges"]
        imported = preserved["activated_import"]
        self.assertEqual((imported["range_import_count"], imported["member_count"]), (1, 8))
        self.assertEqual([row["reference"] for row in imported["range_members"]], list(reviews.STAGES[1:]))
        self.assertEqual(imported["excluded_stages"], ["601.2a"])
        self.assertEqual(imported["separate_cost_analogy"]["target"], "601.2f")
        completion = preserved["completion_range"]
        self.assertEqual([row["reference"] for row in completion["range_members"]], list(reviews.STAGES[:-1]))
        self.assertEqual(completion["semantics"]["priority_condition"], "SPELL_CONTROLLER_HAD_PRIORITY_BEFORE_CASTING")
        self.assertIs(completion["semantics"]["unconditional_priority_return"], False)
        self.assertEqual(completion["origin_evidence"]["package_id"], reviews.PR207_PACKAGE)
        self.assertNotEqual(completion["origin_evidence"]["package_id"], self.current["package_id"])
        self.assertIs(relationships["activation_boundary"]["601_3_automatically_governs_abilities_via_b_i_import"], False)
        self.assertIs(relationships["source_coverage_is_actual_permission_legality_completion_or_execution"], False)

    def test_outside_frontiers_and_all_ten_responsibilities_stay_open(self):
        relationships = self.view["relationship-reassessment.json"]["findings"]
        frontiers = relationships["unresolved_literal_frontiers"]
        self.assertEqual([(row["origin"], row["target"]) for row in frontiers],
            [("601.2", "733"), ("601.2e", "733"), ("602.2", "733"),
             ("602.2a", "701.20a"), ("601.2a", "611.2f"), ("601.2a", "610.5")])
        self.assertTrue(all(row["state"] == "UNRESOLVED" and row["target_body_inspected"] is False for row in frontiers))
        self.assertIs(relationships["all_outside_frontier_bodies_inspected_or_admitted"], False)
        responsibilities = relationships["all_ten_activation_responsibilities"]
        self.assertEqual(len(responsibilities), 10)
        self.assertTrue(all(row["state"] == "OPEN / EXECUTION_BLOCKED" and row["implementation_available"] is False
            for row in responsibilities))
        ready = self.view["composite-coverage.json"]["findings"]["preservation_readiness"]
        self.assertEqual(ready["real_execution"], "BLOCKED")
        self.assertEqual(ready["source_policy_clearance"], "not_granted")
        self.assertEqual(set(ready["permissions"].values()), {"NOT_ESTABLISHED"})
        self.assertEqual(ready["protected_PR207_package_id"], reviews.PR207_PACKAGE)
        self.assertEqual(ready["protected_PR207_projection_id"], reviews.PR207_PROJECTION)

    def test_historical_recommendation_stays_unbegun_and_exactly_one_new_outcome_is_unauthorized(self):
        historical = self.view["scope-preflight.json"]["findings"]["historical_recommendation"]
        self.assertEqual(historical["review_id"], reviews.HISTORICAL_RECOMMENDATION)
        self.assertEqual(historical["milestone"], "Legality-input and semantic-frontier reasoning review")
        self.assertIs(historical["historical_future_milestone_authorized"], False)
        self.assertIs(historical["historical_future_milestone_begun"], False)
        subsequent = self.view["subsequent-recommendation.json"]["findings"]
        self.assertEqual(subsequent["recommendation_count"], 1)
        recommendation = subsequent["recommendation"]
        self.assertEqual(recommendation["milestone"], "Proposed-spell evidence packet contract design")
        self.assertEqual(recommendation["proposed_allowlist"], [])
        self.assertEqual(recommendation["expected_added_source_units"], 0)
        for field in ("future_milestone_authorized", "future_source_projection_authorized", "future_milestone_begun"):
            self.assertIs(recommendation[field], False)

    def test_rehashed_false_closure_or_historical_binding_substitution_is_rejected(self):
        mutations = (
            ("permission-assessment.json", lambda v: v["conditional_limits"].update(beginning_guarantees_successful_completion=True)),
            ("permission-assessment.json", lambda v: v["conditional_limits"].update(c_cost_condition_is_prepaid_or_waived=True)),
            ("relationship-reassessment.json", lambda v: v["checkpoint_overlap"].update(literal_601_2e_to_601_3_citation=True)),
            ("relationship-reassessment.json", lambda v: v["activation_boundary"].update(new_literal_activation_to_601_3_edge=True)),
            ("relationship-reassessment.json", lambda v: v["retained_ranges"]["completion_range"]["origin_evidence"].update(package_id=self.current["package_id"])),
            ("composite-coverage.json", lambda v: v.update(total_projected_rule_count=100.0)),
            ("scope-preflight.json", lambda v: v["source_selection"]["ordered_allowlist"].append("601.4")),
        )
        for filename, mutate in mutations:
            candidate = deepcopy(self.records)
            record = candidate[filename]
            mutate(record["findings"])
            record["review_id"] = package._identity(package.RECORD_DOMAIN,
                {key: value for key, value in record.items() if key != "review_id"})
            with self.subTest(filename=filename), self.assertRaises(GameplayContractError):
                package.validate_records(candidate)


if __name__ == "__main__":
    unittest.main()
