"""Review-only package integrity, strict typing and explicit source reproduction."""
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

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import shared_casting_stage_gap_design as review

REVIEW_ROOT = ROOT / "reference-reviews"
PACKAGE = REVIEW_ROOT / review.PACKAGE_NAME


def reseal(record, domain=review.RECORD_DOMAIN):
    body = {key: value for key, value in record.items() if key != "review_id"}
    record["review_id"] = "sha256:" + sha256_identity({"domain": domain, "content": body})
    return record


class SharedCastingStageReviewTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.records = review.load_package(PACKAGE, review_root=REVIEW_ROOT)

    def test_offline_load_and_manifest_preserve_exact_canonical_bytes(self):
        records = review.validate_records(self.records)
        for name, value in records.items():
            self.assertEqual(review._bytes(value), (PACKAGE / name).read_bytes())
        metadata = review.manifest(records)
        self.assertEqual(review._bytes(metadata), (PACKAGE / "manifest.json").read_bytes())
        self.assertEqual(metadata["current_projection_allowlist"], [])
        self.assertEqual(metadata["new_source_units_projected"], 0)
        self.assertEqual(metadata["projected_rule_count_after"], 88)
        self.assertEqual(metadata["existing_projection_count_after"], 10)
        self.assertFalse(metadata["source_coverage_graph_changed"])
        self.assertNotIn("projection.json", records)
        records["gap-matrix.json"]["schema_version"] = 2
        self.assertEqual(self.records["gap-matrix.json"]["schema_version"], 1)

    def test_record_mismatches_and_wrong_hashing_domain_are_rejected(self):
        for mutate in (
            lambda r: r.update(review_id="sha256:" + "0" * 64),
            lambda r: reseal(r, "gameplay-bounded-activated-ability-procedure-record-v1"),
            lambda r: r.update(record_type="foreign-record"),
            lambda r: r.update(projection_id=r.pop("review_id")),
        ):
            records = deepcopy(self.records)
            mutate(records["gap-matrix.json"])
            with self.subTest(mutation=mutate), self.assertRaises(GameplayContractError):
                review.validate_records(records)

    def test_coherent_foreign_record_substitution_is_rejected(self):
        records = deepcopy(self.records)
        record = records["gap-matrix.json"]
        record["findings"]["foreign_review_claim"] = "unreviewed replacement"
        reseal(record)
        with self.assertRaisesRegex(GameplayContractError, "EXACT_AUTHORED_REVIEW_CONTENT_REQUIRED"):
            review.validate_records(records)
        records = deepcopy(self.records)
        records["gap-matrix.json"] = deepcopy(records["source-inspection.json"])
        records["gap-matrix.json"]["record_type"] = "gap-matrix"
        reseal(records["gap-matrix.json"])
        with self.assertRaises(GameplayContractError):
            review.validate_records(records)

    def test_record_integer_boolean_float_substitutions_are_not_equal(self):
        for replacement in (True, False, 1.0):
            records = deepcopy(self.records)
            records["gap-matrix.json"]["schema_version"] = replacement
            reseal(records["gap-matrix.json"])
            with self.subTest(value=replacement), self.assertRaises(GameplayContractError):
                review.manifest(records)
        for field, replacement in (("new_source_units_projected", False),
                ("new_source_units_projected", 0.0), ("review_only", 1), ("review_only", 1.0),
                ("execution_authorized", 0), ("execution_authorized", 0.0)):
            records = deepcopy(self.records)
            records["readiness.json"]["findings"][field] = replacement
            reseal(records["readiness.json"])
            with self.subTest(field=field, value=replacement), self.assertRaises(GameplayContractError):
                review.validate_records(records)
        for replacement in (True, 296470.0):
            records = deepcopy(self.records)
            records["source-inspection.json"]["findings"]["review_spans"][0]["byte_start"] = replacement
            reseal(records["source-inspection.json"])
            with self.subTest(value=replacement), self.assertRaises(GameplayContractError):
                review.validate_records(records)

    def test_nonplain_and_nonfinite_candidates_are_rejected(self):
        class IntegerSubclass(int):
            pass
        for replacement in (IntegerSubclass(1), float("nan"), float("inf"), (1,)):
            records = deepcopy(self.records)
            records["gap-matrix.json"]["schema_version"] = replacement
            with self.subTest(kind=type(replacement)), self.assertRaises(GameplayContractError):
                review.validate_records(records)
        records = deepcopy(self.records)
        records["gap-matrix.json"][1] = "nonstring key"
        with self.assertRaises(GameplayContractError):
            review.validate_records(records)

    def test_valid_write_load_round_trip_and_append_only_destination(self):
        with tempfile.TemporaryDirectory() as temporary:
            target = Path(temporary) / "package"
            metadata = review.write_package(target, self.records, review_root=REVIEW_ROOT)
            loaded = review.load_package(target, review_root=REVIEW_ROOT)
            self.assertEqual(review._bytes(loaded), review._bytes(self.records))
            self.assertEqual(review._bytes(metadata), (target / "manifest.json").read_bytes())
            for name in review.RECORD_NAMES | {"manifest.json"}:
                self.assertEqual((target / name).read_bytes(), (PACKAGE / name).read_bytes())
            with self.assertRaisesRegex(GameplayContractError, "APPEND_ONLY"):
                review.write_package(target, self.records, review_root=REVIEW_ROOT)

    def test_invalid_write_is_rejected_before_any_output_is_created(self):
        records = deepcopy(self.records)
        records["readiness.json"]["findings"]["execution_authorized"] = True
        reseal(records["readiness.json"])
        with tempfile.TemporaryDirectory() as temporary:
            target = Path(temporary) / "new-parent" / "package"
            with self.assertRaises(GameplayContractError):
                review.write_package(target, records, review_root=REVIEW_ROOT)
            self.assertFalse(target.parent.exists())
            with self.assertRaises(GameplayContractError):
                review.write_package(target, self.records, review_root=Path(temporary) / "missing-history")
            self.assertFalse(target.parent.exists())

    def test_closed_file_set_canonical_json_and_symlink_boundaries(self):
        with tempfile.TemporaryDirectory() as temporary:
            target = Path(temporary) / "package"
            shutil.copytree(PACKAGE, target)
            extra = target / "foreign.json"
            extra.write_text("{}\n")
            with self.assertRaises(GameplayContractError):
                review.load_package(target, review_root=REVIEW_ROOT)
            extra.unlink()
            record = target / "gap-matrix.json"
            original = record.read_bytes()
            record.write_bytes(b" " + original)
            with self.assertRaises(GameplayContractError):
                review.load_package(target, review_root=REVIEW_ROOT)
            record.write_bytes(original.replace(b'{', b'{"duplicate":0,"duplicate":1,', 1))
            with self.assertRaises(GameplayContractError):
                review.load_package(target, review_root=REVIEW_ROOT)
            record.write_bytes(original)
            link = Path(temporary) / "link"
            link.symlink_to(target, target_is_directory=True)
            with self.assertRaises(GameplayContractError):
                review.load_package(link, review_root=REVIEW_ROOT)
            with self.assertRaises(GameplayContractError):
                review.write_package(link / "new", self.records, review_root=REVIEW_ROOT)
            self.assertFalse((target / "new").exists())

    def test_manifest_json_distinct_substitutions_and_rehash_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            target = Path(temporary) / "package"
            shutil.copytree(PACKAGE, target)
            for field, replacement in (("review_only", 1), ("new_source_units_projected", False),
                    ("projected_rule_count_after", 88.0), ("future_milestone_authorized", 0)):
                value = review.manifest(self.records)
                value[field] = replacement
                body = {key: item for key, item in value.items() if key != "package_id"}
                value["package_id"] = "sha256:" + sha256_identity({"domain": review.PACKAGE_SCHEMA, "content": body})
                (target / "manifest.json").write_bytes(review._bytes(value))
                with self.subTest(field=field), self.assertRaises(GameplayContractError):
                    review.load_package(target, review_root=REVIEW_ROOT)

    def test_actual_historical_schema_fields_domains_and_manifest_bindings(self):
        binding = review.validate_historical(review_root=REVIEW_ROOT)
        self.assertEqual(binding["pr199_review_binding_count"], 7)
        self.assertEqual(binding["pr200_review_binding_count"], 9)
        self.assertEqual(binding["historical_review_binding_count"], 58)
        self.assertEqual(binding["pr200_projection_identity"], review.PR200_PROJECTION_ID)
        self.assertEqual(binding["prior_package_ids"][review.historical_projection.PACKAGE_NAME], review.PR200_PACKAGE_ID)
        self.assertEqual(binding["historical_acquisition_identity"], "sha256:669d7db9ebcaf97853058fd62f408ce3c6596d5dae0ee72ff39d2ba9df56bb53")

    def test_retained_context_rule_and_review_references_match_schema_owned_identities(self):
        review._validate_context_bindings(self.records, review_root=REVIEW_ROOT)
        records = deepcopy(self.records)
        context = records["gap-matrix.json"]["findings"]["rows"][0]["retained_projected_context"][0]
        context["rule_id"] = context["projection_id"]
        with self.assertRaisesRegex(GameplayContractError, "RETAINED_CONTEXT_RULE_REFERENCE_BINDING_MISMATCH"):
            review._validate_context_bindings(records, review_root=REVIEW_ROOT)
        records = deepcopy(self.records)
        matrix = records["consumer-dependencies.json"]["findings"]["casting_parent_provenance"]
        matrix["stage_matrix_id"] = matrix["projection_id"]
        with self.assertRaisesRegex(GameplayContractError, "RETAINED_CASTING_STAGE_MATRIX_BINDING_MISMATCH"):
            review._validate_context_bindings(records, review_root=REVIEW_ROOT)

    def test_wrong_historical_own_field_domain_and_bound_bytes_fail(self):
        name = review.historical_projection.PACKAGE_NAME
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            shutil.copytree(REVIEW_ROOT / name, root / name)
            path = root / name / "casting-import.json"
            original = path.read_bytes()
            for mutate in (
                lambda r: r.update(review_id="sha256:" + "0" * 64),
                lambda r: reseal(r, review.historical_design.RECORD_DOMAIN),
                lambda r: r.update(schema_version=True),
                lambda r: r.update(projection_id=r.pop("review_id")),
            ):
                value = json.loads(original)
                mutate(value)
                path.write_bytes(review._bytes(value))
                with self.subTest(mutation=mutate), self.assertRaises(GameplayContractError):
                    review._historical_envelope(root, name, review.historical_projection, review.PR200_PACKAGE_ID)
            path.write_bytes(original)
            value = json.loads((root / name / "manifest.json").read_bytes())
            value["record_ids"]["casting-import.json"] = review.PR200_PROJECTION_ID
            body = {key: item for key, item in value.items() if key != "package_id"}
            value["package_id"] = "sha256:" + sha256_identity({"domain": review.historical_projection.PACKAGE_SCHEMA, "content": body})
            (root / name / "manifest.json").write_bytes(review._bytes(value))
            with self.assertRaisesRegex(GameplayContractError, "HISTORICAL_PACKAGE_BINDING_MISMATCH"):
                review._historical_envelope(root, name, review.historical_projection, review.PR200_PACKAGE_ID)

    def test_coherently_rehashed_foreign_historical_package_fails_before_output(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            historical = root / "history"
            shutil.copytree(REVIEW_ROOT, historical)
            package = historical / review.historical_projection.PACKAGE_NAME
            path = package / "casting-import.json"
            record = json.loads(path.read_bytes())
            record["findings"]["foreign_claim"] = True
            reseal(record, review.historical_projection.RECORD_DOMAIN)
            raw = review._bytes(record)
            path.write_bytes(raw)
            metadata = json.loads((package / "manifest.json").read_bytes())
            metadata["record_ids"][path.name] = record["review_id"]
            metadata["files"][path.name] = {"bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}
            body = {key: item for key, item in metadata.items() if key != "package_id"}
            metadata["package_id"] = "sha256:" + sha256_identity({"domain": review.historical_projection.PACKAGE_SCHEMA, "content": body})
            (package / "manifest.json").write_bytes(review._bytes(metadata))
            target = root / "new" / "package"
            with self.assertRaises(GameplayContractError):
                review.write_package(target, self.records, review_root=historical)
            self.assertFalse(target.parent.exists())

    def test_configured_missing_or_invalid_artifact_fails_and_paths_are_not_reported(self):
        with tempfile.TemporaryDirectory() as temporary:
            missing = Path(temporary) / "sensitive-artifact-location"
            invalid = Path(temporary) / "invalid"
            invalid.write_bytes(b"invented fixture is not the required artifact")
            for path in (missing, invalid):
                with self.subTest(exists=path.exists()), self.assertRaisesRegex(GameplayContractError, "SOURCE_ARTIFACT_OR_VERIFICATION_LINEAGE_INVALID") as caught:
                    review.verify_source(self.records, path, review_root=REVIEW_ROOT)
                self.assertNotIn(str(path), str(caught.exception))
            env = {**os.environ, "PYTHONPATH": str(ROOT / "src"), review.SOURCE_ENV: str(missing)}
            result = subprocess.run([sys.executable, str(ROOT / "scripts/shared_casting_stage_gap_design.py"),
                "verify-source", "--review-root", str(REVIEW_ROOT)], cwd=ROOT, env=env,
                capture_output=True, text=True, check=False)
            self.assertEqual(result.returncode, 1)
            self.assertNotIn(str(missing), result.stdout + result.stderr)
            self.assertNotIn("SKIPPED", result.stdout + result.stderr)

    def test_unconfigured_source_selector_reports_explicit_skip_separate_from_metadata(self):
        env = {**os.environ, "PYTHONPATH": str(ROOT / "src")}
        env.pop(review.SOURCE_ENV, None)
        result = subprocess.run([sys.executable, str(ROOT / "scripts/shared_casting_stage_gap_design.py"),
            "verify-source", "--review-root", str(REVIEW_ROOT)], cwd=ROOT, env=env,
            capture_output=True, text=True, check=False)
        self.assertEqual(result.returncode, 0, result.stderr)
        value = json.loads(result.stdout)
        self.assertEqual(value["source_reproduction"], "SKIPPED_SOURCE_SELECTOR_UNCONFIGURED")
        self.assertEqual(value["status"], "VALID_OFFLINE_METADATA_NOT_FRESH_SOURCE_REPRODUCTION")

    def test_review_span_metadata_has_no_projected_anchor_registration(self):
        self.assertEqual(tuple(row["reference"] for row in review.REVIEW_SPANS), review.REFERENCES)
        self.assertEqual([row["line_count"] for row in review.REVIEW_SPANS], [2, 1, 1, 1])
        for row in review.REVIEW_SPANS:
            self.assertNotIn("anchor_id", row)
            self.assertNotIn("rule_id", row)
            self.assertEqual(row["ending_physical_line"] - row["starting_physical_line"] + 1, row["line_count"])

    def test_actual_attached_original_source_fingerprints_reproduce(self):
        selector = os.environ.get(review.SOURCE_ENV)
        if selector is None:
            self.skipTest("source-dependent skip: MTGLAB_SHARED_CASTING_STAGE_SOURCE is unconfigured; no fresh source reproduction")
        result = review.verify_source(self.records, selector, review_root=REVIEW_ROOT)
        self.assertEqual(result["status"], "VERIFIED_EXACT_FOUR_REVIEW_FINGERPRINTS")
        self.assertEqual(review._bytes(result["review_spans"]), review._bytes(list(review.REVIEW_SPANS)))
        self.assertEqual(result["new_source_units_projected"], 0)
        self.assertFalse(result["source_body_retained"])
        self.assertEqual(result["registered_projected_source_anchors_added"], 0)


if __name__ == "__main__":
    unittest.main()
