"""Immutable single-unit identities and semantic boundaries without the TXT."""
from copy import deepcopy
import json
import unittest

from evidence.contracts import sha256_identity
from gameplay_rules.errors import GameplayContractError
from gameplay_rules.projection.contracts import _json
from gameplay_rules.shared_target_allocation.contracts import (
    BoundedSharedTargetAllocationProjection as Projection, create_projection, rule_identity,
)
from gameplay_rules.shared_target_allocation.source import VERIFIED_ANCHORS, anchor_identity


def reseal(value, domain=None):
    value["projection_id"] = "sha256:" + sha256_identity({"domain": domain or Projection.SCHEMA,
        "content": {key: item for key, item in value.items() if key != "projection_id"}})
    return value


class SharedTargetAllocationContractTests(unittest.TestCase):
    def setUp(self):
        self.projection = create_projection(VERIFIED_ANCHORS)

    def test_canonical_roundtrip_and_immutable_copy(self):
        raw = self.projection.serialize().encode("utf-8")
        restored = Projection.from_json(raw)
        self.assertEqual(restored.serialize().encode("utf-8"), raw)
        self.assertEqual(restored.verify().identity, self.projection.identity)
        with self.assertRaises(TypeError):
            restored.rules[0]["execution_ready"] = True
        copied = restored.to_dict()
        copied["rules"][0]["findings"]["conditional_allocation_declaration"]["minimum_applies_only_within_required_distribution"] = False
        self.assertTrue(restored.rules[0]["findings"]["conditional_allocation_declaration"]["minimum_applies_only_within_required_distribution"])

    def test_wrong_projection_rule_and_anchor_own_ids_fail(self):
        for field in ("projection_id", "rule_id", "anchor_id"):
            value = self.projection.to_dict()
            if field == "projection_id":
                value[field] = value["rules"][0]["rule_id"]
            elif field == "rule_id":
                value["rules"][0][field] = value["rules"][0]["source_anchor"]["anchor_id"]
                reseal(value)
            else:
                value["rules"][0]["source_anchor"][field] = value["rules"][0]["rule_id"]
                value["rules"][0]["rule_id"] = rule_identity(value["rules"][0])
                reseal(value)
            with self.subTest(field=field), self.assertRaises(GameplayContractError):
                Projection.from_dict(value)

    def test_wrong_identity_domain_cannot_authorize_projection(self):
        value = self.projection.to_dict()
        with self.assertRaises(GameplayContractError):
            Projection.from_dict(reseal(value, "gameplay-cr-bounded-activated-ability-projection-v1"))

    def test_coherently_rehashed_altered_knowledge_is_rejected(self):
        value = self.projection.to_dict()
        value["rules"][0]["findings"]["conditional_allocation_declaration"]["each_relevant_target_minimum"] = 0
        value["rules"][0]["rule_id"] = rule_identity(value["rules"][0])
        with self.assertRaises(GameplayContractError):
            Projection.from_dict(reseal(value))

    def test_numeric_counts_reject_boolean_and_float_replacements(self):
        for field in ("selected_rule_count", "new_source_units_projected", "total_projected_rule_count", "resulting_projection_count"):
            for replacement in (True, False, float(self.projection.to_dict()[field])):
                value = self.projection.to_dict()
                value[field] = replacement
                with self.subTest(field=field, replacement=replacement), self.assertRaises(GameplayContractError):
                    Projection.from_dict(reseal(value))

    def test_nested_boolean_replacements_fail_after_rule_and_projection_rehash(self):
        for replacement in (0, 0.0, 1, 1.0):
            value = self.projection.to_dict()
            value["rules"][0]["findings"]["conditional_allocation_declaration"]["minimum_applies_to_all_targets_of_all_spells_or_abilities"] = replacement
            value["rules"][0]["rule_id"] = rule_identity(value["rules"][0])
            with self.subTest(replacement=replacement), self.assertRaises(GameplayContractError):
                Projection.from_dict(reseal(value))

    def test_complete_unit_truncation_fails_after_all_own_identities_rehashed(self):
        value = self.projection.to_dict()
        anchor = value["rules"][0]["source_anchor"]
        anchor.update(byte_end=298685, span_length=241)
        anchor["anchor_id"] = anchor_identity(anchor)
        value["rules"][0]["rule_id"] = rule_identity(value["rules"][0])
        with self.assertRaises(GameplayContractError):
            Projection.from_dict(reseal(value))

    def test_wrong_scope_rule_count_missing_and_extra_fields_fail(self):
        for mutate in (
            lambda value: value.pop("boundary_flags"),
            lambda value: value.update(unapproved_field=True),
            lambda value: value["rules"].append(deepcopy(value["rules"][0])),
            lambda value: value["rules"][0].update(rule_reference="601.2c"),
            lambda value: value.update(selected_references=["601.2d", "601.2c"]),
        ):
            value = self.projection.to_dict()
            mutate(value)
            with self.assertRaises(GameplayContractError):
                Projection.from_dict(reseal(value))

    def test_plain_json_types_required_before_coercion(self):
        class IntegerSubclass(int):
            pass

        for replacement in (IntegerSubclass(1), ("601.2d",), {"unexpected"}):
            value = self.projection.to_dict()
            field = "selected_rule_count" if isinstance(replacement, int) else "selected_references"
            value[field] = replacement
            with self.subTest(kind=type(replacement)), self.assertRaises(GameplayContractError):
                Projection.from_dict(value)
        for value in (None, [], True, 1, 1.0):
            with self.subTest(kind=type(value)), self.assertRaises(GameplayContractError):
                rule_identity(value)
        with self.assertRaises(GameplayContractError):
            create_projection(tuple(_json(VERIFIED_ANCHORS)))

    def test_noncanonical_duplicate_nonfinite_and_invalid_json_structures_fail(self):
        canonical = self.projection.serialize()
        for raw in (
            canonical + "\n", " " + canonical, json.dumps(self.projection.to_dict(), indent=2),
            canonical.replace('"selected_rule_count":1', '"selected_rule_count":1,"selected_rule_count":1'),
            canonical.replace('"selected_rule_count":1', '"selected_rule_count":NaN'),
            "[]", "null", "true", b"\xff", None, True,
        ):
            with self.subTest(kind=type(raw)), self.assertRaises(GameplayContractError):
                Projection.from_json(raw)

    def test_conditional_minimum_and_recipient_scope_are_exact_and_descriptive(self):
        findings = self.projection.to_dict()["rules"][0]["findings"]
        allocation = findings["conditional_allocation_declaration"]
        self.assertEqual(allocation["condition"], "SPELL_REQUIRES_PLAYER_TO_DIVIDE_OR_DISTRIBUTE_AN_EFFECT_AMONG_ONE_OR_MORE_TARGETS")
        self.assertEqual(allocation["distribution_operations"], ["DIVIDE", "DISTRIBUTE"])
        self.assertEqual(allocation["distributed_subject"], "AN_EFFECT")
        self.assertEqual(allocation["illustrative_effect_kinds"], ["DAMAGE", "COUNTERS"])
        self.assertFalse(allocation["illustrations_exhaust_effect_kinds"])
        self.assertEqual(allocation["declaration"], "PLAYER_ANNOUNCES_THE_DIVISION")
        self.assertEqual(allocation["recipient_scope"], "THE_ONE_OR_MORE_TARGETS_OF_THAT_REQUIRED_DISTRIBUTION")
        self.assertEqual(allocation["minimum_recipient_count"], 1)
        self.assertEqual(allocation["each_relevant_target_minimum"], 1)
        self.assertEqual(allocation["minimum_unit"], "WHATEVER_IS_BEING_DIVIDED")
        self.assertTrue(allocation["minimum_applies_only_within_required_distribution"])
        self.assertFalse(allocation["minimum_applies_to_all_targets_of_all_spells_or_abilities"])
        self.assertFalse(allocation["arithmetic_or_allocation_solver_implemented"])
        self.assertFalse(findings["recipient_declaration_distinction"]["recipient_declaration_is_allocation_declaration"])
        self.assertEqual(findings["recipient_declaration_distinction"]["retained_recipient_declaration"], "601.2c")
        self.assertFalse(findings["casting_provenance"]["procedures_interchangeable"])
        self.assertEqual(findings["casting_provenance"]["actor"], "CASTING_PLAYER")
        self.assertEqual(findings["casting_provenance"]["activated_ability_relevance"], "RETAINED_602_2B_CASTING_STAGE_RANGE_IMPORT")
        self.assertEqual(set(findings["unknown_inputs"].values()), {"UNKNOWN"})

    def test_numeric_minimum_rejects_boolean_float_or_other_integer_after_rehash(self):
        for field in ("minimum_recipient_count", "each_relevant_target_minimum"):
            for replacement in (True, False, 1.0, 0, 2, "1"):
                value = self.projection.to_dict()
                value["rules"][0]["findings"]["conditional_allocation_declaration"][field] = replacement
                value["rules"][0]["rule_id"] = rule_identity(value["rules"][0])
                with self.subTest(field=field, replacement=replacement), self.assertRaises(GameplayContractError):
                    Projection.from_dict(reseal(value))

    def test_no_execution_capability_or_permission_is_created(self):
        value = self.projection.to_dict()
        self.assertEqual(value["rules"][0]["runtime_operations_implemented"], [])
        self.assertEqual(value["rules"][0]["execution_readiness"], "BLOCKED")
        self.assertEqual(value["rules"][0]["semantic_closure"], "OPEN")
        self.assertFalse(value["boundary_flags"]["real_snapshot_created"])
        self.assertFalse(value["boundary_flags"]["real_profile_activated"])
        self.assertEqual(value["authorization"]["scope"], "BOUNDED SHARED TARGET-ALLOCATION STAGE PROJECTION")
        self.assertFalse(value["authorization"]["subsequent_milestone_authorized"])

    def test_no_literal_outgoing_citations_and_exact_single_unit_coverage(self):
        value = self.projection.to_dict()
        self.assertEqual(value["rules"][0]["direct_dependency_references"], [])
        self.assertEqual(value["rules"][0]["outgoing_numbered_ranges"], [])
        self.assertEqual(value["graph"]["edges"], [])
        self.assertEqual(value["selected_references"], ["601.2d"])
        self.assertEqual(value["new_source_units_projected"], 1)
        self.assertEqual(value["total_projected_rule_count"], 90)
        self.assertEqual(value["resulting_projection_count"], 12)


if __name__ == "__main__":
    unittest.main()
