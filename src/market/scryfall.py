"""Scryfall bulk-data adapter for bounded production market acquisition.

Provider-shaped records terminate here.  Consumers receive only
``MarketObservation`` values and provider-neutral resolution diagnostics.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal, InvalidOperation
import hashlib
import json
from pathlib import Path
from typing import Any, Iterable, Mapping

from .intelligence import MarketObservation
from .models import MarketValidationError

PROVIDER = "scryfall"
ADAPTER_VERSION = "scryfall-market-adapter-v1"
SOURCE_DATASET = "scryfall-default-cards"


class ProviderAcquisitionError(RuntimeError):
    """The remote source failed before a trustworthy payload was available."""


class ProviderRateLimitError(ProviderAcquisitionError):
    """Scryfall explicitly rate limited the request."""


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def canonical_json(value: Any) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n").encode()


@dataclass(frozen=True)
class Resolution:
    status: str
    provider_id: str | None
    canonical_printing_id: str | None
    method: str | None
    confidence: str
    reason: str | None
    candidates: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {"status": self.status, "source_provider_identifier": self.provider_id,
                "canonical_printing_id": self.canonical_printing_id,
                "mapping_method": self.method, "confidence": self.confidence,
                "reason": self.reason, "candidates": list(self.candidates),
                "provenance": {"adapter": ADAPTER_VERSION, "provider": PROVIDER}}


class ScryfallMarketAdapter:
    """Validate, resolve, and normalize Scryfall default-card records."""

    def __init__(self, canonical_state: Mapping[str, Any], canonical_snapshot_identity: str,
                 verified_mappings: Mapping[str, str] | None = None):
        self.state = canonical_state
        self.snapshot = canonical_snapshot_identity
        self.verified = dict(verified_mappings or {})
        self.printings = canonical_state.get("printing", {})
        self._scryfall: dict[str, list[str]] = {}
        self._tuple: dict[tuple[str, str, str, str], list[str]] = {}
        for printing_id, entity in self.printings.items():
            values = entity.get("values", {})
            if values.get("set_id", "").lower() != "mb2":
                continue
            identifiers = values.get("identifiers", {})
            if identifiers.get("scryfallId"):
                self._scryfall.setdefault(identifiers["scryfallId"], []).append(printing_id)
            language = self._language(values.get("language"))
            for finish in values.get("finish_ids", []):
                key = (values.get("set_id", "").lower(), str(values.get("collector_number", "")),
                       language, str(finish).lower())
                self._tuple.setdefault(key, []).append(printing_id)

    @staticmethod
    def _language(value: Any) -> str:
        aliases = {"english": "en"}
        result = str(value or "").strip().lower()
        return aliases.get(result, result)

    @staticmethod
    def validate_record(record: Mapping[str, Any]) -> None:
        if not isinstance(record, Mapping):
            raise MarketValidationError("Scryfall record must be an object")
        required = ("id", "object", "set", "collector_number", "lang", "finishes", "prices")
        if any(key not in record for key in required):
            raise MarketValidationError("Scryfall record is missing required fields")
        if record["object"] != "card" or not isinstance(record["prices"], Mapping):
            raise MarketValidationError("invalid Scryfall card record")
        if not isinstance(record["finishes"], list) or not record["finishes"]:
            raise MarketValidationError("Scryfall finishes must be a non-empty array")

    def resolve(self, record: Mapping[str, Any], finish: str) -> Resolution:
        self.validate_record(record)
        provider_id = str(record["id"])
        if provider_id in self.verified:
            target = self.verified[provider_id]
            if target not in self.printings:
                return Resolution("rejected", provider_id, None, "verified_provider_mapping", "0",
                                  "verified mapping references an unknown printing")
            exact = self._scryfall.get(provider_id, [])
            if exact and target not in exact:
                return Resolution("rejected", provider_id, None, "verified_provider_mapping", "0",
                                  "verified mapping conflicts with canonical external identifier")
            return Resolution("matched", provider_id, target, "verified_provider_mapping", "1", None)
        exact = sorted(printing_id for printing_id in self._scryfall.get(provider_id, [])
            if finish.lower() in {str(value).lower() for value in
                self.printings[printing_id].get("values", {}).get("finish_ids", [])}
            and self._language(self.printings[printing_id].get("values", {}).get("language"))
                == self._language(record["lang"]))
        if len(exact) == 1:
            return Resolution("matched", provider_id, exact[0], "canonical_external_identifier", "1", None)
        if len(exact) > 1:
            return Resolution("ambiguous", provider_id, None, "canonical_external_identifier", "0",
                              "external identifier maps to multiple printings", tuple(exact))
        key = (str(record["set"]).lower(), str(record["collector_number"]),
               self._language(record["lang"]), finish.lower())
        candidates = sorted(self._tuple.get(key, []))
        if len(candidates) == 1:
            return Resolution("matched", provider_id, candidates[0], "set_collector_language_finish", "0.95", None)
        if len(candidates) > 1:
            return Resolution("ambiguous", provider_id, None, "set_collector_language_finish", "0",
                              "exact tuple maps to multiple printings", tuple(candidates))
        return Resolution("unmatched", provider_id, None, None, "0", "no exact production mapping")

    @staticmethod
    def _price(record: Mapping[str, Any], finish: str) -> Decimal | None:
        key = {"nonfoil": "usd", "foil": "usd_foil", "etched": "usd_etched"}.get(finish)
        value = record["prices"].get(key) if key else None
        if value is None:
            return None
        try:
            result = Decimal(str(value))
        except (InvalidOperation, ValueError) as error:
            raise MarketValidationError("Scryfall USD price must be decimal or null") from error
        if not result.is_finite() or result < 0:
            raise MarketValidationError("Scryfall USD price must be non-negative")
        return result

    def normalize(self, records: Iterable[Mapping[str, Any]], *, observed_at: datetime,
                  retrieved_at: datetime, source_url: str, source_digest: str
                  ) -> tuple[tuple[MarketObservation, ...], tuple[dict[str, Any], ...]]:
        observations, resolutions = [], []
        seen: dict[tuple[str, str], str] = {}
        for record in sorted(records, key=lambda item: str(item.get("id", ""))):
            self.validate_record(record)
            if str(record["set"]).lower() != "mb2":
                resolutions.append(Resolution("rejected", str(record["id"]), None, None, "0",
                                              "outside MB2 target").to_dict())
                continue
            for finish in sorted(set(str(x).lower() for x in record["finishes"])):
                resolution = self.resolve(record, finish)
                item = resolution.to_dict(); item["finish"] = finish; item["language"] = record["lang"]
                resolutions.append(item)
                if resolution.status != "matched":
                    continue
                identity = (str(record["id"]), finish)
                prior = seen.get(identity)
                if prior is not None and prior != resolution.canonical_printing_id:
                    raise MarketValidationError("conflicting provider mapping")
                seen[identity] = resolution.canonical_printing_id or ""
                observations.append(MarketObservation(
                    entity_type="printing", entity_id=resolution.canonical_printing_id or "",
                    provider=PROVIDER, observed_at=observed_at, recorded_at=retrieved_at,
                    price=self._price(record, finish), currency="USD", price_type="market",
                    finish=finish, provider_confidence=Decimal(resolution.confidence),
                    provenance={"adapter": ADAPTER_VERSION, "source_dataset": SOURCE_DATASET,
                        "source_url": source_url, "source_sha256": source_digest,
                        "source_provider_identifier": record["id"],
                        "mapping_method": resolution.method,
                        "canonical_snapshot_identity": self.snapshot}))
        return tuple(observations), tuple(resolutions)


def load_payload(payload: bytes) -> list[Mapping[str, Any]]:
    try:
        value = json.loads(payload)
    except json.JSONDecodeError as error:
        raise MarketValidationError("invalid Scryfall JSON payload") from error
    if not isinstance(value, list):
        raise MarketValidationError("Scryfall bulk payload must be an array")
    return value
