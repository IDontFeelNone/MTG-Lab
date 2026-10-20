"""Bounded source and closed projection tests; fixtures contain invented text."""
from copy import deepcopy
import hashlib
import json
import os
from pathlib import Path
import tempfile
import unittest

from evidence.contracts import deterministic_json, sha256_identity
from gameplay_rules.errors import GameplayContractError
from gameplay_rules.activated_ability_projection.contracts import (
    BoundedActivatedAbilityProjection, create_projection, rule_identity,
)
from gameplay_rules.activated_ability_projection.source import (
    VERIFIED_ANCHORS, SELECTED_REFERENCES, IMPORTED_STAGES, DIRECT_REFERENCES,
    anchor_identity, locate_anchors, validate_spans, verify_bytes, verified_anchors,
)
from gameplay_rules.projection.contracts import _json

ROOT = Path(__file__).resolve().parents[1]
SOURCE_ENV = "MTGLAB_ACTIVATED_ABILITY_PROJECTION_SOURCE_ARTIFACT"


def fictional_source(terminator=b"\n"):
    return terminator.join((
        b"fictional fixture", b"602.2. invented parent", b"\xc2\xa0",
        b"602.2a invented first child", b"\xc2\xa0",
        b"602.2b invented second child", b"\xc2\xa0", b"602.3. ",
    ))


def reseal_projection(value):
    value["projection_id"] = "sha256:" + sha256_identity({
        "domain": BoundedActivatedAbilityProjection.SCHEMA,
        "content": {key: item for key, item in value.items() if key != "projection_id"},
    })
    return value


class ActivatedAbilitySourceStructureTests(unittest.TestCase):
    def test_raw_bytes_preserve_delimiters_offsets_and_hashes(self):
        for terminator in (b"\n", b"\r\n", b"\r"):
            with self.subTest(terminator=terminator):
                raw = fictional_source(terminator)
                anchors = locate_anchors(raw)
                self.assertEqual([anchor["rule_reference"] for anchor in anchors], list(SELECTED_REFERENCES))
                for anchor in anchors:
                    span = raw[anchor["byte_start"]:anchor["byte_end"]]
                    self.assertFalse(span.endswith(terminator))
                    self.assertEqual(anchor["span_sha256"], "sha256:" + hashlib.sha256(span).hexdigest())
                    self.assertEqual(anchor["anchor_id"], anchor_identity(anchor))
                self.assertEqual([anchor["starting_physical_line"] for anchor in anchors], [2, 4, 6])

    def test_fixture_location_cannot_claim_real_source(self):
        with self.assertRaisesRegex(GameplayContractError, "VERIFIED_SOURCE_ARTIFACT_MISMATCH"):
            verify_bytes(fictional_source())
        with self.assertRaises(GameplayContractError):
            create_projection(locate_anchors(fictional_source()))

    def test_terminal_marker_body_is_not_inspected(self):
        raw = fictional_source()
        before = locate_anchors(raw)
        changed = raw + b"arbitrary next body excluded"
        after = locate_anchors(changed)
        for left, right in zip(before, after):
            self.assertEqual(left["byte_start"], right["byte_start"])
            self.assertEqual(left["byte_end"], right["byte_end"])
            self.assertEqual(left["span_sha256"], right["span_sha256"])

    def test_missing_or_duplicate_marker_fails(self):
        for raw in (
            fictional_source().replace(b"602.3. ", b"fictional end"),
            fictional_source() + b"\n602.2a duplicate",
        ):
            with self.subTest(raw_length=len(raw)), self.assertRaises(GameplayContractError):
                locate_anchors(raw)

    def test_fourth_unit_or_changed_local_structure_stops_scope(self):
        for extra in (b"602.2c invented fourth\n", b"  invented continuation\n", b"Example: invented\n"):
            raw = fictional_source().replace(b"602.3. ", extra + b"602.3. ")
            with self.subTest(extra=extra), self.assertRaisesRegex(
                    GameplayContractError, "ACTIVATED_ABILITY_PROCEDURE_SCOPE_INSUFFICIENT"):
                locate_anchors(raw)

    def test_wrong_marker_delimiter_fails(self):
        for marker in (b"602.2 ", b"602.2a. ", b"602.2b\t"):
            target = b"602.2. " if marker.startswith(b"602.2 ") else (
                b"602.2a " if marker.startswith(b"602.2a") else b"602.2b ")
            with self.subTest(marker=marker), self.assertRaises(GameplayContractError):
                locate_anchors(fictional_source().replace(target, marker))

    def test_span_metadata_rejects_boolean_integer_float_substitutions(self):
        for field in ("line_count", "starting_physical_line", "ending_physical_line", "byte_start", "byte_end"):
            for replacement in (True, False, 1.0):
                anchors = _json(VERIFIED_ANCHORS)
                anchors[0][field] = replacement
                anchors[0]["anchor_id"] = anchor_identity(anchors[0])
                with self.subTest(field=field, value=replacement), self.assertRaises(GameplayContractError):
                    validate_spans(anchors)

    def test_span_identity_and_allowlist_rejected(self):
        anchors = _json(VERIFIED_ANCHORS)
        anchors[0]["anchor_id"] = anchors[1]["anchor_id"]
        with self.assertRaises(GameplayContractError):
            validate_spans(anchors)
        with self.assertRaises(GameplayContractError):
            validate_spans(_json(VERIFIED_ANCHORS)[::-1])
        with self.assertRaises(GameplayContractError):
            validate_spans(_json(VERIFIED_ANCHORS) + [_json(VERIFIED_ANCHORS)[0]])

    def test_nonbytes_source_types_rejected(self):
        for invalid in (None, True, 1, 1.0, "fictional", bytearray(b"fictional")):
            with self.subTest(kind=type(invalid)), self.assertRaises(GameplayContractError):
                verify_bytes(invalid)
            with self.subTest(kind=type(invalid)), self.assertRaises(GameplayContractError):
                locate_anchors(invalid)


class ActivatedAbilityProjectionContractTests(unittest.TestCase):
    def setUp(self):
        self.projection = create_projection(VERIFIED_ANCHORS)

    def test_canonical_round_trip_and_immutability(self):
        raw = self.projection.serialize().encode("utf-8")
        rebuilt = BoundedActivatedAbilityProjection.from_json(raw)
        self.assertEqual(rebuilt.serialize().encode(), raw)
        self.assertEqual(rebuilt.identity, self.projection.identity)
        with self.assertRaises(TypeError):
            rebuilt.rules[0]["execution_ready"] = True
        copied = rebuilt.to_dict()
        copied["rules"][0]["execution_ready"] = True
        self.assertFalse(rebuilt.rules[0]["execution_ready"])

    def test_projection_counts_reject_bool_int_float_even_after_rehash(self):
        for field in ("selected_rule_count", "new_source_units_projected", "total_projected_rule_count", "resulting_projection_count"):
            for replacement in (True, False, float(self.projection.to_dict()[field])):
                value = self.projection.to_dict()
                value[field] = replacement
                with self.subTest(field=field, value=replacement), self.assertRaises(GameplayContractError):
                    BoundedActivatedAbilityProjection.from_dict(reseal_projection(value))

    def test_nested_boolean_substitutions_reject_recomputed_rule_and_projection(self):
        for replacement in (0, 0.0, 1, 1.0):
            value = self.projection.to_dict()
            value["rules"][1]["findings"]["ordinary_stack_object"]["controller_evaluation_implemented"] = replacement
            value["rules"][1]["rule_id"] = rule_identity(value["rules"][1])
            with self.subTest(value=replacement), self.assertRaises(GameplayContractError):
                BoundedActivatedAbilityProjection.from_dict(reseal_projection(value))

    def test_coercible_non_json_containers_and_numeric_subclasses_fail(self):
        class IntegerSubclass(int):
            pass

        value = self.projection.to_dict()
        value["selected_rule_count"] = IntegerSubclass(3)
        with self.assertRaises(GameplayContractError):
            BoundedActivatedAbilityProjection.from_dict(value)
        value = self.projection.to_dict()
        value["selected_references"] = tuple(value["selected_references"])
        with self.assertRaises(GameplayContractError):
            BoundedActivatedAbilityProjection.from_dict(value)
        with self.assertRaises(GameplayContractError):
            create_projection(tuple(_json(VERIFIED_ANCHORS)))

    def test_stale_projection_and_rule_ids_rejected(self):
        value = self.projection.to_dict()
        value["projection_id"] = value["rules"][0]["rule_id"]
        with self.assertRaises(GameplayContractError):
            BoundedActivatedAbilityProjection.from_dict(value)
        value = self.projection.to_dict()
        value["rules"][0]["rule_id"] = value["rules"][1]["rule_id"]
        with self.assertRaises(GameplayContractError):
            BoundedActivatedAbilityProjection.from_dict(reseal_projection(value))

    def test_invalid_content_not_authorized_by_recomputed_identity(self):
        value = self.projection.to_dict()
        value["rules"][0]["findings"]["activation_authority"]["fallback_actor"] = "ANY_PLAYER"
        value["rules"][0]["rule_id"] = rule_identity(value["rules"][0])
        with self.assertRaises(GameplayContractError):
            BoundedActivatedAbilityProjection.from_dict(reseal_projection(value))

    def test_duplicate_noncanonical_and_wrong_json_type_fail(self):
        canonical = self.projection.serialize()
        for raw in (
            canonical + "\n", " " + canonical,
            json.dumps(self.projection.to_dict(), indent=2),
            canonical.replace('"selected_rule_count":3', '"selected_rule_count":3,"selected_rule_count":3'),
            "[]", "null", "true",
        ):
            with self.subTest(length=len(raw)), self.assertRaises(GameplayContractError):
                BoundedActivatedAbilityProjection.from_json(raw)

    def test_structural_links_are_not_literal_direct_edges(self):
        projection = self.projection.to_dict()
        literal = {(edge["from"], edge["to"]) for edge in projection["graph"]["edges"]}
        self.assertEqual(literal, {("602.2", "733"), ("602.2a", "701.20a"), ("602.2b", "601.2f")})
        self.assertEqual(_json(DIRECT_REFERENCES), {"602.2": ["733"], "602.2a": ["701.20a"], "602.2b": ["601.2f"]})
        self.assertEqual(list(IMPORTED_STAGES), ["601.2" + letter for letter in "bcdefghi"])
        self.assertNotIn("601.2a", IMPORTED_STAGES)

    def test_missing_extra_fields_and_fourth_rule_fail(self):
        for mutate in (
            lambda value: value.pop("boundary_flags"),
            lambda value: value.update(extra=True),
            lambda value: value["rules"].append(deepcopy(value["rules"][0])),
        ):
            value = self.projection.to_dict()
            mutate(value)
            with self.assertRaises(GameplayContractError):
                BoundedActivatedAbilityProjection.from_dict(reseal_projection(value))


class ActivatedAbilityFreshExternalSourceTests(unittest.TestCase):
    def test_configured_missing_or_invalid_source_fails(self):
        with tempfile.TemporaryDirectory() as directory:
            bad = Path(directory) / "invented.fixture"
            bad.write_bytes(fictional_source())
            for candidate in (None, "", Path(directory) / "missing.fixture", bad):
                with self.subTest(candidate_is_none=candidate is None), self.assertRaises(GameplayContractError):
                    verified_anchors(candidate, review_root=ROOT / "reference-reviews")

    def test_actual_fresh_attached_source_reproduction(self):
        configured = os.environ.get(SOURCE_ENV)
        if configured is None:
            self.skipTest("external owner source unconfigured; offline checks do not establish fresh TXT verification")
        anchors = verified_anchors(configured, review_root=ROOT / "reference-reviews")
        projection = create_projection(anchors)
        self.assertEqual(projection.serialize(), create_projection(VERIFIED_ANCHORS).serialize())
        self.assertEqual(_json(anchors), _json(VERIFIED_ANCHORS))


if __name__ == "__main__":
    unittest.main()
