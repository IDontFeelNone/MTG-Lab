"""Consumer regressions for a valid catalog with incomplete source coverage.

These fictional records isolate the consumer boundary; the writer integration
tests independently exercise admission and record construction.
"""
from __future__ import annotations

import json
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch

from card_intelligence.acquisition import (CardAcquisitionAdapter,
    CardAcquisitionDossier, CardAcquisitionError)
from card_intelligence.mechanics import (DEFAULT_ACQUISITION,
    MechanicalCardIntelligence, MechanicalEvidenceError, content_identity)
from collection.intelligence import CanonicalCollectionResolver


ROOT = Path(__file__).parents[1]
CARDS = ("f0000000-0000-4000-8000-000000000001",
         "f0000000-0000-4000-8000-000000000002")
PRINTINGS = ("f1000000-0000-4000-8000-000000000001",
             "f1000000-0000-4000-8000-000000000002")


class IncompleteCatalogConsumerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temporary = tempfile.TemporaryDirectory()
        cls.data = Path(cls.temporary.name) / "data"
        for relative in ("canonical", "audit",
                "market/acquisitions/" + DEFAULT_ACQUISITION):
            shutil.copytree(ROOT / "data" / relative, cls.data / relative)
        state_path = cls.data / "canonical/state.json"
        state = json.loads(state_path.read_bytes())
        for index, (card, printing) in enumerate(zip(CARDS, PRINTINGS), 1):
            state["card"][card] = {"entity_type": "card", "values": {
                "card_reference": card, "name": f"Fictional Evidence Gap {index}"},
                "evidence_references": [], "promotion_id": "fictional-test-only"}
            state["printing"][printing] = {"entity_type": "printing", "values": {
                "uuid": printing, "card_id": card, "set_id": "fictional",
                "collector_number": str(index), "language": "ja" if index == 1 else "Japanese",
                "finish_ids": ["nonfoil"]}, "evidence_references": [],
                "promotion_id": "fictional-test-only"}
        state_path.write_text(json.dumps(state), encoding="utf-8")
        cls.adapter = CardAcquisitionAdapter(cls.data)

    @classmethod
    def tearDownClass(cls):
        cls.temporary.cleanup()

    def packet(self):
        return {"schema_version": "card-acquisition-input-v1",
            "mode": "synthetic_demonstration", "as_of": "2026-10-13T00:00:00Z",
            "canonical_snapshot_id": self.adapter.mechanical.snapshot_id,
            "sources": [], "candidates": [{"card_id": card, "printing_id": printing,
                "acceptable_printing_ids": [printing], "desired_quantity": 1,
                "preferred_dimensions": {"language": "ja", "finish": "nonfoil", "treatment": None}}
                for card, printing in zip(CARDS, PRINTINGS)]}

    def test_missing_coverage_is_explicit_and_does_not_invent_source_records(self):
        dossier = self.adapter.mechanical.dossier(CARDS[0]).to_dict()
        self.assertEqual(dossier["source"]["resolution"], "missing")
        for field in dossier["fields"].values():
            self.assertEqual((field["status"], field["reason"]),
                ("unknown", "source_binding_missing"))
            self.assertNotIn("value", field)
        for key in ("oracle_id", "provider_record_id", "record_content_identity", "source_record_index"):
            self.assertNotIn(key, dossier["source"])

    def test_full_evaluation_and_dossier_replay_abstain_on_missing_mechanical_binding(self):
        result = self.adapter.evaluate(self.packet(), source_root=self.data).to_dict()
        self.assertEqual(result["decision"]["recommendation"]["outcome"], "abstain")
        self.assertFalse(result["actual_purchase_advice"])
        for row in result["candidates"]:
            reason = "source_binding_missing"
            self.assertIn(f"mechanical_source:{row['card_id']}:{reason}", result["blockers"])
            self.assertEqual(row["source_status"], {"status": "incomplete", "reason": reason})
            self.assertIsNone(row["acquisition_eligible"])
            self.assertIsNone(row["complete_cost_units"])
            self.assertNotIn("record_content_identity", row["source"])
        self.assertEqual(CardAcquisitionDossier(result).to_dict(), result)

    def test_invalid_canonical_identity_remains_an_error(self):
        packet = self.packet()
        packet["candidates"][0]["card_id"] = "not-admitted"
        with self.assertRaisesRegex(CardAcquisitionError, "exact linked canonical"):
            self.adapter.evaluate(packet, source_root=self.data)
        with self.assertRaisesRegex(MechanicalEvidenceError, "exact admitted"):
            self.adapter.mechanical.dossier("not-admitted")

    def test_corrupt_retained_bytes_are_not_missing_coverage(self):
        with tempfile.TemporaryDirectory() as temporary:
            data = Path(temporary) / "data"
            relative = "market/acquisitions/" + DEFAULT_ACQUISITION
            shutil.copytree(self.data / relative, data / relative)
            path = data / relative / "source-mb2.json"
            path.write_bytes(path.read_bytes() + b" ")
            with patch("card_intelligence.mechanics.CanonicalQueryEngine",
                    return_value=self.adapter.query):
                with self.assertRaisesRegex(MechanicalEvidenceError, "integrity mismatch"):
                    MechanicalCardIntelligence(data)

    def test_false_unique_binding_is_not_downgraded_to_missing_coverage(self):
        original = self.adapter.mechanical.dossier
        def corrupted(card_id):
            value = original(card_id).to_dict()
            value["source"]["resolution"] = "unique"
            value["source"]["oracle_id"] = card_id
            return type("CorruptedDossier", (), {"to_dict": lambda self: value})()
        with patch.object(self.adapter.mechanical, "dossier", side_effect=corrupted):
            with self.assertRaisesRegex(CardAcquisitionError, "mechanical source binding"):
                self.adapter.evaluate(self.packet(), source_root=self.data)

    def test_ambiguous_source_coverage_abstains_without_selecting_a_row(self):
        original = self.adapter.mechanical.dossier
        def ambiguous(card_id):
            value = original(card_id).to_dict()
            value["source"].update(resolution="ambiguous",
                matching_provider_record_ids=["fictional-source-a", "fictional-source-b"])
            return type("AmbiguousDossier", (), {"to_dict": lambda self: value})()
        with patch.object(self.adapter.mechanical, "dossier", side_effect=ambiguous):
            result = self.adapter.evaluate(self.packet(), source_root=self.data).to_dict()
        self.assertEqual(result["decision"]["recommendation"]["outcome"], "abstain")
        self.assertTrue(all(row["source_status"]["reason"] == "source_binding_ambiguous"
            for row in result["candidates"]))
        self.assertEqual(CardAcquisitionDossier(result).to_dict(), result)

    def test_partial_row_metadata_cannot_masquerade_as_missing_coverage(self):
        original = self.adapter.mechanical.dossier
        def partial(card_id):
            value = original(card_id).to_dict()
            value["source"]["record_content_identity"] = "sha256:" + "0" * 64
            return type("PartialDossier", (), {"to_dict": lambda self: value})()
        with patch.object(self.adapter.mechanical, "dossier", side_effect=partial):
            with self.assertRaisesRegex(CardAcquisitionError, "incomplete mechanical source binding"):
                self.adapter.evaluate(self.packet(), source_root=self.data)

    def test_mixed_covered_and_uncovered_cards_preserve_the_existing_source_reference(self):
        packet = self.packet()
        covered_printing = next(p for p in self.adapter.printings.values()
            if p.canonical_values.get("card_id") not in CARDS and
                self.adapter.mechanical.dossier(p.canonical_values["card_id"]).to_dict()["source"]["resolution"] == "unique")
        pid = covered_printing.canonical_values["uuid"]
        card = covered_printing.canonical_values["card_id"]
        packet["candidates"][1].update(card_id=card, printing_id=pid, acceptable_printing_ids=[pid])
        result = self.adapter.evaluate(packet, source_root=self.data).to_dict()
        covered = next(row for row in result["candidates"] if row["card_id"] == card)
        self.assertEqual(covered["source"]["resolution"], "unique")
        self.assertNotIn("source_status", covered)
        self.assertTrue(any(e["evidence_id"] == covered["mechanical_dossier_id"] for e in result["evidence"]))
        self.assertEqual(result["decision"]["recommendation"]["outcome"], "abstain")
        self.assertEqual(CardAcquisitionDossier(result).to_dict(), result)

    def test_japanese_labels_and_codes_are_equivalent_without_accepting_english(self):
        resolver = CanonicalCollectionResolver("magic", self.data)
        for printing in PRINTINGS:
            for language in ("Japanese", "ja"):
                with self.subTest(printing=printing, language=language):
                    row = resolver.resolve({"entries": [{"printing_id": printing,
                        "quantity": 1, "language": language, "finish": "nonfoil"}]})["results"][0]
                    self.assertEqual(row["status"], "resolved")
            for language in ("English", "en"):
                row = resolver.resolve({"entries": [{"printing_id": printing,
                    "quantity": 1, "language": language}]})["results"][0]
                self.assertEqual(row["status"], "unresolved")
                self.assertIn("language", row["dimension_conflicts"])

    def test_rehashed_missing_binding_cannot_claim_acquisition(self):
        result = self.adapter.evaluate(self.packet(), source_root=self.data).to_dict()
        result["candidates"][0]["source_status"] = {"status": "complete"}
        result["dossier_id"] = content_identity({k: v for k, v in result.items() if k != "dossier_id"})
        with self.assertRaises(CardAcquisitionError):
            CardAcquisitionDossier(result)
