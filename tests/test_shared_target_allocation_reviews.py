"""Meaningful current coverage and source/semantic provenance regressions."""
from pathlib import Path
import unittest

from gameplay_rules.shared_target_allocation import package

ROOT = Path(__file__).resolve().parents[1]


class SharedTargetAllocationReviewTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.records = package.load_package(ROOT / "reference-reviews" / package.PACKAGE_NAME,
            review_root=ROOT / "reference-reviews")

    def test_parent_resolution_retains_explicit_range_provenance(self):
        value = self.records["casting-parent-reassessment.json"]["findings"]
        self.assertEqual(value["state"], "DIRECT_REFERENCE_RESOLVED")
        self.assertEqual(value["assessment_level"], "SOURCE_COVERAGE_ONLY")
        self.assertEqual(value["source_provenance"]["explicit_range_start"], "601.2a")
        self.assertEqual(value["source_provenance"]["explicit_range_end"], "601.2d")
        self.assertFalse(value["source_provenance"]["parent_individually_enumerates_d"])
        self.assertEqual(value["projected_proposal_members"], ["601.2b", "601.2c", "601.2d"])
        self.assertEqual(value["unprojected_proposal_members"], ["601.2a"])
        self.assertFalse(value["parent_procedure_complete"])

    def test_single_import_has_eight_members_and_actual_d_and_retained_c_identity_bindings(self):
        value = package.current_view(self.records)
        row = value["records"]["activated-import-reassessment.json"]["findings"]
        self.assertEqual(row["range_import_count"], 1)
        self.assertEqual(len(row["range_members"]), 8)
        self.assertEqual(row["projected_members"], ["601.2b", "601.2c", "601.2d", "601.2f", "601.2g", "601.2h"])
        self.assertEqual(row["unprojected_members"], ["601.2e", "601.2i"])
        self.assertEqual(row["member_coverage"], "6/8")
        self.assertEqual(row["excluded_stages"], ["601.2a"])
        self.assertEqual(row["literal_direct_reference_edges_inferred_from_membership"], [])
        self.assertFalse(row["additional_applicability_qualifier_found"])
        c = row["range_members"][2]["projected_evidence"]
        projection = self.records["projection.json"]
        self.assertEqual(c["package_id"], value["package_id"])
        self.assertEqual(c["projection_id"], projection["projection_id"])
        self.assertEqual(c["rule_id"], projection["rules"][0]["rule_id"])
        self.assertEqual(c["anchor_identity"], projection["rules"][0]["source_anchor"]["anchor_id"])
        self.assertEqual(c["source_anchor"], projection["rules"][0]["source_anchor"])

        retained_c = row["range_members"][1]["projected_evidence"]
        self.assertEqual(retained_c["package_id"], "sha256:55b70ae4c7c8fa5f4abadba27a0205f1c433aaff3f6de74f1d42829cf1b999ce")
        self.assertEqual(retained_c["projection_id"], "sha256:5195b58cb6525dd6fc3a86b5e6511392597e6ea089514df3ab62cdcb21dee016")
        self.assertEqual(retained_c["rule_id"], "sha256:d6076ca821f51ee3d694efc7fe38a5c822436d17682889a302e4236c6674506b")
        self.assertEqual(retained_c["anchor_identity"], "sha256:2d8cc88aed759ca45fa2eedec589c2148e6a351e15b1340ffb21927494740b1d")
        self.assertEqual(row["separate_cost_analogy"]["relationship"], "SEPARATE_LITERAL_COST_ANALOGY")
        self.assertFalse(row["historical_pr202_five_of_eight_record_modified"])

    def test_allocation_minimum_is_conditional_and_unknown_inputs_stay_unknown(self):
        value = self.records["consumer-semantic-boundaries.json"]["findings"]["allocation_declaration"]
        self.assertEqual(value["actor"], "CASTING_PLAYER")
        self.assertEqual(value["condition"], "SPELL_REQUIRES_DIVISION_OR_DISTRIBUTION_OF_AN_EFFECT_AMONG_ONE_OR_MORE_TARGETS")
        self.assertEqual(value["recipient_scope"], "EACH_TARGET_OF_THAT_REQUIRED_DISTRIBUTION")
        self.assertIs(type(value["minimum_received_per_scoped_recipient"]), int)
        self.assertEqual(value["minimum_received_per_scoped_recipient"], 1)
        self.assertEqual(value["minimum_subject"], "WHATEVER_IS_BEING_DIVIDED")
        self.assertFalse(value["minimum_applies_to_every_target_of_every_spell_or_ability"])
        self.assertTrue(value["target_declaration_is_separate"])
        self.assertFalse(value["effect_examples_are_exhaustive"])
        self.assertFalse(value["solver_implemented"])
        for field in ("actual_recipients", "total_quantity", "actual_allocation", "card_or_effect_semantics", "applicable_game_state"):
            self.assertEqual(value[field], "UNKNOWN")

    def test_twelve_distinct_projections_admit_exactly_one_new_unit(self):
        value = package.composite_view(self.records)
        components = value["projection_components"]
        references = [reference for item in components for reference in item["projected_references"]]
        prior = package.retained_binding()["rule_bindings"]
        self.assertEqual(len(components), 12)
        self.assertEqual(len({item["projection_id"] for item in components}), 12)
        self.assertEqual(len(references), 90)
        self.assertEqual(len(set(references)), 90)
        self.assertEqual(set(references) - set(prior), {"601.2d"})
        self.assertEqual(len(prior), 89)
        self.assertEqual(components[-1]["package_id"], package.manifest(self.records)["package_id"])

    def test_target_concepts_trigger_consequence_and_consumer_types_stay_distinct(self):
        value = self.records["consumer-semantic-boundaries.json"]["findings"]
        targets = value["target_concepts"]
        self.assertEqual(set(targets) & {"requiring_targets", "actual_chosen_target_count", "targeted_status"},
            {"requiring_targets", "actual_chosen_target_count", "targeted_status"})
        self.assertFalse(targets["zero_count_establishes_mana_ability_eligibility"])
        self.assertIn("one or more", targets["targeted_status"])
        self.assertIn("zero alone does not prove", targets["actual_chosen_target_count"])
        consequence = value["trigger_consequence"]
        self.assertIn("deferred until casting is complete", consequence["description"])
        self.assertTrue(consequence["descriptive_knowledge_only"])
        self.assertFalse(consequence["universal_activated_mana_trigger_or_priority_rule_inferred"])
        self.assertTrue(all(row["literal_citation_from_d"] is False for row in value["context_relationships"]))
        self.assertEqual(value["madness"]["kind"], "INDIRECT_CONSUMER")
        self.assertFalse(value["madness"]["new_direct_d_citation"])
        self.assertEqual([(row["origin"], row["target"], row["state"]) for row in value["preserved_relationships"]],
            [("605.3", "602.2", "DIRECT_REFERENCE_RESOLVED"), ("602.2", "733", "UNRESOLVED"),
             ("602.2a", "701.20a", "UNRESOLVED")])

    def test_all_ten_responsibilities_execution_and_source_permissions_stay_blocked(self):
        semantic = self.records["consumer-semantic-boundaries.json"]["findings"]
        readiness = self.records["preservation-readiness.json"]["findings"]
        self.assertEqual(len(semantic["activated_responsibilities"]), 10)
        self.assertTrue(all(row["state"] == "OPEN / EXECUTION_BLOCKED" and row["implementation_available"] is False
            for row in semantic["activated_responsibilities"]))
        self.assertFalse(semantic["mana_distinctions"]["complete_605_family_source_coverage_establishes_semantic_closure"])
        self.assertEqual(readiness["execution_readiness"], "BLOCKED")
        for field in ("runtime_implemented", "real_snapshot_created", "real_execution_profile_activated", "admission_eligible"):
            self.assertIs(readiness[field], False)
        self.assertEqual(readiness["source_policy_clearance"], "not_granted")
        self.assertEqual(set(readiness["permissions"].values()), {"NOT_ESTABLISHED"})

    def test_exactly_one_retained_evidence_recommendation_is_unbegun(self):
        value = self.records["subsequent-recommendation.json"]["findings"]
        recommendation = value["recommendation"]
        self.assertEqual(value["recommendation_count"], 1)
        self.assertEqual(recommendation["proposed_allowlist"], ["601.2e"])
        self.assertEqual(recommendation["expected_added_source_units"], 1)
        self.assertEqual(recommendation["conditional_resulting_units"], 91)
        self.assertEqual(recommendation["conditional_resulting_projections"], 13)
        self.assertEqual(recommendation["conditional_activated_import_coverage"], "7/8")
        self.assertEqual(value["fresh_additional_body_inspection"], [])
        for field in ("future_milestone_authorized", "future_source_projection_authorized", "future_milestone_begun"):
            self.assertIs(recommendation[field], False)
        self.assertTrue({"601.2i", "701.20a", "733", "603", "runtime"}.issubset(recommendation["explicit_exclusions"]))
