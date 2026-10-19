"""Authored targeting and loyalty scope comparisons, never classifiers.

The retained 605 projection verifies the outgoing citation relationships.  The
unprojected rule-body descriptions in this module are PM design input only.
This record compares future source scopes without reading source artifacts,
recognizing targets, or evaluating an ability's loyalty or mana status.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .common import DesignRecord, PM_INPUT, _exact, _json, _strings


CLASSIFICATION_ONLY_SCOPE = ("606.1", "606.2")
FULL_LOYALTY_SCOPE = ("606.1", "606.2", "606.3", "606.4", "606.5", "606.6")
PROVISIONAL_CLASSIFICATION_SCOPE = ("115.6", *CLASSIFICATION_ONLY_SCOPE)


def _unprojected(reference: str, role: str) -> dict[str, Any]:
    return {
        "rule_reference": reference,
        "proposed_role": role,
        "evidence_status": PM_INPUT,
        "source_verified": False,
        "coverage_state": "UNPROJECTED",
        "exact_body_and_scope": "REQUIRES_FUTURE_SOURCE_VERIFICATION",
    }


def _body() -> dict[str, Any]:
    return {
        "evidence_status": PM_INPUT,
        "observation_scope": "UNPROJECTED_RULE_BODIES_ARE_PM_DESIGN_INPUT_ONLY",
        "target_requirement_design": {
            "dependency_reference": "115.6",
            "dependency_classification": "BOUNDED_DIRECT_DEPENDENCY",
            "capability": "target_requirement_semantics",
            "consumer_references": ["605.1a", "605.1b"],
            "evidence_status": PM_INPUT,
            "source_verified": False,
            "coverage_state": "UNPROJECTED",
            "separate_concepts": [
                "target_requirement_semantics", "current_targets_chosen", "target_legality",
            ],
            "target_requirement_equals_current_target_count": False,
            "target_requirement_equals_target_legality": False,
            "design_observation": (
                "Permitting a declaration of zero targets does not alone establish that an ability has no target requirement."
            ),
            "synthetic_declarations": [
                {
                    "fixture_reference": "synthetic-zero-chosen-targets-with-requirement",
                    "fixture_kind": "SYNTHETIC_ONLY",
                    "evidence_status": "CALLER_SUPPLIED_DESIGN_DECLARATION",
                    "declared_requires_target": True,
                    "declared_current_targets_chosen": 0,
                    "declared_target_legality": "UNKNOWN",
                    "meaning": "ZERO_CHOSEN_TARGETS_DOES_NOT_REMOVE_A_DECLARED_REQUIREMENT",
                    "target_requirement_evaluated": False,
                    "target_selection_performed": False,
                    "target_legality_evaluated": False,
                },
                {
                    "fixture_reference": "synthetic-unknown-target-requirement",
                    "fixture_kind": "SYNTHETIC_ONLY",
                    "evidence_status": "CALLER_SUPPLIED_DESIGN_DECLARATION",
                    "declared_requires_target": "UNKNOWN",
                    "declared_current_targets_chosen": 0,
                    "declared_target_legality": "UNKNOWN",
                    "meaning": "MISSING_REQUIREMENT_KNOWLEDGE_REMAINS_INDETERMINATE",
                    "target_requirement_evaluated": False,
                    "target_selection_performed": False,
                    "target_legality_evaluated": False,
                },
            ],
            "standalone_scope_assessment": {
                "proposed_source_allowlist": ["115.6"],
                "finding": "PROVISIONALLY_COHERENT_FOR_NARROW_TARGET_REQUIREMENT_DISTINCTION",
                "rationale": (
                    "The supplied distinction directly qualifies both retained no-target classification consumers; broader target recognition can remain explicitly unresolved."
                ),
                "surrounding_source_units_claimed_necessary": [],
                "source_coherence_independently_verified": False,
                "future_exact_source_verification_required": True,
                "general_target_recognition_satisfied": False,
                "general_target_parser_available": False,
                "target_legality_satisfied": False,
                "unknown_source_context_action": "STOP_FOR_SEPARATE_SCOPE_REVIEW",
            },
            "unresolved_semantic_boundaries": [
                "activated_ability_target_grammar", "triggered_ability_target_grammar",
                "keyword_defined_targets", "real_card_and_effect_semantics",
                "target_legality", "target_selection",
            ],
            "additional_numbered_dependencies_claimed": [],
            "future_primitives": [
                "target_requirement_evidence", "target_count_declaration",
                "target_requirement_unknown_state", "target_requirement_target_legality_separation",
            ],
            "execution_readiness": "BLOCKED",
        },
        "loyalty_scope_comparison": {
            "dependency_reference": "606",
            "dependency_classification": "BOUNDED_SECTION_CLASSIFICATION_DEPENDENCY",
            "consumer_references": ["605.1a"],
            "evidence_status": PM_INPUT,
            "source_verified": False,
            "coverage_state": "UNPROJECTED",
            "classification_capability": "loyalty_ability_classification",
            "execution_capability": "loyalty_ability_execution",
            "classification_implies_execution": False,
            "candidates": [
                {
                    "candidate": "A_CLASSIFICATION_ONLY",
                    "source_allowlist": list(CLASSIFICATION_ONLY_SCOPE),
                    "source_unit_count": 2,
                    "units": [
                        _unprojected("606.1", "Immediate loyalty-category context for activated abilities."),
                        _unprojected("606.2", "Proposed loyalty-symbol activation-cost classification criterion."),
                    ],
                    "source_coherence": "PROVISIONALLY_COHERENT_CLASSIFICATION_CONTEXT_AND_CRITERION",
                    "consumer_value": "NARROW_LOYALTY_EXCLUSION_KNOWLEDGE_FOR_605_1A",
                    "subsystem_breadth": "CLASSIFICATION_CONTEXT_ONLY",
                    "implementation_risk": "LOW_SCOPE_RISK_WITH_EXPLICIT_BEHAVIOR_DEFERRAL",
                    "broad_606_section_reference_resolved": False,
                    "classification_specific_relationship": "MAY_BE_REPRESENTED_SEPARATELY_AFTER_SOURCE_VERIFICATION",
                    "behavior_units_remaining_unprojected": ["606.3", "606.4", "606.5", "606.6"],
                    "execution_readiness": "BLOCKED",
                },
                {
                    "candidate": "B_COMPLETE_LOCAL_SECTION",
                    "source_allowlist": list(FULL_LOYALTY_SCOPE),
                    "source_unit_count": 6,
                    "units": [
                        _unprojected("606.1", "Immediate loyalty-category context for activated abilities."),
                        _unprojected("606.2", "Proposed loyalty-symbol activation-cost classification criterion."),
                        *[_unprojected(reference, "Proposed loyalty activation or counter-cost behavior outside the narrow classification need.")
                          for reference in FULL_LOYALTY_SCOPE[2:]],
                    ],
                    "source_coherence": "POTENTIAL_COMPLETE_LOCAL_SECTION_REQUIRES_FUTURE_VERIFICATION",
                    "consumer_value": "BROADER_LOYALTY_BEHAVIOR_KNOWLEDGE_BEYOND_605_1A_CLASSIFICATION",
                    "subsystem_breadth": "CLASSIFICATION_PLUS_ACTIVATION_AND_COUNTER_COST_CONTEXT",
                    "implementation_risk": "GREATER_TIMING_STATE_AND_PAYMENT_BOUNDARY_EXPOSURE",
                    "broad_606_section_reference_resolution": "POSSIBLE_ONLY_AFTER_EXACT_COMPLETE_FAMILY_VERIFICATION",
                    "execution_readiness": "BLOCKED",
                },
            ],
            "comparison_criteria": [
                "coherent_classification_context", "retained_consumer_value",
                "broad_section_resolution_honesty", "explicit_behavior_deferral",
                "subsystem_scope_risk", "fail_closed_unknown_state",
            ],
            "preferred_candidate": "A_CLASSIFICATION_ONLY",
            "preference_basis": (
                "Category context and its proposed criterion address the retained loyalty exclusion while avoiding unrelated timing and counter-cost scope; the preference does not depend solely on unit count."
            ),
            "preference_state": "PROVISIONAL_PENDING_EXACT_SOURCE_VERIFICATION",
            "source_shape_or_coherence_discrepancy_action": "STOP_FOR_SEPARATE_SCOPE_REVIEW",
            "section_reference_policy": {
                "classification_only_coverage_closes_broad_606_reference": False,
                "existing_605_1a_direct_dependency_rewritten": False,
                "classification_relationship": "NARROWER_THAN_FULL_SECTION_REFERENCE_RESOLUTION",
                "broad_section_dependency_state_after_classification_only": "PARTIALLY_REPRESENTED_BEHAVIOR_SCOPE_OPEN",
                "future_reassessment_required": True,
            },
            "deferred_behavior_units": [
                _unprojected(reference, "Loyalty activation or counter-cost behavior remains outside classification-only scope.")
                for reference in FULL_LOYALTY_SCOPE[2:]
            ],
            "execution_requirements_remaining": [
                "timing", "stack_state", "main_phase_state", "prior_activation_history",
                "loyalty_counter_costs", "multiple_loyalty_cost_handling",
                "negative_cost_sufficiency", "cost_payment", "permanent_state", "controller_state",
            ],
            "future_primitives": [
                "ability_kind_evidence", "activation_cost_symbol_evidence",
                "loyalty_category_unknown_state", "loyalty_classification_execution_separation",
            ],
            "real_loyalty_classifier_available": False,
            "execution_readiness": "BLOCKED",
        },
        "classification_boundaries": {
            "source_coverage_implies_execution": False,
            "narrow_dependency_coverage_implies_full_section_resolution": False,
            "target_requirement_semantics_implies_target_parser": False,
            "loyalty_classification_implies_loyalty_execution": False,
            "real_ability_classification_available": False,
            "real_card_effect_semantics": "ABSENT",
            "unsupported_result_policy": "INDETERMINATE_OR_UNSUPPORTED_WHEN_UNMODELED_INFORMATION_CAN_AFFECT_A_RESULT",
            "runtime_implemented": False,
        },
        "proposed_classification_projection": {
            "candidate": "BOUNDED_MANA_CLASSIFICATION_DEPENDENCY_SCOPE",
            "exact_provisional_source_allowlist": list(PROVISIONAL_CLASSIFICATION_SCOPE),
            "proposed_source_unit_count": 3,
            "target_consumers": ["605.1a", "605.1b"],
            "source_verified": False,
            "evidence_status": PM_INPUT,
            "source_coherence": "PROVISIONAL_REQUIRES_EXACT_FUTURE_ARTIFACT_REVIEW",
            "broad_606_section_resolution_claimed": False,
            "verified_txt_required_for_future_projection": True,
            "expected_anchor_type": "MULTI_LINE_RULE_BLOCK_ANCHOR",
            "expected_span_policy": "EXACT_RULE_BLOCK_RAW_BYTES_EXCLUDING_FINAL_LINE_TERMINATOR",
            "historical_anchor_conversion": False,
            "authorized": False,
            "started": False,
        },
        "design_notes": [
            "Retained outgoing citations establish dependency relationships; all descriptions and future scopes of unprojected bodies remain PM design input."
        ],
    }


@dataclass(frozen=True)
class ManaClassificationDependencyDesign(DesignRecord):
    """Immutable comparison of narrow targeting and loyalty source scopes."""

    SCHEMA = "mana-classification-dependency-design-v1"
    ID_FIELD = "classification_design_id"
    BODY_FIELDS = frozenset(_body())

    @staticmethod
    def _validate_body(body: dict[str, Any]) -> None:
        expected = _body()
        for field in expected:
            if field != "design_notes":
                _exact(body[field], expected[field], field)
        _strings(body["design_notes"], "design_notes", nonempty=True)


def build_classification_design(*, design_notes: Any = None) -> ManaClassificationDependencyDesign:
    """Build a design record with no source, network, or gameplay access."""
    body = _body()
    if design_notes is not None:
        body["design_notes"] = _json(design_notes)
    return ManaClassificationDependencyDesign.create(body)
