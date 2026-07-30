import contextlib
import hashlib
import io
import json
import tempfile
import unittest
import zipfile
from pathlib import Path

from external_ingestion import AdapterRegistry, ExternalDatasetError, ExternalDatasetIngestor
from mtglab.__main__ import main

TS = "2026-07-30T18:00:00+00:00"


class ExternalDatasetIngestionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.root = Path(self.temp.name)
        self.data = self.root / "input"; self.data.mkdir()
        self.ingestor = ExternalDatasetIngestor(self.root / "state")

    def tearDown(self): self.temp.cleanup()

    def manifest(self, filename, payload, **changes):
        value = {"manifest_schema":"external-dataset-manifest-v1", "dataset_name":"Supplied cards",
                 "logical_identity":"supplied-cards", "version":"1.0.0", "provider":"Example Provider",
                 "publication_date":"2026-07-29", "source_attribution":"Example Provider export",
                 "license":"CC0-1.0", "expected_entity_types":["card"], "schema_version":"example-v1",
                 "checksum":hashlib.sha256(payload).hexdigest(), "data_file":filename, "notes":"test only"}
        value.update(changes); return value

    def bare(self, suffix, payload, **changes):
        source = self.data / f"records{suffix}"; source.write_bytes(payload)
        manifest = self.data / "manifest.json"; manifest.write_text(json.dumps(self.manifest(source.name, payload, **changes)))
        return source, manifest

    def test_json_ingestion_reaches_review_without_promotion_and_is_idempotent(self):
        payload = json.dumps({"records":[{"id":"card-a", "entity_type":"card",
            "normalized":{"name":"Alpha"}}]}).encode()
        source, manifest = self.bare(".json", payload)
        first = self.ingestor.ingest(source, manifest, timestamp=TS)
        second = self.ingestor.ingest(source, manifest, timestamp="2026-07-30T19:00:00+00:00")
        self.assertEqual(first, second); self.assertEqual(first["status"], "awaiting_human_review")
        self.assertTrue(Path(first["review_package_path"]).exists())
        self.assertFalse((self.root / "state/canonical").exists())
        self.assertEqual(len(self.ingestor.list()), 1)

    def test_csv_validation_and_adapter_determinism(self):
        payload = b"id,name,entity_type\ncard-b,Beta,card\ncard-a,Alpha,card\n"
        source, manifest = self.bare(".csv", payload)
        result = self.ingestor.validate(source, manifest)
        self.assertEqual((result["format"], result["record_count"]), ("csv", 2))
        adapter = AdapterRegistry().resolve("anything.csv")
        self.assertEqual(list(adapter.records(payload)), list(adapter.records(payload)))
        registration = self.ingestor.ingest(source, manifest, timestamp=TS)
        normalized = json.loads((Path(registration["review_package_path"]).parent / "normalized.json").read_text())
        self.assertEqual([row["source_record_id"] for row in normalized["records"]], ["card-a", "card-b"])

    def test_zip_ingestion_requires_and_uses_manifest_and_payload(self):
        payload = json.dumps([{"id":"card-a", "normalized":{"name":"Alpha"}}]).encode()
        archive = self.data / "dataset.zip"
        with zipfile.ZipFile(archive, "w") as output:
            output.writestr("manifest.json", json.dumps(self.manifest("records.json", payload)))
            output.writestr("records.json", payload)
        result = self.ingestor.ingest(archive, timestamp=TS)
        self.assertEqual(result["manifest"]["data_file"], "records.json")

    def test_invalid_manifest_checksum_missing_file_and_unsupported_format_fail_closed(self):
        payload = b"[]"
        source, manifest = self.bare(".json", payload, provider="")
        with self.assertRaisesRegex(ExternalDatasetError, "missing required"): self.ingestor.validate(source, manifest)
        source, manifest = self.bare(".json", payload, checksum="0" * 64)
        with self.assertRaisesRegex(ExternalDatasetError, "checksum"): self.ingestor.ingest(source, manifest, timestamp=TS)
        source, manifest = self.bare(".xml", b"<records/>")
        with self.assertRaisesRegex(ExternalDatasetError, "unsupported"): self.ingestor.validate(source, manifest)
        archive = self.data / "missing.zip"
        with zipfile.ZipFile(archive, "w") as output: output.writestr("manifest.json", json.dumps(self.manifest("absent.json", payload)))
        with self.assertRaisesRegex(ExternalDatasetError, "missing"): self.ingestor.validate(archive)
        self.assertEqual(self.ingestor.list(), []); self.assertFalse((self.root / "state/canonical").exists())

    def test_duplicate_identity_with_different_manifest_is_rejected(self):
        first_payload = b'[{"id":"card-a","normalized":{"name":"A"}}]'
        source, manifest = self.bare(".json", first_payload)
        self.ingestor.ingest(source, manifest, timestamp=TS)
        second_payload = b'[{"id":"card-b","normalized":{"name":"B"}}]'
        source.write_bytes(second_payload)
        manifest.write_text(json.dumps(self.manifest(source.name, second_payload, notes="changed")))
        with self.assertRaisesRegex(ExternalDatasetError, "different content"):
            self.ingestor.ingest(source, manifest, timestamp=TS)

    def test_cli_validate_inspect_list_and_ingest(self):
        payload = b'[{"id":"card-a","normalized":{"name":"A"}}]'
        source, manifest = self.bare(".json", payload); state = self.root / "cli"
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(main(["--data-root",str(state),"ingest","validate",str(source),"--manifest",str(manifest)]), 0)
            self.assertEqual(main(["--data-root",str(state),"ingest","inspect",str(source),"--manifest",str(manifest)]), 0)
            self.assertEqual(main(["--data-root",str(state),"ingest",str(source),"--manifest",str(manifest),"--timestamp",TS]), 0)
            self.assertEqual(main(["--data-root",str(state),"ingest","list"]), 0)


if __name__ == "__main__": unittest.main()
