"""Adversarial package boundaries, distinct from fresh attached-source proof.

The mocked source comparison below exercises comparison only. The separately
configured external-artifact test is the fresh byte/anchor reproduction proof.
"""
import copy
import hashlib
import json
import os
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch

from evidence.contracts import deterministic_json, sha256_identity
from gameplay_rules.errors import GameplayContractError
from gameplay_rules.activated_ability_projection import package as pkg

ROOT = Path(__file__).resolve().parents[1]
REVIEWS = ROOT / "reference-reviews"
PACKAGE = REVIEWS / "gameplay-rules-bounded-activated-ability-procedure-projection"
DESIGN = "gameplay-rules-activated-ability-procedure-design"
DESIGN_DOMAIN = "gameplay-activated-ability-procedure-design-record-v1"
DESIGN_NAMES = (
    "source-correspondence.json", "local-scope.json", "procedure-responsibilities.json",
    "casting-import.json", "mana-relationships.json", "consumer-bindings.json", "readiness.json",
)


def canonical_bytes(value):
    return (deterministic_json(value) + "\n").encode("utf-8")


def replace_at(value, path, replacement):
    target = value
    for key in path[:-1]:
        target = target[key]
    target[path[-1]] = replacement


def paths_to(value, predicate, prefix=()):
    if predicate(value):
        yield prefix
    if type(value) is dict:
        for key, item in value.items():
            yield from paths_to(item, predicate, (*prefix, key))
    elif type(value) is list:
        for index, item in enumerate(value):
            yield from paths_to(item, predicate, (*prefix, index))


class NewPackageBoundaryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.records = pkg.load_package(PACKAGE, review_root=REVIEWS)

    def assert_rejected(self, candidate):
        """Each public candidate boundary rejects without mutating or writing."""
        snapshot = repr(candidate)
        with self.subTest(boundary="manifest"), self.assertRaises(GameplayContractError):
            pkg.manifest(candidate)
        with tempfile.TemporaryDirectory() as td:
            destination = Path(td) / "not-created" / "package"
            with self.subTest(boundary="write"), self.assertRaises(GameplayContractError):
                pkg.write_package(destination, candidate, review_root=REVIEWS)
            self.assertFalse(destination.parent.exists())
            self.assertEqual(list(Path(td).iterdir()), [])
        # No external artifact is read by this comparison test.
        with patch.object(pkg, "build_package", return_value=copy.deepcopy(self.records)):
            with self.subTest(boundary="source-comparison"), self.assertRaises(GameplayContractError):
                pkg.verify_source(candidate, None, review_root=REVIEWS)
        self.assertEqual(repr(candidate), snapshot)

    def test_boolean_integer_float_substitutions_at_all_new_record_boundaries(self):
        cases = []
        for name, record in self.records.items():
            bool_path = next(paths_to(record, lambda x: type(x) is bool))
            old = record
            for key in bool_path:
                old = old[key]
            cases.append((name, bool_path, int(old)))
        projection = self.records["projection.json"]
        for predicate, replacement in (
            (lambda x: type(x) is int and x > 1, 3.0),
            (lambda x: type(x) is int and x == 1, True),
        ):
            path = next(paths_to(projection, predicate))
            old = projection
            for key in path:
                old = old[key]
            if type(replacement) is float:
                replacement = float(old)
            cases.append(("projection.json", path, replacement))
        nested_review = self.records["casting-import.json"]
        integer_path = next(paths_to(nested_review["findings"], lambda x: type(x) is int))
        old = nested_review["findings"]
        for key in integer_path:
            old = old[key]
        cases.append(("casting-import.json", ("findings", *integer_path), float(old)))
        for name, path, replacement in cases:
            with self.subTest(record=name, path=path, replacement_type=type(replacement).__name__):
                candidate = copy.deepcopy(self.records)
                replace_at(candidate[name], path, replacement)
                self.assertEqual(candidate, self.records)  # Python's equality trap.
                self.assertNotEqual(canonical_bytes(candidate), canonical_bytes(self.records))
                self.assert_rejected(candidate)

    def test_non_json_substitutions_rejected_without_coercion(self):
        for value in (float("nan"), float("inf"), b"metadata", {"set"}, ("tuple",)):
            candidate = copy.deepcopy(self.records)
            candidate["overall-readiness.json"]["findings"]["non_json_substitution"] = value
            with self.subTest(value_type=type(value).__name__):
                self.assert_rejected(candidate)
        candidate = copy.deepcopy(self.records)
        candidate["overall-readiness.json"]["findings"][0] = "integer key"
        self.assert_rejected(candidate)

    def test_stale_projection_rule_review_and_package_identities_rejected(self):
        paths = [
            ("projection.json", "projection_id"),
            ("projection.json", "rules", 0, "rule_id"),
            ("overall-readiness.json", "review_id"),
        ]
        for path in paths:
            candidate = copy.deepcopy(self.records)
            replace_at(candidate, path, "sha256:" + "0" * 64)
            with self.subTest(path=path):
                self.assert_rejected(candidate)
        with tempfile.TemporaryDirectory() as td:
            target = Path(td) / "package"
            pkg.write_package(target, self.records, review_root=REVIEWS)
            manifest_path = target / "manifest.json"
            manifest = json.loads(manifest_path.read_bytes())
            manifest["package_id"] = "sha256:" + "0" * 64
            manifest_path.write_bytes(canonical_bytes(manifest))
            with self.assertRaises(GameplayContractError):
                pkg.load_package(target, review_root=REVIEWS)

    def test_rehashed_invalid_findings_rejected_before_output(self):
        candidate = copy.deepcopy(self.records)
        name = "overall-readiness.json"
        candidate[name]["findings"]["execution_readiness"] = "READY"
        body = {k: v for k, v in candidate[name].items() if k != "review_id"}
        candidate[name]["review_id"] = "sha256:" + sha256_identity({
            "domain": "gameplay-bounded-activated-ability-procedure-record-v1", "content": body})
        self.assertNotEqual(candidate[name]["review_id"], self.records[name]["review_id"])
        self.assert_rejected(candidate)

    def test_wrong_or_missing_manifest_record_relationship_and_typed_counts_rejected(self):
        original = pkg.manifest(self.records)
        review_names = sorted(original["record_ids"])
        for mode in ("missing", "foreign", "unique-swap", "integer-to-float", "integer-to-bool"):
            with tempfile.TemporaryDirectory() as td:
                target = Path(td) / "package"
                pkg.write_package(target, self.records, review_root=REVIEWS)
                modified = copy.deepcopy(original)
                if mode == "missing":
                    modified["record_ids"].pop(review_names[0])
                elif mode == "foreign":
                    modified["record_ids"][review_names[0]] = original["package_id"]
                elif mode == "unique-swap":
                    a, b = review_names[:2]
                    modified["record_ids"][a], modified["record_ids"][b] = (
                        modified["record_ids"][b], modified["record_ids"][a])
                    self.assertEqual(len(set(modified["record_ids"].values())), len(review_names))
                else:
                    modified["projected_rule_count_after"] = 88.0 if mode.endswith("float") else True
                body = {k: v for k, v in modified.items() if k != "package_id"}
                modified["package_id"] = "sha256:" + sha256_identity({
                    "domain": modified["schema_version"], "content": body})
                (target / "manifest.json").write_bytes(canonical_bytes(modified))
                with self.subTest(mode=mode), self.assertRaises(GameplayContractError):
                    pkg.load_package(target, review_root=REVIEWS)

    def test_invalid_record_with_recomputed_surrounding_metadata_is_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            target = Path(td) / "package"
            metadata = pkg.write_package(target, self.records, review_root=REVIEWS)
            name = "overall-readiness.json"
            changed = copy.deepcopy(self.records[name])
            changed["findings"]["execution_readiness"] = "READY"
            body = {k: v for k, v in changed.items() if k != "review_id"}
            changed["review_id"] = "sha256:" + sha256_identity({
                "domain": "gameplay-bounded-activated-ability-procedure-record-v1", "content": body})
            raw = canonical_bytes(changed)
            (target / name).write_bytes(raw)
            metadata["record_ids"][name] = changed["review_id"]
            metadata["files"][name] = {"bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}
            body = {k: v for k, v in metadata.items() if k != "package_id"}
            metadata["package_id"] = "sha256:" + sha256_identity({
                "domain": metadata["schema_version"], "content": body})
            (target / "manifest.json").write_bytes(canonical_bytes(metadata))
            with self.assertRaises(GameplayContractError):
                pkg.load_package(target, review_root=REVIEWS)

    def test_duplicate_keys_noncanonical_missing_and_extra_files_rejected(self):
        for mode in ("duplicate-record", "duplicate-manifest", "whitespace", "missing", "extra-json", "extra-txt"):
            with tempfile.TemporaryDirectory() as td:
                target = Path(td) / "package"
                pkg.write_package(target, self.records, review_root=REVIEWS)
                path = target / ("manifest.json" if mode == "duplicate-manifest" else "overall-readiness.json")
                raw = path.read_bytes()
                if mode.startswith("duplicate"):
                    key = "package_id" if mode == "duplicate-manifest" else "review_id"
                    value = json.loads(raw)[key]
                    path.write_bytes(("{" + json.dumps(key) + ":" + json.dumps(value) + ",").encode() + raw[1:])
                elif mode == "whitespace":
                    path.write_bytes(raw + b" ")
                elif mode == "missing":
                    path.unlink()
                else:
                    (target / ("extra.txt" if mode.endswith("txt") else "extra.json")).write_bytes(b"{}\n")
                with self.subTest(mode=mode), self.assertRaises(GameplayContractError):
                    pkg.load_package(target, review_root=REVIEWS)

    def test_symlink_hardlink_and_linked_package_paths_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            target = root / "package"
            pkg.write_package(target, self.records, review_root=REVIEWS)
            path = target / "overall-readiness.json"
            raw = path.read_bytes()
            path.unlink()
            path.symlink_to(PACKAGE / path.name)
            with self.assertRaises(GameplayContractError):
                pkg.load_package(target, review_root=REVIEWS)
            path.unlink()
            outside = root / "outside.json"
            outside.write_bytes(raw)
            os.link(outside, path)
            with self.assertRaises(GameplayContractError):
                pkg.load_package(target, review_root=REVIEWS)
            path.unlink()
            path.write_bytes(raw)
            linked = root / "linked"
            linked.symlink_to(target, target_is_directory=True)
            with self.assertRaises(GameplayContractError):
                pkg.load_package(linked, review_root=REVIEWS)
            destination = linked / "new-package"
            with self.assertRaises(GameplayContractError):
                pkg.write_package(destination, self.records, review_root=REVIEWS)
            self.assertFalse(destination.exists())

    def test_valid_deterministic_write_load_rebuild_relocation_and_append_only(self):
        before = canonical_bytes(self.records)
        expected_manifest = json.loads((PACKAGE / "manifest.json").read_bytes())
        self.assertEqual(pkg.manifest(self.records), expected_manifest)
        with tempfile.TemporaryDirectory() as td:
            relocated = Path(td) / "reviews"
            relocated.mkdir()
            for name in {Path(p).parts[1] for p in pkg._pins()["protected_files"]
                         if p.startswith("reference-reviews/")}:
                shutil.copytree(REVIEWS / name, relocated / name)
            destination = relocated / pkg.PACKAGE_NAME
            self.assertEqual(pkg.write_package(destination, self.records, review_root=relocated), expected_manifest)
            self.assertEqual(pkg.load_package(destination, review_root=relocated), self.records)
            self.assertEqual(pkg.rebuild_package(review_root=relocated), self.records)
            for path in PACKAGE.iterdir():
                self.assertEqual((destination / path.name).read_bytes(), path.read_bytes())
            with self.assertRaises(GameplayContractError):
                pkg.write_package(destination, self.records, review_root=relocated)
        self.assertEqual(canonical_bytes(self.records), before)

    def test_current_scope_does_not_carry_unprojected_origin_claims_from_historical_design(self):
        findings = self.records["local-scope.json"]["findings"]
        self.assertEqual(findings["candidate_coverage"], "PROJECTED")
        self.assertNotIn("ORIGIN_UNPROJECTED_NO_NEW_COVERAGE_EDGE", deterministic_json(findings))
        rows = findings["outgoing_literal_references"]
        direct = next(row for row in rows if row["target_reference"] == "601.2f")
        self.assertEqual(direct["state"], "DIRECT_REFERENCE_RESOLVED")

    def test_mocked_valid_source_comparison_is_only_a_comparison_check(self):
        with patch.object(pkg, "build_package", return_value=copy.deepcopy(self.records)):
            result = pkg.verify_source(self.records, None, review_root=REVIEWS)
        self.assertEqual(result["projection_id"], self.records["projection.json"]["projection_id"])
        self.assertFalse(result["source_body_retained"])


class HistoricalIdentityBoundaryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.binding = pkg.retained_binding()

    def copy_inputs(self, root):
        for name in {Path(p).parts[1] for p in pkg._pins()["protected_files"]
                     if p.startswith("reference-reviews/")}:
            shutil.copytree(REVIEWS / name, root / name)

    def rewrite_parent(self, root, manifest):
        body = {k: v for k, v in manifest.items() if k != "package_id"}
        manifest["package_id"] = "sha256:" + sha256_identity({
            "domain": manifest["schema_version"], "content": body})
        (root / DESIGN / "manifest.json").write_bytes(canonical_bytes(manifest))
        binding = copy.deepcopy(self.binding)
        binding["prior_package_ids"][DESIGN] = manifest["package_id"]
        return binding

    def rewrite_record(self, root, name, record):
        raw = canonical_bytes(record)
        (root / DESIGN / name).write_bytes(raw)
        manifest = json.loads((root / DESIGN / "manifest.json").read_bytes())
        manifest["files"][name] = {"bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}
        return self.rewrite_parent(root, manifest)

    def test_seven_pr199_records_use_integer_schema_explicit_domain_and_filename_manifest_binding(self):
        manifest = json.loads((REVIEWS / DESIGN / "manifest.json").read_bytes())
        selected = pkg.validate_review_bindings(self.binding, review_root=REVIEWS)
        for name in DESIGN_NAMES:
            raw = (REVIEWS / DESIGN / name).read_bytes()
            record = json.loads(raw)
            self.assertIs(type(record["schema_version"]), int)
            self.assertEqual(record["schema_version"], 1)
            content = {k: v for k, v in record.items() if k != "review_id"}
            expected = "sha256:" + sha256_identity({"domain": DESIGN_DOMAIN, "content": content})
            self.assertEqual(record["review_id"], expected)
            self.assertEqual(selected[DESIGN + "/" + name], expected)
            self.assertEqual(manifest["record_ids"][name], expected)
            self.assertEqual(manifest["files"][name], {"bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()})
            self.assertNotEqual(expected, "sha256:" + sha256_identity({"domain": 1, "content": content}))

    def test_valid_foreign_id_and_all_unique_record_permutation_rejected_before_output(self):
        names = [DESIGN + "/" + name for name in DESIGN_NAMES]
        foreign = self.binding["prior_package_ids"][DESIGN]
        for mode in ("foreign", "all-unique-swap"):
            binding = copy.deepcopy(self.binding)
            if mode == "foreign":
                binding["review_bindings"][names[0]] = foreign
            else:
                a, b = names[:2]
                selected = binding["review_bindings"]
                selected[a], selected[b] = selected[b], selected[a]
                self.assertEqual(len(set(selected.values())), len(selected))
            with self.subTest(mode=mode), self.assertRaises(GameplayContractError):
                pkg.validate_review_bindings(binding, review_root=REVIEWS)
            pins = copy.deepcopy(pkg._pins())
            pins["binding"] = binding
            with patch.object(pkg, "_pins", return_value=pins):
                with self.assertRaises(GameplayContractError):
                    pkg.verify_prior_packages(REVIEWS)
                with self.assertRaises(GameplayContractError):
                    pkg.rebuild_package(review_root=REVIEWS)
                with tempfile.TemporaryDirectory() as td:
                    target = Path(td) / "must-not-exist" / "package"
                    # Restore a genuine candidate; only the historical selection is corrupt.
                    with patch.object(pkg, "_pins", return_value={**pins, "binding": self.binding}):
                        records = pkg.rebuild_package(review_root=REVIEWS)
                    with self.assertRaises(GameplayContractError):
                        pkg.write_package(target, records, review_root=REVIEWS)
                    self.assertFalse(target.parent.exists())

    def test_inherited_record_foreign_link_is_rejected_as_its_own_identity(self):
        name = "gameplay-rules-mana-direct-dependency-design/dependency-groups.json"
        record = json.loads((REVIEWS / name).read_bytes())
        self.assertNotEqual(record["grouping_id"], record["activated_procedure_design_id"])
        binding = copy.deepcopy(self.binding)
        binding["review_bindings"][name] = record["activated_procedure_design_id"]
        with self.assertRaises(GameplayContractError):
            pkg.validate_review_bindings(binding, review_root=REVIEWS)

    def test_pr199_record_schema_boolean_float_and_missing_own_identity_rejected(self):
        name = DESIGN_NAMES[0]
        original = json.loads((REVIEWS / DESIGN / name).read_bytes())
        for mode in ("bool", "float", "missing", "foreign", "wrong-domain"):
            with tempfile.TemporaryDirectory() as td:
                root = Path(td)
                self.copy_inputs(root)
                record = copy.deepcopy(original)
                if mode == "bool":
                    record["schema_version"] = True
                elif mode == "float":
                    record["schema_version"] = 1.0
                elif mode == "missing":
                    record.pop("review_id")
                elif mode == "foreign":
                    record["review_id"] = self.binding["prior_package_ids"][DESIGN]
                else:
                    content = {k: v for k, v in record.items() if k != "review_id"}
                    record["review_id"] = "sha256:" + sha256_identity({"domain": 1, "content": content})
                binding = self.rewrite_record(root, name, record)
                with self.subTest(mode=mode), self.assertRaises(GameplayContractError):
                    pkg.validate_review_bindings(binding, review_root=root)

    def test_pr199_parent_identity_and_own_manifest_relationship_are_required(self):
        name = DESIGN_NAMES[0]
        for mode in ("missing-parent", "foreign-parent", "missing-record", "wrong-record", "byte-count-float", "wrong-file-hash"):
            with tempfile.TemporaryDirectory() as td:
                root = Path(td)
                self.copy_inputs(root)
                manifest = json.loads((root / DESIGN / "manifest.json").read_bytes())
                binding = copy.deepcopy(self.binding)
                if mode == "missing-parent":
                    binding["prior_package_ids"].pop(DESIGN)
                elif mode == "foreign-parent":
                    binding["prior_package_ids"][DESIGN] = next(v for k, v in binding["prior_package_ids"].items() if k != DESIGN)
                else:
                    if mode == "missing-record":
                        manifest["record_ids"].pop(name)
                    elif mode == "wrong-record":
                        manifest["record_ids"][name] = manifest["record_ids"][DESIGN_NAMES[1]]
                    elif mode == "byte-count-float":
                        manifest["files"][name]["bytes"] = float(manifest["files"][name]["bytes"])
                    else:
                        manifest["files"][name]["sha256"] = "0" * 64
                    binding = self.rewrite_parent(root, manifest)
                with self.subTest(mode=mode), self.assertRaises(GameplayContractError):
                    pkg.validate_review_bindings(binding, review_root=root)

    def test_changed_historical_content_rehashed_with_metadata_cannot_replace_pinned_evidence(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            self.copy_inputs(root)
            name = DESIGN_NAMES[0]
            record = json.loads((root / DESIGN / name).read_bytes())
            record["findings"]["added_claim"] = "not canonical historical evidence"
            content = {k: v for k, v in record.items() if k != "review_id"}
            record["review_id"] = "sha256:" + sha256_identity({"domain": DESIGN_DOMAIN, "content": content})
            binding = self.rewrite_record(root, name, record)
            manifest = json.loads((root / DESIGN / "manifest.json").read_bytes())
            manifest["record_ids"][name] = record["review_id"]
            binding = self.rewrite_parent(root, manifest)
            binding["review_bindings"][DESIGN + "/" + name] = record["review_id"]
            with self.assertRaises(GameplayContractError):
                pkg.validate_review_bindings(binding, review_root=root)
            pins = copy.deepcopy(pkg._pins())
            pins["binding"] = binding
            with patch.object(pkg, "_pins", return_value=pins):
                with self.assertRaises(GameplayContractError):
                    pkg.verify_prior_packages(root)


if __name__ == "__main__":
    unittest.main()
