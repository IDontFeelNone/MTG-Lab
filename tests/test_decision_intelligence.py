"""Synthetic-only proof of the shared, game-neutral decision substrate."""
import json
from pathlib import Path
import unittest

from jsonschema import Draft202012Validator

from decision_intelligence import (
    AcquisitionDecisionOrchestrator,
    AnalysisMetric,
    DecisionAlternative,
    DecisionPolicy,
    DecisionRequest,
    DomainAnalysisEnvelope,
    EvidenceReference,
    MetricCriterion,
    recommendation_reasoning_context,
)


EVIDENCE = EvidenceReference(
    "synthetic-evidence", "synthetic-fixture", "sha256:" + "a" * 64
)


def request(order=("option-b", "option-a")):
    return DecisionRequest(
        "Select a synthetic alternative",
        tuple(
            DecisionAlternative(item, "SYNTHETIC_ACTION_" + item[-1].upper())
            for item in order
        ),
        {"synthetic_constraint": True},
        {"synthetic_preference": "explicit"},
        {"semantics": "synthetic dimensionless test signal"},
        (EVIDENCE,),
        "synthetic-policy",
        "1.0.0",
        {"state": "explicitly supplied"},
        ("synthetic-input-snapshot",),
    )


def analysis(alternative_id, value, state="known", **kwargs):
    return DomainAnalysisEnvelope(
        "synthetic-domain",
        "1.0.0",
        alternative_id,
        (
            AnalysisMetric(
                "synthetic.signal",
                state,
                value if state == "known" else None,
                evidence_ids=("synthetic-evidence",),
                uncertainty=kwargs.pop("metric_uncertainty", {}),
            ),
        ),
        (EVIDENCE,),
        input_snapshot_ids=("synthetic-analysis-snapshot",),
        **kwargs,
    )


def policy():
    return DecisionPolicy(
        "synthetic-policy",
        "1.0.0",
        (MetricCriterion("synthetic.signal", "maximize"),),
    )


def evaluate(analyses):
    return AcquisitionDecisionOrchestrator().evaluate(request(), analyses, policy())


class DecisionIntelligenceTests(unittest.TestCase):
    def test_serialization_selection_provenance_context_and_replay(self):
        first_request = request()
        second_request = request(("option-a", "option-b"))
        self.assertEqual(first_request.to_json(), second_request.to_json())
        self.assertEqual(first_request.request_id, second_request.request_id)
        inputs = (
            analysis(
                "option-b",
                2,
                assumptions=("synthetic assumption",),
                limitations=("synthetic limitation",),
                uncertainty={"kind": "synthetic range"},
                sensitivity_inputs={"synthetic.signal": "caller supplied"},
            ),
            analysis("option-a", 1),
        )
        result = evaluate(inputs)
        replay = evaluate(reversed(inputs))
        self.assertEqual(result.outcome, "selected")
        self.assertEqual(result.selected_alternative_id, "option-b")
        self.assertEqual(result.to_json(), replay.to_json())
        self.assertEqual(result.recommendation_id, replay.recommendation_id)
        self.assertEqual(result.evidence_references, (EVIDENCE,))
        self.assertIn("synthetic assumption", result.assumptions)
        self.assertTrue(result.decision_change_conditions)
        self.assertTrue(result.uncertainties)
        context = recommendation_reasoning_context(result)
        self.assertEqual(context["recommendation"], result.to_dict())
        self.assertIn("without changing", context["instruction"])

    def test_missing_unsupported_incomplete_and_tie_abstain_closed(self):
        missing = evaluate(
            (
                analysis("option-a", 1),
                DomainAnalysisEnvelope(
                    "synthetic-domain", "1", "option-b", (), (EVIDENCE,)
                ),
            )
        )
        unsupported = evaluate(
            (analysis("option-a", 1), analysis("option-b", None, "unsupported"))
        )
        tie = evaluate((analysis("option-a", 1), analysis("option-b", 1)))
        for result in (missing, unsupported, tie):
            self.assertEqual(result.outcome, "abstain")
            self.assertIsNone(result.selected_alternative_id)
        self.assertIn("missing_required_metric", missing.abstention_reasons[0])
        self.assertTrue(
            any("unsupported" in reason for reason in unsupported.abstention_reasons)
        )

    def test_contradiction_abstains_and_uncertainty_is_preserved(self):
        result = evaluate(
            (
                analysis("option-a", 1),
                analysis("option-a", 2),
                analysis(
                    "option-b", 3, metric_uncertainty={"range": [2, 4]}
                ),
            )
        )
        self.assertEqual(result.outcome, "abstain")
        self.assertTrue(
            any(
                reason.startswith("contradictory_evidence")
                for reason in result.abstention_reasons
            )
        )
        self.assertEqual(
            result.to_dict()["uncertainties"][0]["metrics"][0]["uncertainty"],
            {"range": [2, 4]},
        )

    def test_counterargument_preserved_for_later_criterion(self):
        selected_policy = DecisionPolicy(
            "synthetic-policy",
            "1.0.0",
            (
                MetricCriterion("synthetic.primary", "maximize"),
                MetricCriterion("synthetic.secondary", "maximize"),
            ),
        )

        def envelope(alternative_id, primary, secondary):
            return DomainAnalysisEnvelope(
                "synthetic-domain",
                "1",
                alternative_id,
                (
                    AnalysisMetric("synthetic.primary", "known", primary),
                    AnalysisMetric("synthetic.secondary", "known", secondary),
                ),
            )

        result = AcquisitionDecisionOrchestrator().evaluate(
            request(),
            (envelope("option-a", 2, 1), envelope("option-b", 1, 9)),
            selected_policy,
        )
        self.assertEqual(result.selected_alternative_id, "option-a")
        self.assertEqual(result.counterarguments[0].alternative_id, "option-b")

    def test_schema_validation_and_fail_closed_models(self):
        root = Path("src/schemas/v1")
        pairs = (
            (request().to_dict(), "decision-request-v1"),
            (policy().to_dict(), "decision-policy-v1"),
            (analysis("option-a", 1).to_dict(), "decision-analysis-v1"),
            (
                evaluate(
                    (analysis("option-a", 1), analysis("option-b", 2))
                ).to_dict(),
                "recommendation-v1",
            ),
        )
        for instance, name in pairs:
            schema = json.loads((root / f"{name}.schema.json").read_text())
            Draft202012Validator(schema).validate(instance)
        with self.assertRaises(ValueError):
            AnalysisMetric("x", "unknown", 0)
        with self.assertRaises(ValueError):
            DecisionAlternative("x", "", attributes={})

    def test_domain_isolation_and_no_mutation(self):
        before = {path: path.read_bytes() for path in Path("data").rglob("*") if path.is_file()}
        result = evaluate((analysis("option-a", 1), analysis("option-b", 2)))
        after = {path: path.read_bytes() for path in Path("data").rglob("*") if path.is_file()}
        self.assertEqual(result.outcome, "selected")
        self.assertEqual(before, after)
        shared = "\n".join(
            path.read_text()
            for path in Path("src/decision_intelligence").glob("*.py")
        ).lower()
        forbidden = (
            "booster",
            "secret lair",
            "commander",
            "tournament",
            "sealed",
            "singles",
            "deck",
            "card",
            "product",
            "magic",
        )
        self.assertFalse(any(word in shared for word in forbidden))


if __name__ == "__main__":
    unittest.main()
