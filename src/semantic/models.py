"""Immutable contracts for deterministic semantic queries."""
from __future__ import annotations

import json
from dataclasses import dataclass
from types import MappingProxyType
from typing import Any, Mapping


SCHEMA_VERSION = "canonical-semantic-query-v1"


def freeze(value: Any) -> Any:
    if isinstance(value, Mapping):
        return MappingProxyType({str(key): freeze(item) for key, item in sorted(value.items())})
    if isinstance(value, (list, tuple)):
        return tuple(freeze(item) for item in value)
    if isinstance(value, (str, int, float, bool, type(None))):
        return value
    raise TypeError(f"unsupported semantic value: {type(value).__name__}")


def thaw(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {key: thaw(item) for key, item in value.items()}
    if isinstance(value, tuple):
        return [thaw(item) for item in value]
    return value


@dataclass(frozen=True)
class SemanticRequest:
    """A versioned operation and its structured, non-linguistic arguments."""

    operation: str
    parameters: Mapping[str, Any]
    schema_version: str = SCHEMA_VERSION

    def __post_init__(self) -> None:
        if self.schema_version != SCHEMA_VERSION:
            raise ValueError(f"unsupported semantic schema: {self.schema_version}")
        if not self.operation.strip():
            raise ValueError("semantic operation is required")
        object.__setattr__(self, "parameters", freeze(self.parameters))

    def to_dict(self) -> dict[str, Any]:
        return {"schema_version": self.schema_version, "operation": self.operation,
                "parameters": thaw(self.parameters)}


@dataclass(frozen=True)
class SemanticResponse:
    """Immutable result envelope tied to exact canonical and analytics inputs."""

    operation: str
    canonical_snapshot_id: str
    result: Any
    provenance_references: Mapping[str, Any]
    analytics_snapshot_id: str | None = None
    schema_version: str = SCHEMA_VERSION

    def __post_init__(self) -> None:
        if self.schema_version != SCHEMA_VERSION:
            raise ValueError(f"unsupported semantic schema: {self.schema_version}")
        if not self.canonical_snapshot_id.startswith("sha256:"):
            raise ValueError("canonical_snapshot_id must be content-addressed")
        object.__setattr__(self, "result", freeze(self.result))
        object.__setattr__(self, "provenance_references", freeze(self.provenance_references))

    def to_dict(self) -> dict[str, Any]:
        return {"schema_version": self.schema_version, "operation": self.operation,
                "canonical_snapshot_id": self.canonical_snapshot_id,
                "analytics_snapshot_id": self.analytics_snapshot_id,
                "provenance_references": thaw(self.provenance_references),
                "result": thaw(self.result)}

    def to_json(self, *, indent: int | None = None) -> str:
        return json.dumps(self.to_dict(), indent=indent, sort_keys=True,
                          separators=(",", ":") if indent is None else None)
