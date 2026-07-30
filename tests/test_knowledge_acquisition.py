import copy
import json
import tempfile
import unittest
from pathlib import Path

from acquisition import (AcquisitionEngine, AcquisitionError, FixtureProvider, ProviderPolicy,
                         ProviderTrustPolicy, RawSnapshotStore, assertions_from_normalized,
                         build_review_package, dataset_identity, generate_reports,
                         normalize_snapshot, validate_pipeline, validate_review_package)
from validation.json_schema import validate_document

TS = "2026-07-30T12:00:00+00:00"
FIXTURE = Path("data/fixtures/knowledge/reviewed-cards.json")
POLICY = Path("data/fixtures/knowledge/provider-policy.json")


class KnowledgeAcquisitionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.root = Path(self.temp.name)
        self.provider = FixtureProvider({"reviewed-cards": FIXTURE.read_bytes()})
        self.store = RawSnapshotStore(self.root / "raw")
        self.engine = AcquisitionEngine(self.store, self.root / "runs"); self.engine.register(self.provider)
        self.run = self.engine.acquire("fixture", "reviewed-cards", started_at=TS, run_id="phase-84")
        path = Path(self.run["downloaded_snapshots"][0]["path"])
        self.snapshot = json.loads((path / "manifest.json").read_text())
        self.normalized = normalize_snapshot(self.provider, self.store, path, self.root / "normalized.json")
        self.assertions = assertions_from_normalized(
            self.normalized, ProviderTrustPolicy("authoritative_structured", .8, "verified"), TS)
        self.policy = ProviderPolicy.from_dict(json.loads(POLICY.read_text()))

    def tearDown(self): self.temp.cleanup()

    def package(self):
        return build_review_package(self.run, [self.snapshot], [self.normalized], self.assertions,
                                    self.policy, "fixture-v1")

    def test_dataset_identity_and_repeated_acquisition_are_deterministic(self):
        identity = dataset_identity("fixture", "cards", "v1", "2026-07-30", "a" * 64)
        self.assertEqual(identity, dataset_identity("fixture", "cards", "v1", "2026-07-30", "a" * 64))
        validate_document(identity, "dataset-identity", "v1")
        second = self.engine.acquire("fixture", "reviewed-cards", started_at=TS, run_id="phase-84-repeat")
        self.assertEqual(second["unchanged_snapshots"][0]["snapshot_id"], self.snapshot["snapshot_id"])

    def test_provider_policy_is_independent_and_enforced(self):
        self.assertEqual(self.policy.provider_id, self.provider.provider_id)
        wrong = ProviderPolicy("other", "official", 1, (), "Other", ("card",))
        result = validate_pipeline(self.run, [self.snapshot], [self.normalized], self.assertions, wrong)
        self.assertFalse(result["valid"]); self.assertIn("run/provider policy identity mismatch", result["errors"])

    def test_review_package_is_reproducible_complete_and_noncanonical(self):
        first = self.package(); second = self.package()
        self.assertEqual(first, second); validate_review_package(first)
        validate_document(first, "knowledge-review-package", "v1")
        validate_document(self.policy.as_dict(), "provider-policy", "v1")
        self.assertEqual(first["promotion_recommendation"], "hold")
        self.assertGreater(first["unknown_values"]["count"], 0)
        self.assertFalse((self.root / "canonical").exists())

    def test_malformed_review_packages_fail(self):
        package = self.package(); package.pop("evidence_summary")
        with self.assertRaisesRegex(AcquisitionError, "incomplete"): validate_review_package(package)
        package = self.package(); package["candidate_assertions"] = []
        with self.assertRaisesRegex(AcquisitionError, "identity mismatch"): validate_review_package(package)

    def test_conflicts_changes_unknowns_and_reports(self):
        conflicting = copy.deepcopy(self.assertions[0]); conflicting["id"] = "src-" + "f" * 64
        conflicting["asserted_value"] = "contradiction"
        assertions = self.assertions + [conflicting]
        previous = [dict(self.assertions[0], asserted_value="previous")]
        validation = validate_pipeline(self.run, [self.snapshot], [self.normalized], assertions, self.policy)
        reports = generate_reports(self.run, [self.snapshot], [self.normalized], assertions, validation, previous)
        self.assertEqual(reports["conflict_report"]["count"], 1)
        self.assertGreaterEqual(len(reports["changed_values"]), 1)
        self.assertGreater(reports["unknown_field_report"]["count"], 0)
        self.assertEqual(reports, generate_reports(self.run, [self.snapshot], [self.normalized], assertions, validation, previous))

    def test_partial_and_malformed_inputs_fail_before_review(self):
        bad = copy.deepcopy(self.normalized); bad["records"][0]["source_values"] = "bad"
        with self.assertRaisesRegex(AcquisitionError, "pipeline validation failed"):
            build_review_package(self.run, [self.snapshot], [bad], self.assertions, self.policy, "v1")
        partial = copy.deepcopy(self.run); partial["status"] = "partial"
        package = build_review_package(partial, [self.snapshot], [self.normalized], self.assertions, self.policy, "v1")
        self.assertEqual(package["acquisition_run"]["status"], "partial")


if __name__ == "__main__": unittest.main()
