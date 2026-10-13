"""Deterministic, fail-closed projection from canonical assertions to typed records."""
from __future__ import annotations

import hashlib
import json
import os
from copy import deepcopy
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Mapping

from repository.canonical import CanonicalRepository, CanonicalRepositoryError
from validation import SchemaValidationError, validate_document

SCHEMA_VERSION = "typed-canonical-projection-v1"


class ProjectionError(RuntimeError):
    """The requested projection could not be completed safely."""


class ProjectionValidationError(ProjectionError):
    """Canonical inputs cannot produce a complete typed repository."""


def _bytes(value: Any) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":"),
                       ensure_ascii=False) + "\n").encode()


def _digest(value: Any) -> str:
    return hashlib.sha256(_bytes(value)).hexdigest()


def _admission_digest(value: Any) -> str:
    """The production admission format hashes canonical JSON without a newline."""
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"),
                                    ensure_ascii=False).encode()).hexdigest()


def _retained_path(root: Path, relative: str) -> Path:
    path = Path(relative)
    destination = (root / path).resolve()
    if path.is_absolute() or ".." in path.parts or not destination.is_relative_to(root.resolve()):
        raise ProjectionValidationError("admission evidence path escapes data root")
    if not destination.is_file():
        raise ProjectionValidationError(f"retained admission evidence missing: {relative}")
    return destination


def _production_audit(root: Path, promotion_id: str) -> Mapping[str, Any]:
    """Resolve exactly one immutable audit in the existing configured audit tree."""
    matches = []
    for path in sorted((root / "audit").rglob("*.json")):
        retained = _retained_path(root, str(path.relative_to(root)))
        try:
            event = json.loads(retained.read_text())
        except json.JSONDecodeError:
            # Unrelated malformed files cannot satisfy this record's admission.
            continue
        if isinstance(event, Mapping) and event.get("promotion_id") == promotion_id:
            matches.append(event)
    if len(matches) != 1:
        raise ProjectionValidationError("production record needs exactly one retained admission audit")
    return matches[0]


def _historical_admission_records(root: Path, audit: Mapping[str, Any]) -> dict:
    """Reconstruct historical records from their original, digest-bound receipts.

    These are readers for two already completed admission formats, never promotion
    interfaces. No new record may claim these historical lifecycle identities.
    """
    from production_evidence import bounded_promotion as first
    from production_evidence import phase136_promotion as pilot

    promotion_id = audit.get("promotion_id")
    body = {key: value for key, value in audit.items() if key != "audit_digest"}
    if audit.get("result") != "succeeded" or audit.get("audit_digest") != _admission_digest(body):
        raise ProjectionValidationError("historical admission audit integrity failed")
    if promotion_id == first.PROMOTION_ID and audit.get("schema_version") == first.SCHEMA_VERSION:
        relative = (f"production_runs/{first.EVIDENCE_ID}/review_payloads/mb2/"
                    f"{first.BATCH_ID}.json")
        payload = json.loads(_retained_path(root, relative).read_text())
        ids = payload["candidate_ids"]
        if (ids != audit["promoted_entities"] or
                _admission_digest(ids) != first.EXPECTED_CANDIDATE_DIGEST or
                payload["candidate_id_digest"] != first.EXPECTED_CANDIDATE_DIGEST):
            raise ProjectionValidationError("historical candidate membership mismatch")
        for relative, digest in audit["review_artifact_digests"].items():
            if hashlib.sha256(_retained_path(root, relative).read_bytes()).hexdigest() != digest:
                raise ProjectionValidationError("historical review receipt integrity failed")
        lineage = _retained_path(root, f"production_runs/{first.EVIDENCE_ID}/lineage/source.json")
        if hashlib.sha256(lineage.read_bytes()).hexdigest() != audit["source_lineage_digest"]:
            raise ProjectionValidationError("historical source lineage integrity failed")
        records = {kind: {} for kind in first.ENTITY_COUNTS}
        candidates = payload["candidate_payloads"]
        if [row["candidate_identifier"] for row in candidates] != ids:
            raise ProjectionValidationError("historical payload correspondence mismatch")
        for candidate in candidates:
            kind = candidate["entity_type"]
            identifier = first._canonical_id(candidate)
            values = deepcopy(candidate["mapped_fields"])
            if kind == "printing":
                values["card_id"] = values.pop("card_reference").lower()
                values["set_id"] = values.pop("set_code").lower()
                values["finish_ids"] = values.pop("finishes")
            if identifier in records[kind]:
                raise ProjectionValidationError("duplicate historical admission identity")
            records[kind][identifier] = {
                "entity_type": kind, "values": values,
                "unknown_values": candidate["unknown_fields"],
                "confidence": candidate["confidence"], "uncertainty_state": "known",
                "evidence_references": [candidate["candidate_identifier"]],
                "dataset_identity": [candidate["source_dataset"]],
                "acquisition_lineage": [candidate["acquisition_metadata"]],
                "review_package_id": first.BATCH_ID, "promotion_id": first.PROMOTION_ID,
                "provenance": candidate["provenance"]}
        excluded = {"audit_digest", "action", "result", "promoted_entities",
                    "canonical_post_state_digest", "replay", "rollback", "preflight_digest"}
        preflight = {key: value for key, value in audit.items() if key not in excluded}
        preflight.update(candidate_membership=ids, canonical_records=records)
        if _admission_digest(preflight) != audit["preflight_digest"]:
            raise ProjectionValidationError("historical source-to-record binding failed")
        return records
    if (promotion_id == pilot.PROMOTION_ID and
            audit.get("schema_version") == "phase-136-bounded-promotion-audit-v1"):
        verified = pilot.verify_evidence(root)
        if verified["evidence_files"] != audit["evidence_files"]:
            raise ProjectionValidationError("historical pilot evidence receipt mismatch")
        records, candidates = {"printing": {}}, []
        for row in verified["source"]["pilot_printings"]:
            values = {"uuid": row["provider_printing_id"],
                      "card_id": row["provider_card_or_oracle_id"],
                      "set_id": row["set_code"].casefold(), "set_code": row["set_code"],
                      "set_name": row["set_name"], "collector_number": row["collector_number"],
                      "release_date": row["release_date"], "language": row["language"],
                      "finish_ids": row["finishes"], "rarity": row["rarity"],
                      "frame_or_treatment": row["frame_or_treatment"],
                      "promotional": row["promotional"], "reprint": row["reprint"],
                      "digital_or_paper": row["digital_or_paper"],
                      "provider_card_or_oracle_id": row["provider_card_or_oracle_id"],
                      "source_record_identity": row["source_record_identity"]}
            identifier = values["uuid"]
            candidate_id = "mtgjson:printing:" + identifier
            candidates.append({"candidate_id": candidate_id, "classification": "accepted",
                               "entity_type": "printing", "values": values})
            records["printing"][identifier] = {
                "entity_type": "printing", "values": values,
                "unknown_values": {key: {"status": "unknown"} for key in
                    ("promotional", "digital_or_paper") if values[key] == "unknown"},
                "confidence": 1.0, "uncertainty_state": "known",
                "evidence_references": [candidate_id], "dataset_identity": [pilot.RUN_ID],
                "acquisition_lineage": [{"acquisition_run_id": pilot.RUN_ID,
                    "source_sha256": verified["manifest"]["source_sha256"],
                    "normalized_projection_sha256": verified["manifest"]["normalized_projection_sha256"]}],
                "review_package_id": pilot.PROMOTION_ID, "promotion_id": pilot.PROMOTION_ID,
                "provenance": {"provider": "mtgjson",
                               "source_record_identity": values["source_record_identity"]}}
        candidates.sort(key=lambda row: row["candidate_id"])
        if (_admission_digest(candidates) != audit["candidate_digest"] or
                [row["values"]["uuid"] for row in candidates] != audit["promoted_printing_ids"] or
                any(audit["cards_reused"].get(row["card_name"]) != row["provider_card_or_oracle_id"]
                    for row in verified["source"]["pilot_printings"])):
            raise ProjectionValidationError("historical pilot candidate correspondence failed")
        return records
    raise ProjectionValidationError("unsupported production admission evidence format")


@dataclass(frozen=True, slots=True)
class ProjectionRule:
    entity_type: str
    required: tuple[str, ...]
    destination: Callable[[str], str]
    mapper: Callable[[str, Mapping[str, Any], tuple[Mapping[str, Any], ...]], dict[str, Any]]


class ProjectionRegistry:
    """Explicit, immutable-by-convention registry of approved entity mappings."""

    def __init__(self) -> None:
        rules = (
            ProjectionRule("card", ("name",), lambda i: f"cards/{i}/card.json", self._card),
            ProjectionRule("printing", ("card_id", "set_id", "collector_number", "language"),
                           lambda i: f"printings/{i}/printing.json", self._printing),
            ProjectionRule("product", ("game", "name", "product_type"),
                           lambda i: f"products/{i}/product.json", self._product),
            ProjectionRule("product_version", ("product_id", "name", "components"),
                           lambda i: f"product_versions/{i}.json", self._product_version),
            ProjectionRule("rarity", ("game_id", "name"), lambda i: f"rarities/{i}.json", self._taxonomy),
            ProjectionRule("finish", ("game_id", "name"), lambda i: f"finishes/{i}.json", self._taxonomy),
            ProjectionRule("treatment", ("game_id", "name"), lambda i: f"treatments/{i}.json", self._taxonomy),
        )
        self._rules = {rule.entity_type: rule for rule in rules}

    def get(self, entity_type: str) -> ProjectionRule:
        try: return self._rules[entity_type]
        except KeyError as error: raise ProjectionValidationError(
            f"unsupported canonical entity type: {entity_type}") from error

    def inspect(self) -> dict[str, Any]:
        return {"schema_version": SCHEMA_VERSION, "projections": [
            {"entity_type": x.entity_type, "required_assertions": list(x.required)}
            for x in self._rules.values()],
            "virtual_projections": ["set"], "field_projections": ["language"]}

    @staticmethod
    def _base(identifier, values, assertions):
        return {"id": identifier, "metadata": {}, "assertions": list(assertions), **deepcopy(values)}

    def _card(self, identifier, values, assertions):
        result = self._base(identifier, values, assertions)
        result.update(schema_version="v3", game=str(values.get("game", "magic")),
                      normalized_name=str(values.get("normalized_name", values["name"])).casefold(),
                      layout=str(values.get("layout", "normal")))
        return result

    def _printing(self, identifier, values, assertions):
        result = self._base(identifier, values, assertions); result["schema_version"] = "v3"
        if "rarity_id" in result: result["rarity"] = result.pop("rarity_id")
        for key, value in tuple(result.items()):
            if value is None and key not in {"id", "card_id", "set_id", "collector_number", "language"}:
                result[key] = {"status": "unknown", "assertion_ids": sorted(
                    x["id"] for x in assertions if x["path"] == f"/{key}")}
        return result

    def _product(self, identifier, values, assertions):
        return {"schema_version": "v2", "id": identifier, "game": values["game"],
                "name": values["name"], "product_type": values["product_type"],
                "lifecycle_status": values.get("lifecycle_status", "foundation"),
                "version_ids": list(values.get("version_ids", ())), "metadata": {},
                "provenance": self._provenance(assertions)}

    def _product_version(self, identifier, values, assertions):
        return {"schema_version": "v2", "id": identifier,
                "game": values.get("game", "magic"), "product_id": values["product_id"],
                "name": values["name"], "components": deepcopy(values["components"]),
                "metadata": {}, "provenance": self._provenance(assertions)}

    @staticmethod
    def _provenance(assertions):
        grouped = {}
        for item in assertions: grouped.setdefault(item["source_id"], []).append(item["path"].lstrip("/"))
        return [{"source_id": key, "field_paths": sorted(set(paths)),
                 "claim": "approved canonical assertions"} for key, paths in sorted(grouped.items())]

    def _taxonomy(self, identifier, values, assertions):
        return {"id": identifier, "game_id": values["game_id"], "name": values["name"],
                "metadata": {"source_assertion_ids": sorted(x["id"] for x in assertions)}}


class TypedCanonicalProjectionEngine:
    """Read approved canonical state and atomically materialize its typed projection."""

    def __init__(self, canonical_root: Path | str, typed_root: Path | str,
                 audit_root: Path | str, *, game: str = "magic",
                 registry: ProjectionRegistry | None = None) -> None:
        self.canonical_root, self.typed_root = Path(canonical_root), Path(typed_root)
        self.audit_root, self.game = Path(audit_root), game
        self.registry = registry or ProjectionRegistry()
        if self.audit_root.resolve().is_relative_to(self.typed_root.resolve()):
            raise ProjectionError("projection audits must be outside the typed repository")

    def inspect(self, projection_id: str | None = None) -> Any:
        if projection_id is None:
            audits = [json.loads(path.read_text()) for path in self.audit_root.glob("*.json")]
            return {**self.registry.inspect(), "audits": sorted(audits, key=lambda x: x["projection_id"])}
        path = self.audit_root / f"{projection_id}.json"
        if not path.exists(): raise ProjectionError("projection audit not found")
        return json.loads(path.read_text())

    def validate(self) -> dict[str, Any]:
        checks: list[dict[str, Any]] = []
        def add(name, valid, detail=""): checks.append(
            {"name": name, "valid": bool(valid), "detail": detail})
        try: state = json.loads((self.canonical_root / "state.json").read_text())
        except (OSError, json.JSONDecodeError) as error:
            return {"schema_version": SCHEMA_VERSION, "valid": False,
                    "checks": [{"name": "canonical_state", "valid": False, "detail": str(error)}]}
        if not isinstance(state, Mapping):
            return {"schema_version": SCHEMA_VERSION, "valid": False,
                    "checks": [{"name": "canonical_state", "valid": False,
                                "detail": "canonical state must be an entity mapping"}]}
        records, seen_paths, seen_assertions = {}, set(), set()
        admission_cache: dict[str, tuple[dict, str]] = {}
        alias_count = 0
        production_count = 0
        historical_finish_gaps = []
        for kind, entities in sorted(state.items()):
            if not isinstance(entities, Mapping): add("lifecycle_state", False, f"{kind} is not a mapping"); continue
            for identifier, record in sorted(entities.items()):
                if not isinstance(record, Mapping):
                    add("lifecycle_state", False, f"{identifier} is not a record"); continue
                values = record.get("values", {}); references = record.get("evidence_references", [])
                if not isinstance(values, Mapping):
                    add("required_assertions", False, f"{identifier}: values is not a mapping"); continue
                # Production adapters preserve flat provider fields and references
                # to whole reviewed rows. They are not slash-path assertion records.
                if kind == "identifier" or (values and not any(str(path).startswith("/") for path in values)):
                    if kind not in {"card", "printing", "finish", "identifier"}:
                        add("supported_combination", False, f"unsupported production entity type: {kind}")
                        continue
                    path = f"production:{kind}:{identifier}"
                    records[path] = (None, identifier, record)
                    alias_count += kind == "identifier"
                    production_count += 1
                    promotion_id = record.get("promotion_id", "")
                    if not isinstance(promotion_id, str):
                        promotion_id = ""
                    if promotion_id not in admission_cache:
                        try:
                            audit = _production_audit(self.canonical_root.parent, promotion_id)
                            if audit.get("canonical_record_digests") is not None:
                                from production_evidence.automatic_updates import validate_admission_audit
                                validate_admission_audit(self.canonical_root.parent, audit)
                                digests = audit["canonical_record_digests"]
                            else:
                                admitted = _historical_admission_records(self.canonical_root.parent, audit)
                                digests = {entity_type: {key: _admission_digest(item) for key, item in rows.items()}
                                           for entity_type, rows in admitted.items()}
                            admission_cache[promotion_id] = (digests, "")
                        except (OSError, ValueError, KeyError, TypeError, RuntimeError, ImportError) as error:
                            admission_cache[promotion_id] = ({}, str(error))
                    digests, error = admission_cache[promotion_id]
                    bound = digests.get(kind, {}).get(identifier) == _admission_digest(record)
                    add("admission_evidence", bound, f"{identifier}: {error or 'exact retained admission record'}")
                    add("lifecycle_state", bool(promotion_id) and record.get("entity_type") == kind
                        and not record.get("superseded_status"), identifier)
                    required = {"card": ("name",), "printing": ("card_id", "set_id", "collector_number", "language", "finish_ids"),
                                "finish": ("value",), "identifier": ("namespace", "value", "printing_uuid")}[kind]
                    missing = sorted(field for field in required if field not in values)
                    add("required_assertions", not missing, f"{identifier}: {', '.join(missing)}")
                    scalar_fields = tuple(field for field in required if field != "finish_ids")
                    add("required_value_types", all(isinstance(values.get(field), str) and values[field]
                        for field in scalar_fields), identifier)
                    if kind == "card":
                        add("canonical_identity", values.get("card_reference", identifier) == identifier, identifier)
                    elif kind == "printing":
                        add("canonical_identity", values.get("uuid", identifier) == identifier, identifier)
                        dependency = (isinstance(values.get("card_id"), str) and
                            values.get("card_id") in state.get("card", {}) and
                            isinstance(values.get("finish_ids"), list) and bool(values.get("finish_ids")))
                        add("dependency_integrity", dependency, identifier)
                        finishes = values.get("finish_ids", [])
                        missing_finishes = sorted(set(finishes) - set(state.get("finish", {}))) \
                            if isinstance(finishes, list) and all(isinstance(x, str) for x in finishes) else ["invalid finish labels"]
                        # Phase 136 admitted source finish labels such as signed
                        # and etched without corresponding typed Finish entities.
                        # The exact legacy bytes may be read, but are not claimed
                        # to be a complete typed projection. New deltas receive no
                        # such compatibility exception.
                        historical_labels = (bound and
                            promotion_id == "phase-136-mtgjson-pilot-30786023976-1")
                        add("finish_dependency_integrity", not missing_finishes or historical_labels, identifier)
                        if missing_finishes and historical_labels:
                            historical_finish_gaps.append({"printing_id": identifier,
                                "promotion_id": promotion_id, "provider_finish_labels": missing_finishes,
                                "status": "retained_label_without_canonical_finish",
                                "typed_materialization": "blocked"})
                    elif kind == "finish":
                        add("canonical_identity", values.get("value") == identifier, identifier)
                    else:
                        add("dependency_integrity", isinstance(values.get("printing_uuid"), str)
                            and values.get("printing_uuid") in state.get("printing", {}), identifier)
                    valid_references = isinstance(references, list) and bool(references) and all(
                        isinstance(reference, str) for reference in references)
                    add("duplicate_assertions", valid_references
                        and len(references) == len(set(references))
                        and not seen_assertions.intersection(references), identifier)
                    if valid_references: seen_assertions.update(references)
                    continue
                try: rule = self.registry.get(kind)
                except ProjectionValidationError as error:
                    add("supported_combination", False, str(error)); continue
                fields = {str(path).lstrip("/") for path in values}
                lifecycle = (record.get("canonical_identifier") == identifier and record.get("entity_type") == kind
                             and record.get("promotion_id") and not record.get("superseded_status"))
                add("lifecycle_state", lifecycle, identifier)
                missing = sorted(name for name in rule.required if name not in fields)
                add("required_assertions", not missing, f"{identifier}: {', '.join(missing)}")
                path = rule.destination(identifier)
                add("duplicate_projection", path not in seen_paths, path); seen_paths.add(path)
                duplicate_refs = len(references) != len(set(references)) or bool(seen_assertions.intersection(references))
                add("duplicate_assertions", not duplicate_refs, identifier); seen_assertions.update(references)
                records[path] = (rule, identifier, record)
        add("projection_completeness", bool(records), "canonical state must contain supported entities")
        valid = all(x["valid"] for x in checks)
        result = {"schema_version": SCHEMA_VERSION, "valid": valid, "checks": checks,
                  "entity_count": len(records), "canonical_state_digest": _digest(state)}
        if production_count:
            result.update(validation_scope="production-read-and-admission-integrity",
                typed_entity_count=len(records) - alias_count,
                identifier_alias_count=alias_count, production_record_count=production_count,
                fully_dependency_closed=valid and not historical_finish_gaps,
                typed_materialization_ready=False,
                historical_unresolved_finish_references=historical_finish_gaps)
        # Existing assertion-path validation/audit serialization remains byte
        # compatible; production compatibility diagnostics do not repin history.
        return result

    def project(self, timestamp: str) -> dict[str, Any]:
        validation = self.validate()
        if not validation["valid"]: raise ProjectionValidationError("projection validation failed: " + ", ".join(
            x["name"] for x in validation["checks"] if not x["valid"]))
        state = json.loads((self.canonical_root / "state.json").read_text())
        if any(record.get("values") and not any(str(path).startswith("/")
                   for path in record["values"])
               for rows in state.values() for record in rows.values()):
            raise ProjectionValidationError("production record typed materialization is unsupported: "
                "retained whole-row evidence is not v3 field assertions; query aliases remain in canonical state")
        source_assertions = self._approved_assertions(state)
        output: dict[str, Mapping[str, Any]] = {}
        source_ids, entity_ids, assertion_ids = set(), [], set()
        for kind, entities in sorted(state.items()):
            rule = self.registry.get(kind)
            for identifier, record in sorted(entities.items()):
                assertions = []
                for assertion_id in record["evidence_references"]:
                    assertion = deepcopy(source_assertions[assertion_id]); assertion["status"] = "promoted"
                    assertion.pop("schema_version", None)
                    if kind == "printing" and assertion.get("path") == "/rarity_id":
                        assertion["path"] = "/rarity"
                    assertions.append(assertion); source_ids.add(assertion["source_id"]); assertion_ids.add(assertion_id)
                values = {str(path).lstrip("/"): deepcopy(value) for path, value in record["values"].items()}
                document = rule.mapper(identifier, values, tuple(assertions))
                document["metadata"] = {"projection_schema_version": SCHEMA_VERSION,
                    "source_promotion_id": record["promotion_id"],
                    "source_assertion_ids": sorted(record["evidence_references"])}
                self._add_derived_assertions(document, assertions)
                output[rule.destination(identifier)] = document; entity_ids.append(identifier)
        self._add_sources(output, source_ids, source_assertions)
        identity = {"schema_version": SCHEMA_VERSION,
                    "canonical_state_digest": validation["canonical_state_digest"], "game": self.game}
        projection_id = "projection-" + _digest(identity)
        audit = {**identity, "projection_id": projection_id, "timestamp": timestamp,
                 "source_assertion_ids": sorted(assertion_ids), "projected_entity_ids": sorted(entity_ids),
                 "validation_result": validation, "typed_repository_digest": _digest(output)}
        existing = self.audit_root / f"{projection_id}.json"
        if existing.exists():
            prior = json.loads(existing.read_text())
            if {k: v for k, v in prior.items() if k != "timestamp"} != {k: v for k, v in audit.items() if k != "timestamp"}:
                raise ProjectionError("projection identity collision")
            return prior
        try: CanonicalRepository.apply_import(self.game, output, games_root=self.typed_root)
        except (CanonicalRepositoryError, SchemaValidationError, ValueError) as error:
            raise ProjectionValidationError(f"typed repository validation failed: {error}") from error
        self.audit_root.mkdir(parents=True, exist_ok=True)
        descriptor = os.open(existing, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644)
        with os.fdopen(descriptor, "wb") as stream: stream.write(_bytes(audit))
        return audit

    def _approved_assertions(self, state):
        wanted = {identifier for values in state.values() for record in values.values()
                  for identifier in record.get("evidence_references", [])}
        found = {}
        for path in sorted(self.canonical_root.parent.joinpath("audit").glob("*.json")):
            event = json.loads(path.read_text())
            if not event.get("validation_results", {}).get("valid"): continue
            for assertion in event.get("review_package", {}).get("candidate_assertions", []):
                if assertion.get("id") in wanted: found[assertion["id"]] = assertion
        missing = sorted(wanted - set(found))
        if missing: raise ProjectionValidationError("approved source assertions unavailable: " + ", ".join(missing))
        return found

    @staticmethod
    def _add_derived_assertions(document, assertions):
        if "assertions" not in document:
            return
        covered = {x["path"].lstrip("/").split("/", 1)[0] for x in assertions}
        required = set(document) - {"schema_version", "metadata", "assertions"}
        template = assertions[0] if assertions else None
        for field in sorted(required - covered):
            if template is None: continue
            derived = deepcopy(template); derived["id"] = f"{template['id']}.projection.{field.replace('_', '-')}"
            derived["path"], derived["asserted_value"], derived["status"] = f"/{field}", deepcopy(document[field]), "promoted"
            document["assertions"].append(derived)

    @staticmethod
    def _add_sources(output, source_ids, assertions):
        for source_id in sorted(source_ids):
            items = [x for x in assertions.values() if x["source_id"] == source_id]
            date = min(x["timestamp"][:10] for x in items)
            output[f"sources/{source_id}.json"] = {"schema_version": "v1", "id": source_id,
                "title": f"Canonical assertion source {source_id}", "source_classification": "internal",
                "provider": source_id, "source_location": f"canonical-assertions:{source_id}",
                "access_date": date, "verification_status": "confirmed",
                "claims": sorted(x["id"] for x in items), "record_version": SCHEMA_VERSION}
