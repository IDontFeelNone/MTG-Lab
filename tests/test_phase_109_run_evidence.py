import json
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "data/validation/production-runs/30649546787/phase109_run_evidence_summary.json"
SHA256 = re.compile(r"^[0-9a-f]{64}$")


class Phase109RunEvidenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.value = json.loads(EVIDENCE.read_text())

    def test_schema_and_non_promoting_result(self):
        value = self.value
        self.assertEqual(value["schema_version"], "phase109-run-evidence-summary-v1")
        self.assertEqual(value["workflow_run_id"], "30649546787")
        self.assertEqual(value["run_result"], {
            "canonical_write": False,
            "mode": "dry-run",
            "promotion_performed": False,
        })

    def test_hash_shapes_and_source_lineage(self):
        value = self.value
        for digest in (
            value["artifact_inventory_digest"], value["batches"]["digest"],
            value["shards"]["finding_shards_digest"], value["source"]["artifact_sha256"],
            value["source_archive"]["sha256"],
        ):
            self.assertRegex(digest, SHA256)
        self.assertTrue(value["source"]["checksum_valid"])
        self.assertIn(value["source"]["artifact_sha256"][:12], value["dataset"]["identifier"])
        self.assertEqual(value["source_archive"]["name"],
                         "mtgjson-ingestion-30649546787.zip")

    def test_target_shards_and_batch_totals_are_internally_consistent(self):
        value = self.value
        targets = value["targets"]["completed_sets"]
        shards = {item["path"]: item for item in value["shards"]["candidate_shards"]}
        self.assertEqual(value["checkpoint"]["cards_processed"],
                         sum(item["cards"] for item in targets.values()))
        self.assertEqual(value["checkpoint"]["completed_sets"], len(targets))
        for unit, target in targets.items():
            shard = shards[f"{unit}.json"]
            self.assertEqual(shard["sha256"], target["sha256"])
            self.assertRegex(shard["sha256"], SHA256)
        batches = value["batches"]["items"]
        self.assertEqual(value["batches"]["count"], len(batches))
        self.assertEqual(value["dataset"]["candidate_count"],
                         sum(item["candidate_count"] for item in batches))
        self.assertEqual(value["dataset"]["candidate_count"],
                         sum(value["dataset"]["entity_counts"].values()))
        self.assertTrue(all(item["candidate_count"] <= value["batches"]["size"]
                            for item in batches))

    def test_workflow_retains_reconstructable_batch_inputs(self):
        workflow = (ROOT / ".github/workflows/mtgjson-production-ingestion.yml").read_text()
        self.assertIn("streaming/**/candidate-shards/*.json", workflow)
        self.assertIn("streaming/**/review-indexes/**/review-package.json", workflow)


if __name__ == "__main__":
    unittest.main()
