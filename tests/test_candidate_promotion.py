"""Tests for generic Card and Printing candidate review and promotion."""
from __future__ import annotations

import json
import shutil
import tempfile
import unittest
from pathlib import Path

from ingestion.candidates import (
    ArtifactStatus, CandidateValidationState, FieldProvenance, NormalizedCandidate,
    NormalizedCandidateArtifact, ParsedArtifact, ParsedRecord,
)
from repository.promotion import (
    CandidatePromotionService, CandidateReview, PromotionConflict,
    PromotionValidationError, ReviewDecision,
)
from validation import validate_document

DECIDED_AT = "2026-07-29T12:00:00Z"
EVIDENCE_HASH = "a" * 64
SOURCE_ID = "gatherer-lightning-bolt-lea"


def candidate_artifacts(entity_type: str, payload: dict, *, state: str = "valid") -> tuple[dict, dict]:
    record_id = f"{entity_type}-record"
    parsed = ParsedArtifact(
        id=f"parsed-{entity_type}", product_id="candidate_review", source_id=SOURCE_ID,
        acquisition_target_id="review-fixture", raw_evidence_hash=EVIDENCE_HASH,
        parser_id="fixture.repository", parser_version="1", parsed_at=DECIDED_AT,
        input_content_type="application/json", status=ArtifactStatus.SUCCEEDED,
        records=(ParsedRecord(record_id, entity_type, payload, "fixture"),),
    )
    provenance = tuple(FieldProvenance(
        field_path=field, value_origin=field, source_id=SOURCE_ID,
        acquisition_target_id="review-fixture", raw_evidence_hash=EVIDENCE_HASH,
        parsed_artifact_id=parsed.id, parsed_record_id=record_id,
        transformation_id="fixture.repository", transformation_version="1",
        provenance_classification="official", confidence=1.0,
    ) for field in payload)
    candidate = NormalizedCandidate(
        id=f"{entity_type}-candidate", entity_type=entity_type, payload=payload,
        parsed_record_ids=(record_id,), field_provenance=provenance, confidence=1.0,
        validation_state=CandidateValidationState(state),
    )
    artifact = NormalizedCandidateArtifact(
        id=f"{entity_type}-candidates", product_id="candidate_review", source_id=SOURCE_ID,
        acquisition_target_id="review-fixture", raw_evidence_hash=EVIDENCE_HASH,
        parsed_artifact_id=parsed.id, normalizer_id="fixture.repository",
        normalizer_version="1", normalized_at=DECIDED_AT, candidate_type=entity_type,
        status=ArtifactStatus.SUCCEEDED, candidates=(candidate,),
    )
    return artifact.to_dict(), parsed.to_dict()


def card_payload() -> dict:
    return {"schema_version": "v1", "id": "magic.test-card", "game": "magic",
            "name": "Test Card", "provenance": [{"source_id": SOURCE_ID,
            "field_paths": ["id", "game", "name"], "claim": "Fixture identity."}]}


def printing_payload(card_id: str = "magic.test-card") -> dict:
    return {"schema_version": "v1", "id": "magic.tst.1.en", "card_id": card_id,
            "set_code": "TST", "collector_number": "1", "rarity": "common",
            "provenance": [{"source_id": SOURCE_ID,
            "field_paths": ["id", "card_id", "set_code", "collector_number", "rarity"],
            "claim": "Fixture printing."}]}


def print_sheet_payload() -> dict:
    return {"schema_version": "v1", "id": "magic.test-sheet", "game": "magic",
            "name": "Test Sheet", "entries": [{"printing_id": "magic.tst.1.en", "weight": 1}],
            "provenance": [{"source_id": SOURCE_ID,
            "field_paths": ["id", "game", "name", "entries"], "claim": "Fixture sheet."}]}


def slot_payload() -> dict:
    return {"schema_version": "v1", "id": "magic.test-slot", "game": "magic",
            "name": "Test Slot", "print_sheet_id": "magic.test-sheet", "draw_count": 1,
            "replacement": True, "provenance": [{"source_id": SOURCE_ID,
            "field_paths": ["id", "game", "name", "print_sheet_id", "draw_count", "replacement"],
            "claim": "Fixture slot."}]}


class CandidatePromotionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        source = Path(__file__).parents[1] / f"data/canonical/games/magic/sources/{SOURCE_ID}.json"
        target = self.root / f"canonical/games/magic/sources/{SOURCE_ID}.json"
        target.parent.mkdir(parents=True); shutil.copyfile(source, target)
        self.service = CandidatePromotionService(
            games_root=self.root / "canonical/games", audit_root=self.root / "audit/promotions"
        )
        self.approved = CandidateReview(ReviewDecision.APPROVED, "maintainer", DECIDED_AT, "verified")

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def promote(self, entity_type: str, payload: dict) -> dict:
        artifact, parsed = candidate_artifacts(entity_type, payload)
        return self.service.review(artifact, parsed, f"{entity_type}-candidate", self.approved)

    def test_card_then_printing_promote_deterministically_and_idempotently(self) -> None:
        card = self.promote("card", card_payload())
        printing = self.promote("printing", printing_payload())
        repeated = self.promote("printing", printing_payload())
        self.assertEqual(card["outcome"], "promoted")
        self.assertEqual(printing, repeated)
        self.assertEqual(printing["entity_type"], "printing")
        self.assertEqual(printing["candidate_snapshot"]["field_provenance"][0]["source_id"], SOURCE_ID)
        validate_document(card, "promotion-audit"); validate_document(printing, "promotion-audit")
        stored = self.root / "canonical/games/magic/printings/magic.tst.1.en/printing.json"
        self.assertEqual(stored.read_text(), json.dumps(printing_payload(), sort_keys=True, indent=2) + "\n")

    def test_orphan_printing_and_unsupported_entity_are_rejected(self) -> None:
        with self.assertRaises(PromotionValidationError):
            self.promote("printing", printing_payload("magic.missing"))
        artifact, parsed = candidate_artifacts("unsupported", {"id": "future.one", "name": "Future"})
        with self.assertRaisesRegex(PromotionValidationError, "not enabled"):
            self.service.review(artifact, parsed, "unsupported-candidate", self.approved)

    def test_rejection_and_conflict_do_not_change_canonical_data(self) -> None:
        artifact, parsed = candidate_artifacts("card", card_payload())
        rejected = self.service.review(
            artifact, parsed, "card-candidate",
            CandidateReview(ReviewDecision.REJECTED, "maintainer", DECIDED_AT, "insufficient"),
        )
        self.assertEqual(rejected["outcome"], "rejected")
        self.promote("card", card_payload())
        changed = card_payload(); changed["name"] = "Conflicting Name"
        with self.assertRaises(PromotionConflict): self.promote("card", changed)
        self.assertEqual(json.loads((self.root / "canonical/games/magic/cards/magic.test-card/card.json").read_text()), card_payload())

    def test_rollback_refuses_to_orphan_a_printing_then_succeeds_in_dependency_order(self) -> None:
        card = self.promote("card", card_payload()); printing = self.promote("printing", printing_payload())
        rollback = CandidateReview(ReviewDecision.APPROVED, "maintainer", "2026-07-29T13:00:00Z", "rollback")
        with self.assertRaises(PromotionConflict): self.service.rollback(card["id"], rollback)
        self.service.rollback(printing["id"], rollback)
        result = self.service.rollback(card["id"], rollback)
        self.assertEqual(result["outcome"], "rolled_back")

    def test_rules_entities_promote_and_rollback_only_in_dependency_order(self) -> None:
        card = self.promote("card", card_payload())
        printing = self.promote("printing", printing_payload())
        sheet = self.promote("print_sheet", print_sheet_payload())
        slot = self.promote("slot", slot_payload())
        self.assertEqual([sheet["entity_type"], slot["entity_type"]], ["print_sheet", "slot"])
        validate_document(sheet, "promotion-audit"); validate_document(slot, "promotion-audit")
        product_path = self.root / "canonical/games/magic/products/test-product/product.json"
        product_path.parent.mkdir(parents=True)
        product_path.write_text(json.dumps({
            "schema_version": "v1", "id": "test-product", "game": "magic", "name": "Test Product",
            "product_type": "booster", "lifecycle_status": "validated", "slot_ids": ["magic.test-slot"],
            "provenance": [{"claim": "Synthetic dependency fixture",
                            "source_classification": "internal", "source_location": "unit test",
                            "verification_status": "confirmed"}],
        }), encoding="utf-8")
        rollback = CandidateReview(ReviewDecision.APPROVED, "maintainer",
                                   "2026-07-29T13:00:00Z", "dependency rollback")
        with self.assertRaises(PromotionConflict): self.service.rollback(printing["id"], rollback)
        with self.assertRaises(PromotionConflict): self.service.rollback(sheet["id"], rollback)
        with self.assertRaises(PromotionConflict): self.service.rollback(slot["id"], rollback)
        product_path.unlink()
        self.service.rollback(slot["id"], rollback)
        self.service.rollback(sheet["id"], rollback)
        self.service.rollback(printing["id"], rollback)
        self.service.rollback(card["id"], rollback)


if __name__ == "__main__": unittest.main()
