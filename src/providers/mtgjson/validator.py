"""Fail-closed, scope-aware validation for supplied MTGJSON v5 datasets."""
from __future__ import annotations

from collections import defaultdict
from datetime import datetime
import re
from typing import Any, Mapping

MINIMUM_SUPPORTED_MAJOR = 5
VERSION = re.compile(r"^(\d+)\.\d+\.\d+(?:[-+][0-9A-Za-z.-]+)?$")

# This is an explicit allow-list: an unknown third-party namespace is never assumed unique.
# MTGJSON UUID is validated separately as the authoritative printing identity.
IDENTIFIER_POLICY = {
    "scryfallId": {"provider": "Scryfall", "scope": "global", "uniqueness": "strict"},
    "scryfallOracleId": {"provider": "Scryfall", "scope": "card", "uniqueness": "scoped"},
    "oracleId": {"provider": "MTGJSON legacy/Scryfall", "scope": "card", "uniqueness": "scoped"},
    "scryfallIllustrationId": {"provider": "Scryfall", "scope": "illustration", "uniqueness": "scoped"},
}


class MTGJSONValidationError(ValueError):
    """A supplied reference dataset is not eligible for parsing."""


def _required_text(value: Mapping[str, Any], key: str, location: str) -> str:
    item = value.get(key)
    if not isinstance(item, str) or not item.strip():
        raise MTGJSONValidationError(f"{location}.{key} must be a non-empty string")
    return item


def _source_record(code: str, number: str, uuid: str, location: str,
                   identifier_value: str) -> dict[str, str]:
    return {"set_code": code, "collector_number": number, "mtgjson_uuid": uuid,
            "source_location": location, "source_identifier_value": identifier_value}


def identifier_findings(document: Mapping[str, Any], source_dataset: str = "MTGJSON AllPrintings") -> tuple[dict[str, Any], ...]:
    """Return deterministic duplicate-reference findings; strict collisions raise later."""
    occurrences: dict[tuple[str, str], list[dict[str, str]]] = defaultdict(list)
    for set_key, source_set in sorted(document["data"].items()):
        code = source_set["code"].casefold()
        for index, card in enumerate(source_set["cards"]):
            location = f"data.{set_key}.cards[{index}]"
            uuid, number = card["uuid"].casefold(), card["number"]
            for namespace, value in sorted(card.get("identifiers", {}).items()):
                if value:
                    occurrences[(namespace, value.casefold())].append(
                        _source_record(code, number, uuid, location, value))
    findings = []
    for (namespace, normalized), records in sorted(occurrences.items()):
        if len(records) < 2:
            continue
        policy = IDENTIFIER_POLICY.get(namespace, {
            "provider": namespace, "scope": "not-guaranteed", "uniqueness": "not-guaranteed"})
        # Card identifiers intentionally repeat on all printings of the same card.
        if policy["uniqueness"] == "scoped":
            continue
        strict = policy["uniqueness"] == "strict"
        findings.append({
            "severity": "error" if strict else "review-required",
            "code": "duplicate-global-external-identifier" if strict else "non-unique-external-reference",
            "identifier_namespace": namespace,
            "identifier_value": normalized,
            "provider": policy["provider"],
            "scope": policy["scope"],
            "affected_source_records": sorted(records, key=lambda row: (
                row["source_location"], row["mtgjson_uuid"])),
            "source_dataset": source_dataset,
            "explanation": ("The namespace is documented by this adapter as globally unique."
                            if strict else
                            "The third-party namespace has no provider guarantee of global uniqueness."),
            "disposition": ("reject dataset before mapping" if strict else
                            "preserve all references; require review before any unique mapping"),
        })
    return tuple(findings)


def validate_document(document: Any) -> tuple[dict[str, Any], ...]:
    """Validate the supported shape and return non-fatal identifier findings."""
    if not isinstance(document, dict) or not isinstance(document.get("meta"), dict):
        raise MTGJSONValidationError("dataset must contain a meta object")
    if not isinstance(document.get("data"), dict):
        raise MTGJSONValidationError("dataset must contain a data object")
    version = _required_text(document["meta"], "version", "meta")
    match = VERSION.fullmatch(version)
    if not match:
        raise MTGJSONValidationError("meta.version must be semantic version text")
    if int(match.group(1)) < MINIMUM_SUPPORTED_MAJOR:
        raise MTGJSONValidationError(f"unsupported MTGJSON schema version {version}; minimum supported major is {MINIMUM_SUPPORTED_MAJOR}")
    date = _required_text(document["meta"], "date", "meta")
    try:
        datetime.fromisoformat(date.replace("Z", "+00:00"))
    except ValueError as error:
        raise MTGJSONValidationError("meta.date must be ISO 8601") from error

    uuids: set[str] = set()
    for set_key, set_value in sorted(document["data"].items()):
        location = f"data.{set_key}"
        if not isinstance(set_key, str) or not isinstance(set_value, dict):
            raise MTGJSONValidationError(f"{location} must be an object")
        code = _required_text(set_value, "code", location)
        if code.casefold() != set_key.casefold():
            raise MTGJSONValidationError(f"{location}.code conflicts with its dataset key")
        _required_text(set_value, "name", location)
        cards = set_value.get("cards")
        if not isinstance(cards, list):
            raise MTGJSONValidationError(f"{location}.cards must be an array")
        for index, card in enumerate(cards):
            card_location = f"{location}.cards[{index}]"
            if not isinstance(card, dict):
                raise MTGJSONValidationError(f"{card_location} must be an object")
            uuid = _required_text(card, "uuid", card_location).casefold()
            _required_text(card, "name", card_location)
            _required_text(card, "number", card_location)
            if uuid in uuids:
                raise MTGJSONValidationError(f"duplicate printing identifier: {uuid}")
            uuids.add(uuid)
            identifiers = card.get("identifiers", {})
            if not isinstance(identifiers, dict) or any(not isinstance(key, str) or
                    not key.strip() or not isinstance(value, str) or not value.strip()
                    for key, value in identifiers.items()):
                raise MTGJSONValidationError(f"{card_location}.identifiers must map non-empty strings to non-empty strings")
    findings = identifier_findings(document)
    fatal = [item for item in findings if item["severity"] == "error"]
    if fatal:
        item = fatal[0]
        raise MTGJSONValidationError(
            f"duplicate globally unique external identifier {item['identifier_namespace']}:{item['identifier_value']}")
    return findings
