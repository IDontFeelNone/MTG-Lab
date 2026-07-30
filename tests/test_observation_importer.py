import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from observations.importer import ObservationImporter, main, parse_pack_text
from observations.verification import ObservationError


CARDS = ({"id": "magic.sol-ring", "name": "Sol Ring"},
         {"id": "magic.lightning-bolt", "name": "Lightning Bolt"})
PRINTINGS = ({"id": "magic.tst.1.en", "card_id": "magic.sol-ring",
              "metadata": {"product_membership": ["test_product"]}},)


class ObservationImporterTests(unittest.TestCase):
    def test_parser_supports_multiple_packs_and_treatments(self):
        packs = parse_pack_text("Sol Ring [foil]\r\nLightning Bolt\r\n---\r\nUnknown\r\n")
        self.assertEqual(len(packs), 2)
        self.assertEqual(packs[0][0], {"position": 1, "reported_name": "Sol Ring",
                                      "reported_treatment": "foil"})
        self.assertEqual(packs[1][0]["reported_name"], "Unknown")
        with self.assertRaisesRegex(ObservationError, "contains no cards"):
            parse_pack_text("Sol Ring\n---\n")

    @patch("observations.importer.load_card_repository", return_value=(CARDS, PRINTINGS))
    def test_import_preserves_source_verifies_and_regenerates_outputs(self, _load):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "packs.txt"
            original = "Sol Ring [foil]\r\nUnknown Card\r\n---\r\nLightning Bolt\r\n"
            source.write_bytes(original.encode())
            importer = ObservationImporter(observations_root=root / "observations",
                                           derived_root=root / "derived")
            paths = importer.import_file(source, game="magic", product="test_product",
                                         box_id="box_001", recorded_on="2026-07-30")
            pack_root = root / "observations/magic/test_product/boxes/box_001"
            first = json.loads((pack_root / "pack_001.json").read_text())
            self.assertEqual(first["import_source"]["text"], original)
            self.assertEqual(first["cards"][0]["reported_name"], "Sol Ring")
            verification = json.loads((root / "derived/magic/test_product/boxes/box_001/"
                                       "verifications/test_product-box_001-pack_001.verification.json").read_text())
            self.assertEqual(verification["cards"][0]["canonical_card_id"], "magic.sol-ring")
            self.assertEqual(verification["cards"][0]["canonical_printing_id"], "magic.tst.1.en")
            self.assertEqual(verification["cards"][1]["verification_status"], "unmatched")
            manifest = json.loads((pack_root / "manifest.json").read_text())
            self.assertEqual([item["pack_id"] for item in manifest["packs"]],
                             ["pack_001", "pack_002"])
            analytics = json.loads((root / "derived/magic/test_product/boxes/box_001/analytics.json").read_text())
            self.assertEqual(analytics["pack_count"], 2)
            self.assertEqual(analytics["verification_statuses"], {"unmatched": 1, "verified": 2})
            self.assertIn(pack_root / "manifest.json", paths)

    @patch("observations.importer.load_card_repository", return_value=(CARDS, PRINTINGS))
    def test_append_never_rewrites_existing_pack(self, _load):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "pack.txt"
            source.write_text("Sol Ring\n", encoding="utf-8")
            importer = ObservationImporter(observations_root=root / "observations",
                                           derived_root=root / "derived")
            kwargs = {"game": "magic", "product": "test_product", "box_id": "box_001"}
            importer.import_file(source, **kwargs)
            first_path = root / "observations/magic/test_product/boxes/box_001/pack_001.json"
            original = first_path.read_bytes()
            source.write_text("Lightning Bolt\n", encoding="utf-8")
            importer.import_file(source, **kwargs)
            self.assertEqual(first_path.read_bytes(), original)
            self.assertTrue(first_path.with_name("pack_002.json").exists())
            # An undeclared pack is treated as corruption rather than overwritten or adopted.
            first_path.with_name("pack_999.json").write_text("{}", encoding="utf-8")
            with self.assertRaisesRegex(ObservationError, "disagree"):
                importer.import_file(source, **kwargs)

    def test_cli_reports_invalid_input_without_writing(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "empty.txt"
            source.write_text("", encoding="utf-8")
            with self.assertRaises(SystemExit):
                main([str(source), "--game", "magic", "--product", "p", "--box", "b",
                      "--observations-root", str(root / "observations")])
            self.assertFalse((root / "observations").exists())


if __name__ == "__main__":
    unittest.main()
