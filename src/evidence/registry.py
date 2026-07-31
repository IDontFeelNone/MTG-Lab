"""Deterministic reference dataset and artifact registry.

Registry writes are non-canonical and deliberately have no promotion operation.
"""
from __future__ import annotations

import json
from pathlib import Path
import re
from typing import Any

from .contracts import EvidenceArtifact, EvidenceDataset, SCHEMA_VERSION, deterministic_json


class RegistryValidationError(ValueError):
    pass


class ReferenceDatasetRegistry:
    def __init__(self, root: Path | str) -> None:
        self.root = Path(root)
        self.datasets_path = self.root / "datasets"
        self.artifacts_path = self.root / "artifacts"

    @staticmethod
    def _validate_license(record: EvidenceDataset | EvidenceArtifact) -> None:
        if not record.licensing.is_supported():
            raise RegistryValidationError("unknown or unsupported licensing state")

    @staticmethod
    def _validate_identifier(identifier: str, label: str) -> None:
        if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]*", identifier):
            raise RegistryValidationError(f"invalid {label} identifier")

    def register_dataset(self, dataset: EvidenceDataset) -> dict[str, Any]:
        self._validate_license(dataset)
        if not dataset.dataset_identifier or not dataset.provider_identifier or not dataset.dataset_version:
            raise RegistryValidationError("dataset identity fields are required")
        self._validate_identifier(dataset.dataset_identifier, "dataset")
        path = self.datasets_path / f"{dataset.dataset_identifier}.json"
        return self._write_once(path, dataset.to_dict(), "dataset")

    def register_artifact(self, artifact: EvidenceArtifact) -> dict[str, Any]:
        self._validate_license(artifact)
        self._validate_identifier(artifact.artifact_identifier, "artifact")
        if len(artifact.sha256) != 64 or any(c not in "0123456789abcdef" for c in artifact.sha256):
            raise RegistryValidationError("artifact SHA-256 must be 64 lowercase hexadecimal characters")
        path = self.artifacts_path / f"{artifact.artifact_identifier}.json"
        return self._write_once(path, artifact.to_dict(), "artifact")

    @staticmethod
    def _write_once(path: Path, value: dict[str, Any], kind: str) -> dict[str, Any]:
        serialized = deterministic_json(value) + "\n"
        if path.exists():
            if path.read_text(encoding="utf-8") == serialized:
                return value
            raise RegistryValidationError(f"duplicate {kind} identifier with different content: {path.stem}")
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(serialized, encoding="utf-8")
        return value

    def datasets(self) -> list[dict[str, Any]]:
        return self._list(self.datasets_path)

    def artifacts(self) -> list[dict[str, Any]]:
        return self._list(self.artifacts_path)

    @staticmethod
    def _list(path: Path) -> list[dict[str, Any]]:
        if not path.exists():
            return []
        return [json.loads(item.read_text(encoding="utf-8")) for item in sorted(path.glob("*.json"))]

    def validate(self) -> dict[str, Any]:
        errors: list[str] = []
        artifacts = self.artifacts()
        artifact_ids = {item.get("artifact_identifier") for item in artifacts}
        for item in artifacts:
            identifier = item.get("artifact_identifier")
            if item.get("schema_version") != SCHEMA_VERSION:
                errors.append(f"artifact {identifier}: unsupported schema version")
            digest = item.get("sha256", "")
            if len(digest) != 64 or any(c not in "0123456789abcdef" for c in digest):
                errors.append(f"artifact {identifier}: invalid SHA-256")
            licensing = item.get("licensing", {})
            if licensing.get("licensing_assessment", "").lower() in {"", "unknown", "unsupported", "unassessed"}:
                errors.append(f"artifact {identifier}: unsupported licensing state")
        for item in self.datasets():
            if item.get("schema_version") != SCHEMA_VERSION:
                errors.append(f"dataset {item.get('dataset_identifier')}: unsupported schema version")
            for artifact_id in item.get("artifact_identifiers", []):
                if artifact_id not in artifact_ids:
                    errors.append(f"dataset {item.get('dataset_identifier')}: missing artifact {artifact_id}")
            licensing = item.get("licensing", {})
            if licensing.get("licensing_assessment", "").lower() in {"", "unknown", "unsupported", "unassessed"}:
                errors.append(f"dataset {item.get('dataset_identifier')}: unsupported licensing state")
        return {"schema_version": SCHEMA_VERSION, "valid": not errors,
                "dataset_count": len(self.datasets()), "artifact_count": len(artifacts),
                "errors": sorted(errors)}
