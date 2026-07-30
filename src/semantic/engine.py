"""Deterministic translation from semantic operations to canonical engines."""
from __future__ import annotations

import hashlib
import json
from typing import Any, Mapping

from analytics import CanonicalAnalyticsEngine
from query import CanonicalQueryEngine, QueryError, QueryResult

from .models import SemanticRequest, SemanticResponse


class SemanticQueryError(ValueError):
    """The structured request is invalid or names an unknown required resource."""


class CanonicalSemanticQueryEngine:
    """Non-reasoning facade that delegates exclusively to canonical read engines."""

    OPERATIONS = frozenset({"find_identifier", "find_name", "list_type", "list_dataset",
        "list_provenance", "list_validation", "list_confidence", "analytics_summary",
        "dataset_statistics", "provenance_statistics", "validation_statistics"})

    def __init__(self, query: CanonicalQueryEngine,
                 analytics: CanonicalAnalyticsEngine | None = None) -> None:
        self._query = query
        self._analytics = analytics or CanonicalAnalyticsEngine(query)

    def execute(self, request: SemanticRequest) -> SemanticResponse:
        if request.operation not in self.OPERATIONS:
            raise SemanticQueryError(f"unsupported semantic operation: {request.operation}")
        snapshot = self._query.snapshot()
        parameters = request.parameters
        analytics_name = {"analytics_summary": "summary", "dataset_statistics": "dataset",
                          "provenance_statistics": "provenance",
                          "validation_statistics": "validation"}.get(request.operation)
        if analytics_name:
            self._reject_extra(parameters, set())
            report = getattr(self._analytics, analytics_name)()
            payload = report.to_dict()
            identity = "sha256:" + hashlib.sha256(json.dumps(payload, sort_keys=True,
                separators=(",", ":"), ensure_ascii=False).encode()).hexdigest()
            return SemanticResponse(request.operation, snapshot.snapshot_id, payload,
                                    report.provenance, identity)

        entities = self._entities(request.operation, parameters, snapshot.entities)
        values = [item.as_dict() for item in sorted(entities,
                  key=lambda item: (item.entity_type, item.canonical_identity))]
        provenance = {item.canonical_identity: item.provenance_summary for item in entities}
        return SemanticResponse(request.operation, snapshot.snapshot_id, values, provenance)

    def _entities(self, operation: str, values: Mapping[str, Any],
                  all_entities: tuple[QueryResult, ...]) -> tuple[QueryResult, ...]:
        if operation == "find_identifier":
            self._require(values, "identifier"); self._reject_extra(values, {"identifier", "entity_type"})
            try: return (self._query.entity(str(values["identifier"]), entity_type=values.get("entity_type")),)
            except QueryError as error: raise SemanticQueryError(str(error)) from error
        if operation == "find_name":
            self._require(values, "name"); self._reject_extra(values, {"name"})
            found = self._query.search(str(values["name"]), mode="normalized")
            if not found: raise SemanticQueryError(f"unknown canonical name: {values['name']}")
            return found
        if operation == "list_type":
            self._require(values, "entity_type"); self._reject_extra(values, {"entity_type"})
            return self._query.entities(entity_type=str(values["entity_type"]))
        if operation == "list_dataset":
            self._require(values, "dataset"); self._reject_extra(values, {"dataset"})
            found = tuple(self._query.related(str(values["dataset"]), "dataset_entities"))
            if not found: raise SemanticQueryError(f"unknown dataset: {values['dataset']}")
            return tuple(item for item in found if isinstance(item, QueryResult))
        if operation == "list_provenance":
            self._require(values, "source_id"); self._reject_extra(values, {"source_id"})
            source = str(values["source_id"])
            return tuple(item for item in all_entities if source in item.provenance_summary.get("source_ids", ()))
        if operation == "list_validation":
            self._require(values, "state"); self._reject_extra(values, {"state"})
            try: found = self._query.validation(str(values["state"]))
            except QueryError as error: raise SemanticQueryError(str(error)) from error
            return tuple(item for item in found if isinstance(item, QueryResult))
        self._reject_extra(values, {"minimum", "maximum"})
        minimum, maximum = values.get("minimum", 0.0), values.get("maximum", 1.0)
        if isinstance(minimum, bool) or isinstance(maximum, bool) or not isinstance(minimum, (int, float)) or not isinstance(maximum, (int, float)):
            raise SemanticQueryError("confidence bounds must be numbers")
        if not 0 <= minimum <= maximum <= 1:
            raise SemanticQueryError("confidence bounds must satisfy 0 <= minimum <= maximum <= 1")
        return tuple(item for item in all_entities if item.confidence is not None and minimum <= item.confidence <= maximum)

    @staticmethod
    def _require(values: Mapping[str, Any], key: str) -> None:
        if key not in values or values[key] in (None, ""):
            raise SemanticQueryError(f"{key} is required")

    @staticmethod
    def _reject_extra(values: Mapping[str, Any], allowed: set[str]) -> None:
        extra = sorted(set(values) - allowed)
        if extra: raise SemanticQueryError("unexpected parameters: " + ", ".join(extra))
