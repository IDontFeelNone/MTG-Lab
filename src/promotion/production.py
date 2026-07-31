"""Production-scale, deterministic MTGJSON review-batch orchestration."""
from __future__ import annotations

import hashlib
import json
import resource
import time
from pathlib import Path
from typing import Any, Mapping

from acquisition import (CanonicalPromotionEngine, PromotionDecision, ProviderPolicy,
                         ProviderTrustPolicy, assertions_from_normalized,
                         build_review_package)
from ai import AIModelRequest
from analytics import CanonicalAnalyticsEngine
from evidence.contracts import deterministic_json
from projection import TypedCanonicalProjectionEngine
from providers.mtgjson import MTGJSONImportExecution
from providers.mtgjson.streaming import StreamingMTGJSONPlanner
from query import CanonicalQueryEngine
from reasoning import ReasoningContextBuilder, ReasoningContextRequest
from semantic import CanonicalSemanticQueryEngine, SemanticRequest

SCHEMA = "production-mtgjson-ingestion-v1"
PROVIDER = "mtgjson-production"
TIMESTAMP = "2026-07-31T00:00:00+00:00"
POLICY = ProviderPolicy(PROVIDER, "verified_community", .9, ("CC-BY-4.0",),
                        "MTGJSON AllPrintings; independently reviewed",
                        ("card", "printing"))
LANGUAGES = {"English": "en", "Japanese": "ja", "German": "de", "French": "fr",
             "Italian": "it", "Spanish": "es", "Portuguese": "pt", "Russian": "ru",
             "Korean": "ko", "Chinese Simplified": "zh-CN", "Chinese Traditional": "zh-TW"}


def _digest(value: Any) -> str:
    return hashlib.sha256(deterministic_json(value).encode()).hexdigest()


def _id(kind: str, source: str) -> str:
    return f"{kind}-{hashlib.sha256(source.encode()).hexdigest()}"


class ProductionMTGJSONIngestion:
    """Compose existing import, review, promotion, projection, and read layers."""

    def __init__(self, data_root: Path | str, *, batch_size: int = 1000) -> None:
        if batch_size <= 0:
            raise ValueError("batch_size must be positive")
        self.root, self.batch_size = Path(data_root), batch_size
        self.engine = CanonicalPromotionEngine(self.root / "canonical", self.root / "audit")
        self.review_root = self.root / "evidence" / "mtgjson" / "production-batches"

    def prepare(self, source: Path | str) -> dict[str, Any]:
        started = time.perf_counter()
        imported = MTGJSONImportExecution(self.root).import_dataset(source)
        manifest_path = self.review_root / imported["dataset_identifier"] / "manifest.json"
        if manifest_path.exists():
            return json.loads(manifest_path.read_text())
        candidates_doc = MTGJSONImportExecution(self.root).candidates(
            imported["dataset_identifier"])["imports"][0]
        candidates = candidates_doc["candidates"]
        cards = {item["mapped_fields"]["card_reference"]: _id("card", item["candidate_identifier"])
                 for item in candidates if item["entity_type"] == "card"}
        eligible, unresolved, rejected = [], [], []
        for item in candidates:
            kind, values = item["entity_type"], item["mapped_fields"]
            if kind == "card":
                mapped = {"name": values["name"], "normalized_name": values["normalized_name"],
                          "layout": values["layout"], "colors": values["colors"]}
            elif kind == "printing":
                card_id = cards.get(str(values["card_reference"]).casefold())
                mapped = {"card_id": card_id, "set_id": values["set_code"],
                          "collector_number": values["collector_number"],
                          "language": LANGUAGES.get(values["language"], str(values["language"]).casefold()),
                          "rarity_id": values["rarity"],
                          "finishes": values["finishes"]}
            else:
                rejected.append(item); continue
            if kind == "printing" and card_id is None:
                unresolved.append(item); continue
            if any(isinstance(value, Mapping) and value.get("status") == "unknown"
                   for value in mapped.values()):
                unresolved.append(item); continue
            eligible.append({"source": item, "id": _id(kind, item["candidate_identifier"]),
                             "entity_type": kind, "values": mapped})
        eligible.sort(key=lambda row: row["id"])
        card_rows = {row["id"]: row for row in eligible if row["entity_type"] == "card"}
        groups = {identifier: [row] for identifier, row in card_rows.items()}
        for row in eligible:
            if row["entity_type"] == "printing":
                groups.setdefault(row["values"]["card_id"], []).append(row)
        batches: list[list[Mapping[str, Any]]] = []
        current: list[Mapping[str, Any]] = []
        for identifier in sorted(groups):
            group = sorted(groups[identifier], key=lambda row: row["id"])
            if current and len(current) + len(group) > self.batch_size:
                batches.append(current); current = []
            current.extend(group)
        if current: batches.append(current)
        batch_reports = [self._write_batch(imported, index + 1, rows)
                         for index, rows in enumerate(batches)]
        elapsed = max(time.perf_counter() - started, 1e-9)
        report = {"schema_version": SCHEMA, "status": "awaiting_independent_review",
                  "dataset_identifier": imported["dataset_identifier"],
                  "artifact_sha256": imported["artifact_sha256"],
                  "batch_size": self.batch_size, "batch_count": len(batch_reports),
                  "entity_counts": imported["entity_counts"],
                  "identifier_findings": imported["validation"]["identifier_findings"],
                  "identifier_finding_count": len(imported["validation"]["identifier_findings"]),
                  "identifier_finding_counts": self._finding_counts(
                      imported["validation"]["identifier_findings"]),
                  "candidate_count": len(candidates), "duplicate_count": 0,
                  "quarantined_source_record_count": imported["quarantined_source_record_count"],
                  "quarantined_candidate_count": imported["quarantined_candidate_count"],
                  "quarantined_mtgjson_uuids": imported["quarantined_mtgjson_uuids"],
                  "rejected_count": len(rejected), "unresolved_count": len(unresolved),
                  "eligible_count": len(eligible), "promoted_count": 0, "projection_count": 0,
                  "batches": batch_reports,
                  "performance": {"import_seconds": elapsed,
                     "candidates_per_second": round(len(candidates) / elapsed, 2),
                     "peak_memory_mib": round(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024, 2)}}
        self._write(manifest_path, report)
        return report

    def prepare_streaming(self, source: Path | str, *, expected_sha256: str | None = None,
                          targets: tuple[str, ...] = ()) -> dict[str, Any]:
        """Plan without decoding or retaining the complete corpus.

        This is the production dry-run path.  The legacy ``prepare`` entry point remains
        available for compatibility with already reviewed bounded promotion packages.
        """
        return StreamingMTGJSONPlanner(self.root, batch_size=self.batch_size,
                                       targets=targets).plan(source, expected_sha256)

    def _write_batch(self, imported: Mapping[str, Any], number: int,
                     rows: list[Mapping[str, Any]]) -> dict[str, Any]:
        batch_id = f"batch-{number:06d}-{_digest([row['id'] for row in rows])[:12]}"
        snapshot = {"schema_version": "raw-snapshot-v1", "snapshot_id": imported["artifact_sha256"],
                    "provider_id": PROVIDER, "dataset": "allprintings", "publication_timestamp": None,
                    "checksum": {"algorithm": "sha256", "value": imported["artifact_sha256"]}}
        normalized = {"schema_version": "normalized-source-record-v1", "provider_id": PROVIDER,
                      "dataset": "allprintings", "raw_snapshot_id": imported["artifact_sha256"],
                      "records": [{"schema_version": "normalized-source-record-v1", "id": row["id"],
                         "provider_id": PROVIDER, "source_record_id": row["id"],
                         "raw_snapshot_id": imported["artifact_sha256"], "raw_snapshot_path": "registered-artifact",
                         "source_values": row["values"], "canonical_values": {},
                         "unmapped_source_fields": {"entity_type": row["entity_type"]},
                         "validation_errors": []} for row in rows]}
        assertions = assertions_from_normalized(normalized,
            ProviderTrustPolicy("verified_community", .9, "confirmed"), TIMESTAMP)
        run = {"schema_version": "acquisition-run-v1", "run_id": batch_id,
               "provider_id": PROVIDER, "requested_datasets": ["allprintings"],
               "started_at": TIMESTAMP, "completed_at": TIMESTAMP, "status": "succeeded",
               "discovered_records": len(rows), "downloaded_snapshots": [],
               "unchanged_snapshots": [], "failures": [], "normalization_counts": {},
               "assertion_counts": {},
               "warnings": ["external identifier collisions require independent review"]
                           if imported["validation"]["identifier_findings"] else [],
               "identifier_findings": imported["validation"]["identifier_findings"],
               "report_location": "registered-artifact",
               "resumable": True}
        package = build_review_package(run, [snapshot], [normalized], assertions, POLICY,
                                       imported["dataset_identifier"])
        path = self.review_root / imported["dataset_identifier"] / batch_id / "review-package.json"
        self._write(path, package)
        counts = {kind: sum(row["entity_type"] == kind for row in rows) for kind in ("card", "printing")}
        return {"batch_id": batch_id, "entity_count": len(rows), "entity_counts": counts,
                "candidate_count": len(assertions), "duplicate_count": 0, "rejected_count": 0,
                "unresolved_count": 0, "promoted_count": 0, "projection_count": 0,
                "review_status": "pending", "review_package": str(path)}

    def promote(self, dataset_identifier: str, batch_id: str, *, actor: str,
                timestamp: str = TIMESTAMP) -> dict[str, Any]:
        package_path = self.review_root / dataset_identifier / batch_id / "review-package.json"
        package = json.loads(package_path.read_text())
        started = time.perf_counter()
        audit = self.engine.promote(package, POLICY, PromotionDecision(
            actor, timestamp, reason=f"independent approval of {batch_id}"))
        projection_started = time.perf_counter()
        projection = TypedCanonicalProjectionEngine(self.root / "canonical",
            self.root / "canonical/games", self.root / "projection-audit").project(timestamp)
        projection_seconds = max(time.perf_counter() - projection_started, 1e-9)
        projection_count = len(projection["projected_entity_ids"])
        return {"schema_version": SCHEMA, "batch_id": batch_id,
                "promotion_id": audit["promotion_id"],
                "promoted_count": len(audit["promoted_entities"]),
                "projection_id": projection["projection_id"],
                "projection_count": projection_count,
                "performance": {"promotion_seconds": time.perf_counter() - started,
                    "projection_seconds": projection_seconds,
                    "projections_per_second": round(projection_count / projection_seconds, 2)}}

    def rollback(self, promotion_id: str, *, actor: str, timestamp: str) -> dict[str, Any]:
        return self.engine.rollback(promotion_id, PromotionDecision(actor, timestamp,
                                    reason="operator-requested production batch rollback"))

    def verify_downstream(self) -> dict[str, Any]:
        started = time.perf_counter(); replay = self.engine.replay()
        replay_seconds = time.perf_counter() - started
        query = CanonicalQueryEngine(games_root=self.root / "canonical/games", data_root=self.root)
        analytics = CanonicalAnalyticsEngine(query); summary = analytics.summary()
        semantic = CanonicalSemanticQueryEngine(query, analytics)
        cards = query.entities(entity_type="card")
        result = semantic.execute(SemanticRequest("find_identifier",
            {"identifier": cards[0].canonical_identity}))
        context = ReasoningContextBuilder(semantic).build(ReasoningContextRequest(
            SemanticRequest("list_type", {"entity_type": "card"}), include_analytics=True))
        request = AIModelRequest("not-invoked", "1.0.0", "not-invoked", context.context_id,
                                 "phase-106-no-provider", TIMESTAMP,
                                 required_capabilities=("structured-response",))
        checks = {"replay": replay == json.loads((self.root / "canonical/state.json").read_text()),
                  "query": bool(cards), "analytics": summary.data["entity_counts_by_type"]["card"] > 0,
                  "semantic": bool(result.to_dict()["result"]), "reasoning": bool(context.context_id),
                  "ai_request_without_provider": request.provider_identifier == "not-invoked"}
        return {"schema_version": SCHEMA, "valid": all(checks.values()), "checks": checks,
                "replay_seconds": replay_seconds, "ai_model_request": request.to_dict()}

    @staticmethod
    def _finding_counts(findings: list[Mapping[str, Any]] | tuple[Mapping[str, Any], ...]) -> dict[str, Any]:
        namespaces = sorted({str(item["identifier_namespace"]) for item in findings})
        return {"total": len(findings),
                "affected_record_count": sum(len(item["affected_source_records"])
                                             for item in findings),
                "by_namespace": {namespace: sum(item["identifier_namespace"] == namespace
                                                 for item in findings)
                                 for namespace in namespaces},
                "by_disposition": {disposition: sum(item["disposition"] == disposition
                    for item in findings) for disposition in sorted(
                        {str(item["disposition"]) for item in findings})},
                "by_severity": {severity: sum(item["severity"] == severity for item in findings)
                                for severity in ("error", "warning", "review-required")}}

    @staticmethod
    def _write(path: Path, value: Mapping[str, Any]) -> None:
        content = deterministic_json(value) + "\n"; path.parent.mkdir(parents=True, exist_ok=True)
        if path.exists() and path.read_text() != content:
            raise ValueError(f"immutable production ingestion artifact differs: {path}")
        path.write_text(content)
