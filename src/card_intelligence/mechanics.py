"""Read-only, source-attributed mechanics for the admitted production Card cohort.

This is a literal provider projection and descriptive counting profile. It does
not admit facts, parse rules interactions, classify roles, or decide castability.
"""
from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass, replace
from datetime import datetime
from decimal import Decimal, InvalidOperation
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
from typing import Any, Mapping

from query import CanonicalQueryEngine
from reasoning import ReasoningContextBuilder, ReasoningContextRequest, ReasoningContextResult
from reasoning.models import freeze, thaw
from semantic import CanonicalSemanticQueryEngine, SemanticRequest


DOSSIER_VERSION = "mechanical-card-dossier-v1"
COHORT_VERSION = "mechanical-card-cohort-v1"
DEFAULT_ACQUISITION = "scryfall-mb2-30754638264-1"
MAXIMUM_BYTES = 65536
# Explicit type-label vocabulary, not a text-based functional-role classifier.
CARD_TYPES = frozenset({"Artifact", "Battle", "Conspiracy", "Creature", "Dungeon",
    "Enchantment", "Instant", "Kindred", "Land", "Phenomenon", "Plane",
    "Planeswalker", "Scheme", "Sorcery", "Vanguard"})
SUPERTYPES = frozenset({"Basic", "Legendary", "Ongoing", "Snow", "World"})
FIELD_NAMES = ("name", "layout", "oracle_text", "mana_cost", "mana_value", "type_line",
    "colors", "color_identity", "keywords", "power", "toughness", "loyalty",
    "defense", "produced_mana", "color_indicator", "printed_text", "printed_type_line")
UNSUPPORTED = ("functional_role_classification", "verified_rules_interactions",
    "structured_ability_classification", "synergy_or_combo_correctness",
    "best_in_slot_or_substitute_ranking", "competitive_power", "deck_optimization",
    "complete_set_membership", "price_or_acquisition_decisions")


class MechanicalEvidenceError(ValueError):
    """Retained evidence cannot support the requested projection."""


def stable_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, ensure_ascii=False,
                      separators=(",", ":"), allow_nan=False)


def content_identity(value: Any) -> str:
    return "sha256:" + hashlib.sha256(stable_json(value).encode()).hexdigest()


def _field(record: Mapping[str, Any], name: str, prefix: str = "") -> dict[str, Any]:
    key = "cmc" if name == "mana_value" else name
    result = {"source_pointer": prefix + "/" + key}
    if key not in record or record[key] is None:
        return {**result, "status": "unknown",
                "reason": "field_absent" if key not in record else "provider_null"}
    value = record[key]
    valid = (isinstance(value, str) if name not in {
        "mana_value", "colors", "color_identity", "keywords", "produced_mana", "color_indicator"}
        else isinstance(value, list) and all(isinstance(x, str) for x in value))
    if name == "mana_value":
        try:
            number = Decimal(str(value))
            valid = not isinstance(value, bool) and isinstance(value, (int, float)) and number.is_finite() and number >= 0
        except InvalidOperation:
            valid = False
        if valid:
            # normalize() can round under the caller's Decimal context. Formatting
            # and removing fractional zeroes preserves the retained value exactly.
            value = format(number, "f")
            if "." in value:
                value = value.rstrip("0").rstrip(".")
            if number.is_zero():
                value = "0"
            result["value_encoding"] = "decimal-string"
    if name in {"colors", "color_identity", "produced_mana", "color_indicator"} and valid:
        allowed = set("WUBRG" + ("C" if name == "produced_mana" else ""))
        valid = len(value) == len(set(value)) and set(value) <= allowed
    if not valid:
        return {**result, "status": "unresolved", "reason": "unsupported_provider_value", "retained_value": value}
    return {**result, "status": "known", "value": value}


def _types(type_line: Mapping[str, Any]) -> dict[str, Any]:
    """Separate literal labels; never normalize Summon/Poly into guessed types."""
    result = {"source_pointer": type_line["source_pointer"], "basis": "literal_type_line_tokens"}
    if type_line["status"] != "known":
        return {**result, "status": "unknown", "reason": "type_line_unavailable"}
    groups = []
    for component in type_line["value"].split(" // "):
        before, separator, after = component.partition(" — ")
        tokens = before.split()
        unknown = sorted(set(tokens) - CARD_TYPES - SUPERTYPES)
        groups.append({"card_types": sorted(set(tokens) & CARD_TYPES),
            "supertypes": sorted(set(tokens) & SUPERTYPES),
            "subtypes": after.split() if separator else [], "unclassified_tokens": unknown})
    return {**result, "status": "unresolved" if any(g["unclassified_tokens"] or not g["card_types"] for g in groups) else "known",
            "components": groups}


@dataclass(frozen=True)
class MechanicalDossier:
    payload: Mapping[str, Any]

    def __post_init__(self):
        object.__setattr__(self, "payload", freeze(self.payload))

    def to_dict(self) -> dict[str, Any]:
        return thaw(self.payload)

    def to_json(self) -> str:
        return stable_json(self.to_dict())


class MechanicalCardIntelligence:
    """Compose existing canonical queries with one verified retained acquisition."""

    def __init__(self, data_root: Path, *, source_directory: Path | None = None):
        self._initialize(data_root, source_directory=source_directory)

    @classmethod
    def from_attachment(cls, attachment, *, data_root: Path,
                        expected_query_snapshot_id: str,
                        source_directory: Path | None = None) -> MechanicalCardIntelligence:
        """Use one verified catalog and separately selected retained mechanics.

        The evidence root is explicit and need not be the catalog's data root.
        Integrity does not grant source permission or production authority.
        """
        from repository.snapshots import SnapshotAttachment, SnapshotError
        from repository.legacy_profile import LegacyCompatibilityAttachment

        if not isinstance(attachment, (SnapshotAttachment, LegacyCompatibilityAttachment)):
            raise SnapshotError("verified immutable catalog attachment required")
        if not isinstance(expected_query_snapshot_id, str) or not re.fullmatch(
                r"sha256:[0-9a-f]{64}", expected_query_snapshot_id):
            raise MechanicalEvidenceError("an exact expected query snapshot is required")
        query = CanonicalQueryEngine.from_attachment(attachment)
        if query.snapshot().snapshot_id != expected_query_snapshot_id:
            raise MechanicalEvidenceError("attached mechanical canonical snapshot mismatch")
        result = cls.__new__(cls)
        result._initialize(data_root, source_directory=source_directory, query=query)
        return result

    def _initialize(self, data_root, *, source_directory=None, query=None):
        self._attached_query = query
        self.data_root = Path(data_root).resolve()
        self.repository_root = self.data_root.parent
        directory = (Path(source_directory) if source_directory else
                     self.data_root / "market/acquisitions" / DEFAULT_ACQUISITION).resolve()
        if not directory.is_relative_to(self.data_root):
            raise MechanicalEvidenceError("source acquisition must be retained inside data_root")
        self.query = (query if query is not None else
                      CanonicalQueryEngine(data_root=self.data_root,
                                           games_root=self.data_root / "canonical/games"))
        cards = self.query.entities(entity_type="card")
        # card_reference is the admitted production-state identity binding. Typed
        # seed Cards have no such binding and are never selected by name instead.
        self.cards = {r.canonical_identity: r for r in cards
                      if r.canonical_values.get("card_reference") == r.canonical_identity
                      and r.supersession_state == "current"}
        self.snapshot_id = self.query.snapshot().snapshot_id
        if query is not None:
            self._expected_query_snapshot_id = self.snapshot_id
            self._attached_evidence_root = self.data_root
            self._attached_repository_root = self.repository_root
            self._source_directory = directory
            self._attached_source_directory = directory
            self._bound_catalog = freeze(query.catalog_binding)
            if self._bound_catalog is None:
                raise MechanicalEvidenceError("verified catalog attachment required")
            self._source_files = self._source_fingerprint(directory)
            try:
                self.source, rows = self._load_source(directory)
            except MechanicalEvidenceError:
                raise
            except (OSError, ValueError, TypeError, KeyError):
                raise MechanicalEvidenceError("invalid or unavailable mechanical acquisition evidence") from None
        else:
            self.source, rows = self._load_source(directory)
        self.rows: dict[str, list[tuple[int, dict[str, Any]]]] = defaultdict(list)
        excluded = []
        record_ids = set()
        for index, row in enumerate(rows):
            if not isinstance(row, dict) or not isinstance(row.get("id"), str):
                raise MechanicalEvidenceError("source row lacks a provider record identity")
            if row["id"] in record_ids:
                raise MechanicalEvidenceError("duplicate provider record identity")
            record_ids.add(row["id"])
            oracle_id = row.get("oracle_id")
            if row.get("object") != "card" or oracle_id not in self.cards:
                excluded.append({"source_record_index": index, "provider_record_id": row["id"],
                    "oracle_id": oracle_id, "name": row.get("name"), "layout": row.get("layout"),
                    "reason": "unsupported_source_object" if row.get("object") != "card" else
                        "no_canonical_production_card_identity"})
            else:
                self.rows[oracle_id].append((index, row))
        mapped = sorted(identity for identity in self.cards if len(self.rows[identity]) == 1)
        missing = sorted(identity for identity in self.cards if not self.rows[identity])
        ambiguous = sorted(identity for identity in self.cards if len(self.rows[identity]) > 1)
        self.reconciliation = {"source_row_count": len(rows), "production_card_count": len(self.cards),
            "query_card_count": len(cards), "excluded_nonproduction_query_card_count": len(cards) - len(self.cards),
            "uniquely_mapped_card_count": len(mapped), "uniquely_mapped_source_row_count": len(mapped),
            "missing_canonical_card_ids": missing, "ambiguous_canonical_card_ids": ambiguous,
            "excluded_source_rows": excluded, "excluded_source_row_count": len(excluded),
            "ambiguous_source_row_count": sum(len(self.rows[x]) for x in ambiguous),
            "mapping_rule": "exact provider oracle_id equals admitted canonical card_reference; no name fallback",
            "scope": "current canonical production cohort; not complete set membership"}
        self.context_builder = ReasoningContextBuilder(CanonicalSemanticQueryEngine(self.query))
        if query is not None:
            self._attached_context_builder = self.context_builder
            self._source_metadata = freeze(self.source)
            self._rows_identity = content_identity(dict(self.rows))
            self._cards_identity = content_identity({key: value.as_dict() for key, value in self.cards.items()})
            self.verify_inputs()

    @property
    def catalog_binding(self) -> dict[str, Any] | None:
        """Outer catalog identity, deliberately absent from v1 dossier bytes."""
        if self._attached_query is None:
            return None
        self.verify_inputs()
        return thaw(self._bound_catalog)

    @staticmethod
    def _source_fingerprint(directory: Path) -> tuple:
        """Pin only the existing manifest dependency closure, not catalog sources."""
        try:
            manifest_path = directory / "manifest.json"
            if any(p.is_symlink() for p in (manifest_path, *manifest_path.parents)):
                raise MechanicalEvidenceError("mechanical evidence contains a symlink")
            manifest = json.loads(manifest_path.read_bytes())
            names = sorted({"manifest.json", *manifest["files"]})
            if "dry-run-report.json" not in names:
                raise MechanicalEvidenceError("mechanical report dependency is missing")
            result = []
            for name in names:
                if not isinstance(name, str):
                    raise MechanicalEvidenceError("invalid mechanical evidence locator")
                relative = PurePosixPath(name)
                if (relative.is_absolute() or relative.as_posix() != name or ".." in relative.parts
                        or "\\" in name or not relative.parts):
                    raise MechanicalEvidenceError("unsafe mechanical evidence locator")
                path = directory / name
                if any(p.is_symlink() for p in (path, *path.parents)):
                    raise MechanicalEvidenceError("mechanical evidence contains a symlink")
                raw = path.read_bytes()
                result.append((name, len(raw), hashlib.sha256(raw).hexdigest()))
            return tuple(result)
        except MechanicalEvidenceError:
            raise
        except (OSError, ValueError, KeyError, TypeError):
            raise MechanicalEvidenceError("invalid or unavailable mechanical acquisition evidence") from None

    def verify_inputs(self) -> None:
        """Revalidate attached inputs; legacy replay retains its original behavior."""
        if self._attached_query is None:
            return
        if (self.query is not self._attached_query or self.snapshot_id != self._expected_query_snapshot_id
                or self.data_root != self._attached_evidence_root or self.repository_root != self._attached_repository_root
                or self._source_directory != self._attached_source_directory
                or self.context_builder is not self._attached_context_builder
                or self.context_builder._semantic._query is not self._attached_query):
            raise MechanicalEvidenceError("attached mechanical reader was retargeted")
        if (self.query.snapshot().snapshot_id != self._expected_query_snapshot_id
                or self.query.catalog_binding != thaw(self._bound_catalog)):
            raise MechanicalEvidenceError("attached mechanical canonical snapshot changed")
        if (self._source_fingerprint(self._source_directory) != self._source_files
                or self.source != thaw(self._source_metadata)
                or content_identity(dict(self.rows)) != self._rows_identity
                or content_identity({key: value.as_dict() for key, value in self.cards.items()}) != self._cards_identity):
            raise MechanicalEvidenceError("mechanical source integrity mismatch")

    def _load_source(self, directory: Path) -> tuple[dict[str, Any], list[dict[str, Any]]]:
        manifest_path = directory / "manifest.json"
        raw_manifest = manifest_path.read_bytes()
        manifest = json.loads(raw_manifest)
        body = {k: v for k, v in manifest.items() if k != "manifest_content_sha256"}
        encoded = (json.dumps(body, indent=2, sort_keys=True, separators=(",", ": ")) + "\n").encode()
        if hashlib.sha256(encoded).hexdigest() != manifest["manifest_content_sha256"]:
            raise MechanicalEvidenceError("acquisition manifest digest mismatch")
        if manifest["schema_version"] != "market-acquisition-evidence-v1" or manifest["provider"] != "scryfall":
            raise MechanicalEvidenceError("unsupported retained acquisition contract")
        if any(manifest[key] is not False for key in ("canonical_write", "promotion_performed", "observations_persisted")):
            raise MechanicalEvidenceError("retained acquisition boundary flags disagree")
        for key in ("source_observed_at", "retrieved_at"):
            value = manifest[key]
            if not isinstance(value, str) or not value.endswith("Z"):
                raise MechanicalEvidenceError("source timestamps must be retained UTC values")
            datetime.fromisoformat(value[:-1] + "+00:00")
        source_names = []
        for name, meta in manifest["files"].items():
            path = (directory / name).resolve()
            if not path.is_relative_to(directory):
                raise MechanicalEvidenceError("unsafe retained source locator")
            raw = path.read_bytes()
            if len(raw) != meta["bytes"] or hashlib.sha256(raw).hexdigest() != meta["sha256"]:
                raise MechanicalEvidenceError("retained source integrity mismatch")
            if name.startswith("source-") and name.endswith(".json"):
                source_names.append(name)
        if len(source_names) != 1:
            raise MechanicalEvidenceError("expected one exact retained source projection")
        path = directory / source_names[0]
        rows = json.loads(path.read_bytes())
        if not isinstance(rows, list) or len(rows) != manifest["mb2_record_count"]:
            raise MechanicalEvidenceError("retained source row census mismatch")
        dry = json.loads((directory / "dry-run-report.json").read_bytes())
        pairs = {"run_id": "acquisition_run_id", "source_sha256": "provider_source_sha256",
                 "normalized_sha256": "normalized_sha256", "source_observed_at": "source_observed_at",
                 "retrieved_at": "retrieved_at", "mb2_record_count": "mb2_record_count"}
        if any(dry[left] != manifest[right] for left, right in pairs.items()):
            raise MechanicalEvidenceError("retained acquisition report and manifest disagree")
        return {"provider": manifest["provider"], "dataset": manifest["source_dataset"],
            "acquisition_run_id": manifest["acquisition_run_id"], "source_url": manifest["source_url"],
            "source_timestamp": manifest["source_observed_at"], "retrieved_at": manifest["retrieved_at"],
            "retained_source_reference": path.relative_to(self.repository_root).as_posix(),
            "retained_source_sha256": manifest["files"][source_names[0]]["sha256"],
            "manifest_reference": manifest_path.relative_to(self.repository_root).as_posix(),
            "manifest_bytes_sha256": hashlib.sha256(raw_manifest).hexdigest(),
            "acquisition_canonical_snapshot_identity": manifest["canonical_snapshot_identity"],
            "normalized_source_sha256": manifest["normalized_sha256"],
            "upstream_bulk_sha256": manifest["provider_source_sha256"],
            "original_bulk_bytes": "not_retained; upstream digest is an acquisition assertion"}, rows

    def dossier(self, card_id: str) -> MechanicalDossier:
        self.verify_inputs()
        if card_id not in self.cards:
            raise MechanicalEvidenceError("exact admitted production Card ID required")
        canonical = self.cards[card_id]
        matches = self.rows[card_id]
        row = matches[0][1] if len(matches) == 1 else {}
        fields = {name: _field(row, name) for name in FIELD_NAMES}
        if len(matches) != 1:
            for field in fields.values():
                field["reason"] = "source_binding_missing" if not matches else "source_binding_ambiguous"
        faces = []
        raw_faces = row.get("card_faces", [])
        if not isinstance(raw_faces, list) or any(not isinstance(f, dict) for f in raw_faces):
            raise MechanicalEvidenceError("invalid provider face representation")
        for index, face in enumerate(raw_faces):
            face_fields = {name: _field(face, name, f"/card_faces/{index}") for name in FIELD_NAMES}
            faces.append({"source_face_index": index, "fields": face_fields,
                          "type_labels": _types(face_fields["type_line"])})
        provenance = canonical.provenance_summary
        audits = [{"promotion_id": a.get("promotion_id"), "audit_reference": a["audit_reference"],
                   "entity_binding": a["entity_binding"]} for a in provenance.get("promotion_history", [])]
        differences = []
        for key in ("name", "layout", "mana_cost", "colors"):
            old = canonical.canonical_values.get(key)
            if fields[key]["status"] == "known" and old != fields[key]["value"]:
                differences.append({"field": key, "canonical_value": old,
                    "provider_value": fields[key]["value"],
                    "reason": "independent_provider_values_preserved; canonical record not rewritten"})
        source = {**self.source, "resolution": "unique" if len(matches) == 1 else
                  ("missing" if not matches else "ambiguous"),
                  "matching_provider_record_ids": sorted(r["id"] for _, r in matches)}
        if len(matches) == 1:
            source.update({"provider_record_id": row["id"], "oracle_id": row["oracle_id"],
                "source_record_index": matches[0][0], "record_content_identity": content_identity(row),
                "record_identity_profile": "sorted-key compact UTF-8 JSON of entire retained provider record"})
        source["canonical_source_printing_ids"] = sorted(p.canonical_identity
            for p in self.query.related(card_id, "card_printings")
            if p.canonical_values.get("identifiers", {}).get("scryfallId") == row.get("id")) if row else []
        payload = {"schema_version": DOSSIER_VERSION,
            "card_identity": {"game_id": self.query.game, "card_id": card_id,
                              "name": canonical.canonical_values["name"]},
            "canonical_snapshot_id": self.snapshot_id,
            "canonical_values": dict(canonical.canonical_values),
            "canonical_provenance": {"record_provenance": provenance.get("record_provenance"),
                "evidence_references": [a["id"] for a in provenance.get("evidence_assertions", [])],
                "promotion_audit_references": audits},
            "source": source, "fields": fields, "type_labels": _types(fields["type_line"]),
            "faces": faces, "canonical_provider_differences": differences,
            "projection_omissions": {"root_nonmechanical_field_count": len(set(row) -
                (set(FIELD_NAMES) - {"mana_value"}) - {"cmc", "id", "oracle_id", "card_faces"}),
                "face_nonmechanical_field_counts": [len(set(f) - (set(FIELD_NAMES) - {"mana_value"}) - {"cmc"}) for f in raw_faces],
                "mechanical_fields_omitted": 0,
                "policy": "Selected fields and identity bindings retained; other provider fields omitted. Entire-record content identity binds the original."},
            "unsupported_dimensions": list(UNSUPPORTED),
            "interpretation_boundary": {"oracle_text": "literal provider Oracle assertion",
                "printed_text": "Printing-specific provider field; never substituted with Oracle text",
                "metadata": "provider assertions, including cmc, colors and keywords",
                "type_labels": "deterministic literal tokens; unknown labels stay unresolved",
                "abilities": "Oracle text and provider keywords only; no ability or role classifier",
                "faces": "provider face order; no invented face IDs, mana values, or inherited colors",
                "known_empty": "empty string/list is retained evidence, not an unknown or a free-spell claim"}}
        payload["dossier_id"] = content_identity(payload)
        result = MechanicalDossier(payload)
        if len(result.to_json().encode()) > MAXIMUM_BYTES:
            raise MechanicalEvidenceError("mechanical dossier exceeds its byte bound")
        self.verify_inputs()
        return result

    def cohort_report(self) -> dict[str, Any]:
        self.verify_inputs()
        dossiers = [self.dossier(identity).to_dict() for identity in sorted(self.cards)]
        root_coverage = {key: Counter() for key in FIELD_NAMES}
        face_coverage = {key: Counter() for key in FIELD_NAMES}
        types, supertypes, keywords, mana_values, colors, layouts = (Counter() for _ in range(6))
        unresolved_types, missing_printings, differences = [], [], []
        explicit_face_count = multi_card_count = complete_text_count = 0
        fully_classified = 0
        for d in dossiers:
            fields, faces = d["fields"], d["faces"]
            for key, field in fields.items():
                root_coverage[key][field["status"]] += 1
                if field.get("reason"):
                    root_coverage[key]["reason:" + field["reason"]] += 1
            for face in faces:
                for key, field in face["fields"].items():
                    face_coverage[key][field["status"]] += 1
                    if field.get("reason"):
                        face_coverage[key]["reason:" + field["reason"]] += 1
            explicit_face_count += len(faces)
            multi_card_count += len(faces) > 1
            complete_text_count += (all(f["fields"]["oracle_text"]["status"] == "known" for f in faces)
                                    if faces else fields["oracle_text"]["status"] == "known")
            labels = [f["type_labels"] for f in faces] if faces else [d["type_labels"]]
            card_types, card_supers = set(), set()
            for item in labels:
                for component in item.get("components", []):
                    card_types.update(component["card_types"])
                    card_supers.update(component["supertypes"])
            types.update(card_types)
            supertypes.update(card_supers)
            if all(item["status"] == "known" for item in labels):
                fully_classified += 1
            else:
                unresolved_types.append({"card_identity": d["card_identity"], "type_line": fields["type_line"],
                                         "type_labels": labels})
            for name, target in (("mana_value", mana_values), ("layout", layouts)):
                if fields[name]["status"] == "known":
                    target[fields[name]["value"]] += 1
            if fields["color_identity"]["status"] == "known":
                key = "".join(c for c in "WUBRG" if c in fields["color_identity"]["value"]) or "colorless"
                colors[key] += 1
            if fields["keywords"]["status"] == "known":
                keywords.update(set(fields["keywords"]["value"]))
            if not d["source"]["canonical_source_printing_ids"]:
                missing_printings.append(d["card_identity"])
            if d["canonical_provider_differences"]:
                differences.append({"card_identity": d["card_identity"],
                                    "differences": d["canonical_provider_differences"]})
        total = len(dossiers)
        result = {"schema_version": COHORT_VERSION, "canonical_snapshot_id": self.snapshot_id,
            "source": self.source, "reconciliation": self.reconciliation,
            "denominators": {"canonical_cards": total, "explicit_provider_faces": explicit_face_count,
                "represented_source_components": sum(len(d["faces"]) or 1 for d in dossiers if d["source"]["resolution"] == "unique"),
                "explanation": "Card distributions count each canonical Card once per label. Type labels union represented faces; totals across overlapping types need not sum to cohort size. No castability/face-characteristic rule is inferred."},
            "coverage": {"card_fields": {k: dict(v) for k, v in root_coverage.items()},
                         "explicit_face_fields": {k: dict(v) for k, v in face_coverage.items()},
                         "cards_with_all_represented_oracle_text": complete_text_count,
                         "root_known_empty_mana_cost_count": sum(d["fields"]["mana_cost"].get("value") == "" for d in dossiers),
                         "root_known_empty_keyword_count": sum(d["fields"]["keywords"].get("value") == [] for d in dossiers)},
            "card_type_memberships": dict(types), "supertype_memberships": dict(supertypes),
            "fully_classified_type_card_count": fully_classified, "unresolved_type_cards": unresolved_types,
            "mana_value_distribution": [{"mana_value": key, "card_count": mana_values[key]}
                                        for key in sorted(mana_values, key=Decimal)],
            "color_identity_distribution": dict(colors), "keyword_card_frequencies": dict(keywords),
            "layout_distribution": dict(layouts), "multi_faced_card_count": multi_card_count,
            "cards_without_canonical_source_printing": missing_printings,
            "canonical_provider_differences": differences,
            "unsupported_dimensions": list(UNSUPPORTED),
            "scope": "current canonical production cohort; no complete MB2 membership claim or promotion"}
        result["report_id"] = content_identity(result)
        self.verify_inputs()
        return result

    def reasoning_context(self, card_id: str) -> ReasoningContextResult:
        """Manual supplemental projection; the generic semantic builder is unchanged."""
        dossier = self.dossier(card_id).to_dict()
        base = self.context_builder.build(ReasoningContextRequest(
            SemanticRequest("find_identifier", {"identifier": card_id, "entity_type": "card"}),
            requested_entity_types=("card",), maximum_entities=1,
            maximum_relationships=5, maximum_evidence_items=20))
        b = base.to_dict()
        if self._attached_query is not None and b["canonical_snapshot_id"] != self._expected_query_snapshot_id:
            raise MechanicalEvidenceError("mechanical reasoning canonical snapshot mismatch")
        analytics = [{"projection": "mechanical_card_evidence_manual_handoff", "dossier": dossier}]
        truncation = {**b["truncation"], "supplemental_projection": {
            "schema_version": DOSSIER_VERSION, "maximum_serialized_bytes": MAXIMUM_BYTES,
            "mechanical_fields_omitted": 0, "provider_record_omissions": "artwork, flavor, prices, and other nonmechanical raw fields; entire-record content digest retained"}}
        warnings = tuple(sorted(set(b["warnings"] + [
            "Provider mechanics are dated assertions; functional roles, interactions and synergy remain unsupported."])))
        content = {"canonical_snapshot_id": b["canonical_snapshot_id"], "analytics_snapshot_id": None,
            "request": b["normalized_request"], "entities": b["entities"],
            "relationships": b["relationships"], "analytics": analytics,
            "provenance": b["provenance_references"], "evidence": b["evidence_references"],
            "omitted": b["omitted_item_counts"], "truncation": truncation, "warnings": warnings}
        result = replace(base, context_id=content_identity(content), analytics_results=analytics,
                         analytics_snapshot_id=None, truncation=truncation, warnings=warnings)
        if len(result.to_json().encode()) > MAXIMUM_BYTES:
            raise MechanicalEvidenceError("mechanical reasoning context exceeds its byte bound")
        self.verify_inputs()
        return result
