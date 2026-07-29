"""Repository checks for deterministic Mystery Booster 2 Wave 1 ingestion."""
from __future__ import annotations

import json
import unittest
from pathlib import Path

from ingestion import ingest_card_printing_wave
from ingestion.candidate_validation import validate_candidate_artifact
from ingestion.candidates import CandidateValidationState
from repository import load_acquisition_manifest, load_card_repository, load_rules_repository
from validation import validate_document

ROOT = Path(__file__).parents[1]
RAW = ROOT / "data/raw/magic/mystery_booster_2/wave_1/card-printing-evidence.json"
RELATIVE = Path("mystery_booster_2/mb2-wave-1-evidence-bundle/mb2-wave-1-card-printings")
WAVE_CARD_IDS = {"magic.abzan-falconer", "magic.academy-manufactor", "magic.ad-nauseam"}
WAVE_PRINTING_IDS = {"magic.mb2.1.en", "magic.mb2.2.en", "magic.mb2.3.en"}


class Phase61PopulationTests(unittest.TestCase):
    def test_pipeline_is_bounded_deterministic_and_matches_retained_artifacts(self) -> None:
        arguments = dict(
            product_id="mystery_booster_2", bundle_source_id="mb2-wave-1-evidence-bundle",
            acquisition_target_id="mb2-wave-1-card-printings",
            acquired_at="2026-07-29T23:30:00Z",
        )
        first = ingest_card_printing_wave(RAW.read_bytes(), **arguments)
        second = ingest_card_printing_wave(RAW.read_bytes(), **arguments)
        self.assertEqual(first, second)
        self.assertEqual(len(first.cards.candidates), 3)
        self.assertLessEqual(len(first.cards.candidates), 5)
        self.assertEqual(len(first.cards.candidates), len(first.printings.candidates))

        parsed = json.loads((ROOT / "data/intermediate/parsed" / RELATIVE /
                             "mb2-wave-1-parsed.json").read_text())
        cards = json.loads((ROOT / "data/intermediate/candidates" / RELATIVE /
                            "mb2-wave-1-card-candidates.json").read_text())
        printings = json.loads((ROOT / "data/intermediate/candidates" / RELATIVE /
                                "mb2-wave-1-printing-candidates.json").read_text())
        self.assertEqual(first.parsed.to_dict(), parsed)
        self.assertEqual(first.cards.to_dict(), cards)
        self.assertEqual(first.printings.to_dict(), printings)
        for artifact in (cards, printings):
            self.assertEqual(validate_candidate_artifact(artifact, parsed).state,
                             CandidateValidationState.VALID)

    def test_pipeline_enforces_wave_cap_and_complete_evidence(self) -> None:
        arguments = dict(product_id="mystery_booster_2", bundle_source_id="bundle",
                         acquisition_target_id="target", acquired_at="2026-07-29T23:30:00Z")
        with self.assertRaisesRegex(ValueError, "between one and five"):
            ingest_card_printing_wave(RAW.read_bytes(), limit=6, **arguments)
        document = json.loads(RAW.read_text()); del document["records"][0]["rarity"]
        with self.assertRaisesRegex(ValueError, "lacks required fields"):
            ingest_card_printing_wave(json.dumps(document).encode(), **arguments)

    def test_multiple_sources_manifest_and_field_attribution_validate(self) -> None:
        manifest = load_acquisition_manifest(
            "magic", "mystery_booster_2", "mb2_wave_1_card_printings"
        )
        self.assertEqual(len(manifest["source_ids"]), 4)
        parsed = json.loads((ROOT / "data/intermediate/parsed" / RELATIVE /
                             "mb2-wave-1-parsed.json").read_text())
        printings = json.loads((ROOT / "data/intermediate/candidates" / RELATIVE /
                                "mb2-wave-1-printing-candidates.json").read_text())
        sources = {item["source_id"] for candidate in printings["candidates"]
                   for item in candidate["field_provenance"]}
        self.assertEqual(sources, {
            "scryfall-mystery-booster-2-wave-1",
            "wizards-mystery-booster-2-gallery-wave-1",
        })
        validate_document(parsed, "parsed-record-artifact")

    def test_exact_promoted_increment_is_canonical_audited_and_stops_before_rules(self) -> None:
        cards, printings = load_card_repository("magic")
        self.assertEqual(WAVE_CARD_IDS, {item["id"] for item in cards} & WAVE_CARD_IDS)
        self.assertEqual(WAVE_PRINTING_IDS, {item["id"] for item in printings} & WAVE_PRINTING_IDS)
        wave_printings = [item for item in printings if item["id"] in WAVE_PRINTING_IDS]
        self.assertTrue(all(item["card_id"] in WAVE_CARD_IDS for item in wave_printings))
        self.assertTrue(all(item["metadata"]["product_membership"] == ["mystery_booster_2"]
                            for item in wave_printings))
        wave_audits = []
        for path in (ROOT / "data/audit/promotions").glob("*.json"):
            event = json.loads(path.read_text())
            if event["entity_id"] in WAVE_CARD_IDS | WAVE_PRINTING_IDS:
                wave_audits.append(event)
        self.assertEqual(len(wave_audits), 6)
        self.assertTrue(all(event["outcome"] == "promoted" for event in wave_audits))
        self.assertEqual(load_rules_repository("magic"), ((), ()))
        product = json.loads((ROOT / "data/canonical/games/magic/products/mystery_booster_2/product.json").read_text())
        self.assertEqual(product["lifecycle_status"], "foundation")
        self.assertEqual(product["slot_ids"], [])


if __name__ == "__main__":
    unittest.main()
