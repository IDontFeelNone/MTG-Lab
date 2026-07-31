import contextlib
import hashlib
import io
import json
import tempfile
import unittest
from pathlib import Path

from mtglab.__main__ import main
from providers.mtgjson import MTGJSONImportExecution, MTGJSONValidationError


FIXTURE = Path(__file__).parent / "fixtures" / "mtgjson" / "AllPrintings.json"


class MTGJSONImportExecutionTests(unittest.TestCase):
    def test_successful_import_generates_validated_pending_candidates(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            result = MTGJSONImportExecution(root).import_dataset(FIXTURE)
            self.assertEqual(result["candidate_count"], 46)
            self.assertEqual(result["entity_counts"], {"card": 10, "finish": 0,
                "identifier": 20, "language": 1, "printing": 10, "rarity": 4, "set": 1})
            self.assertEqual(result["status"], "awaiting_human_review")
            self.assertFalse(result["canonical_write"])
            queued = MTGJSONImportExecution(root).review()["imports"][0]["candidates"]
            self.assertEqual(len(queued), 46)
            self.assertTrue(all(item["review_status"] == "pending" for item in queued))
            self.assertTrue(all(item["validation_state"] == "validated" for item in queued))
            self.assertFalse((root / "canonical").exists())

    def test_missing_and_malformed_datasets_leave_no_state(self):
        for payload in (None, b'{"bad":true}'):
            with self.subTest(payload=payload), tempfile.TemporaryDirectory() as directory:
                root = Path(directory); execution = MTGJSONImportExecution(root)
                if payload is None:
                    with self.assertRaisesRegex(ValueError, "AllPrintings JSON artifact is required"):
                        execution.import_dataset(None)
                else:
                    source = root / "bad.json"; source.write_bytes(payload)
                    with self.assertRaises(MTGJSONValidationError):
                        execution.import_dataset(source)
                self.assertFalse((root / "evidence").exists())

    def test_duplicate_identifiers_are_rejected_before_registration(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); value = json.loads(FIXTURE.read_text())
            value["data"]["TST"]["cards"].append(dict(value["data"]["TST"]["cards"][0]))
            source = root / "duplicate.json"; source.write_text(json.dumps(value))
            with self.assertRaisesRegex(MTGJSONValidationError, "duplicate printing identifier"):
                MTGJSONImportExecution(root).import_dataset(source)
            self.assertFalse((root / "evidence").exists())

    def test_repeatable_import_and_candidate_hashes(self):
        with tempfile.TemporaryDirectory() as directory:
            execution = MTGJSONImportExecution(directory)
            first = execution.import_dataset(FIXTURE); second = execution.import_dataset(FIXTURE)
            self.assertEqual(first, second)
            candidates = execution.candidates(first["dataset_identifier"])["imports"][0]["candidates"]
            for candidate in candidates:
                supplied = candidate.pop("candidate_hash")
                encoded = json.dumps(candidate, ensure_ascii=False, separators=(",", ":"),
                                     sort_keys=True).encode()
                self.assertEqual(supplied, hashlib.sha256(encoded).hexdigest())

    def test_cli_import_candidates_review_and_missing_source(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for command in (("import", str(FIXTURE)), ("candidates",), ("review",)):
                output = io.StringIO()
                with contextlib.redirect_stdout(output):
                    self.assertEqual(main(["--data-root", str(root), "provider", "mtgjson",
                                           *command, "--format", "json"]), 0)
                self.assertFalse(json.loads(output.getvalue())["canonical_write"])
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                self.assertEqual(main(["--data-root", str(root / "missing"), "provider",
                                       "mtgjson", "import", "--format", "json"]), 2)
            self.assertIn("AllPrintings JSON artifact is required", output.getvalue())


if __name__ == "__main__":
    unittest.main()
