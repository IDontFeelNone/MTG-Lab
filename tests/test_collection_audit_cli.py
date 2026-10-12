"""CLI admission and delivery regressions using temporary fictional inventory."""
from __future__ import annotations

import contextlib
import copy
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from collection.intelligence import (CanonicalCollectionResolver, build_snapshot,
                                    canonical_json, digest, read_import)
from mtglab.__main__ import main


ROOT = Path(__file__).parents[1]
PRINTING = "5c8d3bc4-32fc-5b26-84bf-9921e5884d43"
OTHER_CARD = "dc0593c2-ccb4-4648-a592-c5bcd121dc72"
TIME = "2026-10-12T21:00:00Z"


class CollectionAuditCliTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.resolver = CanonicalCollectionResolver("magic", ROOT / "data")

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.data = self.root / "data"
        self.history = self.data / "collections/assessments"

    def tearDown(self):
        self.temp.cleanup()

    def inventory(self, *, collection_id="fictional-cli-audit"):
        value = {"schema_version": "collection-import-v1", "collection_id": collection_id,
            "source": {"type": "synthetic_fixture", "mode": "synthetic_demonstration",
                "real_user_inventory": False, "name": "Fictional CLI test inventory"},
            "entries": [{"printing_id": PRINTING, "quantity": 1, "finish": "nonfoil",
                "language": "English", "condition": None, "storage_location": "fictional-box",
                "provenance": {"owned_lot_id": "fictional-copy",
                    "organization": {"schema_version": "collection-organization-v1",
                                     "storage_classification": "bulk"}}}]}
        path = self.root / "inventory.json"
        path.write_bytes(canonical_json(value))
        imported = read_import(path)
        snapshot = build_snapshot(imported, self.resolver.resolve(imported))
        self.save_snapshot(snapshot)
        return snapshot

    def save_snapshot(self, snapshot):
        directory = self.data / "collections/snapshots"
        directory.mkdir(parents=True, exist_ok=True)
        (directory / (snapshot["snapshot_id"] + ".json")).write_bytes(canonical_json(snapshot))

    def review_source(self, snapshot, *, human=False):
        claim = {"collection_id": snapshot["collection_id"],
            "card_id": snapshot["resolved_holdings"][0]["card_id"],
            "purpose": "personal_collection_organization", "status": "reviewed",
            "outcome": "Fictional personal review completed; no strategic conclusion.",
            "reason": "Temporary regression fixture, not real user evidence.",
            "assessed_at": TIME, "recorded_at": TIME, "assessment_version": "fictional-review-v1",
            "prior_assessment_id": None, "supersedes": [], "manual_reassessment_trigger": None,
            "human_review": {"kind": "human" if human else "synthetic_mock",
                "approved": human, "reviewer": "fictional-unit-reviewer" if human else None,
                "review_reference": "fictional-unit-attestation" if human else None},
            "snapshot_binding": {key: snapshot[key] for key in
                ("snapshot_id", "snapshot_digest", "source_import_digest", "canonical_snapshot_id")},
            "evidence_references": [{"source_id": "fictional-cli-review", "source_type": "synthetic_fixture",
                "reference": "review.json#/claim", "observed_at": TIME,
                "claim": "Fictional personal review state only."}]}
        claim["snapshot_binding"].update(resolved_printing_ids=[PRINTING],
            source_import_reference={"relative_path": "inventory.json",
                                     "sha256": snapshot["source_import_digest"]})
        (self.root / "review.json").write_bytes(canonical_json({"synthetic": not human, "claim": claim}))

    def run_cli(self, command, snapshot, *options):
        output = io.StringIO()
        argv = ["--data-root", str(self.data), "collection", command,
            "--snapshot", snapshot["snapshot_id"], "--source-root", str(self.root), *options]
        with patch("mtglab.__main__.CanonicalCollectionResolver", return_value=self.resolver):
            with contextlib.redirect_stdout(output):
                code = main(argv)
        raw = output.getvalue().encode("utf-8")
        self.assertLessEqual(len(raw), 65536)
        self.assertTrue(raw.endswith(b"\n"))
        self.assertFalse(raw.endswith(b"\n\n"))
        return code, raw, json.loads(raw)

    def records(self):
        return sorted(self.history.glob("*.json"))

    def test_mock_review_receipt_preserves_boundary_and_exact_replay(self):
        snapshot = self.inventory()
        self.review_source(snapshot)
        before = (self.root / "review.json").read_bytes()
        first = self.run_cli("assess", snapshot, "--source", "review.json")
        second = self.run_cli("assess", snapshot, "--source", "review.json")
        self.assertEqual(first, second)
        self.assertEqual(first[0], 0)
        self.assertEqual(len(self.records()), 1)
        receipt = first[2]
        self.assertEqual(receipt["status"], "reviewed")
        self.assertEqual(receipt["human_review"]["kind"], "synthetic_mock")
        self.assertFalse(receipt["human_review"]["approved"])
        self.assertTrue(receipt["source_classification"]["synthetic"])
        self.assertFalse(receipt["source_classification"]["real_user_inventory"])
        self.assertFalse(receipt["canonical_admission"])
        self.assertFalse(receipt["role_approval"])
        self.assertEqual(before, (self.root / "review.json").read_bytes())

    def test_human_approval_is_not_inferred_from_source_claim(self):
        snapshot = self.inventory()
        self.review_source(snapshot, human=True)
        code, _, result = self.run_cli("assess", snapshot, "--source", "review.json")
        self.assertEqual(code, 2)
        self.assertFalse(result["valid"])
        self.assertIn("trusted", result["error"])
        self.assertEqual(self.records(), [])

    def test_oversize_valid_receipt_fails_before_append(self):
        snapshot = self.inventory(collection_id="x" * 70000)
        self.review_source(snapshot)
        code, _, result = self.run_cli("assess", snapshot, "--source", "review.json")
        self.assertEqual(code, 2)
        self.assertIn("delivery exceeds", result["error"])
        self.assertEqual(self.records(), [])

    def test_oversize_error_diagnostic_is_explicit_and_bounded(self):
        snapshot = self.inventory()
        code, raw, result = self.run_cli("audit", snapshot, "--source", "x" * 70000)
        self.assertEqual(code, 2)
        self.assertFalse(result["valid"])
        self.assertTrue(result["diagnostic_omitted"])
        self.assertEqual(raw, canonical_json(result))
        self.assertEqual(self.records(), [])

    def test_rehashed_wrong_card_review_cannot_persist(self):
        original = self.inventory()
        forged = copy.deepcopy(original)
        holding = forged["resolved_holdings"][0]
        holding["card_id"] = OTHER_CARD
        holding["canonical_reference"]["card"]["canonical_identity"] = OTHER_CARD
        forged["snapshot_digest"] = digest({k: v for k, v in forged.items() if k != "snapshot_digest"})
        self.save_snapshot(forged)
        self.review_source(forged)
        code, _, result = self.run_cli("assess", forged, "--source", "review.json")
        self.assertEqual(code, 2)
        self.assertIn("does not reproduce", result["error"])
        self.assertEqual(self.records(), [])

    def test_exact_query_and_context_preserve_synthetic_governance(self):
        snapshot = self.inventory()
        for options in (("--printing-id", PRINTING), ("--reasoning-context",)):
            code, raw, result = self.run_cli("audit", snapshot, "--source", "inventory.json", *options)
            self.assertEqual(code, 0)
            self.assertTrue(result["source_classification"]["synthetic"])
            self.assertFalse(result["source_classification"]["real_user_inventory"])
            self.assertFalse(result["boundaries"]["acquisition_input_ready"])
            self.assertFalse(result["boundaries"]["role_approval"])
            self.assertEqual(raw, canonical_json(result))


if __name__ == "__main__":
    unittest.main()
