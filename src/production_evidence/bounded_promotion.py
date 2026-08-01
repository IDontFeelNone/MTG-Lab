"""Atomic, replayable promotion of the single reviewed Phase 119 MB2 batch."""
from __future__ import annotations

from collections import Counter
import json
import os
from pathlib import Path
import shutil
import tempfile
from typing import Callable

from .candidate_review import BATCH_ID, EVIDENCE_ID
from .promotion_readiness import _sha, build_promotion_plan, canonical_state_digest
from .repository import EvidenceError

SCHEMA_VERSION = "phase-119-bounded-promotion-v1"
PROMOTION_ID = "phase-119-mb2-batch-000001-e32022126c07"
EXPECTED_CANDIDATE_DIGEST = "e32022126c07036337f810d06dc29b5eead5afd850f7f3af0a26ad5b0d46e66e"
ENTITY_COUNTS = {"card": 384, "finish": 2, "identifier": 235, "printing": 379}


def _json(value: object) -> str:
    return json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n"


def _paths(data_root: Path) -> tuple[Path, Path]:
    return (data_root / "canonical" / "state.json",
            data_root / "audit" / "bounded_promotions" / f"{PROMOTION_ID}.json")


def _payload(data_root: Path) -> dict:
    path = (data_root / "production_runs" / EVIDENCE_ID / "review_payloads" / "mb2" /
            f"{BATCH_ID}.json")
    return json.loads(path.read_text(encoding="utf-8"))


def _canonical_id(candidate: dict) -> str:
    fields = candidate["mapped_fields"]
    kind = candidate["entity_type"]
    if kind == "card": return fields["card_reference"].lower()
    if kind == "printing": return fields["uuid"].lower()
    if kind == "finish": return fields["value"].lower()
    return candidate["candidate_identifier"].rsplit(":", 1)[-1]


def preflight(data_root: Path | str) -> dict:
    """Independently reverify readiness and return the exact deterministic write plan."""
    root = Path(data_root)
    readiness = build_promotion_plan(root)
    payload = _payload(root)
    candidates = payload["candidate_payloads"]
    ids = payload["candidate_ids"]
    if payload["candidate_id_digest"] != EXPECTED_CANDIDATE_DIGEST or _sha(ids) != EXPECTED_CANDIDATE_DIGEST:
        raise EvidenceError("candidate membership digest mismatch")
    if len(candidates) != 1000 or Counter(x["entity_type"] for x in candidates) != Counter(ENTITY_COUNTS):
        raise EvidenceError("approved candidate scope mismatch")
    if any(x.get("mapped_fields", {}).get("set_code", "mb2").casefold() != "mb2" for x in candidates):
        raise EvidenceError("non-MB2 candidate in promotion scope")
    records: dict[str, dict] = {kind: {} for kind in ENTITY_COUNTS}
    candidate_membership = []
    for candidate in candidates:
        kind = candidate["entity_type"]
        identifier = _canonical_id(candidate)
        if identifier in records[kind]: raise EvidenceError(f"duplicate canonical {kind} identity")
        values = dict(candidate["mapped_fields"])
        if kind == "printing":
            values["card_id"] = values.pop("card_reference").lower()
            values["set_id"] = values.pop("set_code").lower()
            values["finish_ids"] = values.pop("finishes")
        record = {"entity_type": kind, "values": values,
                  "unknown_values": candidate["unknown_fields"],
                  "confidence": candidate["confidence"], "uncertainty_state": "known",
                  "evidence_references": [candidate["candidate_identifier"]],
                  "dataset_identity": [candidate["source_dataset"]],
                  "acquisition_lineage": [candidate["acquisition_metadata"]],
                  "review_package_id": BATCH_ID, "promotion_id": PROMOTION_ID,
                  "provenance": candidate["provenance"]}
        records[kind][identifier] = record
        candidate_membership.append(candidate["candidate_identifier"])
    card_ids = set(records["card"])
    orphans = sorted(x for x, row in records["printing"].items()
                     if row["values"]["card_id"] not in card_ids)
    if orphans: raise EvidenceError("dependency orphan rejection")
    review_digests = {}
    for phase in ("phase-115", "phase-116"):
        review_root = root / "reviews" / phase / BATCH_ID
        for path in sorted(review_root.glob("*.json")):
            review_digests[str(path.relative_to(root))] = _sha(path.read_bytes())
    lineage_path = root / "production_runs" / EVIDENCE_ID / "lineage" / "source.json"
    body = {"schema_version": SCHEMA_VERSION, "promotion_id": PROMOTION_ID,
            "readiness_plan_digest": readiness["plan_digest"],
            "evidence_identity": EVIDENCE_ID, "batch_id": BATCH_ID,
            "target": {"code": "MB2", "name": "Mystery Booster 2"},
            "candidate_count": 1000, "candidate_id_digest": EXPECTED_CANDIDATE_DIGEST,
            "findings_digest": readiness["findings_digest"],
            "dependency_digest": readiness["dependency_digest"],
            "source_lineage_digest": _sha(lineage_path.read_bytes()),
            "review_artifact_digests": review_digests,
            "entity_counts": ENTITY_COUNTS, "canonical_pre_state_digest": readiness["canonical_pre_state_digest"],
            "candidate_membership": candidate_membership, "canonical_records": records,
            "dependency_order": ["card", "finish", "printing", "identifier"],
            "excluded_targets": ["MSH", "all_other_batches"]}
    return {**body, "preflight_digest": _sha(body)}


def promote(data_root: Path | str, *, failure_hook: Callable[[str], None] | None = None) -> dict:
    """Atomically write canonical state and its immutable audit, or return idempotent success."""
    root = Path(data_root); state_path, audit_path = _paths(root)
    if audit_path.exists():
        audit = json.loads(audit_path.read_text())
        if audit.get("promotion_id") != PROMOTION_ID or audit.get("candidate_id_digest") != EXPECTED_CANDIDATE_DIGEST:
            raise EvidenceError("conflicting promotion replay")
        if not state_path.exists() or canonical_state_digest(root) != audit["canonical_post_state_digest"]:
            raise EvidenceError("completed promotion state conflicts with immutable audit")
        return {**audit, "idempotent": True}
    plan = preflight(root)
    state = plan.pop("canonical_records")
    state_text = _json(state)
    with tempfile.TemporaryDirectory(dir=root) as temporary:
        stage = Path(temporary); staged_state = stage / "state.json"
        staged_state.write_text(state_text, encoding="utf-8")
        # Digest the exact future canonical tree without mutating the real repository.
        staged_data = stage / "digest-data"
        shutil.copytree(root / "canonical", staged_data / "canonical")
        shutil.copy2(staged_state, staged_data / "canonical" / "state.json")
        post_digest = canonical_state_digest(staged_data)
        audit = {key: value for key, value in plan.items() if key != "candidate_membership"}
        audit.update({"action": "bounded_canonical_promotion", "result": "succeeded",
                      "promoted_entities": plan["candidate_membership"],
                      "canonical_post_state_digest": post_digest,
                      "replay": {"command": "promote", "expected_result": "idempotent_success"},
                      "rollback": {"command": "rollback", "remove": ["canonical/state.json"],
                                   "expected_post_rollback_digest": plan["canonical_pre_state_digest"]}})
        audit["audit_digest"] = _sha(audit)
        staged_audit = stage / "audit.json"; staged_audit.write_text(_json(audit), encoding="utf-8")
        state_path.parent.mkdir(parents=True, exist_ok=True); audit_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            os.replace(staged_state, state_path)
            if failure_hook: failure_hook("after_canonical_write")
            os.replace(staged_audit, audit_path)
            if failure_hook: failure_hook("after_audit_write")
            if canonical_state_digest(root) != post_digest: raise EvidenceError("post-state integrity failure")
        except BaseException:
            state_path.unlink(missing_ok=True); audit_path.unlink(missing_ok=True)
            raise
    return {**audit, "idempotent": False}


def rollback(data_root: Path | str) -> dict:
    """Execute the recorded dependency-safe rollback while retaining immutable audit history."""
    root = Path(data_root); state_path, audit_path = _paths(root)
    if not audit_path.exists(): raise EvidenceError("promotion audit not found")
    audit = json.loads(audit_path.read_text())
    if audit.get("promotion_id") != PROMOTION_ID: raise EvidenceError("conflicting rollback audit")
    if state_path.exists():
        if canonical_state_digest(root) != audit["canonical_post_state_digest"]:
            raise EvidenceError("canonical state drift blocks rollback")
        state_path.unlink()
    digest = canonical_state_digest(root)
    if digest != audit["canonical_pre_state_digest"]: raise EvidenceError("rollback did not restore pre-state")
    return {"promotion_id": PROMOTION_ID, "result": "rolled_back", "canonical_state_digest": digest}
