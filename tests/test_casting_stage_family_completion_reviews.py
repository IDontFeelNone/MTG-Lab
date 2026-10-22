"""Stage knowledge, actual evidence bindings and separate relationship provenance."""
from copy import deepcopy
import json
from pathlib import Path
import unittest

from gameplay_rules.errors import GameplayContractError
from gameplay_rules.casting_stage_family_completion import package

ROOT = Path(__file__).resolve().parents[1]
REVIEWS = ROOT / "reference-reviews"
STAGES = ["601.2" + letter for letter in "abcdefghi"]


class CastingStageFamilyCompletionReviewTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.records = package.load_package(REVIEWS / package.PACKAGE_NAME, review_root=REVIEWS)
        cls.current = package.current_view(cls.records)
        cls.view = cls.current["records"]

    def assert_actual_binding(self, reference, evidence):
        self.assertEqual(evidence["rule_reference"], reference)
        if reference in ("601.2a", "601.2i"):
            projection = self.records["projection.json"]
            rule = next(row for row in projection["rules"] if row["rule_reference"] == reference)
            self.assertEqual(evidence["package_id"], self.current["package_id"])
            self.assertEqual(evidence["projection_id"], projection["projection_id"])
            self.assertEqual(evidence["rule_id"], rule["rule_id"])
            self.assertEqual(evidence["anchor_identity"], rule["source_anchor"]["anchor_id"])
        else:
            self.assertEqual(evidence, {"rule_reference": reference, **package.retained_binding()["rule_bindings"][reference]})
        self.assertNotIn("package_binding", evidence)

    def test_exact_two_unit_admission_completes_nine_stages_without_broad_closure(self):
        value = self.view["composite-coverage.json"]["findings"]
        components = value["projection_components"]
        references = [ref for component in components for ref in component["projected_references"]]
        retained = package.retained_binding()["rule_bindings"]
        self.assertEqual((len(components), len({row["projection_id"] for row in components})), (14, 14))
        self.assertEqual((len(references), len(set(references)), len(retained)), (93, 93, 91))
        self.assertEqual(set(references) - set(retained), {"601.2a", "601.2i"})
        self.assertEqual(components[-1]["projected_references"], ["601.2a", "601.2i"])
        self.assertEqual(components[-1]["package_id"], self.current["package_id"])
        self.assertEqual((value["stage_coverage"], value["parent_proposal_range_coverage"],
            value["single_activated_import_coverage"], value["i_preceding_range_source_coverage"]), ("9/9", "4/4", "8/8", "8/8"))
        self.assertIs(value["broad_601_complete"], False)
        self.assertIs(value["prior_rule_bindings_changed"], False)
        for unadmitted in ("601.3", "733", "701.20a", "611.2f", "610.5", "603"):
            self.assertNotIn(unadmitted, references)

    def test_parent_ranges_keep_original_provenance_and_i_remains_structural(self):
        ranges = self.view["range-reassessment.json"]["findings"]
        parent = ranges["casting_parent"]
        self.assert_actual_binding("601.2", parent["origin_evidence"])
        proposal, cost = parent["proposal_range"], parent["cost_range"]
        self.assertEqual((proposal["start"], proposal["end"], proposal["coverage_before"], proposal["coverage_after"]),
            ("601.2a", "601.2d", "3/4", "4/4"))
        self.assertIs(proposal["original_range_provenance_preserved"], True)
        self.assertEqual([row["reference"] for row in proposal["member_rows"]], STAGES[:4])
        self.assertEqual((cost["start"], cost["end"], cost["coverage"]), ("601.2f", "601.2h", "3/3"))
        self.assertIs(cost["range_and_evidence_unchanged"], True)
        self.assertEqual([row["reference"] for row in cost["member_rows"]], STAGES[5:8])
        for row in proposal["member_rows"] + cost["member_rows"]:
            self.assert_actual_binding(row["reference"], row["projected_evidence"])
        self.assertEqual([row["reference"] for row in parent["structural_siblings"]], ["601.2e", "601.2i"])
        for row in parent["structural_siblings"]:
            self.assertEqual(row["relationship"], "STRUCTURAL_SIBLING_WITHOUT_RETAINED_PARENT_DIRECT_CITATION")
            self.assertIs(row["literal_parent_citation_invented"], False)
        self.assertEqual(parent["preserved_unresolved_literal_references"], ["601.3", "733"])
        original = json.loads((REVIEWS / "gameplay-rules-bounded-casting-projection" / "projection.json").read_bytes())
        retained_parent = next(row for row in original["rules"] if row["rule_reference"] == "601.2")
        self.assertNotIn("601.2i", retained_parent["direct_dependency_references"])
        self.assertIs(parent["stage_coverage_establishes_actual_legality_criteria"], False)

    def test_activation_is_one_b_i_range_with_actual_eight_bindings_and_separate_cost_analogy(self):
        imported = self.view["range-reassessment.json"]["findings"]["activated_import"]
        self.assertEqual(imported["relationship_kind"], "ONE_RANGE_IMPORT_WITH_EIGHT_MEMBER_ROWS")
        self.assertEqual((imported["range_import_count"], imported["member_count"]), (1, 8))
        self.assertEqual((imported["range_start"], imported["range_end"]), ("601.2b", "601.2i"))
        self.assertEqual((imported["member_coverage_before"], imported["member_coverage_after"]), ("7/8", "8/8"))
        self.assertEqual([row["reference"] for row in imported["range_members"]], STAGES[1:])
        for row in imported["range_members"]:
            self.assertEqual(row["coverage"], "PROJECTED")
            self.assert_actual_binding(row["reference"], row["projected_evidence"])
        self.assertEqual(imported["excluded_stages"], ["601.2a"])
        self.assertEqual(imported["literal_direct_reference_edges_inferred_from_membership"], [])
        self.assertIs(imported["i_range_creates_literal_602_2b_to_a_citation"], False)
        self.assertIs(imported["casting_and_activation_interchangeable"], False)
        self.assertIs(imported["spell_specific_facts_apply_unchanged_to_all_abilities"], False)
        analogy = imported["separate_cost_analogy"]
        self.assertEqual((analogy["origin"], analogy["target"], analogy["state"]), ("602.2b", "601.2f", "DIRECT_REFERENCE_RESOLVED"))
        self.assert_actual_binding("601.2f", analogy["target_evidence"])
        self.assertEqual(imported["source_bodies_imported_into_projection"], 0)

    def test_i_has_one_explicit_a_h_range_and_conditional_priority_without_execution(self):
        completion = self.view["range-reassessment.json"]["findings"]["completion_range"]
        self.assertEqual((completion["range_start"], completion["range_end"], completion["range_count"], completion["member_count"]),
            ("601.2a", "601.2h", 1, 8))
        self.assertEqual(completion["source_coverage"], "8/8")
        self.assertEqual([row["reference"] for row in completion["range_members"]], STAGES[:-1])
        for row in completion["range_members"]:
            self.assert_actual_binding(row["reference"], row["projected_evidence"])
        self.assertIs(completion["range_is_a_literal_activation_to_a_citation"], False)
        self.assertEqual(completion["semantics"]["priority_condition"], "SPELL_CONTROLLER_HAD_PRIORITY_BEFORE_CASTING")
        self.assertIs(completion["semantics"]["unconditional_priority_return"], False)
        for field in ("effect_application_implemented", "trigger_detection_ordering_or_placement_implemented", "stack_or_priority_handling_implemented"):
            self.assertIs(completion[field], False)
        i = self.records["projection.json"]["rules"][1]["findings"]
        self.assertEqual(i["priority_context"]["condition"], "CONTROLLER_HAD_PRIORITY_BEFORE_CASTING")
        self.assertIs(i["completion"]["stage_coverage_proves_condition_satisfied"], False)
        self.assertIs(i["trigger_consequence"]["placement_implemented"], False)

    def test_complete_map_explains_each_stage_with_evidence_unknown_inputs_and_missing_machinery(self):
        procedure = self.view["procedure-map.json"]["findings"]
        self.assertEqual(procedure["ordered_references"], STAGES)
        self.assertEqual([row["reference"] for row in procedure["rows"]], STAGES)
        for row in procedure["rows"]:
            self.assert_actual_binding(row["reference"], row["source_evidence"])
            for field in ("bounded_fact", "earlier_later_relationship", "activation_applicability", "unknown_required_inputs_or_criteria", "missing_execution_machinery"):
                self.assertTrue(row[field], (row["reference"], field))
            self.assertEqual(row["actual_legality"], "UNKNOWN_OR_UNSUPPORTED")
            self.assertEqual(row["execution_readiness"], "BLOCKED")
        self.assertEqual(procedure["rows"][0]["activation_applicability"], "EXCLUDED_FROM_LITERAL_B_THROUGH_I_IMPORT")
        self.assertTrue(all(row["activation_applicability"] == "MEMBER_OF_SINGLE_RETAINED_602.2b_RANGE_IMPORT" for row in procedure["rows"][1:]))
        self.assertEqual(len(procedure["explanatory_checks"]), 4)
        self.assertTrue(all(row["answer"] and row["evidence"] and row["relationship"] for row in procedure["explanatory_checks"]))
        self.assertIs(procedure["real_Card_or_Oracle_data_used"], False)
        self.assertIs(procedure["scenario_engine_created"], False)

    def test_scope_decision_preserves_historical_recommendation_and_assesses_missing_inputs(self):
        scope = self.view["scope-decision.json"]["findings"]
        historical = json.loads((REVIEWS / "gameplay-rules-bounded-shared-proposal-legality" / "subsequent-recommendation.json").read_bytes())
        self.assertEqual(scope["historical_recommendation"]["review_id"], historical["review_id"])
        self.assertIs(scope["historical_recommendation"]["record_unchanged"], True)
        self.assertEqual(scope["selected_source_allowlist"], ["601.2a", "601.2i"])
        preflight = self.view["preflight.json"]["findings"]
        self.assertEqual(preflight["conclusion"], "PASSED")
        self.assertEqual(preflight["literal_citations"], {"601.2a": ["611.2f", "610.5"], "601.2i": []})
        self.assertEqual(preflight["additional_source_units_admitted"], [])
        self.assertIs(preflight["recursive_projection_required"], False)
        gap = self.view["legality-gap-assessment.json"]["findings"]
        self.assertEqual({row["category"] for row in gap["missing_inputs"]},
            {"ACTION_AND_OBJECT_INFORMATION", "APPLICABLE_STATE", "LEGALITY_CRITERIA", "CONDITIONAL_COMPLETION"})
        self.assertEqual([(row["origin"], row["target"]) for row in gap["unresolved_frontiers"]],
            [("601.2", "601.3"), ("601.2", "733"), ("601.2e", "733"), ("602.2", "733"),
             ("602.2a", "701.20a"), ("601.2a", "611.2f"), ("601.2a", "610.5")])
        self.assertTrue(all(row["state"] == "UNRESOLVED" and row["target_body_inspected"] is False for row in gap["unresolved_frontiers"]))
        for field in ("criteria_supplied_by_checkpoint", "procedure_order_proves_legality", "full_payment_proves_legality", "absence_of_detected_violation_proves_legality", "legality_solved"):
            self.assertIs(gap[field], False)

    def test_fresh_i_anchor_matches_review_fingerprint_without_promoting_historical_authority(self):
        correspondence = self.view["source-correspondence.json"]["findings"]
        observation = correspondence["i_retained_review_only_observation"]
        folder = REVIEWS / "gameplay-rules-shared-casting-stage-gap-design"
        record = json.loads((folder / "source-inspection.json").read_bytes())
        manifest = json.loads((folder / "manifest.json").read_bytes())
        self.assertEqual(observation["package_id"], manifest["package_id"])
        self.assertEqual(observation["review_id"], record["review_id"])
        self.assertEqual(observation["record_own_identity_field"], "review_id")
        self.assertIs(type(observation["record_schema_version"]), int)
        historical = next(row for row in record["findings"]["review_spans"] if row["reference"] == "601.2i")
        fresh = self.records["projection.json"]["rules"][1]["source_anchor"]
        for field in ("byte_start", "byte_end", "starting_physical_line", "ending_physical_line", "line_count", "owned_example_line_count", "span_sha256"):
            self.assertEqual(fresh[field], historical[field])
            self.assertEqual(observation["historical_span"][field], historical[field])
        self.assertEqual(observation["historical_span"]["span_length"], 341)
        self.assertIs(historical["registered_projected_source_anchor"], False)
        self.assertIs(observation["historical_registered_projected_source_anchor"], False)
        self.assertIs(observation["historical_observation_changed"], False)
        self.assertIs(observation["fresh_verification_required_and_performed"], True)
        self.assertEqual(record["findings"]["current_projection_allowlist"], [])
        self.assertEqual(record["findings"]["new_registered_projected_source_anchors"], 0)
        self.assertIs(correspondence["a_previously_verified_body_finding_assumed"], False)
        self.assertIs(correspondence["offline_metadata_validation_is_fresh_source_verification"], False)

    def test_semantic_frontiers_responsibilities_permissions_and_single_next_recommendation_stay_open(self):
        semantic = self.view["consumer-semantic-boundaries.json"]["findings"]
        self.assertEqual(semantic["madness"]["kind"], "INDIRECT_CONSUMER")
        self.assertIs(semantic["madness"]["new_direct_a_or_i_citation"], False)
        self.assertEqual(len(semantic["activated_responsibilities"]), 10)
        self.assertTrue(all(row["state"] == "OPEN / EXECUTION_BLOCKED" and row["implementation_available"] is False for row in semantic["activated_responsibilities"]))
        self.assertEqual(semantic["preserved_relationships"][0]["assessment_level"], "SOURCE_COVERAGE_ONLY")
        self.assertEqual(semantic["preserved_relationships"][0]["state"], "DIRECT_REFERENCE_RESOLVED")
        self.assertIs(semantic["target_concepts"]["zero_count_establishes_mana_ability_eligibility"], False)
        self.assertEqual(semantic["mana_distinctions"]["priority_condition"], "PRIORITY_IMMEDIATELY_BEFORE_ACTIVATION")
        self.assertIs(semantic["source_coverage_is_semantic_or_execution_closure"], False)
        ready = self.view["preservation-readiness.json"]["findings"]
        self.assertEqual((ready["real_execution"], ready["semantic_closure"]), ("BLOCKED", "OPEN"))
        self.assertEqual(ready["source_policy_clearance"], "not_granted")
        self.assertEqual(set(ready["permissions"].values()), {"NOT_ESTABLISHED"})
        self.assertEqual(ready["historical_acquisition_identity"], "sha256:669d7db9ebcaf97853058fd62f408ce3c6596d5dae0ee72ff39d2ba9df56bb53")
        subsequent = self.view["subsequent-recommendation.json"]["findings"]
        self.assertEqual(subsequent["recommendation_count"], 1)
        self.assertEqual(subsequent["recommendation"]["proposed_allowlist"], [])
        for field in ("future_milestone_authorized", "future_source_projection_authorized", "future_milestone_begun"):
            self.assertIs(subsequent["recommendation"][field], False)

    def test_rehashed_relationship_expansion_or_binding_substitution_is_rejected(self):
        for mutate in (
                lambda value: value["activated_import"]["range_members"].insert(0, deepcopy(value["completion_range"]["range_members"][0])),
                lambda value: value["activated_import"].update(range_import_count=8),
                lambda value: value["activated_import"].update(literal_direct_reference_edges_inferred_from_membership=["601.2a"]),
                lambda value: value["casting_parent"]["structural_siblings"][1].update(literal_parent_citation_invented=True),
                lambda value: value["completion_range"]["semantics"].update(unconditional_priority_return=True),
                lambda value: value["activated_import"]["range_members"][3]["projected_evidence"].update(package_id=self.current["package_id"])):
            records = deepcopy(self.records)
            record = records["range-reassessment.json"]
            mutate(record["findings"])
            record["review_id"] = package._identity(package.RECORD_DOMAIN,
                {key: item for key, item in record.items() if key != "review_id"})
            with self.subTest(mutate=mutate), self.assertRaises(GameplayContractError):
                package.validate_records(records)


if __name__ == "__main__":
    unittest.main()
