"""Source coverage, literal recovery and structural provenance stay distinct."""
from copy import deepcopy
import json
from pathlib import Path
import unittest

from gameplay_rules.errors import GameplayContractError
from gameplay_rules.shared_proposal_legality import package

ROOT = Path(__file__).resolve().parents[1]
REVIEWS = ROOT / "reference-reviews"


def reseal(record):
    record["review_id"] = package._identity(package.RECORD_DOMAIN,
        {key: value for key, value in record.items() if key != "review_id"})


class SharedProposalLegalityReviewTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.records = package.load_package(REVIEWS / package.PACKAGE_NAME, review_root=REVIEWS)

    def test_current_parent_assessment_is_structural_without_a_literal_e_citation(self):
        parent = package.current_view(self.records)["records"]["casting-parent-reassessment.json"]["findings"]
        self.assertEqual(parent["origin_reference"], "601.2")
        self.assertEqual(parent["target_reference"], "601.2e")
        self.assertEqual(parent["relationship"], "STRUCTURAL_SIBLING_WITHOUT_RETAINED_PARENT_DIRECT_CITATION")
        self.assertEqual(parent["state"], "STRUCTURAL_SIBLING_SOURCE_COVERAGE_PROJECTED")
        self.assertIs(parent["retained_parent_literal_direct_citation_to_e"], False)
        self.assertIs(parent["parent_to_e_direct_reference_resolved"], False)
        self.assertIs(parent["proposal_range_expanded"], False)
        self.assertEqual(parent["source_provenance"]["explicit_proposal_range"], ["601.2a", "601.2d"])
        self.assertEqual(parent["source_provenance"]["explicit_cost_range"], ["601.2f", "601.2h"])
        self.assertEqual(parent["proposal_range_members"], ["601.2a", "601.2b", "601.2c", "601.2d"])
        self.assertEqual(parent["projected_proposal_members"], ["601.2b", "601.2c", "601.2d"])
        self.assertEqual(parent["unprojected_proposal_members"], ["601.2a"])
        self.assertIs(parent["proposal_range_complete"], False)
        self.assertIs(parent["parent_procedure_complete"], False)
        e = self.records["projection.json"]["rules"][0]
        evidence = parent["target_evidence"]
        self.assertEqual(evidence["rule_id"], e["rule_id"])
        self.assertEqual(evidence["projection_id"], self.records["projection.json"]["projection_id"])
        self.assertEqual(evidence["anchor_identity"], e["source_anchor"]["anchor_id"])
        self.assertEqual(evidence["package_id"], package.manifest(self.records)["package_id"])
        retained = json.loads((REVIEWS / "gameplay-rules-bounded-casting-projection" / "projection.json").read_bytes())
        casting = next(row for row in retained["rules"] if row["rule_reference"] == "601.2")
        self.assertNotIn("601.2e", casting["direct_dependency_references"])
        self.assertEqual(casting["semantic_distinctions"]["explicit_proposal_stage_references"], parent["proposal_range_members"])
        self.assertEqual(casting["semantic_distinctions"]["explicit_cost_stage_references"], ["601.2f", "601.2g", "601.2h"])
        self.assertIn("601.3", casting["direct_dependency_references"])
        self.assertIn("733", casting["direct_dependency_references"])

    def test_rehashed_parent_direct_resolution_or_range_expansion_is_rejected(self):
        for mutation in (
                lambda value: value.update(state="DIRECT_REFERENCE_RESOLVED"),
                lambda value: value.update(relationship="NORMALIZED_MEMBER_OF_EXPLICIT_PROPOSAL_RANGE"),
                lambda value: value["proposal_range_members"].append("601.2e"),
                lambda value: value["projected_proposal_members"].append("601.2e"),
                lambda value: value["target_evidence"].update(rule_id="sha256:" + "0" * 64)):
            records = deepcopy(self.records)
            record = records["casting-parent-reassessment.json"]
            mutation(record["findings"])
            reseal(record)
            with self.subTest(mutation=mutation), self.assertRaises(GameplayContractError):
                package.validate_records(records)

    def test_one_import_retains_eight_rows_and_actual_historical_bindings(self):
        current = package.current_view(self.records)
        imported = current["records"]["activated-import-reassessment.json"]["findings"]
        self.assertEqual(imported["relationship_kind"], "ONE_RANGE_IMPORT_WITH_EIGHT_MEMBER_ROWS")
        self.assertEqual(imported["range_import_count"], 1)
        self.assertEqual(imported["member_count"], 8)
        self.assertEqual(imported["member_coverage"], "7/8")
        self.assertEqual(imported["projected_member_count_before"], 6)
        self.assertEqual(imported["projected_member_count_after"], 7)
        self.assertEqual(imported["projected_members"], ["601.2b", "601.2c", "601.2d", "601.2e", "601.2f", "601.2g", "601.2h"])
        self.assertEqual(imported["unprojected_members"], ["601.2i"])
        self.assertEqual(imported["excluded_stages"], ["601.2a"])
        self.assertEqual(imported["literal_direct_reference_edges_inferred_from_membership"], [])
        self.assertFalse(imported["all_range_members_projected"])
        self.assertFalse(imported["casting_and_activation_interchangeable"])
        prior = package.retained_binding()["rule_bindings"]
        self.assertEqual([row["reference"] for row in imported["range_members"]], ["601.2" + suffix for suffix in "bcdefghi"])
        for row in imported["range_members"]:
            reference = row["reference"]
            if reference == "601.2i":
                self.assertEqual(row["coverage"], "UNPROJECTED")
                self.assertIsNone(row["projected_evidence"])
                continue
            self.assertEqual(row["coverage"], "PROJECTED")
            evidence = row["projected_evidence"]
            if reference == "601.2e":
                self.assertEqual(evidence["package_id"], current["package_id"])
                self.assertEqual(evidence["projection_id"], self.records["projection.json"]["projection_id"])
                self.assertEqual(evidence["rule_id"], self.records["projection.json"]["rules"][0]["rule_id"])
            else:
                self.assertEqual(evidence, {"rule_reference": reference, **prior[reference]})
        analogy = imported["separate_cost_analogy"]
        self.assertEqual((analogy["origin"], analogy["target"], analogy["state"]), ("602.2b", "601.2f", "DIRECT_REFERENCE_RESOLVED"))

    def test_thirteen_projections_admit_exactly_one_new_real_source_unit(self):
        value = package.composite_view(self.records)
        components = value["projection_components"]
        references = [reference for component in components for reference in component["projected_references"]]
        prior = package.retained_binding()["rule_bindings"]
        self.assertEqual(len(components), 13)
        self.assertEqual(len({component["projection_id"] for component in components}), 13)
        self.assertEqual(len(references), 91)
        self.assertEqual(len(set(references)), 91)
        self.assertEqual(len(prior), 90)
        self.assertEqual(set(references) - set(prior), {"601.2e"})
        self.assertNotIn("733", references)
        self.assertEqual(components[-1]["package_id"], package.manifest(self.records)["package_id"])

    def test_fresh_correspondence_keeps_the_historical_observation_distinct(self):
        value = self.records["design-source-correspondence.json"]["findings"]
        observation = value["historical_observation"]
        self.assertEqual(observation["reference"], "601.2e")
        self.assertEqual(observation["authority"], "RETAINED_PR201_REVIEW_ONLY_SOURCE_OBSERVATION")
        self.assertEqual(observation["historical_coverage"], "UNPROJECTED")
        self.assertIs(observation["historical_registered_projected_source_anchor"], False)
        self.assertIs(observation["historical_record_modified"], False)
        self.assertEqual(value["fresh_authority"], "OWNER_AUTHORIZED_E_ONLY_COMPLETE_UNIT_SOURCE_VERIFICATION")
        self.assertEqual(value["complete_unit"]["physical_lines"], [2472, 2472])
        self.assertEqual(value["complete_unit"]["original_byte_interval"], [298690, 298921])
        self.assertEqual(value["complete_unit"]["owned_example_lines"], 0)
        self.assertEqual(value["literal_outgoing_numbered_citations"], ["733"])
        self.assertEqual(value["literal_outgoing_ranges"], [])
        self.assertIs(value["historical_d_following_e_body_uninspected_statement_changed"], False)
        self.assertIs(value["offline_metadata_is_fresh_source_reproduction"], False)

    def test_recovery_is_one_unresolved_literal_dependency_with_distinct_casting_context(self):
        value = self.records["recovery-dependency.json"]["findings"]
        self.assertEqual((value["origin_reference"], value["target_reference"], value["relationship"]),
            ("601.2e", "733", "DIRECT_NUMBERED_REFERENCE"))
        self.assertEqual(value["state"], "UNRESOLVED")
        self.assertEqual(value["target_source_coverage"], "UNPROJECTED")
        self.assertEqual(value["semantic_recovery_closure"], "OPEN")
        self.assertEqual(value["recovery_execution"], "BLOCKED")
        self.assertEqual(value["target_node"], {"reference": "733", "classification": "UNRESOLVED_RULE",
            "status": "UNRESOLVED", "coverage_state": "UNPROJECTED"})
        for field in ("target_body_inspected", "target_projected", "state_restoration_supported", "additional_consumer_resolves_recovery"):
            self.assertIs(value[field], False)
        self.assertEqual(value["separate_pre_activation_recovery_context"],
            {"origin": "602.2", "context_interchangeable_with_e": False})
        self.assertEqual(value["source_prescribed_conditional_consequence"], self.records["projection.json"]["rules"][0]["findings"]["conditional_failure"])
        self.assertEqual([(row["origin"], row["target"], row["state"]) for row in value["preserved_dependencies"]],
            [("601.2", "733", "UNRESOLVED"), ("602.2", "733", "UNRESOLVED"), ("602.2a", "701.20a", "UNRESOLVED")])
        self.assertTrue(all(row["target_source_coverage"] == "UNPROJECTED" for row in value["preserved_dependencies"]))

    def test_recovery_resolution_fabricated_identity_and_conditional_rewrites_are_rejected(self):
        for mutation in (
                lambda value: value.update(state="DIRECT_REFERENCE_RESOLVED"),
                lambda value: value.update(target_source_coverage="PROJECTED"),
                lambda value: value.update(semantic_recovery_closure="CLOSED"),
                lambda value: value.update(recovery_execution="READY"),
                lambda value: value["target_node"].update(rule_id="sha256:" + "0" * 64),
                lambda value: value["target_node"].update(source_anchor={}),
                lambda value: value["source_prescribed_conditional_consequence"].update(state_restoration_supported=True),
                lambda value: value["preserved_dependencies"][0].update(state="DIRECT_REFERENCE_RESOLVED")):
            records = deepcopy(self.records)
            record = records["recovery-dependency.json"]
            mutation(record["findings"])
            reseal(record)
            with self.subTest(mutation=mutation), self.assertRaises(GameplayContractError):
                package.validate_records(records)

    def test_retained_consumers_and_e_only_findings_have_explicit_provenance(self):
        value = self.records["consumer-semantic-boundaries.json"]["findings"]
        self.assertTrue(all(row["literal_citation_from_e"] is False for row in value["context_relationships"]))
        self.assertEqual(value["proposal_checkpoint"]["checkpoint"]["actual_legality"], "UNKNOWN_OR_UNSUPPORTED")
        self.assertIs(value["proposal_checkpoint"]["casting_provenance"]["unrestricted_activated_ability_legality_rule_inferred"], False)
        self.assertEqual(value["madness"]["kind"], "INDIRECT_CONSUMER")
        self.assertIs(value["madness"]["new_direct_e_citation"], False)
        self.assertEqual([(row["origin"], row["target"], row["state"]) for row in value["preserved_relationships"]],
            [("605.3", "602.2", "DIRECT_REFERENCE_RESOLVED"), ("601.2", "733", "UNRESOLVED"),
             ("602.2", "733", "UNRESOLVED"), ("602.2a", "701.20a", "UNRESOLVED")])
        self.assertEqual(value["preserved_relationships"][0]["assessment_level"], "SOURCE_COVERAGE_ONLY")
        self.assertIs(value["target_concepts"]["zero_count_establishes_mana_ability_eligibility"], False)
        self.assertIs(value["mana_distinctions"]["complete_605_family_source_coverage_establishes_semantic_closure"], False)
        self.assertEqual(value["mana_distinctions"]["priority_condition"], "PRIORITY_IMMEDIATELY_BEFORE_ACTIVATION")
        self.assertTrue(value["knowledge_does_not_establish_legality_casting_activation_or_recovery_completion"])

    def test_readiness_and_permissions_remain_blocked(self):
        readiness = self.records["preservation-readiness.json"]["findings"]
        semantic = self.records["consumer-semantic-boundaries.json"]["findings"]
        self.assertEqual(len(semantic["activated_responsibilities"]), 10)
        for responsibility in semantic["activated_responsibilities"]:
            self.assertEqual(responsibility["state"], "OPEN / EXECUTION_BLOCKED")
            self.assertIs(responsibility["implementation_available"], False)
        self.assertEqual(readiness["execution_readiness"], "BLOCKED")
        for field in ("runtime_implemented", "real_snapshot_created", "real_execution_profile_activated", "admission_eligible"):
            self.assertIs(readiness[field], False)
        self.assertEqual(readiness["source_policy_clearance"], "not_granted")
        self.assertEqual(set(readiness["permissions"].values()), {"NOT_ESTABLISHED"})
        self.assertEqual(semantic["madness"]["kind"], "INDIRECT_CONSUMER")

    def test_only_one_subsequent_recommendation_is_unauthorized_and_unbegun(self):
        value = self.records["subsequent-recommendation.json"]["findings"]
        self.assertEqual(value["recommendation_count"], 1)
        self.assertEqual(value["fresh_additional_body_inspection"], [])
        recommendation = value["recommendation"]
        self.assertEqual(recommendation["kind"], "REVIEW_ONLY_RETAINED_EVIDENCE_DESIGN")
        self.assertEqual(recommendation["proposed_allowlist"], [])
        self.assertEqual(recommendation["expected_added_source_units"], 0)
        self.assertIs(recommendation["requires_separate_owner_authorization"], True)
        for field in ("future_milestone_authorized", "future_source_projection_authorized", "future_milestone_begun"):
            self.assertIs(recommendation[field], False)
