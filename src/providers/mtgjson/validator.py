"""Fail-closed validation for supplied MTGJSON v5 datasets."""
from __future__ import annotations

from datetime import datetime
import re
from typing import Any, Mapping

MINIMUM_SUPPORTED_MAJOR = 5
VERSION = re.compile(r"^(\d+)\.\d+\.\d+(?:[-+][0-9A-Za-z.-]+)?$")


class MTGJSONValidationError(ValueError):
    """A supplied reference dataset is not eligible for parsing."""


def _required_text(value: Mapping[str, Any], key: str, location: str) -> str:
    item = value.get(key)
    if not isinstance(item, str) or not item.strip():
        raise MTGJSONValidationError(f"{location}.{key} must be a non-empty string")
    return item


def validate_document(document: Any) -> None:
    """Validate the supported AllPrintings-style shape and identifier uniqueness."""
    if not isinstance(document, dict) or not isinstance(document.get("meta"), dict):
        raise MTGJSONValidationError("dataset must contain a meta object")
    if not isinstance(document.get("data"), dict):
        raise MTGJSONValidationError("dataset must contain a data object")
    version = _required_text(document["meta"], "version", "meta")
    match = VERSION.fullmatch(version)
    if not match:
        raise MTGJSONValidationError("meta.version must be semantic version text")
    if int(match.group(1)) < MINIMUM_SUPPORTED_MAJOR:
        raise MTGJSONValidationError(
            f"unsupported MTGJSON schema version {version}; minimum supported major is "
            f"{MINIMUM_SUPPORTED_MAJOR}")
    date = _required_text(document["meta"], "date", "meta")
    try:
        datetime.fromisoformat(date.replace("Z", "+00:00"))
    except ValueError as error:
        raise MTGJSONValidationError("meta.date must be ISO 8601") from error

    uuids: set[str] = set()
    printing_identifiers: dict[tuple[str, str], str] = {}
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
            if not isinstance(identifiers, dict) or any(
                    not isinstance(key, str) or not isinstance(value, str)
                    for key, value in identifiers.items()):
                raise MTGJSONValidationError(f"{card_location}.identifiers must map strings to strings")
            for namespace, value in identifiers.items():
                if not value or namespace in {"scryfallOracleId", "oracleId"}:
                    continue
                identity = (namespace, value.casefold())
                if identity in printing_identifiers:
                    raise MTGJSONValidationError(
                        f"duplicate external identifier {namespace}:{value}")
                printing_identifiers[identity] = uuid
