import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path

from external_ingestion import ExternalDatasetError, MTGJSONAdapter, detect_mtgjson, generate_manifest
from mtglab.__main__ import main

FIXTURE = Path(__file__).parent / "fixtures/mtgjson/AllPrintings.json"
TS = "2026-07-30T18:00:00+00:00"


class MTGJSONAdapterTests(unittest.TestCase):
    def test_detection_metadata_manifest_and_supported_mapping(self):
        detected = detect_mtgjson(FIXTURE)
        self.assertEqual((detected["adapter"], detected["mtgjson_version"]), ("mtgjson-v1", "5.2.1"))
        self.assertEqual(detected["record_count"], 21)  # one Set, ten Cards and ten Printings
        manifest = generate_manifest(FIXTURE)
        self.assertEqual(manifest.expected_entity_types, ("card", "printing", "set"))
        records = list(MTGJSONAdapter().records(FIXTURE.read_bytes()))
        card = next(row for row in records if row["id"].startswith("card-"))
        printing = next(row for row in records if row["id"].startswith("printing-"))
        self.assertEqual(card["normalized"]["mana_cost"], "{1}{U}")
        self.assertEqual(printing["normalized"]["set_id"], "set-tst")
        self.assertIn("text", card["unsupported_fields"])

    def test_deterministic_normalization_and_unknown_value(self):
        adapter = MTGJSONAdapter(); payload = FIXTURE.read_bytes()
        first = list(adapter.records(payload)); second = list(adapter.records(payload))
        self.assertEqual(first, second)
        land = next(x for x in first if x.get("normalized", {}).get("name") == "Nameless Land")
        self.assertEqual(land["normalized"]["mana_cost"], {"status": "unknown"})

    def test_malformed_json_unsupported_version_and_unsupported_record(self):
        adapter = MTGJSONAdapter()
        with self.assertRaisesRegex(ExternalDatasetError, "invalid MTGJSON JSON"):
            list(adapter.records(b"{"))
        value = json.loads(FIXTURE.read_text()); value["meta"]["version"] = "6.0.0"
        with self.assertRaisesRegex(ExternalDatasetError, "unsupported MTGJSON version"):
            list(adapter.records(json.dumps(value).encode()))
        value = json.loads(FIXTURE.read_text()); value["data"]["TST"]["cards"][0] = "bad"
        with self.assertRaisesRegex(ExternalDatasetError, "malformed MTGJSON card"):
            list(adapter.records(json.dumps(value).encode()))

    def test_duplicate_and_identifier_conflicts(self):
        adapter = MTGJSONAdapter(); value = json.loads(FIXTURE.read_text())
        value["data"]["TST"]["cards"].append(dict(value["data"]["TST"]["cards"][0]))
        with self.assertRaisesRegex(ExternalDatasetError, "duplicate MTGJSON printing"):
            list(adapter.records(json.dumps(value).encode()))
        value = json.loads(FIXTURE.read_text()); ids = value["data"]["TST"]["cards"][0]["identifiers"]
        ids["multiverseId"] = ids["scryfallId"]
        with self.assertRaisesRegex(ExternalDatasetError, "identifier conflict"):
            list(adapter.records(json.dumps(value).encode()))

    def test_cli_and_repeated_acquisition_import(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            outputs = []
            for args in (["adapter", "detect", str(FIXTURE)],
                         ["adapter", "inspect", str(FIXTURE)],
                         ["adapter", "normalize", str(FIXTURE), "--timestamp", TS],
                         ["adapter", "normalize", str(FIXTURE), "--timestamp", "2026-07-30T19:00:00+00:00"]):
                stream = io.StringIO()
                with contextlib.redirect_stdout(stream):
                    self.assertEqual(main(["--data-root", str(root), *args]), 0)
                outputs.append(json.loads(stream.getvalue()))
            self.assertEqual(outputs[2], outputs[3])
            self.assertEqual(outputs[2]["status"], "awaiting_human_review")
            self.assertFalse((root / "canonical").exists())


if __name__ == "__main__": unittest.main()
