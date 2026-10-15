"""Deterministic, provider-neutral queries over canonical repository state."""
from __future__ import annotations

import hashlib
import json
import unicodedata
from dataclasses import asdict, dataclass, is_dataclass
from pathlib import Path
from typing import Any, Iterable, Mapping

from repository.canonical import CanonicalRepository


class QueryError(ValueError):
    """A query is invalid or has no unique result."""


def _plain(value: Any) -> Any:
    if is_dataclass(value):
        return _plain(asdict(value))
    if isinstance(value, Mapping):
        return {str(k): _plain(v) for k, v in sorted(value.items(), key=lambda x: str(x[0]))}
    if isinstance(value, (tuple, list)):
        return [_plain(v) for v in value]
    return value


def normalize_name(value: str) -> str:
    """Return the contract's locale-independent name comparison key."""
    return " ".join(unicodedata.normalize("NFKC", value).casefold().split())


@dataclass(frozen=True)
class QueryResult:
    """Storage-independent result envelope shared by every future consumer."""

    canonical_identity: str
    entity_type: str
    canonical_values: Mapping[str, Any]
    provenance_summary: Mapping[str, Any]
    confidence: float | None
    uncertainty: str
    supersession_state: str

    def as_dict(self) -> dict[str, Any]:
        return _plain(asdict(self))


@dataclass(frozen=True)
class QuerySnapshot:
    """A content-addressed, storage-independent canonical query snapshot."""

    snapshot_id: str
    game: str
    entities: tuple[QueryResult, ...]

    def as_dict(self) -> dict[str, Any]:
        return {"snapshot_id": self.snapshot_id, "game": self.game,
                "entities": [item.as_dict() for item in self.entities]}


class CanonicalQueryEngine:
    """Read-only facade; downstream callers do not receive repository objects."""

    def __init__(self, game: str = "magic", *, games_root: Path | None = None,
                 data_root: Path | None = None, _read_inventory=None) -> None:
        self._catalog_attachment = None
        self._read_inventory = _read_inventory
        self.game = game
        self.games_root = Path(games_root) if games_root else Path(__file__).resolve().parents[2] / "data/canonical/games"
        self.data_root = Path(data_root) if data_root else self.games_root.parents[2]
        repository_options = ({"read_inventory": _read_inventory}
                              if _read_inventory is not None else {})
        self._repository = CanonicalRepository(game, games_root=self.games_root,
                                               **repository_options)
        self._raw = self._load_raw()
        self._results = tuple(sorted(self._build_results(), key=lambda x: (x.entity_type, x.canonical_identity)))

    @classmethod
    def from_attachment(cls, attachment) -> CanonicalQueryEngine:
        """Read one verified attachment without changing legacy query identities."""
        from repository.snapshots import LegacyPublicAttachment, SnapshotAttachment, SnapshotError
        from repository.legacy_profile import LegacyCompatibilityAttachment

        if not isinstance(attachment, (SnapshotAttachment, LegacyPublicAttachment,
                                       LegacyCompatibilityAttachment)):
            raise SnapshotError("verified catalog attachment required")
        attachment.verify_unchanged()
        bounded = isinstance(attachment, LegacyCompatibilityAttachment)
        try:
            engine = cls(attachment.game, games_root=attachment.games_root,
                         data_root=attachment.data_root,
                         _read_inventory=attachment if bounded else None)
        except SnapshotError:
            raise
        except (ValueError, OSError, KeyError, TypeError):
            if not bounded:
                raise
            # Legacy loader exceptions can contain absolute paths or source values.
            # The bounded attachment reports a safe category rather than that text.
            raise SnapshotError("selected canonical catalog is invalid",
                                code="invalid_catalog") from None
        attachment.verify_unchanged()
        engine._catalog_attachment = attachment
        if bounded:
            attachment.validate_query(engine.snapshot())
        return engine

    def require_capability(self, name: str) -> None:
        """Reject excluded capabilities before any attachment or evidence reads.

        Existing unrestricted readers retain their existing API surface. An explicit
        bounded attachment supplies the capability policy; it cannot be upgraded by
        a query request.
        """
        from repository.legacy_profile import LegacyCompatibilityAttachment

        if isinstance(self._catalog_attachment, LegacyCompatibilityAttachment):
            self._catalog_attachment.require_capability(name)
        elif self._read_inventory is not None:
            self._read_inventory.require_capability(name)

    def _paths(self, root: Path, pattern: str) -> tuple[Path, ...]:
        if self._read_inventory is not None:
            return self._read_inventory.paths(root, pattern)
        return tuple(sorted(root.glob(pattern)))

    def _read_json(self, path: Path):
        if self._read_inventory is not None:
            return self._read_inventory.read_json(path)
        return json.loads(path.read_text())

    def _verify_attachment(self) -> None:
        if self._catalog_attachment is not None:
            from repository.snapshots import SnapshotError

            attachment = self._catalog_attachment
            from repository.legacy_profile import LegacyCompatibilityAttachment

            if (isinstance(attachment, LegacyCompatibilityAttachment)
                    and self._read_inventory is not attachment):
                raise SnapshotError("catalog attachment read inventory changed", code="scope_changed")
            attachment.verify_unchanged()
            if (self.game != attachment.game
                    or self.data_root.resolve() != attachment.data_root.resolve()
                    or self.games_root.resolve() != attachment.games_root.resolve()):
                raise SnapshotError("catalog attachment scope changed")

    @property
    def catalog_binding(self) -> dict[str, Any] | None:
        """Outer attachment identity, separate from the existing query snapshot."""
        self._verify_attachment()
        return self._catalog_attachment.binding if self._catalog_attachment is not None else None

    def snapshot(self) -> QuerySnapshot:
        """Return all query results and their deterministic content identity."""
        self._verify_attachment()
        payload = json.dumps([item.as_dict() for item in self._results], sort_keys=True,
                             separators=(",", ":"), ensure_ascii=False).encode()
        self._verify_attachment()
        return QuerySnapshot("sha256:" + hashlib.sha256(payload).hexdigest(), self.game,
                             self._results)

    def entities(self, *, canonical_id: str | None = None, provider_id: str | None = None,
                 external_id: str | None = None, entity_type: str | None = None,
                 card_name: str | None = None, normalized_name: str | None = None,
                 printing_id: str | None = None, set_id: str | None = None) -> tuple[QueryResult, ...]:
        """Retrieve entities by one or more exact identifiers/attributes."""
        self._verify_attachment()
        filters = (canonical_id, provider_id, external_id, entity_type, card_name,
                   normalized_name, printing_id, set_id)
        if not any(value is not None for value in filters):
            raise QueryError("entity query requires at least one filter")
        values = self._results
        if canonical_id is not None: values = tuple(x for x in values if x.canonical_identity == canonical_id)
        if entity_type is not None: values = tuple(x for x in values if x.entity_type == entity_type.casefold())
        if printing_id is not None: values = tuple(x for x in values if x.entity_type == "printing" and x.canonical_identity == printing_id)
        if set_id is not None: values = tuple(x for x in values if str(x.canonical_values.get("set_id", "")).casefold() == set_id.casefold())
        if card_name is not None: values = tuple(x for x in values if x.entity_type == "card" and x.canonical_values.get("name") == card_name)
        if normalized_name is not None: values = tuple(x for x in values if x.entity_type == "card" and normalize_name(str(x.canonical_values.get("name", ""))) == normalize_name(normalized_name))
        if provider_id is not None: values = tuple(x for x in values if provider_id in self._identifiers(x, "provider"))
        if external_id is not None: values = tuple(x for x in values if external_id in self._identifiers(x, "external"))
        self._verify_attachment()
        return values

    def entity(self, identifier: str, *, entity_type: str | None = None) -> QueryResult:
        matches = self.entities(canonical_id=identifier, entity_type=entity_type)
        if len(matches) != 1: raise QueryError(f"expected one entity for {identifier}, found {len(matches)}")
        return matches[0]

    def search(self, text: str, *, mode: str = "exact", case_insensitive: bool = False) -> tuple[QueryResult, ...]:
        """Search Card names using exact, normalized, or prefix semantics; never fuzzy."""
        self._verify_attachment()
        if mode not in {"exact", "normalized", "prefix"}: raise QueryError("search mode must be exact, normalized, or prefix")
        if not text: raise QueryError("search text must not be empty")
        needle = normalize_name(text) if mode == "normalized" or case_insensitive else text
        found = []
        for result in self._results:
            if result.entity_type != "card": continue
            name = str(result.canonical_values.get("name", ""))
            candidate = normalize_name(name) if mode == "normalized" or case_insensitive else name
            if (mode == "prefix" and candidate.startswith(needle)) or (mode != "prefix" and candidate == needle):
                found.append(result)
        self._verify_attachment()
        return tuple(found)

    def related(self, identifier: str, relationship: str) -> tuple[QueryResult | Mapping[str, Any], ...]:
        """Traverse a named relationship without exposing storage paths or models."""
        if relationship == "promotion_audits":
            self.require_capability("full_query_audit")
        self._verify_attachment()
        if relationship == "card_printings":
            self.entity(identifier, entity_type="card")
            return tuple(x for x in self._results if x.entity_type == "printing" and x.canonical_values.get("card_id") == identifier)
        if relationship == "printing_card":
            printing = self.entity(identifier, entity_type="printing")
            return (self.entity(str(printing.canonical_values["card_id"]), entity_type="card"),)
        if relationship == "printing_set":
            printing = self.entity(identifier, entity_type="printing")
            set_id = str(printing.canonical_values["set_id"])
            return ({"canonical_identity": set_id, "entity_type": "set", "printing_ids":
                     [x.canonical_identity for x in self.entities(set_id=set_id)]},)
        if relationship in {"dataset_entities", "review_package_entities"}:
            key = "dataset_identity" if relationship.startswith("dataset") else "review_package_id"
            return tuple(x for x in self._results if self._provenance_contains(x, key, identifier))
        if relationship == "promotion_audits":
            records = self._audit_records(promotion_id=identifier)
            self._verify_attachment()
            return records
        raise QueryError(f"unsupported relationship: {relationship}")

    def provenance(self, identifier: str) -> Mapping[str, Any]:
        result = self.entity(identifier)
        return {"canonical_identity": identifier, **_plain(result.provenance_summary)}

    def dataset(self, identifier: str) -> Mapping[str, Any]:
        entities = self.related(identifier, "dataset_entities")
        return {"dataset_identity": identifier, "promoted_entities": [x.as_dict() for x in entities]}

    def validation(self, state: str) -> tuple[QueryResult | Mapping[str, Any], ...]:
        """Query explicit epistemic and audit failure states."""
        if state in {"rejected", "validation_failure"}:
            self.require_capability("full_query_audit")
        self._verify_attachment()
        allowed = {"unknown", "conflicting", "unresolved", "rejected", "validation_failure", "superseded"}
        if state not in allowed: raise QueryError("unsupported validation state")
        results: list[QueryResult | Mapping[str, Any]] = []
        for item in self._results:
            assertions = item.provenance_summary.get("evidence_assertions", [])
            if state == "unknown" and (item.uncertainty.startswith("unknown") or self._contains_status(assertions, "unknown")): results.append(item)
            elif state == "conflicting" and (item.uncertainty == "conflicting" or self._contains_status(assertions, "conflicting")): results.append(item)
            elif state == "unresolved" and (item.uncertainty == "unresolved" or self._contains_status(assertions, "unresolved")): results.append(item)
            elif state == "superseded" and item.supersession_state == "superseded": results.append(item)
        if state in {"rejected", "validation_failure"}:
            for audit in self._audit_records():
                rejected = audit.get("rejected_entities", [])
                valid = audit.get("validation_results", {}).get("valid", True)
                if state == "rejected" and rejected or state == "validation_failure" and not valid: results.append(audit)
        self._verify_attachment()
        return tuple(sorted(results, key=lambda x: x.canonical_identity if isinstance(x, QueryResult) else str(x.get("promotion_id", x.get("audit_id", "")))))

    def _load_raw(self) -> dict[str, Mapping[str, Any]]:
        raw = {}
        root = self.games_root / self.game
        for pattern in ("cards/*/card.json", "printings/*/printing.json", "products/*/product.json",
                        "product_versions/**/*.json", "packs/**/*.json", "slots/**/*.json", "print_sheets/**/*.json"):
            for path in self._paths(root, pattern):
                try: value = self._read_json(path)
                except (json.JSONDecodeError, OSError): continue
                if isinstance(value, dict) and value.get("id"): raw[str(value["id"])] = value
        return raw

    def _build_results(self) -> Iterable[QueryResult]:
        typed_identities: set[tuple[str, str]] = set()
        groups = {"game": (self._repository.game,), "card": self._repository.cards, "printing": self._repository.printings,
                  "product": self._repository.products, "product_version": self._repository.product_versions,
                  "pack_definition": self._repository.pack_definitions, "slot": self._repository.pack_slots,
                  "print_sheet": self._repository.sheets, "treatment": self._repository.treatments,
                  "finish": self._repository.finishes, "rarity": self._repository.rarities}
        for kind, records in groups.items():
            for record in records:
                typed_identities.add((kind, record.id))
                values = _plain(record)
                raw = self._raw.get(record.id, {})
                evidence = raw.get("assertions", raw.get("provenance", values.get("assertions", [])))
                sources = sorted({str(x.get("source_id")) for x in evidence if isinstance(x, Mapping) and x.get("source_id")})
                confidence_values = [float(x["confidence"]) for x in evidence if isinstance(x, Mapping) and isinstance(x.get("confidence"), (int, float))]
                confidence = min(confidence_values) if confidence_values else (1.0 if sources else None)
                statuses = {str(x.get("status", "")) for x in evidence if isinstance(x, Mapping)}
                uncertainty = str(raw.get("uncertainty_state", "conflicting" if "conflicting" in statuses else "unresolved" if "unresolved" in statuses else "unknown" if "unknown" in statuses else "known"))
                superseded = bool(raw.get("superseded_status", False)) or "superseded" in statuses
                provenance = {"source_ids": sources, "evidence_assertions": _plain(evidence),
                              "acquisition_lineage": _plain(raw.get("acquisition_lineage", [])),
                              "dataset_identity": _plain(raw.get("dataset_identity", [])),
                              "review_package_id": raw.get("review_package_id"),
                              "provider_policy": _plain(raw.get("provider_policy")),
                              "promotion_history": list(self._audit_summaries(record.id))}
                yield QueryResult(record.id, kind, values, provenance, confidence, uncertainty,
                                  "superseded" if superseded else "current")
        # Phase 85 knowledge promotions use a versioned state projection alongside the
        # typed game tree.  It is read through the same contract, never exposed directly.
        for path in (self.data_root / "canonical" / "state.json",
                     self.data_root / "canonical" / "knowledge" / "state.json"):
            if self._read_inventory is not None:
                if not self._paths(path.parent, path.name):
                    continue
            elif not path.exists():
                continue
            try: state = self._read_json(path)
            except (OSError, json.JSONDecodeError) as error: raise QueryError(f"invalid canonical state: {path}") from error
            for kind, entities in sorted(state.items()):
                if not isinstance(entities, Mapping): continue
                for identifier, record in sorted(entities.items()):
                    entity_type = str(record.get("entity_type", kind))
                    if (entity_type, str(identifier)) in typed_identities:
                        continue
                    evidence_ids = list(record.get("evidence_references", []))
                    audit = self._audit_records(promotion_id=record.get("promotion_id"))
                    package = audit[0].get("review_package", {}) if audit else {}
                    assertions = self._state_assertions(str(identifier), record, package)
                    provenance = {"source_ids": sorted({str(x.get("source_id")) for x in assertions if x.get("source_id")}),
                        "evidence_assertions": assertions, "acquisition_lineage": _plain(record.get("acquisition_lineage", [])),
                        "dataset_identity": _plain(record.get("dataset_identity", [])),
                        "review_package_id": record.get("review_package_id"),
                        "provider_policy": _plain(package.get("provider")),
                        "record_provenance": _plain(record.get("provenance", {})),
                        "promotion_history": list(self._audit_summaries(str(identifier),
                            promotion_id=record.get("promotion_id"), evidence_ids=evidence_ids))}
                    yield QueryResult(str(identifier), entity_type, _plain(record.get("values", {})),
                        provenance, record.get("confidence"), str(record.get("uncertainty_state", "unknown")),
                        "superseded" if record.get("superseded_status") else "current")

    @staticmethod
    def _state_assertions(identifier: str, record: Mapping[str, Any], package: Mapping[str, Any]) -> list[Mapping[str, Any]]:
        """Keep package assertions, or project retained references from bounded state.

        Bounded promotion audits bind candidate membership and digests, rather than
        embedding a review package. A reference projection preserves the state record's
        lineage; it does not invent an assertion value or claim a new verification.
        """
        evidence_ids = list(record.get("evidence_references", []))
        by_id = {x.get("id"): x for x in package.get("candidate_assertions", [])
                 if isinstance(x, Mapping) and x.get("id") in evidence_ids}
        retained = _plain(record.get("provenance", {}))
        source_id = retained.get("source_id") or retained.get("artifact_identifier")
        assertions = []
        for evidence_id in sorted(set(evidence_ids)):
            if evidence_id in by_id:
                assertions.append(_plain(by_id[evidence_id]))
                continue
            reference = {"id": evidence_id, "canonical_identity": identifier,
                         "projection": "retained_canonical_evidence_reference",
                         "provenance": retained,
                         "acquisition_lineage": _plain(record.get("acquisition_lineage", []))}
            if source_id: reference["source_id"] = source_id
            assertions.append(reference)
        return assertions

    def _audit_entries(self, *, entity_id: str | None = None, promotion_id: str | None = None):
        paths = (self._paths(self.data_root / "audit", "**/*.json")
                 if self._read_inventory is not None
                 else sorted((self.data_root / "audit").rglob("*.json")))
        for path in paths:
            try:
                content = (self._read_inventory.read_bytes(path)
                           if self._read_inventory is not None else path.read_bytes())
                value = json.loads(content)
            except (OSError, json.JSONDecodeError): continue
            if promotion_id and value.get("promotion_id") != promotion_id: continue
            ids = (value.get("promoted_entities", []) + value.get("rejected_entities", []) +
                   value.get("promoted_printing_ids", []))
            candidate = value.get("candidate_snapshot", {}).get("canonical_entity", {}).get("id")
            if entity_id and entity_id not in ids and entity_id != candidate: continue
            yield path, content, value

    def _audit_records(self, *, entity_id: str | None = None, promotion_id: str | None = None) -> tuple[Mapping[str, Any], ...]:
        return tuple(_plain(value) for _, _, value in self._audit_entries(
            entity_id=entity_id, promotion_id=promotion_id))

    def _audit_summaries(self, identifier: str, *, promotion_id: str | None = None,
                         evidence_ids: Iterable[str] = ()) -> tuple[Mapping[str, Any], ...]:
        """Bind one entity to the immutable audit without copying its full population."""
        fields = ("schema_version", "promotion_id", "result", "audit_digest",
                  "canonical_pre_state_digest", "canonical_post_state_digest",
                  "source_lineage_digest", "review_artifact_digests", "evidence_files",
                  "acquisition_run_id", "evidence_identity", "batch_id", "readiness_plan_digest")
        summaries = []
        for path, content, value in self._audit_entries(
                entity_id=None if promotion_id else identifier, promotion_id=promotion_id):
            promoted = set(value.get("promoted_entities", []) + value.get("promoted_printing_ids", []))
            references = sorted(set(evidence_ids))
            matched = sorted(promoted.intersection([identifier, *references]))
            summary = {key: _plain(value[key]) for key in fields if key in value}
            summary.update({"audit_reference": {"relative_path": path.relative_to(self.data_root).as_posix(),
                                "sha256": hashlib.sha256(content).hexdigest()},
                            "entity_binding": {"canonical_identity": identifier,
                                "evidence_references": references, "matched_promoted_references": matched},
                            "omitted_promoted_entity_count": len(promoted) - len(matched)})
            summaries.append(summary)
        return tuple(summaries)

    @staticmethod
    def _identifiers(result: QueryResult, kind: str) -> set[str]:
        keys = {f"{kind}_id", f"{kind}_identifier", f"{kind}_identifiers"}
        found: set[str] = set()
        def walk(value: Any, key: str = "") -> None:
            if isinstance(value, Mapping):
                for child_key, child in value.items(): walk(child, str(child_key))
            elif isinstance(value, list):
                for child in value: walk(child, key)
            elif key in keys or (kind == "external" and key.endswith("_id") and key != "card_id"):
                found.add(str(value))
        walk(result.canonical_values); walk(result.provenance_summary)
        return found

    @staticmethod
    def _provenance_contains(result: QueryResult, key: str, identifier: str) -> bool:
        value = result.provenance_summary.get(key)
        def contains(item: Any) -> bool:
            if isinstance(item, Mapping): return any(contains(child) for child in item.values())
            if isinstance(item, (list, tuple)): return any(contains(child) for child in item)
            return str(item) == identifier
        return contains(value)

    @staticmethod
    def _contains_status(assertions: Any, status: str) -> bool:
        return any(isinstance(x, Mapping) and (x.get("status") == status or x.get("evidence_class") == status) for x in assertions)
