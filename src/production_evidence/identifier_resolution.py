"""Phase 116 evidence-only resolution of the first MB2 batch identifier findings."""
from __future__ import annotations

from collections import Counter
import hashlib
import json
from pathlib import Path

from .candidate_review import BATCH_ID, EVIDENCE_ID, review_first_mb2_batch
from .repository import EvidenceError

SCHEMA_VERSION = "phase-116-identifier-resolution-v1"
PHASE_115 = Path("reviews/phase-115") / BATCH_ID
PHASE_116 = Path("reviews/phase-116") / BATCH_ID
ALLOWED_DISPOSITIONS = {
    "approved_after_resolution", "excluded_duplicate", "excluded_source_defect",
    "remains_additional_evidence", "quarantined", "fatal_conflict",
}


def classify_collision(*, uniqueness: str, same_coordinates: bool,
                       byte_identical: bool | None, same_source_uuid: bool,
                       proven_non_unique_alias: bool) -> str:
    """Apply the fail-closed collision decision table without weakening strict identity."""
    if uniqueness == "strict":
        return "quarantined" if same_coordinates else "fatal_conflict"
    if byte_identical and same_source_uuid:
        return "excluded_duplicate"
    if proven_non_unique_alias:
        return "approved_after_resolution"
    return "remains_additional_evidence"


def _canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def _sha(value: object) -> str:
    return hashlib.sha256(value if isinstance(value, bytes) else _canonical(value)).hexdigest()


def _load(path: Path) -> dict:
    return json.loads(path.read_text())


def resolve_first_mb2_identifiers(data_root: Path | str) -> dict:
    """Resolve only the 21 Phase 115 ambiguous identifiers from retained evidence."""
    data_root = Path(data_root)
    baseline = review_first_mb2_batch(data_root)
    retained_ledger_path = data_root / PHASE_115 / "candidate-review-ledger.json"
    retained_ledger = _load(retained_ledger_path)
    if retained_ledger["ledger"] != baseline["ledger"]:
        raise EvidenceError("Phase 115 ledger does not match the deterministic baseline")
    affected = [row for row in retained_ledger["ledger"]
                if row["classification"] == "requires_additional_evidence"]
    if len(affected) != 21 or {row["entity_type"] for row in affected} != {"identifier"}:
        raise EvidenceError("Phase 116 scope must be the exact 21 Phase 115 identifiers")

    run_root = data_root / "production_runs" / EVIDENCE_ID
    payload = _load(run_root / baseline["source_payload"]["path"])
    candidates = {row["candidate_identifier"]: row for row in payload["candidate_payloads"]}
    printing_by_uuid = {row["mapped_fields"]["uuid"]: row for row in payload["candidate_payloads"]
                        if row["entity_type"] == "printing"}
    card_refs = {row["mapped_fields"]["card_reference"] for row in payload["candidate_payloads"]
                 if row["entity_type"] == "card"}
    finding_paths = sorted((run_root / "findings/finding-shards").glob("*.json"))
    findings = [_load(path) for path in finding_paths]
    groups = {(row["identifier_namespace"], str(row["identifier_value"])): (path, row)
              for path, row in zip(finding_paths, findings)}

    resolutions = []
    collision_groups = {}
    for old in affected:
        candidate = candidates[old["candidate_id"]]
        fields = candidate["mapped_fields"]
        key = (fields["namespace"], str(fields["value"]))
        if key not in groups:
            raise EvidenceError(f"missing retained collision finding for {key}")
        finding_path, finding = groups[key]
        printing = printing_by_uuid.get(fields["printing_uuid"])
        if printing is None or printing["mapped_fields"]["card_reference"] not in card_refs:
            raise EvidenceError("identifier dependency closure is incomplete")
        group_id = f"{key[0]}:{key[1]}"
        records = finding["affected_source_records"]
        coordinates = sorted({(row["set_code"], row["collector_number"], row["language"])
                              for row in records})
        # scryfallCardBackId describes a shared card-back asset, not a Printing identity.
        # The retained corpus repeats exactly one value across 820 independently identified
        # MB2 Printings.  Their strict MTGJSON UUID identities and physical coordinates differ.
        # We preserve the references without treating their provider value as globally unique.
        supported_alias = (
            key == ("scryfallCardBackId", "0aeebaf5-8c7d-4636-9e82-8c27447861f7")
            and finding["scope"] == "not-guaranteed"
            and finding["collision_count"] == 820
            and len(records) == 820
            and len({row["mtgjson_uuid"] for row in records}) == 820
            and len(coordinates) > 1
            and {row["set_code"] for row in records} == {"mb2", "msh"}
            and {row["set_name"] for row in records} == {
                "Mystery Booster 2", "Marvel Super Heroes"}
        )
        disposition = classify_collision(
            uniqueness="not-guaranteed", same_coordinates=len(coordinates) == 1,
            byte_identical=None, same_source_uuid=False,
            proven_non_unique_alias=supported_alias)
        classification = "approved" if supported_alias else "requires_additional_evidence"
        physical = printing["mapped_fields"]
        resolutions.append({
            "candidate_id": old["candidate_id"], "entity_type": "identifier",
            "identifier_namespace": key[0], "identifier_value": key[1],
            "conflict_group_id": group_id,
            "conflicting_source_records": [row["mtgjson_uuid"] for row in records],
            "physical_coordinates": {"set_code": physical["set_code"],
                                     "collector_number": physical["collector_number"],
                                     "language": physical["language"]},
            "source_uuid": fields["printing_uuid"],
            "source_json_path": None,
            "source_json_path_evidence": "not_retained_in_v2_finding_projection",
            "records_byte_identical": None,
            "records_byte_identity_evidence": "not_retained_in_v2_finding_projection",
            "coordinates_agree": len(coordinates) == 1,
            "candidate_payloads_agree": True,
            "relationship_evidence": {
                "printing_uuid": fields["printing_uuid"],
                "card_reference": physical["card_reference"],
                "printing_candidate_present": True, "card_candidate_present": True,
            },
            "selected_classification": "non_unique_provider_identifier_alias",
            "rationale": ("Retained evidence establishes a shared card-back reference across "
                          "820 distinct UUID-addressed MB2 Printings; it is not used as a global "
                          "Printing identity and strict UUID uniqueness remains unchanged."),
            "disposition": disposition, "updated_classification": classification,
        })
        collision_groups[group_id] = {
            "identifier_namespace": key[0], "identifier_value": key[1],
            "provider_scope": finding["scope"], "collision_count": finding["collision_count"],
            "source_finding": str(finding_path.relative_to(data_root)),
            "source_finding_sha256": _sha(finding_path.read_bytes()),
            "all_conflicting_source_records": records,
            "distinct_source_uuids": len({row["mtgjson_uuid"] for row in records}),
            "distinct_physical_coordinates": len(coordinates),
            "records_byte_identical": None,
            "coordinates_agree": len(coordinates) == 1,
            "classification": "non_unique_provider_identifier_alias" if supported_alias else "unsupported_or_ambiguous",
            "disposition": disposition,
        }

    resolution_by_id = {row["candidate_id"]: row for row in resolutions}
    updated = []
    for old in retained_ledger["ledger"]:
        resolution = resolution_by_id.get(old["candidate_id"])
        updated.append({**old,
                        "classification": resolution["updated_classification"] if resolution else old["classification"],
                        "phase_116_disposition": resolution["disposition"] if resolution else "unchanged_approved",
                        "reasons": [] if resolution and resolution["updated_classification"] == "approved" else old["reasons"]})
    dispositions = Counter(row["phase_116_disposition"] for row in updated)
    classifications = Counter(row["classification"] for row in updated)
    fatal = dispositions["fatal_conflict"]
    unresolved = dispositions["remains_additional_evidence"]
    quarantined = dispositions["quarantined"]
    excluded = dispositions["excluded_duplicate"] + dispositions["excluded_source_defect"]
    approved_ids = [row["candidate_id"] for row in updated if row["classification"] == "approved"]
    excluded_ids = [row["candidate_id"] for row in updated if row["phase_116_disposition"].startswith("excluded_")]
    additional_ids = [row["candidate_id"] for row in updated if row["phase_116_disposition"] == "remains_additional_evidence"]
    quarantine_ids = [row["candidate_id"] for row in updated if row["phase_116_disposition"] == "quarantined"]
    approved_set = set(approved_ids)
    approved_card_refs = {candidates[item]["mapped_fields"]["card_reference"] for item in approved_ids
                          if candidates[item]["entity_type"] == "card"}
    orphaned = []
    for item in approved_ids:
        candidate = candidates[item]
        if candidate["entity_type"] == "printing" and candidate["mapped_fields"]["card_reference"] not in approved_card_refs:
            orphaned.append(item)
    closure_body = {
        "approved_candidate_ids": approved_ids, "excluded_candidate_ids": excluded_ids,
        "remaining_additional_evidence_candidate_ids": additional_ids,
        "quarantined_candidate_ids": quarantine_ids, "orphaned_printing_candidate_ids": orphaned,
        "no_msh_candidates": all(candidates[item]["mapped_fields"].get("set_code", "mb2") == "mb2"
                                 for item in approved_ids),
    }
    closure_digest = _sha(closure_body)
    closure = {**closure_body, "valid": not orphaned and not fatal, "digest": closure_digest,
               "rule": "every approved Printing has an approved Card; non-approved candidates are absent"}
    findings_body = {"collision_groups": [collision_groups[key] for key in sorted(collision_groups)],
                     "resolutions": resolutions}
    findings_digest = _sha(findings_body)
    artifact_core = {
        "identifier-resolution-ledger.json": {"resolutions": resolutions},
        "collision-analysis-report.json": {"collision_groups": findings_body["collision_groups"]},
        "updated-candidate-classification-ledger.json": {"ledger": updated},
        "updated-findings-report.json": {
            "findings_digest": findings_digest,
            "baseline": {"approved": 979, "excluded": 0, "requires_additional_evidence": 21},
            "summary": {"unchanged_approved": dispositions["unchanged_approved"],
                        "newly_approved": dispositions["approved_after_resolution"],
                        "excluded": excluded, "requires_additional_evidence": unresolved,
                        "quarantined": quarantined, "fatal_conflicts": fatal,
                        "final_classifications": dict(sorted(classifications.items())), "total": len(updated)},
        },
        "dependency-closure-verification.json": closure,
    }
    artifact_digests = {name: _sha(value) for name, value in artifact_core.items()}
    status = "blocked_fatal_conflict" if fatal else "blocked_additional_evidence" if unresolved else "validation_complete"
    phase115_decision = _load(data_root / PHASE_115 / "pending-review-decision.json")
    decision_body = {
        "phase_115_decision_lineage": {"path": str(PHASE_115 / "pending-review-decision.json"),
                                      "sha256": _sha((data_root / PHASE_115 / "pending-review-decision.json").read_bytes()),
                                      "ledger_sha256": phase115_decision["ledger_sha256"]},
        "resolution_artifact_digests": artifact_digests,
        "final_approved_candidate_ids": approved_ids, "final_excluded_candidate_ids": excluded_ids,
        "remaining_additional_evidence_candidate_ids": additional_ids,
        "quarantined_candidate_ids": quarantine_ids,
        "findings_digest": findings_digest, "dependency_closure_digest": closure_digest,
        "status": status, "immutable": True,
        "batch_approved": not (fatal or unresolved or quarantined or orphaned),
        "canonical_write": False,
    }
    decision_digest = _sha(decision_body)
    decision = {**decision_body, "decision_digest": decision_digest}
    type_counts = Counter(candidates[item]["entity_type"] for item in approved_ids)
    blockers = (["fatal_identifier_conflict"] if fatal else []) + (["additional_evidence_unresolved"] if unresolved else [])
    if orphaned: blockers.append("dependency_closure_invalid")
    readiness = {
        "approved_card_count": type_counts["card"], "approved_printing_count": type_counts["printing"],
        "approved_identifier_count": type_counts["identifier"], "approved_finish_count": type_counts["finish"],
        "excluded_count": excluded, "unresolved_count": unresolved, "quarantined_count": quarantined,
        "fatal_conflict_count": fatal, "orphaned_printing_count": len(orphaned),
        "dependency_closure_status": "valid" if closure["valid"] else "invalid",
        "promotion_ready": not blockers, "blockers": blockers, "promotion_performed": False,
        "canonical_write": False,
    }
    artifacts = {**artifact_core, "pending-review-decision.json": decision,
                 "promotion-readiness-report.json": readiness}
    envelope = {"schema_version": SCHEMA_VERSION, "evidence_identity": EVIDENCE_ID,
                "batch_id": BATCH_ID, "review_scope": {"candidate_count": 21,
                "other_mb2_batches_reviewed": 0, "marvel_candidates_reviewed": 0}}
    return {"artifacts": {name: {**envelope, **value} for name, value in artifacts.items()},
            "summary": artifact_core["updated-findings-report.json"]["summary"],
            "decision_digest": decision_digest, "status": status, "readiness": readiness}


def write_identifier_resolution_artifacts(data_root: Path | str, output: Path | str) -> dict:
    result = resolve_first_mb2_identifiers(data_root)
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    for name, value in result["artifacts"].items():
        (output / name).write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")
    return result
