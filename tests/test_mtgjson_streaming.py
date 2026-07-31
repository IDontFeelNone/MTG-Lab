"""Phase 108C memory-bounded streaming acceptance tests (unittest only)."""
import gzip
import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from providers.mtgjson.streaming import StreamingMTGJSONPlanner


def corpus(path: Path) -> str:
    value = {"meta": {"date": "2026-07-31", "version": "5.2.1"}, "data": {}}
    for code, name, offset in (("MB2", "Mystery Booster 2", 0),
                               ("MSH", "Marvel Super Heroes", 10), ("OTH", "Other", 20)):
        value["data"][code] = {"code": code, "name": name, "cards": [{
            "uuid": f"00000000-0000-0000-0000-{offset + i:012d}", "name": f"Card {offset+i}",
            "number": str(i), "rarity": "common", "language": "English",
            "finishes": ["nonfoil"], "layout": "normal", "colors": [],
            "identifiers": {"deckboxId": "shared"} if i == 0 else {}}
            for i in range(3)]}
    path.write_text(json.dumps(value))
    return hashlib.sha256(path.read_bytes()).hexdigest()


class StreamingTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.root = Path(self.temp.name)
        self.source = self.root / "AllPrintings.json"; self.digest = corpus(self.source)

    def tearDown(self): self.temp.cleanup()

    def test_one_set_at_a_time_and_target_excludes_unrelated_candidates(self):
        report = StreamingMTGJSONPlanner(self.root / "state", targets=("Mystery Booster 2",)).plan(
            self.source, self.digest)
        self.assertEqual(report["sets_processed"], 1)
        self.assertEqual(report["selected_set_codes"], ["MB2"])
        self.assertEqual(report["performance"]["maximum_retained_set_records"], 1)
        shard = json.loads(Path(report["candidate_shards"][0]["path"]).read_text())
        self.assertTrue(all(c["mapped_fields"].get("set_code", "mb2") == "mb2"
                            for c in shard["candidates"] if c["entity_type"] == "printing"))

    def test_resume_is_deterministic_and_corruption_is_rejected(self):
        planner = StreamingMTGJSONPlanner(self.root / "state", batch_size=4)
        first = planner.plan(self.source, self.digest)
        second = planner.plan(self.source, self.digest)
        self.assertEqual(first["batch_plan_digest"], second["batch_plan_digest"])
        Path(first["candidate_shards"][0]["path"]).write_text("corrupt")
        with self.assertRaisesRegex(ValueError, "corrupted retained candidate shard"):
            planner.plan(self.source, self.digest)

    def test_compressed_and_uncompressed_are_semantically_equivalent(self):
        compressed = self.root / "AllPrintings.json.gz"
        with gzip.open(compressed, "wb") as target: target.write(self.source.read_bytes())
        gz_hash = hashlib.sha256(compressed.read_bytes()).hexdigest()
        plain = StreamingMTGJSONPlanner(self.root / "plain", batch_size=5).plan(self.source, self.digest)
        zipped = StreamingMTGJSONPlanner(self.root / "gzip", batch_size=5).plan(compressed, gz_hash)
        self.assertEqual(plain["entity_counts"], zipped["entity_counts"])
        self.assertEqual([b["candidate_ids"] for b in plain["batches"]],
                         [b["candidate_ids"] for b in zipped["batches"]])
        self.assertTrue(zipped["compressed"])

    def test_collision_crosses_set_shards_and_summary_has_no_payloads(self):
        report = StreamingMTGJSONPlanner(self.root / "state").plan(self.source, self.digest)
        self.assertEqual(report["identifier_finding_counts"]["by_namespace"], {"deckboxId": 1})
        self.assertNotIn("candidates", report)
        self.assertTrue(report["finding_shards"])
        self.assertFalse(report["canonical_write"])
        self.assertFalse(report["promotion_performed"])


if __name__ == "__main__": unittest.main()
