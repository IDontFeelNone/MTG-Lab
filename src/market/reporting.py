"""Deterministic, read-only reports over retained market observations."""
from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any

from .intelligence import MarketObservation, MarketObservationRepository
from .models import MarketValidationError, normalize_timestamp, validate_identifier

REPORT_VERSION = "market-history-report-v1"
DEFAULT_LIMIT = 100
MAX_LIMIT = 500
ORDERING = ["observed_at", "recorded_at", "provider", "observation_id"]


def parse_timestamp(value: str, name: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except (TypeError, ValueError) as error:
        raise MarketValidationError(f"{name} must be an ISO 8601 timestamp") from error
    if parsed.tzinfo is None:
        raise MarketValidationError(f"{name} must include a timezone")
    return normalize_timestamp(parsed)


def stamp(value: datetime | None) -> str | None:
    return None if value is None else normalize_timestamp(value).isoformat().replace("+00:00", "Z")


class MarketHistoryReports:
    """Query facade which has no persistence methods and opens retained data read-only."""

    def __init__(self, data_root: Path):
        self.data_root = Path(data_root)
        self.repository = MarketObservationRepository(self.data_root / "market/observations")
        self.canonical = json.loads((self.data_root / "canonical/state.json").read_text(encoding="utf-8"))
        self.printings = self.canonical.get("printing", {})
        self.all_observations = self.repository.observations()
        self.providers = {x.provider for x in self.all_observations}
        self.currencies = {x.currency for x in self.all_observations}
        self.price_types = {x.price_type for x in self.all_observations}
        self.finishes = set(self.canonical.get("finish", {}))
        self.languages = {str(x.provenance.get("language")) for x in self.all_observations
                          if x.provenance.get("language")}
        self.acquisitions = {str(x.provenance.get("acquisition_run_id")) for x in self.all_observations
                             if x.provenance.get("acquisition_run_id")}
        identities = {x.provenance.get("canonical_snapshot_identity") for x in self.all_observations
                      if x.provenance.get("canonical_snapshot_identity")}
        self.snapshot_identity = sorted(identities)[0] if len(identities) == 1 else None

    def _filters(self, values: dict[str, Any]) -> dict[str, Any]:
        normalized = {key: value for key, value in values.items() if value is not None}
        if "printing_id" in normalized:
            normalized["printing_id"] = validate_identifier(normalized["printing_id"], "printing_id")
            if normalized["printing_id"] not in self.printings:
                raise MarketValidationError(f"unknown canonical printing ID: {normalized['printing_id']}")
        rules = (("provider", self.providers), ("acquisition_run_id", self.acquisitions),
                 ("finish", self.finishes), ("language", self.languages),
                 ("currency", self.currencies), ("price_type", self.price_types))
        if "currency" in normalized: normalized["currency"] = str(normalized["currency"]).upper()
        if "language" in normalized: normalized["language"] = str(normalized["language"]).lower()
        for name, supported in rules:
            if name in normalized and normalized[name] not in supported:
                raise MarketValidationError(f"unsupported {name}: {normalized[name]}")
        for name in ("observed_from", "observed_to", "as_of"):
            if name in normalized: normalized[name] = parse_timestamp(normalized[name], name)
        if normalized.get("observed_from") and normalized.get("observed_to") and normalized["observed_from"] > normalized["observed_to"]:
            raise MarketValidationError("observed_from cannot follow observed_to")
        return normalized

    def _select(self, filters: dict[str, Any]) -> tuple[dict[str, Any], tuple[MarketObservation, ...]]:
        values = self._filters(filters)
        query = {"entity_type": "printing", "entity_id": values.get("printing_id"),
                 "provider": values.get("provider"), "currency": values.get("currency"),
                 "price_type": values.get("price_type"), "finish": values.get("finish"),
                 "acquisition_run_id": values.get("acquisition_run_id"), "language": values.get("language"),
                 "observed_at_or_after": values.get("observed_from"),
                 "observed_at_or_before": min(x for x in (values.get("observed_to"), values.get("as_of")) if x is not None)
                    if values.get("observed_to") or values.get("as_of") else None}
        selected = self.repository.observations(**query)
        return values, selected

    @staticmethod
    def _observation(value: MarketObservation) -> dict[str, Any]:
        return value.to_dict()

    def _envelope(self, command: str, filters: dict[str, Any], data: Any, count: int,
                  *, truncated: bool = False, ordering: list[str] | None = None) -> dict[str, Any]:
        rendered = {k: stamp(v) if isinstance(v, datetime) else v for k, v in sorted(filters.items())}
        return {"schema_version": REPORT_VERSION, "report_type": command,
                "normalized_filters": rendered, "canonical_snapshot_identity": self.snapshot_identity,
                "result_count": count, "truncated": truncated, "ordering": ordering or [],
                "empty_result": count == 0, "data": data}

    def observations(self, operation: str, filters: dict[str, Any], limit: int = DEFAULT_LIMIT) -> dict[str, Any]:
        normalized, selected = self._select(filters)
        if operation == "count": return self._envelope("observations.count", normalized, {"count": len(selected)}, len(selected))
        if operation in {"first", "latest"}:
            value = (selected[0] if operation == "first" else selected[-1]) if selected else None
            return self._envelope(f"observations.{operation}", normalized,
                                  None if value is None else self._observation(value), int(value is not None), ordering=ORDERING)
        if isinstance(limit, bool) or not 1 <= limit <= MAX_LIMIT:
            raise MarketValidationError(f"limit must be between 1 and {MAX_LIMIT}")
        returned = selected[:limit]
        return self._envelope("observations.list", normalized, [self._observation(x) for x in returned],
                              len(returned), truncated=len(selected) > limit, ordering=ORDERING)

    def printing_history(self, printing_id: str, filters: dict[str, Any]) -> dict[str, Any]:
        filters = {**filters, "printing_id": printing_id}
        normalized, selected = self._select(filters)
        return self._envelope("printing-history", normalized, [self._observation(x) for x in selected],
                              len(selected), ordering=ORDERING)

    def snapshot(self, filters: dict[str, Any]) -> dict[str, Any]:
        normalized, selected = self._select(filters)
        if "as_of" not in normalized: raise MarketValidationError("snapshot requires as_of")
        dimensions: dict[tuple[Any, ...], MarketObservation] = {}
        for item in selected:
            key = (item.entity_id, item.provider, item.finish, item.provenance.get("language"),
                   item.currency, item.price_type)
            dimensions[key] = item
        result = sorted(dimensions.values(), key=lambda x: (x.entity_id, x.provider, x.finish or "",
            str(x.provenance.get("language", "")), x.currency, x.price_type, x.observation_id))
        ordering = ["printing_id", "provider", "finish", "language", "currency", "price_type", "observation_id"]
        return self._envelope("snapshot", normalized, [self._observation(x) for x in result], len(result), ordering=ordering)

    def coverage(self, product: str) -> dict[str, Any]:
        if product != "mystery-booster-2": raise MarketValidationError(f"unsupported product: {product}")
        canonical_ids = {key for key, item in self.printings.items()
                         if str(item.get("values", {}).get("set_id", "")).lower() == "mb2"}
        observations = tuple(x for x in self.all_observations if x.entity_type == "printing" and x.entity_id in canonical_ids)
        covered = {x.entity_id for x in observations}
        report = {"product": product, "covered_printing_count": len(covered),
                  "uncovered_printing_count": len(canonical_ids - covered),
                  "total_canonical_printing_count": len(canonical_ids), "observation_count": len(observations),
                  "provider_count": len({x.provider for x in observations}),
                  "acquisition_count": len({x.provenance.get('acquisition_run_id') for x in observations}),
                  "earliest_source_timestamp": stamp(min((x.observed_at for x in observations), default=None)),
                  "latest_source_timestamp": stamp(max((x.observed_at for x in observations), default=None)),
                  "latest_retrieval_timestamp": stamp(max((x.recorded_at for x in observations), default=None))}
        return self._envelope("coverage", {"product": product}, report, len(covered))

    def acquisition_summary(self, run_id: str) -> dict[str, Any]:
        run_id = validate_identifier(run_id, "acquisition_run_id")
        if run_id not in self.acquisitions: raise MarketValidationError(f"unknown acquisition_run_id: {run_id}")
        values = tuple(x for x in self.all_observations if x.provenance.get("acquisition_run_id") == run_id)
        manifest = json.loads((self.data_root / "market/acquisitions" / run_id / "manifest.json").read_text())
        def counts(items): return dict(sorted(Counter(items).items()))
        report = {"acquisition_run_id": run_id, "provider": manifest["provider"],
                  "acquisition_timestamp": manifest["retrieved_at"], "source_timestamp": manifest["source_observed_at"],
                  "observation_count": len(values), "distinct_printing_count": len({x.entity_id for x in values}),
                  "finish_counts": counts(x.finish for x in values),
                  "language_counts": counts(str(x.provenance.get("language")) for x in values),
                  "currency_counts": counts(x.currency for x in values), "price_type_counts": counts(x.price_type for x in values),
                  "known_price_count": sum(x.price is not None for x in values),
                  "explicit_missing_price_count": sum(x.price is None for x in values),
                  "canonical_snapshot_identity": manifest["canonical_snapshot_identity"],
                  "source_sha256": manifest.get("provider_source_sha256"),
                  "retained_source_sha256": manifest.get("files", {}).get("source-mb2.json", {}).get("sha256"),
                  "normalized_sha256": manifest.get("normalized_sha256")}
        envelope = self._envelope("acquisition-summary", {"acquisition_run_id": run_id}, report, len(values))
        envelope["canonical_snapshot_identity"] = manifest["canonical_snapshot_identity"]
        return envelope
