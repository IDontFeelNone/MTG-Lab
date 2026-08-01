"""Phase 122 availability gate; production stops because retained evidence has no Hobbit set."""
import copy
import gzip
import hashlib
import json
from pathlib import Path
import unittest

from production_evidence.target_availability import (
    bounded_target_evidence, inspect_mtgjson_target, register_trusted_snapshot,
)

ROOT = Path(__file__).resolve().parents[1]


def dataset(*sets):
    return {"meta": {"version": "5.3.0", "date": "2026-07-31"},
            "data": {item.get("code", f"item-{index}"): item for index, item in enumerate(sets)}}


class Phase122HobbitAvailabilityTests(unittest.TestCase):
    def test_refreshed_snapshot_checksum_immutability_and_replay(self):
        import tempfile
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "AllPrintings.json.gz"
            raw = gzip.compress(json.dumps(dataset({"code": "AAA", "name": "Unrelated"})).encode(), mtime=0)
            source.write_bytes(raw)
            digest = hashlib.sha256(raw).hexdigest()
            manifest = register_trusted_snapshot(source, digest, root / "evidence")
            self.assertTrue(manifest["checksum_verified"])
            self.assertEqual(manifest, register_trusted_snapshot(source, digest, root / "evidence"))
            retained = root / "evidence" / manifest["evidence_identity"] / "AllPrintings.json.gz"
            self.assertEqual(retained.read_bytes(), raw)
            with self.assertRaisesRegex(ValueError, "checksum"):
                register_trusted_snapshot(source, "0" * 64, root / "evidence")
            retained.write_bytes(b"changed")
            with self.assertRaisesRegex(FileExistsError, "collision"):
                register_trusted_snapshot(source, digest, root / "evidence")

    def test_zero_matching_targets(self):
        report = inspect_mtgjson_target(dataset({"code": "LTR", "name": "Other Middle-earth Set", "cards": []}), "The Hobbit")
        self.assertEqual(report["status"], "not_yet_published_by_provider")
        self.assertEqual(report["matches"], [])

    def test_multiple_targets_are_ambiguous(self):
        report = inspect_mtgjson_target(dataset(
            {"code": "HOB", "name": "The Hobbit"},
            {"code": "HBC", "name": "The Hobbit Commander"}), "The Hobbit")
        self.assertEqual(report["status"], "ambiguous_with_another_product")
        self.assertEqual([row["code"] for row in report["matches"]], ["HBC", "HOB"])

    def test_unique_selection_real_shape_bounded_extraction_and_identity(self):
        source = dataset(
            {"code": "AAA", "name": "Unrelated", "cards": [{"uuid": "wrong"}]},
            {"code": "XYZ", "name": "The Hobbit", "releaseDate": "unknown",
             "cards": [{"uuid": "one", "name": "Printed", "text": None, "identifiers": {}}]})
        report = inspect_mtgjson_target(source, "The Hobbit")
        self.assertEqual(report["status"], "present_and_uniquely_identifiable")
        self.assertEqual(report["matches"][0]["code"], "XYZ")
        bounded = bounded_target_evidence(source, report, "a" * 64)
        replay = bounded_target_evidence(copy.deepcopy(source), report, "a" * 64)
        self.assertEqual(bounded, replay)
        self.assertNotIn("wrong", json.dumps(bounded))
        self.assertIsNone(bounded["target_payload"]["cards"][0]["text"])
        body = {key: value for key, value in bounded.items() if key not in ("projection_sha256", "evidence_identity")}
        actual = hashlib.sha256(json.dumps(body, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
        self.assertEqual(bounded["projection_sha256"], actual)
        self.assertFalse(bounded["canonical_write"]); self.assertFalse(bounded["promotion_performed"])

    def test_incomplete_and_unsupported_are_distinct(self):
        incomplete = {"meta": {"version": "5.3.0"}, "data": {"": {"name": "The Hobbit"}}}
        self.assertEqual(inspect_mtgjson_target(incomplete, "The Hobbit")["status"], "present_but_incomplete")
        self.assertEqual(inspect_mtgjson_target({"sets": []}, "The Hobbit")["status"], "unsupported_by_current_adapter")

    def test_card_text_alone_does_not_make_a_set_match(self):
        source = dataset({"code": "AAA", "name": "Unrelated", "cards": [{"flavorText": "The Hobbit"}]})
        self.assertEqual(inspect_mtgjson_target(source, "The Hobbit")["plausible_target_count"], 0)

    def test_retained_production_inventory_has_no_hobbit_mb2_or_msh_substitution(self):
        report = json.loads((ROOT / "data/automatic_updates/phase-122-hobbit-availability.json").read_text())
        self.assertEqual(report["status"], "not_yet_published_by_provider")
        self.assertEqual(report["plausible_target_count"], 0)
        self.assertFalse(report["canonical_write"]); self.assertFalse(report["promotion_performed"])
        self.assertEqual(report["inspected_set_codes"], ["MB2", "MSH"])
        self.assertNotIn("target_code", report)


if __name__ == "__main__": unittest.main()
