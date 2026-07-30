import json
import tempfile
import unittest
from contextlib import redirect_stdout
from datetime import datetime, timezone
from io import StringIO
from pathlib import Path
from types import MappingProxyType

from analytics import AnalyticsReport
from decisions import DecisionRule, DecisionService
from mtglab.decisions.__main__ import main


NOW = datetime(2026, 7, 30, 12, tzinfo=timezone.utc)


def report(kind, data):
    return AnalyticsReport(kind, NOW, {"snapshot_sha256": "abc"}, data)


class DecisionEngineTests(unittest.TestCase):
    def test_rule_evaluation_severity_explanation_and_trace(self):
        rule = DecisionRule("duplicates.test", "2.1.0", "duplicate_opportunity",
                            "duplicate_report", "duplicate_copies", "gte", 2,
                            "critical", "Found {value}; configured threshold is {threshold}.")
        decision = DecisionService((rule,), lambda: NOW).evaluate([report("duplicate_report", {"duplicate_copies": 3})])[0]
        self.assertEqual(decision.severity, "critical")
        self.assertEqual(decision.explanation, "Found 3; configured threshold is 2.")
        self.assertEqual(decision.supporting_analytics[0].path, "duplicate_copies")
        self.assertEqual(decision.supporting_analytics[0].inputs["snapshot_sha256"], "abc")

    def test_decisions_are_immutable_ordered_and_reproducible(self):
        rules = (DecisionRule("z", "1", "inventory_alert", "inventory_report", "total", "gt", 0, "warning", "{value}"),
                 DecisionRule("a", "1", "collection_health", "collection_summary", "total", "gt", 0, "info", "{value}"))
        service = DecisionService(rules, lambda: NOW)
        reports = [report("inventory_report", {"total": 1}), report("collection_summary", {"total": 1})]
        first = service.generate_decision_report(reports)
        second = service.generate_decision_report(reversed(reports))
        self.assertEqual(first.to_json(), second.to_json())
        self.assertEqual([d.rule_id for d in first.decisions], ["a", "z"])
        self.assertIsInstance(first.rule_versions, MappingProxyType)

    def test_non_matching_rule_and_category_api(self):
        rules = (DecisionRule("dup", "1", "duplicate_opportunity", "duplicate_report", "count", "gt", 2, "warning", "{value}"),
                 DecisionRule("inv", "1", "inventory_alert", "inventory_report", "count", "gt", 0, "warning", "{value}"))
        service = DecisionService(rules, lambda: NOW)
        reports = [report("duplicate_report", {"count": 2}), report("inventory_report", {"count": 1})]
        self.assertEqual(service.evaluate_duplicates(reports), ())
        self.assertEqual(service.evaluate_inventory(reports)[0].rule_id, "inv")

    def test_configuration_and_schema_validation(self):
        with self.assertRaisesRegex(ValueError, "missing"):
            DecisionRule.from_dict({"rule_id": "incomplete"})
        with self.assertRaisesRegex(ValueError, "operator"):
            DecisionRule("id", "1", "category", "report", "fact", "contains", 1, "info", "text")
        with self.assertRaisesRegex(ValueError, "fact not found"):
            DecisionService((DecisionRule("id", "1", "category", "report", "missing", "eq", 1, "info", "text"),), lambda: NOW).evaluate([report("report", {})])

    def test_report_serialization_preserves_rule_version(self):
        rule = DecisionRule("health", "3.0.0", "collection_health", "summary", "count", "eq", 0, "info", "Empty")
        payload = DecisionService((rule,), lambda: NOW).generate_decision_report([report("summary", {"count": 0})]).to_dict()
        self.assertEqual(payload["schema_version"], "decision-report-v1")
        self.assertEqual(payload["rule_versions"], {"health": "3.0.0"})
        self.assertEqual(payload["decisions"][0]["schema_version"], "decision-v1")

    def test_cli_evaluate_report_and_rules(self):
        with tempfile.TemporaryDirectory() as directory:
            common = ["--collection-file", str(Path(directory) / "missing.json"),
                      "--observations-dir", str(Path(directory) / "observations")]
            for command in (("evaluate",), ("report", "--format", "json"), ("rules",)):
                output = StringIO()
                with redirect_stdout(output):
                    self.assertEqual(main(common + list(command)), 0)
                self.assertIsNotNone(json.loads(output.getvalue()))


if __name__ == "__main__":
    unittest.main()
