"""A provisional bounded stack-exception scope, never a stack implementation."""
from dataclasses import dataclass
from typing import ClassVar

from .common import DesignRecord, PM_INPUT, _exact, _json, _keys, _strings


def _body(notes):
    return {
        "evidence_status": PM_INPUT,
        "frontier_reference": "405.6c",
        "capability": "mana_ability_stack_exception_context",
        "classification": "BOUNDED_STACK_CONTEXT",
        "scope_assessment": {
            "source_scope_size": "SINGLE_CHILD_OR_PARENT_WITH_CHILD",
            "semantic_responsibility": "MANA_ABILITY_NO_STACK_EXCEPTION_AND_PRIORITY_CONTEXT",
            "direct_retained_consumer": "605.3b",
            "semantic_overlap_without_new_citation": ["605.4a"],
            "implementation_risk": "LOW_FOR_SOURCE_COVERAGE_HIGH_FOR_RUNTIME",
            "projection_suitability": "PROVISIONALLY_BOUNDED_PENDING_EXACT_SOURCE_VERIFICATION",
            "general_stack_semantics_supplied": False,
            "source_verified": False,
        },
        "scope_options": [
            {"option_id": "CHILD_ONLY", "exact_provisional_refs": ["405.6c"],
             "proposed_source_unit_count": 1,
             "source_coherence_assessment": "PROVISIONALLY_COHERENT_WITH_RETAINED_605_EXCEPTION_CONTEXT",
             "context_available": ["605.3b", "605.4a"],
             "rationale": "The supplied child description states the mana no-stack exception; retained mana behavior already gives its immediate context.",
             "unresolved_boundary": "GENERAL_STACK_AND_PRIORITY_SEMANTICS",
             "selected_for_future_scope_design": True,
             "evidence_status": PM_INPUT, "source_verified": False, "coverage_state": "UNPROJECTED"},
            {"option_id": "PARENT_AND_CHILD", "exact_provisional_refs": ["405.6", "405.6c"],
             "proposed_source_unit_count": 2,
             "source_coherence_assessment": "ADDITIONAL_NON_STACK_EVENT_PARENT_CONTEXT_MAY_BE_USEFUL",
             "context_available": ["POTENTIAL_GENERAL_NON_STACK_EVENT_PARENT"],
             "rationale": "The proposed parent would frame other non-stack events, but hierarchy alone does not prove it necessary for this mana-specific citation.",
             "unresolved_boundary": "OTHER_405.6_CHILDREN_AND_GENERAL_STACK_SEMANTICS",
             "selected_for_future_scope_design": False,
             "evidence_status": PM_INPUT, "source_verified": False, "coverage_state": "UNPROJECTED"},
        ],
        "scope_decision": {
            "preferred_option": "CHILD_ONLY",
            "exact_provisional_refs": ["405.6c"], "proposed_source_unit_count": 1,
            "parent_405.6_needed": "NOT_ESTABLISHED_BY_AVAILABLE_DESIGN_INPUT",
            "parent_omission_rationale": "Do not add a broad non-stack parent solely for numbered hierarchy when retained 605 coverage frames the specific exception.",
            "decision_state": "PROVISIONAL_PENDING_EXACT_SOURCE_VERIFICATION",
            "independently_verified_minimum_scope": False,
            "if_child_requires_parent_context": "STOP_FOR_SEPARATE_SCOPE_REVIEW",
            "automatic_scope_expansion": False,
            "authorized": False,
        },
        "exception_relationships": [
            {"general_reference": "602.2", "general_role": "GENERAL_PROCEDURE",
             "general_concept": "ORDINARY_ACTIVATED_ABILITY_STACK_PROCEDURE",
             "retained_exception_reference": "605.3b", "exception_role": "MANA_ABILITY_EXCEPTION",
             "supporting_candidate_context": "405.6c",
             "applicability_condition": "QUALIFYING_ACTIVATED_MANA_ABILITY",
             "general_statement_unconditionally_applied_to_mana_abilities": False,
             "evidence_status": PM_INPUT, "source_verified": False,
             "new_direct_citation_created": False},
            {"general_reference": "603", "general_role": "GENERAL_TRIGGERED_PROCEDURE",
             "general_concept": "ORDINARY_TRIGGERED_ABILITY_STACK_PROCEDURE",
             "retained_exception_reference": "605.4a", "exception_role": "TRIGGERED_MANA_EXCEPTION",
             "supporting_candidate_context": "405.6c",
             "applicability_condition": "QUALIFYING_TRIGGERED_MANA_ABILITY",
             "general_statement_unconditionally_applied_to_mana_abilities": False,
             "evidence_status": PM_INPUT, "source_verified": False,
             "new_direct_citation_created": False},
        ],
        "capability_boundary": {
            "evidence_requirements": ["FUTURE_SOURCE_VERIFIED_405.6c_CONTEXT", "RETAINED_605.3b_AND_605.4a_EXCEPTION_EVIDENCE"],
            "semantic_dependencies": ["mana_ability_classification", "general_activated_ability_procedure", "general_triggered_ability_subsystem"],
            "future_primitives": ["mana_ability_no_stack_exception_context"],
            "unsupported_boundaries": ["general_stack_objects", "resolution_queue", "priority", "response_windows", "countering", "effect_execution"],
            "readiness_status": "BLOCKED", "execution_readiness": "NOT_IMPLEMENTED",
            "execution_supported": False, "source_coverage_implies_execution": False,
            "stack_runtime_created": False, "resolution_queue_created": False,
            "priority_evaluated": False, "response_windows_created": False,
        },
        "limitations": [
            "The verified retained fact is the 605.3b outgoing citation; unprojected 405.6c and 405.6 descriptions remain PM design input.",
            "Overlap with retained 605.4a is semantic context, not a new direct CR citation.",
            "A bounded stack-exception projection would supply neither general stack knowledge nor runtime correctness.",
        ],
        "design_notes": notes,
    }


@dataclass(frozen=True)
class StackExceptionDependencyDesign(DesignRecord):
    SCHEMA: ClassVar[str] = "gameplay-rules-stack-exception-dependency-design-v1"
    ID_FIELD: ClassVar[str] = "stack_context_design_id"
    BODY_FIELDS: ClassVar[frozenset[str]] = frozenset(_body([]))

    @staticmethod
    def _validate_body(body):
        _keys(body, StackExceptionDependencyDesign.BODY_FIELDS)
        _strings(body["design_notes"], "design_notes")
        _exact(body, _body(body["design_notes"]), "stack_context_design")


def build_stack_design(*, design_notes=None):
    return StackExceptionDependencyDesign.create(_body([] if design_notes is None else _json(design_notes)))
