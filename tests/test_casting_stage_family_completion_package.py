"""Canonical package identities, fresh historical bindings and snapshot ownership."""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch

from gameplay_rules.errors import GameplayContractError
from gameplay_rules.casting_stage_family_completion import package
from gameplay_rules.shared_proposal_legality import package as historical_e

ROOT = Path(__file__).resolve().parents[1]
REVIEWS = ROOT / "reference-reviews"
PACKAGE = REVIEWS / "gameplay-rules-casting-stage-family-completion"


def reseal(record, domain=None):
    record["review_id"] = package._identity(domain or package.RECORD_DOMAIN,
        {key: item for key, item in record.items() if key != "review_id"})
    return record


class CastingStageFamilyCompletionPackageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.records = package.load_package(PACKAGE, review_root=REVIEWS)

    def test_canonical_write_load_roundtrip_and_actual_own_manifest_domain(self):
        manifest = package.manifest(self.records, review_root=REVIEWS)
        self.assertEqual(manifest["package_id"], package._identity(package.PACKAGE_SCHEMA,
            {key: item for key, item in manifest.items() if key != "package_id"}))
        self.assertEqual((PACKAGE / "manifest.json").read_bytes(), package._bytes(manifest))
        for name, record in self.records.items():
            field = "projection_id" if name == "projection.json" else "review_id"
            self.assertEqual(manifest["record_ids"][name], record[field])
            raw = package._bytes(record)
            self.assertEqual(manifest["files"][name], {"bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()})
        with tempfile.TemporaryDirectory() as temporary:
            target = Path(temporary) / "new"
            package.write_package(target, self.records, review_root=REVIEWS)
            self.assertEqual(package._bytes(package.load_package(target, review_root=REVIEWS)), package._bytes(self.records))
            for name in package.RECORD_NAMES | {"manifest.json"}:
                self.assertEqual((target / name).read_bytes(), (PACKAGE / name).read_bytes())
            with self.assertRaises(GameplayContractError):
                package.write_package(target, self.records, review_root=REVIEWS)

    def test_wrong_own_identity_fields_domain_and_coherently_rehashed_foreign_knowledge_fail(self):
        for mutate in (
                lambda record: record.update(review_id="sha256:" + "0" * 64),
                lambda record: reseal(record, historical_e.RECORD_DOMAIN),
                lambda record: record.update(review_id=self.records["projection.json"]["projection_id"]),
                lambda record: record.update(projection_id=record.pop("review_id")),
                lambda record: record["findings"].update(unsupported_injected_claim=True)):
            records = deepcopy(self.records)
            record = records["preflight.json"]
            mutate(record)
            if "review_id" in record and "unsupported_injected_claim" in record["findings"]:
                reseal(record)
            with self.subTest(mutate=mutate), self.assertRaises(GameplayContractError):
                package.validate_records(records)

    def test_schema_boolean_float_and_nested_numeric_substitutions_fail(self):
        for replacement in (True, 1.0):
            records = deepcopy(self.records)
            record = records["preflight.json"]
            record["schema_version"] = replacement
            reseal(record)
            with self.subTest(replacement=replacement), self.assertRaises(GameplayContractError):
                package.validate_records(records)
        for replacement in (True, 2.0):
            records = deepcopy(self.records)
            records["projection.json"]["selected_rule_count"] = replacement
            with self.subTest(replacement=replacement), self.assertRaises(GameplayContractError):
                package.manifest(records, review_root=REVIEWS)

    def test_invalid_input_rejected_before_output_or_source_access(self):
        records = deepcopy(self.records)
        record = records["preflight.json"]
        record["findings"]["unsupported_injected_claim"] = True
        reseal(record)
        with tempfile.TemporaryDirectory() as temporary:
            target = Path(temporary) / "uncreated" / "new"
            with self.assertRaises(GameplayContractError):
                package.write_package(target, records, review_root=REVIEWS)
            self.assertFalse(target.parent.exists())
            with self.assertRaises(GameplayContractError):
                package.write_package(target, self.records, review_root=Path(temporary) / "absent-history")
            self.assertFalse(target.parent.exists())
        with patch.object(package, "build_package", side_effect=AssertionError("invalid candidate must precede source access")) as build:
            with self.assertRaises(GameplayContractError):
                package.verify_source(records, "unread-invalid-source", review_root=REVIEWS)
            build.assert_not_called()

    def test_manifest_writer_and_source_use_owned_validated_snapshots(self):
        expected_manifest = package._bytes(package.manifest(self.records, review_root=REVIEWS))
        original_validate = package.validate_historical
        for operation in ("manifest", "write"):
            records = deepcopy(self.records)

            def mutate_caller_after_snapshot(*, review_root):
                binding = original_validate(review_root=review_root)
                records["projection.json"]["rules"].clear()
                records["preflight.json"]["findings"]["caller_mutation"] = True
                return binding

            with self.subTest(operation=operation), tempfile.TemporaryDirectory() as temporary:
                with patch.object(package, "validate_historical", side_effect=mutate_caller_after_snapshot):
                    if operation == "manifest":
                        result = package.manifest(records, review_root=REVIEWS)
                    else:
                        result = package.write_package(Path(temporary) / "new", records, review_root=REVIEWS)
                        self.assertEqual(package._bytes(package.load_package(Path(temporary) / "new", review_root=REVIEWS)), package._bytes(self.records))
                self.assertEqual(package._bytes(result), expected_manifest)
        records = deepcopy(self.records)

        def mutate_caller_during_source(*args, **kwargs):
            records["projection.json"]["rules"].clear()
            return deepcopy(self.records)

        with patch.object(package, "build_package", side_effect=mutate_caller_during_source):
            result = package.verify_source(records, "mocked-source-path", review_root=REVIEWS)
        self.assertEqual(result["projection_id"], self.records["projection.json"]["projection_id"])

    def test_closed_file_set_canonical_bytes_and_manifest_binding_mutations_fail(self):
        with tempfile.TemporaryDirectory() as temporary:
            target = Path(temporary) / "package"
            shutil.copytree(PACKAGE, target)
            manifest_path = target / "manifest.json"
            original = manifest_path.read_bytes()
            for mutate in (
                    lambda value: value["record_ids"].update({"preflight.json": value["projection_id"]}),
                    lambda value: value["files"]["projection.json"].update(bytes=float(value["files"]["projection.json"]["bytes"]))):
                value = json.loads(original)
                mutate(value)
                value["package_id"] = package._identity(package.PACKAGE_SCHEMA,
                    {key: item for key, item in value.items() if key != "package_id"})
                manifest_path.write_bytes(package._bytes(value))
                with self.subTest(mutate=mutate), self.assertRaises(GameplayContractError):
                    package.load_package(target, review_root=REVIEWS)
            manifest_path.write_bytes(original)
            record_path = target / "preflight.json"
            raw = record_path.read_bytes()
            record_path.write_bytes(b" " + raw)
            with self.assertRaises(GameplayContractError):
                package.load_package(target, review_root=REVIEWS)
            record_path.write_bytes(raw)
            (target / "foreign.json").write_bytes(b"{}")
            with self.assertRaises(GameplayContractError):
                package.load_package(target, review_root=REVIEWS)

    def test_retained_e_own_contract_and_enclosing_manifest_reject_coherent_rewrites(self):
        package.validate_historical(review_root=REVIEWS)
        with tempfile.TemporaryDirectory() as temporary:
            copied = Path(temporary) / "reviews"
            shutil.copytree(REVIEWS, copied)
            folder = copied / historical_e.PACKAGE_NAME
            record_path, parent_path = folder / "casting-parent-reassessment.json", folder / "manifest.json"
            original_record, original_parent = record_path.read_bytes(), parent_path.read_bytes()
            for domain, schema in ((package.RECORD_DOMAIN, 1), (historical_e.RECORD_DOMAIN, True), (historical_e.RECORD_DOMAIN, 1.0)):
                record, parent = json.loads(original_record), json.loads(original_parent)
                record["schema_version"] = schema
                reseal(record, domain)
                raw = package._bytes(record)
                parent["record_ids"][record_path.name] = record["review_id"]
                parent["files"][record_path.name] = {"bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}
                parent["package_id"] = package._identity(historical_e.PACKAGE_SCHEMA,
                    {key: item for key, item in parent.items() if key != "package_id"})
                record_path.write_bytes(raw)
                parent_path.write_bytes(package._bytes(parent))
                with self.subTest(domain=domain, schema=schema), self.assertRaises(GameplayContractError):
                    package.validate_historical(review_root=copied)
                target = Path(temporary) / "uncreated" / "new"
                with self.assertRaises(GameplayContractError):
                    package.write_package(target, self.records, review_root=copied)
                self.assertFalse(target.parent.exists())
            record_path.write_bytes(original_record)
            parent_path.write_bytes(original_parent)
            package.validate_historical(review_root=copied)

    def test_warm_reconstruction_exports_are_defensive_and_disk_validation_remains_fresh(self):
        raw_binding = package._bytes(package.retained_binding())
        raw_records = package._bytes(package._expected_records())
        binding = package.retained_binding()
        binding["rule_bindings"]["601.2e"]["rule_id"] = "sha256:" + "0" * 64
        binding["projection_components"].clear()
        records = package._expected_records()
        records["projection.json"]["rules"].clear()
        self.assertEqual(package._bytes(package.retained_binding()), raw_binding)
        self.assertEqual(package._bytes(package._expected_records()), raw_records)
        with tempfile.TemporaryDirectory() as temporary:
            copied = Path(temporary) / "reviews"
            shutil.copytree(REVIEWS, copied)
            old = copied / historical_e.PACKAGE_NAME / "casting-parent-reassessment.json"
            old.write_bytes(old.read_bytes() + b"\n")
            with self.assertRaises(GameplayContractError):
                package.validate_historical(review_root=copied)


if __name__ == "__main__":
    unittest.main()
