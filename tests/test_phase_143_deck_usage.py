import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from card_intelligence.deck_usage import (DeckUsageEvidenceError, PILOT_NAMES, canonical_bytes,
                                          load_deck_usage, project_decks)

ROOT = Path(__file__).resolve().parents[1]
IDS = {name: f"card-{index}" for index, name in enumerate(PILOT_NAMES)}


class Phase143DeckUsageTests(unittest.TestCase):
    def document(self):
        decks = [
            {"code": "commander-one", "name": "Commander One", "type": "Commander",
             "commander": [{"name": "Command Tower"}],
             "mainBoard": [{"name": "Sol Ring"}, {"name": "Command Tower"}], "sideBoard": []},
            {"code": "legacy-one", "name": "Belcher", "type": "Legacy", "commander": [],
             "mainBoard": [{"name": "Goblin Charbelcher"}, {"name": "Brainstorm"}], "sideBoard": []},
        ]
        return project_decks(decks, IDS, dataset_timestamp="2026-08-09T00:00:00Z",
                             retrieved_at="2026-08-09T01:00:00Z", source_sha256="a" * 64,
                             source_byte_count=100)

    def test_exact_scope_counts_formats_archetypes_and_deterministic_bytes(self):
        first = self.document(); second = self.document()
        self.assertEqual(canonical_bytes(first), canonical_bytes(second))
        self.assertEqual([x["card_name"] for x in first["records"]], list(PILOT_NAMES))
        command = next(x for x in first["records"] if x["card_name"] == "Command Tower")
        self.assertEqual((command["numerator"], command["denominator"]), (1, 2))
        self.assertEqual(command["formats"], [{"format": "commander", "deck_count": 1}])
        self.assertEqual(command["deck_associations"][0]["boards"], ["commander", "mainBoard"])

    def test_strict_loader_and_malformed_values(self):
        original = self.document()
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "evidence.json"; path.write_bytes(canonical_bytes(original))
            self.assertEqual(load_deck_usage(path)["provider"], "mtgjson")
            for mutate in (lambda x: x["records"][0].update(numerator=-1),
                           lambda x: x["records"][0].update(denominator=None),
                           lambda x: x["records"][0].update(dataset_timestamp=None),
                           lambda x: x["records"][0].update(extra="unsupported")):
                value = json.loads(json.dumps(original)); mutate(value)
                value["records_sha256"] = hashlib.sha256(canonical_bytes(value["records"])).hexdigest()
                path.write_bytes(canonical_bytes(value))
                with self.assertRaises(DeckUsageEvidenceError): load_deck_usage(path)

    def test_duplicates_conflicting_identity_and_non_pilot_fail(self):
        with self.assertRaises(DeckUsageEvidenceError): project_decks(
            [{"code": "x", "name": "X", "mainBoard": [], "sideBoard": [], "commander": []}] * 2,
            IDS, dataset_timestamp="2026-08-09T00:00:00Z", retrieved_at="2026-08-09T00:00:00Z",
            source_sha256="a" * 64, source_byte_count=1)
        with self.assertRaises(DeckUsageEvidenceError): project_decks([], {"Sol Ring": "x"},
            dataset_timestamp="2026-08-09T00:00:00Z", retrieved_at="2026-08-09T00:00:00Z",
            source_sha256="a" * 64, source_byte_count=1)

    def test_no_inference_or_valuation_language(self):
        text = canonical_bytes(self.document()).decode().lower()
        for forbidden in ("demand_score", "buy this", "undervalued", "price_prediction", "scarcity_score"):
            self.assertNotIn(forbidden, text)


if __name__ == "__main__": unittest.main()
