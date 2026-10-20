"""Independent consumer, correspondence and semantic-boundary regressions."""
import json
from pathlib import Path
import unittest

from gameplay_rules.activated_ability_projection import package

ROOT = Path(__file__).resolve().parents[1]
REVIEWS = ROOT / "reference-reviews"


class BoundedActivationConsumerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.records = package.load_package(REVIEWS / package.PACKAGE_NAME, review_root=REVIEWS)
        cls.rules = {r["rule_reference"]: r for r in cls.records["projection.json"]["rules"]}

    def findings(self, name):
        return self.records[name + ".json"]["findings"]

    def test_incoming_dependency_binds_original_and_new_rule_projection_anchor(self):
        direct = self.findings("consumer-reassessment")["direct_reference_reassessments"]
        self.assertEqual(len(direct), 1)
        row = direct[0]
        self.assertEqual((row["origin_reference"], row["target_reference"], row["state"]),
            ("605.3", "602.2", "DIRECT_REFERENCE_RESOLVED"))
        original = package.retained_binding()["rule_bindings"]["605.3"]
        self.assertEqual(row["origin_evidence"], original)
        target = row["target_evidence"]
        self.assertEqual(target["rule_id"], self.rules["602.2"]["rule_id"])
        self.assertEqual(target["projection_id"], self.records["projection.json"]["projection_id"])
        self.assertEqual(target["anchor_identity"], self.rules["602.2"]["source_anchor"]["anchor_id"])
        self.assertFalse(row["historical_dependency_array_rewritten"])
        self.assertFalse(row["historical_unresolved_review_modified"])
        self.assertEqual(row["semantic_closure"], "OPEN")
        self.assertEqual(row["execution_readiness"], "BLOCKED")

    def test_only_literal_references_are_direct_edges(self):
        self.assertEqual({ref: rule["direct_dependency_references"] for ref, rule in self.rules.items()},
            {"602.2": ["733"], "602.2a": ["701.20a"], "602.2b": ["601.2f"]})
        local = self.findings("local-scope")
        self.assertEqual(local["structural_relationships"], [{"parent": "602.2",
            "children": ["602.2a", "602.2b"], "kind": "STRUCTURAL_PARENT_CHILD_NOT_NUMBERED_CITATION"}])
        rows = local["outgoing_literal_references"]
        self.assertEqual([(r["target_reference"], r["state"]) for r in rows],
            [("733", "UNRESOLVED"), ("701.20a", "UNRESOLVED"), ("601.2f", "DIRECT_REFERENCE_RESOLVED")])
        self.assertNotIn("literal_outgoing_references", local)

    def test_one_range_with_eight_members_and_four_unprojected_bodies(self):
        imported = self.findings("casting-import")
        self.assertEqual(imported["range_import_count"], 1)
        rows = imported["range_members"]
        self.assertEqual([row["reference"] for row in rows], ["601.2" + c for c in "bcdefghi"])
        self.assertEqual([row["reference"] for row in rows if row["coverage"] == "PROJECTED"],
            ["601.2b", "601.2f", "601.2g", "601.2h"])
        for row in rows:
            if row["coverage"] == "UNPROJECTED":
                self.assertIsNone(row["retained_evidence"])
                self.assertEqual(row["body_authority"], "UNKNOWN_NOT_INSPECTED")
        self.assertEqual(imported["literal_direct_reference_edges_inferred_from_membership"], [])
        self.assertEqual(imported["excluded_stages"], ["601.2a"])
        self.assertFalse(imported["additional_applicability_qualifier_found"])
        self.assertFalse(imported["all_range_members_projected"])

    def test_cost_analogy_is_directional_and_preserves_action_identity(self):
        cost = self.findings("cost-analogy")
        self.assertEqual((cost["from_concept"], cost["to_concept"]),
            ("SPELL_MANA_COST", "ABILITY_ACTIVATION_COST"))
        self.assertEqual(cost["stage"], package.retained_binding()["rule_bindings"]["601.2f"])
        self.assertEqual(cost["activation_and_casting_action_identities"], "DISTINCT")
        self.assertTrue(cost["range_relationship_separate_from_literal_cost_citation"])
        for name in ("costs_calculated", "payments_performed", "card_semantics_supplied",
                     "cost_parser_supplied", "casting_or_activation_runtime_supplied"):
            self.assertFalse(cost[name])

    def test_mana_exception_and_thirteen_member_mappings_preserved(self):
        mana = self.findings("mana-relationships")
        exception = mana["qualifying_activated_mana_exception"]
        self.assertEqual(exception["no_stack_evidence"], package.retained_binding()["rule_bindings"]["605.3b"])
        self.assertFalse(exception["ordinary_stack_placement_unconditional"])
        self.assertFalse(exception["exception_supplies_complete_activation"])
        expected = {"605.1", "605.1a", "605.1b", "605.2", "605.3", "605.3a", "605.3b", "605.3c",
            "605.4", "605.4a", "605.5", "605.5a", "605.5b"}
        bindings = package.retained_binding()["rule_bindings"]
        for row in mana["preserved_complete_family_mappings"]:
            self.assertIn(row["origin"], ("601.2g", "109.4a"))
            self.assertEqual(row["state"], "SECTION_REFERENCE_RESOLVED_BY_COMPLETE_FAMILY")
            self.assertEqual(row["concrete_family_count"], 13)
            self.assertEqual({r["rule_id"] for r in row["concrete_family_bindings"]},
                {bindings[ref]["rule_id"] for ref in expected})
            self.assertFalse(row["synthetic_605_rule_created"])

    def test_triggered_overlap_and_priority_scope_do_not_invent_citations(self):
        mana = self.findings("mana-relationships")
        overlap = next(row for row in mana["preserved_relationships"] if row.get("origin") == "605.4a")
        self.assertEqual(overlap["kind"], "SEMANTIC_OVERLAP_WITHOUT_DIRECT_CR_CITATION")
        self.assertFalse(overlap["direct_edge_created"])
        priority = mana["priority_return"]
        self.assertEqual(priority["condition"], "PLAYER_HELD_PRIORITY_IMMEDIATELY_BEFORE_MANA_ABILITY_ACTIVATION")
        self.assertEqual(priority["post_resolution_context"], "SAME_PLAYER_RECEIVES_PRIORITY")
        self.assertFalse(priority["every_mana_activation_grants_priority"])
        self.assertFalse(priority["triggered_priority_return_inferred"])
        self.assertFalse(mana["additional_effect_context"]["finer_ordering_inferred"])
        self.assertEqual(mana["parent_405.6"], "UNPROJECTED_SCOPE_NOT_REOPENED")
        self.assertFalse(mana["direct_117_citation_invented"])

    def test_consumers_keep_indirect_routes_and_controller_frontier(self):
        consumers = self.findings("consumer-reassessment")
        rows = {row["consumer"]: row for row in consumers["rows"]}
        for name in ("601.2g", "bounded_casting", "madness"):
            self.assertEqual(rows[name]["source_coverage_state"], "IMPROVED_INDIRECTLY")
            self.assertEqual(rows[name]["new_direct_edges"], [])
        self.assertEqual(rows["madness"]["route"], ["702.35b", "bounded_casting", "601.2g", "605"])
        self.assertFalse(consumers["controller_109.4a_requires_actual_stack_presence"])
        self.assertFalse(consumers["controller_109.4a_closed_by_602.2a"])
        frontier = consumers["shared_triggered_subsystem_outside_scope"]["preserved_frontiers"]
        self.assertEqual([(r["origin"], r["targets"]) for r in frontier],
            [("605.4", ["603"]), ("109.4b", ["603", "603.7d", "603.7e", "603.7f"])])

    def test_all_ten_responsibilities_remain_open_execution_blocked(self):
        rows = self.findings("procedure-responsibilities")["rows"]
        self.assertEqual(len(rows), 10)
        for row in rows:
            self.assertEqual(row["state"], "OPEN / EXECUTION_BLOCKED")
            self.assertEqual(row["semantic_closure"], "OPEN")
            self.assertEqual(row["execution_readiness"], "BLOCKED")
            self.assertFalse(row["implementation_available"])

    def test_composite_adds_only_three_to_nine_immutable_projections(self):
        coverage = package.composite_view(self.records)
        self.assertEqual(coverage["projection_component_counts"], [20, 12, 7, 12, 12, 5, 13, 3, 1, 3])
        components = coverage["projection_components"]
        self.assertEqual(len({r["projection_id"] for r in components}), 10)
        refs = coverage["projected_references"]
        self.assertEqual(len(refs), len(set(refs)))
        self.assertEqual(len(refs), 88)
        self.assertEqual(set(refs) - set(package.retained_binding()["rule_bindings"]), set(self.rules))
        self.assertEqual(components[-1]["package_id"], package.manifest(self.records)["package_id"])
        for excluded in ("602", "602.3", "601.2a", "601.2c", "601.2d", "601.2e", "601.2i", "733", "701.20a", "605"):
            self.assertNotIn(excluded, refs)

    def test_historical_design_authority_is_retained_and_new_anchors_are_separate(self):
        history = json.loads((REVIEWS / "gameplay-rules-activated-ability-procedure-design" / "source-correspondence.json").read_text())
        self.assertFalse(history["projection_authorized"])
        self.assertEqual(history["new_source_units_projected"], 0)
        findings = self.findings("design-source-correspondence")
        self.assertEqual(findings["historical_fingerprint_authority"], "REVIEW_ONLY_NOT_PROJECTED")
        self.assertFalse(findings["historical_authority_upgraded"])
        self.assertEqual(len(findings["merged_design_review_bindings"]), 7)
        self.assertEqual({r["anchor_identity"] for r in findings["fresh_projected_evidence"]},
            {r["source_anchor"]["anchor_id"] for r in self.rules.values()})

    def test_next_scope_review_has_zero_source_authority_and_no_runtime(self):
        ready = self.findings("overall-readiness")
        self.assertEqual(ready["real_profile"], "DESIGN_ONLY / NOT EXECUTABLE")
        self.assertEqual(ready["readiness_code"], "REAL_EXECUTION_PROFILE_NOT_READY")
        self.assertFalse(ready["real_snapshot_created"])
        self.assertFalse(ready["admission_eligible"])
        self.assertEqual(ready["source_policy_clearance"], "not_granted")
        self.assertEqual(set(ready["permissions"].values()), {"NOT_ESTABLISHED"})
        next_scope = ready["next_milestone"]
        self.assertEqual(next_scope["milestone"], "Shared Casting-Stage Gap Scope Design")
        self.assertEqual(next_scope["expected_new_source_units"], 0)
        self.assertEqual(next_scope["future_projection_allowlist"], [])
        for key in ("future_milestone_authorized", "future_source_projection_authorized", "future_milestone_begun"):
            self.assertFalse(next_scope[key])


if __name__ == "__main__":
    unittest.main()
