"""MTGJSON implementation of the Phase 98 evidence provider contract."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Tuple

from evidence import (AcquisitionRequest, EvidenceArtifact, EvidenceDataset, EvidenceProvider,
                      EvidenceProviderAdapter, LicensingMetadata, ProviderCapabilities,
                      ReferenceDatasetRegistry)

from .mapper import map_dataset
from .parser import parse_dataset
from .validator import identifier_findings

PROVIDER_IDENTIFIER = "mtgjson"
ENTITY_TYPES = ("card", "finish", "identifier", "language", "printing", "rarity", "set")
LICENSE = LicensingMetadata(
    "Credit MTGJSON and comply with its dataset terms", "local reference use; no redistribution",
    "CC BY 4.0 dataset metadata reviewed for reference ingestion", "MTG Lab provider policy",
    "2026-07-31T00:00:00Z")


def _finding_counts(findings: tuple[dict[str, Any], ...]) -> dict[str, Any]:
    namespaces = sorted({item["identifier_namespace"] for item in findings})
    return {"total": len(findings),
            "affected_record_count": sum(len(item["affected_source_records"]) for item in findings),
            "by_severity": {severity: sum(item["severity"] == severity for item in findings)
                            for severity in ("error", "warning", "review-required")},
            "by_namespace": {namespace: sum(item["identifier_namespace"] == namespace
                                             for item in findings)
                             for namespace in namespaces}}


class MTGJSONProvider(EvidenceProviderAdapter):
    """Network-free provider over a caller-supplied local MTGJSON file."""

    def __init__(self, registry: ReferenceDatasetRegistry | None = None) -> None:
        self.registry = registry

    def metadata(self) -> EvidenceProvider:
        return EvidenceProvider(PROVIDER_IDENTIFIER, "MTGJSON Reference Dataset", "reference_dataset",
                                "https://mtgjson.com/", LICENSE)

    def capabilities(self) -> ProviderCapabilities:
        return ProviderCapabilities()

    def discover(self, source: Path | str) -> dict[str, Any]:
        path = Path(source)
        if not path.is_file():
            raise ValueError("local MTGJSON dataset file is required")
        payload = path.read_bytes()
        document = parse_dataset(payload)
        return {"source": str(path), "dataset_name": path.stem,
                "dataset_version": document["meta"]["version"],
                "generated_at": document["meta"]["date"], "byte_length": len(payload),
                "sha256": hashlib.sha256(payload).hexdigest(), "entity_types": ENTITY_TYPES}

    def inspect(self, source: Path | str) -> dict[str, Any]:
        discovery = self.discover(source)
        records = map_dataset(parse_dataset(source))
        findings = identifier_findings(parse_dataset(source))
        counts = {kind: sum(item["entity_type"] == kind for item in records)
                  for kind in ENTITY_TYPES}
        return {**discovery, "provider": PROVIDER_IDENTIFIER, "record_count": len(records),
                "entity_counts": counts, "identifier_findings": findings,
                "identifier_finding_counts": _finding_counts(findings), "candidate_sha256": hashlib.sha256(
                    json.dumps(records, ensure_ascii=False, separators=(",", ":"),
                               sort_keys=True).encode()).hexdigest()}

    def register_artifact(self, artifact: EvidenceArtifact) -> EvidenceArtifact:
        if self.registry is None:
            raise ValueError("provider has no reference dataset registry")
        errors = self.validate_artifact(artifact)
        if errors:
            raise ValueError("; ".join(errors))
        self.registry.register_artifact(artifact)
        return artifact

    def register_dataset(self, dataset: EvidenceDataset) -> EvidenceDataset:
        if self.registry is None:
            raise ValueError("provider has no reference dataset registry")
        errors = self.validate_dataset(dataset)
        if errors:
            raise ValueError("; ".join(errors))
        self.registry.register_dataset(dataset)
        return dataset

    def plan(self, request: AcquisitionRequest) -> Tuple[str, ...]:
        if request.provider_identifier != PROVIDER_IDENTIFIER:
            raise ValueError("request provider does not match mtgjson")
        requested = request.requested_artifacts or (request.dataset_identifier,)
        return tuple(sorted(requested))

    def plan_local(self, source: Path | str) -> dict[str, Any]:
        discovered = self.discover(source)
        request = AcquisitionRequest(PROVIDER_IDENTIFIER, discovered["dataset_name"],
                                     (Path(source).name,))
        return {"provider": PROVIDER_IDENTIFIER, "networking": False,
                "automatic_download": False, "canonical_write": False,
                "review_required": True, "request": request.to_dict(),
                "artifacts": self.plan(request), "discovery": discovered}

    def validate_local(self, source: Path | str, expected_sha256: str | None = None) -> dict[str, Any]:
        try:
            result = self.inspect(source)
            errors = []
            if expected_sha256 is not None and result["sha256"] != expected_sha256.casefold():
                errors.append("artifact SHA-256 does not match expected hash")
        except (OSError, ValueError) as error:
            result, errors = {}, [str(error)]
        return {"provider": PROVIDER_IDENTIFIER, "valid": not errors,
                "errors": tuple(sorted(errors)), **result}

    def validate_artifact(self, artifact: EvidenceArtifact) -> Tuple[str, ...]:
        errors = []
        if artifact.provider_identifier != PROVIDER_IDENTIFIER:
            errors.append("artifact provider must be mtgjson")
        if artifact.media_type != "application/json":
            errors.append("artifact media type must be application/json")
        if len(artifact.sha256) != 64 or any(c not in "0123456789abcdef" for c in artifact.sha256):
            errors.append("artifact SHA-256 is malformed")
        if not artifact.licensing.is_supported():
            errors.append("artifact licensing metadata is unsupported")
        return tuple(sorted(errors))
    def validate_dataset(self, dataset: EvidenceDataset) -> Tuple[str, ...]:
        errors = []
        if dataset.provider_identifier != PROVIDER_IDENTIFIER:
            errors.append("dataset provider must be mtgjson")
        try:
            compatible_version = int(dataset.dataset_version.split(".", 1)[0]) >= 5
        except (ValueError, IndexError):
            compatible_version = False
        if not compatible_version:
            errors.append("dataset schema version is unsupported")
        if not dataset.artifact_identifiers:
            errors.append("dataset must reference at least one artifact")
        if not dataset.licensing.is_supported():
            errors.append("dataset licensing metadata is unsupported")
        unsupported = set(dataset.supported_entity_types) - set(ENTITY_TYPES)
        if unsupported:
            errors.append("dataset declares unsupported entity types: " + ", ".join(sorted(unsupported)))
        return tuple(sorted(errors))
