"""Phase 106 production ingestion acceptance tests (unittest only)."""
import json
import tempfile
import unittest
from pathlib import Path

from promotion import ProductionMTGJSONIngestion


def dataset(path: Path, count: int = 24) -> Path:
    cards = []
    for index in range(count):
        cards.append({"uuid": f"00000000-0000-0000-0000-{index:012d}",
                      "name": f"Production Card {index}", "number": str(index + 1),
                      "identifiers": {"scryfallOracleId": f"oracle-{index}"},
                      "rarity": "common", "language": "English",
                      "finishes": ["nonfoil"], "layout": "normal", "colors": ["U"]})
    value = {"meta": {"date": "2026-07-31", "version": "5.2.1"},
             "data": {"TST": {"code": "TST", "name": "Production Test",
                                "releaseDate": "2026-07-31", "cards": cards}}}
    path.write_text(json.dumps(value))
    return path


class ProductionDatasetIngestionTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.source = dataset(self.root / "AllPrintings.json")

    def tearDown(self): self.temporary.cleanup()

    def test_production_import_batches_bounded_promotion_projection_and_consumers(self):
        workflow = ProductionMTGJSONIngestion(self.root / "state", batch_size=10)
        first = workflow.prepare(self.source)
        second = workflow.prepare(self.source)
        self.assertEqual(first["batches"], second["batches"])
        self.assertEqual(first["eligible_count"], 48)
        self.assertEqual(first["batch_count"], 5)
        self.assertEqual(first["duplicate_count"], 0)
        self.assertGreater(first["rejected_count"], 0)
        self.assertEqual(first["unresolved_count"], 0)
        self.assertTrue(all(batch["entity_count"] <= 10 for batch in first["batches"]))

        batch = next(item for item in first["batches"]
                     if item["entity_counts"]["card"] and item["entity_counts"]["printing"])
        promoted = workflow.promote(first["dataset_identifier"], batch["batch_id"],
                                    actor="independent-production-reviewer")
        replayed = workflow.promote(first["dataset_identifier"], batch["batch_id"],
                                    actor="independent-production-reviewer")
        self.assertEqual(promoted["promotion_id"], replayed["promotion_id"])
        self.assertLessEqual(promoted["promoted_count"], 10)
        self.assertEqual(promoted["projection_count"], promoted["promoted_count"])
        self.assertTrue(workflow.verify_downstream()["valid"])

        rollback = workflow.rollback(promoted["promotion_id"], actor="production-operator",
                                     timestamp="2026-07-31T01:00:00+00:00")
        self.assertEqual(len(rollback["promoted_entities"]), promoted["promoted_count"])
        self.assertFalse(any(workflow.engine.replay().values()))

    def test_unknown_required_values_are_unresolved_and_not_promoted(self):
        value = json.loads(self.source.read_text())
        del value["data"]["TST"]["cards"][0]["layout"]
        self.source.write_text(json.dumps(value))
        report = ProductionMTGJSONIngestion(self.root / "state", batch_size=10).prepare(self.source)
        self.assertGreater(report["unresolved_count"], 0)
        self.assertEqual(sum(x["entity_count"] for x in report["batches"]), report["eligible_count"])


if __name__ == "__main__": unittest.main()
