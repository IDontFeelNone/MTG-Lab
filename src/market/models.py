"""Validated immutable values exchanged by market providers and services."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
import re
from types import MappingProxyType
from typing import Any, Mapping


class MarketValidationError(ValueError):
    """Market data does not satisfy the provider contract."""


_IDENTIFIER = re.compile(r"^[a-z0-9][a-z0-9._-]*$")


def validate_identifier(value: str, label: str) -> str:
    value = str(value).strip()
    if not _IDENTIFIER.fullmatch(value):
        raise MarketValidationError(f"{label} must be a stable lowercase identifier")
    return value


def normalize_timestamp(value: datetime) -> datetime:
    if not isinstance(value, datetime) or value.tzinfo is None:
        raise MarketValidationError("timestamp must be a timezone-aware datetime")
    return value.astimezone(timezone.utc)


def _money(value: Any, label: str) -> Decimal | None:
    if value is None:
        return None
    if isinstance(value, bool):
        raise MarketValidationError(f"{label} must be a non-negative number")
    try:
        result = Decimal(str(value))
    except (InvalidOperation, ValueError) as error:
        raise MarketValidationError(f"{label} must be a non-negative number") from error
    if not result.is_finite() or result < 0:
        raise MarketValidationError(f"{label} must be a non-negative number")
    return result


def _immutable(value: Any) -> Any:
    if isinstance(value, Mapping):
        return MappingProxyType({str(key): _immutable(item) for key, item in value.items()})
    if isinstance(value, (list, tuple)):
        return tuple(_immutable(item) for item in value)
    if isinstance(value, (str, int, float, bool, type(None))):
        return value
    raise MarketValidationError(f"metadata contains unsupported value: {type(value).__name__}")


def mutable_metadata(value: Mapping[str, Any]) -> dict[str, Any]:
    def convert(item: Any) -> Any:
        if isinstance(item, Mapping):
            return {key: convert(child) for key, child in item.items()}
        if isinstance(item, tuple):
            return [convert(child) for child in item]
        return item
    return convert(value)


@dataclass(frozen=True)
class PriceValues:
    """Optional price points for one finish or an unspecified finish."""

    latest: Decimal | None = None
    low: Decimal | None = None
    market: Decimal | None = None
    high: Decimal | None = None

    def __post_init__(self) -> None:
        for name in ("latest", "low", "market", "high"):
            object.__setattr__(self, name, _money(getattr(self, name), name))
        if all(getattr(self, name) is None for name in ("latest", "low", "market", "high")):
            raise MarketValidationError("at least one price value is required")

    def to_dict(self) -> dict[str, str]:
        return {name: format(value, "f") for name in ("latest", "low", "market", "high")
                if (value := getattr(self, name)) is not None}


@dataclass(frozen=True)
class ProviderResponse:
    """A provider's partial response before service normalization."""

    printing_id: str
    provider: str
    timestamp: datetime
    values: PriceValues | None = None
    variants: Mapping[str, PriceValues] = field(default_factory=dict)
    currency: str = "USD"
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "printing_id", validate_identifier(self.printing_id, "printing_id"))
        object.__setattr__(self, "provider", validate_identifier(self.provider, "provider"))
        object.__setattr__(self, "timestamp", normalize_timestamp(self.timestamp))
        currency = str(self.currency).strip().upper()
        if len(currency) != 3 or not currency.isalpha():
            raise MarketValidationError("currency must be a three-letter code")
        object.__setattr__(self, "currency", currency)
        variants = {validate_identifier(name, "variant"): value
                    for name, value in self.variants.items()}
        if any(not isinstance(value, PriceValues) for value in variants.values()):
            raise MarketValidationError("variant values must be PriceValues")
        if self.values is not None and not isinstance(self.values, PriceValues):
            raise MarketValidationError("values must be PriceValues")
        if self.values is None and not variants:
            raise MarketValidationError("response must contain values or variants")
        object.__setattr__(self, "variants", MappingProxyType(dict(sorted(variants.items()))))
        object.__setattr__(self, "metadata", _immutable(self.metadata))


@dataclass(frozen=True)
class MarketSnapshot:
    """Immutable normalized market observation referencing one canonical printing."""

    printing_id: str
    provider: str
    timestamp: datetime
    retrieved_at: datetime
    currency: str
    values: PriceValues | None = None
    variants: Mapping[str, PriceValues] = field(default_factory=dict)
    provenance: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        response = ProviderResponse(self.printing_id, self.provider, self.timestamp,
                                    self.values, self.variants, self.currency, self.provenance)
        object.__setattr__(self, "printing_id", response.printing_id)
        object.__setattr__(self, "provider", response.provider)
        object.__setattr__(self, "timestamp", response.timestamp)
        object.__setattr__(self, "currency", response.currency)
        object.__setattr__(self, "variants", response.variants)
        object.__setattr__(self, "provenance", response.metadata)
        retrieved = normalize_timestamp(self.retrieved_at)
        if response.timestamp > retrieved:
            raise MarketValidationError("provider timestamp cannot be later than retrieved_at")
        object.__setattr__(self, "retrieved_at", retrieved)

    @property
    def snapshot_id(self) -> str:
        stamp = self.retrieved_at.strftime("%Y%m%dT%H%M%S.%fZ")
        return f"{self.provider}-{self.printing_id}-{stamp}"

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": "market-snapshot-v1", "snapshot_id": self.snapshot_id,
            "printing_id": self.printing_id, "provider": self.provider,
            "timestamp": self.timestamp.isoformat().replace("+00:00", "Z"),
            "retrieved_at": self.retrieved_at.isoformat().replace("+00:00", "Z"),
            "currency": self.currency,
            "values": self.values.to_dict() if self.values else None,
            "variants": {name: value.to_dict() for name, value in self.variants.items()},
            "provenance": mutable_metadata(self.provenance),
        }
