"""Deterministic, non-canonical knowledge acquisition review artifacts."""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

from .framework import AcquisitionError, NORMALIZED_SCHEMA, RUN_SCHEMA, SNAPSHOT_SCHEMA

REVIEW_SCHEMA = "knowledge-review-package-v1"
REPORT_SCHEMA = "knowledge-pipeline-reports-v1"
POLICY_SCHEMA = "provider-policy-v1"
IDENTITY_SCHEMA = "dataset-identity-v1"


def _canonical(value: Any) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n").encode()


def _digest(value: Any) -> str:
    return hashlib.sha256(_canonical(value)).hexdigest()


@dataclass(frozen=True, slots=True)
class ProviderPolicy:
    """Trust and use policy configured separately from provider adapters."""

    provider_id: str
    evidence_class: str
    confidence_default: float
    license_constraints: tuple[str, ...]
    attribution: str
    allowed_entity_types: tuple[str, ...]
    normalization_rules: Mapping[str, str] = field(default_factory=dict)
    schema_version: str = POLICY_SCHEMA

    def __post_init__(self) -> None:
        allowed = {"official", "authoritative_structured", "verified_community",
                   "direct_observation", "derived", "inferred", "unknown", "conflicting"}
        if (not self.provider_id or self.evidence_class not in allowed or
                not 0 <= self.confidence_default <= 1 or not self.attribution or
                not self.allowed_entity_types):
            raise AcquisitionError("invalid provider policy")

    def as_dict(self) -> dict[str, Any]:
        return {"schema_version": self.schema_version, "provider_id": self.provider_id,
                "evidence_class": self.evidence_class,
                "confidence_default": self.confidence_default,
                "license_constraints": sorted(self.license_constraints),
                "attribution": self.attribution,
                "allowed_entity_types": sorted(self.allowed_entity_types),
                "normalization_rules": dict(sorted(self.normalization_rules.items()))}

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> "ProviderPolicy":
        if value.get("schema_version") != POLICY_SCHEMA:
            raise AcquisitionError("invalid provider policy schema")
        return cls(str(value.get("provider_id", "")), str(value.get("evidence_class", "")),
                   value.get("confidence_default", -1), tuple(value.get("license_constraints", ())),
                   str(value.get("attribution", "")), tuple(value.get("allowed_entity_types", ())),
                   value.get("normalization_rules", {}))


def dataset_identity(provider_id: str, provider_dataset_id: str, acquisition_version: str,
                     publication_date: str | None, snapshot_hash: str) -> dict[str, Any]:
    """Create an identity whose logical component is stable across identical imports."""
    if not all(isinstance(v, str) and v for v in
               (provider_id, provider_dataset_id, acquisition_version, snapshot_hash)):
        raise AcquisitionError("dataset identity fields must be non-empty strings")
    if len(snapshot_hash) != 64 or any(c not in "0123456789abcdef" for c in snapshot_hash):
        raise AcquisitionError("snapshot_hash must be a lowercase sha256 digest")
    if publication_date:
        try: date.fromisoformat(publication_date)
        except (TypeError, ValueError) as error: raise AcquisitionError("invalid publication_date") from error
    components = {"provider_id": provider_id, "provider_dataset_id": provider_dataset_id,
                  "acquisition_version": acquisition_version,
                  "publication_date": publication_date, "snapshot_hash": snapshot_hash}
    return {"schema_version": IDENTITY_SCHEMA, **components,
            "logical_dataset_identity": "dataset-" + _digest(components)}


def validate_pipeline(run: Mapping[str, Any], snapshots: Sequence[Mapping[str, Any]],
                      normalized: Sequence[Mapping[str, Any]], assertions: Sequence[Mapping[str, Any]],
                      policy: ProviderPolicy) -> dict[str, Any]:
    """Validate every boundary before review generation; errors fail closed."""
    errors, warnings = [], []
    if run.get("schema_version") != RUN_SCHEMA: errors.append("invalid acquisition run schema")
    if run.get("provider_id") != policy.provider_id: errors.append("run/provider policy identity mismatch")
    snapshot_ids = set()
    for item in snapshots:
        if item.get("schema_version") != SNAPSHOT_SCHEMA: errors.append("invalid snapshot schema")
        sid = item.get("snapshot_id")
        if not sid or sid in snapshot_ids: errors.append("invalid or duplicate snapshot identity")
        snapshot_ids.add(sid)
        if item.get("provider_id") != policy.provider_id: errors.append("invalid snapshot provenance")
        if item.get("checksum", {}).get("value") != sid: errors.append("snapshot identity/checksum mismatch")
    record_ids, source_keys = set(), set()
    for document in normalized:
        if document.get("schema_version") != NORMALIZED_SCHEMA: errors.append("invalid normalized schema")
        if document.get("provider_id") != policy.provider_id or document.get("raw_snapshot_id") not in snapshot_ids:
            errors.append("invalid normalized provenance")
        for record in document.get("records", []):
            rid = record.get("id"); key = (record.get("raw_snapshot_id"), record.get("source_record_id"))
            if not rid or rid in record_ids: errors.append("duplicate normalized entity")
            if key in source_keys: errors.append("conflicting source identifier")
            record_ids.add(rid); source_keys.add(key)
            if (record.get("schema_version") != NORMALIZED_SCHEMA or
                    not isinstance(record.get("source_values"), dict) or
                    not isinstance(record.get("unmapped_source_fields"), dict)):
                errors.append("malformed normalized record")
            if record.get("validation_errors"): errors.append("normalized record has validation errors")
            entity_type = record.get("unmapped_source_fields", {}).get("entity_type")
            if entity_type and entity_type not in policy.allowed_entity_types:
                errors.append("entity type forbidden by provider policy")
            if record.get("unmapped_source_fields"): warnings.append("normalized record retains unknown fields")
    assertion_ids = set()
    for assertion in assertions:
        if assertion.get("id") in assertion_ids: errors.append("duplicate candidate assertion")
        assertion_ids.add(assertion.get("id"))
        if (assertion.get("status") != "candidate" or assertion.get("source_id") != policy.provider_id or
                "raw_snapshot_id=" not in str(assertion.get("notes", ""))):
            errors.append("invalid assertion provenance")
    return {"valid": not errors, "errors": sorted(set(errors)), "warnings": sorted(set(warnings)),
            "counts": {"snapshots": len(snapshots), "normalized_records": len(record_ids),
                       "candidate_assertions": len(assertions)}}


def generate_reports(run: Mapping[str, Any], snapshots: Sequence[Mapping[str, Any]],
                     normalized: Sequence[Mapping[str, Any]], assertions: Sequence[Mapping[str, Any]],
                     validation: Mapping[str, Any], previous_assertions: Iterable[Mapping[str, Any]] = ()) -> dict[str, Any]:
    old = {(a.get("subject_id"), a.get("path")): a for a in previous_assertions}
    groups: dict[tuple[Any, Any], list[Mapping[str, Any]]] = {}
    for assertion in assertions: groups.setdefault((assertion.get("subject_id"), assertion.get("path")), []).append(assertion)
    conflicts = []
    for key, values in sorted(groups.items(), key=lambda item: str(item[0])):
        distinct = {_canonical(v.get("asserted_value")) for v in values}
        if len(distinct) > 1:
            conflicts.append({"subject_id": key[0], "path": key[1],
                              "assertion_ids": sorted(v["id"] for v in values),
                              "values": sorted((v.get("asserted_value") for v in values), key=lambda x: json.dumps(x, sort_keys=True))})
    changes = []
    for assertion in assertions:
        prior = old.get((assertion.get("subject_id"), assertion.get("path")))
        if prior and prior.get("asserted_value") != assertion.get("asserted_value"):
            changes.append({"subject_id": assertion["subject_id"], "path": assertion["path"],
                            "previous_value": prior.get("asserted_value"), "current_value": assertion.get("asserted_value")})
    unknowns = []
    for document in normalized:
        for record in document.get("records", []):
            for name, value in sorted(record.get("source_values", {}).items()):
                if value is None: unknowns.append({"record_id": record["id"], "field": name, "reason": "null_source_value"})
            for name in sorted(record.get("unmapped_source_fields", {})):
                if name not in {"id", "entity_type"}: unknowns.append({"record_id": record["id"], "field": name, "reason": "unmapped_source_field"})
    record_count = sum(len(d.get("records", [])) for d in normalized)
    fields = sum(len(r.get("source_values", {})) for d in normalized for r in d.get("records", []))
    known = fields - sum(1 for u in unknowns if u["reason"] == "null_source_value")
    return {"schema_version": REPORT_SCHEMA,
            "acquisition_summary": {"run_id": run.get("run_id"), "status": run.get("status"), "snapshot_count": len(snapshots)},
            "normalization_summary": {"document_count": len(normalized), "record_count": record_count},
            "assertion_summary": {"candidate_count": len(assertions)},
            "completeness_report": {"total_fields": fields, "known_fields": known,
                                    "unknown_fields": fields-known, "known_ratio": known / fields if fields else 0.0},
            "validation_report": dict(validation), "conflict_report": {"count": len(conflicts), "conflicts": conflicts},
            "unknown_field_report": {"count": len(unknowns), "unknowns": unknowns},
            "changed_values": sorted(changes, key=lambda x: (x["subject_id"], x["path"]))}


def build_review_package(run: Mapping[str, Any], snapshots: Sequence[Mapping[str, Any]],
                         normalized: Sequence[Mapping[str, Any]], assertions: Sequence[Mapping[str, Any]],
                         policy: ProviderPolicy, acquisition_version: str,
                         previous_assertions: Iterable[Mapping[str, Any]] = ()) -> dict[str, Any]:
    validation = validate_pipeline(run, snapshots, normalized, assertions, policy)
    if not validation["valid"]: raise AcquisitionError("pipeline validation failed: " + "; ".join(validation["errors"]))
    identities = [dataset_identity(policy.provider_id, str(s["dataset"]), acquisition_version,
                    (str(s["publication_timestamp"])[:10] if s.get("publication_timestamp") else None),
                    s["snapshot_id"]) for s in snapshots]
    reports = generate_reports(run, snapshots, normalized, assertions, validation, previous_assertions)
    recommendation = "hold" if (reports["conflict_report"]["count"] or
                                reports["unknown_field_report"]["count"] or validation["warnings"]) else "eligible_for_human_review"
    body = {"schema_version": REVIEW_SCHEMA, "acquisition_run": dict(run),
            "snapshot_lineage": sorted(identities, key=lambda x: x["logical_dataset_identity"]),
            "provider": policy.as_dict(), "candidate_assertions": sorted((dict(a) for a in assertions), key=lambda x: x["id"]),
            "detected_conflicts": reports["conflict_report"], "changed_values": reports["changed_values"],
            "unknown_values": reports["unknown_field_report"], "validation_warnings": validation["warnings"],
            "completeness_metrics": reports["completeness_report"],
            "evidence_summary": {"evidence_class": policy.evidence_class, "snapshot_count": len(snapshots),
                                 "assertion_count": len(assertions)},
            "promotion_recommendation": recommendation, "reports": reports}
    body["review_package_id"] = "review-" + _digest(body)
    validate_review_package(body)
    return body


def validate_review_package(package: Mapping[str, Any]) -> None:
    required = {"schema_version", "review_package_id", "acquisition_run", "snapshot_lineage", "provider",
                "candidate_assertions", "detected_conflicts", "changed_values", "unknown_values",
                "validation_warnings", "completeness_metrics", "evidence_summary", "promotion_recommendation", "reports"}
    if package.get("schema_version") != REVIEW_SCHEMA or not required.issubset(package):
        raise AcquisitionError("malformed or incomplete review package")
    unsigned = {k: v for k, v in package.items() if k != "review_package_id"}
    if package.get("review_package_id") != "review-" + _digest(unsigned):
        raise AcquisitionError("review package identity mismatch")


def write_json(path: Path | str, value: Mapping[str, Any]) -> None:
    target = Path(path); target.parent.mkdir(parents=True, exist_ok=True)
    content = _canonical(value)
    if target.exists() and target.read_bytes() != content: raise AcquisitionError(f"artifact already differs: {target}")
    target.write_bytes(content)
