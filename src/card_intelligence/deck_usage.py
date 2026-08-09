"""Bounded MTGJSON deck projection and strict retained-evidence review."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

SCHEMA = "card-deck-usage-evidence-v1"
PILOT_NAMES = ("Brainstorm", "Command Tower", "Counterspell", "Goblin Charbelcher",
               "Goblin King", "Sol Ring", "Swords to Plowshares", "Treasure Cruise",
               "Walking Ballista", "Wishclaw Talisman")
ALLOWED_RECORD = {"card_id", "card_name", "provider_card_name", "metric", "numerator",
                  "denominator", "dataset_timestamp", "formats", "deck_associations",
                  "completeness", "limitations"}


class DeckUsageEvidenceError(ValueError):
    """A retained deck projection is malformed or ambiguous."""


def canonical_bytes(value: Any) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True, separators=(",", ": ")) + "\n").encode()


def load_deck_usage(path: Path) -> dict[str, Any]:
    document = json.loads(Path(path).read_text(encoding="utf-8"))
    required = {"schema_version", "evidence_source_id", "provider", "provider_dataset",
                "source_endpoint", "dataset_timestamp", "retrieved_at", "source_sha256",
                "source_byte_count", "population_semantics", "identity_mapping",
                "license_considerations", "retention_boundary", "records", "records_sha256"}
    if not isinstance(document, dict) or set(document) != required or document.get("schema_version") != SCHEMA:
        raise DeckUsageEvidenceError("invalid deck usage evidence envelope")
    if document["provider"] != "mtgjson" or document["provider_dataset"] != "AllDeckFiles.zip":
        raise DeckUsageEvidenceError("unsupported provider identity")
    if not isinstance(document["dataset_timestamp"], str) or not document["dataset_timestamp"].endswith("Z"):
        raise DeckUsageEvidenceError("missing or malformed dataset timestamp")
    records = document["records"]
    if not isinstance(records, list) or len(records) != 10 or hashlib.sha256(canonical_bytes(records)).hexdigest() != document["records_sha256"]:
        raise DeckUsageEvidenceError("deck usage evidence must contain ten digest-bound records")
    names, ids = [], []
    for record in records:
        if not isinstance(record, dict) or set(record) != ALLOWED_RECORD:
            raise DeckUsageEvidenceError("record has missing or unsupported fields")
        names.append(record["card_name"]); ids.append(record["card_id"])
        numerator, denominator = record["numerator"], record["denominator"]
        if any(isinstance(v, bool) or not isinstance(v, int) for v in (numerator, denominator)) or not 0 <= numerator <= denominator:
            raise DeckUsageEvidenceError("invalid numerator or denominator")
        if record["metric"] != "represented_deck_count" or record["dataset_timestamp"] != document["dataset_timestamp"]:
            raise DeckUsageEvidenceError("invalid metric or conflicting timestamp")
        decks = record["deck_associations"]
        if not isinstance(decks, list) or len(decks) != numerator or len({x["deck_id"] for x in decks}) != len(decks):
            raise DeckUsageEvidenceError("duplicate or inconsistent deck associations")
        for deck in decks:
            if set(deck) != {"deck_id", "deck_name", "format", "boards"} or not isinstance(deck["boards"], list):
                raise DeckUsageEvidenceError("malformed deck association")
        formats = record["formats"]
        if not isinstance(formats, list) or sum(x["deck_count"] for x in formats) != numerator:
            raise DeckUsageEvidenceError("format counts do not isolate the represented decks")
    if tuple(names) != PILOT_NAMES or len(ids) != len(set(ids)):
        raise DeckUsageEvidenceError("records must map the exact ten-card pilot once")
    return document


def project_decks(decks: list[dict[str, Any]], card_ids: dict[str, str], *, dataset_timestamp: str,
                  source_sha256: str, source_byte_count: int, retrieved_at: str) -> dict[str, Any]:
    """Project a decoded MTGJSON deck population; retain only pilot matches."""
    if set(card_ids) != set(PILOT_NAMES):
        raise DeckUsageEvidenceError("canonical mapping must contain the exact pilot")
    population: list[dict[str, Any]] = []
    seen = set()
    for raw in decks:
        deck_id = str(raw.get("code") or raw.get("fileName") or "").strip()
        name = str(raw.get("name") or "").strip(); fmt = str(raw.get("type") or "unknown").strip().casefold()
        if not deck_id or not name or deck_id in seen:
            raise DeckUsageEvidenceError("missing or duplicate provider deck identity")
        seen.add(deck_id); matches: dict[str, set[str]] = {}
        for board in ("commander", "mainBoard", "sideBoard"):
            cards = raw.get(board, [])
            if not isinstance(cards, list): raise DeckUsageEvidenceError("malformed provider board")
            for card in cards:
                card_name = card.get("name") if isinstance(card, dict) else None
                if card_name in card_ids: matches.setdefault(card_name, set()).add(board)
        population.append({"deck_id": deck_id, "deck_name": name, "format": fmt,
                           "matches": matches})
    records = []
    for card_name in PILOT_NAMES:
        associations = [{"deck_id": d["deck_id"], "deck_name": d["deck_name"],
                         "format": d["format"], "boards": sorted(d["matches"][card_name])}
                        for d in population if card_name in d["matches"]]
        associations.sort(key=lambda x: (x["format"], x["deck_id"]))
        format_counts = [{"format": f, "deck_count": sum(x["format"] == f for x in associations)}
                         for f in sorted({x["format"] for x in associations})]
        records.append({"card_id": card_ids[card_name], "card_name": card_name,
                        "provider_card_name": card_name, "metric": "represented_deck_count",
                        "numerator": len(associations), "denominator": len(population),
                        "dataset_timestamp": dataset_timestamp, "formats": format_counts,
                        "deck_associations": associations,
                        "completeness": "complete_for_provider_deck_snapshot",
                        "limitations": ["MTGJSON deck files are provider-curated deck products, not all played decks.",
                                        "A represented deck is counted once even when a card occurs on multiple boards."]})
    return {"schema_version": SCHEMA, "evidence_source_id": "phase-143-mtgjson-decks",
            "provider": "mtgjson", "provider_dataset": "AllDeckFiles.zip",
            "source_endpoint": "https://mtgjson.com/api/v5/AllDeckFiles.zip",
            "dataset_timestamp": dataset_timestamp, "retrieved_at": retrieved_at,
            "source_sha256": source_sha256, "source_byte_count": source_byte_count,
            "population_semantics": "All distinct provider deck files decoded from the snapshot; numerator is distinct files containing the exact card name and denominator is all decoded files.",
            "identity_mapping": "Exact MTGJSON card name mapped to the existing canonical Card name and ID.",
            "license_considerations": {"license": "MTGJSON project data is distributed under CC BY-SA 4.0; Wizards card data remains subject to its owners.", "url": "https://mtgjson.com/license/"},
            "retention_boundary": "Only ten aggregate records and their matching deck identities, formats, and boards are retained; the ZIP is transient.",
            "records": records, "records_sha256": hashlib.sha256(canonical_bytes(records)).hexdigest()}
