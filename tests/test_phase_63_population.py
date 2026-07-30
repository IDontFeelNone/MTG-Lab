"""Repository checks for evidence-backed Mystery Booster 2 Wave 2."""

from __future__ import annotations

import hashlib
import json
import shutil
import tempfile
import unittest
from pathlib import Path

from evidence_ingestion import (
    card_candidate_ids_requiring_promotion,
    ingest_verified_card_printing_wave,
)
from ingestion.candidate_validation import validate_candidate_artifact
from ingestion.candidates import CandidateValidationState
from repository import EvidenceRepositoryError, load_card_repository, load_rules_repository

ROOT = Path(__file__).parents[1]
RELATIVE = Path("mystery_booster_2/mb2-wave-2/mb2-wave-2-card-printings")
CARD_ID = "magic.adarkar-windform"
PRINTING_ID = "magic.mb2.4.en"


class Phase63PopulationTests(unittest.TestCase):
    def ingest(self, **overrides):
        arguments = dict(
            game="magic", bundle_id="mb2-wave-2",
            artifact_id="mb2-wave-2-card-printing-evidence",
            acquisition_target_id="mb2-wave-2-card-printings",
            acquired_at="2026-07-30T00:35:00Z",
        )
        arguments.update(overrides)
        return ingest_verified_card_printing_wave(**arguments)

    def test_verified_pipeline_is_deterministic_and_matches_retained_artifacts(self) -> None:
        first = self.ingest()
        second = self.ingest()
        self.assertEqual(first, second)
        self.assertEqual([candidate.payload["id"] for candidate in first.cards.candidates],
                         [CARD_ID])
        self.assertEqual([candidate.payload["id"] for candidate in first.printings.candidates],
                         [PRINTING_ID])
        parsed = json.loads((ROOT / "data/intermediate/parsed" / RELATIVE /
                             "mb2-wave-2-parsed.json").read_text())
        cards = json.loads((ROOT / "data/intermediate/candidates" / RELATIVE /
                            "mb2-wave-2-card-candidates.json").read_text())
        printings = json.loads((ROOT / "data/intermediate/candidates" / RELATIVE /
                                "mb2-wave-2-printing-candidates.json").read_text())
        self.assertEqual(first.parsed.to_dict(), parsed)
        self.assertEqual(first.cards.to_dict(), cards)
        self.assertEqual(first.printings.to_dict(), printings)
        for artifact in (cards, printings):
            self.assertEqual(validate_candidate_artifact(artifact, parsed).state,
                             CandidateValidationState.VALID)

    def test_embedded_sources_must_be_attributed_by_verified_artifact(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            temporary = Path(directory)
            evidence_root = temporary / "sources"
            games_root = temporary / "games"
            shutil.copytree(ROOT / "data/sources", evidence_root)
            shutil.copytree(ROOT / "data/canonical/games", games_root)
            archive = evidence_root / "magic/mb2-wave-2/files/card-printing-evidence.json"
            document = json.loads(archive.read_text())
            document["records"][0]["card_source_id"] = "undeclared-source"
            content = (json.dumps(document, indent=2) + "\n").encode()
            archive.write_bytes(content)
            manifest_path = evidence_root / "magic/mb2-wave-2/manifest.json"
            manifest = json.loads(manifest_path.read_text())
            manifest["artifacts"][0]["byte_size"] = len(content)
            manifest["artifacts"][0]["sha256"] = hashlib.sha256(content).hexdigest()
            manifest_path.write_text(json.dumps(manifest))
            with self.assertRaisesRegex(EvidenceRepositoryError,
                                        "not attributed to the verified artifact"):
                self.ingest(evidence_root=evidence_root, games_root=games_root)

    def test_existing_card_is_not_recreated_and_printing_references_it(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            temporary = Path(directory)
            evidence_root = temporary / "sources"
            games_root = temporary / "games"
            shutil.copytree(ROOT / "data/sources", evidence_root)
            shutil.copytree(ROOT / "data/canonical/games", games_root)
            archive = evidence_root / "magic/mb2-wave-2/files/card-printing-evidence.json"
            document = json.loads(archive.read_text())
            document["records"][0].update(
                name="Lightning Bolt", collector_number="999", rarity="common"
            )
            content = (json.dumps(document, indent=2) + "\n").encode()
            archive.write_bytes(content)
            manifest_path = evidence_root / "magic/mb2-wave-2/manifest.json"
            manifest = json.loads(manifest_path.read_text())
            manifest["artifacts"][0]["byte_size"] = len(content)
            manifest["artifacts"][0]["sha256"] = hashlib.sha256(content).hexdigest()
            manifest_path.write_text(json.dumps(manifest))
            wave = self.ingest(evidence_root=evidence_root, games_root=games_root)
            self.assertEqual(
                card_candidate_ids_requiring_promotion(
                    wave, "magic", games_root=games_root
                ),
                (),
            )
            self.assertEqual(len(wave.printings.candidates), 1)
            self.assertEqual(wave.printings.candidates[0].payload["card_id"],
                             "magic.lightning-bolt")

    def test_population_is_bounded_audited_source_declared_and_stops_before_rules(self) -> None:
        cards, printings = load_card_repository("magic")
        self.assertIn(CARD_ID, {card["id"] for card in cards})
        printing = next(item for item in printings if item["id"] == PRINTING_ID)
        self.assertEqual(printing["card_id"], CARD_ID)
        manifest = json.loads((ROOT / "data/sources/magic/mb2-wave-2/manifest.json").read_text())
        declared = set(manifest["source_ids"])
        embedded = {entry["source_id"] for entry in printing["provenance"]}
        self.assertLessEqual(embedded, declared)
        audits = [json.loads(path.read_text()) for path in
                  (ROOT / "data/audit/promotions").glob("*.json")]
        wave_audits = [event for event in audits
                       if event["entity_id"] in {CARD_ID, PRINTING_ID}]
        self.assertEqual(len(wave_audits), 2)
        self.assertTrue(all(event["outcome"] == "promoted" for event in wave_audits))
        self.assertEqual(load_rules_repository("magic"), ((), ()))
        product = json.loads((ROOT / "data/canonical/games/magic/products/"
                              "mystery_booster_2/product.json").read_text())
        self.assertEqual(product["lifecycle_status"], "foundation")
        self.assertEqual(product["slot_ids"], [])


if __name__ == "__main__":
    unittest.main()
