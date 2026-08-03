"""Phase 136 bounded promotion from the retained Phase 135 pilot projection.

This module deliberately has no transport.  It verifies the immutable three-file
evidence boundary, constructs one reviewed candidate for every retained row, and
atomically replaces the canonical state.  The provider UUID is the canonical
Printing identity; no set membership is converted into a Printing.
"""
from __future__ import annotations

from collections import Counter
import hashlib
import json
import os
from pathlib import Path
import shutil
import tempfile

from .promotion_readiness import canonical_state_digest
from .repository import EvidenceError

RUN_ID = "mtgjson-pilot-30786023976-1"
PROMOTION_ID = "phase-136-mtgjson-pilot-30786023976-1"
EXPECTED_PRE_STATE = "793a364794e12002dd561a47a42333332ae7dd64a958fc18903b0cc2381de27f"
INVENTORY = ("acquisition-report.json", "manifest.json", "source-pilot-printings.json")
COUNTS = {"Brainstorm": 47, "Command Tower": 110, "Counterspell": 83,
          "Goblin Charbelcher": 8, "Goblin King": 26, "Sol Ring": 135,
          "Swords to Plowshares": 96, "Treasure Cruise": 14,
          "Walking Ballista": 10, "Wishclaw Talisman": 5}


def _bytes(value: object) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False,
                       separators=(",", ": ")) + "\n").encode()


def _sha(value: bytes | object) -> str:
    if not isinstance(value, bytes):
        value = json.dumps(value, sort_keys=True, separators=(",", ":"),
                           ensure_ascii=False).encode()
    return hashlib.sha256(value).hexdigest()


def verify_evidence(data_root: Path | str) -> dict:
    root = Path(data_root) / "evidence" / "phase-135" / RUN_ID
    if not root.is_dir() or tuple(sorted(x.name for x in root.iterdir() if x.is_file())) != INVENTORY:
        raise EvidenceError("Phase 135 evidence inventory mismatch")
    if any(not x.is_file() for x in root.iterdir()):
        raise EvidenceError("Phase 135 evidence contains a non-regular entry")
    manifest_bytes = (root / "manifest.json").read_bytes()
    manifest = json.loads(manifest_bytes)
    report = json.loads((root / "acquisition-report.json").read_bytes())
    source_bytes = (root / "source-pilot-printings.json").read_bytes()
    source = json.loads(source_bytes)
    if report["manifest_sha256"] != _sha(manifest_bytes):
        raise EvidenceError("manifest digest mismatch")
    if len(source["pilot_printings"]) != 534 or manifest["retained_printing_count"] != 534:
        raise EvidenceError("retained census mismatch")
    if _sha(source_bytes) != manifest["normalized_projection_sha256"] or len(source_bytes) != manifest["normalized_projection_byte_count"]:
        raise EvidenceError("normalized projection integrity mismatch")
    if manifest["printing_counts_by_pilot_card"] != COUNTS:
        raise EvidenceError("pilot printing census mismatch")
    if set(manifest["pilot_scope"]) != set(COUNTS) or len(manifest["pilot_scope"]) != 10:
        raise EvidenceError("pilot scope mismatch")
    zeroes = ("ambiguous_records", "duplicates", "malformed_records", "unsupported_records")
    if any(manifest[x] != 0 for x in zeroes) or manifest["unmatched_pilot_cards"]:
        raise EvidenceError("evidence contains unresolved records")
    if any(manifest[x] for x in ("canonical_write", "promotion_performed", "facts_created")) or report["market_write"]:
        raise EvidenceError("acquisition crossed a write boundary")
    rows = source["pilot_printings"]
    ids = [x["provider_printing_id"] for x in rows]
    if len(ids) != len(set(ids)) or any(not x or x["set_code"] == "MB2" for x in rows):
        raise EvidenceError("unstable, duplicate, or MB2 Printing identity")
    return {"manifest": manifest, "report": report, "source": source,
            "evidence_files": {name: _sha((root / name).read_bytes()) for name in INVENTORY}}


def build_plan(data_root: Path | str) -> dict:
    root = Path(data_root); verified = verify_evidence(root)
    if canonical_state_digest(root) != EXPECTED_PRE_STATE:
        raise EvidenceError("canonical pre-state drift")
    state = json.loads((root / "canonical" / "state.json").read_text())
    cards = {v["values"]["name"]: k for k, v in state["card"].items() if v["values"]["name"] in COUNTS}
    if len(cards) != 10:
        raise EvidenceError("exact canonical Card reuse failed")
    candidates = []
    for row in verified["source"]["pilot_printings"]:
        card_id = cards.get(row["card_name"])
        if card_id != row["provider_card_or_oracle_id"]:
            raise EvidenceError("provider Card identity conflicts with canonical Card")
        values = {"uuid": row["provider_printing_id"], "card_id": card_id,
                  "set_id": row["set_code"].casefold(), "set_code": row["set_code"],
                  "set_name": row["set_name"], "collector_number": row["collector_number"],
                  "release_date": row["release_date"], "language": row["language"],
                  "finish_ids": row["finishes"], "rarity": row["rarity"],
                  "frame_or_treatment": row["frame_or_treatment"],
                  "promotional": row["promotional"], "reprint": row["reprint"],
                  "digital_or_paper": row["digital_or_paper"],
                  "provider_card_or_oracle_id": row["provider_card_or_oracle_id"],
                  "source_record_identity": row["source_record_identity"]}
        candidates.append({"candidate_id": "mtgjson:printing:" + row["provider_printing_id"],
                           "classification": "accepted", "entity_type": "printing",
                           "values": values})
    candidates.sort(key=lambda x: x["candidate_id"])
    return {"schema_version": "phase-136-promotion-plan-v1", "promotion_id": PROMOTION_ID,
            "acquisition_run_id": RUN_ID, "candidate_count": len(candidates),
            "candidate_digest": _sha(candidates), "review_census": {"accepted": 534,
                "existing_canonical_duplicate": 0, "retained_duplicate": 0, "ambiguous": 0,
                "conflicting": 0, "incomplete": 0, "unsupported": 0, "rejected": 0},
            "cards_reused": cards, "supporting_entities_reused": {"finish": ["foil", "nonfoil"]},
            "canonical_pre_state_digest": EXPECTED_PRE_STATE,
            "evidence_files": verified["evidence_files"], "candidates": candidates}


def promote(data_root: Path | str, *, failure_hook=None) -> dict:
    root = Path(data_root); audit_path = root / "audit" / "bounded_promotions" / f"{PROMOTION_ID}.json"
    if audit_path.exists():
        audit = json.loads(audit_path.read_text())
        if canonical_state_digest(root) != audit["canonical_post_state_digest"]:
            raise EvidenceError("conflicting promotion replay")
        return {**audit, "idempotent": True}
    plan = build_plan(root)
    state_path = root / "canonical" / "state.json"; original_state = state_path.read_bytes()
    state = json.loads(original_state)
    for candidate in plan["candidates"]:
        values = candidate["values"]; identity = values["uuid"]
        if identity in state["printing"]: raise EvidenceError("duplicate canonical Printing")
        state["printing"][identity] = {"entity_type": "printing", "values": values,
            "unknown_values": {k: {"status": "unknown"} for k in
                ("promotional", "digital_or_paper") if values[k] == "unknown"},
            "confidence": 1.0, "uncertainty_state": "known",
            "evidence_references": [candidate["candidate_id"]],
            "dataset_identity": [RUN_ID], "acquisition_lineage": [{"acquisition_run_id": RUN_ID,
                "source_sha256": verify_evidence(root)["manifest"]["source_sha256"],
                "normalized_projection_sha256": verify_evidence(root)["manifest"]["normalized_projection_sha256"]}],
            "review_package_id": PROMOTION_ID, "promotion_id": PROMOTION_ID,
            "provenance": {"provider": "mtgjson", "source_record_identity": values["source_record_identity"]}}
    with tempfile.TemporaryDirectory(dir=root) as temp:
        temp = Path(temp); staged = temp / "state.json"; staged.write_bytes(_bytes(state))
        shadow = temp / "shadow"; shutil.copytree(root / "canonical", shadow / "canonical")
        shutil.copy2(staged, shadow / "canonical" / "state.json")
        post = canonical_state_digest(shadow)
        audit = {k: v for k, v in plan.items() if k != "candidates"}
        audit.update({"schema_version": "phase-136-bounded-promotion-audit-v1",
                      "result": "succeeded", "promoted_printing_ids": [x["values"]["uuid"] for x in plan["candidates"]],
                      "canonical_post_state_digest": post, "rollback_identity": PROMOTION_ID + "-rollback",
                      "replay_behavior": "byte-identical idempotent success; conflicts fail closed"})
        audit["audit_digest"] = _sha(audit); staged_audit = temp / "audit.json"; staged_audit.write_bytes(_bytes(audit))
        audit_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            os.replace(staged, state_path)
            if failure_hook: failure_hook("after_canonical_write")
            os.replace(staged_audit, audit_path)
            if failure_hook: failure_hook("after_audit_write")
        except BaseException:
            state_path.write_bytes(original_state); audit_path.unlink(missing_ok=True); raise
    return {**audit, "idempotent": False}


def rollback(data_root: Path | str) -> dict:
    root = Path(data_root); audit_path = root / "audit" / "bounded_promotions" / f"{PROMOTION_ID}.json"
    audit = json.loads(audit_path.read_text())
    if canonical_state_digest(root) != audit["canonical_post_state_digest"]:
        raise EvidenceError("canonical post-state drift blocks rollback")
    state_path = root / "canonical" / "state.json"; state = json.loads(state_path.read_text())
    for identity in audit["promoted_printing_ids"]: state["printing"].pop(identity)
    state_path.write_bytes(_bytes(state))
    if canonical_state_digest(root) != EXPECTED_PRE_STATE: raise EvidenceError("rollback restoration failed")
    return {"rollback_identity": audit["rollback_identity"], "result": "rolled_back",
            "canonical_state_digest": EXPECTED_PRE_STATE}
