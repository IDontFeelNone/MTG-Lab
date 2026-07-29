"""Tests for the generic evidence-preserving ingestion foundation."""
from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from ingestion import (
    AcquisitionRequest, ConflictingStoredContent, FileSystemEvidenceStorage,
    HashingError, IngestionPipeline, InvalidEvidencePath, ParserMismatch,
    SourceTargetMismatch, TransformationStatus, UnknownAcquisitionTarget,
    UnknownSourceReference, UnsupportedContentType, hash_bytes, hash_file,
)
from ingestion.models import ParseResult, RawEvidenceArtifact
from ingestion.parsers import EvidenceParser


def _source(identifier: str) -> dict:
    return {
        "schema_version": "v1", "id": identifier, "title": identifier,
        "source_classification": "internal", "provider": "test",
        "source_location": "fixture", "access_date": "2026-07-29",
        "verification_status": "unverified", "claims": ["fixture"], "record_version": "1",
    }


def _manifest(identifier: str, source_ids: list[str]) -> dict:
    return {
        "schema_version": "v1", "id": identifier, "product_id": "product",
        "source_ids": source_ids, "raw_destination": "data/raw/test",
        "acquisition_method": "fixture", "acquisition_status": "planned",
        "processing_status": "unprocessed", "expected_content_type": "text/plain",
    }


class FixtureParser(EvidenceParser):
    parser_id = "fixture.parser"
    parser_version = "1"
    supported_content_types = ("text/plain",)

    def parse(self, content: bytes, evidence: RawEvidenceArtifact) -> ParseResult:
        return ParseResult(
            parser_id=self.parser_id, parser_version=self.parser_version,
            status=TransformationStatus.SUCCEEDED, records=({"text": content.decode()},),
        )


class FailingParser(FixtureParser):
    def parse(self, content: bytes, evidence: RawEvidenceArtifact) -> ParseResult:
        raise RuntimeError("fixture parser failure")


class IngestionTests(unittest.TestCase):
    def request(self, **overrides: str) -> AcquisitionRequest:
        values = {
            "game": "magic", "product_id": "product", "source_id": "source",
            "acquisition_target_id": "manifest", "content_type": "text/plain",
            "acquired_at": "2026-07-29T00:00:00Z", "original_filename": "source.txt",
        }
        values.update(overrides)
        return AcquisitionRequest(**values)

    def fixture_root(self, directory: str) -> Path:
        root = Path(directory) / "games"
        sources = root / "magic" / "products" / "product" / "sources"
        sources.mkdir(parents=True)
        (sources / "source.json").write_text(json.dumps(_source("source")), encoding="utf-8")
        (sources / "other.json").write_text(json.dumps(_source("other")), encoding="utf-8")
        (sources / "manifest.manifest.json").write_text(
            json.dumps(_manifest("manifest", ["source"])), encoding="utf-8"
        )
        return root

    def test_hashing_is_deterministic_and_file_matches_bytes(self) -> None:
        content = b"immutable evidence"
        self.assertEqual(hash_bytes(content), hash_bytes(content))
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "evidence.bin"
            path.write_bytes(content)
            self.assertEqual(hash_file(path), hash_bytes(content))

    def test_missing_file_hashing_fails(self) -> None:
        with self.assertRaises(HashingError):
            hash_file(Path("missing-evidence.bin"))

    def test_storage_is_safe_idempotent_and_preserves_bytes(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            storage = FileSystemEvidenceStorage(Path(directory) / "raw")
            artifact = storage.store_bytes(self.request(), b"preserve me")
            repeated = storage.store_bytes(self.request(), b"preserve me")
            self.assertEqual(artifact.storage_path, repeated.storage_path)
            self.assertEqual(artifact.storage_path.read_bytes(), b"preserve me")
            self.assertEqual(artifact.original_filename, "source.txt")

    def test_storage_rejects_conflicting_existing_content(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            storage = FileSystemEvidenceStorage(Path(directory) / "raw")
            artifact = storage.store_bytes(self.request(), b"original")
            artifact.storage_path.write_bytes(b"corrupted")
            with self.assertRaises(ConflictingStoredContent):
                storage.store_bytes(self.request(), b"original")

    def test_storage_rejects_path_traversal(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(InvalidEvidencePath):
                FileSystemEvidenceStorage(Path(directory) / "raw").store_bytes(
                    self.request(product_id="../outside"), b"content"
                )

    def test_pipeline_ingests_synthetic_evidence_without_canonical_writes(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = self.fixture_root(directory)
            raw_root = Path(directory) / "raw"
            result = IngestionPipeline(
                FileSystemEvidenceStorage(raw_root), [FixtureParser()], games_root=root
            ).ingest(self.request(), b"synthetic evidence")
            self.assertEqual(result.parse_result.status, TransformationStatus.SUCCEEDED)
            self.assertTrue(result.evidence.storage_path.is_file())
            self.assertFalse(any(raw_root.rglob("product.json")))

    def test_parser_mismatch_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            pipeline = IngestionPipeline(
                FileSystemEvidenceStorage(Path(directory) / "raw"), [FixtureParser()],
                games_root=self.fixture_root(directory),
            )
            with self.assertRaises(ParserMismatch):
                pipeline.ingest(self.request(), b"content", parser=type("Wrong", (FixtureParser,), {
                    "supported_content_types": ("application/json",)
                })())

    def test_content_type_mismatch_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            pipeline = IngestionPipeline(
                FileSystemEvidenceStorage(Path(directory) / "raw"), [FixtureParser()],
                games_root=self.fixture_root(directory),
            )
            with self.assertRaises(UnsupportedContentType):
                pipeline.ingest(self.request(content_type="application/json"), b"content")

    def test_parser_failure_retains_raw_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            pipeline = IngestionPipeline(
                FileSystemEvidenceStorage(Path(directory) / "raw"), [FailingParser()],
                games_root=self.fixture_root(directory),
            )
            result = pipeline.ingest(self.request(), b"retained")
            self.assertEqual(result.parse_result.status, TransformationStatus.FAILED)
            self.assertTrue(result.evidence.storage_path.is_file())
            self.assertEqual(result.evidence.storage_path.read_bytes(), b"retained")

    def test_unknown_source_target_and_cross_reference_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = self.fixture_root(directory)
            pipeline = IngestionPipeline(
                FileSystemEvidenceStorage(Path(directory) / "raw"), [FixtureParser()], games_root=root
            )
            with self.assertRaises(UnknownSourceReference):
                pipeline.ingest(self.request(source_id="missing"), b"content")
            with self.assertRaises(UnknownAcquisitionTarget):
                pipeline.ingest(self.request(acquisition_target_id="missing"), b"content")
            with self.assertRaises(SourceTargetMismatch):
                pipeline.ingest(self.request(source_id="other"), b"content")


if __name__ == "__main__":
    unittest.main()
