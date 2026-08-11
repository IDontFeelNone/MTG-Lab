"""Fail-closed Phase 144 admission of retained MTGJSON deck evidence."""
from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any

from .deck_usage import load_deck_usage
from .models import Evidence, KnowledgeFact
from .repository import KnowledgeRepository, serialize_fact

EVIDENCE_REFERENCE = "data/card_intelligence/demand/phase-143/mtgjson-decks.json"


def _time(value: str) -> datetime:
    return datetime.fromisoformat(value.removesuffix("Z") + "+00:00")


def build_usage_facts(path: Path) -> tuple[KnowledgeFact, ...]:
    """Validate retained evidence and deterministically construct its literal facts."""
    document = load_deck_usage(path)
    facts: list[KnowledgeFact] = []
    for record in document["records"]:
        slug = record["card_name"].casefold().replace(" ", "-")
        evidence = Evidence(
            source_id=document["evidence_source_id"], source_type="retained_dataset",
            reference=EVIDENCE_REFERENCE, observed_at=_time(document["dataset_timestamp"]),
            claim=(f"MTGJSON {document['provider_dataset']} represents {record['card_name']} in "
                   f"{record['numerator']} of {record['denominator']} decoded deck files."))
        common = {
            "provider": "mtgjson", "provider_dataset": document["provider_dataset"],
            "dataset_timestamp": record["dataset_timestamp"],
            "evidence_source_id": document["evidence_source_id"],
            "source_sha256": document["source_sha256"],
            "source_reference": EVIDENCE_REFERENCE,
            "population_semantics": document["population_semantics"],
            "completeness_state": record["completeness"],
            "limitations": record["limitations"],
        }
        base = dict(game_id="magic", card_id=record["card_id"], confidence=None,
                    effective_at=_time(document["dataset_timestamp"]),
                    recorded_at=_time(document["retrieved_at"]), evidence=(evidence,))
        facts.append(KnowledgeFact(
            fact_id=f"phase144-{slug}-demand-deck_inclusion", kind="demand",
            predicate="demand.deck_inclusion", value_status="known",
            value={**common, "metric": record["metric"], "numerator": record["numerator"],
                   "denominator": record["denominator"],
                   "deck_associations": record["deck_associations"]}, supersedes=(), **base))
        facts.append(KnowledgeFact(
            fact_id=f"phase144-{slug}-format-usage", kind="format_usage",
            predicate="format.usage", value_status="known",
            value={**common, "formats": record["formats"],
                   "literal_associations": [
                       {key: association[key] for key in
                        ("provider_deck_identity", "source_record_identity",
                         "retained_record_id", "source_content_sha256", "deck_name", "format")}
                       for association in record["deck_associations"]]},
            supersedes=(), **base))
    return tuple(sorted(facts, key=lambda fact: fact.fact_id))


def admit_usage_facts(path: Path, repository: KnowledgeRepository) -> dict[str, Any]:
    """Append facts, accept byte-identical replay, and reject conflicting replay."""
    facts = build_usage_facts(path)
    added = replayed = 0
    for fact in facts:
        destination = repository._path(fact)
        if destination.exists():
            if destination.read_bytes() != serialize_fact(fact):
                raise ValueError(f"conflicting Phase 144 replay: {fact.fact_id}")
            replayed += 1
        else:
            repository.append(fact); added += 1
    repository.validate()
    return {"facts_added": added, "facts_replayed": replayed, "facts_superseded": 0}
