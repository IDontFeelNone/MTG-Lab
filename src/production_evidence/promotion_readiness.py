"""Validation-gated promotion readiness for the first retained MB2 batch."""
from __future__ import annotations

from collections import Counter
import hashlib
import json
from pathlib import Path

from .candidate_review import BATCH_ID, EVIDENCE_ID
from .identifier_resolution import resolve_first_mb2_identifiers
from .repository import EvidenceError, ProductionEvidenceRepository

SCHEMA_VERSION = "phase-118-promotion-readiness-v1"
TRUSTED_PROVIDERS = frozenset({"mtgjson"})
EXPECTED_CANONICAL_PRE_STATE = "0e5ead0d4693f1dc75c2f7b5e401f22e4fa302f93bb8eab59f0ddeefd0f680ba"
PHASE_116 = Path("reviews/phase-116") / BATCH_ID


def _canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def _sha(value: object) -> str:
    return hashlib.sha256(value if isinstance(value, bytes) else _canonical(value)).hexdigest()


def canonical_state_digest(data_root: Path | str) -> str:
    root = Path(data_root) / "canonical"
    inventory = [{"path": str(path.relative_to(root)), "sha256": _sha(path.read_bytes())}
                 for path in sorted(root.rglob("*")) if path.is_file()]
    return _sha(inventory)


def evaluate_review_gate(*, approved: int, unresolved: int, quarantined: int,
                         fatal_conflicts: int, orphaned: int, target_isolated: bool) -> list[str]:
    """Return deterministic blockers for a resolved candidate review."""
    blockers = []
    if approved != 1000: blockers.append("candidate_membership_incomplete")
    if unresolved: blockers.append("unresolved_candidates_present")
    if quarantined: blockers.append("quarantined_candidates_present")
    if fatal_conflicts: blockers.append("fatal_conflicts_present")
    if orphaned: blockers.append("dependency_closure_invalid")
    if not target_isolated: blockers.append("target_isolation_invalid")
    return blockers


def build_promotion_plan(data_root: Path | str) -> dict:
    """Verify retained evidence and create a non-executing, one-batch promotion plan."""
    data_root = Path(data_root)
    current_digest = canonical_state_digest(data_root)
    if current_digest != EXPECTED_CANONICAL_PRE_STATE:
        audit_path = (data_root / "audit" / "bounded_promotions" /
                      "phase-119-mb2-batch-000001-e32022126c07.json")
        try:
            completed = json.loads(audit_path.read_text())
        except (OSError, json.JSONDecodeError):
            raise EvidenceError("canonical pre-state drift") from None
        audit_digest = completed.pop("audit_digest", None)
        completed_post = completed.get("canonical_post_state_digest")
        if (audit_digest != _sha(completed) or
                completed.get("promotion_id") != "phase-119-mb2-batch-000001-e32022126c07" or
                completed.get("canonical_pre_state_digest") != EXPECTED_CANONICAL_PRE_STATE or
                (completed_post != current_digest and not _verified_later_phase(root=data_root,
                    earlier_post=completed_post, current=current_digest))):
            raise EvidenceError("canonical pre-state drift")

    verification = ProductionEvidenceRepository(data_root).verify(EVIDENCE_ID)
    if not verification["valid"]:
        raise EvidenceError("retained production evidence did not verify")
    run = data_root / "production_runs" / EVIDENCE_ID
    index = json.loads((run / "batch_index.json").read_text())
    selected = [row for row in index["batches"] if row["batch_id"] == BATCH_ID]
    if len(selected) != 1 or selected[0]["target_product"] != "MB2":
        raise EvidenceError("promotion scope must be exactly one retained MB2 batch")

    generated = resolve_first_mb2_identifiers(data_root)["artifacts"]
    verified_artifacts = {
        "identifier-resolution-ledger.json", "collision-analysis-report.json",
        "updated-candidate-classification-ledger.json", "updated-findings-report.json",
        "dependency-closure-verification.json",
    }
    for name in verified_artifacts:
        value = generated[name]
        retained = data_root / PHASE_116 / name
        expected = json.dumps(value, indent=2, sort_keys=True) + "\n"
        if not retained.is_file() or retained.read_text() != expected:
            raise EvidenceError(f"retained Phase 116 artifact mismatch: {name}")

    ledger = generated["updated-candidate-classification-ledger.json"]["ledger"]
    closure = generated["dependency-closure-verification.json"]
    findings = generated["updated-findings-report.json"]["summary"]
    approved_rows = [row for row in ledger if row["classification"] == "approved"]
    payload = json.loads((run / selected[0]["payload_path"]).read_text())
    providers = {row.get("provenance", {}).get("provider") for row in payload["candidate_payloads"]}
    if not providers or not providers <= TRUSTED_PROVIDERS:
        raise EvidenceError("candidate provider is not approved and trusted")

    blockers = evaluate_review_gate(
        approved=len(approved_rows), unresolved=findings["requires_additional_evidence"],
        quarantined=findings["quarantined"], fatal_conflicts=findings["fatal_conflicts"],
        orphaned=len(closure["orphaned_printing_candidate_ids"]),
        target_isolated=closure["no_msh_candidates"],
    )
    if blockers:
        raise EvidenceError("promotion readiness blocked: " + ", ".join(blockers))
    if findings.get("excluded", 0):
        raise EvidenceError("promotion readiness blocked: excluded_candidates_present")

    counts = Counter(row["entity_type"] for row in approved_rows)
    body = {
        "schema_version": SCHEMA_VERSION, "evidence_identity": EVIDENCE_ID,
        "batch_id": BATCH_ID, "target": {"code": "MB2", "name": "Mystery Booster 2"},
        "trusted_providers": sorted(providers), "candidate_count": len(approved_rows),
        "candidate_id_digest": _sha([row["candidate_id"] for row in approved_rows]),
        "entity_counts": dict(sorted(counts.items())), "unresolved_count": 0,
        "quarantined_count": 0, "fatal_conflict_count": 0,
        "dependency_closure": "valid", "target_isolation": "MB2_only",
        "findings_digest": generated["updated-findings-report.json"]["findings_digest"],
        "dependency_digest": closure["digest"],
        "canonical_pre_state_digest": EXPECTED_CANONICAL_PRE_STATE,
        "promotion_ready": True, "explicit_invocation_required": True,
        "promotion_performed": False, "canonical_write": False,
        "audit_requirements": ["source_lineage", "candidate_membership", "pre_and_post_state_digests",
                               "promotion_identifier", "timestamp", "result"],
        "rollback_requirements": ["promotion_identifier", "dependency_order",
                                  "audit_replay_verification", "post_rollback_state_digest"],
    }
    return {**body, "plan_digest": _sha(body)}


def _verified_later_phase(*, root: Path, earlier_post: str, current: str) -> bool:
    """Accept a strictly audited canonical successor without weakening Phase 118."""
    path = root / "audit" / "bounded_promotions" / "phase-136-mtgjson-pilot-30786023976-1.json"
    try:
        audit = json.loads(path.read_text()); identity = audit.pop("audit_digest")
    except (OSError, KeyError, json.JSONDecodeError):
        return False
    return (identity == _sha(audit) and audit.get("result") == "succeeded" and
            audit.get("canonical_pre_state_digest") == earlier_post and
            audit.get("canonical_post_state_digest") == current)
