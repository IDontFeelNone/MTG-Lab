"""Offline evidence for the bounded, non-executable dependency projection.

The real owner-controlled CR document is never a fixture. Locator inputs below
are newly authored test sentences; they test exact physical source spans only.
Preservation digests bind canonical main 71652074fe5640d5b2cb4780c63f6b8bab5642d6
without requiring Git history or assuming a fixed mutable catalog census.
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

from activated_ability_preservation import is_design_addition
from evidence.contracts import deterministic_json
from gameplay_rules.capabilities import ENGINE_CONTRACT_VERSION, EXECUTION_PROFILE
from gameplay_rules.engine import GameplayRulesEngine
from gameplay_rules.errors import GameplayContractError
from gameplay_rules.models import GameplayRulesSnapshot
from gameplay_rules.projection import FoundationalProjection
from gameplay_rules.projection.dependency_contracts import DependencyProjection
from gameplay_rules.projection.dependency_package import load_dependency_package, package_manifest
from gameplay_rules.projection.dependency_reports import (
    CompositeCoverage, DirectClosureReview, ExecutionReadinessReassessment,
)
from gameplay_rules.projection.dependency_scope import SELECTED_REFERENCES
from gameplay_rules.projection.dependency_source import (
    _locate_dependency_anchors, build_dependency_projection,
    verify_dependency_projection_source,
)
from gameplay_rules.snapshots import load_rules_snapshot


ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "reference-reviews/gameplay-rules-foundational-dependencies"
ORIGINAL = ROOT / "reference-reviews/gameplay-rules-foundational-projection"
DESIGN = ROOT / "reference-reviews/gameplay-rules-execution-profile-design"
SOURCE_ROOTS = {
    "artifact_review_root": ROOT / "reference-reviews/gameplay-rules-artifact-verification",
    "source_root": ROOT / "reference-reviews/gameplay-rules-source-versioning",
    "discovery_root": ROOT / "reference-reviews/gameplay-rules-release-discovery-closure",
}
PACKAGE_ROOTS = {"projection_root": ORIGINAL, "design_root": DESIGN, **SOURCE_ROOTS}
EXPECTED_REFERENCES = (
    "104.3a", "111.2", "112.2", "112.2a", "113.10", "113.10a",
    "113.10b", "113.10c", "407.1", "407.2", "407.3", "407.4",
)
ORIGINAL_REFERENCES = (
    "101.1", "101.2", "101.2a", "101.3", "102.1", "102.2", "108.1",
    "108.3", "108.4", "108.4a", "109.1", "109.3", "109.4", "110.1",
    "110.2", "110.2a", "400.1", "400.2", "400.3", "400.7",
)
DIRECT_REFERENCES = {"104.3a", "111.2", "112.2", "113.10", "407"}
EXCEPTIONS = {
    "109.4": {"109.4" + suffix for suffix in "abcdefg"},
    "400.7": {"400.7" + suffix for suffix in "abcdefghijkm"},
}
ARTIFACT_HASH = "sha256:8d860e451f20f38865b725b42d82feb714c725373dd8f3b32b8652b3eeb070ca"
ORIGINAL_ID = "sha256:98bfd574c774a48aaaab4753eb8eb864dc7242effa011568f2ebf59c6a9ce6f7"
ORIGINAL_PACKAGE_ID = "sha256:22740145cf0ec457e0b297eba5ebed3d58054b6d16179bdd738a4f5ccc5463ea"
DESIGN_PACKAGE_ID = "sha256:f20d51ee190b4b23789208d0ae4bfa092d72aa23086fb01251d67b324ddb0687"
HISTORICAL_ID = "sha256:669d7db9ebcaf97853058fd62f408ce3c6596d5dae0ee72ff39d2ba9df56bb53"
OTHER_HASH = "sha256:" + "f" * 64
FILES = {"projection.json", "closure-review.json", "composite-coverage.json",
         "execution-readiness-reassessment.json", "manifest.json"}


def projection():
    return DependencyProjection.from_json((PACKAGE / "projection.json").read_bytes())


def projection_body(record):
    return {key: value for key, value in record.to_dict().items()
            if key not in {"schema_version", "projection_id"}}


def inventory(paths):
    files = set()
    for path in paths:
        files.update([path] if path.is_file() else
                     [item for item in path.rglob("*") if item.is_file()
                      and "__pycache__" not in item.parts and item.suffix != ".pyc"])
    result = []
    for path in sorted(files):
        # The successor guard independently pins every inherited byte.
        if is_design_addition(path):
            continue
        if path.is_symlink():
            raise AssertionError("Protected file must not be a symlink")
        raw = path.read_bytes()
        result.append({"path": path.relative_to(ROOT).as_posix(), "bytes": len(raw),
                       "sha256": hashlib.sha256(raw).hexdigest()})
    return result


class DependencyProjectionContractTests(unittest.TestCase):
    def setUp(self):
        self.projection = projection()

    def test_exact_twelve_selected_references_have_distinct_nonexecutable_identity(self):
        value = self.projection.to_dict()
        self.assertEqual(tuple(SELECTED_REFERENCES), EXPECTED_REFERENCES)
        self.assertEqual(value["selected_rule_count"], 12)
        self.assertEqual(tuple(rule["rule_reference"] for rule in value["rules"]), EXPECTED_REFERENCES)
        self.assertNotEqual(self.projection.identity, ORIGINAL_ID)
        self.assertEqual(value["projection_kind"], "NON_EXECUTABLE")
        self.assertEqual(value["status"], "PROJECTED_FOR_REVIEW")
        self.assertFalse(value["boundary_flags"]["real_rules_executable"])
        self.assertFalse(value["boundary_flags"]["source_body_retained"])

    def test_all_twelve_references_have_authored_semantics_and_explicit_review_boundaries(self):
        required = {"rule_reference", "topic", "paraphrase", "semantic_category", "concept_tags",
                    "dependencies", "unresolved_dependencies", "exception_subrule_boundaries",
                    "limitations", "coverage_state", "review_state", "source_anchor"}
        for reference, rule in zip(EXPECTED_REFERENCES, self.projection.to_dict()["rules"]):
            with self.subTest(reference=reference):
                self.assertEqual(rule["rule_reference"], reference)
                self.assertEqual(set(rule), required)
                self.assertTrue(rule["topic"])
                self.assertTrue(rule["paraphrase"])
                self.assertTrue(rule["semantic_category"])
                self.assertTrue(rule["concept_tags"])
                self.assertTrue(rule["limitations"])
                self.assertEqual(rule["coverage_state"], "SEMANTIC_CLOSURE_OPEN")
                self.assertEqual(rule["review_state"], "PROJECTED_FOR_REVIEW")

    def test_exact_source_lineage_and_all_twelve_anchor_release_bindings_are_pinned(self):
        value = self.projection.to_dict()
        binding = value["source_binding"]
        self.assertEqual(binding["artifact_hash"], ARTIFACT_HASH)
        self.assertEqual(binding["byte_length"], 977752)
        self.assertEqual(binding["effective_date"], "2026-09-25")
        self.assertEqual(binding["verification_result_id"],
                         "sha256:6289f9e138c248f33b950842fd079f9dc9d4be431a9ac8dc1effb4a18ec502b3")
        self.assertEqual(binding["correspondence_review_id"],
                         "sha256:7332e6517b1b28085bbee1fa76b8ecbc9cbe4148e261452449a308ba348d9def")
        previous_end = 0
        previous_line = 0
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

    def test_roundtrip_is_deeply_immutable_and_identity_bound(self):
        body = projection_body(self.projection)
        created = DependencyProjection.create(body)
        self.assertEqual(created, self.projection)
        self.assertEqual(DependencyProjection.from_json(created.serialize()), created)
        self.assertIs(created.verify(), created)
        body["rules"][0]["limitations"].append("Original caller mutation.")
        self.assertEqual(created.to_dict(), self.projection.to_dict())
        with self.assertRaises((FrozenInstanceError, AttributeError, TypeError)):
            created._payload = {}
        with self.assertRaises(TypeError):
            created.rules[0]["source_anchor"]["byte_start"] = 0
        with self.assertRaises(AttributeError):
            created.rules[0]["limitations"].append("Original forbidden mutation.")
        value = created.to_dict()
        value["projection_id"] = OTHER_HASH
        with self.assertRaises(GameplayContractError):
            DependencyProjection.from_dict(value)

    def test_rehashed_rule_expansion_omission_duplicate_and_replacement_fail(self):
        for mutation in ("count", "thirteenth", "missing", "duplicate", "613", "exception"):
            body = projection_body(self.projection)
            if mutation == "count": body["selected_rule_count"] = 13
            elif mutation == "thirteenth": body["rules"].append(body["rules"][-1])
            elif mutation == "missing": body["rules"].pop()
            elif mutation == "duplicate": body["rules"][1] = body["rules"][0]
            else: body["rules"][0]["rule_reference"] = "613" if mutation == "613" else "109.4a"
            with self.subTest(mutation=mutation), self.assertRaises(GameplayContractError):
                DependencyProjection.create(body)

    def test_rehashed_source_binding_anchor_or_authored_semantics_substitution_fails(self):
        for field, original in projection_body(self.projection)["source_binding"].items():
            body = projection_body(self.projection)
            body["source_binding"][field] = original + 1 if type(original) is int else OTHER_HASH
            with self.subTest(binding=field), self.assertRaises(GameplayContractError):
                DependencyProjection.create(body)
        for field, value in (("rule_reference", "613"), ("artifact_hash", OTHER_HASH),
                             ("effective_date", "2026-10-01"), ("byte_start", -1),
                             ("byte_start", True), ("byte_end", 977753),
                             ("line_number", 0), ("span_sha256", "invalid")):
            body = projection_body(self.projection)
            body["rules"][0]["source_anchor"][field] = value
            with self.subTest(anchor=field), self.assertRaises(GameplayContractError):
                DependencyProjection.create(body)
        body = projection_body(self.projection)
        body["rules"][0]["paraphrase"] = "Original replacement beyond retained review scope."
        with self.assertRaises(GameplayContractError):
            DependencyProjection.create(body)

    def test_official_prose_fields_unknown_fields_duplicate_keys_and_nonfinite_numbers_fail(self):
        for target in ("envelope", "rule", "anchor"):
            body = projection_body(self.projection)
            location = {"envelope": body, "rule": body["rules"][0],
                        "anchor": body["rules"][0]["source_anchor"]}[target]
            location["source_text"] = "Original unapproved fixture sentinel."
            with self.subTest(target=target), self.assertRaises(GameplayContractError):
                DependencyProjection.create(body)
        raw = self.projection.serialize()
        for malformed in ('{"selected_rule_count":12,' + raw[1:],
                          raw.replace('"selected_rule_count":12', '"selected_rule_count":NaN'),
                          raw.replace('"selected_rule_count":12', '"selected_rule_count":Infinity'),
                          b"\xff", "[]"):
            with self.subTest(raw=repr(malformed)[:50]), self.assertRaises(GameplayContractError):
                DependencyProjection.from_json(malformed)

    def test_613_is_explicitly_unresolved_and_never_projected(self):
        rules = {rule["rule_reference"]: rule for rule in self.projection.to_dict()["rules"]}
        self.assertNotIn("613", rules)
        downstream = rules["113.10c"]["unresolved_dependencies"]
        self.assertTrue(any(item["reference"] == "613" and item["status"] == "UNRESOLVED"
                            for item in downstream))
        self.assertEqual(rules["113.10c"]["coverage_state"], "SEMANTIC_CLOSURE_OPEN")
        self.assertFalse(set(rules) & set.union(*EXCEPTIONS.values()))


class DependencyProjectionSourceTests(unittest.TestCase):
    def synthetic_lines(self):
        return [(reference + (". " if index % 2 else " ") +
                 f"Original private locator sentinel {index}.").encode("utf-8")
                for index, reference in enumerate(EXPECTED_REFERENCES)]

    def test_anchor_locator_hashes_deterministic_physical_bytes_and_ignores_other_rules(self):
        header = "Original multibyte fixture ☃\r\n".encode("utf-8")
        lines = self.synthetic_lines()
        endings = [b"\r\n" if index % 2 else b"\n" for index in range(len(lines))]
        data = header + b"".join(line + ending for line, ending in zip(lines, endings))
        data += b"613 Original out-of-scope sentinel.\n109.4a Original exception sentinel.\n"
        anchors = _locate_dependency_anchors(data)
        self.assertEqual(_locate_dependency_anchors(data), anchors)
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

    def test_every_missing_or_duplicate_selected_rule_blocks(self):
        lines = self.synthetic_lines()
        for index, reference in enumerate(EXPECTED_REFERENCES):
            for mutation, selected in (("missing", lines[:index] + lines[index + 1:]),
                                       ("duplicate", lines + [lines[index]])):
                with self.subTest(reference=reference, mutation=mutation), \
                     self.assertRaises(GameplayContractError):
                    _locate_dependency_anchors(b"\n".join(selected))

    def test_selected_parent_and_child_references_are_distinct_source_matches(self):
        lines = self.synthetic_lines()
        for reference in ("112.2", "113.10"):
            selected = [line for line in lines if not line.startswith((reference + " ").encode())
                        and not line.startswith((reference + ". ").encode())]
            with self.subTest(reference=reference), self.assertRaises(GameplayContractError):
                _locate_dependency_anchors(b"\n".join(selected))

    def test_missing_wrong_sha_and_symlink_artifacts_block_without_network_retention_or_disclosure(self):
        with tempfile.TemporaryDirectory(prefix="mtglab-dependency-source-") as directory:
            root = Path(directory)
            wrong = root / "private-changed-source.txt"
            sentinel = b"Original private source sentinel; not an official rules document.\n"
            wrong.write_bytes(sentinel)
            wrong_same_length = root / "wrong-sha-correct-length.txt"
            wrong_same_length.write_bytes(b"x" * 977752)
            linked = root / "private-linked-source.txt"
            linked.symlink_to(wrong)
            for path in (root / "missing-source.txt", wrong, wrong_same_length, linked):
                with self.subTest(kind=path.name), \
                     patch("socket.socket", side_effect=AssertionError("network forbidden")), \
                     patch("acquisition.framework.RawSnapshotStore.store", side_effect=AssertionError("source retention forbidden")), \
                     self.assertRaises(GameplayContractError) as caught:
                    build_dependency_projection(path, **SOURCE_ROOTS)
                self.assertNotIn(str(root), str(caught.exception))
                self.assertNotIn(sentinel.decode().strip(), str(caught.exception))

    def test_transient_synthetic_locator_input_is_never_retained_as_source_prose(self):
        # Bypass only cryptographic intake to exercise the authored builder with
        # original synthetic sentences. This does not verify a real artifact.
        data = b"\n".join(self.synthetic_lines()) + b"\n"
        with patch("gameplay_rules.projection.dependency_source._verified_bytes", return_value=data), \
             patch("acquisition.framework.RawSnapshotStore.store", side_effect=AssertionError("source retention forbidden")):
            first = build_dependency_projection("synthetic-only.txt", **SOURCE_ROOTS)
            second = build_dependency_projection("synthetic-only.txt", **SOURCE_ROOTS)
        self.assertEqual(first, second)
        self.assertEqual(len(first.rules), 12)
        self.assertNotIn("Original private locator sentinel", first.serialize())
        for rule, source_line in zip(first.rules, self.synthetic_lines()):
            self.assertEqual(rule["source_anchor"]["span_sha256"],
                             "sha256:" + hashlib.sha256(source_line).hexdigest())

    def test_verification_requires_typed_projection_and_exact_reproduction(self):
        retained = projection()
        with self.assertRaises(GameplayContractError):
            verify_dependency_projection_source(retained.to_dict(), "unavailable.txt", **SOURCE_ROOTS)
        body = projection_body(retained)
        body["rules"][0]["source_anchor"]["span_sha256"] = OTHER_HASH
        changed = DependencyProjection.create(body)
        with patch("gameplay_rules.projection.dependency_source.build_dependency_projection", return_value=retained), \
             self.assertRaises(GameplayContractError):
            verify_dependency_projection_source(changed, "unavailable.txt", **SOURCE_ROOTS)


class DependencyClosureReportTests(unittest.TestCase):
    def setUp(self):
        self.records = load_dependency_package(PACKAGE, **PACKAGE_ROOTS)
        self.closure = self.records["closure-review.json"]
        self.composite = self.records["composite-coverage.json"]
        self.reassessment = self.records["execution-readiness-reassessment.json"]

    def test_all_five_original_direct_references_resolve_with_exact_selected_evidence(self):
        value = self.closure.to_dict()
        self.assertEqual(value["status"], "DIRECT_FOUNDATIONAL_DEPENDENCIES_PROJECTED")
        self.assertEqual(set(value["original_unresolved_references"]), DIRECT_REFERENCES)
        self.assertEqual(value["direct_references_resolved_count"], 5)
        rows = {row["reference"]: row for row in value["direct_resolutions"]}
        self.assertEqual(set(rows), DIRECT_REFERENCES)
        expected = {
            "104.3a": ["104.3a"], "111.2": ["111.2"], "112.2": ["112.2", "112.2a"],
            "113.10": ["113.10", "113.10a", "113.10b", "113.10c"],
            "407": ["407.1", "407.2", "407.3", "407.4"],
        }
        for reference, row in rows.items():
            with self.subTest(reference=reference):
                self.assertEqual(row["status"], "DIRECT_REFERENCE_RESOLVED")
                self.assertEqual(row["evidence_references"], expected[reference])
                self.assertEqual(row["dependency_projection_id"], self.records["projection.json"].identity)
                self.assertTrue(row["source_dependents"])
                self.assertEqual(row["semantic_closure"], "SEMANTIC_CLOSURE_OPEN")
                self.assertFalse(row["semantically_closed_for_execution"])
                self.assertEqual(row["execution_status"], "EXECUTION_BLOCKED")

    def test_new_613_rule_policy_variant_and_semantic_boundaries_remain_open(self):
        value = self.closure.to_dict()
        boundaries = {row["reference"]: row for row in value["newly_discovered_boundaries"]}
        self.assertEqual(value["remaining_unresolved_rules"], ["613"])
        self.assertEqual(boundaries["613"]["classification"], "UNRESOLVED_RULE")
        self.assertEqual(boundaries["613"]["status"], "UNRESOLVED")
        self.assertEqual(boundaries["613"]["required_by"], ["113.10c"])
        for reference in ("tournament_policy", "applicable_law", "deck_policy"):
            with self.subTest(reference=reference):
                self.assertEqual(boundaries[reference]["classification"], "EXTERNAL_POLICY")
                self.assertEqual(boundaries[reference]["status"], "OUT_OF_SCOPE")
        self.assertEqual(boundaries["ante_variant"]["classification"], "UNSUPPORTED_VARIANT")
        self.assertEqual(boundaries["ante_variant"]["status"], "OUT_OF_SCOPE")
        for reference in ("concession_transition", "token_creation", "spell_copy_and_casting",
                          "card_effect_interpretation", "ability_activation", "ability_modification",
                          "ante_state_and_ownership", "zone_inspection"):
            with self.subTest(reference=reference):
                self.assertEqual(boundaries[reference]["classification"], "FUTURE_SEMANTIC_PRIMITIVE")
                self.assertEqual(boundaries[reference]["status"], "OUT_OF_SCOPE")

    def test_readonly_composite_has_exactly_32_units_and_keeps_both_projection_identities(self):
        value = self.composite.to_dict()
        self.assertEqual(value["view_kind"], "DERIVED_READ_ONLY_TWO_PROJECTION_VIEW")
        self.assertEqual(value["original_projected_rule_count"], 20)
        self.assertEqual(value["new_projected_rule_count"], 12)
        self.assertEqual(value["total_projected_rule_count"], 32)
        self.assertEqual(value["projected_references"], list(ORIGINAL_REFERENCES + EXPECTED_REFERENCES))
        self.assertEqual(len(set(value["projected_references"])), 32)
        self.assertEqual(value["original_projection_id"], ORIGINAL_ID)
        self.assertEqual(value["original_package_id"], ORIGINAL_PACKAGE_ID)
        self.assertEqual(value["execution_design_package_id"], DESIGN_PACKAGE_ID)
        self.assertEqual(value["dependency_projection_id"], self.records["projection.json"].identity)
        self.assertNotEqual(value["dependency_projection_id"], ORIGINAL_ID)
        self.assertEqual(len(value["projection_components"]), 2)
        self.assertTrue(all(not component["mutated"] for component in value["projection_components"]))
        self.assertEqual(set(value["direct_dependencies_resolved"]), DIRECT_REFERENCES)
        self.assertEqual(value["remaining_unresolved_rules"], ["613"])
        self.assertEqual(value["historical_acquisition_identity"], HISTORICAL_ID)
        self.assertEqual(value["execution_status"], "EXECUTION_BLOCKED")

    def test_nineteen_deferred_exception_units_remain_unprojected_in_every_derived_view(self):
        selected = set(self.composite.to_dict()["projected_references"])
        for record in (self.composite, self.reassessment):
            families = record.to_dict()["open_exception_families"]
            self.assertEqual(set(families), set(EXCEPTIONS))
            for parent, expected in EXCEPTIONS.items():
                with self.subTest(record=type(record).__name__, parent=parent):
                    self.assertEqual(families[parent]["status"], "UNPROJECTED")
                    self.assertEqual(set(families[parent]["references"]), expected)
                    self.assertEqual(families[parent]["semantic_closure"], "SEMANTIC_CLOSURE_OPEN")
                    self.assertFalse(selected & expected)
            self.assertEqual(sum(len(row["references"]) for row in families.values()), 19)
        self.assertNotIn("400.7l", selected)
        self.assertNotIn("613", selected)
        self.assertNotIn("407", selected)

    def test_reassessment_resolves_direct_blockers_without_asserting_execution_closure(self):
        value = self.reassessment.to_dict()
        rows = {row["rule_reference"]: row for row in value["affected_rules"]}
        self.assertEqual(set(rows), {"101.1", "101.2", "101.2a", "108.3", "108.4", "110.2"})
        # PR #187 retained these targets after following its existing graph.
        # They include propagated unresolved targets, rather than only the
        # immediate source-rule edges, and must all be reassessed here.
        expected = {"101.1": {"104.3a"}, "101.2": {"113.10"}, "101.2a": {"113.10"},
                    "108.3": {"407"}, "108.4": {"112.2", "111.2", "407"},
                    "110.2": {"111.2", "407"}}
        for reference, resolved in expected.items():
            row = rows[reference]
            with self.subTest(reference=reference):
                self.assertEqual(set(row["direct_dependencies_resolved"]), resolved)
                self.assertEqual(set(row["previous_unresolved_dependencies"]), resolved)
                self.assertEqual(row["remaining_original_unresolved_dependencies"], [])
                self.assertEqual(row["dependency_closure"], "SEMANTIC_CLOSURE_OPEN")
                self.assertFalse(row["semantically_closed_for_execution"])
                self.assertFalse(row["execution_ready"])
                self.assertEqual(row["execution_status"], "EXECUTION_BLOCKED")
        self.assertIn("613", rows["101.2a"]["remaining_unresolved_rules"])
        self.assertEqual(value["overall_execution_readiness"], "BLOCKED")
        self.assertEqual(value["readiness_code"], "REAL_EXECUTION_PROFILE_NOT_READY")
        self.assertEqual(value["real_execution_primitives_available"], [])
        self.assertFalse(value["real_snapshot_instantiated"])
        self.assertFalse(value["real_profile_activated"])
        self.assertEqual(value["deterministic_real_runtime_vectors"], "ABSENT")
        self.assertTrue({"COMPLETE_SEMANTIC_CLOSURE_UNKNOWN", "REAL_EXECUTION_PRIMITIVES_ABSENT",
                         "DETERMINISTIC_REAL_RUNTIME_VECTORS_ABSENT", "OWNER_ACTIVATION_NOT_GRANTED",
                         "CARD_EFFECT_SEMANTICS_ABSENT", "UNRESOLVED_RULE:613"} <= set(value["blockers"]))

    def test_no_report_claims_execution_or_policy_permission_and_next_milestone_is_unauthorized(self):
        for record in (self.closure, self.composite, self.reassessment):
            value = record.to_dict()
            with self.subTest(record=type(record).__name__):
                self.assertFalse(value["execution_authorized"])
                self.assertFalse(value["real_rules_executable"])
                self.assertFalse(value["source_body_retained"])
                self.assertFalse(value["oracle_ingested"])
                self.assertEqual(value["source_policy_clearance"], "not_granted")
                self.assertEqual(value["owner_execution_approval"], "NOT_GRANTED")
                self.assertEqual(value["execution_design_package_id"], DESIGN_PACKAGE_ID)
                self.assertEqual(value["original_projection_id"], ORIGINAL_ID)
        next_milestone = self.reassessment.to_dict()["next_milestone"]
        self.assertFalse(next_milestone["authorized"])
        self.assertIn(next_milestone["candidate"], {
            "Object-Control Exception Family Projection", "Zone-Change Identity Exception Family Projection",
            "Ability / Continuous-Effect Dependency Design", "Core State Semantic Primitive Contracts"})
        self.assertTrue(next_milestone["rationale"])

    def test_report_records_roundtrip_and_reject_corrupt_identity_duplicate_or_extra_fields(self):
        for record in (self.closure, self.composite, self.reassessment):
            contract = type(record)
            with self.subTest(record=contract.__name__):
                self.assertIs(record.verify(), record)
                self.assertEqual(contract.from_json(record.serialize()), record)
                with self.assertRaises(TypeError): record._payload["execution_authorized"] = True
                value = record.to_dict()
                value[contract.ID_FIELD] = OTHER_HASH
                with self.assertRaises(GameplayContractError): contract.from_dict(value)
                value = record.to_dict()
                value["source_text"] = "Original unapproved fixture body."
                with self.assertRaises(GameplayContractError): contract.from_dict(value)
                with self.assertRaises(GameplayContractError):
                    contract.from_json('{"game_id":"magic",' + record.serialize()[1:])

    def test_rehashing_cannot_promote_review_evidence_to_semantic_or_runtime_authority(self):
        for record, path, value in (
            (self.closure, ("execution_authorized",), True),
            (self.closure, ("direct_references_resolved_count",), 4),
            (self.closure, ("direct_resolutions", 0, "semantically_closed_for_execution"), True),
            (self.closure, ("direct_resolutions", 0, "execution_status"), "EXECUTABLE"),
            (self.composite, ("total_projected_rule_count",), 33),
            (self.composite, ("projection_components", 0, "mutated"), True),
            (self.reassessment, ("overall_execution_readiness",), "READY"),
            (self.reassessment, ("real_snapshot_instantiated",), True),
            (self.reassessment, ("real_profile_activated",), True),
            (self.reassessment, ("next_milestone", "authorized"), True),
        ):
            body = {key: item for key, item in record.to_dict().items()
                    if key not in {"schema_version", record.ID_FIELD}}
            target = body
            for key in path[:-1]: target = target[key]
            target[path[-1]] = value
            with self.subTest(record=type(record).__name__, path=path), self.assertRaises(GameplayContractError):
                type(record).create(body)


class DependencyPackageTests(unittest.TestCase):
    def copy_package(self):
        temporary = tempfile.TemporaryDirectory(prefix="mtglab-dependency-package-")
        self.addCleanup(temporary.cleanup)
        path = Path(temporary.name) / "relocated-review"
        shutil.copytree(PACKAGE, path)
        return path

    def test_package_relocates_offline_readonly_without_source_retention_or_runtime_construction(self):
        relocated = self.copy_package()
        with ExitStack() as stack:
            for target in ("socket.socket", "gameplay_rules.source_evidence.artifacts.verify_local_artifact",
                           "gameplay_rules.projection.dependency_source.build_dependency_projection",
                           "acquisition.framework.RawSnapshotStore.store", "pathlib.Path.write_bytes",
                           "pathlib.Path.write_text", "gameplay_rules.models.GameplayRulesSnapshot.create"):
                stack.enter_context(patch(target, side_effect=AssertionError("Forbidden offline verification dependency")))
            retained = load_dependency_package(PACKAGE, **PACKAGE_ROOTS)
            moved = load_dependency_package(relocated, **PACKAGE_ROOTS)
        self.assertEqual(retained, moved)
        self.assertEqual(set(retained), FILES - {"manifest.json"})
        raw = {name: (PACKAGE / name).read_bytes() for name in retained}
        self.assertEqual(json.loads((PACKAGE / "manifest.json").read_bytes()), package_manifest(retained, raw))

    def test_tamper_extra_source_missing_symlink_whitespace_and_oversized_files_fail_closed(self):
        for mutation in ("tamper", "extra-source", "missing", "symlink", "hardlink", "whitespace", "oversized"):
            directory = self.copy_package()
            path = directory / "projection.json"
            if mutation == "tamper": path.write_bytes(path.read_bytes().replace(b"NON_EXECUTABLE", b"NOW_EXECUTABLE", 1))
            elif mutation == "extra-source": (directory / "source.txt").write_text("Original private source sentinel.")
            elif mutation == "missing": (directory / "closure-review.json").unlink()
            elif mutation == "symlink":
                path.unlink()
                path.symlink_to(PACKAGE / "projection.json")
            elif mutation == "hardlink":
                held = directory.parent / "held-projection.json"
                path.rename(held)
                path.hardlink_to(held)
            elif mutation == "whitespace": path.write_bytes(path.read_bytes() + b"\n")
            else: path.write_bytes(b" " * 128001)
            with self.subTest(mutation=mutation), self.assertRaises(GameplayContractError) as caught:
                load_dependency_package(directory, **PACKAGE_ROOTS)
            self.assertNotIn(str(directory), str(caught.exception))
            self.assertNotIn("Original private source sentinel", str(caught.exception))

    def test_coherently_rehashed_finding_changes_fail_source_bound_report_reproduction(self):
        records = dict(load_dependency_package(PACKAGE, **PACKAGE_ROOTS))

        def body(record):
            return {key: value for key, value in record.to_dict().items()
                    if key not in {"schema_version", record.ID_FIELD}}

        closure_body = body(records["closure-review.json"])
        closure_body["direct_resolutions"][0]["source_dependents"] = ["108.4"]
        records["closure-review.json"] = DirectClosureReview.create(closure_body)
        composite_body = body(records["composite-coverage.json"])
        composite_body["closure_review_id"] = records["closure-review.json"].identity
        records["composite-coverage.json"] = CompositeCoverage.create(composite_body)
        reassessment_body = body(records["execution-readiness-reassessment.json"])
        reassessment_body["closure_review_id"] = records["closure-review.json"].identity
        reassessment_body["composite_coverage_id"] = records["composite-coverage.json"].identity
        records["execution-readiness-reassessment.json"] = ExecutionReadinessReassessment.create(reassessment_body)
        raw = {name: (record.serialize() + "\n").encode("utf-8") for name, record in records.items()}
        manifest = package_manifest(records, raw)
        directory = self.copy_package()
        for name, value in raw.items(): (directory / name).write_bytes(value)
        (directory / "manifest.json").write_text(deterministic_json(manifest) + "\n")
        with self.assertRaises(GameplayContractError):
            load_dependency_package(directory, **PACKAGE_ROOTS)

    def test_manifest_duplicate_nonfinite_unknown_or_permission_promotion_is_rejected(self):
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
                load_dependency_package(directory, **PACKAGE_ROOTS)

    def test_source_policy_and_all_five_permission_domains_remain_unestablished(self):
        manifest = json.loads((PACKAGE / "manifest.json").read_bytes())
        self.assertEqual(manifest["source_policy_clearance"], "not_granted")
        self.assertEqual(manifest["permissions"], {
            key: "NOT_ESTABLISHED" for key in
            ("private_retention", "redistribution", "free_service", "commercial_service", "ai_export")})
        self.assertFalse(manifest["execution_authorized"])
        self.assertFalse(manifest["admission_eligible"])
        self.assertFalse(manifest["source_body_retained"])
        self.assertEqual(manifest["additional_rules_projected"], [])

    def test_package_only_contains_metadata_with_no_source_prose_fields_paths_or_txt(self):
        self.assertEqual({path.name for path in PACKAGE.iterdir()}, FILES)
        forbidden = {"source_text", "rule_text", "official_text", "oracle_text", "raw_source",
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

    def test_projection_cannot_become_a_real_snapshot_profile_or_engine_input(self):
        retained = projection()
        self.assertFalse(hasattr(retained, "to_rules_snapshot"))
        self.assertFalse(hasattr(retained, "to_execution_profile"))
        with self.assertRaises(GameplayContractError):
            GameplayRulesSnapshot.from_dict(retained.to_dict())
        with self.assertRaises(GameplayContractError):
            load_rules_snapshot(PACKAGE / "projection.json")
        with self.assertRaises(GameplayContractError):
            GameplayRulesEngine(retained, ())


class DependencyPreservationTests(unittest.TestCase):
    def test_all_nonprojection_source_bytes_preserve_runtime_primitives_policy_writer_and_intelligence(self):
        # All production source outside the one authorized review/projection
        # directory remains canonical, including engine, semantics and writer.
        paths = [path for path in (ROOT / "src").iterdir()
                 if path.name != "gameplay_rules"]
        paths.extend(path for path in (ROOT / "src/gameplay_rules").iterdir()
                     if path.name not in {"projection", "casting_design", "mana_ability_design", "mana_dependency_design", "__pycache__"})
        value = inventory(paths)
        self.assertEqual(len(value), 256)
        self.assertEqual(hashlib.sha256(deterministic_json(value).encode()).hexdigest(),
                         "191d9a47b9b9de75dd25cddb4b5497a06c7981858d17f1ecba813610073ee8f1")

    def test_pr187_design_package_bytes_and_identity_remain_exact(self):
        value = inventory([DESIGN])
        self.assertEqual(len(value), 6)
        self.assertEqual(hashlib.sha256(deterministic_json(value).encode()).hexdigest(),
                         "366a70ba5bc368577cb51eb9c71478fe9285f05b689461bff96e927600ae4b4a")
        manifest = json.loads((DESIGN / "manifest.json").read_bytes())
        self.assertEqual(manifest["package_id"], DESIGN_PACKAGE_ID)

    def test_original_twenty_rule_package_bytes_and_identities_remain_exact(self):
        value = inventory([ORIGINAL])
        self.assertEqual(len(value), 2)
        self.assertEqual(hashlib.sha256(deterministic_json(value).encode()).hexdigest(),
                         "0e88e8baac7171f2a390f8a46913952a4a7a57fe7605ece47572c6a9a5fff5f2")
        manifest = json.loads((ORIGINAL / "manifest.json").read_bytes())
        self.assertEqual(manifest["package_id"], ORIGINAL_PACKAGE_ID)
        self.assertEqual(manifest["projection_id"], ORIGINAL_ID)
        old = FoundationalProjection.from_json((ORIGINAL / "projection.json").read_bytes())
        self.assertEqual(old.identity, ORIGINAL_ID)
        self.assertEqual(tuple(rule["rule_reference"] for rule in old.rules), ORIGINAL_REFERENCES)

    def test_architecture_v13_decisions_and_historical_acquisition_identity_are_preserved(self):
        paths = [ROOT / "docs" / name for name in (
            "ARCHITECTURE.md", "DECISIONS.md", "DECISION_ENGINE.md", "DECISION_INTELLIGENCE.md",
            "DECISION_INTELLIGENCE_ASSESSMENT_2026_08_12.md")]
        value = inventory(paths)
        self.assertEqual(len(value), 5)
        self.assertEqual(hashlib.sha256(deterministic_json(value).encode()).hexdigest(),
                         "92054f7315fabe2ac30c6dda0429ebb47bf5cc92f08998de579c5fc1140e98a2")
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

    def test_dependency_modules_do_not_import_or_instantiate_gameplay_network_card_or_policy_engines(self):
        forbidden_imports = {"socket", "http", "urllib", "requests", "subprocess", "simulation",
                             "providers", "external_ingestion", "market", "production_evidence",
                             "repository", "random", "secrets"}
        forbidden_runtime = {"GameplayRulesSnapshot", "CardGameplaySemantics", "GameState", "GameAction",
                             "LegalityResult", "GameTransition", "GameplayRulesEngine", "RawSnapshotStore"}
        paths = list((ROOT / "src/gameplay_rules/projection").glob("dependency_*.py"))
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
                        self.assertNotIn(node.name, {"to_rules_snapshot", "activate_profile", "execute_ante"})
                    if isinstance(node, ast.Call):
                        root = node.func
                        while isinstance(root, ast.Attribute): root = root.value
                        if isinstance(root, ast.Name):
                            self.assertNotIn(root.id, forbidden_runtime | {"exec", "eval", "compile"})


if __name__ == "__main__":
    unittest.main()
