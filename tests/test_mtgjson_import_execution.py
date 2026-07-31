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

    def test_non_unique_external_references_are_preserved_for_review(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); value = json.loads(FIXTURE.read_text())
            first = value["data"]["TST"]["cards"][0]
            first["identifiers"]["deckboxId"] = "2676"
            duplicate = dict(first); duplicate.update({
                "uuid": "00000000-0000-4000-8000-000000000099", "number": "99",
                "identifiers": {"deckboxId": "2676"}})
            value["data"]["TST"]["cards"].append(duplicate)
            source = root / "deckbox.json"; source.write_text(json.dumps(value))
            result = MTGJSONImportExecution(root).import_dataset(source)
            finding = result["validation"]["identifier_findings"][0]
            self.assertEqual(finding["severity"], "review-required")
            queued = MTGJSONImportExecution(root).review(result["dataset_identifier"])["imports"][0]
            self.assertEqual(queued["identifier_findings"],
                             list(result["validation"]["identifier_findings"]))
            references = [item for item in queued["candidates"] if item["entity_type"] == "identifier"
                          and item["mapped_fields"]["namespace"] == "deckboxId"]
            self.assertEqual(len(references), 2)
            self.assertEqual({item["mapped_fields"]["printing_uuid"] for item in references},
                             {first["uuid"], duplicate["uuid"]})
            self.assertFalse(result["canonical_write"])

    def test_duplicate_deterministic_candidate_identifier_remains_fatal(self):
        candidate = {"candidate_identifier": "same", "candidate_hash": "ignored"}
        with self.assertRaisesRegex(ValueError, "duplicate deterministic identifier"):
            MTGJSONImportExecution._validate_candidates((candidate, dict(candidate)))

    def test_ambiguous_scryfall_collision_quarantines_only_dependency_closure(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); value = json.loads(FIXTURE.read_text())
            first = value["data"]["TST"]["cards"][0]
            first.update({"number": "7", "language": "English", "layout": "transform",
                          "side": "a", "faceName": "Front"})
            collision = "0001e77a-7fff-49d2-a55c-42f6fdf6db08"
            first["identifiers"]["scryfallId"] = collision
            second = json.loads(json.dumps(first)); second.update({
                "uuid": "00000000-0000-4000-8000-000000000099", "side": "b",
                "faceName": "Back"})
            value["data"]["TST"]["cards"].append(second)
            source = root / "collision.json"; source.write_text(json.dumps(value))
            result = MTGJSONImportExecution(root).import_dataset(source)
            self.assertEqual(result["quarantined_source_record_count"], 2)
            self.assertGreater(result["candidate_count"], 0)
            queued = MTGJSONImportExecution(root).review(
                result["dataset_identifier"])["imports"][0]["candidates"]
            self.assertFalse(any(item["entity_type"] == "printing" and
                item["mapped_fields"]["uuid"] in result["quarantined_mtgjson_uuids"]
                for item in queued))
            quarantine = json.loads((root / "evidence/mtgjson/imports" /
                result["dataset_identifier"] / "identifier_quarantine.json").read_text())
            self.assertEqual(len(quarantine["mtgjson_uuids"]), 2)
            self.assertTrue(all(item["validation_state"] == "quarantined"
                                for item in quarantine["candidates"]))
            self.assertTrue(all(item["review_status"] == "review-required"
                                for item in quarantine["candidates"]))
            self.assertFalse(result["canonical_write"])

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
