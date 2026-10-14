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


from historical_catalog import historical_repository

# This module replays the retained original catalog, not the current catalog.
ROOT = historical_repository()
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

    def inventory(self, *, collection_id="fictional-cli-audit", source_name="inventory.json"):
        value = {"schema_version": "collection-import-v1", "collection_id": collection_id,
            "source": {"type": "synthetic_fixture", "mode": "synthetic_demonstration",
                "real_user_inventory": False, "name": "Fictional CLI test inventory"},
            "entries": [{"printing_id": PRINTING, "quantity": 1, "finish": "nonfoil",
                "language": "English", "condition": None, "storage_location": "fictional-box",
                "provenance": {"owned_lot_id": "fictional-copy",
                    "organization": {"schema_version": "collection-organization-v1",
                                     "storage_classification": "bulk"}}}]}
        path = self.root / source_name
        path.write_bytes(canonical_json(value))
        imported = read_import(path)
        snapshot = build_snapshot(imported, self.resolver.resolve(imported))
        self.save_snapshot(snapshot)
        return snapshot

    def save_snapshot(self, snapshot):
        directory = self.data / "collections/snapshots"
        directory.mkdir(parents=True, exist_ok=True)
        (directory / (snapshot["snapshot_id"] + ".json")).write_bytes(canonical_json(snapshot))

    def review_source(self, snapshot, *, human=False, source_name="review.json",
                      inventory_name="inventory.json"):
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
                "reference": source_name + "#/claim", "observed_at": TIME,
                "claim": "Fictional personal review state only."}]}
        claim["snapshot_binding"].update(resolved_printing_ids=[PRINTING],
            source_import_reference={"relative_path": inventory_name,
                                     "sha256": snapshot["source_import_digest"]})
        (self.root / source_name).write_bytes(canonical_json({"synthetic": not human, "claim": claim}))

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

    def test_real_inventory_cannot_append_mock_review_even_with_trusted_flag(self):
        self.inventory()
        source_path = self.root / "inventory.json"
        document = json.loads(source_path.read_bytes())
        document["source"] = {"type": "user_inventory", "synthetic": False,
                              "real_user_inventory": True,
                              "notice": "Temporary fictional reproduction of a real-declared inventory."}
        source_path.write_bytes(canonical_json(document))
        imported = read_import(source_path)
        snapshot = build_snapshot(imported, self.resolver.resolve(imported))
        self.save_snapshot(snapshot)
        self.review_source(snapshot)
        before = {p: p.read_bytes() for p in (source_path, self.root / "review.json")}
        for options in ((), ("--record-human-review",)):
            with self.subTest(trust=bool(options)):
                code, raw, result = self.run_cli("assess", snapshot, "--source", "review.json", *options)
                self.assertEqual(code, 2)
                self.assertFalse(result["valid"])
                self.assertIn("synthetic inventory", result["error"])
                self.assertEqual(raw, canonical_json(result))
                self.assertEqual(self.records(), [])
                self.assertEqual({p: p.read_bytes() for p in before}, before)

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

    def test_default_repository_audits_each_collection_with_complete_applicable_history(self):
        fixtures = {}
        for label in ("a", "b"):
            inventory_name = f"inventory-{label}.json"
            review_name = f"review-{label}.json"
            snapshot = self.inventory(collection_id=f"fictional-collection-{label}",
                                      source_name=inventory_name)
            self.review_source(snapshot, source_name=review_name, inventory_name=inventory_name)
            code, _, receipt = self.run_cli("assess", snapshot, "--source", review_name)
            self.assertEqual(code, 0)
            fixtures[label] = (snapshot, inventory_name, [receipt["assessment_id"]])

        # A's successor must retain its predecessor even when B shares the
        # default repository and the same exact canonical Card/Printing.
        snapshot, _, ids = fixtures["a"]
        source = json.loads((self.root / "review-a.json").read_bytes())
        claim = source["claim"]
        claim.update(status="pending", outcome=None,
                     reason="Fictional explicit follow-up remains pending.",
                     prior_assessment_id=ids[0], supersedes=[ids[0]],
                     recorded_at="2026-10-12T21:01:00Z")
        (self.root / "review-a-successor.json").write_bytes(canonical_json(source))
        code, _, receipt = self.run_cli("assess", snapshot, "--source", "review-a-successor.json")
        self.assertEqual(code, 0)
        ids.append(receipt["assessment_id"])
        self.assertEqual(len(self.records()), 3)

        for label, (snapshot, inventory_name, ids) in fixtures.items():
            with self.subTest(collection=label):
                code, raw, result = self.run_cli("audit", snapshot, "--source", inventory_name)
                self.assertEqual(code, 0)
                self.assertEqual(raw, canonical_json(result))
                self.assertEqual(result["collection_id"], snapshot["collection_id"])
                self.assertEqual(result["bindings"]["assessment_ids"], ids)
                self.assertTrue(all(record["collection_id"] == snapshot["collection_id"]
                                    for record in result["assessment_history"]))
                self.assertEqual(result["cards"][0]["history_ids"], ids)
                self.assertEqual(result["cards"][0]["review_status"],
                                 "pending" if label == "a" else "reviewed")
                self.assertFalse(result["cards"][0]["new_discovery_eligible"])


if __name__ == "__main__":
    unittest.main()
