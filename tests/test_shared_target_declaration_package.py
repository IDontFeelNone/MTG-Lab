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

from evidence.contracts import sha256_identity
from gameplay_rules.errors import GameplayContractError
from gameplay_rules.shared_target_declaration import package
from gameplay_rules.shared_target_declaration.source import SOURCE_ENV

ROOT = Path(__file__).resolve().parents[1]
REVIEWS = ROOT / "reference-reviews"
PACKAGE = REVIEWS / package.PACKAGE_NAME


def reseal(record, domain=package.RECORD_DOMAIN):
    body = {key: value for key, value in record.items() if key != "review_id"}
    record["review_id"] = "sha256:" + sha256_identity({"domain": domain, "content": body})
    return record


class SharedTargetDeclarationPackageTests(unittest.TestCase):
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
        for field, replacement in (("projected_member_count_after", 5.0),
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

    def test_cli_unconfigured_skip_and_configured_invalid_source_failure(self):
        environment = os.environ.copy()
        environment["PYTHONPATH"] = str(ROOT / "src")
        environment.pop(SOURCE_ENV, None)
        command = [sys.executable, "-m", "gameplay_rules.shared_target_declaration", "verify-source"]
        result = subprocess.run(command, cwd=ROOT, env=environment, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)["source_reproduction"], "SKIPPED_SOURCE_SELECTOR_UNCONFIGURED")
        environment[SOURCE_ENV] = str(ROOT / "absent-source-for-negative-check")
        result = subprocess.run(command, cwd=ROOT, env=environment, capture_output=True, text=True)
        self.assertEqual(result.returncode, 1)
        self.assertNotIn("VERIFIED_EXACT", result.stdout)
