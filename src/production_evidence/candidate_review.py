"""Deterministic, signature-free review of one retained production candidate batch."""
from __future__ import annotations

import hashlib
import json
from collections import Counter
from pathlib import Path

from .repository import EvidenceError, ProductionEvidenceRepository

RUN_ID = "30663562841"
EVIDENCE_ID = f"{RUN_ID}-review-payload-v2"
BATCH_ID = "mb2-batch-000001-e32022126c07"
CLASSIFICATIONS = {"approved", "excluded", "requires_additional_evidence"}


def _canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def _sha(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def review_first_mb2_batch(data_root: Path | str) -> dict:
    """Review every candidate in the first retained MB2 batch without signing/promoting."""
    data_root = Path(data_root)
    root = data_root / "production_runs" / EVIDENCE_ID
    verification = ProductionEvidenceRepository(data_root).verify(EVIDENCE_ID)
    if not verification["valid"]:
        raise EvidenceError("retained evidence revision v2 did not verify")
    index = json.loads((root / "batch_index.json").read_text())
    selected = [b for b in index["batches"] if b["batch_id"] == BATCH_ID]
    if len(selected) != 1 or selected[0]["target_product"] != "MB2":
        raise EvidenceError("exact first MB2 batch is not uniquely retained")
    batch = selected[0]
    payload_bytes = (root / batch["payload_path"]).read_bytes()
    if _sha(payload_bytes) != batch["payload_sha256"]:
        raise EvidenceError("selected retained payload digest mismatch")
    payload = json.loads(payload_bytes)
    candidates = payload["candidate_payloads"]
    if len(candidates) != 1000 or payload["candidate_ids"] != [c["candidate_identifier"] for c in candidates]:
        raise EvidenceError("review must cover exactly all 1,000 selected candidates")

    bundle = json.loads((root / batch["bundle_path"]).read_text())
    dependency = json.loads((root / "dependency_reports/mb2" / f"{BATCH_ID}.json").read_text())
    if not dependency["valid"] or dependency["candidate_ids"] != payload["candidate_ids"]:
        raise EvidenceError("selected batch dependency closure is invalid")

    cards = {c["mapped_fields"]["card_reference"] for c in candidates if c["entity_type"] == "card"}
    printings = {c["mapped_fields"]["uuid"] for c in candidates if c["entity_type"] == "printing"}
    finishes = {c["mapped_fields"]["value"] for c in candidates if c["entity_type"] == "finish"}
    collisions = {(f["identifier_namespace"], str(f["identifier_value"])): f for f in bundle["findings"]}
    ledger = []
    for ordinal, candidate in enumerate(candidates):
        problems = []
        fields = candidate.get("mapped_fields", {})
        entity = candidate.get("entity_type")
        if candidate.get("validation_state") != "validated": problems.append("not_validated")
        if candidate.get("review_status") != "pending": problems.append("unexpected_lifecycle")
        if candidate.get("confidence") != 1.0: problems.append("insufficient_confidence")
        if not isinstance(candidate.get("unknown_fields"), dict): problems.append("unknowns_not_explicit")
        if candidate.get("provenance", {}).get("provider") != "mtgjson" or candidate.get("source_dataset") != payload["source_lineage"]["dataset_identifier"]:
            problems.append("provenance_mismatch")
        if entity == "card":
            if not all(fields.get(k) for k in ("card_reference", "name", "normalized_name", "layout")):
                problems.append("incomplete_card_identity")
        elif entity == "printing":
            if fields.get("set_code") != "mb2": problems.append("wrong_set")
            if fields.get("card_reference") not in cards: problems.append("missing_card_relationship")
            if not fields.get("collector_number"): problems.append("missing_collector_number")
            if not fields.get("identifiers"): problems.append("missing_identifiers")
            if not fields.get("rarity"): problems.append("missing_rarity")
            if fields.get("language") != "English": problems.append("unsupported_language")
            if not fields.get("finishes") or not set(fields["finishes"]) <= finishes: problems.append("missing_finish_relationship")
        elif entity == "identifier":
            if fields.get("printing_uuid") not in printings: problems.append("missing_printing_relationship")
            if not fields.get("namespace") or not fields.get("value"): problems.append("incomplete_identifier")
            if (fields.get("namespace"), str(fields.get("value"))) in collisions:
                problems.append("non_unique_external_identifier")
        elif entity == "finish":
            if fields.get("value") not in {"foil", "nonfoil"}: problems.append("unsupported_finish")
        else:
            problems.append("unsupported_entity_type")
        classification = "approved" if not problems else "requires_additional_evidence"
        ledger.append({"ordinal": ordinal, "candidate_id": candidate["candidate_identifier"],
                       "entity_type": entity, "classification": classification,
                       "reasons": problems, "candidate_hash": candidate["candidate_hash"]})

    counts = Counter(item["classification"] for item in ledger)
    type_counts = Counter(item["entity_type"] for item in ledger)
    ledger_digest = _sha(_canonical(ledger))
    findings = [{"namespace": ns, "value": value, "collision_count": finding["collision_count"]}
                for (ns, value), finding in sorted(collisions.items())]
    return {
        "schema_version": "phase-115-candidate-review-v1", "evidence_identity": EVIDENCE_ID,
        "source_workflow_run": RUN_ID, "batch_id": BATCH_ID, "target_set_code": "MB2",
        "source_payload": {"path": batch["payload_path"], "sha256": batch["payload_sha256"], "size": batch["payload_size"]},
        "review_scope": {"candidate_count": len(ledger), "other_mb2_batches_reviewed": 0, "marvel_candidates_reviewed": 0},
        "statistics": {"classifications": {name: counts[name] for name in sorted(CLASSIFICATIONS)}, "entity_types": dict(sorted(type_counts.items()))},
        "ledger": ledger, "ledger_sha256": ledger_digest,
        "findings": {"identifier_collisions_considered": len(findings), "details": findings},
        "dependency_closure": {"valid": True, "digest": dependency["dependency_closure_digest"], "rule": dependency["rule"]},
        "pending_decision": {"status": "awaiting_operator_signature", "immutable": True,
                             "ledger_sha256": ledger_digest, "operator_signature": None,
                             "promotion_authorized": False, "canonical_write": False},
        "promotion_readiness": {"ready": False, "approved_candidates": counts["approved"],
                                "blockers": ["operator_signature_missing"] + (["candidates_require_additional_evidence"] if counts["requires_additional_evidence"] else []),
                                "promotion_performed": False, "canonical_write": False},
    }


def write_review_artifacts(data_root: Path | str, output: Path | str) -> dict:
    result = review_first_mb2_batch(data_root)
    output = Path(output); output.mkdir(parents=True, exist_ok=True)
    ledger = {k: result[k] for k in ("schema_version", "evidence_identity", "batch_id", "target_set_code", "source_payload", "ledger", "ledger_sha256")}
    reports = {
        "candidate-review-ledger.json": ledger,
        "findings-report.json": {k: result[k] for k in ("schema_version", "evidence_identity", "batch_id", "statistics", "findings")},
        "pending-review-decision.json": {**result["pending_decision"], "schema_version": result["schema_version"], "evidence_identity": EVIDENCE_ID, "batch_id": BATCH_ID},
        "dependency-closure-verification.json": {**result["dependency_closure"], "schema_version": result["schema_version"], "evidence_identity": EVIDENCE_ID, "batch_id": BATCH_ID},
        "promotion-readiness-report.json": {**result["promotion_readiness"], "schema_version": result["schema_version"], "evidence_identity": EVIDENCE_ID, "batch_id": BATCH_ID},
    }
    for name, value in reports.items(): (output / name).write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")
    return result
