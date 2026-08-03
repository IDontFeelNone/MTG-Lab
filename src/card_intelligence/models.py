"""Immutable versioned contracts for asserted card knowledge.

The values in this module are assertions, not conclusions.  In particular, no
predicate is interpreted and no confidence score is combined by the engine.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from types import MappingProxyType
from typing import Any, Mapping
import re

FACT_SCHEMA = "card-knowledge-fact-v1"
_ID = re.compile(r"^[a-z0-9][a-z0-9._:-]*$")
_KINDS = frozenset({"legality", "archetype_usage", "popularity", "reprint_history",
    "reserved_status", "product_exclusivity", "scarcity", "supply", "demand",
    "synergy", "mechanical_theme", "tribal_theme", "combo", "tutor",
    "infinite_combo", "mana_acceleration", "removal", "card_advantage",
    "win_condition", "staple", "deck_role", "market_catalyst",
    "product_membership", "treatment_availability", "market_price_availability",
    "market_observation_coverage", "evidence_gap"})


class KnowledgeValidationError(ValueError):
    """A knowledge document violates the v1 contract."""


def _identifier(value: Any, label: str) -> str:
    if not isinstance(value, str) or not _ID.fullmatch(value):
        raise KnowledgeValidationError(f"{label} must be a stable lowercase identifier")
    return value


def _timestamp(value: datetime, label: str) -> datetime:
    if not isinstance(value, datetime) or value.tzinfo is None:
        raise KnowledgeValidationError(f"{label} must be timezone-aware")
    return value.astimezone(timezone.utc)


def _freeze(value: Any) -> Any:
    if isinstance(value, Mapping):
        return MappingProxyType({str(k): _freeze(v) for k, v in sorted(value.items())})
    if isinstance(value, (list, tuple)):
        return tuple(_freeze(v) for v in value)
    if value is None or isinstance(value, (str, bool, int)):
        return value
    if isinstance(value, float):
        raise KnowledgeValidationError("fact values must not use binary floating point")
    raise KnowledgeValidationError(f"unsupported fact value: {type(value).__name__}")


def thaw(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {k: thaw(v) for k, v in value.items()}
    if isinstance(value, tuple):
        return [thaw(v) for v in value]
    return value


def _iso(value: datetime) -> str:
    return value.isoformat().replace("+00:00", "Z")


@dataclass(frozen=True)
class Evidence:
    source_id: str
    source_type: str
    reference: str
    observed_at: datetime
    claim: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "source_id", _identifier(self.source_id, "source_id"))
        object.__setattr__(self, "source_type", _identifier(self.source_type, "source_type"))
        if not isinstance(self.reference, str) or not self.reference.strip():
            raise KnowledgeValidationError("evidence reference is required")
        if not isinstance(self.claim, str) or not self.claim.strip():
            raise KnowledgeValidationError("evidence claim is required")
        object.__setattr__(self, "observed_at", _timestamp(self.observed_at, "observed_at"))

    def to_dict(self) -> dict[str, Any]:
        return {"source_id": self.source_id, "source_type": self.source_type,
                "reference": self.reference, "observed_at": _iso(self.observed_at),
                "claim": self.claim}


@dataclass(frozen=True)
class KnowledgeFact:
    fact_id: str
    game_id: str
    card_id: str
    kind: str
    predicate: str
    value_status: str
    value: Any
    confidence: Decimal | None
    effective_at: datetime
    recorded_at: datetime
    evidence: tuple[Evidence, ...]
    supersedes: tuple[str, ...] = ()
    schema_version: str = FACT_SCHEMA

    def __post_init__(self) -> None:
        if self.schema_version != FACT_SCHEMA:
            raise KnowledgeValidationError("unsupported knowledge fact schema")
        for name in ("fact_id", "game_id", "card_id", "predicate"):
            object.__setattr__(self, name, _identifier(getattr(self, name), name))
        if self.kind not in _KINDS:
            raise KnowledgeValidationError("unsupported knowledge kind")
        if self.value_status not in {"known", "unknown"}:
            raise KnowledgeValidationError("value_status must be known or unknown")
        if (self.value_status == "unknown") != (self.value is None):
            raise KnowledgeValidationError("unknown values must be null and known values non-null")
        object.__setattr__(self, "value", _freeze(self.value))
        if self.confidence is not None:
            try:
                confidence = Decimal(str(self.confidence))
            except (InvalidOperation, ValueError) as error:
                raise KnowledgeValidationError("confidence must be between 0 and 1") from error
            if not confidence.is_finite() or not Decimal("0") <= confidence <= Decimal("1"):
                raise KnowledgeValidationError("confidence must be between 0 and 1")
            object.__setattr__(self, "confidence", confidence)
        object.__setattr__(self, "effective_at", _timestamp(self.effective_at, "effective_at"))
        object.__setattr__(self, "recorded_at", _timestamp(self.recorded_at, "recorded_at"))
        if self.effective_at > self.recorded_at:
            raise KnowledgeValidationError("effective_at cannot be later than recorded_at")
        evidence = tuple(self.evidence)
        if not evidence or any(not isinstance(item, Evidence) for item in evidence):
            raise KnowledgeValidationError("at least one valid evidence source is required")
        keys = [(x.source_id, x.reference, x.observed_at) for x in evidence]
        if len(keys) != len(set(keys)):
            raise KnowledgeValidationError("duplicate evidence source")
        object.__setattr__(self, "evidence", tuple(sorted(evidence,
            key=lambda x: (x.source_id, x.reference, x.observed_at))))
        supersedes = tuple(sorted(_identifier(x, "supersedes") for x in self.supersedes))
        if self.fact_id in supersedes or len(supersedes) != len(set(supersedes)):
            raise KnowledgeValidationError("invalid supersession references")
        object.__setattr__(self, "supersedes", supersedes)

    def to_dict(self) -> dict[str, Any]:
        return {"schema_version": self.schema_version, "fact_id": self.fact_id,
            "subject": {"game_id": self.game_id, "card_id": self.card_id},
            "kind": self.kind, "predicate": self.predicate,
            "value": {"status": self.value_status, "data": thaw(self.value)},
            "confidence": format(self.confidence, "f") if self.confidence is not None else None,
            "effective_at": _iso(self.effective_at), "recorded_at": _iso(self.recorded_at),
            "evidence": [x.to_dict() for x in self.evidence],
            "supersedes": list(self.supersedes)}
