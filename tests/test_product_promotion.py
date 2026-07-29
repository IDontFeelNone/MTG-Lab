"""Unit and integration tests for controlled canonical product promotion."""
from __future__ import annotations

import json
import tempfile
import unittest
from copy import deepcopy
from pathlib import Path
from unittest.mock import patch

from ingestion.candidates import (
    ArtifactStatus,
    CandidateValidationState,
    FieldProvenance,
    NormalizedCandidate,
    NormalizedCandidateArtifact,
    ParsedArtifact,
    ParsedRecord,
)
from ingestion.hashing import hash_bytes
from ingestion.intermediate_storage import IntermediateArtifactStorage
from ingestion.mystery_booster_2 import (
    MysteryBooster2ProductOverviewNormalizer,
    MysteryBooster2ProductPageParser,
)
from ingestion.models import RawEvidenceArtifact
from ingestion.normalization import CandidateNormalizationService
from repository.promotion import (
    AuditStorageError,
    ProductPromotionService,
    ProductReview,
    PromotionConflict,
    PromotionValidationError,
    ReviewDecision,
)
from validation import validate_document

EVIDENCE_HASH = "a" * 64
DECIDED_AT = "2026-07-29T12:00:00Z"


def complete_product(product_id: str = "new_product") -> dict:
    return {
        "schema_version": "v1",
        "id": product_id,
        "game": "magic",
        "name": "New Product",
        "product_type": "sealed_product",
        "lifecycle_status": "foundation",
        "slot_ids": [],
        "provenance": [
            {
                "claim": "New Product is a Magic product.",
                "source_classification": "official",
                "source_location": "fixture",
                "verification_status": "confirmed",
            }
        ],
    }


def artifacts(payload: dict | None = None, *, validation_state: str = "valid") -> tuple[dict, dict]:
    product = payload or complete_product()
    parsed = ParsedArtifact(
        id="parsed-product",
        product_id="mystery_booster_2",
        source_id="official_product_page",
        acquisition_target_id="mystery_booster_2_product_overview",
        raw_evidence_hash=EVIDENCE_HASH,
        parser_id="fixture.product",
        parser_version="1",
        parsed_at=DECIDED_AT,
        input_content_type="text/html",
        status=ArtifactStatus.SUCCEEDED,
        records=(
            ParsedRecord(
                id="product-record",
                record_type="product",
                raw_fields=deepcopy(product),
                source_location="fixture",
            ),
        ),
    )
    provenance = tuple(
        FieldProvenance(
            field_path=field,
            value_origin=field,
            source_id=parsed.source_id,
            acquisition_target_id=parsed.acquisition_target_id,
            raw_evidence_hash=parsed.raw_evidence_hash,
            parsed_artifact_id=parsed.id,
            parsed_record_id=parsed.records[0].id,
            transformation_id="fixture.product",
            transformation_version="1",
            provenance_classification="official",
            confidence=1.0,
        )
        for field in product
    )
    candidate = NormalizedCandidate(
        id="product-candidate",
        entity_type="product",
        payload=product,
        parsed_record_ids=(parsed.records[0].id,),
        field_provenance=provenance,
        confidence=1.0,
        validation_state=CandidateValidationState(validation_state),
    )
    normalized = NormalizedCandidateArtifact(
        id="product-candidates",
        product_id=parsed.product_id,
        source_id=parsed.source_id,
        acquisition_target_id=parsed.acquisition_target_id,
        raw_evidence_hash=parsed.raw_evidence_hash,
        parsed_artifact_id=parsed.id,
        normalizer_id="fixture.product",
        normalizer_version="1",
        normalized_at=DECIDED_AT,
        candidate_type="product",
        status=ArtifactStatus.SUCCEEDED,
        candidates=(candidate,),
    )
    return normalized.to_dict(), parsed.to_dict()


class ProductPromotionUnitTests(unittest.TestCase):
    def service(self, directory: str) -> ProductPromotionService:
        root = Path(directory)
        return ProductPromotionService(
            games_root=root / "canonical/games",
            audit_root=root / "audit/promotions",
        )

    def approved(self, *, reason: str = "Reviewed source evidence") -> ProductReview:
        return ProductReview(ReviewDecision.APPROVED, "reviewer@example.test", DECIDED_AT, reason)

    def test_approved_valid_product_is_promoted_audited_and_idempotent(self) -> None:
        candidate, parsed = artifacts()
        with tempfile.TemporaryDirectory() as directory:
            service = self.service(directory)
            first = service.review(candidate, parsed, "product-candidate", self.approved())
            second = service.review(candidate, parsed, "product-candidate", self.approved())
            product_path = Path(directory) / "canonical/games/magic/products/new_product/product.json"

            self.assertEqual(first, second)
            self.assertEqual(first["outcome"], "promoted")
            self.assertEqual(json.loads(product_path.read_text()), complete_product())
            self.assertEqual(first["candidate_snapshot"], candidate["candidates"][0])
            validate_document(first, "promotion-audit")
            self.assertEqual(len(list((Path(directory) / "audit/promotions").glob("*.json"))), 1)

    def test_rejection_is_audited_and_never_changes_canonical_data(self) -> None:
        candidate, parsed = artifacts()
        review = ProductReview(
            ReviewDecision.REJECTED, "reviewer@example.test", DECIDED_AT, "Insufficient evidence"
        )
        with tempfile.TemporaryDirectory() as directory:
            event = self.service(directory).review(candidate, parsed, "product-candidate", review)
            self.assertEqual(event["outcome"], "rejected")
            self.assertFalse((Path(directory) / "canonical").exists())
            validate_document(event, "promotion-audit")

    def test_invalid_unreviewed_and_wrong_type_candidates_cannot_bypass_validation(self) -> None:
        candidate, parsed = artifacts(validation_state="unvalidated")
        with tempfile.TemporaryDirectory() as directory:
            service = self.service(directory)
            with self.assertRaises(PromotionValidationError):
                service.review(candidate, parsed, "product-candidate", self.approved())

            candidate, parsed = artifacts()
            candidate["raw_evidence_hash"] = "b" * 64
            with self.assertRaises(PromotionValidationError):
                service.review(candidate, parsed, "product-candidate", self.approved())

            candidate, parsed = artifacts()
            candidate["candidates"][0]["entity_type"] = "card"
            with self.assertRaises(PromotionValidationError):
                service.review(candidate, parsed, "product-candidate", self.approved())

            candidate, parsed = artifacts()
            candidate["candidates"][0]["field_provenance"] = candidate["candidates"][0][
                "field_provenance"
            ][:-1]
            with self.assertRaises(PromotionValidationError):
                service.review(candidate, parsed, "product-candidate", self.approved())

    def test_conflict_is_reported_without_overwrite(self) -> None:
        candidate, parsed = artifacts({"id": "existing", "name": "Candidate Name"})
        canonical = complete_product("existing")
        canonical["name"] = "Canonical Name"
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "canonical/games/magic/products/existing/product.json"
            path.parent.mkdir(parents=True)
            path.write_text(json.dumps(canonical), encoding="utf-8")
            with self.assertRaises(PromotionConflict):
                self.service(directory).review(candidate, parsed, "product-candidate", self.approved())
            self.assertEqual(json.loads(path.read_text()), canonical)

    def test_rollback_uses_audit_history_and_is_idempotent(self) -> None:
        candidate, parsed = artifacts()
        rollback_review = ProductReview(
            ReviewDecision.APPROVED, "maintainer@example.test", "2026-07-29T13:00:00Z", "Rollback test"
        )
        with tempfile.TemporaryDirectory() as directory:
            service = self.service(directory)
            promotion = service.review(candidate, parsed, "product-candidate", self.approved())
            first = service.rollback(promotion["id"], rollback_review)
            second = service.rollback(promotion["id"], rollback_review)

            self.assertEqual(first, second)
            self.assertEqual(first["related_audit_id"], promotion["id"])
            self.assertEqual(first["outcome"], "rolled_back")
            self.assertFalse(
                (Path(directory) / "canonical/games/magic/products/new_product/product.json").exists()
            )
            self.assertEqual(len(list((Path(directory) / "audit/promotions").glob("*.json"))), 2)

    def test_rollback_refuses_changed_canonical_state(self) -> None:
        candidate, parsed = artifacts()
        with tempfile.TemporaryDirectory() as directory:
            service = self.service(directory)
            promotion = service.review(candidate, parsed, "product-candidate", self.approved())
            path = Path(directory) / "canonical/games/magic/products/new_product/product.json"
            changed = complete_product()
            changed["name"] = "Changed Later"
            path.write_text(json.dumps(changed), encoding="utf-8")
            with self.assertRaises(PromotionConflict):
                service.rollback(
                    promotion["id"],
                    ProductReview(ReviewDecision.APPROVED, "maintainer", DECIDED_AT),
                )
            self.assertEqual(json.loads(path.read_text()), changed)

    def test_failed_audit_write_compensates_canonical_changes(self) -> None:
        candidate, parsed = artifacts()
        with tempfile.TemporaryDirectory() as directory:
            service = self.service(directory)
            path = Path(directory) / "canonical/games/magic/products/new_product/product.json"
            with patch.object(
                service, "_store_audit", side_effect=AuditStorageError("fixture audit failure")
            ):
                with self.assertRaises(AuditStorageError):
                    service.review(candidate, parsed, "product-candidate", self.approved())
            self.assertFalse(path.exists())

    def test_failed_rollback_audit_restores_promoted_state(self) -> None:
        candidate, parsed = artifacts()
        with tempfile.TemporaryDirectory() as directory:
            service = self.service(directory)
            promotion = service.review(candidate, parsed, "product-candidate", self.approved())
            path = Path(directory) / "canonical/games/magic/products/new_product/product.json"
            with patch.object(
                service, "_store_audit", side_effect=AuditStorageError("fixture audit failure")
            ):
                with self.assertRaises(AuditStorageError):
                    service.rollback(
                        promotion["id"],
                        ProductReview(ReviewDecision.APPROVED, "maintainer", DECIDED_AT),
                    )
            self.assertEqual(json.loads(path.read_text()), complete_product())


class MysteryBooster2PromotionIntegrationTests(unittest.TestCase):
    def test_ingestion_candidate_can_be_reviewed_against_canonical_product(self) -> None:
        fixture = Path(__file__).parent / "fixtures/mystery_booster_2/official_product_page.html"
        content = fixture.read_bytes()
        digest = hash_bytes(content)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            evidence = RawEvidenceArtifact(
                id=digest,
                source_id="official_product_page",
                acquisition_target_id="mystery_booster_2_product_overview",
                product_id="mystery_booster_2",
                content_type="text/html",
                acquired_at=DECIDED_AT,
                content_hash=digest,
                storage_path=root / "evidence.bin",
                original_filename=fixture.name,
            )
            parsed = MysteryBooster2ProductPageParser().parse_artifact(content, evidence)
            normalized = CandidateNormalizationService(
                IntermediateArtifactStorage(root / "intermediate")
            ).normalize(parsed, normalizer=MysteryBooster2ProductOverviewNormalizer())
            assert normalized.artifact is not None

            canonical_source = (
                Path(__file__).parents[1]
                / "data/canonical/games/magic/products/mystery_booster_2/product.json"
            )
            canonical_target = root / "canonical/games/magic/products/mystery_booster_2/product.json"
            canonical_target.parent.mkdir(parents=True)
            canonical_target.write_bytes(canonical_source.read_bytes())
            service = ProductPromotionService(
                games_root=root / "canonical/games", audit_root=root / "audit/promotions"
            )
            event = service.review(
                normalized.artifact.to_dict(),
                parsed.to_dict(),
                normalized.artifact.candidates[0].id,
                ProductReview(ReviewDecision.APPROVED, "maintainer", DECIDED_AT),
            )

            self.assertEqual(event["outcome"], "confirmed")
            self.assertEqual(canonical_target.read_bytes(), canonical_source.read_bytes())
            self.assertEqual(
                event["candidate_snapshot"]["field_provenance"],
                normalized.artifact.to_dict()["candidates"][0]["field_provenance"],
            )


if __name__ == "__main__":
    unittest.main()
