"""Public evidence inputs for isolated writer rehearsals; never approval data."""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parents[1]
PACKET = ROOT / "reference-reviews/mb2-reference-coverage/structured-2026-10-13"
RECOMMENDED_DIGEST = "f63585f4a023e2b81656a4cca0c6811a7d598e45f065633c3a11d9a9a2b5d500"
PACKET_DIGEST = "158440b59b45c0d50e81f4d8345f4ea637e6d5bbef6d77400a3a2300738c11b8"


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def prepare_reference_rehearsal(root):
    """Copy original public data/evidence and select the independently bound 810.

    The retained pending candidates are not rewritten. Parsed field context is
    supplied separately to the existing persistence boundary. No private owner
    input, declaration, positions, proposed spelling or assessment is used here.
    """
    from production_evidence.automatic_updates import digest
    from production_evidence.promotion_readiness import canonical_state_digest
    root = Path(root)
    list_path = ROOT / "tests/fixtures/catalog_admission/mb2-recommended-candidate-ids.json"
    list_raw = list_path.read_bytes()
    if sha(list_raw) != RECOMMENDED_DIGEST:
        raise ValueError("recommended candidate list integrity mismatch")
    ids = json.loads(list_raw)
    if len(ids) != 810 or len(set(ids)) != 810 or digest(ids) != RECOMMENDED_DIGEST:
        raise ValueError("recommended candidate order/count mismatch")
    packet_raw = (PACKET / "candidate-preparation.json").read_bytes()
    if sha(packet_raw) != PACKET_DIGEST:
        raise ValueError("retained pending candidate packet integrity mismatch")
    packet = json.loads(packet_raw)
    by_id = {c["payload"]["candidate_identifier"]: c for c in packet["candidates"]}
    selected = [by_id[identifier] for identifier in ids]
    if len(packet["candidates"]) != 819 or len(by_id) != 819:
        raise ValueError("retained pending packet census mismatch")
    if any(c["payload"]["review_status"] != "pending" for c in selected):
        raise ValueError("rehearsal source must remain pending")
    from historical_catalog import historical_data
    shutil.copytree(historical_data(), root / "data")
    evidence = root / "data/test-evidence/structured-reference"
    shutil.copytree(PACKET, evidence)
    rows = [deepcopy(c["payload"]) for c in selected]
    contexts = {c["payload"]["candidate_identifier"]: {
        "field_provenance": deepcopy(c["field_provenance"]),
        "retained_candidate_id": c["id"],
        "retained_candidate_validation_state": c["validation_state"],
        "retained_candidate_packet_sha256": PACKET_DIGEST,
    } for c in selected}
    for candidate in selected:
        context = contexts[candidate["payload"]["candidate_identifier"]]
        for key in ("parsed_artifact_id", "parsed_record_id", "source_id", "raw_evidence_hash"):
            values = {item[key] for item in candidate["field_provenance"] if key in item}
            if len(values) != 1:
                raise ValueError("retained parsed field provenance is not uniquely bound")
            context[key] = values.pop()
    payload = {"candidate_ids": ids, "candidate_payloads": rows,
               "candidate_contexts": contexts, "target_set_code": "plst",
               "rehearsal_only": True, "not_owner_approval": True}
    payload_path = root / "data/test-evidence/reference-input.json"
    payload_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    receipts = [{"path": p.relative_to(root / "data").as_posix(),
                 "sha256": sha(p.read_bytes())}
                for p in sorted(evidence.rglob("*")) if p.is_file()
                and p.name != "source-record.json"]
    config = {
        "schema_version": "automatic-canonical-update-v1", "data_root": "data",
        "rehearsal_only": True, "not_owner_approval": True,
        "target": {"game": "magic", "target_code": "PLST",
            "target_name": "Isolated structured-reference writer rehearsal",
            "trusted_provider": "mtgjson",
            "source_dataset_identity": rows[0]["source_dataset"],
            "source_artifact_or_workflow_run": "retained-structured-reference-2026-10-13",
            "evidence_identity": "isolated-writer-rehearsal-only",
            "batch_identifier": "isolated-reference-810-writer-rehearsal",
            "candidate_digest": RECOMMENDED_DIGEST,
            "expected_target_isolation": "PLST",
            "promotion_policy": "isolated-test-only-not-production-approval",
            "destination_branch": "canonical-update/isolated-reference-810-writer-rehearsal",
            "base_branch": "main"},
        "artifacts": {"source_artifact": "test-evidence/structured-reference/source-record.json",
            "candidate_payload": "test-evidence/reference-input.json",
            "promotion_audit": "audit/bounded_promotions/isolated-reference-810-writer-rehearsal.json",
            "receipts": receipts},
        "integrity": {"source_sha256": sha((evidence / "source-record.json").read_bytes()),
            "candidate_payload_sha256": sha(payload_path.read_bytes()),
            "expected_candidate_count": 810,
            "canonical_pre_state_digest": canonical_state_digest(root / "data")},
        "policy": {"trusted_providers": ["mtgjson"],
            "permitted_final_classifications": ["approved"]},
        "canonical_identity_fields": {"card": "card_reference", "printing": "uuid", "finish": "value"}}
    config_path = root / "reference-rehearsal-config.json"
    config_path.write_text(json.dumps(config, indent=2, sort_keys=True) + "\n")
    return config_path, selected
