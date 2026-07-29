"""Repository-level checks for the bounded Phase 58 population increment."""

from __future__ import annotations

import json
import unittest
from pathlib import Path

from ingestion.candidate_validation import validate_candidate_artifact
from ingestion.candidates import CandidateValidationState
from repository import load_card_repository
from validation import validate_document


ROOT = Path(__file__).parents[1]
SOURCE_ID = "gatherer-limited-edition-alpha-phase-58"
TARGET = "limited-edition-alpha-fixed-ten"


class Phase58PopulationTests(unittest.TestCase):
    def test_fixed_candidate_artifacts_are_valid_and_bounded(self) -> None:
        base = Path("phase_58_population") / SOURCE_ID / TARGET
        for entity_type in ("card", "printing"):
            parsed = json.loads((
                ROOT / "data/intermediate/parsed" / base / f"phase-58-{entity_type}-parsed.json"
            ).read_text())
            candidates = json.loads((
                ROOT / "data/intermediate/candidates" / base
                / f"phase-58-{entity_type}-candidates.json"
            ).read_text())
            validate_document(parsed, "parsed-record-artifact")
            validate_document(candidates, "normalized-candidate-artifact")
            self.assertEqual(candidates["candidate_count"], 10)
            self.assertEqual(
                validate_candidate_artifact(candidates, parsed).state,
                CandidateValidationState.VALID,
            )

    def test_promoted_increment_has_source_attribution_and_audits(self) -> None:
        cards, printings = load_card_repository("magic")
        phase_cards = [card for card in cards if card["provenance"][0]["source_id"] == SOURCE_ID]
        phase_printings = [printing for printing in printings
                           if printing["provenance"][0]["source_id"] == SOURCE_ID]
        self.assertEqual(len(phase_cards), 10)
        self.assertEqual(len(phase_printings), 10)
        self.assertTrue(all(
            item["provenance"][0]["source_id"] == SOURCE_ID
            for item in (*phase_cards, *phase_printings)
        ))

        audits = []
        for path in sorted((ROOT / "data/audit/promotions").glob("*.json")):
            event = json.loads(path.read_text())
            validate_document(event, "promotion-audit")
            if event["candidate_snapshot"]["payload"]["provenance"][0]["source_id"] == SOURCE_ID:
                audits.append(event)
        self.assertEqual(len(audits), 20)
        self.assertTrue(all(event["decision"] == "approved" for event in audits))
        self.assertTrue(all(event["outcome"] == "promoted" for event in audits))
        self.assertEqual({event["entity_type"] for event in audits}, {"card", "printing"})


if __name__ == "__main__":
    unittest.main()
