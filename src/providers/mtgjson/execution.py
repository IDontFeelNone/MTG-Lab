"""Local MTGJSON import execution ending at the human review queue."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
from typing import Any, Mapping

from evidence import (AcquisitionMetadata, EvidenceArtifact, EvidenceDataset,
                      ReferenceDatasetRegistry, ReviewMetadata)
from evidence.contracts import deterministic_json

from .mapper import map_dataset
from .parser import parse_dataset
from .provider import ENTITY_TYPES, LICENSE, MTGJSONProvider, PROVIDER_IDENTIFIER
from .validator import identifier_findings


def _write_repeatable(path: Path, value: Any) -> None:
    serialized = deterministic_json(value) + "\n"
    if path.exists() and path.read_text(encoding="utf-8") != serialized:
        raise ValueError(f"existing import state conflicts with this dataset: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(serialized, encoding="utf-8")


class MTGJSONImportExecution:
    """Validate, register, map, and queue one caller-supplied AllPrintings artifact."""

    def __init__(self, data_root: Path | str) -> None:
        self.root = Path(data_root) / "evidence" / "mtgjson"
        self.registry = ReferenceDatasetRegistry(Path(data_root) / "evidence" / "registry")

    def import_dataset(self, source: Path | str | None) -> dict[str, Any]:
        if source is None:
            raise ValueError("local MTGJSON AllPrintings JSON artifact is required; supply its path as SOURCE")
        path = Path(source)
        if not path.is_file():
            raise ValueError(f"local MTGJSON AllPrintings JSON artifact is required; file not found: {path}")

        # All fail-closed document and mapping validation happens before repository state changes.
        payload = path.read_bytes()
        document = parse_dataset(payload)
        findings = identifier_findings(document)
        mapped = map_dataset(document)
        if not document["data"] or not mapped:
            raise ValueError("MTGJSON AllPrintings dataset is incomplete: at least one set and candidate are required")
        digest = hashlib.sha256(payload).hexdigest()
        version = document["meta"]["version"]
        stamp = document["meta"]["date"]
        safe_version = re.sub(r"[^A-Za-z0-9._-]", "-", version)
        dataset_id = f"mtgjson-allprintings-{safe_version}-{digest[:12]}"
        artifact_id = f"mtgjson-allprintings-{digest}"
        acquisition = AcquisitionMetadata(stamp, stamp, "local-supplied-file", f"sha256:{digest}")
        artifact = EvidenceArtifact(PROVIDER_IDENTIFIER, dataset_id, artifact_id, digest,
                                    "application/json", len(payload), acquisition, LICENSE)
        dataset = EvidenceDataset(PROVIDER_IDENTIFIER, dataset_id, version, stamp, LICENSE,
                                  (("artifact_sha256", digest), ("dataset", "AllPrintings")),
                                  ENTITY_TYPES, (artifact_id,), ReviewMetadata())
        provider = MTGJSONProvider(self.registry)
        artifact_errors = provider.validate_artifact(artifact)
        dataset_errors = provider.validate_dataset(dataset)
        if artifact_errors or dataset_errors:
            raise ValueError("; ".join(artifact_errors + dataset_errors))

        candidates = tuple(self._candidate(record, dataset_id, artifact_id, acquisition)
                           for record in mapped)
        self._validate_candidates(candidates)
        provider.register_artifact(artifact)
        provider.register_dataset(dataset)
        import_root = self.root / "imports" / dataset_id
        _write_repeatable(import_root / "candidates.json", {"schema_version": "1.0.0",
                          "dataset_identifier": dataset_id, "candidates": candidates})
        _write_repeatable(import_root / "review_queue.json", {"schema_version": "1.0.0",
                          "dataset_identifier": dataset_id, "review_status": "pending",
                          "identifier_findings": findings, "candidates": candidates})
        counts = {kind: sum(item["entity_type"] == kind for item in candidates)
                  for kind in ENTITY_TYPES}
        return {"schema_version": "1.0.0", "status": "awaiting_human_review",
                "provider": PROVIDER_IDENTIFIER, "dataset_identifier": dataset_id,
                "artifact_identifier": artifact_id, "artifact_sha256": digest,
                "candidate_sha256": hashlib.sha256(deterministic_json(candidates).encode()).hexdigest(),
                "candidate_count": len(candidates), "entity_counts": counts,
                "validation": {"valid": True, "errors": [], "identifier_findings": findings,
                    "review_required": bool(findings)},
                "review_queue": {"status": "pending", "count": len(candidates),
                                 "approved_count": 0},
                "canonical_write": False, "promotion_performed": False}

    @staticmethod
    def _candidate(record: Mapping[str, Any], dataset_id: str, artifact_id: str,
                   acquisition: AcquisitionMetadata) -> dict[str, Any]:
        value = {**record, "provenance": {"provider": PROVIDER_IDENTIFIER,
                 "artifact_identifier": artifact_id}, "source_dataset": dataset_id,
                 "validation_state": "validated", "review_status": "pending",
                 "confidence": 1.0, "acquisition_metadata": acquisition.to_dict()}
        value["candidate_hash"] = hashlib.sha256(deterministic_json(value).encode()).hexdigest()
        return value

    @staticmethod
    def _validate_candidates(candidates: tuple[dict[str, Any], ...]) -> None:
        identifiers = [item["candidate_identifier"] for item in candidates]
        if len(identifiers) != len(set(identifiers)):
            raise ValueError("candidate consistency failure: duplicate deterministic identifier")
        for item in candidates:
            supplied = item["candidate_hash"]
            body = {key: value for key, value in item.items() if key != "candidate_hash"}
            if supplied != hashlib.sha256(deterministic_json(body).encode()).hexdigest():
                raise ValueError("candidate consistency failure: invalid candidate hash")

    def candidates(self, dataset_identifier: str | None = None) -> dict[str, Any]:
        return self._read("candidates.json", dataset_identifier)

    def review(self, dataset_identifier: str | None = None) -> dict[str, Any]:
        return self._read("review_queue.json", dataset_identifier)

    def _read(self, filename: str, dataset_identifier: str | None) -> dict[str, Any]:
        imports = self.root / "imports"
        paths = ([imports / dataset_identifier / filename] if dataset_identifier else
                 sorted(imports.glob(f"*/{filename}")) if imports.exists() else [])
        records = []
        for path in paths:
            if path.is_file():
                records.append(json.loads(path.read_text(encoding="utf-8")))
        return {"schema_version": "1.0.0", "imports": records,
                "canonical_write": False, "promotion_performed": False}
