"""Synthetic coverage for the canonical Print Sheet and Slot repository."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from repository import (
    RulesRepositoryError, canonical_rules_repository_bytes, load_print_sheet,
    load_rules_repository, load_slot,
)


def _source() -> dict:
    return {"schema_version": "v1", "id": "internal-fixture", "title": "Synthetic fixture",
            "source_classification": "internal", "provider": "MTG Lab",
            "source_location": "tests/test_rules_repository.py", "access_date": "2026-07-29",
            "verification_status": "confirmed", "claims": ["Synthetic repository behavior"],
            "record_version": "1"}


def _provenance(fields: list[str]) -> list[dict]:
    return [{"source_id": "internal-fixture", "field_paths": fields,
             "claim": "Synthetic repository fixture."}]


def _card() -> dict:
    return {"schema_version": "v1", "id": "magic.fixture", "game": "magic",
            "name": "Fixture", "provenance": _provenance(["id", "game", "name"])}


def _printing() -> dict:
    fields = ["id", "card_id", "set_code", "collector_number", "rarity"]
    return {"schema_version": "v1", "id": "magic.tst.1.en", "card_id": "magic.fixture",
            "set_code": "TST", "collector_number": "1", "rarity": "common",
            "provenance": _provenance(fields)}


def _sheet() -> dict:
    fields = ["id", "game", "name", "entries"]
    return {"schema_version": "v1", "id": "magic.fixture-sheet", "game": "magic",
            "name": "Fixture Sheet", "entries": [{"printing_id": "magic.tst.1.en", "weight": 1}],
            "provenance": _provenance(fields)}


def _slot() -> dict:
    fields = ["id", "game", "name", "print_sheet_id", "draw_count", "replacement"]
    return {"schema_version": "v1", "id": "magic.fixture-slot", "game": "magic",
            "name": "Fixture Slot", "print_sheet_id": "magic.fixture-sheet", "draw_count": 1,
            "replacement": True, "provenance": _provenance(fields)}


def _write(root: Path, relative: str, document: dict) -> None:
    path = root / relative; path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(document), encoding="utf-8")


def _complete_repository(root: Path) -> None:
    _write(root, "magic/sources/internal-fixture.json", _source())
    _write(root, "magic/cards/magic.fixture/card.json", _card())
    _write(root, "magic/printings/magic.tst.1.en/printing.json", _printing())
    _write(root, "magic/print_sheets/magic.fixture-sheet/print-sheet.json", _sheet())
    _write(root, "magic/slots/magic.fixture-slot/slot.json", _slot())


class RulesRepositoryTests(unittest.TestCase):
    def test_empty_canonical_rules_repository_is_valid_and_deterministic(self) -> None:
        sheets, slots = load_rules_repository("magic")
        self.assertEqual((sheets, slots), ((), ()))
        self.assertEqual(canonical_rules_repository_bytes("magic"),
                         canonical_rules_repository_bytes("magic"))

    def test_complete_synthetic_graph_loads_and_snapshots_deterministically(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); _complete_repository(root)
            sheets, slots = load_rules_repository("magic", games_root=root)
            self.assertEqual(load_print_sheet("magic", sheets[0]["id"], games_root=root), sheets[0])
            self.assertEqual(load_slot("magic", slots[0]["id"], games_root=root), slots[0])
            snapshot = json.loads(canonical_rules_repository_bytes("magic", games_root=root))
            self.assertEqual(snapshot["print_sheets"][0]["entries"][0]["weight"], 1)

    def test_missing_dependencies_and_duplicate_entries_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); _complete_repository(root)
            (root / "magic/printings/magic.tst.1.en/printing.json").unlink()
            with self.assertRaisesRegex(RulesRepositoryError, "missing Printing"):
                load_rules_repository("magic", games_root=root)
            _write(root, "magic/printings/magic.tst.1.en/printing.json", _printing())
            sheet = _sheet(); sheet["entries"].append(sheet["entries"][0].copy())
            _write(root, "magic/print_sheets/magic.fixture-sheet/print-sheet.json", sheet)
            with self.assertRaisesRegex(RulesRepositoryError, "duplicate Printing"):
                load_rules_repository("magic", games_root=root)

    def test_missing_sheet_product_slot_cross_game_and_provenance_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); _complete_repository(root)
            (root / "magic/print_sheets/magic.fixture-sheet/print-sheet.json").unlink()
            with self.assertRaisesRegex(RulesRepositoryError, "missing Print Sheet"):
                load_rules_repository("magic", games_root=root)
            _write(root, "magic/print_sheets/magic.fixture-sheet/print-sheet.json", _sheet())
            slot = _slot(); slot["game"] = "other"
            _write(root, "magic/slots/magic.fixture-slot/slot.json", slot)
            with self.assertRaisesRegex(RulesRepositoryError, "canonical path"):
                load_rules_repository("magic", games_root=root)
            slot = _slot(); slot["provenance"][0]["field_paths"].remove("replacement")
            _write(root, "magic/slots/magic.fixture-slot/slot.json", slot)
            with self.assertRaisesRegex(RulesRepositoryError, "lacks field provenance"):
                load_rules_repository("magic", games_root=root)
            _write(root, "magic/slots/magic.fixture-slot/slot.json", _slot())
            product = {"schema_version": "v1", "id": "fixture-product", "game": "magic",
                       "name": "Fixture", "product_type": "booster", "lifecycle_status": "validated",
                       "slot_ids": ["magic.missing-slot"], "provenance": [{"claim": "Synthetic",
                       "source_classification": "internal", "source_location": "test fixture",
                       "verification_status": "confirmed"}]}
            _write(root, "magic/products/fixture-product/product.json", product)
            with self.assertRaisesRegex(RulesRepositoryError, "missing Slot"):
                load_rules_repository("magic", games_root=root)


if __name__ == "__main__": unittest.main()
