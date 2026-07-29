"""Cross-artifact validation for non-canonical normalized candidates."""
from __future__ import annotations
from typing import Any, Mapping
from validation import SchemaValidationError, validate_document
from .candidates import CandidateValidationResult, CandidateValidationState

def validate_candidate_artifact(candidate:Mapping[str,Any], parsed:Mapping[str,Any])->CandidateValidationResult:
    errors:list[str]=[]
    try: validate_document(candidate,"normalized-candidate-artifact")
    except SchemaValidationError as e: return CandidateValidationResult(CandidateValidationState.INVALID,(str(e),))
    for field in ("product_id","source_id","acquisition_target_id","raw_evidence_hash"):
        if candidate[field]!=parsed.get(field): errors.append(f"{field} does not match parsed artifact")
    if candidate["parsed_artifact_id"]!=parsed.get("id"): errors.append("parsed_artifact_id does not match parsed artifact")
    parsed_ids={r["id"] for r in parsed.get("records",[])}
    seen:set[str]=set()
    for record in candidate["candidates"]:
        if record["id"] in seen: errors.append(f"duplicate candidate identifier: {record['id']}")
        seen.add(record["id"])
        missing=set(record["parsed_record_ids"])-parsed_ids
        if missing: errors.append(f"unknown parsed record references: {sorted(missing)}")
        for provenance in record["field_provenance"]:
            if provenance["parsed_artifact_id"]!=parsed["id"] or provenance["parsed_record_id"] not in parsed_ids:
                errors.append("field provenance does not reference parsed artifact records")
    return CandidateValidationResult(CandidateValidationState.INVALID if errors else CandidateValidationState.VALID,tuple(errors))
