"""Unit and integration coverage for canonical Card and Printing data."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from repository import (
    CardRepositoryError,
    canonical_repository_bytes,
    load_card,
    load_card_repository,
    load_printing,
)


def _source() -> dict:
    return {
        "schema_version": "v1",
        "id": "official-source",
        "title": "Official source",
        "source_classification": "official",
        "provider": "Publisher",
        "source_location": "https://example.com/card",
        "access_date": "2026-07-29",
        "verification_status": "confirmed",
        "claims": ["Card and printing identity"],
        "record_version": "1",
    }


def _card(card_id: str = "magic.example") -> dict:
    return {
        "schema_version": "v1",
        "id": card_id,
        "game": "magic",
        "name": "Example",
        "provenance": [{
            "source_id": "official-source",
            "field_paths": ["id", "game", "name"],
            "claim": "Card identity",
        }],
    }


def _printing(card_id: str = "magic.example") -> dict:
    return {
        "schema_version": "v1",
        "id": "magic.tst.1.en",
        "card_id": card_id,
        "set_code": "TST",
        "collector_number": "1",
        "rarity": "common",
        "language": "en",
        "provenance": [{
            "source_id": "official-source",
            "field_paths": [
                "id", "card_id", "set_code", "collector_number", "rarity", "language"
            ],
            "claim": "Printing identity",
        }],
    }


def _write(root: Path, relative: str, document: dict) -> None:
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(document), encoding="utf-8")


class CanonicalCardRepositoryTests(unittest.TestCase):
    def test_canonical_dataset_is_structurally_and_referentially_valid(self) -> None:
        cards, printings = load_card_repository("magic")
        self.assertEqual(len(cards), 11)
        self.assertEqual(len(printings), 11)
        card_ids = {card["id"] for card in cards}
        self.assertEqual({printing["card_id"] for printing in printings}, card_ids)
        for card in cards:
            self.assertEqual(load_card("magic", card["id"]), card)
        for printing in printings:
            self.assertEqual(load_printing("magic", printing["id"]), printing)

    def test_canonical_output_is_reproducible(self) -> None:
        first = canonical_repository_bytes("magic")
        second = canonical_repository_bytes("magic")
        self.assertEqual(first, second)
        snapshot = json.loads(first)
        self.assertEqual(snapshot["cards"][0]["id"], "magic.ancestral-recall")
        self.assertEqual(snapshot["printings"][0]["id"], "magic.lea.161.en")

    def test_orphaned_printing_is_rejected_with_identifiers(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            _write(root, "magic/sources/official-source.json", _source())
            _write(root, "magic/cards/magic.example/card.json", _card())
            _write(root, "magic/printings/magic.tst.1.en/printing.json", _printing("magic.missing"))
            with self.assertRaisesRegex(
                CardRepositoryError,
                "magic.tst.1.en references missing Card magic.missing",
            ):
                load_card_repository("magic", games_root=root)

    def test_invalid_record_and_path_mismatch_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            _write(root, "magic/sources/official-source.json", _source())
            invalid = _card()
            del invalid["name"]
            _write(root, "magic/cards/magic.example/card.json", invalid)
            with self.assertRaisesRegex(CardRepositoryError, "Invalid canonical card"):
                load_card("magic", "magic.example", games_root=root)

            _write(root, "magic/cards/magic.example/card.json", _card("magic.duplicate"))
            with self.assertRaisesRegex(CardRepositoryError, "do not match"):
                load_card_repository("magic", games_root=root)

    def test_missing_source_and_field_provenance_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            _write(root, "magic/cards/magic.example/card.json", _card())
            with self.assertRaisesRegex(CardRepositoryError, "source-record record not found"):
                load_card("magic", "magic.example", games_root=root)

            _write(root, "magic/sources/official-source.json", _source())
            card = _card()
            card["provenance"][0]["field_paths"].remove("name")
            _write(root, "magic/cards/magic.example/card.json", card)
            with self.assertRaisesRegex(CardRepositoryError, "lacks field provenance for: name"):
                load_card("magic", "magic.example", games_root=root)


if __name__ == "__main__":
    unittest.main()
