"""Review-only projection regressions; no official source document is a fixture.

Retained metadata can be checked offline. Synthetic locator inputs below contain
only original test sentences and never stand in for verified official bytes.
"""
from dataclasses import FrozenInstanceError
import hashlib
import io
import json
from pathlib import Path
import shutil
import tempfile
import unittest
from contextlib import redirect_stdout
from unittest.mock import patch

from evidence.contracts import deterministic_json, sha256_identity
from gameplay_rules.errors import GameplayContractError
from gameplay_rules.models import GameplayRulesSnapshot
from gameplay_rules.projection import FoundationalProjection, load_projection_package
from gameplay_rules.projection.__main__ import main
from gameplay_rules.projection.package import package_manifest
from gameplay_rules.projection.source import _locate_anchors, build_projection, verify_projection_source
from gameplay_rules.snapshots import load_rules_snapshot
from gameplay_rules.source_evidence.artifact_review import verify_artifact_review_package
from gameplay_rules.source_evidence.closure import verify_discovery_package
from gameplay_rules.source_evidence.review import verify_review_package


ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "reference-reviews/gameplay-rules-foundational-projection"
SOURCE = ROOT / "reference-reviews/gameplay-rules-source-versioning"
DISCOVERY = ROOT / "reference-reviews/gameplay-rules-release-discovery-closure"
ARTIFACT_REVIEW = ROOT / "reference-reviews/gameplay-rules-artifact-verification"
ROOTS = {"artifact_review_root": ARTIFACT_REVIEW, "source_root": SOURCE,
         "discovery_root": DISCOVERY}
EXPECTED_REFERENCES = (
    "101.1", "101.2", "101.2a", "101.3", "102.1", "102.2",
    "108.1", "108.3", "108.4", "108.4a", "109.1", "109.3", "109.4",
    "110.1", "110.2", "110.2a", "400.1", "400.2", "400.3", "400.7",
)
ARTIFACT_HASH = "sha256:8d860e451f20f38865b725b42d82feb714c725373dd8f3b32b8652b3eeb070ca"
OTHER_HASH = "sha256:" + "f" * 64


class FoundationalProjectionContractTests(unittest.TestCase):
    def setUp(self):
        self.projection = FoundationalProjection.from_json((PACKAGE / "projection.json").read_bytes())

    def body(self):
        return {key: value for key, value in self.projection.to_dict().items()
                if key not in {"schema_version", "projection_id"}}

    def test_exact_twenty_authorized_references_and_source_lineage_are_pinned(self):
        value = self.projection.to_dict()
        self.assertEqual(value["selected_rule_count"], 20)
        self.assertEqual(tuple(rule["rule_reference"] for rule in value["rules"]), EXPECTED_REFERENCES)
        self.assertEqual(value["source_binding"], {
            "artifact_hash": ARTIFACT_HASH, "byte_length": 977752, "effective_date": "2026-09-25",
            "verification_result_id": "sha256:6289f9e138c248f33b950842fd079f9dc9d4be431a9ac8dc1effb4a18ec502b3",
            "correspondence_review_id": "sha256:7332e6517b1b28085bbee1fa76b8ecbc9cbe4148e261452449a308ba348d9def",
            "artifact_review_package_id": "sha256:b5ad8b6f59c0311a33726e1733dc9bb239804bd0ab387ed789caf0d870aba36a",
            "selection_id": "sha256:5f22a1aa78b5fd2ec5a0ae7d942d6065a8b065a5cc4ee79db300514a5ebe5f63",
        })
        self.assertEqual(value["projection_kind"], "NON_EXECUTABLE")
        self.assertFalse(value["boundary_flags"]["real_rules_executable"])
        self.assertFalse(value["boundary_flags"]["admission_eligible"])
        self.assertEqual(value["authorization"]["source_policy_clearance"], "not_granted")

    def test_roundtrip_identity_and_deep_immutability(self):
        body = self.body()
        created = FoundationalProjection.create(body)
        self.assertEqual(created, self.projection)
        self.assertEqual(FoundationalProjection.from_json(created.serialize()), created)
        self.assertIs(created.verify(), created)
        self.assertEqual(created.serialize(), self.projection.serialize())
        body["rules"][0]["limitations"].append("Original caller edit.")
        copy = created.to_dict()
        copy["rules"][0]["source_anchor"]["byte_start"] = 0
        self.assertEqual(created.to_dict(), self.projection.to_dict())
        with self.assertRaises((FrozenInstanceError, AttributeError, TypeError)):
            created._payload = {}
        with self.assertRaises(TypeError):
            created.rules[0]["source_anchor"]["byte_start"] = 0
        with self.assertRaises(AttributeError):
            created.rules[0]["limitations"].append("Forbidden nested edit.")

    def test_corrupt_identity_duplicate_keys_nonfinite_and_unknown_fields_are_rejected(self):
        value = self.projection.to_dict()
        value["projection_id"] = OTHER_HASH
        with self.assertRaises(GameplayContractError):
            FoundationalProjection.from_dict(value)
        serialized = self.projection.serialize()
        bad_json = [
            '{"selected_rule_count":20,' + serialized[1:],
            serialized.replace('"selected_rule_count":20', '"selected_rule_count":NaN'),
            serialized.replace('"selected_rule_count":20', '"selected_rule_count":Infinity'),
            b"\xff", "[]",
        ]
        for raw in bad_json:
            with self.subTest(raw=repr(raw)[:60]), self.assertRaises(GameplayContractError):
                FoundationalProjection.from_json(raw)
        for target in ("envelope", "rule", "anchor"):
            body = self.body()
            location = {"envelope": body, "rule": body["rules"][0],
                        "anchor": body["rules"][0]["source_anchor"]}[target]
            location["source_text"] = "Original unapproved fixture field."
            with self.subTest(target=target), self.assertRaises(GameplayContractError):
                FoundationalProjection.create(body)

    def test_rehashed_changes_cannot_expand_rules_or_replace_authored_content(self):
        for mutation in ("count", "missing", "duplicate", "replacement", "paraphrase", "executable", "permission"):
            body = self.body()
            if mutation == "count": body["selected_rule_count"] = 19
            elif mutation == "missing": body["rules"].pop()
            elif mutation == "duplicate": body["rules"][1] = body["rules"][0]
            elif mutation == "replacement": body["rules"][0]["rule_reference"] = "104.3a"
            elif mutation == "paraphrase": body["rules"][0]["paraphrase"] = "Original unauthorized replacement."
            elif mutation == "executable": body["boundary_flags"]["real_rules_executable"] = True
            else: body["authorization"]["source_policy_clearance"] = "granted"
            with self.subTest(mutation=mutation), self.assertRaises(GameplayContractError):
                FoundationalProjection.create(body)

    def test_every_source_binding_field_resists_rehashed_substitution(self):
        for field, original in self.body()["source_binding"].items():
            body = self.body()
            body["source_binding"][field] = original + 1 if type(original) is int else OTHER_HASH
            with self.subTest(field=field), self.assertRaises(GameplayContractError):
                FoundationalProjection.create(body)

    def test_unresolved_dependencies_and_all_unprojected_exceptions_stay_explicit(self):
        graph = self.projection.to_dict()["graph"]
        statuses = {node["rule_reference"]: node["status"] for node in graph["nodes"]}
        self.assertEqual({ref for ref, status in statuses.items() if status == "PROJECTED"},
                         set(EXPECTED_REFERENCES))
        self.assertEqual({ref for ref, status in statuses.items() if status == "UNRESOLVED"},
                         {"104.3a", "111.2", "112.2", "113.10", "407"})
        exceptions = {"109.4": {f"109.4{letter}" for letter in "abcdefg"},
                      "400.7": {f"400.7{letter}" for letter in "abcdefghijkm"}}
        self.assertEqual({ref for ref, status in statuses.items() if status == "UNPROJECTED_EXCEPTION"},
                         set.union(*exceptions.values()))
        for parent, expected in exceptions.items():
            edges = [edge for edge in graph["edges"]
                     if edge["from_reference"] == parent and edge["relation"] == "EXCEPTION"]
            self.assertEqual({edge["to_reference"] for edge in edges}, expected)
            self.assertEqual({edge["status"] for edge in edges}, {"UNPROJECTED_EXCEPTION"})
        self.assertNotIn("400.7l", statuses)

    def test_rehashing_graph_cannot_omit_or_resolve_a_boundary(self):
        for mutation in ("missing_exception_node", "missing_exception_edge", "resolved_dependency", "missing_unsupported"):
            body = self.body()
            if mutation == "missing_exception_node":
                body["graph"]["nodes"] = [node for node in body["graph"]["nodes"]
                                          if node["rule_reference"] != "109.4g"]
            elif mutation == "missing_exception_edge":
                body["graph"]["edges"] = [edge for edge in body["graph"]["edges"]
                                          if edge["to_reference"] != "400.7m"]
            elif mutation == "resolved_dependency":
                next(node for node in body["graph"]["nodes"]
                     if node["rule_reference"] == "111.2")["status"] = "PROJECTED"
            else: body["unsupported_dimensions"].remove("simulation")
            with self.subTest(mutation=mutation), self.assertRaises(GameplayContractError):
                FoundationalProjection.create(body)

    def test_invalid_source_span_types_bounds_and_overlap_fail_closed(self):
        mutations = [("byte_start", -1), ("byte_start", True), ("byte_start", 1.0),
                     ("byte_end", 977753), ("byte_end", 0), ("line_number", 0),
                     ("line_number", "1"), ("span_sha256", "invalid"),
                     ("rule_reference", "104.3a"), ("artifact_hash", OTHER_HASH),
                     ("span_policy", "NORMALIZED_TEXT")]
        for field, value in mutations:
            body = self.body()
            body["rules"][0]["source_anchor"][field] = value
            with self.subTest(field=field, value=value), self.assertRaises(GameplayContractError):
                FoundationalProjection.create(body)
        for mutation in ("empty", "overlap", "line_order"):
            body = self.body()
            first, second = [rule["source_anchor"] for rule in body["rules"][:2]]
            if mutation == "empty": first["byte_end"] = first["byte_start"]
            elif mutation == "overlap": second["byte_start"] = first["byte_end"] - 1
            else: second["line_number"] = first["line_number"]
            with self.subTest(mutation=mutation), self.assertRaises(GameplayContractError):
                FoundationalProjection.create(body)


class FoundationalProjectionSourceTests(unittest.TestCase):
    def synthetic_lines(self):
        return [(reference + (". " if index % 2 else " ") +
                 f"Original project-authored locator fixture {index}.").encode("utf-8")
                for index, reference in enumerate(EXPECTED_REFERENCES)]

    def test_locator_hashes_exact_physical_bytes_without_line_terminators(self):
        lines = self.synthetic_lines()
        header = "Original multibyte fixture ☃\r\n".encode("utf-8")
        endings = [b"\r\n" if index % 2 else b"\n" for index in range(len(lines))]
        data = header + b"".join(line + ending for line, ending in zip(lines, endings))
        anchors = _locate_anchors(data)
        offset = len(header)
        for index, (anchor, line, ending) in enumerate(zip(anchors, lines, endings)):
            self.assertEqual(anchor["rule_reference"], EXPECTED_REFERENCES[index])
            self.assertEqual(anchor["line_number"], index + 2)
            self.assertEqual((anchor["byte_start"], anchor["byte_end"]), (offset, offset + len(line)))
            self.assertEqual(data[anchor["byte_start"]:anchor["byte_end"]], line)
            self.assertEqual(anchor["span_sha256"], "sha256:" + hashlib.sha256(line).hexdigest())
            self.assertNotIn("text", anchor)
            offset += len(line) + len(ending)

    def test_locator_rejects_missing_or_duplicate_selected_lines(self):
        lines = self.synthetic_lines()
        for data in (b"\n".join(lines[:-1]), b"\n".join(lines + [lines[0]])):
            with self.assertRaises(GameplayContractError):
                _locate_anchors(data)
        # A subordinate selected reference must not satisfy its parent's slot.
        with self.assertRaises(GameplayContractError):
            _locate_anchors(b"\n".join(line for line in lines if line != lines[1]))

    def test_missing_changed_or_symlink_source_is_rejected_without_path_or_body_disclosure(self):
        with tempfile.TemporaryDirectory(prefix="mtglab-projection-source-test-") as directory:
            root = Path(directory)
            changed = root / "changed-source.txt"
            sentinel = b"Original private fixture sentinel, not official source.\n"
            changed.write_bytes(sentinel)
            linked = root / "linked-source.txt"
            linked.symlink_to(changed)
            for path in (root / "unavailable-source.txt", changed, linked):
                with self.subTest(kind=path.name), \
                     patch("socket.socket", side_effect=AssertionError("network forbidden")), \
                     patch("acquisition.framework.RawSnapshotStore.store", side_effect=AssertionError("source retention forbidden")), \
                     self.assertRaises(GameplayContractError) as caught:
                    build_projection(path, **ROOTS)
                self.assertNotIn(str(root), str(caught.exception))
                self.assertNotIn(sentinel.decode().strip(), str(caught.exception))

    def test_source_verification_requires_typed_projection_and_exact_reproduction(self):
        projection = FoundationalProjection.from_json((PACKAGE / "projection.json").read_bytes())
        with self.assertRaises(GameplayContractError):
            verify_projection_source(projection.to_dict(), "unavailable-source.txt", **ROOTS)
        altered = projection.to_dict()
        altered.pop("schema_version")
        altered.pop("projection_id")
        altered["rules"][0]["source_anchor"]["span_sha256"] = OTHER_HASH
        altered_projection = FoundationalProjection.create(altered)
        with patch("gameplay_rules.projection.source.build_projection", return_value=projection), \
             self.assertRaises(GameplayContractError):
            verify_projection_source(altered_projection, "unavailable-source.txt", **ROOTS)


class FoundationalProjectionPackageTests(unittest.TestCase):
    def copy_package(self):
        temporary = tempfile.TemporaryDirectory(prefix="mtglab-projection-package-test-")
        self.addCleanup(temporary.cleanup)
        path = Path(temporary.name) / "review"
        shutil.copytree(PACKAGE, path)
        return path

    def cli(self, *extra):
        output = io.StringIO()
        args = [str(PACKAGE), "--artifact-review-root", str(ARTIFACT_REVIEW),
                "--source-root", str(SOURCE), "--discovery-root", str(DISCOVERY), *extra]
        with redirect_stdout(output):
            code = main(args)
        return code, json.loads(output.getvalue()), output.getvalue()

    def test_offline_integrity_and_relocation_need_no_source_network_or_writes(self):
        relocated = self.copy_package()
        with patch("socket.socket", side_effect=AssertionError("network forbidden")), \
             patch("gameplay_rules.source_evidence.artifacts.verify_local_artifact",
                   side_effect=AssertionError("external official source unavailable in CI")), \
             patch("pathlib.Path.write_text", side_effect=AssertionError("read-only verification")), \
             patch("pathlib.Path.write_bytes", side_effect=AssertionError("read-only verification")):
            first = load_projection_package(PACKAGE, **ROOTS)
            self.assertEqual(load_projection_package(relocated, **ROOTS), first)
        raw = (PACKAGE / "projection.json").read_bytes()
        manifest = json.loads((PACKAGE / "manifest.json").read_bytes())
        self.assertEqual(manifest, package_manifest(first, raw))
        self.assertEqual(manifest["files"]["projection.json"]["bytes"], len(raw))
        self.assertFalse(manifest["source_body_retained"])
        self.assertFalse(manifest["real_rules_executable"])

    def test_package_inventory_excludes_source_bodies_and_absolute_local_paths(self):
        self.assertEqual({path.name for path in PACKAGE.iterdir()}, {"manifest.json", "projection.json"})
        for path in PACKAGE.iterdir():
            raw = path.read_bytes()
            self.assertLess(len(raw), 128000)
            for marker in (b"/tmp/", b"/workspace/", b"codex-remote-attachments", b"%PDF", b"MagicCompRules"):
                with self.subTest(path=path.name, marker=marker):
                    self.assertNotIn(marker, raw)
            json.loads(raw)

    def test_tampered_extra_missing_symlink_or_noncanonical_package_is_rejected(self):
        for mutation in ("tampered", "extra", "missing", "symlink", "whitespace"):
            root = self.copy_package()
            target = root / "projection.json"
            if mutation == "tampered": target.write_bytes(target.read_bytes() + b"x")
            elif mutation == "extra": (root / "unexpected-source.txt").write_text("Original fixture sentinel.")
            elif mutation == "missing": (root / "manifest.json").unlink()
            elif mutation == "symlink":
                target.unlink()
                target.symlink_to(PACKAGE / "projection.json")
            else: target.write_bytes(target.read_bytes() + b"\n")
            with self.subTest(mutation=mutation), self.assertRaises(GameplayContractError):
                load_projection_package(root, **ROOTS)

    def test_manifest_duplicate_nonfinite_unknown_and_rehashed_lineage_edits_fail(self):
        for mutation in ("duplicate", "nonfinite", "unknown", "lineage"):
            root = self.copy_package()
            path = root / "manifest.json"
            value = json.loads(path.read_bytes())
            if mutation == "duplicate": raw = '{"selected_rule_count":20,' + deterministic_json(value)[1:]
            elif mutation == "nonfinite": raw = deterministic_json(value).replace('"selected_rule_count":20', '"selected_rule_count":NaN')
            else:
                value["unexpected"] = False if mutation == "unknown" else None
                if mutation == "lineage":
                    value.pop("unexpected")
                    value["prior_artifact_review_package_id"] = OTHER_HASH
                body = {key: item for key, item in value.items() if key != "package_id"}
                value["package_id"] = "sha256:" + sha256_identity({
                    "domain": value["schema_version"], "content": body})
                raw = deterministic_json(value)
            path.write_text(raw)
            with self.subTest(mutation=mutation), self.assertRaises(GameplayContractError):
                load_projection_package(root, **ROOTS)

    def test_projection_cannot_be_loaded_as_executable_gameplay_rules(self):
        projection = load_projection_package(PACKAGE, **ROOTS)
        with self.assertRaises(GameplayContractError):
            GameplayRulesSnapshot.from_dict(projection.to_dict())
        with self.assertRaises(GameplayContractError):
            load_rules_snapshot(PACKAGE / "projection.json")

    def test_cli_distinguishes_offline_integrity_from_unavailable_source_proof(self):
        with patch("socket.socket", side_effect=AssertionError("network forbidden")):
            code, result, _ = self.cli()
        self.assertEqual(code, 0)
        self.assertEqual(result["status"], "VERIFIED_PROJECTION_PACKAGE_INTEGRITY")
        self.assertEqual(result["selected_rule_count"], 20)
        self.assertFalse(result["source_spans_reverified"])
        self.assertFalse(result["real_rules_executable"])
        with tempfile.TemporaryDirectory(prefix="mtglab-unavailable-private-source-") as directory:
            unavailable = str(Path(directory) / "private-owner-file.txt")
            code, result, output = self.cli("--artifact", unavailable)
        self.assertEqual(code, 1)
        self.assertEqual(result, {"error": "FOUNDATIONAL_PROJECTION_VERIFICATION_BLOCKED",
                                 "source_body_retained": False, "real_rules_executable": False})
        self.assertNotIn(unavailable, output)
        code, result, _ = self.cli("--artifact", "")
        self.assertEqual(code, 1)
        self.assertEqual(result["error"], "FOUNDATIONAL_PROJECTION_VERIFICATION_BLOCKED")

    def test_prior_packages_and_protected_acquisition_identity_remain_valid(self):
        self.assertEqual(verify_review_package(SOURCE)["package_id"],
                         "sha256:63c904317a6b8406a759950074175acf8a1cee0b9d20b8aa9e37a62382eeeca9")
        self.assertEqual(verify_discovery_package(DISCOVERY, previous_root=SOURCE)["package_id"],
                         "sha256:3e6c83491ade17d6e5cce5b9970eca5d59f8e0955f50e4f65234ad499d941e7d")
        self.assertEqual(verify_artifact_review_package(ARTIFACT_REVIEW,
            source_root=SOURCE, discovery_root=DISCOVERY)["package_id"],
            "sha256:b5ad8b6f59c0311a33726e1733dc9bb239804bd0ab387ed789caf0d870aba36a")
        fixture = ROOT / "tests/fixtures/historical_replay/card-acquisition-pilot"
        manifest = json.loads((fixture / "manifest.json").read_bytes())
        self.assertEqual(manifest["protected_inventory_identity"],
                         "sha256:669d7db9ebcaf97853058fd62f408ce3c6596d5dae0ee72ff39d2ba9df56bb53")
        for relative, binding in manifest["files"].items():
            raw = (fixture / relative).read_bytes()
            self.assertEqual({"bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}, binding)


if __name__ == "__main__":
    unittest.main()
