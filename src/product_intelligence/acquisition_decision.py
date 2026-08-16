"""Synthetic-first fixed-content acquisition decisions over descriptive analysis."""
from __future__ import annotations

from decimal import Decimal, InvalidOperation
from typing import Any, Mapping

from decision_intelligence import (
    AcquisitionDecisionOrchestrator,
    AnalysisMetric,
    DecisionAlternative,
    DecisionPolicy,
    DecisionRequest,
    DomainAnalysisEnvelope,
    EvidenceReference,
    Factor,
    MetricCriterion,
    StructuredRecommendation,
)

from .analysis import DEFERRED_DIMENSIONS, FixedContentProductAnalysis
from .models import ProductValidationError

MINIMIZE_ACQUISITION_COST = "minimize_acquisition_cost_for_guaranteed_contents"
ACQUIRE_GUARANTEED_CONTENTS_NOW = "acquire_guaranteed_contents_now"
SUPPORTED_OBJECTIVES = frozenset(
    {MINIMIZE_ACQUISITION_COST, ACQUIRE_GUARANTEED_CONTENTS_NOW}
)

BUY_SEALED_NOW = "BUY_SEALED_NOW"
BUY_SINGLES_NOW = "BUY_SINGLES_NOW"
WAIT = "WAIT"
BUY_SEALED_AND_KEEP_SEALED = "BUY_SEALED_AND_KEEP_SEALED"
SELL_EARLY_REBUY_LATER = "SELL_EARLY_REBUY_LATER"
SUPPORTED_ALTERNATIVES = (BUY_SEALED_NOW, BUY_SINGLES_NOW)
KNOWN_ALTERNATIVES = frozenset(
    SUPPORTED_ALTERNATIVES
    + (WAIT, BUY_SEALED_AND_KEEP_SEALED, SELL_EARLY_REBUY_LATER)
)

POLICY_ID = "fixed-content-current-acquisition-cost"
POLICY_VERSION = "1.0.0"
COST_METRIC = "acquisition.current_comparable_cost"


def current_acquisition_cost_policy() -> DecisionPolicy:
    """Return the exact versioned policy used by this vertical."""
    return DecisionPolicy(
        POLICY_ID, POLICY_VERSION, (MetricCriterion(COST_METRIC, "minimize"),)
    )


def _decimal(value: Any, name: str) -> Decimal:
    try:
        result = Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError) as error:
        raise ProductValidationError(f"{name} must be a finite non-negative decimal") from error
    if not result.is_finite() or result < 0:
        raise ProductValidationError(f"{name} must be a finite non-negative decimal")
    return result


def _evidence(payload: Mapping[str, Any]) -> tuple[EvidenceReference, ...]:
    items = tuple(EvidenceReference(**item) for item in payload.get("evidence", ()))
    by_id: dict[str, EvidenceReference] = {}
    for item in items:
        if item.evidence_id not in by_id:
            by_id[item.evidence_id] = item
    return tuple(sorted(by_id.values(), key=lambda item: item.evidence_id))


def _has_provenance_conflict(payload: Mapping[str, Any]) -> bool:
    by_id: dict[str, EvidenceReference] = {}
    for raw in payload.get("evidence", ()):
        item = EvidenceReference(**raw)
        if item.evidence_id in by_id and by_id[item.evidence_id] != item:
            return True
        by_id[item.evidence_id] = item
    return False


def build_sealed_vs_singles_request(
    analysis: FixedContentProductAnalysis,
    objective: str,
    *,
    constraints: Mapping[str, Any],
    preferences: Mapping[str, Any] | None = None,
    supported_alternatives: tuple[str, ...] = SUPPORTED_ALTERNATIVES,
) -> DecisionRequest:
    """Project Product Intelligence identity and facts into a generic request."""
    if not isinstance(analysis, FixedContentProductAnalysis):
        raise ProductValidationError("typed fixed-content analysis is required")
    payload = analysis.to_dict()
    alternatives = tuple(
        DecisionAlternative(
            action,
            action,
            (payload["product_id"],),
            {"support_state": "supported" if action in SUPPORTED_ALTERNATIVES else "unsupported"},
        )
        for action in supported_alternatives
    )
    if not alternatives or len(set(supported_alternatives)) != len(supported_alternatives):
        raise ProductValidationError("supported alternatives must be non-empty and unique")
    if any(action not in KNOWN_ALTERNATIVES for action in supported_alternatives):
        raise ProductValidationError("unknown acquisition alternative")
    evidence = _evidence(payload)
    timestamps = sorted(
        item.recorded_at for item in evidence if item.recorded_at is not None
    )
    domain_inputs = {
        "product_id": payload["product_id"],
        "game_id": payload["game_id"],
        "manifest_id": payload["manifest_id"],
        "offer_id": payload["offer_id"],
        "product_analysis_id": payload["analysis_id"],
        "analysis_state": payload["state"],
        "currency": payload["currency"],
        "coverage": payload["coverage"],
        "comparability_issues": payload["comparability_issues"],
        "assumptions": payload["assumptions"],
        "limitations": payload["limitations"],
        "unsupported_dimensions": payload["unsupported_dimensions"],
        "evidence_timestamps": timestamps,
    }
    return DecisionRequest(
        objective,
        alternatives,
        dict(constraints),
        dict(preferences or {}),
        domain_inputs,
        evidence,
        POLICY_ID,
        POLICY_VERSION,
        {"confidence_semantics": "evidence completeness and decision support; not future-price probability"},
        (payload["analysis_id"], payload["manifest_id"], payload["offer_id"]),
    )


def _preflight_reasons(
    payload: Mapping[str, Any], request: DecisionRequest
) -> tuple[str, ...]:
    reasons: list[str] = []
    if request.objective not in SUPPORTED_OBJECTIVES:
        reasons.append("unsupported_objective")
    if _has_provenance_conflict(payload):
        reasons.append("provenance_conflict")
    actions = {item.action for item in request.alternatives}
    if actions != set(SUPPORTED_ALTERNATIVES):
        reasons.append("unsupported_alternative_requested")
    if payload["state"] != "known":
        reasons.append("decision_critical_product_analysis_incomplete")
    coverage = payload["coverage"]
    if coverage["unknown_unpriced_component_count"] or coverage["unknown_unpriced_quantity"]:
        reasons.append("required_component_values_unknown")
    issues = set(payload["comparability_issues"])
    if "incompatible_currencies" in issues:
        reasons.append("incompatible_currencies")
    if issues - {"incompatible_currencies"}:
        reasons.append("incompatible_market_dimensions")
    if "singles_transaction_cost" not in request.constraints:
        reasons.append("singles_transaction_cost_unknown")
    if payload.get("total_guaranteed_component_acquisition_value") is None:
        reasons.append("missing_components_acquisition_cost")
    if payload.get("sealed_acquisition_cost") is None:
        reasons.append("missing_sealed_acquisition_cost")
    if payload.get("sealed_minus_components") is not None:
        sealed = Decimal(payload["sealed_acquisition_cost"])
        components = Decimal(payload["total_guaranteed_component_acquisition_value"])
        if Decimal(payload["sealed_minus_components"]) != sealed - components:
            reasons.append("contradictory_product_economics")
        if Decimal(payload["components_minus_sealed"]) != components - sealed:
            reasons.append("contradictory_product_economics")
    return tuple(sorted(set(reasons)))


def _envelopes(
    payload: Mapping[str, Any], request: DecisionRequest, reasons: tuple[str, ...]
) -> tuple[DomainAnalysisEnvelope, ...]:
    evidence = _evidence(payload)
    evidence_ids = tuple(item.evidence_id for item in evidence)
    currency = payload["currency"]
    known = not reasons
    singles_fee = _decimal(request.constraints.get("singles_transaction_cost", 0), "singles_transaction_cost")
    costs = {
        BUY_SEALED_NOW: Decimal(payload.get("sealed_acquisition_cost") or 0),
        BUY_SINGLES_NOW: Decimal(payload.get("total_guaranteed_component_acquisition_value") or 0) + singles_fee,
    }
    common_places = max(0, *(max(0, -cost.as_tuple().exponent) for cost in costs.values()))
    scale = Decimal(10) ** common_places
    normalized_costs = {action: int(cost * scale) for action, cost in costs.items()}
    limitations = tuple(payload["limitations"]) + tuple(
        f"not evaluated: {name}" for name in sorted(DEFERRED_DIMENSIONS)
    )
    uncertainty = {
        "coverage": payload["coverage"],
        "comparability_issues": payload["comparability_issues"],
        "unsupported_dimensions": payload["unsupported_dimensions"],
        "decision_support_state": "supported" if known else "insufficient",
    }
    by_action = {item.action: item.alternative_id for item in request.alternatives}
    return tuple(
        DomainAnalysisEnvelope(
            "fixed-content-acquisition-decision",
            POLICY_VERSION,
            by_action[action],
            (
                AnalysisMetric(
                    COST_METRIC,
                    "known" if known else "incomplete",
                    normalized_costs[action] if known else None,
                    f"{currency} scaled by 10^{common_places}",
                    evidence_ids=evidence_ids,
                ),
            ),
            evidence,
            state="known" if known else "incomplete",
            assumptions=tuple(payload["assumptions"]),
            limitations=limitations,
            uncertainty=uncertainty,
            sensitivity_inputs={
                "sealed_cost": payload.get("sealed_acquisition_cost"),
                "singles_component_cost": payload.get("total_guaranteed_component_acquisition_value"),
                "singles_transaction_cost": format(singles_fee, "f"),
                "comparison_decimal_places": common_places,
            },
            input_snapshot_ids=request.input_snapshot_ids,
        )
        for action in SUPPORTED_ALTERNATIVES
        if action in by_action
    )


def evaluate_sealed_vs_singles(
    analysis: FixedContentProductAnalysis,
    objective: str,
    *,
    constraints: Mapping[str, Any],
    preferences: Mapping[str, Any] | None = None,
    supported_alternatives: tuple[str, ...] = SUPPORTED_ALTERNATIVES,
) -> StructuredRecommendation:
    """Build and evaluate the bounded current-cost acquisition decision."""
    request = build_sealed_vs_singles_request(
        analysis,
        objective,
        constraints=constraints,
        preferences=preferences,
        supported_alternatives=supported_alternatives,
    )
    payload = analysis.to_dict()
    reasons = _preflight_reasons(payload, request)
    envelopes = _envelopes(payload, request, reasons)
    result = AcquisitionDecisionOrchestrator().evaluate(
        request, envelopes, current_acquisition_cost_policy()
    )
    combined_reasons = tuple(sorted(set(result.abstention_reasons) | set(reasons)))
    by_id = {item.alternative_id: item.action for item in request.alternatives}
    selected_action = by_id.get(result.selected_alternative_id) if not combined_reasons else None
    sealed = Decimal(payload.get("sealed_acquisition_cost") or 0)
    singles_fee = _decimal(request.constraints.get("singles_transaction_cost", 0), "singles_transaction_cost")
    singles = Decimal(payload.get("total_guaranteed_component_acquisition_value") or 0) + singles_fee
    difference = abs(sealed - singles)
    concentration = payload.get("largest_component_percentage")
    selected_id = result.selected_alternative_id if selected_action else None
    rationale = ({
        "objective": objective,
        "selected_action": selected_action,
        "currency": payload["currency"],
        "sealed_current_acquisition_cost": format(sealed, "f"),
        "singles_current_acquisition_cost": format(singles, "f"),
        "estimated_current_acquisition_cost_difference": format(difference, "f"),
        "largest_value_driving_component": payload.get("largest_value_driving_component"),
        "anchor_concentration_percentage": concentration,
        "anchor_concentration_semantics": "descriptive current component-value concentration; not a price forecast",
    },) if not combined_reasons else ({"objective": objective, "selected_action": None},)
    supporting = result.supporting_factors
    counterarguments = result.counterarguments
    if selected_id and concentration is not None:
        supporting += (Factor(
            "anchor-concentration-context",
            selected_id,
            "product.anchor_concentration_percentage",
            f"The largest component represents {concentration}% of current guaranteed-component value; this is descriptive only.",
            tuple(item.evidence_id for item in result.evidence_references),
        ),)
    if selected_id:
        other = BUY_SEALED_NOW if selected_action == BUY_SINGLES_NOW else BUY_SINGLES_NOW
        counterarguments += (Factor(
            "alternative-cost-threshold-counterargument",
            other,
            COST_METRIC,
            "The non-selected current route would become preferred if its comparable acquisition cost fell below the selected route's cost.",
            tuple(item.evidence_id for item in result.evidence_references),
        ),)
    conditions = ()
    if selected_id:
        conditions = (
            {
                "condition": "BUY_SINGLES_NOW remains preferred while comparable singles acquisition cost is below effective sealed acquisition cost",
                "singles_cost_upper_threshold": format(sealed, "f"),
                "currency": payload["currency"],
            },
            {
                "condition": "BUY_SEALED_NOW remains preferred while effective sealed acquisition cost is below comparable singles acquisition cost",
                "sealed_cost_upper_threshold": format(singles, "f"),
                "currency": payload["currency"],
            },
            {"condition": "decision becomes indeterminate if a required component value becomes unavailable"},
            {"condition": "recommendation applies only to the supplied acquisition objective", "objective": objective},
        )
    return StructuredRecommendation(
        request.request_id,
        "selected" if selected_id else "abstain",
        selected_id,
        POLICY_ID,
        POLICY_VERSION,
        rationale,
        result.evidence_references,
        supporting,
        counterarguments,
        result.uncertainties,
        result.assumptions,
        result.limitations,
        conditions,
        result.input_snapshot_ids,
        combined_reasons,
    )
