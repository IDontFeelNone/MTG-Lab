import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from acquisition import (AcquisitionEngine, AcquisitionError, AcquisitionProvider, FixtureProvider,
                         ProviderResponse, ProviderTrustPolicy, RawSnapshotStore,
                         assertions_from_normalized, compare_assertions, normalize_snapshot)
from validation.json_schema import validate_document

TS = "2026-07-30T12:00:00+00:00"


class RawAcquisitionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.root = Path(self.temp.name)
        self.payload = b'[{"id":"card-1","normalized":{"name":"Alpha"},"extra":7}]\n'
        self.provider = FixtureProvider({"cards": self.payload})
        self.store = RawSnapshotStore(self.root / "raw", max_payload_bytes=1000)
        self.engine = AcquisitionEngine(self.store, self.root / "runs"); self.engine.register(self.provider)

    def tearDown(self): self.temp.cleanup()

    def acquire(self): return self.engine.acquire("fixture", "cards", started_at=TS, run_id="run-1")

    def test_offline_snapshot_is_byte_exact_immutable_and_deterministic(self):
        first = self.acquire(); entry = first["downloaded_snapshots"][0]; directory = Path(entry["path"])
        self.assertEqual((directory / "payload.bin").read_bytes(), self.payload)
        self.assertEqual(entry["snapshot_id"], hashlib.sha256(self.payload).hexdigest())
        validate_document(json.loads((directory / "manifest.json").read_text()), "raw-snapshot", "v1")
        before = (directory / "manifest.json").read_bytes()
        second = self.engine.acquire("fixture", "cards", started_at=TS, run_id="run-2")
        self.assertEqual(second["unchanged_snapshots"][0]["path"], str(directory))
        self.assertEqual(before, (directory / "manifest.json").read_bytes())
        self.assertEqual(directory.parts[-3:-1], ("fixture", "cards"))

    def test_checksum_tampering_and_security_guards(self):
        directory = Path(self.acquire()["downloaded_snapshots"][0]["path"])
        (directory / "payload.bin").write_bytes(b"tampered")
        with self.assertRaisesRegex(AcquisitionError, "checksum"): self.store.load(directory)
        with self.assertRaises(AcquisitionError): self.engine.acquire("fixture", "../bad", started_at=TS)
        with self.assertRaisesRegex(AcquisitionError, "size"): RawSnapshotStore(self.root / "tiny", 1).store(
            "fixture", self.provider.build_request("cards", {}), self.provider.retrieve(self.provider.build_request("cards", {})), TS)

    def test_normalization_lineage_unmapped_retention_and_assertions(self):
        directory = Path(self.acquire()["downloaded_snapshots"][0]["path"])
        normalized = normalize_snapshot(self.provider, self.store, directory, self.root / "normalized.json")
        record = normalized["records"][0]
        self.assertEqual(record["raw_snapshot_id"], directory.name)
        self.assertEqual(record["unmapped_source_fields"]["extra"], 7)
        self.assertEqual(record["canonical_values"], {})
        validate_document(record, "normalized-source-record", "v1")
        assertions = assertions_from_normalized(normalized, ProviderTrustPolicy("authoritative_structured", .8, "verified"), TS)
        self.assertEqual(assertions[0]["status"], "candidate")
        self.assertIn(directory.name, assertions[0]["notes"])
        validate_document({k: v for k, v in assertions[0].items() if k != "schema_version"}, "assertion", "v3")
        self.assertFalse((self.root / "canonical").exists())

    def test_changed_assertions_are_reported_not_replaced(self):
        directory = Path(self.acquire()["downloaded_snapshots"][0]["path"])
        old = assertions_from_normalized(normalize_snapshot(self.provider, self.store, directory, self.root / "n1.json"), ProviderTrustPolicy(), TS)
        other = FixtureProvider({"cards2": b'[{"id":"card-1","normalized":{"name":"Beta"}}]'})
        engine = AcquisitionEngine(self.store, self.root / "runs2"); engine.register(other)
        second = engine.acquire("fixture", "cards2", started_at=TS, run_id="run-2")
        new = assertions_from_normalized(normalize_snapshot(other, self.store, Path(second["downloaded_snapshots"][0]["path"]), self.root / "n2.json"), ProviderTrustPolicy(), TS)
        report = compare_assertions(old, new)
        self.assertEqual(report["changes"][0]["kind"], "changed"); self.assertEqual(len(report["conflicts"]), 1)

    def test_partial_failure_remains_auditable_and_resumable(self):
        provider = FixtureProvider({"good": [], "bad": []}, fail_datasets={"bad"})
        engine = AcquisitionEngine(self.store, self.root / "partial"); engine.register(provider)
        report = engine.acquire("fixture", ["good", "bad"], started_at=TS, run_id="partial-run")
        self.assertEqual(report["status"], "partial"); self.assertTrue(report["resumable"])
        self.assertEqual(engine.report("partial-run"), report)

    def test_malformed_content_duplicates_type_and_provider_collision(self):
        for payload, message in [(b"{", "malformed"), (b'[{"id":"x"},{"id":"x"}]', "duplicate")]:
            provider = FixtureProvider({"bad": payload}); response = provider.retrieve(provider.build_request("bad", {}))
            ref = self.store.store("fixture", provider.build_request("bad", {}), response, TS)
            with self.assertRaisesRegex(AcquisitionError, message): normalize_snapshot(provider, self.store, ref.path, self.root / (message + ".json"))
        request = self.provider.build_request("cards", {})
        with self.assertRaisesRegex(AcquisitionError, "unsupported"): self.store.store(
            "fixture", request, ProviderResponse(b"x", "application/octet-stream"), TS)
        with self.assertRaisesRegex(AcquisitionError, "credentials"): self.store.store(
            "fixture", self.provider.build_request("cards", {"token": "nope"}),
            self.provider.retrieve(request), TS)
        with self.assertRaisesRegex(AcquisitionError, "collision"): self.engine.register(FixtureProvider({}))


if __name__ == "__main__": unittest.main()
