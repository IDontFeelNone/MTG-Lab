"""Deterministic, auditable orchestration of the existing governance pipeline."""
from __future__ import annotations

import hashlib
import json
import os
from copy import deepcopy
from pathlib import Path
from typing import Any, Mapping

from acquisition import (AcquisitionEngine, CanonicalPromotionEngine, FixtureProvider,
                         PromotionDecision, ProviderPolicy, ProviderTrustPolicy,
                         RawSnapshotStore, assertions_from_normalized,
                         build_review_package, normalize_snapshot)

REGISTRY_SCHEMA = "canonical-dataset-registry-v1"
SESSION_SCHEMA = "canonical-import-session-v1"
REPORT_SCHEMA = "canonical-import-report-v1"


class DatasetImportError(ValueError):
    """A registration, resolution, or import boundary failed safely."""


def _bytes(value: Any) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n").encode()


def _id(prefix: str, value: Any) -> str:
    return prefix + hashlib.sha256(_bytes(value)).hexdigest()


def _write(path: Path, value: Any, *, immutable: bool = False) -> None:
    content = _bytes(value); path.parent.mkdir(parents=True, exist_ok=True)
    if immutable and path.exists() and path.read_bytes() != content:
        raise DatasetImportError(f"immutable artifact differs: {path}")
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    temporary.write_bytes(content); os.replace(temporary, path)


class DatasetRegistry:
    """Versioned first-class dataset identities and append-only import history."""

    def __init__(self, root: Path | str = "data/datasets") -> None:
        self.root = Path(root)

    def register(self, manifest: Mapping[str, Any]) -> dict[str, Any]:
        required = ("logical_dataset_identity", "dataset_version", "provider",
                    "publication_date", "schema_version", "supported_entity_types")
        missing = [key for key in required if not manifest.get(key)]
        if missing: raise DatasetImportError("dataset registration missing: " + ", ".join(missing))
        logical = str(manifest["logical_dataset_identity"])
        version = str(manifest["dataset_version"])
        if not set(manifest["supported_entity_types"]).issubset({"card", "printing"}):
            raise DatasetImportError("unsupported entity type")
        canonical_import_id = _id("dataset-import-", [logical, version, manifest["provider"]])
        path = self.root / logical / f"{version}.json"
        if path.exists():
            existing = json.loads(path.read_text())
            comparable = {k: existing[k] for k in manifest if k in existing}
            if comparable != dict(manifest): raise DatasetImportError("dataset version is already registered differently")
            return existing
        record = {"registry_schema_version": REGISTRY_SCHEMA, **deepcopy(dict(manifest)),
                  "import_status": "registered", "import_history": [],
                  "canonical_import_id": canonical_import_id}
        _write(path, record, immutable=True)
        return record

    def get(self, logical: str, version: str) -> dict[str, Any]:
        path = self.root / logical / f"{version}.json"
        if not path.exists(): raise DatasetImportError("dataset is not registered")
        return json.loads(path.read_text())

    def list(self) -> list[dict[str, Any]]:
        return [json.loads(path.read_text()) for path in sorted(self.root.glob("*/*.json"))]

    def record_session(self, logical: str, version: str, session_id: str, status: str) -> None:
        record = self.get(logical, version)
        entry = {"session_id": session_id, "status": status}
        if entry not in record["import_history"]: record["import_history"].append(entry)
        record["import_history"].sort(key=lambda x: x["session_id"])
        record["import_status"] = "imported" if status == "completed" else status
        _write(self.root / logical / f"{version}.json", record)


class EntityResolver:
    """Resolve identifier aliases with stable priority and explicit failure classes."""

    NAMESPACES = ("canonical_identifier", "provider_identifier", "external_identifiers",
                  "alternate_identifiers")

    def resolve(self, records: list[Mapping[str, Any]]) -> dict[str, Any]:
        claims: dict[tuple[str, str], set[str]] = {}; prepared = []
        for index, source in enumerate(records):
            row = deepcopy(dict(source)); identifiers = row.get("identifiers", {})
            canonical = identifiers.get("canonical_identifier")
            if not canonical:
                provider = identifiers.get("provider_identifier")
                canonical = _id(f"{row.get('entity_type', 'entity')}-", provider) if provider else None
            if canonical:
                for namespace in self.NAMESPACES:
                    values = identifiers.get(namespace, [])
                    if isinstance(values, str): values = [values]
                    for value in values: claims.setdefault((namespace, str(value)), set()).add(str(canonical))
            prepared.append((index, row, canonical))
        collisions = {key: sorted(value) for key, value in claims.items() if len(value) > 1}
        seen: set[str] = set(); resolved = []; rejected = []; unresolved = []
        for index, row, canonical in prepared:
            source_id = str(row.get("id", index))
            if not canonical:
                unresolved.append({"source_id": source_id, "reason": "no_resolvable_identifier"}); continue
            identifiers = row.get("identifiers", {})
            bad = sorted(f"{n}:{v}" for n in self.NAMESPACES
                         for v in ([identifiers.get(n)] if isinstance(identifiers.get(n), str) else identifiers.get(n, []))
                         if (n, str(v)) in collisions)
            if bad:
                rejected.append({"source_id": source_id, "canonical_identifier": canonical,
                                 "reason": "identifier_collision", "collisions": bad}); continue
            if canonical in seen:
                rejected.append({"source_id": source_id, "canonical_identifier": canonical,
                                 "reason": "duplicate_canonical_identifier"}); continue
            if row.get("identity_conflict"):
                rejected.append({"source_id": source_id, "canonical_identifier": canonical,
                                 "reason": "conflicting_identity"}); continue
            seen.add(canonical); row["id"] = canonical
            row["normalized"] = {**row.get("normalized", {}), "canonical_identifier": canonical,
                                 "entity_type": row.get("entity_type", "card")}
            resolved.append(row)
        return {"resolved": sorted(resolved, key=lambda x: x["id"]),
                "rejected": sorted(rejected, key=lambda x: x["source_id"]),
                "unresolved": sorted(unresolved, key=lambda x: x["source_id"]),
                "collisions": [{"namespace": k[0], "identifier": k[1], "canonical_identifiers": v}
                               for k, v in sorted(collisions.items())]}


class ImportManager:
    """Execute acquisition, review, promotion, session storage, and reporting."""

    def __init__(self, root: Path | str = "data", registry: DatasetRegistry | None = None) -> None:
        self.root = Path(root); self.registry = registry or DatasetRegistry(self.root / "datasets")

    def run(self, logical: str, version: str, source: Path | str, *, actor: str,
            timestamp: str, allow_partial: bool = True) -> dict[str, Any]:
        dataset = self.registry.get(logical, version); payload = json.loads(Path(source).read_text())
        if payload.get("review_status") != "reviewed": raise DatasetImportError("dataset must be reviewed")
        resolution = EntityResolver().resolve(payload.get("records", []))
        if not allow_partial and (resolution["rejected"] or resolution["unresolved"]):
            raise DatasetImportError("partial import is not allowed")
        governed = {"records": resolution["resolved"]}
        input_digest = hashlib.sha256(_bytes(payload)).hexdigest()
        session_id = _id("import-session-", [dataset["canonical_import_id"], input_digest, actor, timestamp])
        session_root = self.root / "import-sessions" / session_id
        if (session_root / "report.json").exists():
            return self.report(session_id)
        raw = RawSnapshotStore(self.root / "raw")
        provider = FixtureProvider({logical: _bytes(governed)})
        acquisition = AcquisitionEngine(raw, self.root / "acquisition-runs"); acquisition.register(provider)
        run = acquisition.acquire("fixture", logical, started_at=timestamp, run_id=session_id)
        snapshot_path = Path((run["downloaded_snapshots"] or run["unchanged_snapshots"])[0]["path"])
        snapshot = json.loads((snapshot_path / "manifest.json").read_text())
        normalized = normalize_snapshot(provider, raw, snapshot_path, session_root / "normalized.json")
        policy = ProviderPolicy("fixture", "authoritative_structured", .9, (),
                                str(dataset["provider"]), tuple(dataset["supported_entity_types"]))
        assertions = assertions_from_normalized(normalized,
            ProviderTrustPolicy("authoritative_structured", .9, "verified"), timestamp)
        package = build_review_package(run, [snapshot], [normalized], assertions, policy, version)
        _write(session_root / "review-package.json", package, immutable=True)
        promotion = CanonicalPromotionEngine(self.root / "canonical" / "knowledge",
                                             self.root / "audit" / "knowledge-promotions")
        audit = promotion.promote(package, policy, PromotionDecision(actor, timestamp,
                                  allow_unknowns=True, reason="reviewed canonical dataset import"))
        status = "partial" if resolution["rejected"] or resolution["unresolved"] else "completed"
        imported = sorted(audit["promoted_entities"])
        session = {"schema_version": SESSION_SCHEMA, "session_id": session_id,
                   "dataset": {"logical_dataset_identity": logical, "dataset_version": version,
                               "canonical_import_id": dataset["canonical_import_id"]},
                   "acquisition_run": run["run_id"], "review_package": package["review_package_id"],
                   "promotion_id": audit["promotion_id"], "imported_entities": imported,
                   "rejected_entities": resolution["rejected"], "unresolved_entities": resolution["unresolved"],
                   "validation_results": audit["validation_results"], "completion_status": status,
                   "timing": {"started_at": timestamp, "completed_at": timestamp}, "input_digest": input_digest}
        report = self._report(session, dataset, resolution, audit, len(payload.get("records", [])))
        _write(session_root / "session.json", session, immutable=True); _write(session_root / "report.json", report, immutable=True)
        self.registry.record_session(logical, version, session_id, status)
        return report

    def status(self, session_id: str) -> dict[str, Any]:
        path = self.root / "import-sessions" / session_id / "session.json"
        if not path.exists(): raise DatasetImportError("import session not found")
        return json.loads(path.read_text())

    def report(self, session_id: str) -> dict[str, Any]:
        path = self.root / "import-sessions" / session_id / "report.json"
        if not path.exists(): raise DatasetImportError("import report not found")
        return json.loads(path.read_text())

    @staticmethod
    def _report(session: Mapping[str, Any], dataset: Mapping[str, Any], resolution: Mapping[str, Any],
                audit: Mapping[str, Any], total: int) -> dict[str, Any]:
        imported = len(session["imported_entities"]); rejected = len(session["rejected_entities"])
        unresolved = len(session["unresolved_entities"])
        return {"schema_version": REPORT_SCHEMA, "report_id": _id("import-report-", session),
                "dataset_summary": {k: dataset[k] for k in ("logical_dataset_identity", "dataset_version", "provider", "publication_date", "schema_version", "supported_entity_types", "canonical_import_id")},
                "import_summary": {"session_id": session["session_id"], "status": session["completion_status"], "total_entities": total},
                "imported_entities": session["imported_entities"], "rejected_entities": session["rejected_entities"],
                "unresolved_entities": session["unresolved_entities"], "validation_summary": audit["validation_results"],
                "promotion_summary": {"promotion_id": audit["promotion_id"], "promoted_count": imported,
                                      "canonical_state_digest": audit["canonical_state_digest"]},
                "audit_summary": {"actor": audit["actor"], "timestamp": audit["timestamp"],
                                  "review_package_id": session["review_package"]},
                "completeness_metrics": {"total": total, "imported": imported, "rejected": rejected,
                                         "unresolved": unresolved, "import_ratio": imported / total if total else 0.0},
                "resolution_summary": {"collision_count": len(resolution["collisions"]), "collisions": resolution["collisions"]}}
