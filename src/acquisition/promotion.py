"""Fail-closed promotion from reviewed knowledge into versioned canonical state."""
from __future__ import annotations

import hashlib
import json
import os
import tempfile
from copy import deepcopy
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Mapping, Sequence

from validation import SchemaValidationError, validate_document

from .framework import AcquisitionError
from .knowledge import ProviderPolicy, _canonical, dataset_identity, validate_review_package

PROMOTION_SCHEMA = "canonical-promotion-event-v1"
AUDIT_SCHEMA = "canonical-promotion-audit-v1"


class PromotionError(AcquisitionError):
    """A promotion gate failed; canonical state was not changed."""


@dataclass(frozen=True, slots=True)
class PromotionDecision:
    actor: str
    timestamp: str
    approved: bool = True
    allow_unknowns: bool = False
    reason: str = "reviewed"

    def __post_init__(self) -> None:
        if not self.actor.strip() or not self.timestamp or not self.reason.strip():
            raise PromotionError("promotion decision requires actor, timestamp, and reason")
        try: parsed = datetime.fromisoformat(self.timestamp.replace("Z", "+00:00"))
        except ValueError as error: raise PromotionError("promotion timestamp must be ISO 8601") from error
        if parsed.tzinfo is None: raise PromotionError("promotion timestamp must include a timezone")

    def as_dict(self) -> dict[str, Any]:
        return {"actor": self.actor, "timestamp": self.timestamp, "approved": self.approved,
                "allow_unknowns": self.allow_unknowns, "reason": self.reason}


def _digest(value: Any) -> str:
    return hashlib.sha256(_canonical(value)).hexdigest()


def _write_once(path: Path, value: Mapping[str, Any]) -> None:
    content = _canonical(value); path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        if path.read_bytes() != content: raise PromotionError(f"immutable artifact differs: {path}")
        return
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644)
    with os.fdopen(descriptor, "wb") as stream: stream.write(content)


def _replace(path: Path, value: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(dir=path.parent, prefix=".promotion-")
    try:
        with os.fdopen(descriptor, "wb") as stream: stream.write(_canonical(value)); stream.flush(); os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary): os.unlink(temporary)


class CanonicalPromotionEngine:
    """The sole writer for the knowledge canonical repository and its audit history."""

    def __init__(self, root: Path | str, audit_root: Path | str | None = None) -> None:
        self.root = Path(root); self.audit_root = Path(audit_root) if audit_root else self.root.parent / "audit"
        if self.audit_root.resolve().is_relative_to(self.root.resolve()):
            raise PromotionError("audit storage must be outside canonical storage")

    def validate(self, package: Mapping[str, Any], policy: ProviderPolicy,
                 decision: PromotionDecision) -> dict[str, Any]:
        checks: list[dict[str, Any]] = []
        def check(name: str, valid: bool, detail: str = "") -> None:
            checks.append({"name": name, "valid": bool(valid), "detail": detail})
        try: validate_review_package(package); check("review_package", True)
        except (AcquisitionError, SchemaValidationError) as error: check("review_package", False, str(error))
        try: validate_document(package, "knowledge-review-package", "v1"); check("schema", True)
        except Exception as error: check("schema", False, str(error))
        embedded = package.get("provider", {})
        check("provider_policy", embedded == policy.as_dict(), "embedded policy must equal supplied policy")
        lineage = package.get("snapshot_lineage", [])
        identities_valid = bool(lineage)
        for item in lineage:
            try:
                expected = dataset_identity(item["provider_id"], item["provider_dataset_id"],
                    item["acquisition_version"], item.get("publication_date"), item["snapshot_hash"])
                identities_valid = identities_valid and item == expected
            except (KeyError, TypeError, AcquisitionError): identities_valid = False
        check("dataset_identity", identities_valid and len({_digest(x) for x in lineage}) == len(lineage))
        checksums = [x.get("snapshot_hash") for x in lineage if isinstance(x, Mapping)]
        check("integrity", len(checksums) == len(lineage) and all(isinstance(x, str) and len(x) == 64 for x in checksums))
        assertions = package.get("candidate_assertions", [])
        ids = [x.get("id") for x in assertions if isinstance(x, Mapping)]
        check("duplicates", len(ids) == len(assertions) and len(ids) == len(set(ids)))
        check("conflicts", package.get("detected_conflicts", {}).get("count") == 0)
        unknown_count = package.get("unknown_values", {}).get("count", 0)
        check("unknown_values", unknown_count == 0 or decision.allow_unknowns,
              "unknowns require an explicit reviewed decision")
        metrics = package.get("completeness_metrics", {})
        complete = (metrics.get("total_fields", 0) == metrics.get("known_fields", 0) + metrics.get("unknown_fields", 0))
        check("completeness", complete)
        check("assertion_policy", all(a.get("source_id") == policy.provider_id and
              a.get("evidence_class") == policy.evidence_class and a.get("status") == "candidate" for a in assertions))
        unsigned = {k: v for k, v in package.items() if k != "review_package_id"}
        check("reproducibility", package.get("review_package_id") == "review-" + _digest(unsigned))
        check("decision", decision.approved)
        return {"valid": all(x["valid"] for x in checks), "checks": checks}

    def promote(self, package: Mapping[str, Any], policy: ProviderPolicy,
                decision: PromotionDecision) -> dict[str, Any]:
        validation = self.validate(package, policy, decision)
        identity = {"action": "promote", "review_package_id": package.get("review_package_id"),
                    "decision": decision.as_dict(), "policy": policy.as_dict()}
        promotion_id = "promotion-" + _digest(identity)
        existing = self._audit(promotion_id, required=False)
        if existing is not None:
            if existing.get("validation_results", {}).get("valid"): return existing
            raise PromotionError("promotion validation previously failed")
        if not validation["valid"]:
            rejected = sorted({str(a.get("subject_id")) for a in package.get("candidate_assertions", [])
                               if isinstance(a, Mapping) and a.get("subject_id")})
            failure = {"schema_version": AUDIT_SCHEMA, "promotion_id": promotion_id, "action": "promote",
                "actor": decision.actor, "timestamp": decision.timestamp, "inputs": identity,
                "review_package": deepcopy(package), "validation_results": validation,
                "promoted_entities": [], "rejected_entities": rejected,
                "warnings": deepcopy(package.get("validation_warnings", [])),
                "conflicts": deepcopy(package.get("detected_conflicts", {}).get("conflicts", [])),
                "canonical_state_digest": _digest(self._state())}
            _write_once(self.audit_root / f"{promotion_id}.json", failure)
            raise PromotionError("promotion validation failed: " + ", ".join(
                x["name"] for x in validation["checks"] if not x["valid"]))
        grouped: dict[str, list[Mapping[str, Any]]] = {}
        for assertion in package["candidate_assertions"]:
            grouped.setdefault(assertion["subject_id"], []).append(assertion)
        entities, conflicts = [], []
        for entity_id, assertions in sorted(grouped.items()):
            values: dict[str, Any] = {}
            for assertion in sorted(assertions, key=lambda x: x["path"]):
                if assertion["path"] in values and values[assertion["path"]] != assertion["asserted_value"]:
                    conflicts.append({"entity_id": entity_id, "path": assertion["path"]})
                values[assertion["path"]] = deepcopy(assertion["asserted_value"])
            entity_type = next((r.get("unmapped_source_fields", {}).get("entity_type")
                                for d in package["reports"].get("normalized_documents", []) for r in d.get("records", [])
                                if r.get("source_record_id") == entity_id), None)
            # Review packages v1 do not embed normalized documents; policy-constrained inference is deterministic.
            entity_type = entity_type or ("printing" if "card_id" in {p.lstrip('/') for p in values} else "card")
            if entity_type not in policy.allowed_entity_types: conflicts.append({"entity_id": entity_id, "path": "/entity_type"})
            entities.append((entity_type, entity_id, values, assertions))
        if conflicts: raise PromotionError("conflicting assertions cannot be promoted")
        records = []
        for entity_type, entity_id, values, assertions in entities:
            previous = self.current(entity_type, entity_id, required=False)
            if previous and previous["values"] == values and previous["review_package_id"] == package["review_package_id"]:
                records.append(previous); continue
            version = {"schema_version": "canonical-knowledge-record-v1", "canonical_identifier": entity_id,
                "entity_type": entity_type, "promotion_timestamp": decision.timestamp, "promotion_id": promotion_id,
                "review_package_id": package["review_package_id"], "dataset_identity": deepcopy(package["snapshot_lineage"]),
                "acquisition_lineage": deepcopy(package["acquisition_run"]),
                "evidence_references": sorted(a["id"] for a in assertions),
                "confidence": min(a["confidence"] for a in assertions),
                "uncertainty_state": "unknowns_reviewed" if package["unknown_values"]["count"] else "known",
                "superseded_status": False, "replaces": previous["promotion_id"] if previous else None,
                "values": values}
            _write_once(self.root / "versions" / entity_type / entity_id / f"{promotion_id}.json", version)
            records.append(version)
        state = self._state(); updated = deepcopy(state)
        for record in records: updated.setdefault(record["entity_type"], {})[record["canonical_identifier"]] = record
        audit = {"schema_version": AUDIT_SCHEMA, "promotion_id": promotion_id, "action": "promote",
                 "actor": decision.actor, "timestamp": decision.timestamp, "inputs": identity,
                 "review_package": deepcopy(package), "validation_results": validation,
                 "promoted_entities": [r["canonical_identifier"] for r in records], "rejected_entities": [],
                 "warnings": deepcopy(package["validation_warnings"]), "conflicts": conflicts,
                 "canonical_state_digest": _digest(updated)}
        _write_once(self.audit_root / f"{promotion_id}.json", audit); _replace(self.root / "state.json", updated)
        return audit

    def rollback(self, promotion_id: str, decision: PromotionDecision) -> dict[str, Any]:
        source = self._audit(promotion_id); identity = {"action": "rollback", "source_promotion_id": promotion_id,
                                                        "decision": decision.as_dict()}
        rollback_id = "promotion-" + _digest(identity)
        existing = self._audit(rollback_id, required=False)
        if existing: return existing
        if not decision.approved or source["action"] != "promote": raise PromotionError("rollback requires an approved promotion")
        state = self._state(); updated = deepcopy(state); restored = []
        for entity_id in source["promoted_entities"]:
            matches = [(kind, value) for kind, values in state.items() for key, value in values.items()
                       if key == entity_id and value["promotion_id"] == promotion_id]
            if len(matches) != 1: raise PromotionError("canonical state changed; rollback refused")
            kind, current = matches[0]; prior_id = current.get("replaces")
            if prior_id:
                prior = json.loads((self.root / "versions" / kind / entity_id / f"{prior_id}.json").read_text())
                compensation = dict(prior, promotion_id=rollback_id, promotion_timestamp=decision.timestamp,
                                    replaces=promotion_id, superseded_status=False)
                _write_once(self.root / "versions" / kind / entity_id / f"{rollback_id}.json", compensation)
                updated[kind][entity_id] = compensation; restored.append(entity_id)
            else:
                updated[kind].pop(entity_id); restored.append(entity_id)
        audit = {"schema_version": AUDIT_SCHEMA, "promotion_id": rollback_id, "action": "rollback",
                 "actor": decision.actor, "timestamp": decision.timestamp, "inputs": identity,
                 "review_package": source["review_package"], "validation_results": {"valid": True, "checks": []},
                 "promoted_entities": restored, "rejected_entities": [], "warnings": [], "conflicts": [],
                 "canonical_state_digest": _digest(updated)}
        _write_once(self.audit_root / f"{rollback_id}.json", audit); _replace(self.root / "state.json", updated)
        return audit

    def replay(self, audits: Sequence[Mapping[str, Any]] | None = None) -> dict[str, Any]:
        events = list(audits) if audits is not None else [json.loads(p.read_text()) for p in self.audit_root.glob("*.json")]
        events.sort(key=lambda x: (x["timestamp"], x["promotion_id"]))
        state: dict[str, Any] = {}
        for event in events:
            if not event.get("validation_results", {}).get("valid"):
                continue
            if event["action"] == "promote":
                for entity_id in event["promoted_entities"]:
                    candidates = list(self.root.glob(f"versions/*/{entity_id}/{event['promotion_id']}.json"))
                    if len(candidates) != 1: raise PromotionError("replay version missing or ambiguous")
                    record = json.loads(candidates[0].read_text()); state.setdefault(record["entity_type"], {})[entity_id] = record
            else:
                source = event["inputs"]["source_promotion_id"]
                for entity_id in event["promoted_entities"]:
                    candidates = list(self.root.glob(f"versions/*/{entity_id}/{event['promotion_id']}.json"))
                    if candidates:
                        record = json.loads(candidates[0].read_text()); state.setdefault(record["entity_type"], {})[entity_id] = record
                    else:
                        for values in state.values():
                            if entity_id in values and values[entity_id]["promotion_id"] == source: values.pop(entity_id)
            if _digest(state) != event["canonical_state_digest"]: raise PromotionError("replay state digest mismatch")
        return state

    def audit(self, promotion_id: str | None = None) -> Any:
        return self._audit(promotion_id) if promotion_id else sorted(
            (json.loads(p.read_text()) for p in self.audit_root.glob("*.json")), key=lambda x: (x["timestamp"], x["promotion_id"]))

    def history(self, entity_type: str, entity_id: str) -> list[dict[str, Any]]:
        return [json.loads(p.read_text()) for p in sorted((self.root / "versions" / entity_type / entity_id).glob("*.json"))]

    def current(self, entity_type: str, entity_id: str, required: bool = True) -> dict[str, Any] | None:
        value = self._state().get(entity_type, {}).get(entity_id)
        if value is None and required: raise PromotionError("canonical entity not found")
        return deepcopy(value)

    def _state(self) -> dict[str, Any]:
        path = self.root / "state.json"
        return json.loads(path.read_text()) if path.exists() else {}

    def _audit(self, promotion_id: str | None, required: bool = True) -> dict[str, Any] | None:
        if not promotion_id: raise PromotionError("promotion id required")
        path = self.audit_root / f"{promotion_id}.json"
        if not path.exists():
            if required: raise PromotionError("audit event not found")
            return None
        return json.loads(path.read_text())
