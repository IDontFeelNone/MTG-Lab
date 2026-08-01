"""Phase 117 fail-closed operator authorization boundary for the first MB2 batch."""
from __future__ import annotations

from collections import Counter
from datetime import datetime
import hashlib
import json
from pathlib import Path
import re

from .candidate_review import BATCH_ID, EVIDENCE_ID
from .identifier_resolution import resolve_first_mb2_identifiers
from .repository import EvidenceError, ProductionEvidenceRepository

SCHEMA_VERSION = "phase-117-operator-authorization-v1"
PHASE_115 = Path("reviews/phase-115") / BATCH_ID
PHASE_116 = Path("reviews/phase-116") / BATCH_ID
PHASE_117 = Path("reviews/phase-117") / BATCH_ID
DECISIONS = {"authorize_for_promotion", "reject", "return_for_additional_review"}
HUMAN_FIELDS = ["operator_identity", "operator_role", "review_reference", "reviewed_at",
                "authorization_decision", "operator_notes", "signature_request_digest",
                "authorized_batch_id", "authorized_candidate_digest"]
PLACEHOLDERS = {"unknown", "placeholder", "tbd", "todo", "n/a", "none", "operator",
                "your name", "name", "changeme"}


def _canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def _sha(value: object) -> str:
    return hashlib.sha256(value if isinstance(value, bytes) else _canonical(value)).hexdigest()


def _load(path: Path) -> dict:
    return json.loads(path.read_text())


def canonical_state_digest(data_root: Path | str) -> str:
    """Hash canonical paths and bytes without modifying them."""
    root = Path(data_root) / "canonical"
    inventory = [{"path": str(p.relative_to(root)), "sha256": _sha(p.read_bytes())}
                 for p in sorted(root.rglob("*")) if p.is_file()]
    return _sha(inventory)


def verify_review_chain(data_root: Path | str) -> dict:
    """Independently regenerate and compare the retained evidence/review chain."""
    data_root = Path(data_root)
    run = data_root / "production_runs" / EVIDENCE_ID
    manifest, metadata = _load(run / "manifest.json"), _load(run / "metadata.json")
    if manifest.get("evidence_identity") != EVIDENCE_ID:
        raise EvidenceError("retained evidence identity mismatch")
    ProductionEvidenceRepository(data_root).verify(EVIDENCE_ID)
    index = _load(run / "batch_index.json")
    batches = [row for row in index["batches"] if row["batch_id"] == BATCH_ID]
    if len(batches) != 1 or batches[0]["target_product"] != "MB2" or batches[0]["retained_payload_count"] != 1000:
        raise EvidenceError("exact MB2 batch identity/count mismatch")
    batch = batches[0]
    payload_path = run / batch["payload_path"]
    if _sha(payload_path.read_bytes()) != batch["payload_sha256"]:
        raise EvidenceError("source payload digest mismatch")
    generated = resolve_first_mb2_identifiers(data_root)["artifacts"]
    phase_digests = {}
    for phase, relative in (("phase_115", PHASE_115), ("phase_116", PHASE_116)):
        files = {}
        for path in sorted((data_root / relative).glob("*.json")):
            files[path.name] = _sha(path.read_bytes())
        phase_digests[phase] = files
    for name, value in generated.items():
        retained = data_root / PHASE_116 / name
        expected = json.dumps(value, indent=2, sort_keys=True) + "\n"
        if not retained.exists() or retained.read_text() != expected:
            raise EvidenceError(f"Phase 116 artifact mismatch: {name}")
    decision115 = _load(data_root / PHASE_115 / "pending-review-decision.json")
    decision116 = _load(data_root / PHASE_116 / "pending-review-decision.json")
    ledger = _load(data_root / PHASE_116 / "updated-candidate-classification-ledger.json")["ledger"]
    approved = [row for row in ledger if row["classification"] == "approved"]
    counts = Counter(row["entity_type"] for row in approved)
    closure = _load(data_root / PHASE_116 / "dependency-closure-verification.json")
    findings = _load(data_root / PHASE_116 / "updated-findings-report.json")
    if len(ledger) != 1000 or len(approved) != 1000 or counts != Counter(card=384, printing=379, identifier=235, finish=2):
        raise EvidenceError("final candidate reconciliation mismatch")
    if not closure["valid"] or not closure["no_msh_candidates"] or closure["orphaned_printing_candidate_ids"]:
        raise EvidenceError("dependency closure or target isolation mismatch")
    if any(row.get("classification") != "approved" for row in ledger):
        raise EvidenceError("unresolved candidate exists")
    if decision115.get("operator_signature") or decision116.get("operator_signature") or decision116.get("promotion_authorized"):
        raise EvidenceError("prior authorization exists")
    if manifest.get("canonical_write") or manifest.get("promotion_performed") or metadata.get("canonical_write") or metadata.get("promotion_performed"):
        raise EvidenceError("prior canonical write or promotion reported")
    candidate_ids = [row["candidate_id"] for row in approved]
    return {
        "schema_version": SCHEMA_VERSION, "evidence_identity": EVIDENCE_ID,
        "batch_id": BATCH_ID, "status": "verified", "evidence_verification_status": "verified",
        "candidate_review_status": "verified", "identifier_resolution_status": "verified",
        "identifier_policy_status": "applied", "dependency_closure_status": "valid",
        "target_isolation_status": "MB2_only", "candidate_count": 1000,
        "approved_candidate_count": 1000, "approved_entity_counts": dict(sorted(counts.items())),
        "final_candidate_ids": candidate_ids, "final_candidate_id_digest": _sha(candidate_ids),
        "phase_115_decision_id": "phase-115/pending-review-decision",
        "phase_115_decision_digest": phase_digests["phase_115"]["pending-review-decision.json"],
        "phase_116_decision_id": "phase-116/pending-review-decision",
        "phase_116_decision_digest": phase_digests["phase_116"]["pending-review-decision.json"],
        "phase_artifact_digests": phase_digests,
        "findings_digest": findings["findings_digest"],
        "dependency_closure_digest": closure["digest"],
        "workflow_run_id": metadata["run_id"], "source_artifact_identity": metadata["artifact_name"],
        "source_sha256": metadata["source_sha256"], "archive_sha256": metadata["original_archive_sha256"],
        "source_payload_sha256": batch["payload_sha256"],
        "canonical_pre_state_digest": canonical_state_digest(data_root),
        "prior_authorization_present": False, "canonical_write": False, "promotion_performed": False,
    }


def build_signature_request(data_root: Path | str) -> tuple[dict, dict, dict, dict]:
    chain = verify_review_chain(data_root)
    request_body = {
        "schema_version": SCHEMA_VERSION, "evidence_identity": EVIDENCE_ID,
        "workflow_run_id": chain["workflow_run_id"], "source_artifact_identity": chain["source_artifact_identity"],
        "source_sha256": chain["source_sha256"], "archive_sha256": chain["archive_sha256"],
        "batch_id": BATCH_ID, "target": {"code": "MB2", "name": "Mystery Booster 2"},
        "phase_115_decision": {"id": chain["phase_115_decision_id"], "digest": chain["phase_115_decision_digest"]},
        "phase_116_decision": {"id": chain["phase_116_decision_id"], "digest": chain["phase_116_decision_digest"]},
        "final_candidate_id_digest": chain["final_candidate_id_digest"],
        "final_approved_candidate_count": 1000, "approved_entity_counts": chain["approved_entity_counts"],
        "findings_digest": chain["findings_digest"], "dependency_closure_digest": chain["dependency_closure_digest"],
        "canonical_pre_state_digest": chain["canonical_pre_state_digest"],
        "exact_promotion_scope": {"batch_ids": [BATCH_ID], "candidate_ids": chain["final_candidate_ids"]},
        "scope_statements": ["Authorization applies only to this batch.",
            "No Marvel/MSH data is included.", "Authorization does not approve another batch.",
            "Promotion remains a separate operation."],
        "required_human_entered_fields": HUMAN_FIELDS, "status": "awaiting_operator_authorization",
    }
    request = {**request_body, "signature_request_digest": _sha(request_body)}
    contract = {"schema_version": SCHEMA_VERSION, "required_fields": HUMAN_FIELDS,
        "authorization_decisions": sorted(DECISIONS), "exact_batch_count": 1,
        "immutable": True, "canonical_state_must_match_request": True,
        "prohibited_operator_identities": ["AI", "Codex", "ChatGPT", "OpenAI", "placeholder"],
        "review_reference_requirement": "durable non-placeholder reference containing a namespace and identifier",
        "timestamp_requirement": "RFC 3339 timestamp with timezone", "canonical_write": False,
        "promotion_performed": False}
    readiness = {"schema_version": SCHEMA_VERSION, "evidence_identity": EVIDENCE_ID, "batch_id": BATCH_ID,
        "evidence_verification_status": "verified", "candidate_review_status": "verified",
        "identifier_resolution_status": "verified", "dependency_closure_status": "valid",
        "signature_request_status": "awaiting_operator_authorization", "operator_authorization_status": "absent",
        "canonical_pre_state_digest": chain["canonical_pre_state_digest"], "eligible_candidate_count": 1000,
        "eligible_entity_counts": chain["approved_entity_counts"], "operator_authorization_present": False,
        "eligible_for_promotion": False, "promotion_performed": False, "canonical_write": False,
        "remaining_blockers": ["genuine_operator_authorization_missing", "promotion_is_a_separate_phase"]}
    return request, chain, contract, readiness


def write_phase117_artifacts(data_root: Path | str, output: Path | str | None = None) -> dict:
    data_root = Path(data_root); output = Path(output) if output else data_root / PHASE_117
    values = dict(zip(("signature-request.json", "review-chain-verification.json",
                       "authorization-contract.json", "promotion-readiness-report.json"),
                      build_signature_request(data_root)))
    output.mkdir(parents=True, exist_ok=True)
    for name, value in values.items():
        path = output / name; rendered = json.dumps(value, indent=2, sort_keys=True) + "\n"
        if path.exists() and path.read_text() != rendered:
            raise EvidenceError(f"immutable Phase 117 artifact conflict: {name}")
        path.write_text(rendered)
    return values


def _validate_human_fields(fields: dict, request: dict) -> None:
    missing = [key for key in HUMAN_FIELDS if key not in fields]
    if missing: raise EvidenceError("missing authorization fields: " + ", ".join(missing))
    for key in ("operator_identity", "operator_role", "review_reference"):
        value = fields[key]
        if not isinstance(value, str) or not value.strip() or value.strip().lower() in PLACEHOLDERS:
            raise EvidenceError(f"invalid or placeholder {key}")
    if re.search(r"\b(ai|codex|chatgpt|openai|automation|bot|workflow|artificial intelligence)\b",
                 fields["operator_identity"], re.I):
        raise EvidenceError("AI systems cannot be operators")
    if not re.fullmatch(r"[A-Za-z][A-Za-z0-9_.-]{1,31}:[A-Za-z0-9][A-Za-z0-9_./-]{2,127}", fields["review_reference"]):
        raise EvidenceError("review_reference must be a durable namespaced identifier")
    try:
        timestamp = datetime.fromisoformat(fields["reviewed_at"].replace("Z", "+00:00"))
    except (AttributeError, ValueError) as exc:
        raise EvidenceError("reviewed_at must be RFC 3339") from exc
    if timestamp.tzinfo is None: raise EvidenceError("reviewed_at must include timezone")
    if fields["authorization_decision"] not in DECISIONS: raise EvidenceError("invalid authorization_decision")
    if (not isinstance(fields["operator_notes"], str) or not fields["operator_notes"].strip() or
            fields["operator_notes"].strip().lower() in PLACEHOLDERS):
        raise EvidenceError("operator_notes must be genuine non-placeholder text")
    if fields["signature_request_digest"] != request["signature_request_digest"]: raise EvidenceError("signature request digest mismatch")
    if fields["authorized_batch_id"] != BATCH_ID: raise EvidenceError("authorized batch mismatch")
    if fields["authorized_candidate_digest"] != request["final_candidate_id_digest"]: raise EvidenceError("authorized candidate digest mismatch")
    if request["exact_promotion_scope"]["batch_ids"] != [BATCH_ID] or request["target"]["code"] != "MB2":
        raise EvidenceError("authorization scope is not exactly one MB2 batch")


def record_authorization(data_root: Path | str, fields: dict) -> dict:
    """Record genuine supplied authorization; never write canonical state or promote."""
    data_root = Path(data_root); output = data_root / PHASE_117
    request_path = output / "signature-request.json"
    if not request_path.exists(): raise EvidenceError("immutable signature request is missing")
    request = _load(request_path)
    expected, chain, _, _ = build_signature_request(data_root)
    if request != expected: raise EvidenceError("signature request or canonical pre-state drift")
    _validate_human_fields(fields, request)
    body = {"schema_version": SCHEMA_VERSION, **fields,
        "review_chain_lineage": {key: chain[key] for key in ("evidence_identity", "workflow_run_id",
            "source_artifact_identity", "source_sha256", "archive_sha256", "phase_115_decision_id",
            "phase_115_decision_digest", "phase_116_decision_id", "phase_116_decision_digest",
            "findings_digest", "dependency_closure_digest", "final_candidate_id_digest")},
        "prior_canonical_state_digest": request["canonical_pre_state_digest"],
        "status": {"authorize_for_promotion": "authorized_for_later_promotion",
                   "reject": "rejected", "return_for_additional_review": "returned_for_additional_review"}[fields["authorization_decision"]],
        "canonical_write": False, "promotion_performed": False, "immutable": True}
    artifact = {**body, "authorization_digest": _sha(body)}
    path = output / "operator-authorization.json"
    rendered = json.dumps(artifact, indent=2, sort_keys=True) + "\n"
    if path.exists():
        if path.read_text() != rendered: raise EvidenceError("conflicting immutable authorization exists")
        return _load(path)
    path.write_text(rendered)
    if _load(path) != artifact or _sha({k: v for k, v in artifact.items() if k != "authorization_digest"}) != artifact["authorization_digest"]:
        raise EvidenceError("written authorization failed verification")
    return artifact


def verify_authorization_artifact(data_root: Path | str) -> dict:
    """Verify the retained authorization against the live immutable request and chain."""
    data_root = Path(data_root)
    path = data_root / PHASE_117 / "operator-authorization.json"
    if not path.is_file():
        raise EvidenceError("operator authorization is missing")
    artifact = _load(path)
    digest = artifact.get("authorization_digest")
    body = {key: value for key, value in artifact.items() if key != "authorization_digest"}
    if not isinstance(digest, str) or _sha(body) != digest:
        raise EvidenceError("authorization digest mismatch")
    request, chain, _, _ = build_signature_request(data_root)
    fields = {key: artifact.get(key) for key in HUMAN_FIELDS}
    _validate_human_fields(fields, request)
    expected_lineage = {key: chain[key] for key in ("evidence_identity", "workflow_run_id",
        "source_artifact_identity", "source_sha256", "archive_sha256", "phase_115_decision_id",
        "phase_115_decision_digest", "phase_116_decision_id", "phase_116_decision_digest",
        "findings_digest", "dependency_closure_digest", "final_candidate_id_digest")}
    if artifact.get("review_chain_lineage") != expected_lineage:
        raise EvidenceError("authorization review-chain lineage mismatch")
    if artifact.get("prior_canonical_state_digest") != request["canonical_pre_state_digest"]:
        raise EvidenceError("authorization canonical pre-state mismatch")
    if artifact.get("canonical_write") is not False or artifact.get("promotion_performed") is not False:
        raise EvidenceError("authorization reports a canonical write or promotion")
    return artifact
