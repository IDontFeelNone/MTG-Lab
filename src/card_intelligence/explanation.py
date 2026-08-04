"""Deterministic, read-only explanations of retained pilot-card evidence.

This module deliberately reports evidence coverage, not a value, value score,
forecast, ranking, or recommendation.
"""
from __future__ import annotations

from collections import Counter
from decimal import Decimal
import hashlib
import json
from pathlib import Path
from typing import Any

from market.intelligence import MarketObservationRepository
from market.reporting import history_readiness

from .repository import KnowledgeRepository


SCHEMA_VERSION = "card-value-explanation-v1"
PRICE_SCHEMA_VERSION = "card-value-explanation-v2"
ERROR_VERSION = "card-value-explanation-error-v1"
CANONICAL_IDENTITY = "sha256:881c4ddf1dd5f3dc8004aef001277407e359b165cba6d9f5e8d442e9eef48077"


class ExplanationError(ValueError):
    """The requested explanation is outside the retained pilot boundary."""


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class CardValueExplanationEngine:
    """Read existing canonical, knowledge, and market repositories without writing."""

    def __init__(self, data_root: Path):
        self.data_root = Path(data_root)
        self.canonical_path = self.data_root / "canonical/state.json"
        self.canonical = json.loads(self.canonical_path.read_text(encoding="utf-8"))
        self.facts = KnowledgeRepository(self.data_root / "knowledge").validate()
        self.observations = MarketObservationRepository(
            self.data_root / "market/observations").observations()
        phase136 = [fact for fact in self.facts if fact.fact_id.startswith("phase136-")
                    and fact.kind == "reprint_history"]
        if len(phase136) != 10:
            raise ExplanationError("expected exactly ten active Phase 136 pilot histories")
        self.pilot_ids = frozenset(fact.card_id for fact in phase136)
        self.cards = self.canonical.get("card", {})
        self.printings = self.canonical.get("printing", {})
        self.names = {self.cards[card_id]["values"]["name"].casefold(): card_id
                      for card_id in self.pilot_ids}

    def resolve(self, *, name: str | None = None, card_id: str | None = None) -> str:
        if (name is None) == (card_id is None):
            raise ExplanationError("provide exactly one card name or --card-id")
        if card_id is not None:
            if card_id not in self.pilot_ids:
                raise ExplanationError("card ID is not in the ten-card pilot")
            return card_id
        normalized = str(name).strip().casefold()
        if normalized not in self.names:
            raise ExplanationError("card name is not in the ten-card pilot")
        return self.names[normalized]

    def explain(self, *, name: str | None = None, card_id: str | None = None,
                include_observed_prices: bool = False) -> dict[str, Any]:
        selected_id = self.resolve(name=name, card_id=card_id)
        card = self.cards[selected_id]
        printings = sorted((item for item in self.printings.values()
                            if item.get("values", {}).get("card_id") == selected_id),
                           key=lambda item: item["values"]["uuid"])
        facts = [fact for fact in self.facts if fact.card_id == selected_id]
        superseded = {old for fact in facts for old in fact.supersedes}
        active = sorted((fact for fact in facts if fact.fact_id not in superseded),
                        key=lambda fact: fact.fact_id)
        printing_ids = {item["values"]["uuid"] for item in printings}
        observations = sorted((item for item in self.observations
                               if item.entity_type == "printing" and item.entity_id in printing_ids),
                              key=lambda item: (item.observed_at, item.recorded_at,
                                                item.provider, item.observation_id))
        history_fact = next(fact for fact in active if fact.kind == "reprint_history")
        history = history_fact.to_dict()["value"]["data"]
        rules_facts = [fact for fact in active if fact.kind in {
            "legality", "mechanical_theme", "tribal_theme", "tutor", "mana_acceleration",
            "removal", "card_advantage", "win_condition", "deck_role"}]
        product_facts = [fact for fact in active if fact.kind == "product_membership"]
        unknown = sorted(fact.predicate for fact in active if fact.value_status == "unknown")
        generated_at = max([fact.recorded_at.isoformat().replace("+00:00", "Z") for fact in active]
                           + [item.recorded_at.isoformat().replace("+00:00", "Z")
                              for item in observations])
        sections = {
            "printing_history": self._printing_history(history, printings),
            "market": self._market(observations),
            "rules": self._rules(rules_facts, product_facts),
            "evidence_quality": {
                "known": sorted(fact.predicate for fact in active if fact.value_status == "known"),
                "unknown": unknown,
                "incomplete": ["printing history is bounded to retained evidence and is not globally complete"],
                "unsupported": ["Commander usage", "tournament results", "inventory",
                                "demand evidence", "scarcity conclusions", "value conclusions"],
            },
        }
        evidence_ids = sorted({e.source_id for fact in active for e in fact.evidence})
        document = {
            "schema_version": SCHEMA_VERSION,
            "explanation_generated_at": generated_at,
            "card_identity": {"game_id": "magic", "card_id": selected_id,
                              "name": card["values"]["name"]},
            "canonical_snapshot": {"identity": CANONICAL_IDENTITY,
                                   "path": "data/canonical/state.json",
                                   "sha256": _sha256(self.canonical_path),
                                   "card": {key: card["values"].get(key)
                                            for key in ("name", "normalized_name", "mana_cost", "layout")}},
            "evidence_sections": sections,
            "evidence_counts": {
                "active_knowledge_facts": len(active),
                "known_facts": sum(f.value_status == "known" for f in active),
                "unknown_facts": len(unknown),
                "retained_printings": len(printings),
                "market_observations": len(observations),
                "evidence_sources": len(evidence_ids),
            },
            "limitations": [
                "This repository currently contains no reviewed Commander usage.",
                "This repository currently contains no reviewed tournament results.",
                "This repository currently contains no retained inventory information.",
                "This repository currently contains no demand evidence.",
                "Printing count is not supply quantity and does not establish scarcity.",
                "Market observations are reported only as coverage; prices are not interpreted.",
                "No value estimate, value score, ranking, prediction, or recommendation is produced.",
            ],
            "provenance": {
                "canonical": {"path": "data/canonical/state.json", "identity": CANONICAL_IDENTITY},
                "knowledge_fact_ids": [fact.fact_id for fact in active],
                "knowledge_evidence_source_ids": evidence_ids,
                "market_observation_ids": [item.observation_id for item in observations],
                "input_only": True,
            },
        }
        if include_observed_prices:
            document["schema_version"] = PRICE_SCHEMA_VERSION
            document["evidence_sections"]["observed_price_evidence"] = \
                self._observed_price_evidence(selected_id, printings, observations)
            document["evidence_sections"]["evidence_quality"] = self._price_quality(
                document["evidence_sections"]["evidence_quality"], observations)
            document["limitations"] = self._price_limitations()
        return document

    @staticmethod
    def _dimension(item) -> tuple[str, str, str, str, str, str]:
        return (item.entity_id, item.provider, item.finish or "",
                str(item.provenance.get("language", "")), item.currency, item.price_type)

    def _observed_price_evidence(self, card_id: str, printings: list[dict[str, Any]],
                                 observations) -> dict[str, Any]:
        """Render retained assertions without combining exact market dimensions."""
        stamp = lambda value: value.isoformat().replace("+00:00", "Z")
        by_id = {item["values"]["uuid"]: item["values"] for item in printings}
        dimensions: dict[tuple[str, ...], list[Any]] = {}
        for item in observations:
            dimensions.setdefault(self._dimension(item), []).append(item)
        rendered = []
        dimension_summaries = []
        for key in sorted(dimensions):
            values = sorted(dimensions[key], key=lambda item: (
                item.observed_at, item.recorded_at, item.observation_id))
            known = [item.price for item in values if item.price is not None]
            for index, item in enumerate(values):
                printing = by_id[item.entity_id]
                rendered.append({
                    "canonical_printing_id": item.entity_id,
                    "canonical_card_id": card_id,
                    "set_code": printing.get("set_id"),
                    "collector_number": printing.get("collector_number"),
                    "finish": item.finish,
                    "language": item.provenance.get("language"),
                    "provider": item.provider,
                    "provider_record_id": item.provenance.get("source_provider_identifier"),
                    "currency": item.currency,
                    "price_type": item.price_type,
                    "price": {"state": "known" if item.price is not None else "explicitly_unavailable",
                              "amount": None if item.price is None else format(item.price, "f")},
                    "source_timestamp": stamp(item.observed_at),
                    "retrieval_timestamp": stamp(item.recorded_at),
                    "acquisition_run_id": item.provenance.get("acquisition_run_id"),
                    "observation_id": item.observation_id,
                    "provenance": {
                        "source_url": item.provenance.get("source_url"),
                        "source_sha256": item.provenance.get("source_sha256"),
                        "normalized_sha256": item.provenance.get("normalized_sha256"),
                    },
                    "history_position": {"first": index == 0, "latest": index == len(values) - 1,
                                         "only": len(values) == 1},
                })
            ordered = sorted(known)
            median = None
            if ordered:
                middle = len(ordered) // 2
                median = ordered[middle] if len(ordered) % 2 else \
                    (ordered[middle - 1] + ordered[middle]) / Decimal(2)
            dimension_summaries.append({
                "dimension": {"canonical_printing_id": key[0], "provider": key[1],
                              "finish": key[2] or None, "language": key[3] or None,
                              "currency": key[4], "price_type": key[5]},
                "observation_count": len(values), "known_price_count": len(known),
                "explicit_missing_price_count": len(values) - len(known),
                "minimum_amount": None if not ordered else format(ordered[0], "f"),
                "maximum_amount": None if not ordered else format(ordered[-1], "f"),
                "median_amount": None if median is None else format(median, "f"),
                "statistic_observation_count": len(known),
                "history_state": "single_observation_no_trend" if len(values) == 1 else "multiple_observations",
                "latest_observation_id": values[-1].observation_id,
            })
        covered = sorted({item.entity_id for item in observations})
        source_times = [item.observed_at for item in observations]
        retrieval_times = [item.recorded_at for item in observations]
        summary = {
            "total_observation_count": len(observations),
            "known_price_observation_count": sum(item.price is not None for item in observations),
            "explicit_missing_price_observation_count": sum(item.price is None for item in observations),
            "distinct_covered_printing_count": len(covered),
            "distinct_provider_count": len({item.provider for item in observations}),
            "distinct_finish_count": len({item.finish for item in observations}),
            "distinct_language_count": len({item.provenance.get("language") for item in observations}),
            "distinct_currency_count": len({item.currency for item in observations}),
            "distinct_price_type_count": len({item.price_type for item in observations}),
            "earliest_source_timestamp": None if not source_times else stamp(min(source_times)),
            "latest_source_timestamp": None if not source_times else stamp(max(source_times)),
            "latest_retrieval_timestamp": None if not retrieval_times else stamp(max(retrieval_times)),
            "observation_history_span": None if not source_times else {
                "from": stamp(min(source_times)), "to": stamp(max(source_times)),
                "seconds": int((max(source_times) - min(source_times)).total_seconds())},
            "covered_printing_ids": covered,
            "uncovered_retained_printing_count": len(printings) - len(covered),
            "latest_observation_for_each_exact_dimension": [item["latest_observation_id"]
                                                            for item in dimension_summaries],
        }
        return {"ordering": ["canonical_printing_id", "provider", "finish", "language",
                             "currency", "price_type", "source_timestamp", "observation_id"],
                "summary": summary, "observations": rendered,
                "compatible_dimension_summaries": dimension_summaries,
                "history_readiness": history_readiness(list(observations))}

    @staticmethod
    def _price_quality(base: dict[str, Any], observations) -> dict[str, Any]:
        return {"known": sorted(set(base["known"] + [
                    "observed price amount", "provider", "finish", "currency", "price type",
                    "source timestamp", "retrieval timestamp", "observation provenance"])),
                "unknown": base["unknown"],
                "explicitly_unavailable": (["provider price value"]
                    if any(item.price is None for item in observations) else []),
                "incomplete": sorted(set(base["incomplete"] + [
                    "only one retained acquisition", "market coverage is limited to retained MB2 Printings",
                    "no time series sufficient to establish price movement",
                    "market coverage is incomplete across 913 canonical Printings"])),
                "unsupported": sorted(set(base["unsupported"] + [
                    "completed-sale velocity", "inventory depth", "Commander demand",
                    "tournament demand", "buylist spread", "future price direction",
                    "fair-value estimate"]))}

    @staticmethod
    def _price_limitations() -> list[str]:
        return [
            "One retained snapshot does not establish a price trend.",
            "An observation is a provider assertion, not a completed sale.",
            "A market price is not guaranteed realizable value.",
            "MB2 price coverage does not price every retained historical Printing.",
            "Different finishes and Printings are not interchangeable.",
            "Printing count does not equal supply quantity.",
            "No inventory or sales-velocity evidence is retained.",
            "No buylist evidence is retained.",
            "No demand, Commander usage, or tournament usage evidence is retained.",
            "No price prediction is produced.",
            "No recommendation is produced.",
        ]

    @staticmethod
    def _printing_history(history: dict[str, Any], printings: list[dict[str, Any]]) -> dict[str, Any]:
        values = [item["values"] for item in printings]
        promotional = Counter(str(item.get("promotional", "unknown")).lower() for item in values)
        return {
            "total_retained_printings": history["total_known_canonical_printings"],
            "total_retained_reprints": history["reprint_count"],
            "first_retained_printing": history["earliest_known_canonical_printing_date"],
            "latest_retained_printing": history["latest_known_canonical_printing_date"],
            "distinct_retained_sets": history["set_codes_and_names"],
            "finishes": history["known_finishes"],
            "treatments": history["known_treatments"],
            "promotional_variants": {
                "known_promotional": promotional.get("true", 0),
                "known_nonpromotional": promotional.get("false", 0),
                "unknown": promotional.get("unknown", 0),
            },
            "coverage_state": history["coverage_state"],
            "evidence_completeness_state": history["evidence_completeness_state"],
        }

    @staticmethod
    def _market(observations) -> dict[str, Any]:
        stamp = lambda value: value.isoformat().replace("+00:00", "Z")
        first = observations[0] if observations else None
        latest = observations[-1] if observations else None
        return {
            "observation_count": len(observations),
            "first_observation": None if first is None else stamp(first.observed_at),
            "latest_observation": None if latest is None else stamp(latest.observed_at),
            "provider_coverage": sorted({item.provider for item in observations}),
            "supported_currencies": sorted({item.currency for item in observations}),
            "observation_span": None if first is None else {
                "from": stamp(first.observed_at), "to": stamp(latest.observed_at)},
        }

    @staticmethod
    def _rules(rules_facts, product_facts) -> dict[str, Any]:
        known = {fact.predicate: fact.to_dict()["value"]["data"] for fact in rules_facts
                 if fact.value_status == "known"}
        oracle = known.pop("mechanical.oracle_text", None)
        return {
            "oracle_text": None if oracle is None else oracle.get("oracle_text"),
            "mechanical_roles": [{"predicate": key, "evidence": known[key]}
                                 for key in sorted(known) if key != "format.legalities"],
            "legality": known.get("format.legalities"),
            "product_membership": [fact.to_dict()["value"]["data"] for fact in product_facts
                                   if fact.value_status == "known"],
        }


def explanation_bytes(document: dict[str, Any]) -> bytes:
    return (json.dumps(document, indent=2, sort_keys=True, separators=(",", ": ")) + "\n").encode()
