"""Typed, evidence-preserving artifacts for the generic ingestion pipeline."""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path
from typing import Any, Mapping


class TransformationStatus(StrEnum):
    PENDING = "pending"
    SUCCEEDED = "succeeded"
    FAILED = "failed"


class ValidationStatus(StrEnum):
    NOT_RUN = "not_run"
    PASSED = "passed"
    FAILED = "failed"


@dataclass(frozen=True, slots=True)
class AcquisitionRequest:
    game: str
    product_id: str
    source_id: str
    acquisition_target_id: str
    content_type: str
    acquired_at: str
    original_filename: str | None = None


@dataclass(frozen=True, slots=True)
class RawEvidenceArtifact:
    id: str
    source_id: str
    acquisition_target_id: str
    product_id: str
    content_type: str
    acquired_at: str
    content_hash: str
    storage_path: Path
    original_filename: str | None = None


@dataclass(frozen=True, slots=True)
class ParseResult:
    parser_id: str
    parser_version: str
    status: TransformationStatus
    records: tuple[Mapping[str, Any], ...] = ()
    errors: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()
    output_location: Path | None = None


@dataclass(frozen=True, slots=True)
class NormalizationResult:
    transformer_id: str
    transformer_version: str
    status: TransformationStatus
    records: tuple[Mapping[str, Any], ...] = ()
    errors: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()
    output_location: Path | None = None


@dataclass(frozen=True, slots=True)
class ArtifactValidationResult:
    validator_id: str
    validator_version: str
    status: ValidationStatus
    errors: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class PipelineResult:
    request: AcquisitionRequest
    evidence: RawEvidenceArtifact
    parse_result: ParseResult
    normalization_result: NormalizationResult | None = None
    validation_result: ArtifactValidationResult | None = None
    errors: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()
