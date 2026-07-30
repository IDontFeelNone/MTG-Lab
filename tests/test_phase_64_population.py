"""Phase 64 scalable population and retained review-report checks."""
from __future__ import annotations

import json
import shutil
import tempfile
import unittest
from pathlib import Path

from evidence_ingestion import ingest_verified_card_printing_wave
from ingestion import ingest_card_printing_wave
from ingestion.intermediate_storage import IntermediateArtifactStorage
from ingestion.population_review import build_population_review_report, report_is_clean
from repository import EvidenceRepositoryError
from validation import validate_document

ROOT = Path(__file__).parents[1]
REVIEW_PATH = (ROOT / "data/intermediate/reviews/mystery_booster_2/mb2-wave-2/"
               "mb2-wave-2-card-printings")


def synthetic_content(count: int) -> bytes:
    records = [{
        "name": f"Synthetic Card {index:02d}", "set_code": "TST",
        "collector_number": str(index), "rarity": "common", "language": "en",
        "card_source_id": "gatherer-magic-card-identities-wave-1",
        "printing_source_id": "scryfall-mystery-booster-2-wave-1",
        "membership_source_id": "wizards-mystery-booster-2-gallery-wave-1",
        "source_location": f"synthetic fixture record {index}",
    } for index in range(1, count + 1)]
    return json.dumps({"bundle_version": "1", "records": records}).encode()


class Phase64PopulationTests(unittest.TestCase):
    def test_batch_accepts_twenty_five_and_never_silently_truncates(self) -> None:
        arguments = dict(product_id="mystery_booster_2", bundle_source_id="synthetic-bundle",
                         acquisition_target_id="synthetic-target",
                         acquired_at="2026-07-30T12:00:00Z")
        wave = ingest_card_printing_wave(synthetic_content(25), **arguments)
        self.assertEqual(len(wave.parsed.records), 25)
        self.assertEqual(len(wave.cards.candidates), 25)
        self.assertEqual(len(wave.printings.candidates), 25)
        with self.assertRaisesRegex(ValueError, "exceeding the limit of 25"):
            ingest_card_printing_wave(synthetic_content(26), **arguments)
        with self.assertRaisesRegex(ValueError, "between one and twenty-five"):
            ingest_card_printing_wave(synthetic_content(1), limit=26, **arguments)

    def test_review_report_is_deterministic_and_summarizes_expected_delta(self) -> None:
        wave = ingest_card_printing_wave(
            synthetic_content(25), product_id="mystery_booster_2",
            bundle_source_id="synthetic-bundle", acquisition_target_id="synthetic-target",
            acquired_at="2026-07-30T12:00:00Z",
        )
        first = build_population_review_report(
            wave, "magic", generated_at="2026-07-30T12:05:00Z"
        )
        second = build_population_review_report(
            wave, "magic", generated_at="2026-07-30T12:05:00Z"
        )
        self.assertEqual(first, second)
        self.assertEqual(first["summary"], {
            "total_records": 25, "new_cards": 25, "reused_existing_cards": 0,
            "new_printings": 25, "duplicates": 0, "conflicts": 0,
            "rejected_records": 0, "expected_card_count_change": 25,
            "expected_printing_count_change": 25,
        })
        self.assertEqual(first["repository_counts_before"], {"cards": 15, "printings": 15})
        self.assertEqual(first["expected_repository_counts_after"], {"cards": 40, "printings": 40})
        self.assertTrue(report_is_clean(first))
        validate_document(first, "population-review-report")

    def test_manifest_population_boundary_rejects_count_and_identity_drift(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            temporary = Path(directory)
            evidence_root = temporary / "sources"
            games_root = temporary / "games"
            shutil.copytree(ROOT / "data/sources", evidence_root)
            shutil.copytree(ROOT / "data/canonical/games", games_root)
            manifest_path = evidence_root / "magic/mb2-wave-2/manifest.json"
            manifest = json.loads(manifest_path.read_text())
            artifact = manifest["artifacts"][0]
            artifact["population_batch"] = {
                "expected_record_count": 2,
                "expected_printing_ids": ["magic.mb2.4.en", "magic.mb2.5.en"],
            }
            manifest_path.write_text(json.dumps(manifest))
            with self.assertRaisesRegex(EvidenceRepositoryError, "record count"):
                ingest_verified_card_printing_wave(
                    "magic", "mb2-wave-2", "mb2-wave-2-card-printing-evidence",
                    acquisition_target_id="mb2-wave-2-card-printings",
                    acquired_at="2026-07-30T00:35:00Z", evidence_root=evidence_root,
                    games_root=games_root,
                )

    def test_retained_report_matches_verified_repository_state(self) -> None:
        wave = ingest_verified_card_printing_wave(
            "magic", "mb2-wave-2", "mb2-wave-2-card-printing-evidence",
            acquisition_target_id="mb2-wave-2-card-printings",
            acquired_at="2026-07-30T00:35:00Z",
        )
        report = build_population_review_report(
            wave, "magic", generated_at="2026-07-30T12:30:00Z"
        )
        retained = json.loads(next(REVIEW_PATH.glob("*.json")).read_text())
        self.assertEqual(report, retained)
        self.assertEqual(report["summary"]["total_records"], 1)
        self.assertEqual(report["summary"]["reused_existing_cards"], 1)
        self.assertEqual(report["summary"]["duplicates"], 1)
        self.assertEqual(report["summary"]["expected_card_count_change"], 0)
        self.assertEqual(report["summary"]["expected_printing_count_change"], 0)
        self.assertTrue(report_is_clean(report))
        storage = IntermediateArtifactStorage()
        self.assertEqual(storage.load_review_report(
            report["product_id"], report["source_id"], report["acquisition_target_id"],
            report["id"],
        ), report)


if __name__ == "__main__":
    unittest.main()
