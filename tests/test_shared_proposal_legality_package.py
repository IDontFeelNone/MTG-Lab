"""Strict identity, retained lineage and canonical bounded-package boundaries."""
from copy import deepcopy
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

from evidence.contracts import sha256_identity
from gameplay_rules.errors import GameplayContractError
from gameplay_rules.shared_proposal_legality import package
from gameplay_rules.shared_proposal_legality.source import SOURCE_ENV

ROOT = Path(__file__).resolve().parents[1]
REVIEWS = ROOT / "reference-reviews"
PACKAGE = REVIEWS / package.PACKAGE_NAME


def reseal(record, domain=package.RECORD_DOMAIN):
    body = {key: value for key, value in record.items() if key != "review_id"}
    record["review_id"] = "sha256:" + sha256_identity({"domain": domain, "content": body})
    return record


class SharedProposalLegalityPackageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.records = package.load_package(PACKAGE, review_root=REVIEWS)

    def test_exact_canonical_round_trip_and_manifest_own_domain(self):
        metadata = package.manifest(self.records)
        body = {key: value for key, value in metadata.items() if key != "package_id"}
        self.assertEqual(metadata["package_id"], "sha256:" + sha256_identity({
            "domain": package.PACKAGE_SCHEMA, "content": body}))
        self.assertEqual(package._bytes(metadata), (PACKAGE / "manifest.json").read_bytes())
        with tempfile.TemporaryDirectory() as temporary:
            target = Path(temporary) / "new"
            package.write_package(target, self.records, review_root=REVIEWS)
            self.assertEqual(package._bytes(package.load_package(target, review_root=REVIEWS)), package._bytes(self.records))
            for name in package.RECORD_NAMES | {"manifest.json"}:
                self.assertEqual((target / name).read_bytes(), (PACKAGE / name).read_bytes())
            with self.assertRaisesRegex(GameplayContractError, "APPEND_ONLY"):
                package.write_package(target, self.records, review_root=REVIEWS)

    def test_wrong_own_ids_domains_and_referenced_id_substitutions(self):
        for mutation in (
                lambda record: record.update(review_id="sha256:" + "0" * 64),
                lambda record: reseal(record, "gameplay-shared-casting-stage-gap-design-record-v1"),
                lambda record: record.update(review_id=record["findings"]["merged_design_package_id"]),
                lambda record: record.update(projection_id=record.pop("review_id"))):
            records = deepcopy(self.records)
            mutation(records["design-source-correspondence.json"])
            with self.subTest(mutation=mutation), self.assertRaises(GameplayContractError):
                package.validate_records(records)

    def test_coherently_rehashed_foreign_or_altered_records_are_rejected(self):
        for name, mutation in (
                ("casting-parent-reassessment.json", lambda record: record["findings"].update(parent_procedure_complete=True)),
                ("activated-import-reassessment.json", lambda record: record["findings"].update(additional_applicability_qualifier_found=True)),
                ("preservation-readiness.json", lambda record: record["findings"].update(runtime_implemented=True))):
            records = deepcopy(self.records)
            mutation(records[name])
            reseal(records[name])
            with self.subTest(name=name), self.assertRaisesRegex(GameplayContractError, "EXACT_AUTHORED"):
                package.manifest(records)
        records = deepcopy(self.records)
        records["casting-parent-reassessment.json"] = deepcopy(records["activated-import-reassessment.json"])
        records["casting-parent-reassessment.json"]["record_type"] = "casting-parent-reassessment"
        reseal(records["casting-parent-reassessment.json"])
        with self.assertRaises(GameplayContractError):
            package.validate_records(records)

    def test_json_distinct_types_and_nonplain_structures_are_rejected(self):
        for replacement in (True, 1.0):
            records = deepcopy(self.records)
            records["casting-parent-reassessment.json"]["schema_version"] = replacement
            reseal(records["casting-parent-reassessment.json"])
            with self.subTest(schema=replacement), self.assertRaises(GameplayContractError):
                package.validate_records(records)
        for field, replacement in (("projected_member_count_after", 7.0),
                ("range_import_count", True), ("all_range_members_projected", 0),
                ("all_range_members_projected", 0.0)):
            records = deepcopy(self.records)
            records["activated-import-reassessment.json"]["findings"][field] = replacement
            reseal(records["activated-import-reassessment.json"])
            with self.subTest(field=field, replacement=replacement), self.assertRaises(GameplayContractError):
                package.validate_records(records)
        class IntegerSubclass(int):
            pass
        for replacement in (IntegerSubclass(1), float("nan"), (1,), {1: "foreign"}):
            records = deepcopy(self.records)
            records["casting-parent-reassessment.json"]["schema_version"] = replacement
            with self.subTest(kind=type(replacement)), self.assertRaises(GameplayContractError):
                package.validate_records(records)

    def test_invalid_new_or_retained_input_is_rejected_before_output_creation(self):
        records = deepcopy(self.records)
        records["activated-import-reassessment.json"]["findings"]["range_members"].pop()
        reseal(records["activated-import-reassessment.json"])
        with tempfile.TemporaryDirectory() as temporary:
            target = Path(temporary) / "missing-parent" / "package"
            with self.assertRaises(GameplayContractError):
                package.write_package(target, records, review_root=REVIEWS)
            self.assertFalse(target.parent.exists())
            with self.assertRaises(GameplayContractError):
                package.write_package(target, self.records, review_root=Path(temporary) / "absent-history")
            self.assertFalse(target.parent.exists())

    def test_closed_file_set_wrong_manifest_bindings_and_noncanonical_bytes(self):
        with tempfile.TemporaryDirectory() as temporary:
            target = Path(temporary) / "package"
            shutil.copytree(PACKAGE, target)
            manifest_path = target / "manifest.json"
            original_manifest = manifest_path.read_bytes()
            for mutate in (
                    lambda value: value.update(package_id="sha256:" + "0" * 64),
                    lambda value: value["record_ids"].update({"casting-parent-reassessment.json": value["record_ids"]["projection.json"]}),
                    lambda value: value["files"]["projection.json"].update(bytes=float(value["files"]["projection.json"]["bytes"]))):
                value = json.loads(original_manifest)
                mutate(value)
                body = {key: item for key, item in value.items() if key != "package_id"}
                if value["package_id"] != "sha256:" + "0" * 64:
                    value["package_id"] = package._identity(package.PACKAGE_SCHEMA, body)
                manifest_path.write_bytes(package._bytes(value))
                with self.subTest(mutation=mutate), self.assertRaises(GameplayContractError):
                    package.load_package(target, review_root=REVIEWS)
            manifest_path.write_bytes(original_manifest)
            extra = target / "foreign.json"
            extra.write_bytes(b"{}\n")
            with self.assertRaises(GameplayContractError):
                package.load_package(target, review_root=REVIEWS)
            extra.unlink()
            record = target / "casting-parent-reassessment.json"
            original = record.read_bytes()
            for bad in (b" " + original, original.replace(b'{', b'{"duplicate":0,"duplicate":1,', 1)):
                record.write_bytes(bad)
                with self.assertRaises(GameplayContractError):
                    package.load_package(target, review_root=REVIEWS)
            record.write_bytes(original)
            link = Path(temporary) / "link"
            link.symlink_to(target, target_is_directory=True)
            with self.assertRaises(GameplayContractError):
                package.load_package(link, review_root=REVIEWS)
            with self.assertRaises(GameplayContractError):
                package.write_package(link / "new", self.records, review_root=REVIEWS)
            self.assertFalse((target / "new").exists())

    def test_pr201_actual_own_domain_manifest_and_exact_retained_bytes(self):
        package.validate_historical(review_root=REVIEWS)
        with tempfile.TemporaryDirectory() as temporary:
            copied = Path(temporary) / "reviews"
            shutil.copytree(REVIEWS, copied)
            record_path = copied / package.DESIGN_NAME / "readiness.json"
            parent_path = copied / package.DESIGN_NAME / "manifest.json"
            original_record, original_parent = record_path.read_bytes(), parent_path.read_bytes()
            for domain, mutation in (
                    ("gameplay-bounded-activated-ability-procedure-record-v1", lambda value: None),
                    ("gameplay-shared-casting-stage-gap-design-record-v1", lambda value: value["findings"].update(new_source_units_projected=1)),
                    ("gameplay-shared-casting-stage-gap-design-record-v1", lambda value: value.update(schema_version=True))):
                record, parent = json.loads(original_record), json.loads(original_parent)
                mutation(record)
                body = {key: value for key, value in record.items() if key != "review_id"}
                record["review_id"] = package._identity(domain, body)
                raw = package._bytes(record)
                parent["record_ids"]["readiness.json"] = record["review_id"]
                parent["files"]["readiness.json"] = {"bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}
                parent["package_id"] = package._identity("gameplay-shared-casting-stage-gap-design-package-v1",
                    {key: value for key, value in parent.items() if key != "package_id"})
                record_path.write_bytes(raw)
                parent_path.write_bytes(package._bytes(parent))
                with self.subTest(domain=domain, mutation=mutation), self.assertRaises(GameplayContractError):
                    package.validate_historical(review_root=copied)
                with self.assertRaises(GameplayContractError):
                    package.manifest(self.records, review_root=copied)
                target = Path(temporary) / "uncreated" / "package"
                with self.assertRaises(GameplayContractError):
                    package.write_package(target, self.records, review_root=copied)
                self.assertFalse(target.parent.exists())
            record_path.write_bytes(original_record)
            parent_path.write_bytes(original_parent)
            package.validate_historical(review_root=copied)

    def test_pr203_own_domain_and_coherently_rehashed_historical_binding_changes_fail(self):
        with tempfile.TemporaryDirectory() as temporary:
            copied = Path(temporary) / "reviews"
            shutil.copytree(REVIEWS, copied)
            folder = copied / "gameplay-rules-bounded-shared-target-allocation"
            record_path, parent_path = folder / "casting-parent-reassessment.json", folder / "manifest.json"
            original_record, original_parent = record_path.read_bytes(), parent_path.read_bytes()
            for domain, mutate in (
                    (package.RECORD_DOMAIN, lambda value: None),
                    ("gameplay-bounded-shared-target-allocation-record-v1", lambda value: value["findings"].update(parent_procedure_complete=True)),
                    ("gameplay-bounded-shared-target-allocation-record-v1", lambda value: value.update(schema_version=1.0)),
                    ("gameplay-bounded-shared-target-allocation-record-v1", lambda value: value.update(schema_version=True))):
                record, parent = json.loads(original_record), json.loads(original_parent)
                mutate(record)
                reseal(record, domain)
                raw = package._bytes(record)
                parent["record_ids"][record_path.name] = record["review_id"]
                parent["files"][record_path.name] = {"bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}
                parent["package_id"] = package._identity("gameplay-bounded-shared-target-allocation-package-v1",
                    {key: value for key, value in parent.items() if key != "package_id"})
                record_path.write_bytes(raw)
                parent_path.write_bytes(package._bytes(parent))
                with self.subTest(domain=domain), self.assertRaises(GameplayContractError):
                    package.validate_historical(review_root=copied)
                target = Path(temporary) / "uncreated" / "new"
                with self.assertRaises(GameplayContractError):
                    package.write_package(target, self.records, review_root=copied)
                self.assertFalse(target.parent.exists())
            record_path.write_bytes(original_record)
            parent_path.write_bytes(original_parent)
            package.validate_historical(review_root=copied)

    def test_warm_metadata_caches_return_defensive_copies_and_revalidate_disk_history(self):
        original_binding = package._bytes(package.retained_binding())
        original_records = package._bytes(package._expected_records())
        binding = package.retained_binding()
        binding["rule_bindings"]["601.2d"]["rule_id"] = "sha256:" + "0" * 64
        binding["projection_components"].clear()
        records = package._expected_records()
        records["recovery-dependency.json"]["findings"]["state"] = "DIRECT_REFERENCE_RESOLVED"
        records["projection.json"]["rules"].clear()
        self.assertEqual(package._bytes(package.retained_binding()), original_binding)
        self.assertEqual(package._bytes(package._expected_records()), original_records)
        with tempfile.TemporaryDirectory() as temporary:
            copied = Path(temporary) / "reviews"
            shutil.copytree(REVIEWS, copied)
            historical = copied / "gameplay-rules-bounded-shared-target-allocation" / "casting-parent-reassessment.json"
            historical.write_bytes(historical.read_bytes() + b"\n")
            with self.assertRaises(GameplayContractError):
                package.validate_historical(review_root=copied)
            target = Path(temporary) / "uncreated" / "package"
            with self.assertRaises(GameplayContractError):
                package.write_package(target, self.records, review_root=copied)
            self.assertFalse(target.parent.exists())

    def test_new_reference_metadata_rewrites_are_rejected_before_output_creation(self):
        for name, mutate in (
                ("design-source-correspondence.json", lambda value: value.update(literal_outgoing_numbered_citations=[])),
                ("design-source-correspondence.json", lambda value: value.update(literal_outgoing_numbered_citations=["733.1"])),
                ("recovery-dependency.json", lambda value: value.update(target_reference="733.1")),
                ("recovery-dependency.json", lambda value: value["target_node"].update(package_id="sha256:" + "0" * 64))):
            records = deepcopy(self.records)
            mutate(records[name]["findings"])
            reseal(records[name])
            with tempfile.TemporaryDirectory() as temporary:
                target = Path(temporary) / "uncreated" / "package"
                with self.subTest(name=name, mutation=mutate), self.assertRaises(GameplayContractError):
                    package.write_package(target, records, review_root=REVIEWS)
                self.assertFalse(target.parent.exists())

    def test_source_boundary_rejects_rehashed_record_before_source_or_output_access(self):
        records = deepcopy(self.records)
        record = records["consumer-semantic-boundaries.json"]
        record["findings"]["unauthorized_injected_knowledge"] = True
        reseal(record)
        with mock.patch.object(package, "build_package", side_effect=AssertionError("source must not be accessed")) as build:
            with self.assertRaises(GameplayContractError):
                package.verify_source(records, "unread-invalid-source", review_root=REVIEWS)
            build.assert_not_called()
        with tempfile.TemporaryDirectory() as temporary:
            target = Path(temporary) / "uncreated" / "new"
            with self.assertRaises(GameplayContractError):
                package.write_package(target, records, review_root=REVIEWS)
            self.assertFalse(target.parent.exists())

    def test_writer_uses_validated_snapshot_when_caller_mutates_during_real_history_validation(self):
        records = deepcopy(self.records)
        expected = package._bytes(self.records)
        actual_historical_validation = package.validate_historical

        def validate_history_and_mutate_caller(*, review_root):
            records["recovery-dependency.json"]["findings"]["state"] = "DIRECT_REFERENCE_RESOLVED"
            reseal(records["recovery-dependency.json"])
            return actual_historical_validation(review_root=review_root)

        with tempfile.TemporaryDirectory() as temporary:
            target = Path(temporary) / "retained"
            with mock.patch.object(package, "validate_historical", side_effect=validate_history_and_mutate_caller) as validate:
                package.write_package(target, records, review_root=REVIEWS)
                self.assertGreaterEqual(validate.call_count, 1)
            self.assertEqual(records["recovery-dependency.json"]["findings"]["state"], "DIRECT_REFERENCE_RESOLVED")
            self.assertEqual(package._bytes(package.load_package(target, review_root=REVIEWS)), expected)
            self.assertEqual((target / "recovery-dependency.json").read_bytes(), package._bytes(self.records["recovery-dependency.json"]))

    def test_synthetic_source_boundary_uses_validated_snapshot_when_caller_mutates(self):
        # Synthetic mutation test only: the patched builder establishes no source authority.
        records = deepcopy(self.records)
        validated_snapshot = deepcopy(self.records)

        def synthetic_builder_and_caller_mutation(*args, **kwargs):
            records["projection.json"]["projection_id"] = "sha256:" + "0" * 64
            records["projection.json"]["rules"][0]["source_anchor"]["anchor_id"] = "sha256:" + "0" * 64
            return deepcopy(validated_snapshot)

        with mock.patch.object(package, "build_package", side_effect=synthetic_builder_and_caller_mutation) as build:
            result = package.verify_source(records, "synthetic-unread-source", review_root=REVIEWS)
            build.assert_called_once()
        self.assertEqual(records["projection.json"]["projection_id"], "sha256:" + "0" * 64)
        self.assertEqual(result["projection_id"], validated_snapshot["projection.json"]["projection_id"])
        self.assertEqual(result["source_anchor"], validated_snapshot["projection.json"]["rules"][0]["source_anchor"])

    def test_direct_history_validation_matches_original_loader_and_complete_bindings(self):
        # The unchanged original loader is exercised once as an independent
        # equivalence oracle; the production e validator never delegates to it.
        from gameplay_rules.shared_target_allocation import package as original
        inherited = original.load_package(REVIEWS / original.PACKAGE_NAME, review_root=REVIEWS)
        inherited_manifest = json.loads((REVIEWS / original.PACKAGE_NAME / "manifest.json").read_bytes())
        original_binding = original.retained_binding()
        composite = deepcopy(inherited["composite-coverage.json"]["findings"])

        def resolve_enclosing_package(value):
            if type(value) is dict:
                if "package_binding" in value:
                    self.assertEqual(value.pop("package_binding"), "THIS_ENCLOSING_PACKAGE")
                    value["package_id"] = inherited_manifest["package_id"]
                for child in value.values():
                    resolve_enclosing_package(child)
            elif type(value) is list:
                for child in value:
                    resolve_enclosing_package(child)

        resolve_enclosing_package(composite)
        original_binding["canonical_base"] = package.CANONICAL_MAIN
        original_binding["projection_components"] = composite["projection_components"]
        original_binding["rule_bindings"] = composite["all_prior_rule_bindings"]
        projection = inherited["projection.json"]
        for rule in projection["rules"]:
            original_binding["rule_bindings"][rule["rule_reference"]] = {
                "retained_package": original.PACKAGE_NAME, "package_id": inherited_manifest["package_id"],
                "projection_id": projection["projection_id"], "rule_id": rule["rule_id"],
                "anchor_identity": rule["source_anchor"]["anchor_id"],
                "source_anchor": deepcopy(rule["source_anchor"]), "identity_basis": "EXISTING_STANDALONE_ID"}
        original_binding["prior_package_ids"][original.PACKAGE_NAME] = inherited_manifest["package_id"]
        actual = package.validate_historical(review_root=REVIEWS)
        self.assertEqual(package._bytes(actual), package._bytes(original_binding))
        self.assertEqual(package._bytes(package.retained_binding()), package._bytes(original_binding))
        reproduced = package.rebuild_package(review_root=REVIEWS)
        self.assertEqual(package._bytes(reproduced), package._bytes(self.records))
        for name, record in reproduced.items():
            self.assertEqual(package._bytes(record), (PACKAGE / name).read_bytes())
        self.assertEqual(package._bytes(package.manifest(reproduced)), (PACKAGE / "manifest.json").read_bytes())

    def test_every_canonical_historical_evidence_file_is_rechecked_after_cache_warmup(self):
        guard_path = ROOT / "tests" / "fixtures" / "shared-proposal-legality-protected-state.json"
        raw_guard = guard_path.read_bytes()
        self.assertEqual(hashlib.sha256(raw_guard).hexdigest(),
            "ef2bb3484803d44f9e1ad20e1be1c27b15d3901d3b4e1b86b1476662c0c4e094")
        guard = json.loads(raw_guard)
        self.assertEqual(guard["canonical_base"], "a21cda0c22092a77ec07097d7b155e7a71bd8de2")
        rows = [row for row in guard["protected_files"] if row["path"].startswith("reference-reviews/")]
        self.assertEqual(len(rows), 150)
        self.assertEqual(len({row["path"] for row in rows}), 150)
        self.assertEqual(len({str(Path(row["path"]).parent) for row in rows}), 22)
        with tempfile.TemporaryDirectory() as temporary:
            copied = Path(temporary) / "reviews"
            shutil.copytree(REVIEWS, copied)
            package.retained_binding()
            package._expected_records()
            package.validate_historical(review_root=copied)
            for row in rows:
                relative = Path(row["path"]).relative_to("reference-reviews")
                target = copied / relative
                original = target.read_bytes()
                self.assertEqual(len(original), row["bytes"])
                self.assertEqual(hashlib.sha256(original).hexdigest(), row["sha256"])
                self.assertTrue(original)
                try:
                    target.write_bytes(bytes([original[0] ^ 1]) + original[1:])
                    with self.subTest(path=row["path"]), self.assertRaises(GameplayContractError):
                        package.validate_historical(review_root=copied)
                finally:
                    target.write_bytes(original)
            package.validate_historical(review_root=copied)

    def test_cli_unconfigured_skip_and_configured_invalid_source_failure(self):
        environment = os.environ.copy()
        environment["PYTHONPATH"] = str(ROOT / "src")
        environment.pop(SOURCE_ENV, None)
        command = [sys.executable, "-m", "gameplay_rules.shared_proposal_legality", "verify-source"]
        result = subprocess.run(command, cwd=ROOT, env=environment, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)["source_reproduction"], "SKIPPED_SOURCE_SELECTOR_UNCONFIGURED")
        environment[SOURCE_ENV] = str(ROOT / "absent-source-for-negative-check")
        result = subprocess.run(command, cwd=ROOT, env=environment, capture_output=True, text=True)
        self.assertEqual(result.returncode, 1)
        self.assertNotIn("VERIFIED_EXACT", result.stdout)
