"""Tests for the versioned schema registry and validation boundary."""

from __future__ import annotations

import unittest

from validation import SchemaValidationError, validate_document


class SchemaValidationTests(unittest.TestCase):
    def test_valid_card_is_accepted(self) -> None:
        validate_document(
            {
                "schema_version": "v1",
                "id": "magic.lightning-bolt",
                "game": "magic",
                "name": "Lightning Bolt",
            },
            "card",
        )

    def test_invalid_slot_is_rejected(self) -> None:
        with self.assertRaises(SchemaValidationError):
            validate_document(
                {
                    "schema_version": "v1",
                    "id": "rare",
                    "name": "Rare",
                    "print_sheet_id": "rare-sheet",
                    "draw_count": 0,
                    "replacement": True,
                },
                "slot",
            )

    def test_unknown_schema_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            validate_document({}, "unknown")


if __name__ == "__main__":
    unittest.main()
