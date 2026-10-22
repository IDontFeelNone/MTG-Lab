"""Two-unit source identities, strict JSON types and owned immutable knowledge."""
from copy import deepcopy
import json
import unittest

from evidence.contracts import sha256_identity
from gameplay_rules.errors import GameplayContractError
from gameplay_rules.projection.contracts import _json
from gameplay_rules.casting_stage_family_completion.contracts import (
    CastingStageFamilyCompletionProjection as Projection, create_projection, rule_identity,
)
from gameplay_rules.casting_stage_family_completion.source import VERIFIED_ANCHORS, anchor_identity


def reseal(value):
    value["projection_id"] = "sha256:" + sha256_identity({"domain": Projection.SCHEMA,
        "content": {key: item for key, item in value.items() if key != "projection_id"}})
    return value


class CastingStageFamilyCompletionContractTests(unittest.TestCase):
    def setUp(self):
        self.projection = create_projection(VERIFIED_ANCHORS)

    def test_two_distinct_rules_share_one_projection_with_exact_scope(self):
        value = self.projection.to_dict()
        self.assertEqual(value["selected_references"], ["601.2a", "601.2i"])
        self.assertEqual([row["rule_reference"] for row in value["rules"]], ["601.2a", "601.2i"])
        self.assertEqual(value["selected_rule_count"], 2)
        self.assertEqual(value["new_source_units_projected"], 2)
        self.assertEqual(value["total_projected_rule_count"], 93)
        self.assertEqual(value["resulting_projection_count"], 14)
        identities = [value["projection_id"]]
        for row in value["rules"]:
            identities.extend((row["rule_id"], row["source_anchor"]["anchor_id"]))
            self.assertEqual(row["rule_id"], rule_identity(row))
            self.assertEqual(row["source_anchor"]["anchor_id"], anchor_identity(row["source_anchor"]))
        self.assertEqual(len(identities), len(set(identities)))

    def test_canonical_roundtrip_and_private_snapshot_ownership(self):
        caller_owned = self.projection.to_dict()
        restored = Projection.from_dict(caller_owned)
        raw = restored.serialize().encode("utf-8")
        caller_owned["rules"][0]["source_anchor"]["byte_start"] = 0
        caller_owned["selected_references"].clear()
        exported = restored.to_dict()
        exported["rules"][1]["findings"]["injected"] = True
        self.assertEqual(restored.serialize().encode("utf-8"), raw)
        self.assertEqual(Projection.from_json(raw).serialize().encode("utf-8"), raw)
        self.assertEqual(restored.verify().identity, restored.identity)
        with self.assertRaises(TypeError):
            restored.rules[0]["execution_ready"] = True

    def test_boolean_integer_float_substitutions_fail_after_coherent_rehash(self):
        for field in ("selected_rule_count", "new_source_units_projected", "total_projected_rule_count", "resulting_projection_count"):
            for replacement in (True, False, float(self.projection.to_dict()[field])):
                value = self.projection.to_dict()
                value[field] = replacement
                with self.subTest(field=field, replacement=replacement), self.assertRaises(GameplayContractError):
                    Projection.from_dict(reseal(value))
        for replacement in (0, 0.0, 1, 1.0):
            value = self.projection.to_dict()
            value["rules"][1]["execution_ready"] = replacement
            value["rules"][1]["rule_id"] = rule_identity(value["rules"][1])
            with self.subTest(replacement=replacement), self.assertRaises(GameplayContractError):
                Projection.from_dict(reseal(value))

    def test_rule_and_anchor_content_cannot_be_changed_under_coherent_own_ids(self):
        for mutate in (
                lambda row: row["findings"].update(unsupported_injected_claim=True),
                lambda row: row.update(direct_dependency_references=[]),
                lambda row: row["source_anchor"].update(byte_end=294955, span_length=674)):
            value = self.projection.to_dict()
            row = value["rules"][0]
            mutate(row)
            row["source_anchor"]["anchor_id"] = anchor_identity(row["source_anchor"])
            row["rule_id"] = rule_identity(row)
            with self.subTest(mutate=mutate), self.assertRaises(GameplayContractError):
                Projection.from_dict(reseal(value))

    def test_wrong_own_identity_fields_or_domains_and_partial_batch_fail(self):
        for mutate in (
                lambda value: value.update(projection_id=value["rules"][0]["rule_id"]),
                lambda value: value["rules"][0].update(rule_id=value["rules"][1]["rule_id"]),
                lambda value: value["rules"][0]["source_anchor"].update(anchor_id=value["projection_id"]),
                lambda value: value["rules"].pop(),
                lambda value: value["rules"].append(deepcopy(value["rules"][0])),
                lambda value: value.update(selected_references=["601.2a"]),
                lambda value: value.update(extra_field=True)):
            value = self.projection.to_dict()
            mutate(value)
            with self.subTest(mutate=mutate), self.assertRaises(GameplayContractError):
                Projection.from_dict(value)
        value = self.projection.to_dict()
        value["projection_id"] = "sha256:" + sha256_identity({"domain": "foreign-projection-v1",
            "content": {key: item for key, item in value.items() if key != "projection_id"}})
        with self.assertRaises(GameplayContractError):
            Projection.from_dict(value)

    def test_nonplain_noncanonical_duplicate_and_nonfinite_inputs_fail(self):
        class IntegerSubclass(int):
            pass

        for replacement in (IntegerSubclass(2), ("601.2a", "601.2i"), {"unexpected"}):
            value = self.projection.to_dict()
            value["selected_rule_count" if isinstance(replacement, int) else "selected_references"] = replacement
            with self.subTest(kind=type(replacement)), self.assertRaises(GameplayContractError):
                Projection.from_dict(value)
        canonical = self.projection.serialize()
        for raw in (canonical + "\n", " " + canonical, json.dumps(self.projection.to_dict(), indent=2),
                canonical.replace('"selected_rule_count":2', '"selected_rule_count":2,"selected_rule_count":2'),
                canonical.replace('"selected_rule_count":2', '"selected_rule_count":NaN'),
                "[]", "null", b"\xff", None, True):
            with self.subTest(raw_type=type(raw)), self.assertRaises(GameplayContractError):
                Projection.from_json(raw)
        with self.assertRaises(GameplayContractError):
            create_projection(tuple(_json(VERIFIED_ANCHORS)))


if __name__ == "__main__":
    unittest.main()
