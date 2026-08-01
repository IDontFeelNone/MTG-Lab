"""Versioned provider-neutral market observations and deterministic analytics."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation, ROUND_HALF_EVEN, localcontext
import hashlib
import json
import os
from pathlib import Path
from types import MappingProxyType
from typing import Any, Iterable, Mapping

from .models import MarketValidationError, normalize_timestamp, validate_identifier

SCHEMA_VERSION = "market-observation-v1"
ANALYTICS_VERSION = "market-analytics-v1"
_Q = Decimal("0.000001")


def _decimal(value: Any, name: str, *, optional: bool = True) -> Decimal | None:
    if value is None and optional:
        return None
    try:
        result = Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError) as error:
        raise MarketValidationError(f"{name} must be a finite decimal") from error
    if not result.is_finite() or result < 0:
        raise MarketValidationError(f"{name} must be a non-negative finite decimal")
    return result


def _plain(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {str(k): _plain(v) for k, v in sorted(value.items())}
    if isinstance(value, (list, tuple)): return [_plain(v) for v in value]
    if isinstance(value, Decimal): return format(value, "f")
    if isinstance(value, (str, int, float, bool, type(None))): return value
    raise MarketValidationError(f"unsupported provenance value: {type(value).__name__}")


def _frozen(value: Mapping[str, Any]) -> Mapping[str, Any]:
    def freeze(item: Any) -> Any:
        if isinstance(item, Mapping): return MappingProxyType({str(k): freeze(v) for k, v in item.items()})
        if isinstance(item, (list, tuple)): return tuple(freeze(v) for v in item)
        return item
    return freeze(_plain(value))


def _stamp(value: datetime) -> str:
    return normalize_timestamp(value).isoformat().replace("+00:00", "Z")


@dataclass(frozen=True)
class MarketObservation:
    """One immutable provider assertion; absence of ``price`` is an explicit unknown."""

    entity_type: str
    entity_id: str
    provider: str
    observed_at: datetime
    recorded_at: datetime
    price: Decimal | None
    currency: str = "USD"
    price_type: str = "market"
    finish: str | None = None
    buylist_price: Decimal | None = None
    listing_count: int | None = None
    sales_count: int | None = None
    spread: Decimal | None = None
    provider_confidence: Decimal | None = None
    provenance: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.entity_type not in {"card", "printing", "product"}:
            raise MarketValidationError("entity_type must be card, printing, or product")
        object.__setattr__(self, "entity_id", validate_identifier(self.entity_id, "entity_id"))
        object.__setattr__(self, "provider", validate_identifier(self.provider, "provider"))
        object.__setattr__(self, "observed_at", normalize_timestamp(self.observed_at))
        object.__setattr__(self, "recorded_at", normalize_timestamp(self.recorded_at))
        if self.observed_at > self.recorded_at: raise MarketValidationError("observed_at cannot follow recorded_at")
        currency = str(self.currency).upper().strip()
        if len(currency) != 3 or not currency.isalpha(): raise MarketValidationError("currency must be a three-letter code")
        object.__setattr__(self, "currency", currency)
        object.__setattr__(self, "price_type", validate_identifier(self.price_type, "price_type"))
        if self.finish is not None: object.__setattr__(self, "finish", validate_identifier(self.finish, "finish"))
        for name in ("price", "buylist_price", "spread", "provider_confidence"):
            object.__setattr__(self, name, _decimal(getattr(self, name), name))
        if self.provider_confidence is not None and self.provider_confidence > 1:
            raise MarketValidationError("provider_confidence must be between zero and one")
        for name in ("listing_count", "sales_count"):
            value = getattr(self, name)
            if value is not None and (isinstance(value, bool) or not isinstance(value, int) or value < 0):
                raise MarketValidationError(f"{name} must be a non-negative integer")
        if not self.provenance: raise MarketValidationError("provenance is required")
        object.__setattr__(self, "provenance", _frozen(self.provenance))

    def payload(self) -> dict[str, Any]:
        return {"schema_version": SCHEMA_VERSION, "entity_type": self.entity_type,
                "entity_id": self.entity_id, "provider": self.provider,
                "observed_at": _stamp(self.observed_at), "recorded_at": _stamp(self.recorded_at),
                "price": _plain(self.price), "currency": self.currency, "price_type": self.price_type,
                "finish": self.finish, "buylist_price": _plain(self.buylist_price),
                "listing_count": self.listing_count, "sales_count": self.sales_count,
                "spread": _plain(self.spread), "provider_confidence": _plain(self.provider_confidence),
                "provenance": _plain(self.provenance)}

    @property
    def observation_id(self) -> str:
        encoded = json.dumps(self.payload(), sort_keys=True, separators=(",", ":")).encode()
        return hashlib.sha256(encoded).hexdigest()

    def to_dict(self) -> dict[str, Any]:
        return {**self.payload(), "observation_id": self.observation_id}

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> "MarketObservation":
        if value.get("schema_version") != SCHEMA_VERSION: raise MarketValidationError("unsupported market observation schema")
        result = cls(entity_type=value["entity_type"], entity_id=value["entity_id"], provider=value["provider"],
            observed_at=datetime.fromisoformat(value["observed_at"].replace("Z", "+00:00")),
            recorded_at=datetime.fromisoformat(value["recorded_at"].replace("Z", "+00:00")),
            price=value.get("price"), currency=value.get("currency", "USD"), price_type=value.get("price_type", "market"),
            finish=value.get("finish"), buylist_price=value.get("buylist_price"), listing_count=value.get("listing_count"),
            sales_count=value.get("sales_count"), spread=value.get("spread"), provider_confidence=value.get("provider_confidence"),
            provenance=value.get("provenance", {}))
        if value.get("observation_id") != result.observation_id: raise MarketValidationError("observation integrity check failed")
        return result


class MarketObservationRepository:
    """Separate append-only storage; canonical repositories are never accepted or written."""

    def __init__(self, root: Path): self.root = Path(root)

    def append(self, observation: MarketObservation) -> Path:
        if not isinstance(observation, MarketObservation): raise MarketValidationError("only MarketObservation may be appended")
        path = self.root / observation.entity_type / observation.entity_id / observation.provider / f"{observation.observation_id}.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        content = json.dumps(observation.to_dict(), indent=2, sort_keys=True) + "\n"
        try: fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644)
        except FileExistsError as error:
            # A retry may safely reuse an identity only when the complete serialized
            # bytes are identical.  Tampering or identity reuse fails closed.
            if path.read_bytes() == content.encode("utf-8"):
                return path
            raise MarketValidationError("observation identity exists with different bytes") from error
        with os.fdopen(fd, "w", encoding="utf-8") as stream: stream.write(content)
        return path

    def load(self, path: Path) -> MarketObservation:
        path = Path(path)
        try: result = MarketObservation.from_dict(json.loads(path.read_text(encoding="utf-8")))
        except (KeyError, TypeError, ValueError, json.JSONDecodeError) as error:
            if isinstance(error, MarketValidationError): raise
            raise MarketValidationError(f"invalid market observation: {path}") from error
        expected = self.root / result.entity_type / result.entity_id / result.provider / f"{result.observation_id}.json"
        if path.resolve() != expected.resolve(): raise MarketValidationError("observation path does not match content")
        return result

    def observations(self, *, entity_type: str | None = None, entity_id: str | None = None,
                     provider: str | None = None, currency: str | None = None,
                     price_type: str | None = None, finish: str | None = None) -> tuple[MarketObservation, ...]:
        values = (self.load(p) for p in sorted(self.root.glob("*/*/*/*.json")))
        filtered = [x for x in values if (entity_type is None or x.entity_type == entity_type)
            and (entity_id is None or x.entity_id == entity_id) and (provider is None or x.provider == provider)
            and (currency is None or x.currency == currency.upper()) and (price_type is None or x.price_type == price_type)
            and (finish is None or x.finish == finish)]
        return tuple(sorted(filtered, key=lambda x: (x.observed_at, x.recorded_at, x.provider, x.observation_id)))


class MarketAnalytics:
    """Pure calculations over supplied observations; it contains no adapters."""

    @staticmethod
    def _prices(values: Iterable[MarketObservation]) -> list[MarketObservation]:
        return sorted((x for x in values if x.price is not None), key=lambda x: (x.observed_at, x.observation_id))

    @staticmethod
    def _render(value: Decimal | None) -> str | None:
        return None if value is None else format(value.quantize(_Q, rounding=ROUND_HALF_EVEN), "f")

    def summarize(self, observations: Iterable[MarketObservation], *, as_of: datetime | None = None) -> dict[str, Any]:
        all_values = list(observations)
        if as_of is not None:
            cutoff = normalize_timestamp(as_of); all_values = [x for x in all_values if x.observed_at <= cutoff]
        values = self._prices(all_values)
        latest = values[-1] if values else None
        def change(days: int) -> Decimal | None:
            if latest is None: return None
            prior = [x for x in values if x.observed_at <= latest.observed_at - timedelta(days=days)]
            if not prior or prior[-1].price == 0: return None
            return (latest.price - prior[-1].price) / prior[-1].price
        average = sum((x.price for x in values), Decimal(0)) / len(values) if values else None
        result = {"schema_version": ANALYTICS_VERSION, "status": "known" if latest else "unknown",
            "current_market_value": self._render(latest.price if latest else None), "average_market_value": self._render(average),
            "historical_trend": self._render(change(30)), "daily_change": self._render(change(1)),
            "weekly_change": self._render(change(7)), "monthly_change": self._render(change(30)),
            "moving_averages": {str(d): self._render(self.moving_average(values, d)) for d in (7, 30, 90)},
            "price_volatility": self._render(self.volatility(values)),
            "liquidity_score": self._render(self.liquidity(all_values)),
            "confidence": self._render(self.confidence(all_values)), "observation_count": len(all_values),
            "priced_observation_count": len(values), "provider": latest.provider if latest else None,
            "timestamp": _stamp(latest.observed_at) if latest else None,
            "provenance": _plain(latest.provenance) if latest else []}
        return result

    def moving_average(self, values: Iterable[MarketObservation], days: int) -> Decimal | None:
        prices = self._prices(values)
        if not prices or days < 1: return None
        selected = [x.price for x in prices if x.observed_at >= prices[-1].observed_at - timedelta(days=days)]
        return sum(selected, Decimal(0)) / len(selected)

    def volatility(self, values: Iterable[MarketObservation]) -> Decimal | None:
        prices = self._prices(values)
        returns = [(b.price - a.price) / a.price for a, b in zip(prices, prices[1:]) if a.price != 0]
        if not returns: return None
        mean = sum(returns, Decimal(0)) / len(returns)
        with localcontext() as context:
            context.prec = 28
            return (sum(((x - mean) ** 2 for x in returns), Decimal(0)) / len(returns)).sqrt()

    def liquidity(self, values: Iterable[MarketObservation]) -> Decimal | None:
        latest = sorted(values, key=lambda x: (x.observed_at, x.observation_id))[-1] if values else None
        if latest is None or latest.listing_count is None or latest.sales_count is None or latest.spread is None: return None
        depth = min(Decimal(latest.listing_count) / Decimal(100), Decimal(1))
        sales = min(Decimal(latest.sales_count) / Decimal(30), Decimal(1))
        spread = max(Decimal(0), Decimal(1) - min(latest.spread, Decimal(1)))
        return (depth + sales + spread) / Decimal(3)

    def confidence(self, values: Iterable[MarketObservation]) -> Decimal | None:
        latest = sorted(values, key=lambda x: (x.observed_at, x.observation_id))[-1] if values else None
        if latest is None or latest.provider_confidence is None: return None
        completeness = sum(x is not None for x in (latest.price, latest.listing_count, latest.sales_count, latest.spread))
        return (latest.provider_confidence * Decimal(4) + Decimal(completeness) / Decimal(4)) / Decimal(5)
