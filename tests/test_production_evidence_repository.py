"""Phase 111 production evidence repository tests (unittest only)."""
import contextlib
import hashlib
import io
import json
import tempfile
import unittest
import zipfile
from pathlib import Path

from mtglab.__main__ import main
from production_evidence import EvidenceError, ProductionEvidenceRepository


def canonical(value):
    return (json.dumps(value, indent=2, sort_keys=True) + "\n").encode()


class ProductionEvidenceTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.repository = ProductionEvidenceRepository(self.root / "data")

    def tearDown(self):
        self.temporary.cleanup()

    def archive(self, run_id="30663562841", mutate=None, omit=None):
        bundle_path = "review_batches/mb2/mb2-batch-1.json"
        bundle = canonical({"review_package": {"review_status": "pending"},
            "candidate_ids": ["card-1"], "dependency_closure": ["card-1"],
            "payload_references": ["sha256:payload"], "provenance": {"provider": "mtgjson"},
            "findings": [], "lineage": {"source_sha256": "a" * 64},
            "deterministic_digests": {"candidate_ids_sha256": "b" * 64}})
        files = {
            "metadata.json": canonical({"run_id": run_id, "source_dataset_id": "mtgjson-allprintings",
                                        "source_sha256": "a" * 64}),
            bundle_path: bundle,
            "batch_index.json": canonical({"batches": [{"batch_id": "mb2-batch-1",
                "target_product": "MB2", "candidate_ids_sha256": "b" * 64,
                "bundle_path": bundle_path, "bundle_sha256": hashlib.sha256(bundle).hexdigest()}]}),
            "lineage/source.json": canonical({"dataset_id": "mtgjson-allprintings",
                                               "sha256": "a" * 64}),
            "summaries/run.json": canonical({"canonical_write": False}),
        }
        if omit: files.pop(omit)
        inventory = [{"path": name, "sha256": hashlib.sha256(data).hexdigest(), "size": len(data)}
                     for name, data in sorted(files.items())]
        manifest = {"schema_version": "1.0.0", "workflow": {"run_id": run_id,
            "workflow_name": "MTGJSON production ingestion", "repository": "owner/MTG-Lab",
            "commit_sha": "c" * 40}, "source": {"dataset_id": "mtgjson-allprintings",
            "sha256": "a" * 64}, "files": inventory}
        files["manifest.json"] = canonical(manifest)
        if mutate:
            mutate(files)
        path = self.root / f"{run_id}.zip"
        with zipfile.ZipFile(path, "w") as archive:
            for name in sorted(files):
                info = zipfile.ZipInfo(name, (1980, 1, 1, 0, 0, 0))
                info.compress_type = zipfile.ZIP_DEFLATED
                archive.writestr(info, files[name])
        return path, hashlib.sha256(path.read_bytes()).hexdigest()

    def test_archive_and_internal_hash_verification_and_deterministic_intake(self):
        archive, digest = self.archive()
        result = self.repository.intake(archive, digest, "30663562841")
        self.assertEqual(result["run_id"], "30663562841")
        self.assertTrue(self.repository.verify("30663562841")["valid"])
        first = (self.repository.root / "index.json").read_bytes()
        self.repository.rebuild_index()
        self.assertEqual(first, (self.repository.root / "index.json").read_bytes())

    def test_archive_hash_run_identity_and_corruption_are_rejected(self):
        archive, digest = self.archive()
        with self.assertRaisesRegex(EvidenceError, "archive SHA-256"):
            self.repository.intake(archive, "0" * 64, "30663562841")
        with self.assertRaisesRegex(EvidenceError, "run identity"):
            self.repository.intake(archive, digest, "99")
        broken, broken_digest = self.archive("2", lambda files: files.__setitem__(
            "metadata.json", files["metadata.json"] + b" "))
        with self.assertRaisesRegex(EvidenceError, "internal hash"):
            self.repository.intake(broken, broken_digest, "2")

    def test_missing_file_and_duplicate_are_rejected(self):
        archive, digest = self.archive(omit="batch_index.json")
        with self.assertRaisesRegex(EvidenceError, "missing required file"):
            self.repository.intake(archive, digest, "30663562841")
        archive, digest = self.archive()
        self.repository.intake(archive, digest, "30663562841")
        with self.assertRaisesRegex(EvidenceError, "duplicate production run"):
            self.repository.intake(archive, digest, "30663562841")

    def test_deterministic_index_lookup_and_cli_json(self):
        for run_id in ("20", "10"):
            archive, digest = self.archive(run_id)
            self.repository.intake(archive, digest, run_id)
        self.assertEqual([item["run_id"] for item in self.repository.runs()["runs"]], ["10", "20"])
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            status = main(["--data-root", str(self.root / "data"), "evidence", "batches", "10",
                           "--format", "json"])
        self.assertEqual(status, 0)
        self.assertEqual(json.loads(output.getvalue())["batches"][0]["target_product"], "MB2")


if __name__ == "__main__":
    unittest.main()
