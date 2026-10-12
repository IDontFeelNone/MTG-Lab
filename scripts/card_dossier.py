"""Bounded, read-only Card evidence dossiers over existing public read contracts.

The dossier is a retained-evidence projection, not a strategic judgment or an
acquisition evaluation.  Its manual handoff uses the existing immutable
ReasoningContextResult contract; no model or transport is invoked.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
from typing import Any, Mapping

from card_intelligence.deck_usage import load_deck_usage
from card_intelligence.demand_review import load_reviewed_demand
from card_intelligence.explanation import CardValueExplanationEngine
from card_intelligence.repository import KnowledgeRepository
from query import CanonicalQueryEngine
from semantic import CanonicalSemanticQueryEngine, SemanticRequest

from reasoning.context import ReasoningContextBuilder
from reasoning.models import ReasoningContextRequest, ReasoningContextResult, freeze, thaw


DOSSIER_VERSION = "card-evidence-dossier-v1"
MAXIMUM_BYTES = 65536
PRINTING_SAMPLE_LIMIT = 5
DECK_SAMPLE_LIMIT = 5


def canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"))


def content_identity(value: Any) -> str:
    return "sha256:" + hashlib.sha256(canonical_json(value).encode()).hexdigest()


def _digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


@dataclass(frozen=True)
class CardEvidenceDossier:
    """Immutable dossier plus an existing-contract manual reasoning handoff."""

    payload: Mapping[str, Any]
    reasoning_context: ReasoningContextResult

    def __post_init__(self):
        object.__setattr__(self, "payload", freeze(self.payload))

    def to_dict(self) -> dict[str, Any]:
        return thaw(self.payload)

    def to_json(self) -> str:
        return canonical_json(self.to_dict())


class CardEvidenceDossierBuilder:
    """Project one explicitly supplied production Card ID without name fallback."""

    def __init__(self, data_root: Path):
        self.data_root = Path(data_root).resolve()
        self.repository_root = self.data_root.parent
        self.engine = CardValueExplanationEngine(self.data_root)
        self.query = CanonicalQueryEngine(data_root=self.data_root,
                                         games_root=self.data_root / "canonical/games")
        self.context_builder = ReasoningContextBuilder(CanonicalSemanticQueryEngine(self.query))

    def _retained_path(self, reference: str) -> Path:
        relative = reference.split("#", 1)[0]
        path = (self.repository_root / relative).resolve()
        if not path.is_relative_to(self.data_root) or not path.exists():
            raise ValueError(f"source reference is not retained repository evidence: {reference}")
        return path

    def _reference_integrity(self, reference: str) -> dict[str, Any]:
        path = self._retained_path(reference)
        if path.is_file():
            return {"reference": reference, "retained_bytes_sha256": _digest(path),
                    "byte_count": path.stat().st_size, "verification": "retained_file_bytes"}
        files = sorted(p for p in path.rglob("*") if p.is_file())
        entries = [{"relative_path": p.relative_to(path).as_posix(),
                    "sha256": _digest(p)} for p in files]
        return {"reference": reference, "file_count": len(files),
                "file_inventory_identity": content_identity(entries),
                "verification": "canonical_json_relative_path_sha256_inventory"}

    def _inputs(self, report: dict[str, Any]) -> dict[str, Any]:
        """Verify retained digests; distinguish unavailable upstream source bytes."""
        sections = report["evidence_sections"]
        acquisitions = []
        for run_id in sorted({o["acquisition_run_id"]
                              for o in sections["observed_price_evidence"]["observations"]}):
            directory = self.data_root / "market/acquisitions" / run_id
            manifest_path = directory / "manifest.json"
            manifest = json.loads(manifest_path.read_text())
            without_identity = {k: v for k, v in manifest.items() if k != "manifest_content_sha256"}
            # Existing market-acquisition-evidence-v1 hashes pretty JSON plus a
            # trailing newline, rather than this dossier's compact JSON profile.
            manifest_bytes = (json.dumps(without_identity, indent=2, sort_keys=True,
                                         separators=(",", ": ")) + "\n").encode()
            if hashlib.sha256(manifest_bytes).hexdigest() != manifest["manifest_content_sha256"]:
                raise ValueError("acquisition manifest content digest mismatch")
            for name, metadata in manifest["files"].items():
                path = directory / name
                if _digest(path) != metadata["sha256"] or path.stat().st_size != metadata["bytes"]:
                    raise ValueError(f"retained source digest mismatch: {path.name}")
            matching = [o for o in sections["observed_price_evidence"]["observations"]
                        if o["acquisition_run_id"] == run_id]
            if any(o["provenance"]["source_sha256"] != manifest["provider_source_sha256"] or
                   o["provenance"]["normalized_sha256"] != manifest["normalized_sha256"] or
                   o["source_timestamp"] != manifest["source_observed_at"] or
                   o["retrieval_timestamp"] != manifest["retrieved_at"] for o in matching):
                raise ValueError("market observation and acquisition provenance disagree")
            acquisitions.append({"acquisition_run_id": run_id, "provider": manifest["provider"],
                "manifest": self._reference_integrity(manifest_path.relative_to(self.repository_root).as_posix()),
                "retained_source": self._reference_integrity((directory / "source-mb2.json").relative_to(self.repository_root).as_posix()),
                "provider_source_sha256": manifest["provider_source_sha256"],
                "normalized_sha256": manifest["normalized_sha256"],
                "source_timestamp": manifest["source_observed_at"], "retrieved_at": manifest["retrieved_at"],
                "original_bulk_source_bytes": "not_retained; digest is an acquisition assertion"})
        printing_directory = self.data_root / "evidence/phase-135/mtgjson-pilot-30786023976-1"
        printing_manifest = json.loads((printing_directory / "manifest.json").read_text())
        printing_source = printing_directory / "source-pilot-printings.json"
        if (_digest(printing_source) != printing_manifest["normalized_projection_sha256"] or
                printing_source.stat().st_size != printing_manifest["normalized_projection_byte_count"]):
            raise ValueError("retained printing source digest mismatch")
        rank_path = self.data_root / "card_intelligence/demand/phase-142/scryfall-edhrec-rank.json"
        rank = load_reviewed_demand(rank_path)
        deck_path = self.data_root / "card_intelligence/demand/phase-143/mtgjson-decks.json"
        deck = load_deck_usage(deck_path)
        return {"market_acquisitions": acquisitions,
            "printing_provider": {"provider": printing_manifest["provider"],
                "retained_source": self._reference_integrity(printing_source.relative_to(self.repository_root).as_posix()),
                "manifest": self._reference_integrity((printing_directory / "manifest.json").relative_to(self.repository_root).as_posix()),
                "upstream_source_sha256": printing_manifest["source_sha256"],
                "acquisition_timestamp": printing_manifest["acquisition_timestamp"],
                "dataset_publication_timestamp": printing_manifest["dataset_publication_timestamp"],
                "license": printing_manifest["license"], "attribution": printing_manifest["attribution"],
                "original_bulk_source_bytes": "not_retained; digest is an acquisition assertion"},
            "demand_providers": [{"provider": doc["provider"],
                "retained_projection": self._reference_integrity(path.relative_to(self.repository_root).as_posix()),
                "projection_records_sha256": doc["records_sha256"],
                "upstream_source_sha256": doc["source_sha256"],
                "dataset_timestamp": doc["dataset_timestamp"], "retrieved_at": doc["retrieved_at"],
                "source_endpoint": doc["source_endpoint"], "license_considerations": doc["license_considerations"],
                "original_source_bytes": "not_retained; only the reviewed projection can be replayed"}
                for doc, path in ((rank, rank_path), (deck, deck_path))]}

    def build(self, card_id: str) -> CardEvidenceDossier:
        if not isinstance(card_id, str) or card_id not in self.engine.cards:
            raise ValueError("an exact production Card ID is required; name and seed selection are unsupported")
        record = self.engine.cards[card_id]
        if record.get("values", {}).get("card_reference") != card_id:
            raise ValueError("production Card identity does not match its canonical reference")
        report = self.engine.explain(card_id=card_id, include_demand_evidence=True)
        if report["schema_version"] != "card-value-explanation-v4":
            raise ValueError("reviewed v4 production evidence is required")
        base = self.context_builder.build(ReasoningContextRequest(
            SemanticRequest("find_identifier", {"identifier": card_id, "entity_type": "card"}),
            requested_entity_types=("card",), maximum_entities=1, maximum_relationships=5,
            maximum_evidence_items=20))
        if len(base.entities) != 1 or base.entities[0]["canonical_identity"] != card_id:
            raise ValueError("canonical query did not return the exact production Card")
        if not base.evidence_references:
            raise ValueError("promoted production evidence lineage is missing")
        sections = json.loads(canonical_json(report["evidence_sections"]))
        # v4's legacy quality.incomplete text still describes its v1 coverage.
        # The actual v4 historical section and limitations govern this projection.
        sections.pop("evidence_quality")
        sections["observed_price_evidence"].pop("history_readiness")
        history = sections["printing_history"]
        sets = history.pop("distinct_retained_sets")
        history["distinct_retained_set_count"] = len(sets)
        history["retained_set_sample"] = sets[:PRINTING_SAMPLE_LIMIT]
        deck = sections["deck_usage_evidence"]
        associations = sorted(deck["literal_deck_associations"],
                              key=lambda a: a["source_record_identity"])
        deck["literal_deck_associations"] = associations[:DECK_SAMPLE_LIMIT]
        printings = sorted((p["values"] for p in self.engine.printings.values()
                            if p["values"].get("card_id") == card_id), key=lambda p: p["uuid"])
        observed_ids = {o["canonical_printing_id"]
                        for o in sections["observed_price_evidence"]["observations"]}
        # Keep every observed Printing's identity; sample the remaining coverage.
        selected = [p for p in printings if p["uuid"] in observed_ids]
        selected.extend(p for p in printings if p["uuid"] not in observed_ids)
        selected = sorted(selected[:PRINTING_SAMPLE_LIMIT], key=lambda p: p["uuid"])
        sections["printing_identities"] = selected
        facts = {f.fact_id: f for f in KnowledgeRepository(self.data_root / "knowledge").validate()}
        fact_inventory = []
        sources: dict[str, dict[str, Any]] = {}
        for fact_id in report["provenance"]["knowledge_fact_ids"]:
            fact = facts[fact_id].to_dict()
            fact_path = self.data_root / "knowledge/facts/magic" / card_id / f"{fact_id}.json"
            fact_inventory.append({"fact_id": fact_id, "predicate": fact["predicate"],
                "value_status": fact["value"]["status"], "effective_at": fact["effective_at"],
                "recorded_at": fact["recorded_at"],
                "retained_fact": self._reference_integrity(fact_path.relative_to(self.repository_root).as_posix()),
                "evidence_source_ids": sorted({e["source_id"] for e in fact["evidence"]})})
            for evidence in fact["evidence"]:
                source = sources.setdefault(evidence["source_id"], {"source_id": evidence["source_id"],
                    "source_type": evidence["source_type"], "references": []})
                reference = {**self._reference_integrity(evidence["reference"]),
                             "observed_at": evidence["observed_at"]}
                if reference not in source["references"]:
                    source["references"].append(reference)
        omitted = {"printing_identities": len(printings) - len(selected),
            "retained_set_identities": len(sets) - len(history["retained_set_sample"]),
            "literal_deck_associations": len(associations) - len(deck["literal_deck_associations"]),
            "market_observations": 0, "active_knowledge_fact_references": 0,
            "knowledge_source_references": 0, "legacy_evidence_quality_section": 1,
            "duplicate_observed_price_history_readiness_section": 1}
        payload = {"schema_version": DOSSIER_VERSION, "card_identity": report["card_identity"],
            "canonical_entity": thaw(base.entities[0]),
            "snapshots": {"canonical_query_snapshot_id": base.canonical_snapshot_id,
                "canonical_card_value_snapshot_identity": report["canonical_snapshot"]["identity"],
                "canonical_state": self._reference_integrity("data/canonical/state.json"),
                "source_card_value_report_identity": content_identity(report),
                "source_card_value_report_version": report["schema_version"],
                "base_reasoning_context_id": base.context_id},
            "retained_evidence_as_of": report["explanation_generated_at"],
            "evidence_counts": report["evidence_counts"], "evidence_sections": sections,
            "provenance": {"facts": fact_inventory,
                "sources": [sources[key] for key in sorted(sources)],
                "market_observation_ids": report["provenance"]["market_observation_ids"]},
            "input_integrity": self._inputs(report), "omitted_item_counts": omitted,
            "limits": {"maximum_serialized_bytes": MAXIMUM_BYTES,
                "printing_identity_sample": PRINTING_SAMPLE_LIMIT,
                "retained_set_sample": PRINTING_SAMPLE_LIMIT, "deck_association_sample": DECK_SAMPLE_LIMIT,
                "ordering": "Printing sample prioritizes observed Printing UUIDs, then other UUIDs; selected sample sorted by UUID. Other samples: set code; source-record identity; fact/source ID."},
            "limitations": sorted(set(report["limitations"] + [
                "Historical observations are provider market fields, not completed sales or current offers.",
                "Legality and rules evidence are dated retained assertions, not a live rules verification.",
                "Unsupported: competitive rank, best-in-slot status, synergy/combo correctness, forecasts, investment value, acquisition decisions.",
                "Missing: current offers, buyer costs, inventory, tournament results, and globally representative deck usage.",
                "Original provider bulk files and MTGJSON ZIP are not retained; reviewed projections and recorded source digests remain independently attributable.",
                "Full CardValue report and legacy evidence_quality are omitted; its full content identity is retained."])),
            "permissions": {"read_only": True, "production_admission": False,
                "acquisition_evaluation": False, "human_readiness_attestation": False,
                "model_execution": False}}
        payload["dossier_id"] = content_identity(payload)
        analytics = [{"projection": "bounded_card_value_evidence_manual_handoff", "dossier": payload}]
        b = base.to_dict()
        truncation = {**b["truncation"], "occurred": b["truncation"]["occurred"] or any(omitted.values()),
            "supplemental_projection": {
            "schema_version": DOSSIER_VERSION, "omitted_item_counts": omitted,
            "maximum_serialized_bytes": MAXIMUM_BYTES,
            "sampling_policy": payload["limits"]["ordering"]}}
        warnings = tuple(sorted(set(b["warnings"] + [
            f"dossier {key} truncated: {count} omitted" for key, count in omitted.items() if count])))
        content = {"canonical_snapshot_id": b["canonical_snapshot_id"], "analytics_snapshot_id": None,
            "request": b["normalized_request"], "entities": b["entities"],
            "relationships": b["relationships"], "analytics": analytics,
            "provenance": b["provenance_references"], "evidence": b["evidence_references"],
            "omitted": b["omitted_item_counts"], "truncation": truncation, "warnings": warnings}
        context = ReasoningContextResult(content_identity(content), b["canonical_snapshot_id"],
            b["normalized_request"], b["entities"], b["relationships"], analytics,
            b["provenance_references"], b["evidence_references"], b["validation_information"],
            b["confidence_information"], b["omitted_item_counts"], truncation, warnings)
        dossier = CardEvidenceDossier(payload, context)
        if any(len(serialized.encode()) > MAXIMUM_BYTES
               for serialized in (dossier.to_json(), context.to_json())):
            raise ValueError("bounded Card dossier or reasoning context exceeds its byte limit")
        return dossier


def render_explanation(dossier: CardEvidenceDossier) -> str:
    """Deterministic example whose factual values come only from its dossier."""
    d = dossier.to_dict()
    s = d["evidence_sections"]
    demand = s["demand_usage_evidence"]["facts"][0]
    rank = demand["exact_retained_value"]["rank"]
    deck = s["deck_usage_evidence"]
    market = s["observed_price_evidence"]["summary"]
    lines = [f"# {d['card_identity']['name']} — retained-evidence explanation", "",
        f"Dossier: `{d['dossier_id']}`. References below are JSON pointers into this dossier.", "",
        "Verified facts", "",
        f"- Exact production Card: `{d['card_identity']['card_id']}`; mana cost {d['canonical_entity']['canonical_values']['mana_cost']} (`/card_identity`, `/canonical_entity/canonical_values`).",
        f"- Retained Oracle text: {s['rules']['oracle_text']} (`/evidence_sections/rules/oracle_text`).",
        f"- Retained printing coverage: {d['evidence_counts']['retained_printings']} Printings; this is a bounded repository count (`/evidence_counts/retained_printings`).",
        f"- Scryfall supplied EDHREC ordinal rank {rank} at {demand['dataset_timestamp']}. It is not a deck count (`/evidence_sections/demand_usage_evidence`).",
        f"- MTGJSON represented this Card in {deck['numerator']} of {deck['denominator']} decoded provider deck files at {deck['dataset_timestamp']}; this provider population is not global usage (`/evidence_sections/deck_usage_evidence`).",
        f"- {market['total_observation_count']} historical market observations cover {market['distinct_covered_printing_count']} Printing, from {market['earliest_source_timestamp']} to {market['latest_source_timestamp']}. They are provider market fields, not completed sales or current offers (`/evidence_sections/observed_price_evidence/summary`).",
        "", "Deterministic descriptive calculations", ""]
    for index, movement in enumerate(s["historical_price_evidence"]["descriptive_movement_entries"]):
        lines.append(f"- {movement['provider']} {movement['set_code']} #{movement['collector_number']}, {movement['finish']}, {movement['language']}, {movement['currency']} {movement['price_type']}: {movement['first_amount']} → {movement['latest_amount']}; absolute change {movement['absolute_change']}, percentage change {movement['percentage_change']}%, over {movement['elapsed_seconds']} seconds (`/evidence_sections/historical_price_evidence/descriptive_movement_entries/{index}`).")
    lines.extend(["", "Supported interpretations", "",
        "- These exact market dimensions support description of the retained historical movement only; their scope does not establish a forecast (`/evidence_sections/historical_price_evidence/history_readiness_state`).",
        "- The two demand providers describe independent metrics and populations. An ordinal rank and provider-curated deck-file inclusion cannot be combined into global demand (`/evidence_sections/demand_usage_evidence/metric_semantics`, `/evidence_sections/deck_usage_evidence/population_semantics`).",
        "", "Unknown or unsupported conclusions", "",
        "- Current buyer offers and transaction costs, competitive rankings, best-in-slot comparisons, verified combos, forecasts, investment value, and acquisition recommendations are unsupported by this dossier (`/limitations`, `/permissions`).",
        "- Printing and deck samples omit entries explicitly counted in `/omitted_item_counts`; complete raw provider corpora are not retained (`/input_integrity`).",
        "", "This is a read-only manual explanation example. No model executed and no readiness or acquisition decision was authorized.", ""])
    return "\n".join(lines)
