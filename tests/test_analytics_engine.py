import json
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
from types import MappingProxyType

from analytics import AnalyticsService
from collection import (Acquisition, Collection, DeckAssignment, InventoryLocation, OwnedCard)
from mtglab.analytics.__main__ import main


NOW = datetime(2026, 7, 30, 12, tzinfo=timezone.utc)


def fixture_collection():
    acquisitions = (
        Acquisition("pack", "pack_opening", datetime(2026, 7, 1, tzinfo=timezone.utc), "product-a"),
        Acquisition("gift", "gift", datetime(2026, 7, 2, tzinfo=timezone.utc)),
    )
    cards = (
        OwnedCard("owned-1", "printing-a", "pack", "binder", 3, finish="foil"),
        OwnedCard("owned-2", "printing-b", "gift", "box", 1),
    )
    locations = (InventoryLocation("binder", "Binder"), InventoryLocation("box", "Box"))
    return Collection("test", cards, acquisitions, locations, (DeckAssignment("deck", "owned-1", 2),))


class AnalyticsEngineTests(unittest.TestCase):
    def setUp(self):
        self.analytics = AnalyticsService(lambda: NOW)
        self.collection = fixture_collection()

    def test_collection_and_duplicate_reports_are_immutable_and_versioned(self):
        summary = self.analytics.collection_summary(self.collection)
        self.assertEqual(summary.schema_version, "analytics-report-v1")
        self.assertEqual(summary.data["total_cards"], 4)
        self.assertEqual(summary.data["finish_distribution"], {"foil": 3, "nonfoil": 1})
        self.assertIsInstance(summary.data, MappingProxyType)
        with self.assertRaises(TypeError):
            summary.data["total_cards"] = 0
        duplicates = self.analytics.duplicate_report(self.collection).to_dict()
        self.assertEqual(duplicates["data"]["items"], [
            {"printing_id": "printing-a", "quantity": 3, "extra_copies": 2}
        ])

    def test_acquisition_growth_and_inventory_utilization(self):
        acquisition = self.analytics.acquisition_report(self.collection).data
        self.assertEqual(acquisition["cards_by_type"], {"gift": 1, "pack_opening": 3})
        self.assertEqual(acquisition["collection_growth"][-1]["cumulative"], 4)
        inventory = self.analytics.inventory_report(self.collection).data
        self.assertEqual(inventory["assigned_cards"], 2)
        self.assertEqual(inventory["unassigned_cards"], 2)
        self.assertEqual(inventory["utilization_ratio"], 0.5)

    def test_observation_statistics_are_game_agnostic_and_deterministic(self):
        observations = [{"observation_id": "open-1", "product_id": "set-x", "cards": [
            {"printing_id": "card-z", "finish": "glossy"},
            {"printing_id": "card-z", "finish": "glossy"},
        ]}]
        first = self.analytics.observation_report(observations).to_dict()
        second = self.analytics.observation_report(observations).to_dict()
        self.assertEqual(first, second)
        self.assertEqual(first["data"]["product_openings"], {"set-x": 1})
        self.assertEqual(first["data"]["card_frequency"], [{"id": "card-z", "count": 2}])

    def test_cli_emits_json_for_an_empty_collection(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "missing.json"
            from contextlib import redirect_stdout
            from io import StringIO
            output = StringIO()
            with redirect_stdout(output):
                self.assertEqual(main(["--collection-file", str(path), "collection"]), 0)
            payload = json.loads(output.getvalue())
            self.assertEqual(payload["report_type"], "collection_summary")
            self.assertEqual(payload["data"]["total_cards"], 0)


if __name__ == "__main__":
    unittest.main()
