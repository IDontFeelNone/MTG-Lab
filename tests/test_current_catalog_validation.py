"""Current checkout consumers: never replace their input with a replay fixture."""
import json
from pathlib import Path
import unittest

from card_intelligence.acquisition import CardAcquisitionAdapter
from card_intelligence.mechanics import MechanicalCardIntelligence, MechanicalEvidenceError
from collection.intelligence import CanonicalCollectionResolver
from historical_catalog import historical_data
from projection.engine import TypedCanonicalProjectionEngine
from query.engine import CanonicalQueryEngine

DATA = Path(__file__).resolve().parents[1] / "data"


class CurrentCatalogValidationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.state = json.loads((DATA / "canonical/state.json").read_bytes())
        cls.query = CanonicalQueryEngine("magic", data_root=DATA, games_root=DATA / "canonical/games")
        cls.resolver = CanonicalCollectionResolver("magic", DATA)
        cls.mechanical = MechanicalCardIntelligence(DATA)

    def test_query_and_collection_read_actual_current_catalog(self):
        self.assertEqual(set(self.mechanical.cards), set(self.state["card"]))
        self.assertTrue(set(self.state["card"]) <= set(self.resolver.cards))
        self.assertEqual(set(self.resolver.production_printing_ids), set(self.state["printing"]))
        original = json.loads((historical_data() / "canonical/state.json").read_bytes())
        if self.state != original:
            self.assertNotEqual(self.resolver.canonical_snapshot_id,
                CanonicalCollectionResolver("magic", historical_data()).canonical_snapshot_id)
        for identifier, record in self.state["printing"].items():
            card = record["values"]["card_id"]
            self.assertEqual(self.query.related(identifier, "printing_card")[0].canonical_identity, card)
            result = self.resolver.resolve({"entries": [{"printing_id": identifier, "quantity": 1}]})["results"][0]
            self.assertEqual((result["status"], result["card_id"]), ("resolved", card))

    def test_projection_validates_current_records_and_all_identifier_aliases(self):
        result = TypedCanonicalProjectionEngine(DATA / "canonical", DATA / "canonical/games",
                                                DATA / "projection-audit").validate()
        self.assertTrue(result["valid"], [r for r in result["checks"] if not r["valid"]])
        self.assertEqual(result["entity_count"], sum(len(v) for v in self.state.values()))
        self.assertEqual(result["identifier_alias_count"], len(self.state["identifier"]))
        self.assertFalse(result["typed_materialization_ready"])

    def test_mechanical_coverage_is_accounted_without_claiming_completeness(self):
        reconciliation = self.mechanical.reconciliation
        self.assertEqual(reconciliation["production_card_count"], len(self.state["card"]))
        missing = set(reconciliation["missing_canonical_card_ids"])
        ambiguous = set(reconciliation["ambiguous_canonical_card_ids"])
        self.assertTrue(missing <= set(self.state["card"]))
        self.assertFalse(missing & ambiguous)
        self.assertEqual(reconciliation["uniquely_mapped_card_count"] + len(missing) + len(ambiguous),
                         len(self.state["card"]))
        for identifier in missing:
            dossier = self.mechanical.dossier(identifier).to_dict()
            self.assertEqual(dossier["source"]["resolution"], "missing")
            self.assertNotIn("provider_record_id", dossier["source"])
            for field in dossier["fields"].values():
                self.assertEqual((field["status"], field["reason"]), ("unknown", "source_binding_missing"))
        with self.assertRaises(MechanicalEvidenceError):
            self.mechanical.dossier("not-a-valid-current-identity")

    def test_missing_current_mechanical_evidence_blocks_acquisition_safely(self):
        missing = set(self.mechanical.reconciliation["missing_canonical_card_ids"])
        rows = [(p, r["values"]) for p, r in self.state["printing"].items()
                if r["values"]["card_id"] in missing]
        # The original fully covered cohort also exercises the empty-gap case;
        # expanded checkouts exercise the same real consumer against new Cards.
        self.assertEqual(bool(rows), bool(missing))
        if rows:
            # The existing acquisition contract compares two or three distinct
            # Cards; a one-Card packet cannot reach missing-evidence handling.
            unique = {}
            for pid, printing in sorted(rows):
                unique.setdefault(printing["card_id"], (pid, printing))
            self.assertGreaterEqual(len(unique), 2)
            selected = list(unique.values())[:2]
            packet = {"schema_version": "card-acquisition-input-v1", "mode": "synthetic_demonstration",
                "as_of": "2026-10-13T00:00:00Z", "canonical_snapshot_id": self.mechanical.snapshot_id,
                "sources": [], "candidates": [{"card_id": printing["card_id"], "printing_id": pid,
                    "acceptable_printing_ids": [pid], "desired_quantity": 1,
                    "preferred_dimensions": {"language": printing["language"], "finish": "nonfoil", "treatment": None}}
                    for pid, printing in selected]}
            result = CardAcquisitionAdapter(DATA).evaluate(packet, source_root=DATA.parent).to_dict()
            self.assertEqual(result["decision"]["recommendation"]["outcome"], "abstain")
            self.assertTrue(any("source_binding_missing" in reason for reason in result["blockers"]))
            self.assertEqual(len(result["candidates"]), 2)
            self.assertTrue(all(c["source_status"] == {"status": "incomplete", "reason": "source_binding_missing"}
                                for c in result["candidates"]))
            self.assertFalse(result["actual_purchase_advice"])


if __name__ == "__main__":
    unittest.main()
