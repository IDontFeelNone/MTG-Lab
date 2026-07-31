"""Fail-closed operational delivery for production MTGJSON ingestion."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Mapping

from evidence.contracts import deterministic_json

from .production import ProductionMTGJSONIngestion

SCHEMA = "mtgjson-dataset-delivery-v1"


def _write(path: Path, value: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(deterministic_json(value) + "\n")


class MTGJSONDatasetDelivery:
    """Verify caller-delivered bytes and call the Phase 106 public API."""

    def __init__(self, data_root: Path | str, *, batch_size: int = 1000) -> None:
        self.root = Path(data_root).expanduser().resolve()
        self.ingestion = ProductionMTGJSONIngestion(self.root, batch_size=batch_size)
        self.reports = self.root / "reports" / "mtgjson-delivery"

    def verify(self, source: Path | str, expected_sha256: str) -> dict[str, Any]:
        if not expected_sha256:
            raise ValueError("expected SHA-256 is required")
        expected = expected_sha256.strip().casefold()
        if len(expected) != 64 or any(c not in "0123456789abcdef" for c in expected):
            raise ValueError("expected SHA-256 must be 64 lowercase hexadecimal characters")
        path = Path(source).expanduser()
        if path.is_symlink() or not path.is_file():
            raise ValueError("source must be an existing regular, non-symlink file")
        actual = hashlib.sha256(path.read_bytes()).hexdigest()
        report = {"schema_version": SCHEMA, "valid": actual == expected,
                  "algorithm": "sha256", "expected_sha256": expected,
                  "actual_sha256": actual, "byte_length": path.stat().st_size,
                  "canonical_write": False}
        _write(self.reports / "checksum-verification.json", report)
        if actual != expected:
            raise ValueError(f"SHA-256 mismatch: expected {expected}, received {actual}")
        return report

    def plan(self, source: Path | str, expected_sha256: str,
             selected_batch: str | None = None) -> dict[str, Any]:
        checksum = self.verify(source, expected_sha256)
        manifest = self.ingestion.prepare(Path(source).resolve())
        acquisition = {"schema_version": SCHEMA, "status": "caller_delivered_verified",
                       "artifact_sha256": checksum["actual_sha256"],
                       "byte_length": checksum["byte_length"], "storage": "operator_managed",
                       "license": "CC-BY-4.0", "attribution": "MTGJSON AllPrintings",
                       "canonical_write": False}
        provider = {"schema_version": SCHEMA, "valid": True, "provider": "mtgjson",
                    "dataset_identifier": manifest["dataset_identifier"],
                    "artifact_sha256": manifest["artifact_sha256"],
                    "identifier_findings": manifest["identifier_findings"],
                    "identifier_finding_counts": manifest["identifier_finding_counts"]}
        summary = {key: manifest[key] for key in ("schema_version", "dataset_identifier",
                   "artifact_sha256", "entity_counts", "candidate_count", "eligible_count",
                   "rejected_count", "unresolved_count", "identifier_findings",
                   "identifier_finding_count", "identifier_finding_counts")}
        plan = {"schema_version": SCHEMA, "dataset_identifier": manifest["dataset_identifier"],
                "batch_size": manifest["batch_size"], "batch_count": manifest["batch_count"],
                "batches": manifest["batches"], "digest": hashlib.sha256(
                    deterministic_json(manifest["batches"]).encode()).hexdigest()}
        performance = {"schema_version": SCHEMA, **manifest["performance"]}
        rollback = {"schema_version": SCHEMA, "promotion_id": None,
                    "instruction": "Run rollback with the promotion_id after promotion.",
                    "evidence_retained": True}
        for name, value in (("acquisition", acquisition), ("provider-validation", provider),
                            ("dataset-summary", summary), ("batch-plan", plan),
                            ("validation-log", {"schema_version": SCHEMA, "valid": True,
                             "checks": ["checksum", "json", "provider-schema", "batch-plan"]}),
                            ("performance", performance), ("rollback", rollback)):
            _write(self.reports / f"{name}.json", value)
        if selected_batch:
            selected = [b for b in manifest["batches"] if b["batch_id"] == selected_batch]
            if len(selected) != 1:
                raise ValueError("selected batch must identify exactly one deterministic batch")
            _write(self.reports / "selected-review-batch.json", {
                "schema_version": SCHEMA, "review_status": "pending", "batch": selected[0]})
        return {"schema_version": SCHEMA, "mode": "dry-run", "canonical_write": False,
                "manifest": manifest, "reports": str(self.reports)}

    def promote(self, source: Path | str, expected_sha256: str, batch_id: str,
                *, reviewer: str, review_reference: str) -> dict[str, Any]:
        if not reviewer.strip() or not review_reference.strip():
            raise ValueError("independent reviewer and review reference are required")
        planned = self.plan(source, expected_sha256, batch_id)
        manifest = planned["manifest"]
        selected = [b for b in manifest["batches"] if b["batch_id"] == batch_id]
        if len(selected) != 1:
            raise ValueError("promotion requires exactly one batch from the deterministic plan")
        _write(self.reports / "selected-review-batch.json", {
            "schema_version": SCHEMA, "reviewer": reviewer,
            "review_reference": review_reference, "batch": selected[0]})
        result = self.ingestion.promote(manifest["dataset_identifier"], batch_id, actor=reviewer)
        _write(self.reports / "promotion-result.json", result)
        _write(self.reports / "typed-projection-result.json", {
            "schema_version": SCHEMA, "projection_id": result["projection_id"],
            "projection_count": result["projection_count"]})
        downstream = self.ingestion.verify_downstream()
        _write(self.reports / "downstream-verification.json", downstream)
        _write(self.reports / "rollback.json", {
            "schema_version": SCHEMA, "promotion_id": result["promotion_id"],
            "instruction": "Use the rollback command with this promotion_id and a new actor/timestamp.",
            "evidence_retained": True})
        return {"schema_version": SCHEMA, "mode": "reviewed-promotion", "batch": selected[0],
                "promotion": result, "downstream": downstream, "reports": str(self.reports)}

    def rollback(self, promotion_id: str, *, actor: str, timestamp: str) -> dict[str, Any]:
        if not actor.strip() or not timestamp.strip():
            raise ValueError("rollback actor and timestamp are required")
        result = self.ingestion.rollback(promotion_id, actor=actor, timestamp=timestamp)
        _write(self.reports / "rollback-result.json", result)
        return result
