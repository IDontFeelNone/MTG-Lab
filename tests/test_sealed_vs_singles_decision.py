"""Synthetic end-to-end Product-to-Decision acquisition vertical tests."""
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path
import unittest

from decision_intelligence import EvidenceReference, recommendation_reasoning_context
from market.intelligence import MarketObservation
from product_intelligence import (
    ACQUIRE_GUARANTEED_CONTENTS_NOW,
    BUY_SEALED_NOW,
    BUY_SINGLES_NOW,
    MINIMIZE_ACQUISITION_COST,
    WAIT,
    ComponentValuationInput,
    FixedContentProductAnalysis,
    FixedContentProductManifest,
    GuaranteedComponent,
    ProductAcquisitionOffer,
    analyze_fixed_content,
    build_sealed_vs_singles_request,
    current_acquisition_cost_policy,
    evaluate_sealed_vs_singles,
)

NOW = datetime(2026, 8, 15, tzinfo=timezone.utc)
MANIFEST_EVIDENCE = EvidenceReference(
    "synthetic-contents", "synthetic-fixture", "sha256:" + "1" * 64,
    "2026-08-15T00:00:00Z"
)
OFFER_EVIDENCE = EvidenceReference(
    "synthetic-sealed-offer", "synthetic-fixture", "sha256:" + "2" * 64,
    "2026-08-15T00:00:00Z"
)


def fixture_analysis(
    sealed="60", singles=("23.56", "14.44"), *, completeness="complete",
    offer_currency="USD", value_currency="USD", second_provider="synthetic-market",
):
    components = (
        GuaranteedComponent("figure-alpha", "collectible-figure", 1, "edition-a", "standard", "xx", evidence_ids=("synthetic-contents",)),
        GuaranteedComponent("figure-beta", "collectible-figure", 1, "edition-b", "standard", "xx", evidence_ids=("synthetic-contents",)),
    )
    manifest = FixedContentProductManifest(
        "synthetic-figure-set", "synthetic-figures", "fixed-collection", components,
        completeness, (MANIFEST_EVIDENCE,), effective_at=NOW,
        unknowns=() if completeness == "complete" else ("manifest may omit a figure",),
        assumptions=("supplied offers are contemporaneously comparable",),
        limitations=("synthetic evidence only",),
    )
    offer = ProductAcquisitionOffer(
        "sealed-offer", manifest.product_id, "synthetic-shop", NOW,
        offer_currency, Decimal(sealed), (OFFER_EVIDENCE,),
    )
    valuations = []
    for index, (component, price) in enumerate(zip(components, singles)):
        observation = MarketObservation(
            "printing", component.printing_id,
            "synthetic-market" if index == 0 else second_provider,
            NOW, NOW, None if price is None else Decimal(price), value_currency,
            "current-acquisition-offer", component.finish,
            provenance={"language": component.language, "fixture": "synthetic"},
        )
        valuations.append(ComponentValuationInput(
            component.component_id, observation, component.printing_id,
            component.finish, component.language,
        ))
    return analyze_fixed_content(manifest, offer, tuple(valuations), top_n=2)


def decide(analysis, objective=MINIMIZE_ACQUISITION_COST, **kwargs):
    return evaluate_sealed_vs_singles(
        analysis, objective,
        constraints=kwargs.pop("constraints", {"singles_transaction_cost": "0"}),
        **kwargs,
    )


class SealedVsSinglesDecisionTests(unittest.TestCase):
    def test_singles_cheaper_end_to_end_projection_identity_and_replay(self):
        analysis = fixture_analysis()
        request = build_sealed_vs_singles_request(
            analysis, MINIMIZE_ACQUISITION_COST,
            constraints={"singles_transaction_cost": "0"},
            preferences={"delivery": "now"},
        )
        replay = build_sealed_vs_singles_request(
            analysis, MINIMIZE_ACQUISITION_COST,
            constraints={"singles_transaction_cost": "0"},
            preferences={"delivery": "now"},
            supported_alternatives=(BUY_SINGLES_NOW, BUY_SEALED_NOW),
        )
        self.assertEqual(request.request_id, replay.request_id)
        self.assertEqual(request.domain_inputs["product_id"], "synthetic-figure-set")
        self.assertEqual(request.domain_inputs["analysis_state"], "known")
        self.assertEqual(len(request.domain_inputs["evidence_timestamps"]), 4)
        result = decide(analysis)
        self.assertEqual(result.selected_alternative_id, BUY_SINGLES_NOW)
        self.assertEqual(result.rationale[0]["estimated_current_acquisition_cost_difference"], "22.00")
        self.assertEqual(result.to_json(), decide(analysis).to_json())
        self.assertEqual(current_acquisition_cost_policy().to_dict(), current_acquisition_cost_policy().to_dict())
        self.assertIn(analysis.analysis_id, result.input_snapshot_ids)

    def test_sealed_cheaper_and_objectives_are_isolated(self):
        analysis = fixture_analysis("45", ("30", "28"))
        first = decide(analysis)
        second = decide(analysis, ACQUIRE_GUARANTEED_CONTENTS_NOW)
        self.assertEqual(first.selected_alternative_id, BUY_SEALED_NOW)
        self.assertEqual(second.selected_alternative_id, BUY_SEALED_NOW)
        self.assertNotEqual(first.request_id, second.request_id)
        self.assertEqual(second.rationale[0]["objective"], ACQUIRE_GUARANTEED_CONTENTS_NOW)

    def test_transaction_costs_change_the_supported_current_cost_decision(self):
        analysis = fixture_analysis("42", ("20", "20"))
        self.assertEqual(decide(analysis).selected_alternative_id, BUY_SINGLES_NOW)
        with_fees = decide(analysis, constraints={"singles_transaction_cost": "3"})
        self.assertEqual(with_fees.selected_alternative_id, BUY_SEALED_NOW)
        self.assertEqual(with_fees.rationale[0]["singles_current_acquisition_cost"], "43")
        missing = decide(analysis, constraints={})
        self.assertEqual(missing.outcome, "abstain")
        self.assertIn("singles_transaction_cost_unknown", missing.abstention_reasons)

    def test_incomplete_unknown_currency_and_market_dimensions_abstain(self):
        cases = (
            fixture_analysis(completeness="incomplete"),
            fixture_analysis(singles=(None, "38")),
            fixture_analysis(offer_currency="EUR"),
            fixture_analysis(second_provider="other-market"),
        )
        results = tuple(decide(item) for item in cases)
        self.assertTrue(all(item.outcome == "abstain" for item in results))
        self.assertIn("required_component_values_unknown", results[1].abstention_reasons)
        self.assertIn("incompatible_currencies", results[2].abstention_reasons)
        self.assertIn("incompatible_market_dimensions", results[3].abstention_reasons)

    def test_tie_unsupported_objective_and_future_alternative_abstain(self):
        tied = decide(fixture_analysis("38", ("20", "18")))
        self.assertEqual(tied.outcome, "abstain")
        self.assertIn("policy_tie", tied.abstention_reasons)
        future = decide(fixture_analysis(), "which_option_will_appreciate_more")
        self.assertEqual(future.outcome, "abstain")
        self.assertIn("unsupported_objective", future.abstention_reasons)
        waiting = decide(
            fixture_analysis(), supported_alternatives=(BUY_SEALED_NOW, BUY_SINGLES_NOW, WAIT)
        )
        self.assertEqual(waiting.outcome, "abstain")
        self.assertIn("unsupported_alternative_requested", waiting.abstention_reasons)

    def test_contradiction_and_provenance_conflict_fail_closed(self):
        original = fixture_analysis().to_dict()
        original.pop("analysis_id")
        original["sealed_minus_components"] = "999"
        contradictory = decide(FixedContentProductAnalysis(original))
        self.assertEqual(contradictory.outcome, "abstain")
        self.assertIn("contradictory_product_economics", contradictory.abstention_reasons)
        conflict = fixture_analysis().to_dict()
        conflict.pop("analysis_id")
        duplicate = dict(conflict["evidence"][0])
        duplicate["content_digest"] = "sha256:" + "9" * 64
        conflict["evidence"].append(duplicate)
        conflicted = decide(FixedContentProductAnalysis(conflict))
        self.assertEqual(conflicted.outcome, "abstain")
        self.assertIn("provenance_conflict", conflicted.abstention_reasons)

    def test_thresholds_anchor_context_gaps_and_reasoning_context(self):
        analysis = fixture_analysis("60", ("31", "7"))
        result = decide(analysis)
        self.assertEqual(result.selected_alternative_id, BUY_SINGLES_NOW)
        rationale = result.rationale[0]
        self.assertGreater(Decimal(rationale["anchor_concentration_percentage"]), Decimal("80"))
        self.assertIn("not a price forecast", rationale["anchor_concentration_semantics"])
        self.assertTrue(any("descriptive only" in item.statement for item in result.supporting_factors))
        conditions = result.to_dict()["decision_change_conditions"]
        self.assertEqual(conditions[0]["singles_cost_upper_threshold"], "60")
        self.assertEqual(conditions[1]["sealed_cost_upper_threshold"], "38")
        self.assertTrue(any("objective" in item for item in conditions))
        for gap in ("presale_scarcity_premium", "sealed_collectible_premium", "reprint_risk", "historical_comparable_product_behavior"):
            self.assertTrue(any(gap in item for item in result.limitations))
        context = recommendation_reasoning_context(result)
        recommendation = context["recommendation"]
        self.assertEqual(recommendation["selected_alternative_id"], BUY_SINGLES_NOW)
        self.assertTrue(recommendation["supporting_factors"])
        self.assertTrue(recommendation["counterarguments"])
        self.assertTrue(recommendation["decision_change_conditions"])
        self.assertTrue(recommendation["uncertainties"])

    def test_game_neutral_no_special_cases_and_protected_data_unchanged(self):
        before = {path: path.read_bytes() for path in Path("data").rglob("*") if path.is_file()}
        result = decide(fixture_analysis())
        after = {path: path.read_bytes() for path in Path("data").rglob("*") if path.is_file()}
        self.assertEqual(result.outcome, "selected")
        self.assertEqual(before, after)
        source = Path("src/product_intelligence/acquisition_decision.py").read_text().lower()
        for name in ("crack the plates", "hobbit", "secret lair", "commander deck", "magic"):
            self.assertNotIn(name, source)
        self.assertNotIn("future price", " ".join(item.statement.lower() for item in result.supporting_factors))


if __name__ == "__main__":
    unittest.main()
