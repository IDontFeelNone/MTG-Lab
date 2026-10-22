"""Regression boundaries shared by the optimized c/d retained-evidence paths."""
from contextlib import ExitStack
from copy import deepcopy
import json
import os
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest import mock

from gameplay_rules.errors import GameplayContractError
from gameplay_rules.shared_target_declaration import package as declaration
from gameplay_rules.shared_target_allocation import package as allocation
from gameplay_rules.shared_proposal_legality import package as legality

ROOT = Path(__file__).resolve().parents[1]
REVIEWS = ROOT / "reference-reviews"
PACKAGES = (declaration, allocation)


def retained_records(package):
    return {name: json.loads((REVIEWS / package.PACKAGE_NAME / name).read_bytes())
        for name in package.RECORD_NAMES}


class SharedStageValidationTests(unittest.TestCase):
    def test_fixed_metadata_and_records_return_private_copies(self):
        for package in PACKAGES:
            with self.subTest(package=package.PACKAGE_NAME):
                binding = package.retained_binding()
                binding["prior_package_ids"].clear()
                self.assertTrue(package.retained_binding()["prior_package_ids"])
                records = package._expected_records()
                records["projection.json"]["rules"].clear()
                self.assertEqual(package._bytes(package._expected_records()),
                    package._bytes(retained_records(package)))

    def test_public_history_operations_recheck_current_content_after_warmup(self):
        # Different history generations exercise baseline pins and both newly
        # shared successor checks. Equal-length replacement and restored mtime
        # ensure neither paths nor timestamps can authorize warmed operations.
        for package in PACKAGES:
            records = retained_records(package)
            with self.subTest(package=package.PACKAGE_NAME), tempfile.TemporaryDirectory() as temporary:
                review = Path(temporary) / "reviews"
                shutil.copytree(REVIEWS, review)
                package.manifest(records, review_root=review)
                selections = [
                    review / "gameplay-rules-source-versioning" / "manifest.json",
                    review / package.DESIGN_NAME / "source-inspection.json",
                ]
                if package is allocation:
                    selections.append(review / declaration.PACKAGE_NAME / "projection.json")
                for path in selections:
                    raw = path.read_bytes()
                    stamp = path.stat()
                    try:
                        path.write_bytes(bytes([raw[0] ^ 1]) + raw[1:])
                        os.utime(path, ns=(stamp.st_atime_ns, stamp.st_mtime_ns))
                        operations = (
                            lambda: package.manifest(records, review_root=review),
                            lambda: package.rebuild_package(review_root=review),
                            lambda: package.load_package(REVIEWS / package.PACKAGE_NAME, review_root=review),
                            lambda: package.write_package(Path(temporary) / "uncreated" / "package",
                                records, review_root=review),
                        )
                        for operation in operations:
                            with self.subTest(history=path.name), self.assertRaises(GameplayContractError):
                                operation()
                        self.assertFalse((Path(temporary) / "uncreated").exists())
                    finally:
                        path.write_bytes(raw)
                self.assertEqual(package._bytes(package.load_package(
                    REVIEWS / package.PACKAGE_NAME, review_root=review)), package._bytes(records))

    def test_selected_review_root_is_honored_with_cold_and_warm_metadata(self):
        for package in (*PACKAGES, legality):
            records = retained_records(package)
            with self.subTest(package=package.PACKAGE_NAME), tempfile.TemporaryDirectory() as temporary:
                review = Path(temporary) / "reviews"
                shutil.copytree(REVIEWS, review)
                empty = Path(temporary) / "empty"
                empty.mkdir()
                for predecessor in (*PACKAGES, legality):
                    predecessor._retained_binding_bytes.cache_clear()
                    predecessor._expected_record_bytes.cache_clear()
                # The actual selected copy must suffice even if every default
                # directory is unusable, with every predecessor cache cold too.
                with ExitStack() as patches:
                    for predecessor in (*PACKAGES, legality):
                        patches.enter_context(mock.patch.object(predecessor,
                            "DEFAULT_REVIEW_ROOT", Path(temporary) / "absent-default"))
                    metadata = package.manifest(records, review_root=review)
                    self.assertEqual(package._bytes(metadata),
                        (REVIEWS / package.PACKAGE_NAME / "manifest.json").read_bytes())
                    for invalid in (empty, Path(temporary) / "missing"):
                        with self.assertRaises(GameplayContractError):
                            package.manifest(records, review_root=invalid)
                        destination = Path(temporary) / "uncreated" / "package"
                        with self.assertRaises(GameplayContractError):
                            package.write_package(destination, records, review_root=invalid)
                        self.assertFalse(destination.parent.exists())

    def test_cold_reconstruction_consumes_the_captured_caller_snapshot(self):
        for package in PACKAGES:
            from importlib import import_module
            reviews = import_module(package.__package__ + ".reviews")
            actual = reviews.authored_records
            for boundary in ("validate_records", "manifest", "write_package", "current_view", "composite_view"):
                canonical = retained_records(package)
                caller = deepcopy(canonical)
                expected_manifest = json.loads((REVIEWS / package.PACKAGE_NAME / "manifest.json").read_bytes())
                package._expected_record_bytes.cache_clear()

                def reconstruct_and_mutate(*args, **kwargs):
                    caller["projection.json"]["rules"].clear()
                    caller["preservation-readiness.json"]["findings"].clear()
                    return actual(*args, **kwargs)

                with self.subTest(package=package.PACKAGE_NAME, boundary=boundary), tempfile.TemporaryDirectory() as temporary:
                    with mock.patch.object(reviews, "authored_records", side_effect=reconstruct_and_mutate) as hook:
                        if boundary == "validate_records":
                            result = package.validate_records(caller)
                            self.assertEqual(package._bytes(result), package._bytes(canonical))
                        elif boundary == "manifest":
                            self.assertEqual(package.manifest(caller, review_root=REVIEWS), expected_manifest)
                        elif boundary == "write_package":
                            destination = Path(temporary) / "new"
                            self.assertEqual(package.write_package(destination, caller,
                                review_root=REVIEWS), expected_manifest)
                            for name in package.RECORD_NAMES | {"manifest.json"}:
                                self.assertEqual((destination / name).read_bytes(),
                                    (REVIEWS / package.PACKAGE_NAME / name).read_bytes())
                        elif boundary == "current_view":
                            result = package.current_view(caller)
                            self.assertEqual(len(result["records"]["projection.json"]["rules"]), 1)
                            self.assertEqual(result["package_id"], expected_manifest["package_id"])
                            self.assertTrue(result["records"]["preservation-readiness.json"]["findings"])
                        else:
                            result = package.composite_view(caller)
                            self.assertEqual(result["total_projected_rule_count"],
                                canonical["composite-coverage.json"]["findings"]["total_projected_rule_count"])
                    hook.assert_called_once()
                    self.assertEqual(caller["projection.json"]["rules"], [])

    def test_history_validation_cannot_replace_writer_or_view_snapshot(self):
        for package in PACKAGES:
            canonical = retained_records(package)
            package.validate_records(canonical)
            actual = package.validate_historical
            for boundary in ("manifest", "write_package", "current_view", "composite_view"):
                caller = deepcopy(canonical)

                def history_and_mutate(*args, **kwargs):
                    caller["projection.json"]["rules"].clear()
                    return actual(*args, **kwargs)

                with self.subTest(package=package.PACKAGE_NAME, boundary=boundary), tempfile.TemporaryDirectory() as temporary:
                    with mock.patch.object(package, "validate_historical", side_effect=history_and_mutate):
                        if boundary == "manifest":
                            result = package.manifest(caller, review_root=REVIEWS)
                            self.assertEqual(package._bytes(result),
                                (REVIEWS / package.PACKAGE_NAME / "manifest.json").read_bytes())
                        elif boundary == "write_package":
                            destination = Path(temporary) / "new"
                            package.write_package(destination, caller, review_root=REVIEWS)
                            self.assertEqual((destination / "projection.json").read_bytes(),
                                (REVIEWS / package.PACKAGE_NAME / "projection.json").read_bytes())
                        elif boundary == "current_view":
                            result = package.current_view(caller)
                            self.assertEqual(result["records"]["projection.json"], canonical["projection.json"])
                        else:
                            result = package.composite_view(caller)
                            self.assertEqual(result["total_projected_rule_count"],
                                canonical["composite-coverage.json"]["findings"]["total_projected_rule_count"])

    def test_synthetic_source_comparison_consumes_the_same_private_snapshot(self):
        # This synthetic builder supplies no artifact or fresh source authority.
        for package in PACKAGES:
            canonical = retained_records(package)
            caller = deepcopy(canonical)

            def synthetic_reproduction(*args, **kwargs):
                caller["projection.json"]["rules"].clear()
                return deepcopy(canonical)

            with self.subTest(package=package.PACKAGE_NAME), mock.patch.object(
                    package, "build_package", side_effect=synthetic_reproduction):
                result = package.verify_source(caller, "synthetic-no-source-authority", review_root=REVIEWS)
                self.assertEqual(result["source_anchor"], canonical["projection.json"]["rules"][0]["source_anchor"])
                self.assertEqual(result["projection_id"], canonical["projection.json"]["projection_id"])
