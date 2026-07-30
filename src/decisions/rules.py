"""Versioned, data-driven decision rules."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from analytics import AnalyticsReport


OPERATORS = {"gt", "gte", "lt", "lte", "eq", "ne"}


@dataclass(frozen=True)
class DecisionRule:
    rule_id: str
    version: str
    category: str
    report_type: str
    fact_path: str
    operator: str
    threshold: Any
    severity: str
    explanation: str

    def __post_init__(self) -> None:
        if not all((self.rule_id.strip(), self.version.strip(), self.category.strip(),
                    self.report_type.strip(), self.fact_path.strip(), self.explanation.strip())):
            raise ValueError("rule text fields must not be empty")
        if self.operator not in OPERATORS:
            raise ValueError(f"unsupported rule operator: {self.operator}")
        if self.severity not in {"info", "warning", "critical"}:
            raise ValueError(f"unsupported severity: {self.severity}")

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> "DecisionRule":
        required = ("rule_id", "version", "category", "report_type", "fact_path",
                    "operator", "threshold", "severity", "explanation")
        missing = [key for key in required if key not in value]
        if missing:
            raise ValueError(f"rule configuration missing: {', '.join(missing)}")
        return cls(**{key: value[key] for key in required})

    def fact(self, report: AnalyticsReport) -> Any:
        value: Any = report.data
        for part in self.fact_path.split("."):
            if not isinstance(value, Mapping) or part not in value:
                raise ValueError(f"analytics fact not found: {self.report_type}.{self.fact_path}")
            value = value[part]
        return value

    def matches(self, value: Any) -> bool:
        return {"gt": lambda: value > self.threshold, "gte": lambda: value >= self.threshold,
                "lt": lambda: value < self.threshold, "lte": lambda: value <= self.threshold,
                "eq": lambda: value == self.threshold, "ne": lambda: value != self.threshold}[self.operator]()


class DuplicateThresholdRule(DecisionRule):
    pass


class InventoryLocationRule(DecisionRule):
    pass


class MissingCoverageRule(DecisionRule):
    pass


class ObservationConsistencyRule(DecisionRule):
    pass


class CollectionGrowthRule(DecisionRule):
    pass


DEFAULT_RULES = (
    DuplicateThresholdRule("duplicates.extra-copies", "1.0.0", "duplicate_opportunity", "duplicate_report", "duplicate_copies", "gt", 0, "warning", "Collection has {value} duplicate copies (threshold {threshold})."),
    InventoryLocationRule("inventory.unassigned", "1.0.0", "inventory_alert", "inventory_report", "unassigned_cards", "gt", 0, "warning", "Inventory has {value} unassigned cards (threshold {threshold})."),
    MissingCoverageRule("collection.missing-coverage", "1.0.0", "missing_collection_coverage", "collection_summary", "unique_printings", "eq", 0, "critical", "Collection coverage contains {value} unique printings."),
    ObservationConsistencyRule("observations.empty", "1.0.0", "observation_anomaly", "observation_report", "observation_count", "eq", 0, "warning", "Observation analytics contains {value} observations."),
    CollectionGrowthRule("collection.health.empty", "1.0.0", "collection_health", "collection_summary", "total_cards", "eq", 0, "info", "Collection health reports {value} total cards."),
    DecisionRule("products.no-openings", "1.0.0", "product_opening_summary", "product_report", "products", "eq", (), "info", "Product opening summary contains no products."),
    DecisionRule("acquisition.no-history", "1.0.0", "acquisition_opportunity", "acquisition_report", "acquisition_count", "eq", 0, "info", "Acquisition history contains {value} acquisitions."),
)
