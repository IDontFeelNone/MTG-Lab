import json
import tempfile
import unittest
from pathlib import Path

from canonical_import import ImportError, JSONSource, import_dataset
from repository.canonical import CanonicalRepository

class CanonicalImportTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.root = Path(self.temp.name) / "games"; self.root.mkdir()
        self.source = Path(self.temp.name) / "reviewed.json"
        self.data = {"schema_version":"v1", "game":"future_game", "source":"reviewed-test",
                     "source_version":"2026.1", "review_status":"reviewed", "import_timestamp":"2026-07-30T00:00:00+00:00",
                     "rarities":[{"id":"common", "name":"Common"}],
                     "finishes":[{"id":"standard", "name":"Standard"}]}
    def tearDown(self): self.temp.cleanup()
    def write(self): self.source.write_text(json.dumps(self.data))
    def test_success_duplicate_determinism_and_provenance(self):
        self.write(); first = import_dataset(JSONSource(self.source), "future_game", games_root=self.root)
        before = (self.root/"future_game"/"rarities"/"common.json").read_bytes()
        second = import_dataset(JSONSource(self.source), "future_game", games_root=self.root)
        self.assertTrue(first.applied); self.assertEqual(second.unchanged, 2); self.assertEqual(before, (self.root/"future_game"/"rarities"/"common.json").read_bytes())
        value = json.loads(before); self.assertEqual(value["metadata"]["import_provenance"]["source_version"], "2026.1")
        self.assertEqual(CanonicalRepository("future_game", games_root=self.root).rarities[0].id, "common")
    def test_dry_run_and_validation_only_do_not_write(self):
        self.write(); self.assertFalse(import_dataset(JSONSource(self.source), "future_game", games_root=self.root, dry_run=True).applied)
        self.assertFalse((self.root/"future_game").exists())
        self.assertTrue(import_dataset(JSONSource(self.source), "future_game", games_root=self.root, validation_only=True).validation_only)
        self.assertFalse((self.root/"future_game").exists())
    def test_invalid_duplicate_and_missing_relationship_roll_back(self):
        self.data["rarities"].append({"id":"common", "name":"Again"}); self.write()
        with self.assertRaisesRegex(ImportError, "Duplicate"): import_dataset(JSONSource(self.source), "future_game", games_root=self.root)
        self.assertFalse((self.root/"future_game").exists())
        self.data["rarities"] = []; self.data["slots"] = [{"id":"slot", "name":"Slot", "sheet_id":"absent", "count":1}]; self.write()
        with self.assertRaisesRegex(ImportError, "missing Sheet"): import_dataset(JSONSource(self.source), "future_game", games_root=self.root)
        self.assertFalse((self.root/"future_game").exists())

if __name__ == "__main__": unittest.main()
