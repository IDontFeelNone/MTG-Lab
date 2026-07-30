"""Immutable values returned by the analytics engine."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from types import MappingProxyType
from typing import Any, Mapping


def _freeze(value: Any) -> Any:
    if isinstance(value, Mapping):
        return MappingProxyType({str(key): _freeze(item) for key, item in value.items()})
    if isinstance(value, (list, tuple)):
        return tuple(_freeze(item) for item in value)
    if isinstance(value, (str, int, float, bool, type(None))):
        return value
    raise TypeError(f"unsupported report value: {type(value).__name__}")


def thaw(value: Any) -> Any:
    """Convert frozen report values to JSON-compatible values."""
    if isinstance(value, Mapping):
        return {key: thaw(item) for key, item in value.items()}
    if isinstance(value, tuple):
        return [thaw(item) for item in value]
    return value


@dataclass(frozen=True)
class AnalyticsReport:
    """A versioned, immutable snapshot of one deterministic computation."""

    report_type: str
    generated_at: datetime
    inputs: Mapping[str, Any]
    data: Mapping[str, Any]
    schema_version: str = "analytics-report-v1"

    def __post_init__(self) -> None:
        if not self.report_type.strip():
            raise ValueError("report_type is required")
        if self.schema_version != "analytics-report-v1":
            raise ValueError(f"unsupported analytics report schema: {self.schema_version}")
        if self.generated_at.tzinfo is None:
            raise ValueError("generated_at must be timezone-aware")
        object.__setattr__(self, "generated_at", self.generated_at.astimezone(timezone.utc))
        object.__setattr__(self, "inputs", _freeze(self.inputs))
        object.__setattr__(self, "data", _freeze(self.data))

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "report_type": self.report_type,
            "generated_at": self.generated_at.isoformat().replace("+00:00", "Z"),
            "inputs": thaw(self.inputs),
            "data": thaw(self.data),
        }

    def to_json(self, *, indent: int | None = None) -> str:
        """Serialize with stable key ordering for storage or content hashing."""
        import json

        return json.dumps(self.to_dict(), indent=indent, sort_keys=True, separators=(",", ":") if indent is None else None)
