"""Meaningful current coverage and source/semantic provenance regressions."""
from pathlib import Path
import unittest

from gameplay_rules.shared_target_declaration import package

ROOT = Path(__file__).resolve().parents[1]


class SharedTargetDeclarationReviewTests(unittest.TestCase):
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
        self.assertFalse(value["source_provenance"]["parent_individually_enumerates_c"])
        self.assertEqual(value["projected_proposal_members"], ["601.2b", "601.2c"])
        self.assertEqual(value["unprojected_proposal_members"], ["601.2a", "601.2d"])
        self.assertFalse(value["parent_procedure_complete"])

    def test_single_import_has_eight_members_and_actual_c_identity_binding(self):
        value = package.current_view(self.records)
        row = value["records"]["activated-import-reassessment.json"]["findings"]
        self.assertEqual(row["range_import_count"], 1)
        self.assertEqual(len(row["range_members"]), 8)
        self.assertEqual(row["projected_members"], ["601.2b", "601.2c", "601.2f", "601.2g", "601.2h"])
        self.assertEqual(row["unprojected_members"], ["601.2d", "601.2e", "601.2i"])
        self.assertEqual(row["member_coverage"], "5/8")
        self.assertEqual(row["excluded_stages"], ["601.2a"])
        self.assertEqual(row["literal_direct_reference_edges_inferred_from_membership"], [])
        self.assertFalse(row["additional_applicability_qualifier_found"])
        c = row["range_members"][1]["projected_evidence"]
        projection = self.records["projection.json"]
        self.assertEqual(c["package_id"], value["package_id"])
        self.assertEqual(c["projection_id"], projection["projection_id"])
        self.assertEqual(c["rule_id"], projection["rules"][0]["rule_id"])
        self.assertEqual(c["anchor_identity"], projection["rules"][0]["source_anchor"]["anchor_id"])
        self.assertEqual(c["source_anchor"], projection["rules"][0]["source_anchor"])

    def test_eleven_distinct_projections_admit_exactly_one_new_unit(self):
        value = package.composite_view(self.records)
        components = value["projection_components"]
        references = [reference for item in components for reference in item["projected_references"]]
        prior = package.retained_binding()["rule_bindings"]
        self.assertEqual(len(components), 11)
        self.assertEqual(len({item["projection_id"] for item in components}), 11)
        self.assertEqual(len(references), 89)
        self.assertEqual(len(set(references)), 89)
        self.assertEqual(set(references) - set(prior), {"601.2c"})
        self.assertEqual(len(prior), 88)
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
        self.assertTrue(all(row["literal_citation_from_c"] is False for row in value["context_relationships"]))
        self.assertEqual(value["madness"]["kind"], "INDIRECT_CONSUMER")
        self.assertFalse(value["madness"]["new_direct_c_citation"])
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
        self.assertEqual(recommendation["proposed_allowlist"], ["601.2d"])
        self.assertEqual(recommendation["expected_added_source_units"], 1)
        self.assertEqual(recommendation["conditional_resulting_units"], 90)
        self.assertEqual(recommendation["conditional_resulting_projections"], 12)
        self.assertEqual(recommendation["conditional_activated_import_coverage"], "6/8")
        self.assertEqual(value["fresh_additional_body_inspection"], [])
        for field in ("future_milestone_authorized", "future_source_projection_authorized", "future_milestone_begun"):
            self.assertIs(recommendation[field], False)
        self.assertTrue({"601.2e", "601.2i", "701.20a", "733", "603", "runtime"}.issubset(recommendation["explicit_exclusions"]))
