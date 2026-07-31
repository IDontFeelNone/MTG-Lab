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
        records, seen_paths, seen_assertions = {}, set(), set()
        for kind, entities in sorted(state.items()):
            if not isinstance(entities, Mapping): add("lifecycle_state", False, f"{kind} is not a mapping"); continue
            try: rule = self.registry.get(kind)
            except ProjectionValidationError as error: add("supported_combination", False, str(error)); continue
            for identifier, record in sorted(entities.items()):
                values = record.get("values", {}); references = record.get("evidence_references", [])
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
        return {"schema_version": SCHEMA_VERSION, "valid": valid, "checks": checks,
                "entity_count": len(records), "canonical_state_digest": _digest(state)}

    def project(self, timestamp: str) -> dict[str, Any]:
        validation = self.validate()
        if not validation["valid"]: raise ProjectionValidationError("projection validation failed: " + ", ".join(
            x["name"] for x in validation["checks"] if not x["valid"]))
        state = json.loads((self.canonical_root / "state.json").read_text())
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
