"""Immutable single-unit identities and semantic boundaries without the TXT."""
from copy import deepcopy
import json
import unittest

from evidence.contracts import sha256_identity
from gameplay_rules.errors import GameplayContractError
from gameplay_rules.projection.contracts import _json
from gameplay_rules.shared_proposal_legality.contracts import (
    BoundedSharedProposalLegalityProjection as Projection, create_projection, rule_identity,
)
from gameplay_rules.shared_proposal_legality.source import VERIFIED_ANCHORS, anchor_identity


def reseal(value, domain=None):
    value["projection_id"] = "sha256:" + sha256_identity({"domain": domain or Projection.SCHEMA,
        "content": {key: item for key, item in value.items() if key != "projection_id"}})
    return value


class SharedProposalLegalityContractTests(unittest.TestCase):
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
        copied["rules"][0]["execution_ready"] = True
        self.assertFalse(restored.rules[0]["execution_ready"])

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
        value["rules"][0]["findings"]["unauthorized_injected_claim"] = True
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
            value["rules"][0]["execution_ready"] = replacement
            value["rules"][0]["rule_id"] = rule_identity(value["rules"][0])
            with self.subTest(replacement=replacement), self.assertRaises(GameplayContractError):
                Projection.from_dict(reseal(value))

    def test_complete_unit_truncation_fails_after_all_own_identities_rehashed(self):
        value = self.projection.to_dict()
        anchor = value["rules"][0]["source_anchor"]
        anchor.update(byte_end=298920, span_length=230)
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
            lambda value: value.update(selected_references=["601.2e", "601.2d"]),
        ):
            value = self.projection.to_dict()
            mutate(value)
            with self.assertRaises(GameplayContractError):
                Projection.from_dict(reseal(value))

    def test_plain_json_types_required_before_coercion(self):
        class IntegerSubclass(int):
            pass

        for replacement in (IntegerSubclass(1), ("601.2e",), {"unexpected"}):
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

    def test_no_execution_capability_or_permission_is_created(self):
        value = self.projection.to_dict()
        rule = value["rules"][0]
        self.assertEqual(rule["runtime_operations_implemented"], [])
        self.assertEqual(rule["execution_readiness"], "BLOCKED")
        self.assertEqual(rule["semantic_closure"], "OPEN")
        self.assertFalse(value["boundary_flags"]["real_snapshot_created"])
        self.assertFalse(value["boundary_flags"]["real_profile_activated"])
        self.assertEqual(value["authorization"]["scope"], "BOUNDED SHARED PROPOSAL-LEGALITY CHECKPOINT PROJECTION")
        self.assertFalse(value["authorization"]["subsequent_milestone_authorized"])

    def test_checkpoint_actor_object_conditional_consequence_and_unknowns_are_separate(self):
        findings = self.projection.to_dict()["rules"][0]["findings"]
        checkpoint = findings["checkpoint"]
        self.assertEqual(checkpoint["actor_or_mechanism"], "THE_GAME")
        self.assertEqual(checkpoint["checked_object"], "PROPOSED_SPELL")
        self.assertEqual(checkpoint["question"], "WHETHER_THE_PROPOSED_SPELL_CAN_LEGALLY_BE_CAST")
        self.assertIs(checkpoint["criteria_supplied"], False)
        self.assertEqual(checkpoint["actual_legality"], "UNKNOWN_OR_UNSUPPORTED")
        self.assertIs(checkpoint["absence_of_detected_violation_proves_legality"], False)
        failure = findings["conditional_failure"]
        self.assertEqual(failure["condition"], "PROPOSED_SPELL_IS_ILLEGAL")
        self.assertEqual(failure["source_prescribed_consequence"], "GAME_RETURNS_TO_BEFORE_THAT_SPELLS_CASTING_WAS_PROPOSED")
        self.assertEqual(failure["return_point"], "MOMENT_BEFORE_CASTING_OF_THAT_SPELL_WAS_PROPOSED")
        self.assertEqual(failure["literal_recovery_reference"], "733")
        self.assertEqual(failure["recovery_mechanics"], "UNRESOLVED")
        self.assertEqual(failure["recovery_execution"], "BLOCKED")
        self.assertIs(failure["state_restoration_supported"], False)
        self.assertIs(failure["pre_activation_recovery_context_interchangeable"], False)
        self.assertEqual(findings["unknown_inputs"], {"legality_criteria": "UNKNOWN_OR_UNSUPPORTED",
            "Card_or_effect_information": "UNKNOWN", "applicable_game_state": "UNKNOWN",
            "execution_machinery": "UNIMPLEMENTED"})

    def test_no_express_positive_branch_or_contextual_success_is_invented(self):
        findings = self.projection.to_dict()["rules"][0]["findings"]
        self.assertEqual(findings["legal_outcome_branch"], {"expressly_stated": False,
            "positive_literal_e_to_f_reference": False, "successful_continuation_guaranteed": False})
        context = findings["procedure_context"]
        self.assertEqual(context["authority"], "RETAINED_STRUCTURAL_CONTEXT_ONLY")
        self.assertEqual(context["declarations"], ["601.2c", "601.2d"])
        self.assertEqual(context["later_cost_stage"], "601.2f")
        self.assertEqual(context["literal_outgoing_context_citations"], [])
        self.assertIs(context["procedure_order_establishes_legality"], False)
        self.assertEqual(findings["casting_provenance"]["activated_ability_relevance"], "RETAINED_602_2B_CASTING_STAGE_RANGE_IMPORT")
        self.assertIs(findings["casting_provenance"]["unrestricted_activated_ability_legality_rule_inferred"], False)

    def test_literal_recovery_dependency_adds_no_second_source_unit(self):
        value = self.projection.to_dict()
        rule = value["rules"][0]
        self.assertEqual(rule["rule_reference"], "601.2e")
        self.assertEqual(rule["direct_dependency_references"], ["733"])
        self.assertEqual(rule["outgoing_numbered_ranges"], [])
        self.assertEqual(value["selected_references"], ["601.2e"])
        self.assertEqual(len(value["rules"]), 1)
        self.assertEqual(value["new_source_units_projected"], 1)
        self.assertEqual(value["total_projected_rule_count"], 91)
        self.assertEqual(value["resulting_projection_count"], 13)
        target = next(row for row in value["graph"]["nodes"] if row["reference"] == "733")
        self.assertEqual(target["classification"], "UNRESOLVED_RULE")
        self.assertEqual(target["status"], "UNRESOLVED")
        self.assertEqual(target["coverage_state"], "UNPROJECTED")
        self.assertFalse(set(target) & {"rule_id", "projection_id", "source_anchor", "anchor_id", "package_id", "package_binding"})
        self.assertEqual(len(value["graph"]["edges"]), 1)
        edge = value["graph"]["edges"][0]
        self.assertEqual(edge["from_reference"], "601.2e")
        self.assertEqual(edge["to_reference"], "733")
        self.assertEqual(edge["relation"], "DIRECT_NUMBERED_REFERENCE")
        self.assertEqual(edge["status"], "UNRESOLVED")

    def test_missing_or_altered_reference_metadata_and_invented_edges_fail_after_rehash(self):
        for mutation in (
                lambda value: value["rules"][0].update(direct_dependency_references=[]),
                lambda value: value["rules"][0].update(direct_dependency_references=["733.1"]),
                lambda value: value["rules"][0].update(direct_dependency_references=["733", "601.2f"]),
                lambda value: value["graph"]["edges"].clear(),
                lambda value: value["graph"]["nodes"][1].update(rule_id="sha256:" + "0" * 64),
                lambda value: value["graph"]["nodes"][1].update(source_anchor={}),
                lambda value: value["graph"]["nodes"][1].update(package_binding="THIS_ENCLOSING_PACKAGE")):
            value = self.projection.to_dict()
            mutation(value)
            value["rules"][0]["rule_id"] = rule_identity(value["rules"][0])
            with self.subTest(mutation=mutation), self.assertRaises(GameplayContractError):
                Projection.from_dict(reseal(value))


if __name__ == "__main__":
    unittest.main()
