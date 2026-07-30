"""Immutable, serializable values produced by the Decision Engine."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from types import MappingProxyType
from typing import Any, Mapping


def freeze(value: Any) -> Any:
    if isinstance(value, Mapping):
        return MappingProxyType({str(k): freeze(v) for k, v in value.items()})
    if isinstance(value, (list, tuple)):
        return tuple(freeze(v) for v in value)
    if isinstance(value, (str, int, float, bool, type(None))):
        return value
    raise TypeError(f"unsupported decision value: {type(value).__name__}")


def thaw(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {k: thaw(v) for k, v in value.items()}
    if isinstance(value, tuple):
        return [thaw(v) for v in value]
    return value


@dataclass(frozen=True)
class AnalyticsFact:
    report_type: str
    path: str
    value: Any
    inputs: Mapping[str, Any]

    def __post_init__(self) -> None:
        object.__setattr__(self, "value", freeze(self.value))
        object.__setattr__(self, "inputs", freeze(self.inputs))

    def to_dict(self) -> dict[str, Any]:
        return {"report_type": self.report_type, "path": self.path,
                "value": thaw(self.value), "inputs": thaw(self.inputs)}


@dataclass(frozen=True)
class Decision:
    decision_id: str
    category: str
    severity: str
    explanation: str
    supporting_analytics: tuple[AnalyticsFact, ...]
    rule_id: str
    generated_at: datetime
    schema_version: str = "decision-v1"

    def __post_init__(self) -> None:
        if self.schema_version != "decision-v1":
            raise ValueError(f"unsupported decision schema: {self.schema_version}")
        if self.severity not in {"info", "warning", "critical"}:
            raise ValueError(f"unsupported severity: {self.severity}")
        if self.generated_at.tzinfo is None:
            raise ValueError("generated_at must be timezone-aware")
        object.__setattr__(self, "generated_at", self.generated_at.astimezone(timezone.utc))
        object.__setattr__(self, "supporting_analytics", tuple(self.supporting_analytics))

    def to_dict(self) -> dict[str, Any]:
        return {"schema_version": self.schema_version, "decision_id": self.decision_id,
                "category": self.category, "severity": self.severity,
                "explanation": self.explanation,
                "supporting_analytics": [f.to_dict() for f in self.supporting_analytics],
                "rule_id": self.rule_id,
                "generated_at": self.generated_at.isoformat().replace("+00:00", "Z")}


@dataclass(frozen=True)
class DecisionReport:
    decisions: tuple[Decision, ...]
    generated_at: datetime
    rule_versions: Mapping[str, str]
    schema_version: str = "decision-report-v1"

    def __post_init__(self) -> None:
        if self.schema_version != "decision-report-v1":
            raise ValueError(f"unsupported decision report schema: {self.schema_version}")
        if self.generated_at.tzinfo is None:
            raise ValueError("generated_at must be timezone-aware")
        object.__setattr__(self, "generated_at", self.generated_at.astimezone(timezone.utc))
        object.__setattr__(self, "decisions", tuple(self.decisions))
        object.__setattr__(self, "rule_versions", freeze(self.rule_versions))

    def to_dict(self) -> dict[str, Any]:
        return {"schema_version": self.schema_version,
                "generated_at": self.generated_at.isoformat().replace("+00:00", "Z"),
                "rule_versions": thaw(self.rule_versions),
                "decisions": [d.to_dict() for d in self.decisions]}

    def to_json(self, *, indent: int | None = None) -> str:
        import json
        return json.dumps(self.to_dict(), sort_keys=True, indent=indent,
                          separators=(",", ":") if indent is None else None)
