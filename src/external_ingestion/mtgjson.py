"""MTGJSON v5 provider adapter.

Provider knowledge is deliberately confined to this module.  Its output is the same
provider-neutral ``normalized`` envelope consumed by the Phase 88 ingestion boundary.
"""
from __future__ import annotations

import hashlib
import json
import re
import unicodedata
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable, Mapping

from .framework import DatasetManifest, ExternalDatasetError, FormatAdapter

PROVIDER = "MTGJSON"
PROVIDER_ID = "mtgjson"
SUPPORTED_MAJOR = 5
LICENSE = "Creative Commons Attribution 4.0 International (CC BY 4.0)"
ATTRIBUTION = "MTGJSON (https://mtgjson.com/)"
_ID = re.compile(r"^[0-9a-fA-F-]{8,}$")
_COLORS = frozenset("WUBRG")


def _unknown() -> dict[str, str]:
    return {"status": "unknown"}


def _stable_text(value: str) -> str:
    return " ".join(unicodedata.normalize("NFC", value).split())


class MTGJSONAdapter(FormatAdapter):
    """Strict adapter for MTGJSON v5 AllPrintings-style JSON documents."""

    extensions = (".json",)
    content_type = "application/json"

    def document(self, payload: bytes) -> Mapping[str, Any]:
        try:
            value = json.loads(payload)
        except (UnicodeDecodeError, json.JSONDecodeError) as error:
            raise ExternalDatasetError("invalid MTGJSON JSON") from error
        if not isinstance(value, dict) or not isinstance(value.get("meta"), dict) or not isinstance(value.get("data"), dict):
            raise ExternalDatasetError("not an MTGJSON dataset: expected meta and data objects")
        version = value["meta"].get("version")
        if not isinstance(version, str) or not re.fullmatch(r"\d+\.\d+\.\d+(?:[-+][0-9A-Za-z.-]+)?", version):
            raise ExternalDatasetError("MTGJSON meta.version is required")
        if int(version.split(".", 1)[0]) != SUPPORTED_MAJOR:
            raise ExternalDatasetError(f"unsupported MTGJSON version: {version}; supported major is 5")
        generated = value["meta"].get("date")
        try:
            datetime.fromisoformat(str(generated).replace("Z", "+00:00"))
        except ValueError as error:
            raise ExternalDatasetError("MTGJSON meta.date must be ISO 8601") from error
        return value

    def metadata(self, payload: bytes, dataset_name: str) -> dict[str, Any]:
        doc = self.document(payload)
        return {"provider": PROVIDER, "provider_id": PROVIDER_ID,
                "mtgjson_version": doc["meta"]["version"], "dataset_name": dataset_name,
                "generation_timestamp": doc["meta"]["date"], "license": LICENSE,
                "source_attribution": ATTRIBUTION}

    def records(self, payload: bytes) -> Iterable[Mapping[str, Any]]:
        doc = self.document(payload)
        output: list[dict[str, Any]] = []
        printing_ids: set[str] = set()
        card_fingerprints: dict[str, tuple[Any, ...]] = {}
        for set_code, source_set in sorted(doc["data"].items()):
            if not isinstance(source_set, dict) or not isinstance(source_set.get("cards"), list):
                raise ExternalDatasetError(f"unsupported MTGJSON record: set {set_code!r} has no cards array")
            code = str(source_set.get("code", set_code)).lower()
            if code != str(set_code).lower() or not re.fullmatch(r"[a-z0-9]+", code):
                raise ExternalDatasetError(f"MTGJSON set identifier conflict: {set_code}")
            set_name = source_set.get("name")
            if not isinstance(set_name, str) or not set_name.strip():
                raise ExternalDatasetError(f"MTGJSON set {set_code} is missing name")
            output.append({"id": f"set-{code}", "entity_type": "set", "normalized": {
                "entity_type": "set", "canonical_identifier": f"set-{code}", "name": _stable_text(set_name),
                "code": code, "release_date": source_set.get("releaseDate", _unknown())},
                "unsupported_fields": sorted(k for k in source_set if k not in {"cards", "code", "name", "releaseDate"})})
            for index, card in enumerate(source_set["cards"]):
                if not isinstance(card, dict):
                    raise ExternalDatasetError(f"malformed MTGJSON card at {set_code}[{index}]")
                self._add_card(output, card, code, printing_ids, card_fingerprints)
        return output

    def _add_card(self, output: list[dict[str, Any]], card: Mapping[str, Any], set_code: str,
                  printing_ids: set[str], fingerprints: dict[str, tuple[Any, ...]]) -> None:
        required = ("uuid", "name", "number")
        missing = [key for key in required if not isinstance(card.get(key), str) or not card[key].strip()]
        if missing:
            raise ExternalDatasetError("malformed MTGJSON card missing: " + ", ".join(missing))
        uuid = card["uuid"].lower()
        if not _ID.fullmatch(uuid):
            raise ExternalDatasetError(f"malformed MTGJSON uuid: {card['uuid']}")
        if uuid in printing_ids:
            raise ExternalDatasetError(f"duplicate MTGJSON printing identifier: {uuid}")
        printing_ids.add(uuid)
        identifiers = card.get("identifiers", {})
        if not isinstance(identifiers, dict) or any(not isinstance(k, str) or not isinstance(v, str) for k, v in identifiers.items()):
            raise ExternalDatasetError(f"malformed MTGJSON identifiers for {uuid}")
        values = [v for v in identifiers.values() if v]
        if len(values) != len(set(values)):
            raise ExternalDatasetError(f"identifier conflict within MTGJSON printing: {uuid}")
        colors = card.get("colors")
        if colors is not None and (not isinstance(colors, list) or any(c not in _COLORS for c in colors) or len(colors) != len(set(colors))):
            raise ExternalDatasetError(f"malformed MTGJSON colors for {uuid}")
        name = _stable_text(card["name"])
        layout = card.get("layout", _unknown())
        mana = card.get("manaCost", _unknown())
        fingerprint = (name.casefold(), json.dumps(layout, sort_keys=True), json.dumps(colors, sort_keys=True), json.dumps(mana, sort_keys=True))
        oracle = identifiers.get("scryfallOracleId") or card.get("identifiers", {}).get("oracleId")
        card_id = "card-" + (oracle.lower() if oracle and _ID.fullmatch(oracle) else hashlib.sha256("\0".join(map(str, fingerprint)).encode()).hexdigest())
        prior = fingerprints.setdefault(card_id, fingerprint)
        if prior != fingerprint:
            raise ExternalDatasetError(f"identifier conflict for canonical card: {card_id}")
        if prior == fingerprint and not any(row["id"] == card_id for row in output):
            output.append({"id": card_id, "entity_type": "card", "normalized": {
                "entity_type": "card", "canonical_identifier": card_id, "game": "magic-the-gathering",
                "name": name, "normalized_name": name.casefold(), "layout": layout,
                "colors": sorted(colors) if colors is not None else _unknown(), "mana_cost": mana},
                "unsupported_fields": sorted(k for k in card if k not in {"uuid", "name", "number", "identifiers", "rarity", "layout", "colors", "manaCost"})})
        output.append({"id": f"printing-{uuid}", "entity_type": "printing", "normalized": {
            "entity_type": "printing", "canonical_identifier": f"printing-{uuid}", "card_id": card_id,
            "set_id": f"set-{set_code}", "collector_number": _stable_text(card["number"]),
            "language": "en", "rarity": card.get("rarity", _unknown()),
            "identifiers": {k: identifiers[k] for k in sorted(identifiers)}},
            "unsupported_fields": []})


def detect_mtgjson(source: Path | str) -> dict[str, Any]:
    path = Path(source)
    if not path.is_file():
        raise ExternalDatasetError("MTGJSON dataset file is missing")
    payload = path.read_bytes(); adapter = MTGJSONAdapter()
    metadata = adapter.metadata(payload, path.stem)
    return {"detected": True, "adapter": "mtgjson-v1", **metadata,
            "record_count": len(list(adapter.records(payload)))}


def generate_manifest(source: Path | str) -> DatasetManifest:
    path = Path(source); payload = path.read_bytes(); adapter = MTGJSONAdapter()
    metadata = adapter.metadata(payload, path.stem)
    generated = str(metadata["generation_timestamp"])
    publication_date = generated[:10]
    logical = re.sub(r"[^a-z0-9]+", "-", path.stem.lower()).strip("-") or "mtgjson-dataset"
    return DatasetManifest(path.stem, logical, str(metadata["mtgjson_version"]), PROVIDER,
                           publication_date, ATTRIBUTION, LICENSE, ("card", "printing", "set"),
                           "mtgjson-v5", hashlib.sha256(payload).hexdigest(), path.name,
                           "Generated deterministically by the MTGJSON provider adapter")
