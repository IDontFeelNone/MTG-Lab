"""Tests for generic canonical product loading."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from repository import ProductLoadError, load_product


class ProductRepositoryTests(unittest.TestCase):
    def test_loads_mystery_booster_2_foundation_record(self) -> None:
        product = load_product("magic", "mystery_booster_2")

        self.assertEqual(product["id"], "mystery_booster_2")
        self.assertEqual(product["game"], "magic")
        self.assertEqual(product["metadata"]["status"], "foundation")
        self.assertEqual(product["slot_ids"], [])

    def test_preserves_provenance_classifications(self) -> None:
        product = load_product("magic", "mystery_booster_2")
        provenance = product["metadata"]["provenance"]

        self.assertEqual(len(provenance["confirmed_official_facts"]), 1)
        self.assertEqual(provenance["community_supported_research"], [])
        self.assertEqual(
            provenance["unverified_or_future_inference"][0]["status"], "not recorded"
        )

    def test_missing_product_raises_domain_error(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            with self.assertRaises(ProductLoadError):
                load_product(
                    "magic", "missing_product", games_root=Path(temporary_directory)
                )

    def test_invalid_product_record_raises_domain_error(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            games_root = Path(temporary_directory)
            record_path = (
                games_root
                / "magic"
                / "products"
                / "invalid_product"
                / "product.json"
            )
            record_path.parent.mkdir(parents=True)
            record_path.write_text(
                json.dumps({"schema_version": "v1", "id": "invalid_product"}),
                encoding="utf-8",
            )

            with self.assertRaises(ProductLoadError):
                load_product("magic", "invalid_product", games_root=games_root)


if __name__ == "__main__":
    unittest.main()
