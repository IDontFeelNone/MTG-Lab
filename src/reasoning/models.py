"""Immutable, versioned reasoning-context contracts."""
from __future__ import annotations

import json
from dataclasses import dataclass
from types import MappingProxyType
from typing import Any, Mapping

from semantic import SCHEMA_VERSION as SEMANTIC_SCHEMA_VERSION, SemanticRequest

SCHEMA_VERSION = "canonical-reasoning-context-v1"
ORDERING = "entity-type,canonical-identity;relationship-type,source,target;evidence-id"


def freeze(value: Any) -> Any:
    if isinstance(value, Mapping):
        return MappingProxyType({str(k): freeze(v) for k, v in sorted(value.items())})
    if isinstance(value, (list, tuple)): return tuple(freeze(v) for v in value)
    if isinstance(value, (str, int, float, bool, type(None))): return value
    raise TypeError(f"unsupported reasoning-context value: {type(value).__name__}")


def thaw(value: Any) -> Any:
    if isinstance(value, Mapping): return {k: thaw(v) for k, v in value.items()}
    if isinstance(value, tuple): return [thaw(v) for v in value]
    return value


@dataclass(frozen=True)
class ReasoningContextRequest:
    semantic_request: SemanticRequest
    requested_entity_types: tuple[str, ...] = ()
    requested_datasets: tuple[str, ...] = ()
    requested_provenance_sources: tuple[str, ...] = ()
    validation_states: tuple[str, ...] = ()
    minimum_confidence: float | None = None
    maximum_confidence: float | None = None
    include_analytics: bool = False
    analytics_operation: str = "analytics_summary"
    maximum_entities: int = 100
    maximum_relationships: int = 100
    maximum_evidence_items: int = 100
    truncation_policy: str = "canonical-order-prefix"
    schema_version: str = SCHEMA_VERSION

    def __post_init__(self):
        if self.schema_version != SCHEMA_VERSION: raise ValueError(f"unsupported reasoning context schema: {self.schema_version}")
        if not isinstance(self.semantic_request, SemanticRequest): raise TypeError("semantic_request must be SemanticRequest")
        for name in ("requested_entity_types", "requested_datasets", "requested_provenance_sources", "validation_states"):
            object.__setattr__(self, name, tuple(sorted(set(getattr(self, name)))))

    def to_dict(self):
        return {"schema_version": self.schema_version, "semantic_request": self.semantic_request.to_dict(),
            "requested_entity_types": list(self.requested_entity_types), "requested_datasets": list(self.requested_datasets),
            "requested_provenance_sources": list(self.requested_provenance_sources), "validation_states": list(self.validation_states),
            "minimum_confidence": self.minimum_confidence, "maximum_confidence": self.maximum_confidence,
            "include_analytics": self.include_analytics, "analytics_operation": self.analytics_operation,
            "maximum_entities": self.maximum_entities, "maximum_relationships": self.maximum_relationships,
            "maximum_evidence_items": self.maximum_evidence_items, "truncation_policy": self.truncation_policy}


@dataclass(frozen=True)
class ReasoningContextResult:
    context_id: str
    canonical_snapshot_id: str
    normalized_request: Mapping[str, Any]
    entities: tuple[Any, ...]
    relationships: tuple[Any, ...]
    analytics_results: tuple[Any, ...]
    provenance_references: Mapping[str, Any]
    evidence_references: Mapping[str, Any]
    validation_information: Mapping[str, Any]
    confidence_information: Mapping[str, Any]
    omitted_item_counts: Mapping[str, int]
    truncation: Mapping[str, Any]
    warnings: tuple[str, ...]
    analytics_snapshot_id: str | None = None
    semantic_response_schema_version: str = SEMANTIC_SCHEMA_VERSION
    ordering: str = ORDERING
    schema_version: str = SCHEMA_VERSION

    def __post_init__(self):
        if self.schema_version != SCHEMA_VERSION: raise ValueError("unsupported reasoning context schema")
        if not self.context_id.startswith("sha256:") or not self.canonical_snapshot_id.startswith("sha256:"): raise ValueError("snapshot and context identifiers must be content-addressed")
        for name in ("normalized_request", "entities", "relationships", "analytics_results", "provenance_references", "evidence_references", "validation_information", "confidence_information", "omitted_item_counts", "truncation", "warnings"):
            object.__setattr__(self, name, freeze(getattr(self, name)))

    def to_dict(self):
        return {"schema_version": self.schema_version, "semantic_response_schema_version": self.semantic_response_schema_version,
            "context_id": self.context_id, "canonical_snapshot_id": self.canonical_snapshot_id,
            "analytics_snapshot_id": self.analytics_snapshot_id, "normalized_request": thaw(self.normalized_request),
            "entities": thaw(self.entities), "relationships": thaw(self.relationships), "analytics_results": thaw(self.analytics_results),
            "provenance_references": thaw(self.provenance_references), "evidence_references": thaw(self.evidence_references),
            "validation_information": thaw(self.validation_information), "confidence_information": thaw(self.confidence_information),
            "omitted_item_counts": thaw(self.omitted_item_counts), "truncation": thaw(self.truncation),
            "warnings": thaw(self.warnings), "ordering": self.ordering}

    def to_json(self, *, indent=None):
        return json.dumps(self.to_dict(), sort_keys=True, ensure_ascii=False, indent=indent,
                          separators=(",", ":") if indent is None else None)
