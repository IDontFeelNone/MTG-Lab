"""Immutable, provider-independent AI adapter contracts."""
from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from types import MappingProxyType
from typing import Any, Mapping

SCHEMA_VERSION = "ai-model-adapter-v1"
SUPPORTED_SCHEMA_VERSIONS = frozenset({SCHEMA_VERSION})
SUPPORTED_CAPABILITIES = frozenset({"structured-response"})


def freeze(value: Any) -> Any:
    if isinstance(value, Mapping):
        return MappingProxyType({str(key): freeze(item) for key, item in sorted(value.items())})
    if isinstance(value, (list, tuple)): return tuple(freeze(item) for item in value)
    if isinstance(value, (str, int, float, bool, type(None))): return value
    raise TypeError(f"unsupported AI contract value: {type(value).__name__}")


def thaw(value: Any) -> Any:
    if isinstance(value, Mapping): return {key: thaw(item) for key, item in value.items()}
    if isinstance(value, tuple): return [thaw(item) for item in value]
    return value


def _validate_timestamp(value: str, name: str) -> None:
    try: datetime.fromisoformat(value.replace("Z", "+00:00"))
    except (TypeError, ValueError) as error: raise ValueError(f"{name} must be an ISO-8601 timestamp") from error


def _validate_schema(value: str) -> None:
    if value not in SUPPORTED_SCHEMA_VERSIONS: raise ValueError(f"unsupported AI adapter schema: {value}")


class Serializable:
    def to_json(self, *, indent=None):
        return json.dumps(self.to_dict(), sort_keys=True, ensure_ascii=False, indent=indent,
                          separators=(",", ":") if indent is None else None)


@dataclass(frozen=True)
class AIProviderCapabilities(Serializable):
    capabilities: tuple[str, ...] = ("structured-response",)
    schema_version: str = SCHEMA_VERSION

    def __post_init__(self):
        _validate_schema(self.schema_version)
        object.__setattr__(self, "capabilities", tuple(sorted(set(self.capabilities))))

    def to_dict(self): return {"schema_version": self.schema_version, "capabilities": list(self.capabilities)}


@dataclass(frozen=True)
class AIProviderMetadata(Serializable):
    provider_identifier: str
    provider_version: str
    model_identifiers: tuple[str, ...]
    schema_version: str = SCHEMA_VERSION

    def __post_init__(self):
        _validate_schema(self.schema_version)
        object.__setattr__(self, "model_identifiers", tuple(sorted(set(self.model_identifiers))))

    def to_dict(self):
        return {"schema_version": self.schema_version, "provider_identifier": self.provider_identifier,
                "provider_version": self.provider_version, "model_identifiers": list(self.model_identifiers)}


@dataclass(frozen=True)
class AIExecutionMetadata(Serializable):
    execution_identifier: str
    started_at: str
    completed_at: str | None = None
    input_tokens: int | None = None
    output_tokens: int | None = None
    total_tokens: int | None = None
    schema_version: str = SCHEMA_VERSION

    def __post_init__(self):
        _validate_schema(self.schema_version)
        _validate_timestamp(self.started_at, "started_at")
        if self.completed_at is not None: _validate_timestamp(self.completed_at, "completed_at")
        for name in ("input_tokens", "output_tokens", "total_tokens"):
            value = getattr(self, name)
            if value is not None and (isinstance(value, bool) or not isinstance(value, int) or value < 0):
                raise ValueError(f"{name} must be a non-negative integer or null")

    def to_dict(self):
        return {"schema_version": self.schema_version, "execution_identifier": self.execution_identifier,
                "started_at": self.started_at, "completed_at": self.completed_at,
                "input_tokens": self.input_tokens, "output_tokens": self.output_tokens, "total_tokens": self.total_tokens}


@dataclass(frozen=True)
class AIModelRequest(Serializable):
    provider_identifier: str
    provider_version: str
    model_identifier: str
    reasoning_context_identifier: str
    execution_identifier: str
    created_at: str
    required_capabilities: tuple[str, ...] = ("structured-response",)
    schema_version: str = SCHEMA_VERSION

    def __post_init__(self):
        _validate_schema(self.schema_version)
        object.__setattr__(self, "required_capabilities", tuple(sorted(set(self.required_capabilities))))
        _validate_timestamp(self.created_at, "created_at")

    def to_dict(self):
        return {"schema_version": self.schema_version, "provider_identifier": self.provider_identifier,
                "provider_version": self.provider_version, "model_identifier": self.model_identifier,
                "reasoning_context_identifier": self.reasoning_context_identifier,
                "execution_identifier": self.execution_identifier, "created_at": self.created_at,
                "required_capabilities": list(self.required_capabilities)}


@dataclass(frozen=True)
class AIModelResponse(Serializable):
    provider_identifier: str
    provider_version: str
    model_identifier: str
    reasoning_context_identifier: str
    execution_metadata: AIExecutionMetadata
    structured_response: Mapping[str, Any]
    schema_version: str = SCHEMA_VERSION

    def __post_init__(self):
        _validate_schema(self.schema_version)
        object.__setattr__(self, "structured_response", freeze(self.structured_response))

    @property
    def execution_identifier(self): return self.execution_metadata.execution_identifier

    def to_dict(self):
        return {"schema_version": self.schema_version, "provider_identifier": self.provider_identifier,
                "provider_version": self.provider_version, "model_identifier": self.model_identifier,
                "reasoning_context_identifier": self.reasoning_context_identifier,
                "execution_metadata": self.execution_metadata.to_dict(),
                "structured_response": thaw(self.structured_response)}
