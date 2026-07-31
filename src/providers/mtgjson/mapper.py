"""Deterministic MTGJSON-to-candidate mapping.

These records are evidence candidates only.  This module has no canonical repository access.
"""
from __future__ import annotations

import hashlib
import json
import unicodedata
from typing import Any, Mapping

SUPPORTED_SET_FIELDS = frozenset({"cards", "code", "name", "releaseDate", "languages"})
SUPPORTED_CARD_FIELDS = frozenset({
    "uuid", "name", "number", "identifiers", "rarity", "language", "finishes",
    "layout", "colors", "manaCost",
})


def _text(value: str) -> str:
    return " ".join(unicodedata.normalize("NFC", value).split())


def _unknown() -> dict[str, str]:
    return {"status": "unknown"}


def _identity(kind: str, value: Any) -> str:
    encoded = json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True)
    return f"mtgjson:{kind}:{hashlib.sha256(encoded.encode()).hexdigest()}"


def _record(kind: str, source: Mapping[str, Any], mapped: Mapping[str, Any],
            supported: frozenset[str], natural_key: Any) -> dict[str, Any]:
    return {"candidate_identifier": _identity(kind, natural_key), "entity_type": kind,
            "mapped_fields": dict(mapped),
            "unknown_fields": {key: source[key] for key in sorted(source) if key not in supported}}


def map_dataset(document: Mapping[str, Any]) -> tuple[dict[str, Any], ...]:
    """Map sets and their cards into stable, explicit candidate records."""
    records: list[dict[str, Any]] = []
    seen_cards: set[str] = set()
    seen_reference: set[tuple[str, str]] = set()
    for set_key, source_set in sorted(document["data"].items()):
        code = source_set["code"].casefold()
        records.append(_record("set", source_set, {
            "code": code, "name": _text(source_set["name"]),
            "release_date": source_set.get("releaseDate", _unknown()),
        }, SUPPORTED_SET_FIELDS, code))
        for source_card in sorted(source_set["cards"], key=lambda card: card["uuid"].casefold()):
            uuid = source_card["uuid"].casefold()
            identifiers = {key: source_card.get("identifiers", {})[key]
                           for key in sorted(source_card.get("identifiers", {}))}
            oracle = identifiers.get("scryfallOracleId") or identifiers.get("oracleId")
            card_key = oracle.casefold() if oracle else _identity("card-fallback", {
                "name": _text(source_card["name"]).casefold(),
                "layout": source_card.get("layout", _unknown()),
                "mana_cost": source_card.get("manaCost", _unknown()),
            })
            if card_key not in seen_cards:
                seen_cards.add(card_key)
                records.append(_record("card", source_card, {
                    "name": _text(source_card["name"]),
                    "normalized_name": _text(source_card["name"]).casefold(),
                    "card_reference": card_key,
                    "layout": source_card.get("layout", _unknown()),
                    "colors": sorted(source_card["colors"]) if "colors" in source_card else _unknown(),
                    "mana_cost": source_card.get("manaCost", _unknown()),
                }, SUPPORTED_CARD_FIELDS, card_key))
            language = source_card.get("language", "English")
            rarity = source_card.get("rarity", _unknown())
            finishes = source_card.get("finishes", _unknown())
            records.append(_record("printing", source_card, {
                "uuid": uuid, "card_reference": card_key, "set_code": code,
                "collector_number": _text(source_card["number"]), "language": language,
                "rarity": rarity, "finishes": finishes, "identifiers": identifiers,
            }, SUPPORTED_CARD_FIELDS, uuid))
            references = (("language", language), ("rarity", rarity))
            if isinstance(finishes, list):
                references += tuple(("finish", finish) for finish in finishes)
            for kind, value in references:
                if isinstance(value, str) and (kind, value) not in seen_reference:
                    seen_reference.add((kind, value))
                    records.append(_record(kind, {}, {"value": value}, frozenset(), value))
            for namespace, value in identifiers.items():
                records.append(_record("identifier", {}, {
                    "namespace": namespace, "value": value, "printing_uuid": uuid,
                }, frozenset(), (namespace, value, uuid)))
    return tuple(sorted(records, key=lambda item: item["candidate_identifier"]))
