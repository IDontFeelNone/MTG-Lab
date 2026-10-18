"""Offline contracts for the twelve bounded zone-change dependency records.

Official source bytes are external, never fixtures. Authored locator sentences
exercise byte spans without claiming source authenticity. Preservation digests
bind canonical main fe6eb895914decb3c0f5fdcda74cd595173cff93 independently of Git.
"""
import ast
from contextlib import ExitStack
from dataclasses import FrozenInstanceError
import hashlib
import json
import os
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch

from evidence.contracts import deterministic_json
from gameplay_rules.capabilities import ENGINE_CONTRACT_VERSION, EXECUTION_PROFILE
from gameplay_rules.engine import GameplayRulesEngine
from gameplay_rules.errors import GameplayContractError
from gameplay_rules.models import GameplayRulesSnapshot
from gameplay_rules.projection.zone_change_dependency_contracts import ZoneChangeDependencyProjection
from gameplay_rules.projection.zone_change_dependency_package import (
    build_zone_change_dependency_package, composite_coverage_view,
    load_zone_change_dependency_package, package_manifest,
    write_zone_change_dependency_package,
)
from gameplay_rules.projection.zone_change_dependency_scope import SELECTED_REFERENCES
from gameplay_rules.projection.zone_change_dependency_source import (
    _locate_zone_change_dependency_anchors, build_zone_change_dependency_source,
    verify_zone_change_dependency_projection_source,
)
from gameplay_rules.snapshots import load_rules_snapshot


ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "reference-reviews/gameplay-rules-zone-change-direct-dependencies"
ORIGINAL = ROOT / "reference-reviews/gameplay-rules-foundational-projection"
DESIGN = ROOT / "reference-reviews/gameplay-rules-execution-profile-design"
DEPENDENCY = ROOT / "reference-reviews/gameplay-rules-foundational-dependencies"
OBJECT_CONTROL = ROOT / "reference-reviews/gameplay-rules-object-control-exceptions"
ZONE_CHANGE = ROOT / "reference-reviews/gameplay-rules-zone-change-exceptions"
SOURCE_ROOTS = {
    "artifact_review_root": ROOT / "reference-reviews/gameplay-rules-artifact-verification",
    "source_root": ROOT / "reference-reviews/gameplay-rules-source-versioning",
    "discovery_root": ROOT / "reference-reviews/gameplay-rules-release-discovery-closure",
}
PACKAGE_ROOTS = {"projection_root": ORIGINAL, "design_root": DESIGN,
                 "dependency_root": DEPENDENCY, "object_control_root": OBJECT_CONTROL,
                 "zone_change_root": ZONE_CHANGE, **SOURCE_ROOTS}
EXPECTED_REFERENCES = (
    "611.3", "611.3a", "611.3b", "611.3d", "704.5m", "702.35a", "702.35b", "702.35c",
    "123.5", "123.5a", "123.5b", "123.5c",
)
ORIGINAL_REFERENCES = (
    "101.1", "101.2", "101.2a", "101.3", "102.1", "102.2", "108.1", "108.3",
    "108.4", "108.4a", "109.1", "109.3", "109.4", "110.1", "110.2", "110.2a",
    "400.1", "400.2", "400.3", "400.7",
)
DEPENDENCY_REFERENCES = (
    "104.3a", "111.2", "112.2", "112.2a", "113.10", "113.10a", "113.10b",
    "113.10c", "407.1", "407.2", "407.3", "407.4",
)
OBJECT_REFERENCES = tuple("109.4" + suffix for suffix in "abcdefg")
ZONE_REFERENCES = tuple("400.7" + suffix for suffix in "abcdefghijkm")
OBJECT_DEPENDENCIES = {"605", "603", "603.7d", "603.7e", "603.7f", "114",
                       "901.6", "902.6", "904.7", "905.5"}
CASTING_DEPENDENCIES = {"601.2b", "601.2f", "601.2g", "601.2h"}
UNRESOLVED_RULES = OBJECT_DEPENDENCIES | CASTING_DEPENDENCIES | {"613"}
EXPLICIT_REFERENCES = {reference: () for reference in EXPECTED_REFERENCES}
EXPLICIT_REFERENCES.update({"611.3d": ("611.3a", "611.3b"),
                            "702.35b": ("601.2b", "601.2f", "601.2g", "601.2h"),
                            "702.35c": ("400.7k",), "123.5": ("400.7",)})
ARTIFACT_HASH = "sha256:8d860e451f20f38865b725b42d82feb714c725373dd8f3b32b8652b3eeb070ca"
ORIGINAL_ID = "sha256:98bfd574c774a48aaaab4753eb8eb864dc7242effa011568f2ebf59c6a9ce6f7"
DEPENDENCY_ID = "sha256:23c7882d3291c0b5bccadff2a4c0422d5680412308cbff2cd0137401fd4fc7f1"
OBJECT_ID = "sha256:f4b75e686bfb5202f54818dc4fc9247a49a6e6ef84e2d57f070e990c25b6cce9"
ZONE_ID = "sha256:0b32e8c16fc2089949d50c0ece4b2afb7b69355f2573f041cfc8b932aa4db141"
PACKAGE_IDS = (
    "sha256:22740145cf0ec457e0b297eba5ebed3d58054b6d16179bdd738a4f5ccc5463ea",
    "sha256:684727e763c228c5eebaacbbde9e19de631f168252f8f592a600ee0a60640a3a",
    "sha256:f8cf8053b8bf9e7cc9471520eb02cc3e1e29a716f99a2ac623ec36b40343acab",
    "sha256:4836f6ea330cc40365540f85541160ef2251ff6ed88f7959f9d9e594031f7875",
)
DESIGN_ID = "sha256:f20d51ee190b4b23789208d0ae4bfa092d72aa23086fb01251d67b324ddb0687"
HISTORICAL_ID = "sha256:669d7db9ebcaf97853058fd62f408ce3c6596d5dae0ee72ff39d2ba9df56bb53"
OTHER_HASH = "sha256:" + "f" * 64
EXTERNAL_ARTIFACT = os.environ.get("MTGLAB_ZONE_CHANGE_DEPENDENCY_ARTIFACT") or os.environ.get("MTGLAB_VERIFIED_CR_ARTIFACT")
FILES = {"projection.json", "closure-review.json", "zone-change-readiness-reassessment.json",
         "composite-coverage.json", "manifest.json"}


def projection():
    return ZoneChangeDependencyProjection.from_json((PACKAGE / "projection.json").read_bytes())


def record_body(record):
    return {key: value for key, value in record.to_dict().items()
            if key not in {"schema_version", record.ID_FIELD}}


def inventory(paths):
    files = set()
    for path in paths:
        files.update([path] if path.is_file() else [item for item in path.rglob("*")
                     if item.is_file() and "__pycache__" not in item.parts and item.suffix != ".pyc"])
    result = []
    for path in sorted(files):
        if path.is_symlink():
            raise AssertionError("Protected file must not be a symlink")
        raw = path.read_bytes()
        result.append({"path": path.relative_to(ROOT).as_posix(), "bytes": len(raw),
                       "sha256": hashlib.sha256(raw).hexdigest()})
    return result


class ZoneChangeDependencyProjectionTests(unittest.TestCase):
    def setUp(self):
        self.projection = projection()
        self.rules = {rule["rule_reference"]: rule for rule in self.projection.to_dict()["rules"]}

    def test_exact_twelve_rule_allowlist_without_thirteenth_rule_or_existing_parent_duplicates(self):
        value = self.projection.to_dict()
        self.assertEqual(tuple(SELECTED_REFERENCES), EXPECTED_REFERENCES)
        self.assertEqual(value["selected_rule_count"], 12)
        self.assertEqual(tuple(self.rules), EXPECTED_REFERENCES)
        self.assertEqual(len(value["rules"]), 12)
        self.assertFalse(set(self.rules) & {"400.7", "400.7k", "611.3c", "702.35", "613"})
        self.assertFalse(set(self.rules) & CASTING_DEPENDENCIES)
        self.assertEqual([reference for reference in self.rules if reference.startswith("704.5")], ["704.5m"])
        self.assertEqual([reference for reference in self.rules if reference.startswith("702.35")],
                         ["702.35a", "702.35b", "702.35c"])
        self.assertEqual(value["projection_kind"], "NON_EXECUTABLE")
        self.assertEqual(value["milestone_status"], "ZONE_CHANGE_DIRECT_DEPENDENCIES_PROJECTED")
        self.assertFalse(value["boundary_flags"]["execution_authorized"])
        self.assertFalse(value["boundary_flags"]["real_rules_executable"])
        self.assertFalse(value["boundary_flags"]["source_body_retained"])

    def test_each_rule_retains_authored_semantics_identity_and_explicit_source_dependencies(self):
        identities = set()
        for reference, rule in self.rules.items():
            with self.subTest(reference=reference):
                for field in ("topic", "paraphrase", "semantic_category", "concept_tags", "limitations",
                              "subsystem_boundaries", "required_future_semantic_primitives"):
                    self.assertTrue(rule[field], field)
                self.assertEqual(tuple(rule["direct_dependency_references"]), EXPLICIT_REFERENCES[reference])
                self.assertEqual(rule["review_state"], "PROJECTED_FOR_REVIEW")
                self.assertEqual(rule["coverage_state"], "DEPENDENCY_REFERENCE_PROJECTED")
                self.assertEqual(rule["semantic_closure_state"], "OPEN")
                self.assertEqual(rule["execution_readiness"], "BLOCKED")
                self.assertFalse(rule["execution_ready"])
                self.assertRegex(rule["rule_id"], r"^sha256:[0-9a-f]{64}$")
                identities.add(rule["rule_id"])
        self.assertEqual(len(identities), 12)

    def test_source_lineage_exact_unique_physical_spans_and_deterministic_identities(self):
        binding = self.projection.to_dict()["source_binding"]
        self.assertEqual(binding["artifact_hash"], ARTIFACT_HASH)
        self.assertEqual(binding["byte_length"], 977752)
        self.assertEqual(binding["effective_date"], "2026-09-25")
        self.assertEqual(binding["verification_result_id"],
                         "sha256:6289f9e138c248f33b950842fd079f9dc9d4be431a9ac8dc1effb4a18ec502b3")
        self.assertEqual(binding["correspondence_review_id"],
                         "sha256:7332e6517b1b28085bbee1fa76b8ecbc9cbe4148e261452449a308ba348d9def")
        anchors = [rule["source_anchor"] for rule in self.rules.values()]
        self.assertEqual(len({anchor["line_number"] for anchor in anchors}), 12)
        self.assertEqual(len({anchor["span_sha256"] for anchor in anchors}), 12)
        for reference, anchor in zip(EXPECTED_REFERENCES, anchors):
            with self.subTest(reference=reference):
                self.assertEqual(anchor["rule_reference"], reference)
                self.assertEqual(anchor["artifact_hash"], ARTIFACT_HASH)
                self.assertEqual(anchor["effective_date"], "2026-09-25")
                self.assertEqual(anchor["span_policy"], "EXACT_RULE_LINE_EXCLUDING_LINE_TERMINATOR")
                self.assertGreater(anchor["line_number"], 0)
                self.assertGreaterEqual(anchor["byte_start"], 0)
                self.assertGreater(anchor["byte_end"], anchor["byte_start"])
                self.assertLessEqual(anchor["byte_end"], 977752)
                self.assertRegex(anchor["span_sha256"], r"^sha256:[0-9a-f]{64}$")
        ordered = sorted(anchors, key=lambda item: item["byte_start"])
        for left, right in zip(ordered, ordered[1:]):
            self.assertLessEqual(left["byte_end"], right["byte_start"])
            self.assertLess(left["line_number"], right["line_number"])
        self.assertEqual(type(self.projection).create(record_body(self.projection)), self.projection)

    def test_projection_rejects_reidentified_scope_semantics_source_and_execution_substitution(self):
        for mutation in ("count", "thirteenth", "missing", "duplicate", "611.3c", "613", "601.2b",
                         "paraphrase", "direct-reference", "source-hash", "execution", "source-text"):
            body = record_body(self.projection)
            if mutation == "count": body["selected_rule_count"] = 13
            elif mutation == "thirteenth": body["rules"].append(body["rules"][-1])
            elif mutation == "missing": body["rules"].pop()
            elif mutation == "duplicate": body["rules"][1] = body["rules"][0]
            elif mutation == "paraphrase": body["rules"][0]["paraphrase"] = "Authored unapproved substitute."
            elif mutation == "direct-reference": body["rules"][3]["direct_dependency_references"] = []
            elif mutation == "source-hash": body["source_binding"]["artifact_hash"] = OTHER_HASH
            elif mutation == "execution": body["boundary_flags"]["real_rules_executable"] = True
            elif mutation == "source-text": body["rules"][0]["source_text"] = "Unapproved fixture sentinel."
            else: body["rules"][0]["rule_reference"] = mutation
            with self.subTest(mutation=mutation), self.assertRaises(GameplayContractError):
                ZoneChangeDependencyProjection.create(body)

    def test_contract_roundtrip_immutability_and_strict_json(self):
        value = self.projection
        self.assertIs(value.verify(), value)
        self.assertEqual(type(value).from_json(value.serialize()), value)
        body = record_body(value)
        created = type(value).create(body)
        body["rules"][0]["limitations"].append("Authored caller mutation sentinel.")
        self.assertEqual(created, value)
        with self.assertRaises((FrozenInstanceError, AttributeError, TypeError)): value.new_attribute = True
        with self.assertRaises(TypeError): value.rules[0]["source_anchor"]["byte_start"] = 0
        substituted = value.to_dict()
        substituted[value.ID_FIELD] = OTHER_HASH
        with self.assertRaises(GameplayContractError): type(value).from_dict(substituted)
        raw = value.serialize()
        for invalid in ('{"selected_rule_count":12,' + raw[1:],
                        raw.replace('"selected_rule_count":12', '"selected_rule_count":NaN'),
                        raw.replace('"selected_rule_count":12', '"selected_rule_count":Infinity'), b"\xff", "[]"):
            with self.subTest(invalid=repr(invalid)[:60]), self.assertRaises(GameplayContractError):
                type(value).from_json(invalid)

    def test_static_effect_context_dynamic_application_and_special_exception_are_distinct(self):
        context = self.rules["611.3"]["semantic_distinctions"]
        dynamic = self.rules["611.3a"]["semantic_distinctions"]
        duration = self.rules["611.3b"]["semantic_distinctions"]
        exception = self.rules["611.3d"]["semantic_distinctions"]
        self.assertEqual(context["relationship"], "STATIC_ABILITY_MAY_GENERATE_CONTINUOUS_EFFECT")
        self.assertTrue(context["context_only"])
        self.assertFalse(dynamic["initial_object_set_frozen"])
        self.assertEqual(duration["permanent_location"], "battlefield")
        self.assertEqual(duration["other_object_location"], "appropriate_zone")
        self.assertEqual(exception["exception_to"], ["611.3a", "611.3b"])
        self.assertEqual(set(exception["qualifying_access"]), {
            "play_land", "cast_permanent_spell", "grant_casting_ability_to_permanent_spell_or_card"})
        self.assertEqual(exception["additional_granted_ability_zone"], "battlefield_only")
        self.assertEqual(exception["unstated_duration"], "until_end_of_game")
        self.assertFalse(exception["general_effect_follows_object_rule"])
        relations = {(row["reference"], row["relation"]) for row in self.rules["611.3d"]["dependencies"]}
        self.assertTrue({("611.3a", "EXCEPTION_TO"), ("611.3b", "EXCEPTION_TO")} <= relations)
        self.assertNotIn("611.3c", self.rules)
        self.assertIn("dynamic_static_continuous_effect_application",
                      {row["reference"] for row in self.rules["611.3a"]["required_future_semantic_primitives"]})

    def test_aura_sba_retains_both_conditions_owner_destination_and_only_subsystem_boundaries(self):
        rule = self.rules["704.5m"]
        semantics = rule["semantic_distinctions"]
        self.assertEqual(set(semantics["conditions"]), {
            "attached_to_illegal_object_or_player", "not_attached_to_object_or_player"})
        self.assertEqual(semantics["destination"], "owners_graveyard")
        self.assertEqual(semantics["supplies_evidence_for"], "400.7f")
        self.assertEqual(rule["direct_dependency_references"], [])
        self.assertTrue({"aura_attachment_legality", "state_based_action_scheduler", "zone_move_execution"} <=
                        {row["reference"] for row in rule["subsystem_boundaries"]})

    def test_madness_definition_retains_two_linked_abilities_and_is_not_just_a_discount(self):
        semantics = self.rules["702.35a"]["semantic_distinctions"]
        self.assertEqual(semantics["ability_count"], 2)
        self.assertEqual(semantics["first_ability"], {
            "kind": "static", "functional_zone": "hand", "discard_occurs": True,
            "replacement_destination": "exile"})
        self.assertEqual(semantics["second_ability"], {
            "kind": "triggered", "trigger": "first_ability_applied", "casting_optional": True,
            "casting_player": "owner", "cost": "madness_cost_instead_of_mana_cost",
            "uncast_destination": "owners_graveyard"})
        self.assertFalse(semantics["casting_discount_only"])
        self.assertTrue({"discard_replacement_behavior", "exile", "triggered_abilities", "optional_casting",
                         "alternative_costs", "graveyard_movement"} <=
                        {row["reference"] for row in self.rules["702.35a"]["subsystem_boundaries"]})

    def test_madness_casting_frontier_stays_unresolved_unprojected_and_backlink_reuses_400_7k(self):
        unresolved = self.rules["702.35b"]["unresolved_dependencies"]
        self.assertEqual({row["reference"] for row in unresolved}, CASTING_DEPENDENCIES)
        for row in unresolved:
            self.assertEqual(row["status"], "UNRESOLVED")
            self.assertEqual(row["coverage_state"], "UNPROJECTED")
            self.assertNotIn(row["reference"], self.rules)
        lookup = self.rules["702.35c"]["semantic_distinctions"]
        self.assertEqual(lookup["backlink"], "400.7k")
        self.assertTrue(lookup["trigger_resolved"])
        self.assertFalse(lookup["card_cast"])
        self.assertTrue(lookup["destination_must_be_public"])
        self.assertEqual(lookup["lookup_actor"], "effects_referencing_discarded_card")
        self.assertFalse(lookup["general_object_identity_preserved"])
        self.assertNotIn("400.7k", self.rules)

    def test_sticker_public_hidden_distinction_and_existing_400_7_exception_are_preserved(self):
        semantics = self.rules["123.5"]["semantic_distinctions"]
        self.assertFalse(semantics["hidden_destination_retains_stickers"])
        self.assertTrue(semantics["public_destination_retains_stickers"])
        self.assertTrue(semantics["public_destination_sticker_effects_continue"])
        self.assertEqual(semantics["exception_to"], ["400.7"])
        self.assertFalse(semantics["general_object_identity_preserved"])
        self.assertEqual(self.rules["123.5"]["dependencies"][0]["status"], "PROJECTED_IN_FOUNDATIONAL")
        self.assertNotIn("400.7", self.rules)

    def test_meld_and_merge_are_distinct_unsupported_sticker_boundaries_without_invented_refs(self):
        meld = self.rules["123.5a"]["semantic_distinctions"]
        merge = self.rules["123.5b"]["semantic_distinctions"]
        self.assertEqual(meld["result"], "melded_permanent")
        self.assertTrue(meld["all_component_stickers_retained"])
        self.assertTrue(meld["relative_timestamp_order_retained"])
        self.assertEqual(merge["result"], "merged_permanent")
        self.assertFalse(merge["meld_relationship"])
        for reference, boundary in (("123.5a", "melded_permanent_composition"),
                                    ("123.5b", "merged_permanent_composition")):
            with self.subTest(reference=reference):
                self.assertEqual(self.rules[reference]["direct_dependency_references"], [])
                self.assertIn({"reference": boundary, "classification": "UNRESOLVED_SUBSYSTEM", "status": "UNSUPPORTED"},
                              self.rules[reference]["subsystem_boundaries"])
                self.assertFalse(self.rules[reference]["execution_ready"])

    def test_split_composite_only_one_owner_selected_object_retains_stickers_and_effects(self):
        semantics = self.rules["123.5c"]["semantic_distinctions"]
        self.assertEqual(semantics["origin"], "battlefield")
        self.assertEqual(semantics["destination"], "another_public_zone")
        self.assertEqual(semantics["composite_kinds"], ["melded", "merged"])
        self.assertTrue(semantics["multiple_resulting_objects_possible"])
        self.assertEqual(semantics["retaining_resulting_object_count"], 1)
        self.assertEqual(semantics["choice_actor"], "owner")
        self.assertTrue(semantics["all_stickers_retained_by_chosen_object"])
        self.assertTrue(semantics["sticker_effects_apply_only_to_chosen_object"])
        self.assertFalse(semantics["stickers_always_follow_each_card"])

    def test_reidentification_cannot_erase_critical_semantic_distinctions_or_forge_anchors(self):
        for reference, field, replacement in (
            ("611.3a", "initial_object_set_frozen", True),
            ("611.3d", "exception_to", []), ("611.3d", "general_effect_follows_object_rule", True),
            ("702.35a", "ability_count", 1), ("702.35a", "casting_discount_only", True),
            ("702.35c", "card_cast", True), ("123.5", "hidden_destination_retains_stickers", True),
            ("123.5a", "relative_timestamp_order_retained", False),
            ("123.5b", "meld_relationship", True),
            ("123.5c", "retaining_resulting_object_count", 2),
            ("123.5c", "choice_actor", "controller"),
            ("123.5c", "sticker_effects_apply_only_to_chosen_object", False),
        ):
            body = record_body(self.projection)
            body["rules"][EXPECTED_REFERENCES.index(reference)]["semantic_distinctions"][field] = replacement
            with self.subTest(reference=reference, field=field), self.assertRaises(GameplayContractError):
                ZoneChangeDependencyProjection.create(body)
        for field, replacement in (("artifact_hash", OTHER_HASH), ("rule_reference", "611.3c"),
                                   ("effective_date", "2026-10-01"), ("line_number", 0),
                                   ("byte_start", -1), ("byte_start", True),
                                   ("byte_end", 977753), ("span_sha256", "invalid")):
            body = record_body(self.projection)
            body["rules"][0]["source_anchor"][field] = replacement
            with self.subTest(anchor=field), self.assertRaises(GameplayContractError):
                ZoneChangeDependencyProjection.create(body)


class ZoneChangeDependencySourceTests(unittest.TestCase):
    def synthetic_lines(self):
        citations = {"611.3d": " See rules 611.3a–b.", "702.35b": " See rules 601.2b and 601.2f–h.",
                     "702.35c": " See rule 400.7k.", "123.5": " See rule 400.7."}
        return [(reference + (". " if index % 2 else " ") + f"Authored locator sentinel {index}." +
                 citations.get(reference, "")).encode()
                for index, reference in enumerate(EXPECTED_REFERENCES)]

    def synthetic_source(self):
        return b"\n".join(self.synthetic_lines()) + b"\n"

    def test_exact_line_bytes_offsets_multibyte_header_and_mixed_terminators_are_deterministic(self):
        header = "Authored locator header ☃\r\n".encode()
        lines = self.synthetic_lines()
        endings = [b"\r\n" if index % 2 else b"\n" for index in range(12)]
        data = header + b"".join(line + end for line, end in zip(lines, endings))
        data += b"611.3c Authored excluded context.\n613 Authored excluded subsystem.\n"
        anchors = _locate_zone_change_dependency_anchors(data)
        self.assertEqual(anchors, _locate_zone_change_dependency_anchors(data))
        self.assertEqual(tuple(anchor["rule_reference"] for anchor in anchors), EXPECTED_REFERENCES)
        offset = len(header)
        for index, (anchor, line, ending) in enumerate(zip(anchors, lines, endings)):
            with self.subTest(reference=EXPECTED_REFERENCES[index]):
                self.assertEqual(anchor["line_number"], index + 2)
                self.assertEqual((anchor["byte_start"], anchor["byte_end"]), (offset, offset + len(line)))
                self.assertEqual(anchor["span_sha256"], "sha256:" + hashlib.sha256(line).hexdigest())
                self.assertEqual(data[anchor["byte_start"]:anchor["byte_end"]], line)
                self.assertNotIn("text", anchor)
            offset += len(line) + len(ending)

    def test_every_selected_reference_must_match_once_without_prefix_substitution(self):
        lines = self.synthetic_lines()
        for index, reference in enumerate(EXPECTED_REFERENCES):
            mutations = {"missing": lines[:index] + lines[index + 1:], "duplicate": lines + [lines[index]],
                         "prefix": lines[:index] + [(reference + "a Authored child sentinel.").encode()] + lines[index + 1:]}
            for mutation, selected in mutations.items():
                with self.subTest(reference=reference, mutation=mutation), self.assertRaises(GameplayContractError):
                    _locate_zone_change_dependency_anchors(b"\n".join(selected))

    def test_explicit_numbered_dependencies_cannot_be_omitted_changed_or_invented(self):
        source = self.synthetic_source()
        for fragment in ("See rules 611.3a–b.", "See rules 601.2b and 601.2f–h.",
                         "See rule 400.7k.", "See rule 400.7."):
            for replacement in (b"Authored omitted reference.", b"See rule 999.1."):
                with self.subTest(fragment=fragment, replacement=replacement), self.assertRaises(GameplayContractError):
                    _locate_zone_change_dependency_anchors(source.replace(fragment.encode(), replacement))
        with self.assertRaises(GameplayContractError):
            _locate_zone_change_dependency_anchors(source.replace(b"sentinel 0.", b"sentinel 0. See rule 613."))

    def test_exact_source_artifact_required_missing_wrong_length_wrong_sha_symlink_fail_offline(self):
        with tempfile.TemporaryDirectory(prefix="mtglab-zone-dependency-source-") as directory:
            root = Path(directory)
            wrong = root / "authored-wrong.txt"
            sentinel = b"Authored private sentinel; never an official source.\n"
            wrong.write_bytes(sentinel)
            same_length = root / "wrong-sha.txt"
            same_length.write_bytes(b"x" * 977752)
            linked = root / "linked.txt"
            linked.symlink_to(wrong)
            for path in (root / "missing.txt", wrong, same_length, linked):
                with self.subTest(kind=path.name), patch("socket.socket", side_effect=AssertionError("network forbidden")), \
                     patch("acquisition.framework.RawSnapshotStore.store", side_effect=AssertionError("retention forbidden")), \
                     self.assertRaises(GameplayContractError) as caught:
                    build_zone_change_dependency_source(path, **SOURCE_ROOTS)
                self.assertNotIn(str(root), str(caught.exception))
                self.assertNotIn(sentinel.decode().strip(), str(caught.exception))

    def test_authored_synthetic_construction_is_deterministic_and_retains_neither_prose_nor_paths(self):
        with patch("gameplay_rules.projection.zone_change_dependency_source._verified_bytes", return_value=self.synthetic_source()), \
             patch("socket.socket", side_effect=AssertionError("network forbidden")), \
             patch("acquisition.framework.RawSnapshotStore.store", side_effect=AssertionError("retention forbidden")):
            first = build_zone_change_dependency_source("authored-private.txt", **SOURCE_ROOTS)
            second = build_zone_change_dependency_source("relocated-private.txt", **SOURCE_ROOTS)
        self.assertEqual(first, second)
        self.assertEqual(len(first.rules), 12)
        self.assertNotIn("Authored locator sentinel", first.serialize())
        self.assertNotIn("private.txt", first.serialize())

    def test_fresh_verification_requires_typed_projection_and_exact_reproduction(self):
        retained = projection()
        with self.assertRaises(GameplayContractError):
            verify_zone_change_dependency_projection_source(retained.to_dict(), "unavailable.txt", **SOURCE_ROOTS)
        with patch("gameplay_rules.projection.zone_change_dependency_source._verified_bytes", return_value=self.synthetic_source()):
            different = build_zone_change_dependency_source("authored-private.txt", **SOURCE_ROOTS)
        with patch("gameplay_rules.projection.zone_change_dependency_source.build_zone_change_dependency_source", return_value=retained), \
             self.assertRaises(GameplayContractError):
            verify_zone_change_dependency_projection_source(different, "unavailable.txt", **SOURCE_ROOTS)

    @unittest.skipUnless(EXTERNAL_ARTIFACT, "external owner-controlled source not configured")
    def test_owner_artifact_rebuilds_exact_package_and_proves_no_selected_source_line_retained(self):
        path = EXTERNAL_ARTIFACT
        with patch("socket.socket", side_effect=AssertionError("network forbidden")), \
             patch("acquisition.framework.RawSnapshotStore.store", side_effect=AssertionError("retention forbidden")):
            result = verify_zone_change_dependency_projection_source(projection(), path, **SOURCE_ROOTS)
            rebuilt = build_zone_change_dependency_source(path, **SOURCE_ROOTS)
            rebuilt_package = build_zone_change_dependency_package(path, **PACKAGE_ROOTS)
        self.assertEqual(rebuilt, projection())
        self.assertEqual(rebuilt_package, load_zone_change_dependency_package(PACKAGE, **PACKAGE_ROOTS))
        self.assertEqual(result["status"], "VERIFIED_EXACT_SOURCE_SPANS")
        self.assertEqual(result["source_anchor_count"], 12)
        self.assertEqual(result["artifact_hash"], ARTIFACT_HASH)
        self.assertFalse(result["source_body_retained"])
        source = Path(path).read_bytes()
        for rule in rebuilt.rules:
            anchor = rule["source_anchor"]
            selected_line = source[anchor["byte_start"]:anchor["byte_end"]]
            for file in PACKAGE.iterdir():
                self.assertNotIn(selected_line, file.read_bytes())


class ZoneChangeDependencyReviewTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.records = load_zone_change_dependency_package(PACKAGE, **PACKAGE_ROOTS)
        cls.closure = cls.records["closure-review.json"]
        cls.reassessment = cls.records["zone-change-readiness-reassessment.json"]
        cls.composite = cls.records["composite-coverage.json"]

    def test_all_four_direct_targets_resolve_through_coherent_selected_context_and_families(self):
        value = self.closure.to_dict()
        self.assertEqual(value["resolved_count"], 4)
        expected = {
            "611.3d": (["611.3d"], ["611.3", "611.3a", "611.3b"]),
            "704.5m": (["704.5m"], []),
            "702.35": (["702.35a", "702.35b", "702.35c"], []),
            "123.5": (["123.5", "123.5a", "123.5b", "123.5c"], []),
        }
        self.assertEqual([row["target_reference"] for row in value["direct_reference_findings"]], list(expected))
        for finding in value["direct_reference_findings"]:
            with self.subTest(target=finding["target_reference"]):
                represented, context = expected[finding["target_reference"]]
                self.assertEqual(finding["represented_references"], represented)
                self.assertEqual(finding["context_references"], context)
                self.assertEqual(finding["status"], "DIRECT_REFERENCE_RESOLVED")
                self.assertEqual(finding["semantic_closure"], "SEMANTIC_CLOSURE_OPEN")
                self.assertFalse(finding["execution_ready"])
                self.assertEqual(finding["execution_status"], "EXECUTION_BLOCKED")
        self.assertEqual(set(value["remaining_unresolved_rules"]), UNRESOLVED_RULES)

    def test_affected_exceptions_reduce_numbered_blockers_but_retain_semantic_and_runtime_blockers(self):
        findings = self.closure.to_dict()["affected_exception_reassessments"]
        targets = {"400.7b": "611.3d", "400.7f": "704.5m", "400.7k": "702.35", "400.7m": "123.5"}
        self.assertEqual([row["rule_reference"] for row in findings], list(targets))
        for finding in findings:
            reference = finding["rule_reference"]
            with self.subTest(reference=reference):
                self.assertEqual(finding["previous_explicit_dependencies"], [targets[reference]])
                self.assertTrue(finding["newly_projected_dependency_evidence"])
                self.assertEqual(set(finding["remaining_unresolved_numbered_dependencies"]),
                                 CASTING_DEPENDENCIES if reference == "400.7k" else set())
                self.assertTrue(finding["direct_numbered_blockers_reduced"])
                self.assertTrue(finding["remaining_semantic_subsystem_boundaries"])
                self.assertTrue(finding["required_future_semantic_primitives"])
                self.assertEqual(finding["direct_reference_status"], "DIRECT_REFERENCE_RESOLVED")
                self.assertEqual(finding["semantic_closure"], "SEMANTIC_CLOSURE_OPEN")
                self.assertFalse(finding["execution_ready"])
                self.assertFalse(finding["mutated"])
                self.assertEqual(finding["execution_status"], "EXECUTION_BLOCKED")

    def test_parent_400_7_stays_unpromoted_with_exception_family_and_four_targets_represented(self):
        parent = self.closure.to_dict()["parent_reassessment"]
        self.assertEqual(parent["rule_reference"], "400.7")
        self.assertTrue(parent["direct_exception_family_represented"])
        self.assertTrue(parent["four_direct_dependency_targets_represented"])
        self.assertEqual(parent["unresolved_direct_dependency_targets"], [])
        self.assertEqual(set(parent["remaining_unresolved_numbered_dependencies"]), CASTING_DEPENDENCIES)
        self.assertEqual(parent["complete_zone_change_semantics"], "UNKNOWN")
        self.assertEqual(parent["dependency_closure"], "OPEN")
        self.assertEqual(parent["semantic_closure"], "SEMANTIC_CLOSURE_OPEN")
        self.assertFalse(parent["required_primitives_available"])
        self.assertFalse(parent["parent_reprojected"])
        self.assertFalse(parent["mutated"])
        self.assertFalse(parent["execution_ready"])
        self.assertEqual(parent["execution_status"], "EXECUTION_BLOCKED")

    def test_new_direct_numbered_edges_bind_selected_prior_or_unprojected_units_exactly(self):
        edges = self.closure.to_dict()["new_numbered_dependencies"]
        expected = {(source, target) for source, targets in EXPLICIT_REFERENCES.items() for target in targets}
        self.assertEqual({(row["from_reference"], row["target_reference"]) for row in edges}, expected)
        self.assertEqual(len(edges), 8)
        for row in edges:
            with self.subTest(edge=(row["from_reference"], row["target_reference"])):
                unresolved = row["target_reference"] in CASTING_DEPENDENCIES
                self.assertEqual(row["status"], "UNRESOLVED" if unresolved else "DIRECT_REFERENCE_RESOLVED")
                self.assertEqual(row["projection_state"], "UNPROJECTED" if unresolved else "PROJECTED")
                self.assertEqual(row["component"], "NONE" if unresolved else "THIS_PROJECTION"
                                 if row["target_reference"] in {"611.3a", "611.3b"} else "PRIOR_PROJECTION")

    def test_capability_dimensions_preserve_evidence_and_open_subsystems_without_runtime_primitives(self):
        value = self.reassessment.to_dict()
        self.assertEqual(value["capability_id"], "zone_change_identity")
        dimensions = {row["dimension"]: row for row in value["zone_change_dimensions"]}
        for name, expected_refs in (
            ("granted_static_ability_continuity", {"611.3", "611.3a", "611.3b", "611.3d"}),
            ("aura_sba_tracking", {"704.5m"}),
            ("madness", {"702.35a", "702.35b", "702.35c"}),
            ("sticker_continuity", {"123.5", "123.5a", "123.5b", "123.5c"}),
        ):
            with self.subTest(dimension=name):
                self.assertTrue(expected_refs <= set(dimensions[name]["supporting_projected_references"]))
                self.assertTrue(dimensions[name]["open_semantic_boundaries"])
        for name in ("spell_history_access", "public_zone_constraints", "land_play_permission_identity_bridge",
                     "cast_permission_granted_ability_continuity", "same_effect_cost_object_tracking"):
            self.assertIn(name, dimensions)
        for dimension in dimensions.values():
            self.assertFalse(dimension["execution_supported"])
            self.assertFalse(dimension["implementation_primitive_available"])
            self.assertEqual(dimension["execution_status"], "EXECUTION_BLOCKED")
        self.assertEqual(value["dependency_closure"], "OPEN")
        self.assertEqual(value["semantic_closure"], "SEMANTIC_CLOSURE_OPEN")
        self.assertEqual(value["overall_execution_readiness"], "BLOCKED")
        self.assertEqual(value["readiness_code"], "REAL_EXECUTION_PROFILE_NOT_READY")
        self.assertEqual(value["real_execution_primitives_available"], [])
        self.assertEqual(set(value["remaining_unresolved_rules"]), UNRESOLVED_RULES)
        self.assertEqual(set(value["newly_unresolved_rules"]), CASTING_DEPENDENCIES)
        self.assertFalse(value["real_snapshot_instantiated"])
        self.assertFalse(value["real_profile_activated"])
        for boundary in ("continuous_effects", "effect_execution", "casting", "triggered_abilities",
                         "zone_move_execution", "aura_attachment_legality", "state_based_action_scheduler",
                         "melded_permanent_composition", "merged_permanent_composition", "sticker_runtime"):
            self.assertIn(boundary, value["unsupported_subsystems"])
        for blocker in ("CARD_EFFECT_SEMANTICS_ABSENT", "DETERMINISTIC_REAL_RUNTIME_VECTORS_ABSENT", "OWNER_ACTIVATION_NOT_GRANTED"):
            self.assertIn(blocker, value["blockers"])

    def test_composite_exact_sixty_three_units_preserves_five_distinct_projection_and_package_identities(self):
        value = self.composite.to_dict()
        for field, count in (("foundational", 20), ("dependency", 12), ("object_control", 7),
                             ("zone_change", 12), ("zone_change_dependency", 12)):
            self.assertEqual(value[field + "_projected_rule_count"], count)
        self.assertEqual(value["total_projected_rule_count"], 63)
        self.assertEqual(value["projected_references"], list(ORIGINAL_REFERENCES + DEPENDENCY_REFERENCES +
                         OBJECT_REFERENCES + ZONE_REFERENCES + EXPECTED_REFERENCES))
        self.assertEqual(len(set(value["projected_references"])), 63)
        self.assertEqual(value["projected_references"].count("400.7"), 1)
        self.assertEqual(value["projected_references"].count("400.7k"), 1)
        self.assertFalse((UNRESOLVED_RULES | {"611.3c"}) & set(value["projected_references"]))
        components = value["projection_components"]
        self.assertEqual([row["projection_id"] for row in components],
                         [ORIGINAL_ID, DEPENDENCY_ID, OBJECT_ID, ZONE_ID, projection().identity])
        self.assertEqual(len({row["projection_id"] for row in components}), 5)
        self.assertTrue(all(not row["mutated"] for row in components))
        self.assertEqual(value["historical_acquisition_identity"], HISTORICAL_ID)
        self.assertEqual(set(value["remaining_unresolved_rules"]), UNRESOLVED_RULES)
        manifest = json.loads((PACKAGE / "manifest.json").read_bytes())
        before = {name: record.serialize() for name, record in self.records.items()}
        view = composite_coverage_view(self.records, manifest)
        self.assertEqual([row["package_id"] for row in view["projection_components"]],
                         [*PACKAGE_IDS, manifest["package_id"]])
        self.assertEqual(len({row["package_id"] for row in view["projection_components"]}), 5)
        self.assertEqual(view["total_projected_rule_count"], 63)
        self.assertEqual(before, {name: record.serialize() for name, record in self.records.items()})
        with self.assertRaises(GameplayContractError): composite_coverage_view(self.records, dict(manifest, package_id=OTHER_HASH))

    def test_reports_reject_reidentified_execution_permission_promotion_unknown_fields_and_mutation(self):
        for record in (self.closure, self.reassessment, self.composite):
            with self.subTest(record=type(record).__name__):
                self.assertIs(record.verify(), record)
                self.assertEqual(type(record).from_json(record.serialize()), record)
                with self.assertRaises((FrozenInstanceError, AttributeError, TypeError)): record.new_attribute = True
                with self.assertRaises(TypeError): record._payload["execution_authorized"] = True
                value = record.to_dict()
                value[record.ID_FIELD] = OTHER_HASH
                with self.assertRaises(GameplayContractError): type(record).from_dict(value)
                for key, promoted in (("execution_authorized", True), ("real_rules_executable", True),
                                      ("source_policy_clearance", "granted"), ("source_text", "Unapproved prose sentinel.")):
                    body = record_body(record)
                    body[key] = promoted
                    with self.subTest(field=key), self.assertRaises(GameplayContractError): type(record).create(body)

    def test_exactly_one_next_milestone_follows_frontier_without_authorization(self):
        next_milestone = self.reassessment.to_dict()["next_milestone"]
        self.assertFalse(next_milestone["authorized"])
        self.assertIn(next_milestone["candidate"], {
            "Core Control Dependency Projection", "Madness Casting Dependency Design",
            "Ability / Continuous-Effect Dependency Design", "Core State Semantic Primitive Contracts"})
        self.assertTrue(next_milestone["rationale"])
        candidates = next_milestone["evaluated_candidates"]
        self.assertEqual(sum(row["candidate"] == next_milestone["candidate"] for row in candidates), 1)
        self.assertEqual(len({row["candidate"] for row in candidates}), 4)
        self.assertTrue(all(row.get("authorized", False) is False for row in candidates))


class ZoneChangeDependencyPreservationTests(unittest.TestCase):
    def assert_inventory(self, paths, count, digest):
        value = inventory(paths)
        self.assertEqual(len(value), count)
        self.assertEqual(hashlib.sha256(deterministic_json(value).encode()).hexdigest(), digest)

    def test_runtime_product_tier_a_intelligence_mb2_writer_admission_and_policy_are_byte_identical(self):
        paths = [path for path in (ROOT / "src").iterdir() if path.name != "gameplay_rules"]
        paths.extend(path for path in (ROOT / "src/gameplay_rules").iterdir()
                     if path.name not in {"projection", "casting_design", "__pycache__"})
        self.assert_inventory(paths, 256, "191d9a47b9b9de75dd25cddb4b5497a06c7981858d17f1ecba813610073ee8f1")

    def test_all_twenty_one_prior_projection_modules_are_byte_identical(self):
        paths = [path for path in (ROOT / "src/gameplay_rules/projection").glob("*.py")
                 if not path.name.startswith(("zone_change_dependency_", "bounded_casting_"))]
        self.assert_inventory(paths, 21, "07287a6cf0aaa6f978bf6d3a3d31d5067a646009b55d6b07558542e9de39c0ac")

    def test_five_prior_rules_packages_are_byte_identical_with_exact_package_identities(self):
        cases = (
            (ORIGINAL, 2, "0e88e8baac7171f2a390f8a46913952a4a7a57fe7605ece47572c6a9a5fff5f2", PACKAGE_IDS[0]),
            (DESIGN, 6, "366a70ba5bc368577cb51eb9c71478fe9285f05b689461bff96e927600ae4b4a", DESIGN_ID),
            (DEPENDENCY, 5, "8d15ff54b5b75a568c341f7d95d6cefea0c018c3acb633011b5d48ae64a3aced", PACKAGE_IDS[1]),
            (OBJECT_CONTROL, 6, "9697a7cf6faa6c953a351ce6ab88ead754d3833e1c07e3dd0ad5a37e037c7619", PACKAGE_IDS[2]),
            (ZONE_CHANGE, 5, "63767db303554bd2e5df1a2c028391744c1060b79bf2f8c2c3c137833cc17ca1", PACKAGE_IDS[3]),
        )
        for path, count, digest, identity in cases:
            with self.subTest(package=path.name):
                self.assert_inventory([path], count, digest)
                self.assertEqual(json.loads((path / "manifest.json").read_bytes())["package_id"], identity)

    def test_architecture_decision_and_historical_acquisition_remain_exact(self):
        paths = [ROOT / "docs" / name for name in (
            "ARCHITECTURE.md", "DECISIONS.md", "DECISION_ENGINE.md", "DECISION_INTELLIGENCE.md",
            "DECISION_INTELLIGENCE_ASSESSMENT_2026_08_12.md")]
        self.assert_inventory(paths, 5, "92054f7315fabe2ac30c6dda0429ebb47bf5cc92f08998de579c5fc1140e98a2")
        fixture = ROOT / "tests/fixtures/historical_replay/card-acquisition-pilot"
        manifest = json.loads((fixture / "manifest.json").read_bytes())
        self.assertEqual(manifest["protected_inventory_identity"], HISTORICAL_ID)
        for relative, binding in manifest["files"].items():
            raw = (fixture / relative).read_bytes()
            self.assertEqual({"bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}, binding)

    def test_fictional_execution_profile_and_empty_simulation_are_unchanged(self):
        self.assertEqual(ENGINE_CONTRACT_VERSION, "gameplay-kernel-v1")
        self.assertEqual(EXECUTION_PROFILE, "fictional-two-player-v1")
        self.assertEqual({path.name for path in (ROOT / "src/simulation").iterdir()
                          if path.name != "__pycache__"}, {".gitkeep"})

    def test_new_modules_have_no_gameplay_network_or_card_semantics_implementation(self):
        forbidden_imports = {"socket", "http", "urllib", "requests", "subprocess", "simulation",
                             "providers", "external_ingestion", "market", "production_evidence",
                             "repository", "random", "secrets"}
        forbidden_runtime = {"GameplayRulesSnapshot", "CardGameplaySemantics", "GameState", "GameAction",
                             "LegalityResult", "GameTransition", "GameplayRulesEngine", "RawSnapshotStore"}
        forbidden_functions = {"to_rules_snapshot", "to_execution_profile", "activate_profile", "move_object",
                               "query_history", "execute_trigger", "cast_spell", "play_land", "apply_continuous_effect",
                               "perform_state_based_actions", "execute_madness", "apply_sticker", "merge_permanents",
                               "meld_permanents", "discard_card", "exile_card", "pay_alternative_cost", "apply_layers",
                               "check_aura_legality"}
        paths = list((ROOT / "src/gameplay_rules/projection").glob("zone_change_dependency_*.py"))
        self.assertTrue(paths)
        for path in paths:
            tree = ast.parse(path.read_text(encoding="utf-8"))
            for node in ast.walk(tree):
                imports = []
                if isinstance(node, ast.Import): imports = [name.name for name in node.names]
                elif isinstance(node, ast.ImportFrom) and node.level == 0: imports = [node.module or ""]
                with self.subTest(file=path.name):
                    self.assertFalse({name.split(".")[0] for name in imports} & forbidden_imports)
                    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        self.assertNotIn(node.name, forbidden_functions)
                    if isinstance(node, ast.Name): self.assertNotIn(node.id, forbidden_runtime)


class ZoneChangeDependencyPackageTests(unittest.TestCase):
    def copy_package(self):
        temporary = tempfile.TemporaryDirectory(prefix="mtglab-zone-dependency-package-")
        self.addCleanup(temporary.cleanup)
        path = Path(temporary.name) / "relocated-review"
        shutil.copytree(PACKAGE, path)
        return path

    def test_package_relocates_offline_readonly_without_artifact_raw_store_snapshot_or_writes(self):
        moved = self.copy_package()
        with ExitStack() as stack:
            for target in ("socket.socket", "gameplay_rules.source_evidence.artifacts.verify_local_artifact",
                           "gameplay_rules.projection.zone_change_dependency_source.build_zone_change_dependency_source",
                           "acquisition.framework.RawSnapshotStore.store", "pathlib.Path.write_bytes",
                           "pathlib.Path.write_text", "gameplay_rules.models.GameplayRulesSnapshot.create"):
                stack.enter_context(patch(target, side_effect=AssertionError("Forbidden offline dependency")))
            retained = load_zone_change_dependency_package(PACKAGE, **PACKAGE_ROOTS)
            relocated = load_zone_change_dependency_package(moved, **PACKAGE_ROOTS)
        self.assertEqual(retained, relocated)
        self.assertEqual(set(retained), FILES - {"manifest.json"})
        raw = {name: (PACKAGE / name).read_bytes() for name in retained}
        self.assertEqual(json.loads((PACKAGE / "manifest.json").read_bytes()), package_manifest(retained, raw))

    def test_tampered_extra_source_missing_links_noncanonical_oversized_and_directory_entries_reject(self):
        for mutation in ("tamper", "extra-source", "missing", "symlink", "hardlink", "whitespace", "oversized", "directory"):
            directory = self.copy_package()
            path = directory / "projection.json"
            if mutation == "tamper": path.write_bytes(path.read_bytes().replace(b"NON_EXECUTABLE", b"NOW_EXECUTABLE", 1))
            elif mutation == "extra-source": (directory / "source.txt").write_text("Authored private sentinel.")
            elif mutation == "missing": (directory / "closure-review.json").unlink()
            elif mutation == "symlink":
                path.unlink()
                path.symlink_to(PACKAGE / "projection.json")
            elif mutation == "hardlink":
                held = directory.parent / "held-projection.json"
                path.rename(held)
                path.hardlink_to(held)
            elif mutation == "whitespace": path.write_bytes(path.read_bytes() + b"\n")
            elif mutation == "oversized": path.write_bytes(b" " * 128001)
            else:
                path.unlink()
                path.mkdir()
            with self.subTest(mutation=mutation), self.assertRaises(GameplayContractError) as caught:
                load_zone_change_dependency_package(directory, **PACKAGE_ROOTS)
            self.assertNotIn(str(directory), str(caught.exception))
            self.assertNotIn("Authored private sentinel", str(caught.exception))

    def test_symlink_package_root_and_ancestor_reject(self):
        moved = self.copy_package()
        for target in (moved, moved.parent):
            link = moved.parent.parent / ("mtglab-zone-dependency-link-" + target.name)
            self.addCleanup(link.unlink, missing_ok=True)
            link.symlink_to(target, target_is_directory=True)
            with self.subTest(target=target.name), self.assertRaises(GameplayContractError):
                load_zone_change_dependency_package(link if target == moved else link / moved.name, **PACKAGE_ROOTS)

    def test_manifest_duplicate_nonfinite_unknown_and_permission_promotion_reject(self):
        raw = (PACKAGE / "manifest.json").read_text()
        for mutation in ('{"selected_rule_count":12,' + raw[1:],
                         raw.replace('"selected_rule_count":12', '"selected_rule_count":NaN'),
                         '{"unexpected":"sentinel",' + raw[1:],
                         raw.replace('"execution_authorized":false', '"execution_authorized":true'),
                         raw.replace('"private_retention":"NOT_ESTABLISHED"', '"private_retention":"GRANTED"')):
            directory = self.copy_package()
            (directory / "manifest.json").write_text(mutation)
            with self.subTest(mutation=mutation[:70]), self.assertRaises(GameplayContractError):
                load_zone_change_dependency_package(directory, **PACKAGE_ROOTS)

    def test_coherently_rehashed_false_resolution_rejects_independent_report_reproduction(self):
        records = dict(load_zone_change_dependency_package(PACKAGE, **PACKAGE_ROOTS))
        body = record_body(records["closure-review.json"])
        body["direct_reference_findings"][0]["status"] = "UNRESOLVED"
        records["closure-review.json"] = type(records["closure-review.json"]).create(body)
        for name in ("zone-change-readiness-reassessment.json", "composite-coverage.json"):
            body = record_body(records[name])
            body["closure_review_id"] = records["closure-review.json"].identity
            if name == "composite-coverage.json":
                body["zone_change_readiness_reassessment_id"] = records["zone-change-readiness-reassessment.json"].identity
            records[name] = type(records[name]).create(body)
        raw = {name: (record.serialize() + "\n").encode() for name, record in records.items()}
        manifest = package_manifest(records, raw)
        directory = self.copy_package()
        for name, value in raw.items(): (directory / name).write_bytes(value)
        (directory / "manifest.json").write_text(deterministic_json(manifest) + "\n")
        with self.assertRaises(GameplayContractError):
            load_zone_change_dependency_package(directory, **PACKAGE_ROOTS)

    def test_metadata_only_files_no_source_prose_examples_attachment_paths_or_source_txt(self):
        self.assertEqual({path.name for path in PACKAGE.iterdir()}, FILES)
        forbidden = {"source_text", "rule_text", "official_text", "oracle_text", "raw_source", "parent_text",
                     "source_body", "document_text", "examples", "quotation"}
        def inspect(value):
            if isinstance(value, dict):
                self.assertFalse(set(value) & forbidden)
                for item in value.values(): inspect(item)
            elif isinstance(value, list):
                for item in value: inspect(item)
        for path in PACKAGE.iterdir():
            with self.subTest(file=path.name):
                raw = path.read_bytes()
                self.assertFalse(path.is_symlink())
                self.assertLess(len(raw), 128001)
                for marker in (b"/tmp/", b"/workspace/", b"codex-remote-attachments", b"%PDF", b"MagicCompRules"):
                    self.assertNotIn(marker, raw)
                inspect(json.loads(raw))
        self.assertFalse(list(ROOT.rglob("*MagicCompRules*.txt")))

    def test_source_permissions_runtime_admission_and_existing_rule_reprojection_remain_blocked(self):
        manifest = json.loads((PACKAGE / "manifest.json").read_bytes())
        self.assertEqual(manifest["source_policy_clearance"], "not_granted")
        self.assertEqual(manifest["permissions"], {key: "NOT_ESTABLISHED" for key in
                         ("private_retention", "redistribution", "free_service", "commercial_service", "ai_export")})
        self.assertFalse(manifest["execution_authorized"])
        self.assertFalse(manifest["admission_eligible"])
        self.assertFalse(manifest["source_body_retained"])
        self.assertEqual(manifest["additional_rules_projected"], [])
        self.assertEqual(manifest["selected_rule_count"], 12)
        self.assertEqual(manifest["composite_projected_rule_count"], 63)
        self.assertEqual(manifest["historical_acquisition_identity"], HISTORICAL_ID)
        retained = projection()
        self.assertFalse(hasattr(retained, "to_rules_snapshot"))
        self.assertFalse(hasattr(retained, "to_execution_profile"))
        with self.assertRaises(GameplayContractError): GameplayRulesSnapshot.from_dict(retained.to_dict())
        with self.assertRaises(GameplayContractError): load_rules_snapshot(PACKAGE / "projection.json")
        with self.assertRaises(GameplayContractError): GameplayRulesEngine(retained, ())

    def test_append_only_writer_reproduces_exact_bytes_and_rejects_overwrite(self):
        records = load_zone_change_dependency_package(PACKAGE, **PACKAGE_ROOTS)
        with tempfile.TemporaryDirectory(prefix="mtglab-zone-dependency-output-") as directory:
            destination = Path(directory) / "new-review"
            manifest = write_zone_change_dependency_package(destination, records)
            self.assertEqual(manifest, json.loads((PACKAGE / "manifest.json").read_bytes()))
            self.assertEqual({path.name: path.read_bytes() for path in destination.iterdir()},
                             {path.name: path.read_bytes() for path in PACKAGE.iterdir()})
            with self.assertRaises(GameplayContractError): write_zone_change_dependency_package(destination, records)
            link = Path(directory) / "linked-review"
            link.symlink_to(destination, target_is_directory=True)
            with self.assertRaises(GameplayContractError): write_zone_change_dependency_package(link, records)


if __name__ == "__main__":
    unittest.main()
