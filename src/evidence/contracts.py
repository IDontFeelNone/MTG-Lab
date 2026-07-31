"""Immutable contracts for evidence acquired outside the canonical repository."""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
import hashlib
import json
from typing import Any, Mapping, Tuple

SCHEMA_VERSION = "1.0.0"


def deterministic_json(value: Any) -> str:
    """Return the framework's canonical JSON representation."""
    if hasattr(value, "to_dict"):
        value = value.to_dict()
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def sha256_identity(value: bytes | str | Mapping[str, Any]) -> str:
    if isinstance(value, Mapping):
        value = deterministic_json(value)
    if isinstance(value, str):
        value = value.encode("utf-8")
    return hashlib.sha256(value).hexdigest()


class Contract:
    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def serialize(self) -> str:
        return deterministic_json(self.to_dict())

    @property
    def identity_sha256(self) -> str:
        """Content identity for a complete serialized contract."""
        return sha256_identity(self.serialize())


@dataclass(frozen=True)
class LicensingMetadata(Contract):
    attribution_requirements: str
    redistribution_policy: str
    licensing_assessment: str
    assessed_by: str
    assessed_at: str

    def is_supported(self) -> bool:
        forbidden = {"", "unknown", "unsupported", "unassessed"}
        return (self.licensing_assessment.strip().lower() not in forbidden
                and self.redistribution_policy.strip().lower() not in forbidden
                and bool(self.assessed_by.strip()) and bool(self.assessed_at.strip()))


@dataclass(frozen=True)
class ReviewMetadata(Contract):
    status: str = "pending"
    reviewer: str = ""
    reviewed_at: str = ""
    notes: str = ""


@dataclass(frozen=True)
class AcquisitionMetadata(Contract):
    acquired_at: str
    captured_at: str
    capture_method: str
    source_identity: str


@dataclass(frozen=True)
class EvidenceProvider(Contract):
    provider_identifier: str
    name: str
    category: str
    source_identity: str
    licensing: LicensingMetadata
    schema_version: str = SCHEMA_VERSION


@dataclass(frozen=True)
class EvidenceSource(Contract):
    provider_identifier: str
    source_identifier: str
    source_identity: str
    source_type: str
    licensing: LicensingMetadata
    schema_version: str = SCHEMA_VERSION


@dataclass(frozen=True)
class EvidenceArtifact(Contract):
    provider_identifier: str
    dataset_identifier: str
    artifact_identifier: str
    sha256: str
    media_type: str
    byte_length: int
    acquisition: AcquisitionMetadata
    licensing: LicensingMetadata
    review: ReviewMetadata = field(default_factory=ReviewMetadata)
    schema_version: str = SCHEMA_VERSION


@dataclass(frozen=True)
class EvidenceDataset(Contract):
    provider_identifier: str
    dataset_identifier: str
    dataset_version: str
    acquisition_timestamp: str
    licensing: LicensingMetadata
    source_metadata: Tuple[Tuple[str, str], ...]
    supported_entity_types: Tuple[str, ...]
    artifact_identifiers: Tuple[str, ...]
    review: ReviewMetadata = field(default_factory=ReviewMetadata)
    schema_version: str = SCHEMA_VERSION


@dataclass(frozen=True)
class AcquisitionRequest(Contract):
    provider_identifier: str
    dataset_identifier: str
    requested_artifacts: Tuple[str, ...] = ()
    schema_version: str = SCHEMA_VERSION


@dataclass(frozen=True)
class AcquisitionResult(Contract):
    provider_identifier: str
    dataset_identifier: str
    artifact_identifiers: Tuple[str, ...]
    status: str
    metadata: AcquisitionMetadata
    errors: Tuple[str, ...] = ()
    schema_version: str = SCHEMA_VERSION
