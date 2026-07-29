"""Product-specific tests for controlled Mystery Booster 2 evidence processing."""
from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from ingestion import AcquisitionRequest, FileSystemEvidenceStorage, IngestionPipeline, hash_bytes
from ingestion.candidates import ArtifactStatus
from ingestion.intermediate_storage import IntermediateArtifactStorage
from ingestion.mystery_booster_2 import (
    MysteryBooster2ProductOverviewNormalizer,
    MysteryBooster2ProductPageParser,
)
from ingestion.models import RawEvidenceArtifact, TransformationStatus
from ingestion.normalization import CandidateNormalizationService
from validation import validate_document

FIXTURE = Path(__file__).parent / "fixtures/mystery_booster_2/official_product_page.html"
ACQUIRED_AT = "2026-07-29T00:00:00Z"


class MysteryBooster2IngestionTests(unittest.TestCase):
    def evidence(self, content: bytes, root: Path) -> RawEvidenceArtifact:
        digest = hash_bytes(content)
        return RawEvidenceArtifact(
            id=digest,
            source_id="official_product_page",
            acquisition_target_id="mystery_booster_2_product_overview",
            product_id="mystery_booster_2",
            content_type="text/html",
            acquired_at=ACQUIRED_AT,
            content_hash=digest,
            storage_path=root / "evidence.bin",
            original_filename="official_product_page.html",
        )

    def test_real_evidence_fixture_produces_schema_valid_traceable_artifacts(self) -> None:
        content = FIXTURE.read_bytes()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            parser = MysteryBooster2ProductPageParser()
            parsed = parser.parse_artifact(content, self.evidence(content, root))
            validate_document(parsed.to_dict(), "parsed-record-artifact")

            result = CandidateNormalizationService(
                IntermediateArtifactStorage(root / "intermediate"),
                (MysteryBooster2ProductOverviewNormalizer(),),
            ).normalize(parsed)

            self.assertEqual(result.status, ArtifactStatus.SUCCEEDED)
            self.assertIsNotNone(result.artifact)
            assert result.artifact is not None
            document = result.artifact.to_dict()
            validate_document(document, "normalized-candidate-artifact")
            self.assertEqual(document["candidates"][0]["payload"]["name"], "Mystery Booster 2")
            self.assertEqual(
                document["candidates"][0]["field_provenance"][0]["parsed_record_id"],
                parsed.records[0].id,
            )

    def test_pipeline_preserves_fixture_bytes_deterministically(self) -> None:
        content = FIXTURE.read_bytes()
        request = AcquisitionRequest(
            game="magic",
            product_id="mystery_booster_2",
            source_id="official_product_page",
            acquisition_target_id="mystery_booster_2_product_overview",
            content_type="text/html",
            acquired_at=ACQUIRED_AT,
            original_filename=FIXTURE.name,
        )
        with tempfile.TemporaryDirectory() as directory:
            storage = FileSystemEvidenceStorage(Path(directory) / "raw")
            pipeline = IngestionPipeline(storage, (MysteryBooster2ProductPageParser(),))
            first = pipeline.ingest(request, content)
            second = pipeline.ingest(request, content)
            self.assertEqual(first.parse_result.status, TransformationStatus.SUCCEEDED)
            self.assertEqual(first.evidence.storage_path, second.evidence.storage_path)
            self.assertEqual(first.evidence.storage_path.read_bytes(), content)
            self.assertEqual(first.evidence.content_hash, hash_bytes(content))

    def test_missing_optional_title_is_partial_and_normalizable(self) -> None:
        content = b"<html><head><title>Mystery Booster 2</title></head></html>"
        with tempfile.TemporaryDirectory() as directory:
            parsed = MysteryBooster2ProductPageParser().parse_artifact(
                content, self.evidence(content, Path(directory))
            )
            self.assertEqual(parsed.status, ArtifactStatus.PARTIAL)
            self.assertIn("Missing open graph title", parsed.warnings)
            result = MysteryBooster2ProductOverviewNormalizer().normalize(parsed)
            self.assertEqual(result.status, ArtifactStatus.PARTIAL)

    def test_invalid_and_empty_inputs_fail_without_candidates(self) -> None:
        parser = MysteryBooster2ProductPageParser()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            invalid = b"\xff"
            parsed = parser.parse_artifact(invalid, self.evidence(invalid, root))
            self.assertEqual(parsed.status, ArtifactStatus.FAILED)
            self.assertEqual(
                MysteryBooster2ProductOverviewNormalizer().normalize(parsed).status,
                ArtifactStatus.FAILED,
            )
            empty = b"<html><head></head></html>"
            self.assertEqual(
                parser.parse_artifact(empty, self.evidence(empty, root)).status,
                ArtifactStatus.FAILED,
            )


if __name__ == "__main__":
    unittest.main()
