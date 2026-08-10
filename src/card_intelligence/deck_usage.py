"""Bounded MTGJSON deck projection and strict retained-evidence review."""
from __future__ import annotations

import hashlib
import io
import json
from datetime import datetime
from pathlib import Path
from typing import Any
import zipfile

SCHEMA = "card-deck-usage-evidence-v1"
PILOT_NAMES = ("Brainstorm", "Command Tower", "Counterspell", "Goblin Charbelcher",
               "Goblin King", "Sol Ring", "Swords to Plowshares", "Treasure Cruise",
               "Walking Ballista", "Wishclaw Talisman")
ALLOWED_RECORD = {"card_id", "card_name", "provider_card_name", "metric", "numerator",
                  "denominator", "dataset_timestamp", "formats", "deck_associations",
                  "completeness", "limitations"}
HEX_DIGITS = frozenset("0123456789abcdef")
POPULATION_SEMANTICS = ("All distinct provider deck files decoded from the snapshot; numerator is "
                        "distinct files containing the exact card name and denominator is all decoded files.")
IDENTITY_MAPPING = ("Exact MTGJSON card name maps to canonical Card identity. MTGJSON code is optional "
                    "provider identity; ZIP member path is source-record identity; a path-derived MTG Lab "
                    "ID retains records without merging code collisions.")


def _is_sha256(value: object) -> bool:
    return isinstance(value, str) and len(value) == 64 and set(value) <= HEX_DIGITS


def _is_utc_timestamp(value: object) -> bool:
    if not isinstance(value, str) or not value.endswith("Z"):
        return False
    try:
        datetime.fromisoformat(value[:-1] + "+00:00")
    except ValueError:
        return False
    return True


class DeckUsageEvidenceError(ValueError):
    """A retained deck projection is malformed or ambiguous."""


def canonical_bytes(value: Any) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True, separators=(",", ": ")) + "\n").encode()


def decode_deck_archive(payload: bytes) -> list[dict[str, Any]]:
    """Decode every JSON member while retaining its provider source coordinate."""
    decks: list[dict[str, Any]] = []
    seen: dict[str, str] = {}
    with zipfile.ZipFile(io.BytesIO(payload)) as archive:
        members = sorted(
            (info for info in archive.infolist()
             if info.filename.endswith(".json") and not info.is_dir()),
            key=lambda info: info.filename,
        )
        for info in members:
            member_path = info.filename
            member_bytes = archive.read(info)
            content_sha256 = hashlib.sha256(member_bytes).hexdigest()
            if member_path in seen:
                reason = ("conflicting_source_record_content" if seen[member_path] != content_sha256
                          else "duplicate_source_record_identity")
                raise DeckUsageEvidenceError(
                    f"{reason}: member_path={member_path!r} "
                    f"member_path_sha256={hashlib.sha256(member_path.encode()).hexdigest()}"
                )
            seen[member_path] = content_sha256
            try:
                value = json.loads(member_bytes)
            except (UnicodeDecodeError, json.JSONDecodeError) as exc:
                raise DeckUsageEvidenceError(
                    f"malformed_deck_json: member_path={member_path!r}"
                ) from exc
            deck = value.get("data", value) if isinstance(value, dict) else value
            if not isinstance(deck, dict):
                raise DeckUsageEvidenceError(
                    f"malformed_deck_object: member_path={member_path!r}"
                )
            decks.append({"source_record_identity": member_path,
                          "source_content_sha256": content_sha256,
                          "deck": deck})
    return decks


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
    if (document["population_semantics"] != POPULATION_SEMANTICS or
            document["identity_mapping"] != IDENTITY_MAPPING):
        raise DeckUsageEvidenceError("unsupported population or identity semantics")
    if not _is_utc_timestamp(document["dataset_timestamp"]) or not _is_utc_timestamp(document["retrieved_at"]):
        raise DeckUsageEvidenceError("missing or malformed evidence timestamp")
    if not _is_sha256(document["source_sha256"]) or isinstance(document["source_byte_count"], bool) or not isinstance(document["source_byte_count"], int) or document["source_byte_count"] <= 0:
        raise DeckUsageEvidenceError("missing or malformed deterministic source identity")
    records = document["records"]
    if not isinstance(records, list) or len(records) != 10 or hashlib.sha256(canonical_bytes(records)).hexdigest() != document["records_sha256"]:
        raise DeckUsageEvidenceError("deck usage evidence must contain ten digest-bound records")
    names, ids, denominators = [], [], []
    for record in records:
        if not isinstance(record, dict) or set(record) != ALLOWED_RECORD:
            raise DeckUsageEvidenceError("record has missing or unsupported fields")
        names.append(record["card_name"]); ids.append(record["card_id"])
        numerator, denominator = record["numerator"], record["denominator"]
        denominators.append(denominator)
        if any(isinstance(v, bool) or not isinstance(v, int) for v in (numerator, denominator)) or not 0 <= numerator <= denominator:
            raise DeckUsageEvidenceError("invalid numerator or denominator")
        if record["metric"] != "represented_deck_count" or record["dataset_timestamp"] != document["dataset_timestamp"]:
            raise DeckUsageEvidenceError("invalid metric or conflicting timestamp")
        decks = record["deck_associations"]
        if not isinstance(decks, list) or not all(isinstance(x, dict) for x in decks):
            raise DeckUsageEvidenceError("duplicate or inconsistent deck associations")
        identities = [x.get("source_record_identity", x.get("deck_id")) for x in decks]
        if len(decks) != numerator or None in identities or len(set(identities)) != len(decks):
            raise DeckUsageEvidenceError("duplicate or inconsistent deck associations")
        for deck in decks:
            legacy = {"deck_id", "deck_name", "format", "boards"}
            current = {"provider_deck_identity", "source_record_identity", "retained_record_id",
                       "source_content_sha256", "deck_name", "format", "boards"}
            if set(deck) not in (legacy, current) or not isinstance(deck["boards"], list):
                raise DeckUsageEvidenceError("malformed deck association")
            if set(deck) == current and (deck["provider_deck_identity"] is not None and
                                         not isinstance(deck["provider_deck_identity"], str)):
                raise DeckUsageEvidenceError("malformed provider deck identity")
            if set(deck) == current and (
                    not isinstance(deck["source_record_identity"], str) or
                    not isinstance(deck["retained_record_id"], str) or
                    not isinstance(deck["source_content_sha256"], str) or
                    not _is_sha256(deck["source_content_sha256"])):
                raise DeckUsageEvidenceError("malformed source-record identity")
            if set(deck) == current and deck["retained_record_id"] != (
                    "mtgjson-deck-" + hashlib.sha256(
                        deck["source_record_identity"].encode()).hexdigest()):
                raise DeckUsageEvidenceError("retained record identity does not match source path")
        formats = record["formats"]
        if not isinstance(formats, list) or sum(x["deck_count"] for x in formats) != numerator:
            raise DeckUsageEvidenceError("format counts do not isolate the represented decks")
    if tuple(names) != PILOT_NAMES or len(ids) != len(set(ids)):
        raise DeckUsageEvidenceError("records must map the exact ten-card pilot once")
    if len(set(denominators)) != 1:
        raise DeckUsageEvidenceError("records must share one decoded-member denominator")
    return document


def project_decks(decks: list[dict[str, Any]], card_ids: dict[str, str], *, dataset_timestamp: str,
                  source_sha256: str, source_byte_count: int, retrieved_at: str) -> dict[str, Any]:
    """Project a decoded MTGJSON deck population; retain only pilot matches."""
    if set(card_ids) != set(PILOT_NAMES):
        raise DeckUsageEvidenceError("canonical mapping must contain the exact pilot")
    population: list[dict[str, Any]] = []
    seen_sources: dict[str, str] = {}
    for decoded in decks:
        if not isinstance(decoded, dict) or set(decoded) != {"source_record_identity", "source_content_sha256", "deck"}:
            raise DeckUsageEvidenceError("malformed_decoded_deck: required source coordinate unavailable")
        raw = decoded["deck"]
        source_identity = decoded["source_record_identity"]
        content_sha256 = decoded["source_content_sha256"]
        if (not isinstance(raw, dict) or not isinstance(source_identity, str) or not source_identity or
                not isinstance(content_sha256, str) or len(content_sha256) != 64 or
                any(character not in "0123456789abcdef" for character in content_sha256)):
            raise DeckUsageEvidenceError("malformed_decoded_deck: invalid source coordinate or content digest")
        if source_identity in seen_sources:
            reason = ("conflicting_source_record_content" if seen_sources[source_identity] != content_sha256
                      else "duplicate_source_record_identity")
            raise DeckUsageEvidenceError(
                f"{reason}: member_path={source_identity!r} "
                f"member_path_sha256={hashlib.sha256(source_identity.encode()).hexdigest()}"
            )
        seen_sources[source_identity] = content_sha256
        provider_identity_value = raw.get("code")
        provider_identity = (str(provider_identity_value).strip()
                             if provider_identity_value is not None else None)
        provider_identity = provider_identity or None
        name = str(raw.get("name") or "").strip(); fmt = str(raw.get("type") or "unknown").strip().casefold()
        if not name:
            raise DeckUsageEvidenceError(
                f"missing_deck_name: member_path={source_identity!r} "
                f"provider_id_present={provider_identity is not None} "
                f"top_level_keys={sorted(map(str, raw))[:20]}"
            )
        matches: dict[str, set[str]] = {}
        for board in ("commander", "mainBoard", "sideBoard"):
            cards = raw.get(board, [])
            if not isinstance(cards, list):
                raise DeckUsageEvidenceError(
                    f"malformed_provider_board: member_path={source_identity!r} board={board}"
                )
            for card in cards:
                card_name = card.get("name") if isinstance(card, dict) else None
                if card_name in card_ids: matches.setdefault(card_name, set()).add(board)
        population.append({"provider_deck_identity": provider_identity,
                           "source_record_identity": source_identity,
                           "retained_record_id": "mtgjson-deck-" + hashlib.sha256(source_identity.encode()).hexdigest(),
                           "source_content_sha256": content_sha256,
                           "deck_name": name, "format": fmt, "matches": matches})
    records = []
    for card_name in PILOT_NAMES:
        associations = [{"provider_deck_identity": d["provider_deck_identity"],
                         "source_record_identity": d["source_record_identity"],
                         "retained_record_id": d["retained_record_id"],
                         "source_content_sha256": d["source_content_sha256"],
                         "deck_name": d["deck_name"],
                         "format": d["format"], "boards": sorted(d["matches"][card_name])}
                        for d in population if card_name in d["matches"]]
        associations.sort(key=lambda x: (x["format"], x["source_record_identity"]))
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
            "population_semantics": POPULATION_SEMANTICS,
            "identity_mapping": IDENTITY_MAPPING,
            "license_considerations": {"license": "MTGJSON project data is distributed under CC BY-SA 4.0; Wizards card data remains subject to its owners.", "url": "https://mtgjson.com/license/"},
            "retention_boundary": "Only ten aggregate records and matching provider/source identities, content digests, literal names, formats, and boards are retained; the ZIP is transient.",
            "records": records, "records_sha256": hashlib.sha256(canonical_bytes(records)).hexdigest()}
