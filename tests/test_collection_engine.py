import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

from collection import (Acquisition, Collection, CollectionError, CollectionRepository,
                        CollectionService, InventoryLocation)


class CanonicalStub:
    def get_printing(self, identifier):
        if identifier not in {"alpha.one", "alpha.two"}:
            raise KeyError(identifier)
        return identifier


class CollectionEngineTests(unittest.TestCase):
    def setUp(self):
        identifiers = iter((f"id-{number}" for number in range(20)))
        self.service = CollectionService(CanonicalStub(), lambda: next(identifiers))
        self.acquisition = Acquisition("acq", "pack_opening", datetime(2026, 7, 30, tzinfo=timezone.utc), "product.one")
        self.binder = InventoryLocation("binder", "Binder", "binder")
        self.collection = Collection("mine")

    def test_ownership_and_canonical_validation(self):
        result = self.service.add(self.collection, "alpha.one", 2, self.acquisition, self.binder,
                                  observation_id="box-1", finish="foil")
        self.assertEqual(sum(card.quantity for card in self.service.owned(result, "alpha.one")), 2)
        self.assertEqual(result.cards[0].observation_id, "box-1")
        with self.assertRaisesRegex(CollectionError, "unknown canonical"):
            self.service.add(result, "missing", 1, self.acquisition, self.binder)

    def test_split_merge_remove_and_move_quantity_math(self):
        result = self.service.add(self.collection, "alpha.one", 5, self.acquisition, self.binder)
        result = self.service.split(result, "id-0", 2)
        self.assertEqual(sorted(card.quantity for card in result.cards), [2, 3])
        result = self.service.merge(result, tuple(card.id for card in result.cards))
        trade = InventoryLocation("trade", "Trade Binder", "trade_binder")
        result = self.service.move(result, "id-0", trade, 2)
        self.assertEqual(sorted(card.quantity for card in result.cards), [2, 3])
        moved = next(card for card in result.cards if card.location_id == "trade")
        result = self.service.remove(result, moved.id, 1)
        self.assertEqual(sum(card.quantity for card in result.cards), 4)

    def test_deterministic_summary_tracks_duplicates_acquisition_and_location(self):
        result = self.service.add(self.collection, "alpha.one", 3, self.acquisition, self.binder, finish="foil")
        gift = Acquisition("gift", "gift", datetime(2026, 7, 29, tzinfo=timezone.utc))
        result = self.service.add(result, "alpha.two", 1, gift, self.binder)
        expected = {"total_cards": 4, "unique_printings": 2, "duplicate_count": 2,
                    "finish_breakdown": {"foil": 3, "nonfoil": 1},
                    "acquisition_breakdown": {"gift": 1, "pack_opening": 3},
                    "inventory_locations": {"Binder": 4}}
        self.assertEqual(self.service.summary(result), expected)
        self.assertEqual(self.service.summary(result), expected)

    def test_repository_round_trip(self):
        result = self.service.add(self.collection, "alpha.one", 1, self.acquisition, self.binder)
        with tempfile.TemporaryDirectory() as directory:
            repository = CollectionRepository(Path(directory) / "collection.json")
            repository.save(result)
            self.assertEqual(repository.load(), result)


if __name__ == "__main__":
    unittest.main()
