"""Immutable mana-ability behavior concepts, without activation or resolution.

All proposed 605 behavior is PM scoping input.  Existing source projections do
not turn these descriptions into independently verified 605 rule knowledge.
"""
from __future__ import annotations

from dataclasses import dataclass

from .common import DesignRecord, PM_INPUT, _exact, _json, _text


ACTIVATION_WINDOW_ORDER = (
    "ORDINARY_PRIORITY_WINDOW",
    "DURING_SPELL_CASTING_REQUIRING_MANA_PAYMENT",
    "DURING_ABILITY_ACTIVATION_REQUIRING_MANA_PAYMENT",
    "RULE_REQUESTS_MANA_PAYMENT",
    "EFFECT_REQUESTS_MANA_PAYMENT",
)


def _notes(value):
    if not isinstance(value, list) or not value or len(value) > 64:
        from .common import _fail
        _fail("design_notes: bounded nonempty list required")
    for note in value:
        _text(note, "design_notes")


def _capability(evidence, dependencies, primitives, boundaries):
    return {
        "evidence_requirements": evidence,
        "semantic_dependencies": dependencies,
        "future_primitives": primitives,
        "readiness_status": "BLOCKED",
        "implementation_status": "NOT_IMPLEMENTED",
        "unsupported_boundaries": boundaries,
        "source_coverage_status": "DESIGN_SCOPED_UNPROJECTED",
        "source_verified": False,
        "execution_supported": False,
        "implied_ready_capabilities": [],
    }


def _body():
    return {
        "evidence_status": PM_INPUT,
        "activation_windows": [
            {
                "sequence": index,
                "opportunity_id": opportunity,
                "eligibility_category_only": True,
                "condition": condition,
                "evidence_status": PM_INPUT,
                "actual_activation_eligibility_evaluated": False,
                "execution_supported": False,
            }
            for index, (opportunity, condition) in enumerate(zip(
                ACTIVATION_WINDOW_ORDER,
                (
                    "PLAYER_HAS_PRIORITY",
                    "SPELL_CASTING_HAS_REQUIRED_MANA_PAYMENT",
                    "ABILITY_ACTIVATION_HAS_REQUIRED_MANA_PAYMENT",
                    "RULE_REQUESTS_MANA_PAYMENT",
                    "EFFECT_REQUESTS_MANA_PAYMENT",
                ),
            ), 1)
        ],
        "activated_mana_behavior": {
            "evidence_status": PM_INPUT,
            "applies_only_if": "QUALIFYING_ACTIVATED_MANA_ABILITY",
            "ordinary_procedure_boundary": "GENERAL_ACTIVATED_ABILITY_PROCEDURE",
            "candidate_procedure_reference": {
                "reference": "602.2",
                "status": "CANDIDATE_DIRECT_REFERENCE_REQUIRES_SOURCE_VERIFICATION",
                "source_verified": False,
                "projected": False,
            },
            "stack_presence_concept": "DOES_NOT_ENTER_STACK",
            "resolution_sequence_concept": "IMMEDIATELY_AFTER_ACTIVATION",
            "stack_object_targeting_concept": "NO_NORMAL_STACK_OBJECT_TARGET",
            "stack_object_countering_concept": "NO_NORMAL_STACK_OBJECT_COUNTERING",
            "stack_object_response_concept": "NO_NORMAL_STACK_OBJECT_RESPONSE",
            "same_ability_reactivation_concept": "PROHIBITED_UNTIL_ITS_ACTIVATION_FINISHES_RESOLVING",
            "activation_performed": False,
            "resolution_performed": False,
            "response_window_created": False,
            "stack_object_created": False,
            "countering_implemented": False,
        },
        "triggered_mana_behavior": {
            "evidence_status": PM_INPUT,
            "applies_only_if": "QUALIFYING_TRIGGERED_MANA_ABILITY",
            "qualifying_trigger_relationship_categories": [
                "ACTIVATION_OF_ACTIVATED_MANA_ABILITY",
                "RESOLUTION_OF_ACTIVATED_MANA_ABILITY",
                "MANA_ADDED",
            ],
            "classification_requirements": [
                "NO_TARGET",
                "QUALIFYING_TRIGGER_RELATIONSHIP",
                "COULD_ADD_MANA_ON_RESOLUTION",
            ],
            "ordinary_procedure_boundary": "GENERAL_TRIGGERED_ABILITY_SEMANTICS",
            "candidate_procedure_reference": {
                "reference": "603",
                "status": "CANDIDATE_DIRECT_REFERENCE_REQUIRES_SOURCE_VERIFICATION",
                "source_verified": False,
                "projected": False,
            },
            "stack_presence_concept": "DOES_NOT_ENTER_STACK",
            "resolution_sequence_concept": "IMMEDIATELY_AFTER_THE_MANA_ABILITY_THAT_CAUSED_IT",
            "priority_wait_concept": "DOES_NOT_WAIT_FOR_PRIORITY",
            "trigger_detection_performed": False,
            "resolution_performed": False,
            "priority_evaluated": False,
            "stack_object_created": False,
        },
        "ordinary_ability_boundary": {
            "ordinary_activated_ability_stack_behavior": "UNKNOWN_REQUIRES_SEPARATE_SOURCE_REVIEW",
            "ordinary_triggered_ability_stack_behavior": "UNKNOWN_REQUIRES_SEPARATE_SOURCE_REVIEW",
            "mana_exception_satisfies_general_ability_semantics": False,
            "candidate_stack_reference": {
                "reference": "405.6c",
                "status": "CANDIDATE_DIRECT_REFERENCE_REQUIRES_SOURCE_VERIFICATION",
                "source_verified": False,
                "projected": False,
            },
            "stack_runtime": "ABSENT",
            "priority_runtime": "ABSENT",
            "trigger_runtime": "ABSENT",
            "general_activation_runtime": "ABSENT",
        },
        "capabilities": {
            "activated_mana_ability_activation_window": _capability(
                ["FUTURE_SOURCE_VERIFIED_605_ACTIVATION_OPPORTUNITIES", "RETAINED_601.2g_CONSUMER"],
                ["mana_ability_classification", "priority_semantics", "casting_payment_context", "ability_activation_payment_context"],
                ["activated_mana_activation_context", "mana_payment_request_context"],
                ["priority", "casting_execution", "general_ability_activation", "cost_payment"],
            ),
            "activated_mana_ability_immediate_resolution": _capability(
                ["FUTURE_SOURCE_VERIFIED_605_ACTIVATED_BEHAVIOR", "FUTURE_STACK_EXCEPTION_REVIEW"],
                ["mana_ability_classification", "general_activated_ability_semantics", "stack_exception_semantics"],
                ["activated_mana_immediate_resolution", "same_ability_resolution_guard"],
                ["activated_ability_execution", "effect_execution", "stack", "responses", "countering"],
            ),
            "triggered_mana_ability_immediate_resolution": _capability(
                ["FUTURE_SOURCE_VERIFIED_605_TRIGGERED_BEHAVIOR", "FUTURE_TRIGGER_SUBSYSTEM_REVIEW"],
                ["mana_ability_classification", "general_triggered_ability_semantics", "causal_mana_ability_relationship"],
                ["triggered_mana_immediate_sequence", "mana_trigger_causality"],
                ["trigger_detection", "trigger_ordering", "effect_execution", "stack", "priority"],
            ),
            "mana_payment_opportunity": _capability(
                ["RETAINED_601.2g_CONSUMER", "FUTURE_SOURCE_VERIFIED_605_OPPORTUNITIES"],
                ["mana_ability_classification", "activated_mana_ability_activation_window", "determined_cost_mana_condition"],
                ["mana_payment_opportunity_context"],
                ["cost_evaluation", "payment", "mana_production_semantics", "mana_pool_semantics"],
            ),
        },
        "capability_separation": {
            "classification_implies_activation": False,
            "activation_window_implies_resolution": False,
            "no_stack_concept_implies_stack_runtime": False,
            "immediate_resolution_implies_mana_production": False,
            "mana_payment_opportunity_implies_payment": False,
            "source_coverage_implies_execution": False,
            "mana_production_semantics": "BLOCKED_ABSENT",
            "mana_pool_semantics": "BLOCKED_ABSENT",
            "payment_integration": "BLOCKED_ABSENT",
        },
        "design_notes": [
            "These are eligibility and sequencing concepts supplied for review; no ability is activated, detected, resolved, or paid for.",
            "Ordinary ability procedure, priority, stack authority, and real Card/effect semantics require independent closure.",
        ],
    }


@dataclass(frozen=True)
class ManaAbilityBehaviorDesign(DesignRecord):
    """A fixed conceptual behavior inventory, not an ability procedure."""

    SCHEMA = "mana-ability-behavior-design-v1"
    ID_FIELD = "behavior_design_id"
    BODY_FIELDS = frozenset(_body())

    @staticmethod
    def _validate_body(body):
        for field, expected in _body().items():
            if field != "design_notes":
                _exact(body[field], expected, field)
        _notes(body["design_notes"])


def build_behavior_design(*, design_notes=None):
    """Build review metadata without real source access or gameplay input."""
    body = _body()
    if design_notes is not None:
        body["design_notes"] = _json(design_notes)
    return ManaAbilityBehaviorDesign.create(body)
