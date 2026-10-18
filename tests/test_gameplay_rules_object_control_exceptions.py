"""Offline checks for the fixed seven-rule object-control evidence milestone.

The official owner-controlled TXT is never a test fixture. Newly authored
sentences exercise the bounded physical-line locators without granting source
verification. Preservation inventories bind canonical main
f1b72325ec4c84f20063da1945b1f8b7f8721970 independently of Git history.
"""
import ast
from contextlib import ExitStack
from dataclasses import FrozenInstanceError
import hashlib
import json
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
from gameplay_rules.projection.object_control_package import (
    composite_coverage_view, load_object_control_package, package_manifest, write_object_control_package,
)
from gameplay_rules.projection.object_control_source import (
    _build_source_anomaly, _locate_object_control_anchors, build_object_control_projection,
    build_object_control_source, build_source_anomaly, verify_object_control_projection_source,
)
from gameplay_rules.projection.object_control_scope import SELECTED_REFERENCES
from gameplay_rules.snapshots import load_rules_snapshot


ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "reference-reviews/gameplay-rules-object-control-exceptions"
ORIGINAL = ROOT / "reference-reviews/gameplay-rules-foundational-projection"
DESIGN = ROOT / "reference-reviews/gameplay-rules-execution-profile-design"
DEPENDENCY = ROOT / "reference-reviews/gameplay-rules-foundational-dependencies"
SOURCE_ROOTS = {
    "artifact_review_root": ROOT / "reference-reviews/gameplay-rules-artifact-verification",
    "source_root": ROOT / "reference-reviews/gameplay-rules-source-versioning",
    "discovery_root": ROOT / "reference-reviews/gameplay-rules-release-discovery-closure",
}
PACKAGE_ROOTS = {"projection_root": ORIGINAL, "design_root": DESIGN,
                 "dependency_root": DEPENDENCY, **SOURCE_ROOTS}
EXPECTED_REFERENCES = tuple("109.4" + suffix for suffix in "abcdefg")
ORIGINAL_REFERENCES = (
    "101.1", "101.2", "101.2a", "101.3", "102.1", "102.2", "108.1", "108.3",
    "108.4", "108.4a", "109.1", "109.3", "109.4", "110.1", "110.2", "110.2a",
    "400.1", "400.2", "400.3", "400.7",
)
DEPENDENCY_REFERENCES = (
    "104.3a", "111.2", "112.2", "112.2a", "113.10", "113.10a", "113.10b",
    "113.10c", "407.1", "407.2", "407.3", "407.4",
)
UNRESOLVED = {
    "109.4a": ("605",), "109.4b": ("603", "603.7d", "603.7e", "603.7f"),
    "109.4c": ("114",), "109.4d": ("901.6",), "109.4e": ("902.6",),
    "109.4f": ("904.7",), "109.4g": ("905.5",),
}
VARIANTS = {"109.4d": "Planechase", "109.4e": "Vanguard", "109.4f": "Archenemy",
            "109.4g": "Conspiracy Draft"}
DEFERRED_ZONE = tuple("400.7" + suffix for suffix in "abcdefghijkm")
ARTIFACT_HASH = "sha256:8d860e451f20f38865b725b42d82feb714c725373dd8f3b32b8652b3eeb070ca"
ORIGINAL_ID = "sha256:98bfd574c774a48aaaab4753eb8eb864dc7242effa011568f2ebf59c6a9ce6f7"
ORIGINAL_PACKAGE_ID = "sha256:22740145cf0ec457e0b297eba5ebed3d58054b6d16179bdd738a4f5ccc5463ea"
DESIGN_PACKAGE_ID = "sha256:f20d51ee190b4b23789208d0ae4bfa092d72aa23086fb01251d67b324ddb0687"
DEPENDENCY_ID = "sha256:23c7882d3291c0b5bccadff2a4c0422d5680412308cbff2cd0137401fd4fc7f1"
DEPENDENCY_PACKAGE_ID = "sha256:684727e763c228c5eebaacbbde9e19de631f168252f8f592a600ee0a60640a3a"
HISTORICAL_ID = "sha256:669d7db9ebcaf97853058fd62f408ce3c6596d5dae0ee72ff39d2ba9df56bb53"
OTHER_HASH = "sha256:" + "f" * 64
FILES = {"projection.json", "source-anomaly.json", "family-closure-review.json",
         "control-readiness-reassessment.json", "composite-coverage.json", "manifest.json"}


def projection():
    return ObjectControlProjection.from_json((PACKAGE / "projection.json").read_bytes())


def anomaly():
    return SourceAnomaly.from_json((PACKAGE / "source-anomaly.json").read_bytes())


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


class ObjectControlProjectionContractTests(unittest.TestCase):
    def setUp(self):
        self.projection = projection()

    def test_exact_seven_selected_exceptions_and_separate_nonexecutable_identity(self):
        value = self.projection.to_dict()
        self.assertEqual(tuple(SELECTED_REFERENCES), EXPECTED_REFERENCES)
        self.assertEqual(value["selected_rule_count"], 7)
        self.assertEqual(tuple(rule["rule_reference"] for rule in value["rules"]), EXPECTED_REFERENCES)
        self.assertEqual(len(set(rule["rule_reference"] for rule in value["rules"])), 7)
        self.assertNotIn(self.projection.identity, {ORIGINAL_ID, DEPENDENCY_ID})
        self.assertEqual(value["projection_kind"], "NON_EXECUTABLE")
        self.assertEqual(value["status"], "PROJECTED_FOR_REVIEW")
        self.assertFalse(value["boundary_flags"]["real_rules_executable"])
        self.assertFalse(value["boundary_flags"]["source_body_retained"])
        self.assertFalse(value["boundary_flags"]["execution_authorized"])

    def test_all_seven_have_authored_semantics_boundaries_and_distinct_rule_identities(self):
        identifiers = set()
        for reference, rule in zip(EXPECTED_REFERENCES, self.projection.to_dict()["rules"]):
            with self.subTest(reference=reference):
                self.assertEqual(rule["rule_reference"], reference)
                for field in ("topic", "paraphrase", "semantic_category", "concept_tags", "limitations",
                              "dependencies", "unresolved_dependencies", "required_future_semantic_primitives"):
                    self.assertTrue(rule[field], field)
                self.assertIn("variant_boundaries", rule)
                self.assertEqual(rule["coverage_state"], "EXCEPTION_REFERENCE_PROJECTED")
                self.assertEqual(rule["review_state"], "PROJECTED_FOR_REVIEW")
                self.assertRegex(rule["rule_id"], r"^sha256:[0-9a-f]{64}$")
                identifiers.add(rule["rule_id"])
        self.assertEqual(len(identifiers), 7)

    def test_release_lineage_and_all_seven_exact_line_anchors_are_bound(self):
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
        for reference, rule in zip(EXPECTED_REFERENCES, value["rules"]):
            anchor = rule["source_anchor"]
            with self.subTest(reference=reference):
                self.assertEqual(anchor["rule_reference"], reference)
                self.assertEqual(anchor["artifact_hash"], ARTIFACT_HASH)
                self.assertEqual(anchor["effective_date"], "2026-09-25")
                self.assertEqual(anchor["span_policy"], "EXACT_RULE_LINE_EXCLUDING_LINE_TERMINATOR")
                self.assertRegex(anchor["span_sha256"], r"^sha256:[0-9a-f]{64}$")
                self.assertGreaterEqual(anchor["byte_start"], previous_end)
                self.assertGreater(anchor["byte_end"], anchor["byte_start"])
                self.assertLessEqual(anchor["byte_end"], 977752)
                self.assertGreater(anchor["line_number"], previous_line)
            previous_end, previous_line = anchor["byte_end"], anchor["line_number"]

    def test_roundtrip_deep_immutability_and_identity_binding(self):
        body = record_body(self.projection)
        created = ObjectControlProjection.create(body)
        self.assertEqual(created, self.projection)
        self.assertEqual(ObjectControlProjection.from_json(created.serialize()), created)
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
            ObjectControlProjection.from_dict(value)

    def test_rehashing_cannot_add_eighth_parent_dependency_or_remove_duplicate_exception(self):
        for mutation in ("count", "eighth", "parent", "missing", "duplicate", "605", "613", "400.7a"):
            body = record_body(self.projection)
            if mutation == "count": body["selected_rule_count"] = 8
            elif mutation == "eighth": body["rules"].append(body["rules"][-1])
            elif mutation == "missing": body["rules"].pop()
            elif mutation == "duplicate": body["rules"][1] = body["rules"][0]
            else: body["rules"][0]["rule_reference"] = "109.4" if mutation == "parent" else mutation
            with self.subTest(mutation=mutation), self.assertRaises(GameplayContractError):
                ObjectControlProjection.create(body)

    def test_anchor_lineage_and_project_authored_semantics_cannot_be_substituted_by_rehashing(self):
        for field, original in record_body(self.projection)["source_binding"].items():
            body = record_body(self.projection)
            body["source_binding"][field] = original + 1 if type(original) is int else OTHER_HASH
            with self.subTest(binding=field), self.assertRaises(GameplayContractError):
                ObjectControlProjection.create(body)
        for field, value in (("rule_reference", "109.4"), ("artifact_hash", OTHER_HASH),
                             ("effective_date", "2026-10-01"), ("byte_start", -1),
                             ("byte_start", True), ("byte_end", 977753),
                             ("line_number", 0), ("span_sha256", "invalid")):
            body = record_body(self.projection)
            body["rules"][0]["source_anchor"][field] = value
            with self.subTest(anchor=field), self.assertRaises(GameplayContractError):
                ObjectControlProjection.create(body)
        body = record_body(self.projection)
        body["rules"][0]["paraphrase"] = "Authored replacement outside the retained scope."
        with self.assertRaises(GameplayContractError):
            ObjectControlProjection.create(body)

    def test_unknown_prose_fields_duplicate_keys_and_nonfinite_numbers_are_rejected(self):
        for target in ("envelope", "rule", "anchor"):
            body = record_body(self.projection)
            location = {"envelope": body, "rule": body["rules"][0],
                        "anchor": body["rules"][0]["source_anchor"]}[target]
            location["source_text"] = "Authored unapproved fixture sentinel."
            with self.subTest(target=target), self.assertRaises(GameplayContractError):
                ObjectControlProjection.create(body)
        raw = self.projection.serialize()
        for malformed in ('{"selected_rule_count":7,' + raw[1:],
                          raw.replace('"selected_rule_count":7', '"selected_rule_count":NaN'),
                          raw.replace('"selected_rule_count":7', '"selected_rule_count":Infinity'),
                          b"\xff", "[]"):
            with self.subTest(raw=repr(malformed)[:50]), self.assertRaises(GameplayContractError):
                ObjectControlProjection.from_json(malformed)


class ObjectControlSourceTests(unittest.TestCase):
    def synthetic_lines(self):
        return [(reference + (". " if index % 2 else " ") +
                 f"Authored private locator sentinel {index}.").encode("utf-8")
                for index, reference in enumerate(EXPECTED_REFERENCES)]

    def synthetic_source(self):
        return b"109.4 Authored bounded six exceptions count observation.\n" + b"\n".join(self.synthetic_lines()) + b"\n"

    def test_seven_anchors_hash_physical_bytes_deterministically_and_ignore_other_rules(self):
        header = "Authored multibyte fixture ☃\r\n".encode("utf-8")
        lines = self.synthetic_lines()
        endings = [b"\r\n" if index % 2 else b"\n" for index in range(7)]
        data = header + b"".join(line + ending for line, ending in zip(lines, endings))
        data += b"109.4 Authored parent sentinel.\n109.4aa Authored nonselected sentinel.\n613 Authored ignored sentinel.\n"
        anchors = _locate_object_control_anchors(data)
        self.assertEqual(_locate_object_control_anchors(data), anchors)
        self.assertEqual(len(anchors), 7)
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
                    _locate_object_control_anchors(b"\n".join(selected))

    def test_parent_and_nonselected_child_cannot_substitute_for_selected_exception(self):
        for index, reference in enumerate(EXPECTED_REFERENCES):
            lines = self.synthetic_lines()
            lines[index] = ("109.4 Authored parent sentinel.\n" + reference + "a Authored child sentinel.").encode()
            with self.subTest(reference=reference), self.assertRaises(GameplayContractError):
                _locate_object_control_anchors(b"\n".join(lines))

    def test_actual_verified_artifact_required_missing_wrong_length_wrong_sha_and_symlinks_rejected(self):
        with tempfile.TemporaryDirectory(prefix="mtglab-object-source-") as directory:
            root = Path(directory)
            wrong = root / "private-changed-source.txt"
            sentinel = b"Authored private source sentinel; not an official document.\n"
            wrong.write_bytes(sentinel)
            wrong_same_length = root / "wrong-sha-correct-length.txt"
            wrong_same_length.write_bytes(b"x" * 977752)
            linked = root / "private-linked-source.txt"
            linked.symlink_to(wrong)
            for path in (root / "missing-source.txt", wrong, wrong_same_length, linked):
                for builder in (build_object_control_source, build_object_control_projection, build_source_anomaly):
                    with self.subTest(kind=path.name, builder=builder.__name__), \
                         patch("socket.socket", side_effect=AssertionError("network forbidden")), \
                         patch("acquisition.framework.RawSnapshotStore.store", side_effect=AssertionError("source retention forbidden")), \
                         self.assertRaises(GameplayContractError) as caught:
                        builder(path, **SOURCE_ROOTS)
                    self.assertNotIn(str(root), str(caught.exception))
                    self.assertNotIn(sentinel.decode().strip(), str(caught.exception))

    def test_synthetic_source_builds_authored_metadata_without_retaining_its_prose_or_touching_network(self):
        # Mocking intake here tests locator/builder separation; it makes no
        # assertion that this synthetic input is an authenticated CR artifact.
        data = self.synthetic_source()
        with patch("gameplay_rules.projection.object_control_source._verified_bytes", return_value=data), \
             patch("socket.socket", side_effect=AssertionError("network forbidden")), \
             patch("acquisition.framework.RawSnapshotStore.store", side_effect=AssertionError("source retention forbidden")):
            first = build_object_control_source("synthetic-only.txt", **SOURCE_ROOTS)
            second = build_object_control_source("synthetic-only.txt", **SOURCE_ROOTS)
        self.assertEqual(first, second)
        projected, observed = first
        self.assertEqual(len(projected.rules), 7)
        for record in (projected, observed):
            self.assertNotIn("Authored private locator sentinel", record.serialize())
            self.assertNotIn("Authored bounded test assertion", record.serialize())
            self.assertNotIn("synthetic-only.txt", record.serialize())
        for rule, source_line in zip(projected.rules, self.synthetic_lines()):
            self.assertEqual(rule["source_anchor"]["span_sha256"], "sha256:" + hashlib.sha256(source_line).hexdigest())

    def test_fresh_verification_requires_typed_records_and_exact_source_reproduction(self):
        retained, observed = projection(), anomaly()
        for projected, source_anomaly in ((retained.to_dict(), observed), (retained, observed.to_dict())):
            with self.subTest(projected_type=type(projected).__name__), self.assertRaises(GameplayContractError):
                verify_object_control_projection_source(projected, source_anomaly, "unavailable.txt", **SOURCE_ROOTS)
        # The independent synthetic rebuild is valid metadata but differs
        # from the retained artifact anchors and cannot verify them.
        with patch("gameplay_rules.projection.object_control_source._verified_bytes", return_value=self.synthetic_source()):
            different, different_anomaly = build_object_control_source("synthetic-only.txt", **SOURCE_ROOTS)
        with patch("gameplay_rules.projection.object_control_source.build_object_control_source",
                   return_value=(retained, observed)), self.assertRaises(GameplayContractError):
            verify_object_control_projection_source(different, different_anomaly, "unavailable.txt", **SOURCE_ROOTS)


class ObjectControlPreservationTests(unittest.TestCase):
    def assert_inventory(self, paths, count, digest):
        value = inventory(paths)
        self.assertEqual(len(value), count)
        self.assertEqual(hashlib.sha256(deterministic_json(value).encode()).hexdigest(), digest)

    def test_all_nonprojection_production_source_preserves_runtime_policy_cards_and_writer(self):
        paths = [path for path in (ROOT / "src").iterdir() if path.name != "gameplay_rules"]
        paths.extend(path for path in (ROOT / "src/gameplay_rules").iterdir()
                     if path.name not in {"projection", "casting_design", "__pycache__"})
        self.assert_inventory(paths, 256, "191d9a47b9b9de75dd25cddb4b5497a06c7981858d17f1ecba813610073ee8f1")

    def test_prior_projection_infrastructure_is_byte_identical(self):
        # Later append-only families are outside this milestone's original inventory.
        paths = [path for path in (ROOT / "src/gameplay_rules/projection").glob("*.py")
                 if not path.name.startswith(("object_control_", "zone_change_", "bounded_casting_"))]
        self.assert_inventory(paths, 11, "03b512cc5da329a2e7a6fa7a2ec3c00e9fd18bffc20cedb9c6292035399621e3")

    def test_original_twenty_rule_package_and_projection_identity_preserved(self):
        self.assert_inventory([ORIGINAL], 2, "0e88e8baac7171f2a390f8a46913952a4a7a57fe7605ece47572c6a9a5fff5f2")
        manifest = json.loads((ORIGINAL / "manifest.json").read_bytes())
        self.assertEqual(manifest["package_id"], ORIGINAL_PACKAGE_ID)
        self.assertEqual(manifest["projection_id"], ORIGINAL_ID)
        old = FoundationalProjection.from_json((ORIGINAL / "projection.json").read_bytes())
        self.assertEqual(old.identity, ORIGINAL_ID)
        self.assertEqual(tuple(rule["rule_reference"] for rule in old.rules), ORIGINAL_REFERENCES)

    def test_pr187_execution_design_package_is_byte_identical(self):
        self.assert_inventory([DESIGN], 6, "366a70ba5bc368577cb51eb9c71478fe9285f05b689461bff96e927600ae4b4a")
        self.assertEqual(json.loads((DESIGN / "manifest.json").read_bytes())["package_id"], DESIGN_PACKAGE_ID)

    def test_pr188_direct_dependency_package_and_projection_identity_preserved(self):
        self.assert_inventory([DEPENDENCY], 5, "8d15ff54b5b75a568c341f7d95d6cefea0c018c3acb633011b5d48ae64a3aced")
        manifest = json.loads((DEPENDENCY / "manifest.json").read_bytes())
        self.assertEqual(manifest["package_id"], DEPENDENCY_PACKAGE_ID)
        self.assertEqual(manifest["dependency_projection_id"], DEPENDENCY_ID)
        prior = DependencyProjection.from_json((DEPENDENCY / "projection.json").read_bytes())
        self.assertEqual(prior.identity, DEPENDENCY_ID)
        self.assertEqual(tuple(rule["rule_reference"] for rule in prior.rules), DEPENDENCY_REFERENCES)

    def test_architecture_v13_decision017_and_historical_card_acquisition_identity_preserved(self):
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

    def test_fictional_profile_and_empty_simulation_are_preserved(self):
        self.assertEqual(ENGINE_CONTRACT_VERSION, "gameplay-kernel-v1")
        self.assertEqual(EXECUTION_PROFILE, "fictional-two-player-v1")
        self.assertEqual({path.name for path in (ROOT / "src/simulation").iterdir()
                          if path.name != "__pycache__"}, {".gitkeep"})

    def test_new_modules_do_not_import_or_instantiate_network_runtime_cards_or_policy_engines(self):
        forbidden_imports = {"socket", "http", "urllib", "requests", "subprocess", "simulation",
                             "providers", "external_ingestion", "market", "production_evidence",
                             "repository", "random", "secrets"}
        forbidden_runtime = {"GameplayRulesSnapshot", "CardGameplaySemantics", "GameState", "GameAction",
                             "LegalityResult", "GameTransition", "GameplayRulesEngine", "RawSnapshotStore"}
        paths = list((ROOT / "src/gameplay_rules/projection").glob("object_control_*.py"))
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
                        self.assertNotIn(node.name, {"to_rules_snapshot", "to_execution_profile", "activate_profile",
                                                     "query_controller", "execute_mana_ability", "execute_trigger"})
                    if isinstance(node, ast.Call):
                        called = node.func
                        while isinstance(called, ast.Attribute): called = called.value
                        if isinstance(called, ast.Name):
                            self.assertNotIn(called.id, forbidden_runtime | {"exec", "eval", "compile"})


class ObjectControlAnomalyTests(unittest.TestCase):
    def setUp(self):
        self.anomaly = anomaly()

    def test_source_count_discrepancy_has_own_identity_and_retains_all_seven_exceptions(self):
        value = self.anomaly.to_dict()
        self.assertEqual(value["anomaly_type"], "DECLARED_ENUMERATED_COUNT_MISMATCH")
        self.assertEqual(value["parent"], "109.4")
        self.assertEqual(value["parent_declared_count"], 6)
        self.assertEqual(value["enumerated_subrule_count"], 7)
        self.assertEqual(value["enumerated_refs"], list(EXPECTED_REFERENCES))
        self.assertEqual(value["source_release"], "2026-09-25")
        self.assertFalse(value["correction_applied"])
        self.assertFalse(value["source_intent_inferred"])
        self.assertFalse(value["subrule_invalidity_inferred"])
        self.assertEqual(value["interpretation"], "SOURCE_INCONSISTENCY_RETAINED")
        self.assertRegex(self.anomaly.identity, r"^sha256:[0-9a-f]{64}$")
        self.assertNotEqual(self.anomaly.identity, projection().identity)
        self.assertEqual(value["parent_source_anchor"]["rule_reference"], "109.4")
        self.assertEqual(value["parent_source_anchor"]["artifact_hash"], ARTIFACT_HASH)
        self.assertEqual(value["parent_source_anchor"]["effective_date"], "2026-09-25")
        self.assertNotIn("109.4", [rule["rule_reference"] for rule in projection().rules])

    def test_anomaly_cannot_correct_source_infer_intent_discard_subrule_or_claim_execution(self):
        for path, value in ((("parent_declared_count",), 7), (("parent_declared_count",), True),
                            (("enumerated_subrule_count",), 6), (("enumerated_refs",), list(EXPECTED_REFERENCES[:-1])),
                            (("correction_applied",), True), (("source_intent_inferred",), True),
                            (("subrule_invalidity_inferred",), True), (("interpretation",), "CORRECTED"),
                            (("boundary_flags", "execution_authorized"), True),
                            (("parent_source_anchor", "rule_reference"), "109.4a")):
            body = record_body(self.anomaly)
            target = body
            for key in path[:-1]: target = target[key]
            target[path[-1]] = value
            with self.subTest(path=path), self.assertRaises(GameplayContractError):
                SourceAnomaly.create(body)

    def test_parent_count_evidence_rejects_missing_duplicate_changed_or_reordered_parent(self):
        source = ObjectControlSourceTests().synthetic_source()
        parent, rest = source.split(b"\n", 1)
        for mutation, data in (
            ("missing-parent", rest), ("duplicate-parent", parent + b"\n" + source),
            ("changed-count", source.replace(b"six", b"seven", 1)),
            ("ambiguous-count", parent + b" six exceptions\n" + rest),
            ("reordered-parent", rest + parent + b"\n"),
        ):
            with self.subTest(mutation=mutation), self.assertRaises(GameplayContractError):
                _build_source_anomaly(data)

    def test_parent_anomaly_hashes_exact_line_without_retaining_parent_prose(self):
        source = ObjectControlSourceTests().synthetic_source()
        parent = source.split(b"\n", 1)[0]
        observed = _build_source_anomaly(source)
        self.assertEqual(_build_source_anomaly(source), observed)
        value = observed.to_dict()
        anchor = value["parent_source_anchor"]
        self.assertEqual(anchor["byte_start"], 0)
        self.assertEqual(anchor["byte_end"], len(parent))
        self.assertEqual(anchor["line_number"], 1)
        self.assertEqual(anchor["span_sha256"], "sha256:" + hashlib.sha256(parent).hexdigest())
        self.assertNotIn(parent.decode(), observed.serialize())
        self.assertNotIn("Authored bounded test assertion", observed.serialize())

    def test_anomaly_roundtrip_is_immutable_and_unknown_official_prose_fields_fail(self):
        self.assertEqual(SourceAnomaly.from_json(self.anomaly.serialize()), self.anomaly)
        self.assertEqual(SourceAnomaly.create(record_body(self.anomaly)), self.anomaly)
        self.assertIs(self.anomaly.verify(), self.anomaly)
        with self.assertRaises(TypeError): self.anomaly._payload["correction_applied"] = True
        for field in ("status", "new_attribute"):
            with self.subTest(field=field), self.assertRaises((FrozenInstanceError, AttributeError, TypeError)):
                setattr(self.anomaly, field, True)
        body = record_body(self.anomaly)
        body["parent_text"] = "Authored unapproved parent prose sentinel."
        with self.assertRaises(GameplayContractError): SourceAnomaly.create(body)
        value = self.anomaly.to_dict()
        value[self.anomaly.ID_FIELD] = OTHER_HASH
        with self.assertRaises(GameplayContractError): SourceAnomaly.from_dict(value)


class ObjectControlDependencyAndClosureTests(unittest.TestCase):
    def setUp(self):
        self.records = load_object_control_package(PACKAGE, **PACKAGE_ROOTS)
        self.projection = self.records["projection.json"]
        self.family = self.records["family-closure-review.json"]
        self.reassessment = self.records["control-readiness-reassessment.json"]
        self.composite = self.records["composite-coverage.json"]

    def test_all_ten_unresolved_control_dependency_edges_are_explicit_and_not_projected(self):
        value = self.projection.to_dict()
        rules = {rule["rule_reference"]: rule for rule in value["rules"]}
        nodes = {node["reference"]: node for node in value["graph"]["nodes"]}
        edges = {(edge["from_reference"], edge["to_reference"]): edge for edge in value["graph"]["edges"]}
        self.assertEqual(sum(map(len, UNRESOLVED.values())), 10)
        for reference, targets in UNRESOLVED.items():
            rule = rules[reference]
            with self.subTest(reference=reference):
                self.assertEqual(tuple(rule["direct_dependency_references"]), targets)
                self.assertEqual(tuple(item["reference"] for item in rule["unresolved_dependencies"]), targets)
                self.assertEqual(nodes[reference]["classification"], "PROJECTED_EXCEPTION")
                self.assertEqual(nodes[reference]["status"], "EXCEPTION_REFERENCE_PROJECTED")
            for target in targets:
                with self.subTest(reference=reference, target=target):
                    self.assertNotIn(target, rules)
                    self.assertEqual(nodes[target]["classification"], "UNRESOLVED_RULE")
                    self.assertEqual(nodes[target]["status"], "UNRESOLVED")
                    self.assertEqual(edges[reference, target]["classification"], "UNRESOLVED_RULE")
                    self.assertEqual(edges[reference, target]["status"], "UNRESOLVED")
                    self.assertEqual(edges[reference, target]["relation"], "DEPENDS_ON")
        self.assertEqual(set(self.family.to_dict()["newly_unresolved_rules"]), set.union(*map(set, UNRESOLVED.values())))

    def test_core_and_casual_variant_domains_are_classified_and_all_remain_nonexecutable(self):
        for rule in self.projection.to_dict()["rules"]:
            reference = rule["rule_reference"]
            with self.subTest(reference=reference):
                self.assertEqual(rule["domain_classification"],
                                 "CASUAL_VARIANT_SUBSYSTEM" if reference in VARIANTS else "CORE_GAME_SUBSYSTEM")
                self.assertFalse(rule["exception_semantics_closed"])
                self.assertFalse(rule["execution_ready"])
                if reference in VARIANTS:
                    self.assertEqual(rule["variant_boundaries"], [{"reference": VARIANTS[reference],
                                     "classification": "UNSUPPORTED_VARIANT", "status": "UNSUPPORTED"}])
                else:
                    self.assertEqual(rule["variant_boundaries"], [])
        unsupported = set(self.reassessment.to_dict()["unsupported_subsystems"])
        self.assertTrue(set(VARIANTS.values()) <= unsupported)
        self.assertTrue({"mana_abilities", "triggered_abilities", "delayed_triggered_abilities", "emblems"} <= unsupported)

    def test_seven_of_seven_family_reference_coverage_never_claims_semantic_or_execution_closure(self):
        value = self.family.to_dict()
        self.assertEqual(value["status"], "OBJECT_CONTROL_EXCEPTION_FAMILY_PROJECTED")
        self.assertEqual(value["parent_reference"], "109.4")
        self.assertEqual(value["prior_unprojected_exceptions"], list(EXPECTED_REFERENCES))
        coverage = value["direct_family_coverage"]
        self.assertEqual(coverage["expected_count"], 7)
        self.assertEqual(coverage["projected_count"], 7)
        self.assertEqual(coverage["references"], list(EXPECTED_REFERENCES))
        self.assertEqual(coverage["status"], "DIRECT_EXCEPTION_FAMILY_REPRESENTED")
        self.assertFalse(coverage["exception_semantics_closed"])
        self.assertFalse(coverage["execution_ready"])
        findings = {row["rule_reference"]: row for row in value["exception_findings"]}
        self.assertEqual(set(findings), set(EXPECTED_REFERENCES))
        for reference, row in findings.items():
            with self.subTest(reference=reference):
                self.assertEqual(row["reference_status"], "EXCEPTION_REFERENCE_PROJECTED")
                self.assertEqual(row["unresolved_rules"], list(UNRESOLVED[reference]))
                self.assertEqual(row["dependency_closure"], "OPEN")
                self.assertFalse(row["exception_semantics_closed"])
                self.assertFalse(row["execution_ready"])
                self.assertEqual(row["execution_status"], "EXECUTION_BLOCKED")
        observation = value["source_quality_observation"]
        self.assertEqual(observation["source_anomaly_id"], self.records["source-anomaly.json"].identity)
        self.assertEqual(observation["effect_on_source_usability"], "SOURCE_REMAINS_USABLE")
        self.assertFalse(observation["correction_applied"])
        self.assertFalse(observation["intent_inferred"])
        self.assertFalse(observation["subrule_validity_inferred"])

    def test_parent1094_reference_enumeration_represented_but_dependencies_semantics_and_execution_open(self):
        parent = self.family.to_dict()["parent_reassessment"]
        self.assertEqual(parent["rule_reference"], "109.4")
        self.assertEqual(parent["original_projection_id"], ORIGINAL_ID)
        self.assertEqual(parent["direct_exception_enumeration"], "DIRECT_EXCEPTION_FAMILY_REPRESENTED")
        self.assertEqual(parent["projected_exception_references"], list(EXPECTED_REFERENCES))
        self.assertEqual(parent["unprojected_direct_exception_references"], [])
        self.assertEqual(parent["dependency_closure"], "OPEN")
        self.assertEqual(parent["variant_coverage"], "DESCRIBED_BUT_UNSUPPORTED")
        self.assertFalse(parent["required_primitives_available"])
        self.assertEqual(parent["complete_control_semantics"], "UNKNOWN")
        self.assertEqual(parent["semantic_closure"], "SEMANTIC_CLOSURE_OPEN")
        self.assertFalse(parent["execution_ready"])
        self.assertEqual(parent["execution_status"], "EXECUTION_BLOCKED")

    def test_control_reassessment_covers_all_required_rules_and_eight_control_dimensions(self):
        value = self.reassessment.to_dict()
        rows = {row["rule_reference"]: row for row in value["affected_rules"]}
        self.assertEqual(set(rows), {"108.4", "108.4a", "109.4", "110.2", "110.2a", "111.2", "112.2", *EXPECTED_REFERENCES})
        self.assertEqual(rows["109.4"]["direct_exceptions_represented"], list(EXPECTED_REFERENCES))
        for reference, row in rows.items():
            with self.subTest(reference=reference):
                self.assertEqual(row["dependency_closure"], "OPEN")
                self.assertEqual(row["semantic_closure"], "SEMANTIC_CLOSURE_OPEN")
                self.assertFalse(row["execution_ready"])
                self.assertEqual(row["execution_status"], "EXECUTION_BLOCKED")
                self.assertIn(row["component_projection_id"], {ORIGINAL_ID, DEPENDENCY_ID, self.projection.identity})
        dimensions = {row["dimension"]: row for row in value["control_dimensions"]}
        self.assertEqual(set(dimensions), {"ownership", "permanent_control", "spell_control", "token_control",
                                         "ability_control", "emblem_control", "variant_control", "control_change_and_effect_semantics"})
        for name, dimension in dimensions.items():
            with self.subTest(dimension=name):
                self.assertTrue(dimension["supporting_projected_references"])
                self.assertTrue(dimension["open_semantic_boundaries"])
                self.assertFalse(dimension["execution_supported"])
                self.assertFalse(dimension["implementation_primitive_available"])
                self.assertEqual(dimension["execution_status"], "EXECUTION_BLOCKED")
        self.assertEqual(value["overall_execution_readiness"], "BLOCKED")
        self.assertEqual(value["readiness_code"], "REAL_EXECUTION_PROFILE_NOT_READY")
        self.assertEqual(value["real_execution_primitives_available"], [])
        self.assertFalse(value["real_snapshot_instantiated"])
        self.assertFalse(value["real_profile_activated"])
        self.assertEqual(value["target_profile_id"], "magic-comprehensive-rules-20260925-v1")
        self.assertTrue({"COMPLETE_CONTROL_SEMANTICS_UNKNOWN", "REAL_EXECUTION_PRIMITIVES_ABSENT",
                         "CARD_EFFECT_SEMANTICS_ABSENT", "DETERMINISTIC_REAL_RUNTIME_VECTORS_ABSENT",
                         "OWNER_ACTIVATION_NOT_GRANTED", "UNRESOLVED_RULE:613"} <= set(value["blockers"]))

    def test_readonly_composite_has_exact39_units_and_three_separate_projection_identities(self):
        value = self.composite.to_dict()
        self.assertEqual(value["view_kind"], "DERIVED_READ_ONLY_THREE_PROJECTION_VIEW")
        self.assertEqual(value["foundational_projected_rule_count"], 20)
        self.assertEqual(value["dependency_projected_rule_count"], 12)
        self.assertEqual(value["object_control_projected_rule_count"], 7)
        self.assertEqual(value["total_projected_rule_count"], 39)
        self.assertEqual(value["projected_references"], list(ORIGINAL_REFERENCES + DEPENDENCY_REFERENCES + EXPECTED_REFERENCES))
        self.assertEqual(len(set(value["projected_references"])), 39)
        self.assertEqual(value["foundational_projection_id"], ORIGINAL_ID)
        self.assertEqual(value["foundational_package_id"], ORIGINAL_PACKAGE_ID)
        self.assertEqual(value["dependency_projection_id"], DEPENDENCY_ID)
        self.assertEqual(value["dependency_package_id"], DEPENDENCY_PACKAGE_ID)
        self.assertEqual(value["execution_design_package_id"], DESIGN_PACKAGE_ID)
        components = value["projection_components"]
        self.assertEqual(len(components), 3)
        self.assertEqual(len({row["projection_id"] for row in components}), 3)
        self.assertEqual([row["projection_id"] for row in components], [ORIGINAL_ID, DEPENDENCY_ID, self.projection.identity])
        self.assertTrue(all(not row["mutated"] for row in components))
        self.assertEqual(value["historical_acquisition_identity"], HISTORICAL_ID)
        self.assertEqual(value["execution_status"], "EXECUTION_BLOCKED")
        self.assertEqual(set(value["newly_unresolved_rules"]), set.union(*map(set, UNRESOLVED.values())))
        self.assertEqual(set(value["remaining_unresolved_rules"]), {"613"} | set.union(*map(set, UNRESOLVED.values())))

    def test_4007_family_and613_remain_unprojected_without_parent_reprojection(self):
        value = self.composite.to_dict()
        projected = value["projected_references"]
        families = value["open_exception_families"]
        self.assertEqual(set(families), {"400.7"})
        self.assertEqual(families["400.7"]["status"], "UNPROJECTED")
        self.assertEqual(tuple(families["400.7"]["references"]), DEFERRED_ZONE)
        self.assertFalse(set(projected) & set(DEFERRED_ZONE))
        self.assertNotIn("613", projected)
        self.assertNotIn("400.7l", projected)
        self.assertEqual(projected.count("109.4"), 1)
        represented = value["represented_exception_families"]["109.4"]
        self.assertEqual(represented["references"], list(EXPECTED_REFERENCES))
        self.assertFalse(represented["exception_semantics_closed"])
        self.assertFalse(represented["execution_ready"])

    def test_every_report_is_immutable_roundtrippable_and_never_grants_runtime_or_policy_authority(self):
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
                body = record_body(record)
                body["source_text"] = "Authored unapproved fixture sentinel."
                with self.assertRaises(GameplayContractError): type(record).create(body)
                with self.assertRaises(GameplayContractError):
                    type(record).from_json('{"game_id":"magic",' + record.serialize()[1:])

    def test_rehashing_cannot_promote_reference_coverage_to_execution_or_change_scope(self):
        for record, path, value in (
            (self.family, ("execution_authorized",), True),
            (self.family, ("direct_family_coverage", "execution_ready"), True),
            (self.family, ("parent_reassessment", "complete_control_semantics"), "CLOSED"),
            (self.family, ("exception_findings", 0, "exception_semantics_closed"), True),
            (self.reassessment, ("overall_execution_readiness",), "READY"),
            (self.reassessment, ("real_snapshot_instantiated",), True),
            (self.reassessment, ("real_profile_activated",), True),
            (self.reassessment, ("next_milestone", "authorized"), True),
            (self.composite, ("total_projected_rule_count",), 40),
            (self.composite, ("projection_components", 0, "mutated"), True),
        ):
            body = record_body(record)
            target = body
            for key in path[:-1]: target = target[key]
            target[path[-1]] = value
            with self.subTest(record=type(record).__name__, path=path), self.assertRaises(GameplayContractError):
                type(record).create(body)

    def test_exactly_one_next_milestone_is_recommended_but_not_authorized(self):
        next_milestone = self.reassessment.to_dict()["next_milestone"]
        self.assertFalse(next_milestone["authorized"])
        self.assertIn(next_milestone["candidate"], {
            "Core Control Dependency Projection", "Zone-Change Identity Exception Family Projection",
            "Ability / Continuous-Effect Dependency Design", "Casual Variant Control Dependency Projection"})
        self.assertTrue(next_milestone["rationale"])
        self.assertEqual(sum(item["eligible"] for item in next_milestone["evaluated_candidates"]), 1)


class ObjectControlPackageTests(unittest.TestCase):
    def copy_package(self):
        temporary = tempfile.TemporaryDirectory(prefix="mtglab-object-package-")
        self.addCleanup(temporary.cleanup)
        path = Path(temporary.name) / "relocated-review"
        shutil.copytree(PACKAGE, path)
        return path

    def test_package_relocates_deterministically_offline_readonly_without_source_or_runtime(self):
        relocated = self.copy_package()
        with ExitStack() as stack:
            for target in ("socket.socket", "gameplay_rules.source_evidence.artifacts.verify_local_artifact",
                           "gameplay_rules.projection.object_control_source.build_object_control_source",
                           "acquisition.framework.RawSnapshotStore.store", "pathlib.Path.write_bytes",
                           "pathlib.Path.write_text", "gameplay_rules.models.GameplayRulesSnapshot.create"):
                stack.enter_context(patch(target, side_effect=AssertionError("Forbidden offline verification dependency")))
            retained = load_object_control_package(PACKAGE, **PACKAGE_ROOTS)
            moved = load_object_control_package(relocated, **PACKAGE_ROOTS)
        self.assertEqual(retained, moved)
        self.assertEqual(set(retained), FILES - {"manifest.json"})
        raw = {name: (PACKAGE / name).read_bytes() for name in retained}
        self.assertEqual(json.loads((PACKAGE / "manifest.json").read_bytes()), package_manifest(retained, raw))

    def test_tamper_extra_txt_missing_links_noncanonical_oversized_and_directory_entries_fail(self):
        for mutation in ("tamper", "extra-source", "missing", "symlink", "hardlink", "whitespace", "oversized", "directory"):
            directory = self.copy_package()
            path = directory / "projection.json"
            if mutation == "tamper": path.write_bytes(path.read_bytes().replace(b"NON_EXECUTABLE", b"NOW_EXECUTABLE", 1))
            elif mutation == "extra-source": (directory / "source.txt").write_text("Authored private source sentinel.")
            elif mutation == "missing": (directory / "source-anomaly.json").unlink()
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
                load_object_control_package(directory, **PACKAGE_ROOTS)
            self.assertNotIn(str(directory), str(caught.exception))
            self.assertNotIn("Authored private source sentinel", str(caught.exception))

    def test_symlink_package_root_and_symlink_ancestor_fail(self):
        relocated = self.copy_package()
        for target in (relocated, relocated.parent):
            link = relocated.parent.parent / ("mtglab-object-link-" + target.name)
            self.addCleanup(link.unlink, missing_ok=True)
            link.symlink_to(target, target_is_directory=True)
            with self.subTest(target=target.name), self.assertRaises(GameplayContractError):
                load_object_control_package(link if target == relocated else link / relocated.name, **PACKAGE_ROOTS)

    def test_coherently_rehashed_false_finding_still_fails_independent_report_reproduction(self):
        records = dict(load_object_control_package(PACKAGE, **PACKAGE_ROOTS))
        body = record_body(records["family-closure-review.json"])
        body["exception_findings"][0]["unresolved_rules"] = ["613"]
        records["family-closure-review.json"] = type(records["family-closure-review.json"]).create(body)
        body = record_body(records["control-readiness-reassessment.json"])
        body["family_closure_review_id"] = records["family-closure-review.json"].identity
        records["control-readiness-reassessment.json"] = type(records["control-readiness-reassessment.json"]).create(body)
        body = record_body(records["composite-coverage.json"])
        body["family_closure_review_id"] = records["family-closure-review.json"].identity
        body["control_readiness_reassessment_id"] = records["control-readiness-reassessment.json"].identity
        records["composite-coverage.json"] = type(records["composite-coverage.json"]).create(body)
        raw = {name: (record.serialize() + "\n").encode() for name, record in records.items()}
        manifest = package_manifest(records, raw)
        directory = self.copy_package()
        for name, value in raw.items(): (directory / name).write_bytes(value)
        (directory / "manifest.json").write_text(deterministic_json(manifest) + "\n")
        with self.assertRaises(GameplayContractError):
            load_object_control_package(directory, **PACKAGE_ROOTS)

    def test_manifest_duplicate_nonfinite_unknown_and_permission_promotion_rejected(self):
        raw = (PACKAGE / "manifest.json").read_text()
        mutations = (
            '{"selected_rule_count":7,' + raw[1:],
            raw.replace('"selected_rule_count":7', '"selected_rule_count":NaN'),
            '{"unexpected":"fixture",' + raw[1:],
            raw.replace('"execution_authorized":false', '"execution_authorized":true'),
            raw.replace('"private_retention":"NOT_ESTABLISHED"', '"private_retention":"GRANTED"'),
        )
        for mutation in mutations:
            directory = self.copy_package()
            (directory / "manifest.json").write_text(mutation)
            with self.subTest(mutation=mutation[:70]), self.assertRaises(GameplayContractError):
                load_object_control_package(directory, **PACKAGE_ROOTS)

    def test_source_policy_and_all_permission_domains_remain_unchanged(self):
        manifest = json.loads((PACKAGE / "manifest.json").read_bytes())
        self.assertEqual(manifest["source_policy_clearance"], "not_granted")
        self.assertEqual(manifest["permissions"], {key: "NOT_ESTABLISHED" for key in
                         ("private_retention", "redistribution", "free_service", "commercial_service", "ai_export")})
        self.assertFalse(manifest["execution_authorized"])
        self.assertFalse(manifest["admission_eligible"])
        self.assertFalse(manifest["source_body_retained"])
        self.assertFalse(manifest["parent_reprojected"])
        self.assertEqual(manifest["additional_rules_projected"], [])
        self.assertEqual(manifest["selected_rule_count"], 7)
        self.assertEqual(manifest["composite_projected_rule_count"], 39)
        self.assertEqual(manifest["historical_acquisition_identity"], HISTORICAL_ID)

    def test_package_contains_exact_six_metadata_files_with_no_prose_examples_attachment_paths_or_txt(self):
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

    def test_projection_cannot_become_a_snapshot_profile_or_engine_input(self):
        retained = projection()
        self.assertFalse(hasattr(retained, "to_rules_snapshot"))
        self.assertFalse(hasattr(retained, "to_execution_profile"))
        with self.assertRaises(GameplayContractError): GameplayRulesSnapshot.from_dict(retained.to_dict())
        with self.assertRaises(GameplayContractError): load_rules_snapshot(PACKAGE / "projection.json")
        with self.assertRaises(GameplayContractError): GameplayRulesEngine(retained, ())

    def test_resolved_readonly_composite_exposes_all_three_literal_package_ids_without_mutating_records(self):
        records = load_object_control_package(PACKAGE, **PACKAGE_ROOTS)
        manifest = json.loads((PACKAGE / "manifest.json").read_bytes())
        before = {name: record.serialize() for name, record in records.items()}
        view = composite_coverage_view(records, manifest)
        self.assertEqual([row["package_id"] for row in view["projection_components"]],
                         [ORIGINAL_PACKAGE_ID, DEPENDENCY_PACKAGE_ID, manifest["package_id"]])
        self.assertEqual(len({row["projection_id"] for row in view["projection_components"]}), 3)
        self.assertEqual(view["total_projected_rule_count"], 39)
        self.assertFalse(view["execution_authorized"])
        self.assertFalse(view["real_rules_executable"])
        self.assertEqual(before, {name: record.serialize() for name, record in records.items()})
        changed = dict(manifest, package_id=OTHER_HASH)
        with self.assertRaises(GameplayContractError): composite_coverage_view(records, changed)

    def test_package_writer_is_append_only_and_reproduces_identical_metadata_bytes(self):
        records = load_object_control_package(PACKAGE, **PACKAGE_ROOTS)
        with tempfile.TemporaryDirectory(prefix="mtglab-object-output-") as directory:
            destination = Path(directory) / "new-review"
            manifest = write_object_control_package(destination, records)
            self.assertEqual(manifest, json.loads((PACKAGE / "manifest.json").read_bytes()))
            self.assertEqual({path.name: path.read_bytes() for path in destination.iterdir()},
                             {path.name: path.read_bytes() for path in PACKAGE.iterdir()})
            with self.assertRaises(GameplayContractError): write_object_control_package(destination, records)
            link = Path(directory) / "linked-review"
            link.symlink_to(destination, target_is_directory=True)
            with self.assertRaises(GameplayContractError): write_object_control_package(link, records)


if __name__ == "__main__":
    unittest.main()
