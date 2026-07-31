"""Phase 110A target-specific retained review artifact tests (unittest only)."""
import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from providers.mtgjson.streaming import StreamingMTGJSONPlanner


def write_corpus(path):
    data = {}
    for code, name, offset in (("MB2", "Mystery Booster 2", 0),
                               ("MSH", "Marvel Super Heroes", 100)):
        data[code] = {"code": code, "name": name, "cards": [{
            "uuid": f"00000000-0000-0000-0000-{offset + number:012d}",
            "name": f"{code} Card {number}", "number": str(number), "rarity": "common",
            "language": "English", "finishes": ["nonfoil"], "layout": "normal",
            "colors": []} for number in range(1, 4)]}
    path.write_text(json.dumps({"meta": {"date": "2026-07-31", "version": "5.2.1"},
                                "data": data}))
    return hashlib.sha256(path.read_bytes()).hexdigest()


class TargetReviewArtifactTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.source = self.root / "AllPrintings.json"
        self.sha = write_corpus(self.source)

    def tearDown(self): self.temp.cleanup()

    def plan(self):
        return StreamingMTGJSONPlanner(self.root / "state", batch_size=4,
            targets=("Mystery Booster 2", "Marvel Super Heroes")).plan(self.source, self.sha)

    def test_targets_partition_before_dependency_closed_deterministic_batching(self):
        first = self.plan(); second = self.plan()
        self.assertEqual(first["batch_plan_digest"], second["batch_plan_digest"])
        self.assertEqual({b["target_set_code"] for b in first["batches"]}, {"MB2", "MSH"})
        for batch in first["batches"]:
            self.assertIn(batch["target_set_code"].casefold(), batch["batch_id"])
            verified = StreamingMTGJSONPlanner.verify_batch(batch)
            self.assertTrue(verified["valid"])
            closure = json.loads(Path(batch["dependency_closure_report"]).read_text())
            self.assertTrue(closure["valid"])

    def test_payload_id_lists_manifests_and_pending_packages_are_retained(self):
        report = self.plan()
        self.assertFalse(report["canonical_write"]); self.assertFalse(report["promotion_performed"])
        for batch in report["batches"]:
            for key in ("candidate_payload_references", "candidate_id_list", "batch_manifest",
                        "dependency_closure_report", "review_package"):
                self.assertTrue(batch[key])
            package = json.loads(Path(batch["review_package"]).read_text())
            self.assertEqual(package["review_status"], "pending")
            self.assertFalse(package["canonical_write"]); self.assertFalse(package["promotion_performed"])
            self.assertTrue(all(value is None for value in package["approval_fields"].values()))

    def test_missing_payload_or_review_package_fails_closed(self):
        report = self.plan(); batch = report["batches"][0]
        Path(batch["candidate_payload_references"][0]["path"]).unlink()
        with self.assertRaisesRegex(ValueError, "missing candidate payload"):
            StreamingMTGJSONPlanner.verify_batch(batch)
        report = StreamingMTGJSONPlanner(self.root / "fresh", batch_size=4,
            targets=("MB2",)).plan(self.source, self.sha)
        batch = report["batches"][0]; Path(batch["review_package"]).unlink()
        with self.assertRaisesRegex(ValueError, "review package"):
            StreamingMTGJSONPlanner.verify_batch(batch)

    def test_cross_target_contamination_fails_closed(self):
        report = self.plan()
        mb2 = next(b for b in report["batches"] if b["target_set_code"] == "MB2")
        msh = next(b for b in report["batches"] if b["target_set_code"] == "MSH")
        mb2["candidate_payload_references"] = msh["candidate_payload_references"]
        with self.assertRaisesRegex(ValueError, "cross-target"):
            StreamingMTGJSONPlanner.verify_batch(mb2)

    def test_quarantined_rejected_unresolved_and_unsupported_are_excluded(self):
        report = self.plan()
        for batch in report["batches"]:
            excluded = json.loads(Path(batch["review_package"]).read_text())["excluded_candidates"]
            self.assertEqual(excluded["rejected"], [])
            self.assertEqual(excluded["unresolved"], [])
            self.assertEqual(excluded["unsupported"], [])
            self.assertFalse(set(batch["candidate_ids"]) & set(excluded["quarantined"]))


if __name__ == "__main__": unittest.main()
