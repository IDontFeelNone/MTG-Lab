"""Deterministic orchestration for decision rule evaluation."""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from typing import Callable, Iterable

from analytics import AnalyticsReport

from .models import AnalyticsFact, Decision, DecisionReport, thaw
from .rules import DEFAULT_RULES, DecisionRule


class DecisionService:
    def __init__(self, rules: Iterable[DecisionRule] = DEFAULT_RULES,
                 clock: Callable[[], datetime] | None = None):
        self.rules = tuple(sorted(rules, key=lambda r: (r.rule_id, r.version)))
        if len({r.rule_id for r in self.rules}) != len(self.rules):
            raise ValueError("rule identifiers must be unique")
        self._clock = clock or (lambda: datetime.now(timezone.utc))

    def evaluate(self, reports: Iterable[AnalyticsReport], *, categories: set[str] | None = None) -> tuple[Decision, ...]:
        by_type = {}
        for report in reports:
            if not isinstance(report, AnalyticsReport) or report.schema_version != "analytics-report-v1":
                raise ValueError("Decision Engine requires analytics-report-v1 inputs")
            if report.report_type in by_type:
                raise ValueError(f"duplicate analytics report type: {report.report_type}")
            by_type[report.report_type] = report
        generated_at = self._clock()
        decisions = []
        for rule in self.rules:
            if categories is not None and rule.category not in categories:
                continue
            report = by_type.get(rule.report_type)
            if report is None:
                continue
            value = rule.fact(report)
            if rule.matches(value):
                fact = AnalyticsFact(report.report_type, rule.fact_path, value, report.inputs)
                identity = {"rule_id": rule.rule_id, "rule_version": rule.version,
                            "fact": fact.to_dict()}
                decision_id = "decision-" + hashlib.sha256(json.dumps(identity, sort_keys=True, separators=(",", ":")).encode()).hexdigest()[:20]
                explanation = rule.explanation.format(value=thaw(value), threshold=rule.threshold)
                decisions.append(Decision(decision_id, rule.category, rule.severity,
                                          explanation, (fact,), rule.rule_id, generated_at))
        return tuple(sorted(decisions, key=lambda d: (d.category, d.severity, d.rule_id, d.decision_id)))

    def evaluate_collection(self, reports: Iterable[AnalyticsReport]) -> tuple[Decision, ...]:
        return self.evaluate(reports, categories={"collection_health", "missing_collection_coverage", "acquisition_opportunity"})

    def evaluate_inventory(self, reports: Iterable[AnalyticsReport]) -> tuple[Decision, ...]:
        return self.evaluate(reports, categories={"inventory_alert"})

    def evaluate_observations(self, reports: Iterable[AnalyticsReport]) -> tuple[Decision, ...]:
        return self.evaluate(reports, categories={"observation_anomaly", "product_opening_summary"})

    def evaluate_duplicates(self, reports: Iterable[AnalyticsReport]) -> tuple[Decision, ...]:
        return self.evaluate(reports, categories={"duplicate_opportunity"})

    def generate_decision_report(self, reports: Iterable[AnalyticsReport]) -> DecisionReport:
        decisions = self.evaluate(reports)
        generated_at = decisions[0].generated_at if decisions else self._clock()
        return DecisionReport(decisions, generated_at, {r.rule_id: r.version for r in self.rules})
