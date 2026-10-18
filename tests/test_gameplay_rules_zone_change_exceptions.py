"""Offline contracts for the exact twelve-rule zone-change exception family.

The official TXT is an external construction input, never a public fixture.
Newly authored locator sentences test physical spans without impersonating a
verified source artifact. Preservation inventories bind canonical main
0d32501048b5fd5c3f4a4c51e00920715aefb8ef independently of Git history.
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
from gameplay_rules.projection import FoundationalProjection
from gameplay_rules.projection.dependency_contracts import DependencyProjection
from gameplay_rules.projection.object_control_contracts import ObjectControlProjection, SourceAnomaly
from gameplay_rules.projection.zone_change_contracts import ZoneChangeProjection
from gameplay_rules.projection.zone_change_package import (
    composite_coverage_view, load_zone_change_package, package_manifest, write_zone_change_package,
)
from gameplay_rules.projection.zone_change_scope import SELECTED_REFERENCES
from gameplay_rules.projection.zone_change_source import (
    _locate_zone_change_anchors, build_zone_change_projection, build_zone_change_source,
    verify_zone_change_projection_source,
)
from gameplay_rules.snapshots import load_rules_snapshot


ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "reference-reviews/gameplay-rules-zone-change-exceptions"
ORIGINAL = ROOT / "reference-reviews/gameplay-rules-foundational-projection"
DESIGN = ROOT / "reference-reviews/gameplay-rules-execution-profile-design"
DEPENDENCY = ROOT / "reference-reviews/gameplay-rules-foundational-dependencies"
OBJECT_CONTROL = ROOT / "reference-reviews/gameplay-rules-object-control-exceptions"
SOURCE_ROOTS = {
    "artifact_review_root": ROOT / "reference-reviews/gameplay-rules-artifact-verification",
    "source_root": ROOT / "reference-reviews/gameplay-rules-source-versioning",
    "discovery_root": ROOT / "reference-reviews/gameplay-rules-release-discovery-closure",
}
PACKAGE_ROOTS = {"projection_root": ORIGINAL, "design_root": DESIGN,
                 "dependency_root": DEPENDENCY, "object_control_root": OBJECT_CONTROL,
                 **SOURCE_ROOTS}
EXPECTED_REFERENCES = tuple("400.7" + suffix for suffix in "abcdefghijkm")
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
OBJECT_DEPENDENCIES = {"605", "603", "603.7d", "603.7e", "603.7f", "114",
                       "901.6", "902.6", "904.7", "905.5"}
EXPLICIT_REFERENCES = {reference: () for reference in EXPECTED_REFERENCES}
EXPLICIT_REFERENCES.update({"400.7b": ("611.3d",), "400.7f": ("704.5m",),
                            "400.7k": ("702.35",), "400.7m": ("123.5",)})
NEW_DEPENDENCIES = {"611.3d", "704.5m", "702.35", "123.5"}
ARTIFACT_HASH = "sha256:8d860e451f20f38865b725b42d82feb714c725373dd8f3b32b8652b3eeb070ca"
ORIGINAL_ID = "sha256:98bfd574c774a48aaaab4753eb8eb864dc7242effa011568f2ebf59c6a9ce6f7"
ORIGINAL_PACKAGE_ID = "sha256:22740145cf0ec457e0b297eba5ebed3d58054b6d16179bdd738a4f5ccc5463ea"
DESIGN_PACKAGE_ID = "sha256:f20d51ee190b4b23789208d0ae4bfa092d72aa23086fb01251d67b324ddb0687"
DEPENDENCY_ID = "sha256:23c7882d3291c0b5bccadff2a4c0422d5680412308cbff2cd0137401fd4fc7f1"
DEPENDENCY_PACKAGE_ID = "sha256:684727e763c228c5eebaacbbde9e19de631f168252f8f592a600ee0a60640a3a"
OBJECT_ID = "sha256:f4b75e686bfb5202f54818dc4fc9247a49a6e6ef84e2d57f070e990c25b6cce9"
OBJECT_PACKAGE_ID = "sha256:f8cf8053b8bf9e7cc9471520eb02cc3e1e29a716f99a2ac623ec36b40343acab"
ANOMALY_ID = "sha256:4825f549d8e7a59935ac23ab0d5d068e11deb55adcb163bdc18f1f8658c0b74e"
HISTORICAL_ID = "sha256:669d7db9ebcaf97853058fd62f408ce3c6596d5dae0ee72ff39d2ba9df56bb53"
OTHER_HASH = "sha256:" + "f" * 64
FILES = {"projection.json", "family-closure-review.json",
         "zone-change-readiness-reassessment.json", "composite-coverage.json", "manifest.json"}


def projection():
    return ZoneChangeProjection.from_json((PACKAGE / "projection.json").read_bytes())


def record_body(record):
    return {key: value for key, value in record.to_dict().items()
            if key not in {"schema_version", record.ID_FIELD}}


def inventory(paths):
    files = set()
    for path in paths:
        files.update([path] if path.is_file() else
                     [item for item in path.rglob("*") if item.is_file()
                      and "__pycache__" not in item.parts and item.suffix != ".pyc"])
    result = []
    for path in sorted(files):
        if path.is_symlink():
            raise AssertionError("Protected file must not be a symlink")
        raw = path.read_bytes()
        result.append({"path": path.relative_to(ROOT).as_posix(), "bytes": len(raw),
                       "sha256": hashlib.sha256(raw).hexdigest()})
    return result


class ZoneChangeProjectionContractTests(unittest.TestCase):
    def setUp(self):
        self.projection = projection()

    def test_exact_twelve_selected_exceptions_no_parent_l_or_thirteenth_rule(self):
        value = self.projection.to_dict()
        self.assertEqual(tuple(SELECTED_REFERENCES), EXPECTED_REFERENCES)
        self.assertEqual(value["selected_rule_count"], 12)
        self.assertEqual(tuple(rule["rule_reference"] for rule in value["rules"]), EXPECTED_REFERENCES)
        self.assertEqual(len({rule["rule_reference"] for rule in value["rules"]}), 12)
        self.assertNotIn("400.7", SELECTED_REFERENCES)
        self.assertNotIn("400.7l", SELECTED_REFERENCES)
        self.assertNotIn(self.projection.identity, {ORIGINAL_ID, DEPENDENCY_ID, OBJECT_ID})
        self.assertEqual(value["projection_kind"], "NON_EXECUTABLE")
        self.assertEqual(value["status"], "PROJECTED_FOR_REVIEW")
        self.assertEqual(value["milestone_status"], "ZONE_CHANGE_EXCEPTION_FAMILY_PROJECTED")
        self.assertFalse(value["boundary_flags"]["real_rules_executable"])
        self.assertFalse(value["boundary_flags"]["source_body_retained"])
        self.assertFalse(value["boundary_flags"]["execution_authorized"])

    def test_each_selected_rule_has_authored_semantics_identity_and_open_boundaries(self):
        identifiers = set()
        for reference, rule in zip(EXPECTED_REFERENCES, self.projection.to_dict()["rules"]):
            with self.subTest(reference=reference):
                self.assertEqual(rule["rule_reference"], reference)
                for field in ("topic", "paraphrase", "semantic_category", "concept_tags", "limitations",
                              "dependencies", "subsystem_boundaries", "required_future_semantic_primitives"):
                    self.assertTrue(rule[field], field)
                self.assertEqual(rule["coverage_state"], "EXCEPTION_REFERENCE_PROJECTED")
                self.assertEqual(rule["review_state"], "PROJECTED_FOR_REVIEW")
                self.assertFalse(rule["exception_semantics_closed"])
                self.assertFalse(rule["execution_ready"])
                self.assertRegex(rule["rule_id"], r"^sha256:[0-9a-f]{64}$")
                identifiers.add(rule["rule_id"])
        self.assertEqual(len(identifiers), 12)

    def test_semantic_subsystems_stay_structured_without_invented_numbered_dependencies(self):
        rules = {rule["rule_reference"]: rule for rule in self.projection.to_dict()["rules"]}
        expected = {
            "400.7a": {"continuous_effects", "spell_resolution", "characteristics_evaluation", "control_changes", "stack_behavior"},
            "400.7b": {"static_abilities", "continuous_effects", "granted_abilities", "characteristic_layers"},
            "400.7c": {"prevention_effects", "damage", "spell_resolution", "damage_source_continuity"},
            "400.7d": {"spell_history", "casting", "costs", "mana", "spell_resolution", "card_abilities"},
            "400.7e": {"zone_change_triggers", "triggered_abilities", "public_zone_object_tracking"},
            "400.7f": {"aura_attachment", "leaves_the_battlefield_triggers", "simultaneous_zone_movement", "state_based_action_movement", "new_object_tracking"},
            "400.7g": {"casting", "casting_permissions", "stack_movement", "card_semantics"},
            "400.7h": {"casting", "casting_permissions", "stack_movement", "effect_continuity"},
            "400.7i": {"land_play", "land_play_permissions", "battlefield_entry", "turn_timing"},
            "400.7j": {"effects", "costs", "zone_movement", "public_zone_object_tracking", "object_history"},
            "400.7k": {"madness", "discard", "exile_handling", "casting_through_madness", "triggered_abilities"},
            "400.7m": {"stickers", "ticket_costs", "name_stickers", "ability_stickers", "continuous_effects"},
        }
        for reference, names in expected.items():
            with self.subTest(reference=reference):
                boundaries = rules[reference]["subsystem_boundaries"]
                self.assertEqual({row["reference"] for row in boundaries}, names)
                for row in boundaries:
                    self.assertEqual(row["classification"], "UNSUPPORTED_KEYWORD_SUBSYSTEM" if row["reference"] == "madness"
                                     else "UNRESOLVED_SUBSYSTEM")
                    self.assertEqual(row["status"], "UNSUPPORTED")
                self.assertEqual(tuple(rules[reference]["direct_dependency_references"]), EXPLICIT_REFERENCES[reference])

    def test_reidentification_cannot_erase_critical_semantic_distinctions(self):
        for reference, field, replacement in (
            ("400.7d", "object_identity_equivalence", True),
            ("400.7g", "relationship", "OTHER_EFFECT_PARTS_STACK_OBJECT_FINDABILITY"),
            ("400.7h", "relationship", "GRANTED_CASTING_ABILITY_CONTINUATION"),
            ("400.7i", "land_play_is_casting", True),
            ("400.7j", "movement_cases", [{"cause": "effect", "lookup_actor": "any_effect"}]),
            ("400.7m", "general_object_identity_preserved", True),
        ):
            body = record_body(self.projection)
            body["rules"][EXPECTED_REFERENCES.index(reference)]["semantic_distinctions"][field] = replacement
            with self.subTest(reference=reference, field=field), self.assertRaises(GameplayContractError):
                ZoneChangeProjection.create(body)

    def test_release_lineage_and_twelve_ordered_exact_physical_line_anchors(self):
        value = self.projection.to_dict()
        binding = value["source_binding"]
        self.assertEqual(binding["artifact_hash"], ARTIFACT_HASH)
        self.assertEqual(binding["byte_length"], 977752)
        self.assertEqual(binding["effective_date"], "2026-09-25")
        self.assertEqual(binding["verification_result_id"],
                         "sha256:6289f9e138c248f33b950842fd079f9dc9d4be431a9ac8dc1effb4a18ec502b3")
        self.assertEqual(binding["correspondence_review_id"],
                         "sha256:7332e6517b1b28085bbee1fa76b8ecbc9cbe4148e261452449a308ba348d9def")
        previous_end = previous_line = 0
        for index, (reference, rule) in enumerate(zip(EXPECTED_REFERENCES, value["rules"])):
            anchor = rule["source_anchor"]
            with self.subTest(reference=reference):
                self.assertEqual(anchor["rule_reference"], reference)
                self.assertEqual(anchor["artifact_hash"], ARTIFACT_HASH)
                self.assertEqual(anchor["effective_date"], "2026-09-25")
                self.assertEqual(anchor["span_policy"], "EXACT_RULE_LINE_EXCLUDING_LINE_TERMINATOR")
                self.assertRegex(anchor["span_sha256"], r"^sha256:[0-9a-f]{64}$")
                self.assertEqual(anchor["line_number"], 1957 + index * 2)
                self.assertGreaterEqual(anchor["byte_start"], previous_end)
                self.assertGreater(anchor["byte_end"], anchor["byte_start"])
                self.assertLessEqual(anchor["byte_end"], 977752)
                self.assertGreater(anchor["line_number"], previous_line)
            previous_end, previous_line = anchor["byte_end"], anchor["line_number"]

    def test_roundtrip_deep_immutability_and_identity_binding(self):
        body = record_body(self.projection)
        created = ZoneChangeProjection.create(body)
        self.assertEqual(created, self.projection)
        self.assertEqual(ZoneChangeProjection.from_json(created.serialize()), created)
        self.assertIs(created.verify(), created)
        body["rules"][0]["limitations"].append("Authored caller mutation sentinel.")
        self.assertEqual(created, self.projection)
        for field in ("_payload", "status", "new_attribute"):
            with self.subTest(field=field), self.assertRaises((FrozenInstanceError, AttributeError, TypeError)):
                setattr(created, field, {})
        with self.assertRaises(TypeError):
            created.rules[0]["source_anchor"]["byte_start"] = 0
        with self.assertRaises(AttributeError):
            created.rules[0]["limitations"].append("Forbidden mutation sentinel.")
        value = created.to_dict()
        value[created.ID_FIELD] = OTHER_HASH
        with self.assertRaises(GameplayContractError):
            ZoneChangeProjection.from_dict(value)

    def test_reidentification_cannot_add_thirteenth_parent_l_dependency_or_remove_duplicate_rule(self):
        for mutation in ("count", "thirteenth", "parent", "missing", "duplicate", "400.7l", "611.3d", "613"):
            body = record_body(self.projection)
            if mutation == "count": body["selected_rule_count"] = 13
            elif mutation == "thirteenth": body["rules"].append(body["rules"][-1])
            elif mutation == "missing": body["rules"].pop()
            elif mutation == "duplicate": body["rules"][1] = body["rules"][0]
            else: body["rules"][0]["rule_reference"] = "400.7" if mutation == "parent" else mutation
            with self.subTest(mutation=mutation), self.assertRaises(GameplayContractError):
                ZoneChangeProjection.create(body)

    def test_source_binding_anchors_and_authored_semantics_cannot_be_substituted(self):
        for field, original in record_body(self.projection)["source_binding"].items():
            body = record_body(self.projection)
            body["source_binding"][field] = original + 1 if type(original) is int else OTHER_HASH
            with self.subTest(binding=field), self.assertRaises(GameplayContractError):
                ZoneChangeProjection.create(body)
        for field, value in (("rule_reference", "400.7"), ("artifact_hash", OTHER_HASH),
                             ("effective_date", "2026-10-01"), ("byte_start", -1),
                             ("byte_start", True), ("byte_end", 977753),
                             ("line_number", 0), ("span_sha256", "invalid")):
            body = record_body(self.projection)
            body["rules"][0]["source_anchor"][field] = value
            with self.subTest(anchor=field), self.assertRaises(GameplayContractError):
                ZoneChangeProjection.create(body)
        for index in range(12):
            body = record_body(self.projection)
            body["rules"][index]["paraphrase"] = "Authored substitute outside retained scope."
            with self.subTest(rule=index), self.assertRaises(GameplayContractError):
                ZoneChangeProjection.create(body)

    def test_unknown_prose_fields_duplicate_keys_and_nonfinite_numbers_are_rejected(self):
        for target in ("envelope", "rule", "anchor"):
            body = record_body(self.projection)
            location = {"envelope": body, "rule": body["rules"][0],
                        "anchor": body["rules"][0]["source_anchor"]}[target]
            location["source_text"] = "Authored unapproved fixture sentinel."
            with self.subTest(target=target), self.assertRaises(GameplayContractError):
                ZoneChangeProjection.create(body)
        raw = self.projection.serialize()
        for malformed in ('{"selected_rule_count":12,' + raw[1:],
                          raw.replace('"selected_rule_count":12', '"selected_rule_count":NaN'),
                          raw.replace('"selected_rule_count":12', '"selected_rule_count":Infinity'),
                          b"\xff", "[]"):
            with self.subTest(raw=repr(malformed)[:50]), self.assertRaises(GameplayContractError):
                ZoneChangeProjection.from_json(malformed)


class ZoneChangeSourceTests(unittest.TestCase):
    def synthetic_lines(self):
        return [(reference + (". " if index % 2 else " ") +
                 f"Authored private locator sentinel {index}." +
                 "".join(" See rule " + target + "." for target in EXPLICIT_REFERENCES[reference])).encode("utf-8")
                for index, reference in enumerate(EXPECTED_REFERENCES)]

    def synthetic_source(self):
        return b"\n".join(self.synthetic_lines()) + b"\n"

    def test_twelve_anchors_hash_exact_physical_bytes_deterministically_without_general_parser(self):
        header = "Authored multibyte fixture ☃\r\n".encode("utf-8")
        lines = self.synthetic_lines()
        endings = [b"\r\n" if index % 2 else b"\n" for index in range(12)]
        data = header + b"".join(line + ending for line, ending in zip(lines, endings))
        data += b"400.7 Authored parent sentinel.\n400.8a Authored nonselected sentinel.\n613 Authored ignored sentinel.\n"
        anchors = _locate_zone_change_anchors(data)
        self.assertEqual(_locate_zone_change_anchors(data), anchors)
        self.assertEqual(len(anchors), 12)
        offset = len(header)
        for index, (anchor, line, ending) in enumerate(zip(anchors, lines, endings)):
            with self.subTest(reference=EXPECTED_REFERENCES[index]):
                self.assertEqual(anchor["rule_reference"], EXPECTED_REFERENCES[index])
                self.assertEqual(anchor["line_number"], index + 2)
                self.assertEqual((anchor["byte_start"], anchor["byte_end"]), (offset, offset + len(line)))
                self.assertEqual(data[anchor["byte_start"]:anchor["byte_end"]], line)
                self.assertEqual(anchor["span_sha256"], "sha256:" + hashlib.sha256(line).hexdigest())
                self.assertEqual(anchor["artifact_hash"], ARTIFACT_HASH)
                self.assertEqual(anchor["effective_date"], "2026-09-25")
                self.assertNotIn("text", anchor)
            offset += len(line) + len(ending)

    def test_every_missing_or_duplicate_exception_blocks(self):
        lines = self.synthetic_lines()
        for index, reference in enumerate(EXPECTED_REFERENCES):
            for mutation, selected in (("missing", lines[:index] + lines[index + 1:]),
                                       ("duplicate", lines + [lines[index]])):
                with self.subTest(reference=reference, mutation=mutation), self.assertRaises(GameplayContractError):
                    _locate_zone_change_anchors(b"\n".join(selected))

    def test_parent_or_nonselected_child_cannot_substitute_for_selected_exception(self):
        for index, reference in enumerate(EXPECTED_REFERENCES):
            lines = self.synthetic_lines()
            lines[index] = ("400.7 Authored parent sentinel.\n" + reference + "a Authored child sentinel.").encode()
            with self.subTest(reference=reference), self.assertRaises(GameplayContractError):
                _locate_zone_change_anchors(b"\n".join(lines))

    def test_unexpected_l_or_other_extra_direct_child_cannot_enter_family(self):
        for reference in ("400.7l", "400.7n", "400.7aa"):
            with self.subTest(reference=reference), self.assertRaises(GameplayContractError):
                _locate_zone_change_anchors(self.synthetic_source() + (reference + " Authored extra sentinel.\n").encode())

    def test_missing_changed_or_invented_direct_source_reference_rejects(self):
        source = self.synthetic_source()
        for target in sorted(NEW_DEPENDENCIES):
            for mutation in (source.replace(("See rule " + target + ".").encode(), b"Authored omitted reference."),
                             source.replace(target.encode(), b"999.1")):
                with self.subTest(target=target), self.assertRaises(GameplayContractError):
                    _locate_zone_change_anchors(mutation)
        with self.assertRaises(GameplayContractError):
            _locate_zone_change_anchors(source.replace(b"sentinel 0.", b"sentinel 0. See rule 613."))

    def test_verified_artifact_required_missing_wrong_length_wrong_sha_and_symlink_reject(self):
        with tempfile.TemporaryDirectory(prefix="mtglab-zone-source-") as directory:
            root = Path(directory)
            wrong = root / "private-changed-source.txt"
            sentinel = b"Authored private source sentinel; not an official document.\n"
            wrong.write_bytes(sentinel)
            wrong_same_length = root / "wrong-sha-correct-length.txt"
            wrong_same_length.write_bytes(b"x" * 977752)
            linked = root / "private-linked-source.txt"
            linked.symlink_to(wrong)
            for path in (root / "missing-source.txt", wrong, wrong_same_length, linked):
                for builder in (build_zone_change_source, build_zone_change_projection):
                    with self.subTest(kind=path.name, builder=builder.__name__), \
                         patch("socket.socket", side_effect=AssertionError("network forbidden")), \
                         patch("acquisition.framework.RawSnapshotStore.store", side_effect=AssertionError("source retention forbidden")), \
                         self.assertRaises(GameplayContractError) as caught:
                        builder(path, **SOURCE_ROOTS)
                    self.assertNotIn(str(root), str(caught.exception))
                    self.assertNotIn(sentinel.decode().strip(), str(caught.exception))

    def test_synthetic_builder_is_deterministic_without_prose_retention_network_or_raw_store(self):
        # Intake is deliberately replaced only to isolate authored construction;
        # this synthetic source does not establish artifact authentication.
        with patch("gameplay_rules.projection.zone_change_source._verified_bytes", return_value=self.synthetic_source()), \
             patch("socket.socket", side_effect=AssertionError("network forbidden")), \
             patch("acquisition.framework.RawSnapshotStore.store", side_effect=AssertionError("source retention forbidden")):
            first = build_zone_change_source("synthetic-only.txt", **SOURCE_ROOTS)
            second = build_zone_change_projection("synthetic-only.txt", **SOURCE_ROOTS)
        self.assertEqual(first, second)
        self.assertEqual(len(first.rules), 12)
        self.assertNotIn("Authored private locator sentinel", first.serialize())
        self.assertNotIn("synthetic-only.txt", first.serialize())
        for rule, source_line in zip(first.rules, self.synthetic_lines()):
            self.assertEqual(rule["source_anchor"]["span_sha256"], "sha256:" + hashlib.sha256(source_line).hexdigest())

    def test_fresh_verification_requires_typed_projection_and_exact_source_reproduction(self):
        retained = projection()
        with self.assertRaises(GameplayContractError):
            verify_zone_change_projection_source(retained.to_dict(), "unavailable.txt", **SOURCE_ROOTS)
        with patch("gameplay_rules.projection.zone_change_source._verified_bytes", return_value=self.synthetic_source()):
            different = build_zone_change_source("synthetic-only.txt", **SOURCE_ROOTS)
        with patch("gameplay_rules.projection.zone_change_source.build_zone_change_source", return_value=retained), \
             self.assertRaises(GameplayContractError):
            verify_zone_change_projection_source(different, "unavailable.txt", **SOURCE_ROOTS)

    @unittest.skipUnless(os.environ.get("MTGLAB_VERIFIED_CR_ARTIFACT"), "external owner-controlled source not configured")
    def test_optional_owner_artifact_freshly_verifies_all_twelve_retained_spans(self):
        with patch("socket.socket", side_effect=AssertionError("network forbidden")), \
             patch("acquisition.framework.RawSnapshotStore.store", side_effect=AssertionError("source retention forbidden")):
            result = verify_zone_change_projection_source(projection(), os.environ["MTGLAB_VERIFIED_CR_ARTIFACT"], **SOURCE_ROOTS)
        self.assertEqual(result["status"], "VERIFIED_EXACT_SOURCE_SPANS")
        self.assertEqual(result["source_anchor_count"], 12)
        self.assertEqual(result["artifact_hash"], ARTIFACT_HASH)
        self.assertFalse(result["source_body_retained"])
        source = Path(os.environ["MTGLAB_VERIFIED_CR_ARTIFACT"]).read_bytes()
        for rule in projection().rules:
            anchor = rule["source_anchor"]
            selected_line = source[anchor["byte_start"]:anchor["byte_end"]]
            for path in PACKAGE.iterdir():
                self.assertNotIn(selected_line, path.read_bytes())


class ZoneChangePreservationTests(unittest.TestCase):
    def assert_inventory(self, paths, count, digest):
        value = inventory(paths)
        self.assertEqual(len(value), count)
        self.assertEqual(hashlib.sha256(deterministic_json(value).encode()).hexdigest(), digest)

    def test_runtime_product_tier_a_cards_mb2_writer_admission_and_policy_source_are_byte_identical(self):
        paths = [path for path in (ROOT / "src").iterdir() if path.name != "gameplay_rules"]
        paths.extend(path for path in (ROOT / "src/gameplay_rules").iterdir()
                     if path.name not in {"projection", "casting_design", "__pycache__"})
        self.assert_inventory(paths, 256, "191d9a47b9b9de75dd25cddb4b5497a06c7981858d17f1ecba813610073ee8f1")

    def test_prior_projection_infrastructure_is_byte_identical(self):
        paths = [path for path in (ROOT / "src/gameplay_rules/projection").glob("*.py")
                 if not path.name.startswith(("zone_change_", "bounded_casting_"))]
        self.assert_inventory(paths, 16, "7eda9f9c213c5ffe9308db29c872692bc31cdf1ef564ca7149b035a8a35a5f02")

    def test_foundational_twenty_rule_package_is_byte_identical(self):
        self.assert_inventory([ORIGINAL], 2, "0e88e8baac7171f2a390f8a46913952a4a7a57fe7605ece47572c6a9a5fff5f2")
        manifest = json.loads((ORIGINAL / "manifest.json").read_bytes())
        self.assertEqual(manifest["package_id"], ORIGINAL_PACKAGE_ID)
        self.assertEqual(manifest["projection_id"], ORIGINAL_ID)
        retained = FoundationalProjection.from_json((ORIGINAL / "projection.json").read_bytes())
        self.assertEqual(retained.identity, ORIGINAL_ID)
        self.assertEqual(tuple(rule["rule_reference"] for rule in retained.rules), ORIGINAL_REFERENCES)

    def test_execution_design_package_is_byte_identical(self):
        self.assert_inventory([DESIGN], 6, "366a70ba5bc368577cb51eb9c71478fe9285f05b689461bff96e927600ae4b4a")
        self.assertEqual(json.loads((DESIGN / "manifest.json").read_bytes())["package_id"], DESIGN_PACKAGE_ID)

    def test_direct_dependency_package_is_byte_identical(self):
        self.assert_inventory([DEPENDENCY], 5, "8d15ff54b5b75a568c341f7d95d6cefea0c018c3acb633011b5d48ae64a3aced")
        manifest = json.loads((DEPENDENCY / "manifest.json").read_bytes())
        self.assertEqual(manifest["package_id"], DEPENDENCY_PACKAGE_ID)
        self.assertEqual(manifest["dependency_projection_id"], DEPENDENCY_ID)
        retained = DependencyProjection.from_json((DEPENDENCY / "projection.json").read_bytes())
        self.assertEqual(retained.identity, DEPENDENCY_ID)
        self.assertEqual(tuple(rule["rule_reference"] for rule in retained.rules), DEPENDENCY_REFERENCES)

    def test_object_control_package_and_anomaly_are_byte_identical(self):
        self.assert_inventory([OBJECT_CONTROL], 6, "9697a7cf6faa6c953a351ce6ab88ead754d3833e1c07e3dd0ad5a37e037c7619")
        self.assert_inventory([OBJECT_CONTROL / "source-anomaly.json"], 1,
                              "a22f4374ee145eecbf9ac510590d9df24c4589fcaf08ac2843e690facf420ee3")
        manifest = json.loads((OBJECT_CONTROL / "manifest.json").read_bytes())
        self.assertEqual(manifest["package_id"], OBJECT_PACKAGE_ID)
        self.assertEqual(ObjectControlProjection.from_json((OBJECT_CONTROL / "projection.json").read_bytes()).identity, OBJECT_ID)
        self.assertEqual(SourceAnomaly.from_json((OBJECT_CONTROL / "source-anomaly.json").read_bytes()).identity, ANOMALY_ID)

    def test_architecture_decision017_and_historical_acquisition_are_preserved(self):
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

    def test_fictional_profile_contract_and_empty_simulation_are_preserved(self):
        self.assertEqual(ENGINE_CONTRACT_VERSION, "gameplay-kernel-v1")
        self.assertEqual(EXECUTION_PROFILE, "fictional-two-player-v1")
        self.assertEqual({path.name for path in (ROOT / "src/simulation").iterdir()
                          if path.name != "__pycache__"}, {".gitkeep"})

    def test_new_modules_contain_no_network_runtime_card_semantics_or_subsystem_implementation(self):
        forbidden_imports = {"socket", "http", "urllib", "requests", "subprocess", "simulation",
                             "providers", "external_ingestion", "market", "production_evidence",
                             "repository", "random", "secrets"}
        forbidden_runtime = {"GameplayRulesSnapshot", "CardGameplaySemantics", "GameState", "GameAction",
                             "LegalityResult", "GameTransition", "GameplayRulesEngine", "RawSnapshotStore"}
        forbidden_functions = {"to_rules_snapshot", "to_execution_profile", "activate_profile", "move_object",
                               "query_history", "execute_trigger", "cast_spell", "play_land", "apply_continuous_effect",
                               "prevent_damage", "perform_state_based_actions", "execute_madness", "apply_sticker"}
        paths = list((ROOT / "src/gameplay_rules/projection").glob("zone_change_*.py"))
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
                    if isinstance(node, ast.Call):
                        called = node.func
                        while isinstance(called, ast.Attribute): called = called.value
                        if isinstance(called, ast.Name):
                            self.assertNotIn(called.id, forbidden_runtime | {"exec", "eval", "compile"})


class ZoneChangeDependencyAndClosureTests(unittest.TestCase):
    def setUp(self):
        self.records = load_zone_change_package(PACKAGE, **PACKAGE_ROOTS)
        self.projection = self.records["projection.json"]
        self.family = self.records["family-closure-review.json"]
        self.reassessment = self.records["zone-change-readiness-reassessment.json"]
        self.composite = self.records["composite-coverage.json"]

    def test_exact_direct_source_dependencies_are_recorded_and_remain_unprojected(self):
        rules = {rule["rule_reference"]: rule for rule in self.projection.to_dict()["rules"]}
        graph = self.projection.to_dict()["graph"]
        nodes = {node["reference"]: node for node in graph["nodes"]}
        edges = {(edge["from_reference"], edge["to_reference"]): edge for edge in graph["edges"]}
        for reference, targets in EXPLICIT_REFERENCES.items():
            rule = rules[reference]
            with self.subTest(reference=reference):
                self.assertEqual(tuple(rule["direct_dependency_references"]), targets)
                self.assertEqual(tuple(item["reference"] for item in rule["unresolved_dependencies"]), targets)
            for target in targets:
                with self.subTest(reference=reference, target=target):
                    self.assertNotIn(target, rules)
                    self.assertEqual(nodes[target]["classification"], "UNRESOLVED_RULE")
                    self.assertEqual(nodes[target]["status"], "UNRESOLVED")
                    self.assertEqual(edges[reference, target]["classification"], "UNRESOLVED_RULE")
                    self.assertEqual(edges[reference, target]["status"], "UNRESOLVED")
        self.assertEqual(set(self.family.to_dict()["newly_unresolved_rules"]), NEW_DEPENDENCIES)
        numbered = {node["reference"] for node in graph["nodes"] if node["classification"] == "UNRESOLVED_RULE"}
        self.assertEqual(numbered, NEW_DEPENDENCIES)

    def test_history_permission_land_cost_and_sticker_relationships_remain_distinct(self):
        rules = {rule["rule_reference"]: rule for rule in self.projection.to_dict()["rules"]}
        # These checks use project-authored metadata, never source wording.
        for reference in ("400.7d", "400.7g", "400.7h", "400.7i", "400.7j", "400.7m"):
            with self.subTest(reference=reference):
                self.assertTrue(rules[reference]["semantic_distinctions"])
        history = deterministic_json(rules["400.7d"]).lower()
        self.assertIn("history", history)
        self.assertIn("spell_to_permanent_history_access", history)
        self.assertIn("cost", history)
        self.assertIn("mana", history)
        self.assertFalse(rules["400.7d"]["semantic_distinctions"]["object_identity_equivalence"])
        self.assertEqual(rules["400.7d"]["semantic_distinctions"]["relationship"], "OBJECT_HISTORY_ACCESS")
        self.assertNotEqual(rules["400.7g"]["paraphrase"], rules["400.7h"]["paraphrase"])
        self.assertNotEqual(rules["400.7g"]["rule_id"], rules["400.7h"]["rule_id"])
        self.assertIn("cast_permission_identity_bridge", deterministic_json(rules["400.7g"]))
        self.assertEqual(rules["400.7g"]["semantic_distinctions"]["relationship"], "GRANTED_CASTING_ABILITY_CONTINUATION")
        self.assertEqual(rules["400.7h"]["semantic_distinctions"]["relationship"], "OTHER_EFFECT_PARTS_STACK_OBJECT_FINDABILITY")
        self.assertIn("land_play_permission_identity_bridge", deterministic_json(rules["400.7i"]))
        self.assertIn("casting", deterministic_json(rules["400.7i"]).lower())
        self.assertFalse(rules["400.7i"]["semantic_distinctions"]["land_play_is_casting"])
        self.assertIn("effect", deterministic_json(rules["400.7j"]).lower())
        self.assertIn("cost", deterministic_json(rules["400.7j"]).lower())
        self.assertEqual(rules["400.7j"]["semantic_distinctions"]["movement_cases"], [
            {"cause": "effect", "lookup_actor": "other_parts_of_same_effect"},
            {"cause": "spell_or_ability_cost", "lookup_actor": "effects_of_that_spell_or_ability"}])
        self.assertIn("sticker", deterministic_json(rules["400.7m"]).lower())
        sticker = rules["400.7m"]["semantic_distinctions"]
        self.assertTrue(sticker["sticker_retention"])
        self.assertTrue(sticker["sticker_effect_continuation"])
        self.assertFalse(sticker["general_object_identity_preserved"])

    def test_l_is_expected_lettering_omission_and_not_missing_rule_or_source_anomaly(self):
        policy = self.projection.to_dict()["lettering_policy"]
        self.assertIn("EXPECTED_CR_SUBRULE_LETTERING", deterministic_json(policy))
        self.assertIn("400.7l", deterministic_json(policy))
        self.assertIn("400.7l", deterministic_json(self.family.to_dict()["lettering_review"]))
        self.assertNotIn("source-anomaly.json", self.records)
        for record in (self.projection, self.family):
            raw = record.serialize()
            self.assertNotIn('"source_anomaly":true', raw)
            self.assertNotIn('"missing_source_unit_inferred":true', raw)
            self.assertNotIn('"correction_applied":true', raw)
            self.assertNotIn('"MISSING_SUBRULE"', raw)

    def test_family_coverage_is_twelve_of_twelve_without_semantic_or_parent_promotion(self):
        family = self.family.to_dict()
        coverage = family["direct_family_coverage"]
        self.assertIn("DIRECT_EXCEPTION_FAMILY_REPRESENTED", deterministic_json(coverage))
        self.assertEqual(coverage["expected_count"], 12)
        self.assertEqual(coverage["projected_count"], 12)
        self.assertEqual(coverage["references"], list(EXPECTED_REFERENCES))
        self.assertEqual(coverage["additional_rules_projected"], [])
        self.assertFalse(coverage["parent_reprojected"])
        self.assertEqual(len(family["exception_findings"]), 12)
        self.assertEqual({row["rule_reference"] for row in family["exception_findings"]}, set(EXPECTED_REFERENCES))
        for finding in family["exception_findings"]:
            self.assertFalse(finding["exception_semantics_closed"])
            self.assertFalse(finding["execution_ready"])
        self.assertFalse(coverage["exception_semantics_closed"])
        self.assertFalse(coverage["execution_ready"])
        parent = family["parent_reassessment"]
        self.assertEqual(parent["rule_reference"], "400.7")
        self.assertEqual(parent["unprojected_direct_exception_references"], [])
        self.assertEqual(parent["prior_unprojected_direct_exception_count"], 12)
        self.assertEqual(parent["direct_exception_enumeration"], "DIRECT_EXCEPTION_FAMILY_REPRESENTED")
        self.assertEqual(parent["explicit_dependency_closure"], "OPEN")
        self.assertEqual(parent["dependency_closure"], "OPEN")
        self.assertEqual(parent["semantic_subsystem_closure"], "OPEN")
        self.assertEqual(parent["historical_object_lookup_semantics"], "UNIMPLEMENTED")
        self.assertEqual(parent["zone_movement_semantics"], "UNIMPLEMENTED")
        self.assertEqual(parent["public_hidden_zone_behavior"], "UNRESOLVED")
        self.assertFalse(parent["required_primitives_available"])
        self.assertFalse(parent["parent_reprojected"])
        self.assertEqual(parent["semantic_closure"], "SEMANTIC_CLOSURE_OPEN")
        self.assertFalse(parent["execution_ready"])
        self.assertEqual(parent["execution_status"], "EXECUTION_BLOCKED")

    def test_capability_reassessment_has_required_dimensions_and_remains_nonexecutable(self):
        value = self.reassessment.to_dict()
        dimensions = value["zone_change_dimensions"]
        self.assertEqual({row["dimension"] for row in dimensions}, {
            "default_new_object_identity", "spell_to_permanent_effect_continuity", "granted_static_ability_continuity",
            "prevention_continuity", "spell_history_access", "zone_change_trigger_object_tracking", "aura_sba_tracking",
            "cast_permission_granted_ability_continuity", "cast_permission_other_effect_findability",
            "land_play_permission_identity_bridge", "same_effect_cost_object_tracking", "madness",
            "sticker_continuity", "public_zone_constraints", "complete_semantic_closure"})
        raw = deterministic_json(dimensions)
        for concept in ("default_new_object", "effect_continuity", "prevention", "history", "trigger",
                        "aura", "cast", "land", "cost", "madness", "sticker", "public"):
            with self.subTest(concept=concept): self.assertIn(concept, raw.lower())
        for dimension in dimensions:
            self.assertFalse(dimension["execution_supported"])
            self.assertFalse(dimension["implementation_primitive_available"])
            self.assertEqual(dimension["execution_status"], "EXECUTION_BLOCKED")
        self.assertEqual(value["complete_zone_change_semantics"], "UNKNOWN")
        self.assertEqual(value["overall_execution_readiness"], "BLOCKED")
        self.assertEqual(value["readiness_code"], "REAL_EXECUTION_PROFILE_NOT_READY")
        self.assertEqual(value["real_execution_primitives_available"], [])
        self.assertIn("madness", value["unsupported_subsystems"])
        self.assertIn("UNSUPPORTED_KEYWORD_SUBSYSTEM:madness", value["blockers"])
        self.assertFalse(value["real_snapshot_instantiated"])
        self.assertFalse(value["real_profile_activated"])
        self.assertEqual(value["target_profile_id"], "magic-comprehensive-rules-20260925-v1")
        self.assertTrue(NEW_DEPENDENCIES | OBJECT_DEPENDENCIES | {"613"} <= set(value["remaining_unresolved_rules"]))

    def test_four_component_composite_has_exact_fifty_one_source_units_and_separate_identities(self):
        value = self.composite.to_dict()
        self.assertEqual(value["foundational_projected_rule_count"], 20)
        self.assertEqual(value["dependency_projected_rule_count"], 12)
        self.assertEqual(value["object_control_projected_rule_count"], 7)
        self.assertEqual(value["zone_change_projected_rule_count"], 12)
        self.assertEqual(value["total_projected_rule_count"], 51)
        self.assertEqual(value["projected_references"],
                         list(ORIGINAL_REFERENCES + DEPENDENCY_REFERENCES + OBJECT_REFERENCES + EXPECTED_REFERENCES))
        self.assertEqual(len(set(value["projected_references"])), 51)
        self.assertEqual(value["projected_references"].count("400.7"), 1)
        self.assertNotIn("400.7l", value["projected_references"])
        self.assertFalse((NEW_DEPENDENCIES | OBJECT_DEPENDENCIES | {"613"}) & set(value["projected_references"]))
        components = value["projection_components"]
        self.assertEqual(len(components), 4)
        self.assertEqual([row["projection_id"] for row in components],
                         [ORIGINAL_ID, DEPENDENCY_ID, OBJECT_ID, self.projection.identity])
        self.assertEqual(len({row["projection_id"] for row in components}), 4)
        self.assertTrue(all(not row["mutated"] for row in components))
        self.assertEqual(value["historical_acquisition_identity"], HISTORICAL_ID)
        self.assertEqual(value["execution_status"], "EXECUTION_BLOCKED")
        self.assertEqual(set(value["remaining_unresolved_rules"]), NEW_DEPENDENCIES | OBJECT_DEPENDENCIES | {"613"})

    def test_reports_are_immutable_and_cannot_reidentify_execution_or_permission_promotions(self):
        for record in (self.family, self.reassessment, self.composite):
            value = record.to_dict()
            with self.subTest(record=type(record).__name__):
                self.assertIs(record.verify(), record)
                self.assertEqual(type(record).from_json(record.serialize()), record)
                self.assertFalse(value["execution_authorized"])
                self.assertFalse(value["real_rules_executable"])
                self.assertFalse(value["source_body_retained"])
                self.assertFalse(value["oracle_ingested"])
                self.assertEqual(value["source_policy_clearance"], "not_granted")
                self.assertEqual(value["owner_execution_approval"], "NOT_GRANTED")
                with self.assertRaises((FrozenInstanceError, AttributeError, TypeError)): record.new_attribute = True
                with self.assertRaises(TypeError): record._payload["execution_authorized"] = True
                value[record.ID_FIELD] = OTHER_HASH
                with self.assertRaises(GameplayContractError): type(record).from_dict(value)
                for key, promoted in (("execution_authorized", True), ("real_rules_executable", True),
                                      ("source_policy_clearance", "granted"), ("source_text", "Unapproved prose sentinel.")):
                    body = record_body(record)
                    body[key] = promoted
                    with self.subTest(field=key), self.assertRaises(GameplayContractError): type(record).create(body)

    def test_exactly_one_next_milestone_is_recommended_without_authorization(self):
        next_milestone = self.reassessment.to_dict()["next_milestone"]
        self.assertFalse(next_milestone["authorized"])
        self.assertIn(next_milestone["candidate"], {
            "Zone-Change Direct Dependency Projection", "Core Control Dependency Projection",
            "Ability / Continuous-Effect Dependency Design", "Core State Semantic Primitive Contracts"})
        self.assertTrue(next_milestone["rationale"])
        candidates = next_milestone["evaluated_candidates"]
        self.assertEqual(sum(item["candidate"] == next_milestone["candidate"] for item in candidates), 1)
        self.assertEqual(len({item["candidate"] for item in candidates}), len(candidates))
        self.assertTrue(all(item.get("authorized", False) is False for item in candidates))


class ZoneChangePackageTests(unittest.TestCase):
    def copy_package(self):
        temporary = tempfile.TemporaryDirectory(prefix="mtglab-zone-package-")
        self.addCleanup(temporary.cleanup)
        path = Path(temporary.name) / "relocated-review"
        shutil.copytree(PACKAGE, path)
        return path

    def test_package_relocates_deterministically_offline_readonly_without_source_runtime_or_raw_store(self):
        relocated = self.copy_package()
        with ExitStack() as stack:
            for target in ("socket.socket", "gameplay_rules.source_evidence.artifacts.verify_local_artifact",
                           "gameplay_rules.projection.zone_change_source.build_zone_change_source",
                           "acquisition.framework.RawSnapshotStore.store", "pathlib.Path.write_bytes",
                           "pathlib.Path.write_text", "gameplay_rules.models.GameplayRulesSnapshot.create"):
                stack.enter_context(patch(target, side_effect=AssertionError("Forbidden offline verification dependency")))
            retained = load_zone_change_package(PACKAGE, **PACKAGE_ROOTS)
            moved = load_zone_change_package(relocated, **PACKAGE_ROOTS)
        self.assertEqual(retained, moved)
        self.assertEqual(set(retained), FILES - {"manifest.json"})
        raw = {name: (PACKAGE / name).read_bytes() for name in retained}
        self.assertEqual(json.loads((PACKAGE / "manifest.json").read_bytes()), package_manifest(retained, raw))

    def test_tamper_extra_source_missing_links_noncanonical_oversized_and_directory_entries_reject(self):
        for mutation in ("tamper", "extra-source", "missing", "symlink", "hardlink", "whitespace", "oversized", "directory"):
            directory = self.copy_package()
            path = directory / "projection.json"
            if mutation == "tamper": path.write_bytes(path.read_bytes().replace(b"NON_EXECUTABLE", b"NOW_EXECUTABLE", 1))
            elif mutation == "extra-source": (directory / "source.txt").write_text("Authored private source sentinel.")
            elif mutation == "missing": (directory / "family-closure-review.json").unlink()
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
                load_zone_change_package(directory, **PACKAGE_ROOTS)
            self.assertNotIn(str(directory), str(caught.exception))
            self.assertNotIn("Authored private source sentinel", str(caught.exception))

    def test_symlink_package_root_and_symlink_ancestor_reject(self):
        relocated = self.copy_package()
        for target in (relocated, relocated.parent):
            link = relocated.parent.parent / ("mtglab-zone-link-" + target.name)
            self.addCleanup(link.unlink, missing_ok=True)
            link.symlink_to(target, target_is_directory=True)
            with self.subTest(target=target.name), self.assertRaises(GameplayContractError):
                load_zone_change_package(link if target == relocated else link / relocated.name, **PACKAGE_ROOTS)

    def test_coherently_rehashed_false_finding_rejects_independent_report_reproduction(self):
        records = dict(load_zone_change_package(PACKAGE, **PACKAGE_ROOTS))
        body = record_body(records["family-closure-review.json"])
        body["exception_findings"][0]["unresolved_rules"] = ["613"]
        records["family-closure-review.json"] = type(records["family-closure-review.json"]).create(body)
        for name in ("zone-change-readiness-reassessment.json", "composite-coverage.json"):
            body = record_body(records[name])
            body["family_closure_review_id"] = records["family-closure-review.json"].identity
            if name == "composite-coverage.json":
                body["zone_change_readiness_reassessment_id"] = records["zone-change-readiness-reassessment.json"].identity
            records[name] = type(records[name]).create(body)
        raw = {name: (record.serialize() + "\n").encode() for name, record in records.items()}
        manifest = package_manifest(records, raw)
        directory = self.copy_package()
        for name, value in raw.items(): (directory / name).write_bytes(value)
        (directory / "manifest.json").write_text(deterministic_json(manifest) + "\n")
        with self.assertRaises(GameplayContractError):
            load_zone_change_package(directory, **PACKAGE_ROOTS)

    def test_manifest_duplicate_nonfinite_unknown_and_permission_promotion_reject(self):
        raw = (PACKAGE / "manifest.json").read_text()
        mutations = (
            '{"selected_rule_count":12,' + raw[1:],
            raw.replace('"selected_rule_count":12', '"selected_rule_count":NaN'),
            '{"unexpected":"fixture",' + raw[1:],
            raw.replace('"execution_authorized":false', '"execution_authorized":true'),
            raw.replace('"private_retention":"NOT_ESTABLISHED"', '"private_retention":"GRANTED"'),
        )
        for mutation in mutations:
            directory = self.copy_package()
            (directory / "manifest.json").write_text(mutation)
            with self.subTest(mutation=mutation[:70]), self.assertRaises(GameplayContractError):
                load_zone_change_package(directory, **PACKAGE_ROOTS)

    def test_permissions_source_clearance_and_no_runtime_admission_or_parent_reprojection(self):
        manifest = json.loads((PACKAGE / "manifest.json").read_bytes())
        self.assertEqual(manifest["source_policy_clearance"], "not_granted")
        self.assertEqual(manifest["permissions"], {key: "NOT_ESTABLISHED" for key in
                         ("private_retention", "redistribution", "free_service", "commercial_service", "ai_export")})
        self.assertFalse(manifest["execution_authorized"])
        self.assertFalse(manifest["admission_eligible"])
        self.assertFalse(manifest["source_body_retained"])
        self.assertFalse(manifest["parent_reprojected"])
        self.assertEqual(manifest["additional_rules_projected"], [])
        self.assertEqual(manifest["selected_rule_count"], 12)
        self.assertEqual(manifest["composite_projected_rule_count"], 51)
        self.assertEqual(manifest["historical_acquisition_identity"], HISTORICAL_ID)

    def test_exact_metadata_only_files_no_source_prose_examples_attachment_paths_or_txt(self):
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

    def test_projection_cannot_become_real_snapshot_profile_or_engine_input(self):
        retained = projection()
        self.assertFalse(hasattr(retained, "to_rules_snapshot"))
        self.assertFalse(hasattr(retained, "to_execution_profile"))
        with self.assertRaises(GameplayContractError): GameplayRulesSnapshot.from_dict(retained.to_dict())
        with self.assertRaises(GameplayContractError): load_rules_snapshot(PACKAGE / "projection.json")
        with self.assertRaises(GameplayContractError): GameplayRulesEngine(retained, ())

    def test_resolved_readonly_composite_exposes_four_literal_package_ids_without_mutation(self):
        records = load_zone_change_package(PACKAGE, **PACKAGE_ROOTS)
        manifest = json.loads((PACKAGE / "manifest.json").read_bytes())
        before = {name: record.serialize() for name, record in records.items()}
        view = composite_coverage_view(records, manifest)
        self.assertEqual([row["package_id"] for row in view["projection_components"]],
                         [ORIGINAL_PACKAGE_ID, DEPENDENCY_PACKAGE_ID, OBJECT_PACKAGE_ID, manifest["package_id"]])
        self.assertEqual(len({row["projection_id"] for row in view["projection_components"]}), 4)
        self.assertEqual(view["total_projected_rule_count"], 51)
        self.assertFalse(view["execution_authorized"])
        self.assertFalse(view["real_rules_executable"])
        self.assertEqual(before, {name: record.serialize() for name, record in records.items()})
        with self.assertRaises(GameplayContractError):
            composite_coverage_view(records, dict(manifest, package_id=OTHER_HASH))

    def test_append_only_package_writer_reproduces_identical_metadata_bytes(self):
        records = load_zone_change_package(PACKAGE, **PACKAGE_ROOTS)
        with tempfile.TemporaryDirectory(prefix="mtglab-zone-output-") as directory:
            destination = Path(directory) / "new-review"
            manifest = write_zone_change_package(destination, records)
            self.assertEqual(manifest, json.loads((PACKAGE / "manifest.json").read_bytes()))
            self.assertEqual({path.name: path.read_bytes() for path in destination.iterdir()},
                             {path.name: path.read_bytes() for path in PACKAGE.iterdir()})
            with self.assertRaises(GameplayContractError): write_zone_change_package(destination, records)
            link = Path(directory) / "linked-review"
            link.symlink_to(destination, target_is_directory=True)
            with self.assertRaises(GameplayContractError): write_zone_change_package(link, records)


if __name__ == "__main__":
    unittest.main()
