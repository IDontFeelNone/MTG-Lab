"""Scope a shared trigger subsystem without admitting source or trigger runtime."""
from dataclasses import dataclass
from typing import ClassVar

from .common import DesignRecord, PM_INPUT, _exact, _json, _keys, _strings


TRIGGERED_CAPABILITIES = (
    "triggered_ability_classification", "trigger_event_detection", "trigger_registration",
    "triggered_ability_controller_attribution", "trigger_stack_placement", "trigger_ordering",
    "delayed_trigger_semantics", "delayed_trigger_controller_attribution",
    "zone_change_trigger_semantics", "reflexive_trigger_semantics",
)
DELAYED_CONTROLLER_FRONTIER = ("603.7d", "603.7e", "603.7f")


def _capabilities():
    requirements = (
        ("TRIGGERED_ABILITY_FORM_AND_KIND_EVIDENCE", ["triggered_ability_kind"], ["real_ability_and_effect_semantics"]),
        ("TRIGGER_EVENT_AND_AUTOMATIC_TRIGGERING_EVIDENCE", ["trigger_event_match"], ["event_semantics", "real_effect_semantics"]),
        ("TRIGGER_REGISTRATION_RULES", ["trigger_registration_record"], ["trigger_event_detection", "game_state_history"]),
        ("GENERAL_TRIGGER_CONTROLLER_RULES", ["trigger_controller_evidence"], ["general_controller_semantics", "trigger_source_identity"]),
        ("TRIGGER_STACK_PLACEMENT_RULES", ["trigger_stack_proposal"], ["stack_semantics", "priority_context"]),
        ("TRIGGER_ORDERING_AND_APNAP_RULES", ["trigger_ordering_contract"], ["player_order", "simultaneous_trigger_context"]),
        ("DELAYED_TRIGGER_PARENT_CONTEXT", ["delayed_trigger_identity"], ["effect_history", "trigger_lifetime_semantics"]),
        ("DELAYED_TRIGGER_CONTROLLER_CONTEXT_AND_SELECTED_FRONTIER", ["delayed_trigger_controller_attribution"], ["delayed_trigger_semantics", "general_controller_semantics"]),
        ("ZONE_CHANGE_TRIGGER_RULES", ["zone_change_trigger_evidence"], ["zone_change_identity", "historical_information"]),
        ("REFLEXIVE_TRIGGER_RULES", ["reflexive_trigger_relationship"], ["effect_execution", "trigger_event_semantics"]),
    )
    return [{
        "capability": capability, "evidence_requirements": [evidence],
        "future_primitives": primitives, "semantic_dependencies": dependencies,
        "readiness_status": "BLOCKED", "execution_readiness": "NOT_IMPLEMENTED",
        "implementation_available": False, "execution_supported": False,
        "independently_scoped": True, "implied_ready_capabilities": [],
        "evidence_status": PM_INPUT, "source_verified": False,
    } for capability, (evidence, primitives, dependencies) in zip(TRIGGERED_CAPABILITIES, requirements)]


def _body(notes):
    return {
        "evidence_status": PM_INPUT,
        "frontier_reference": "603",
        "subsystem": "general_triggered_ability_subsystem",
        "classification": "LARGE_SHARED_CORE_SUBSYSTEM",
        "scope_assessment": {
            "source_scope_size": "BROAD_SECTION_WITH_MULTIPLE_SPECIALIZED_FAMILIES",
            "semantic_responsibility": "GENERAL_TRIGGER_DETECTION_CONTROLLER_STACK_ORDERING_AND_SPECIALIZED_TRIGGERS",
            "shared_retained_consumers": ["605.4", "109.4b"],
            "implementation_risk": "HIGH",
            "design_before_projection_required": True,
            "detailed_subsystem_design_complete": False,
            "projection_ready": False,
            "dedicated_design_milestone_ready": True,
            "whole_section_projection_recommended": False,
            "source_verified": False,
        },
        "capabilities": _capabilities(),
        "shared_controller_consumer": {
            "retained_rule_reference": "109.4b",
            "retained_dependency_references": ["603", *DELAYED_CONTROLLER_FRONTIER],
            "required_shared_subsystem": "general_triggered_ability_subsystem",
            "controller_capabilities": ["triggered_ability_controller_attribution", "delayed_trigger_controller_attribution"],
            "separate_mana_trigger_model_created": False,
            "separate_controller_trigger_model_created": False,
            "target_rule_bodies_source_verified_in_this_milestone": False,
            "existing_rule_or_dependencies_modified": False,
        },
        "delayed_trigger_controller_scope_comparison": {
            "evidence_status": PM_INPUT, "source_verified": False,
            "capability": "delayed_trigger_controller_attribution",
            "verified_retained_outgoing_frontier": list(DELAYED_CONTROLLER_FRONTIER),
            "target_rule_body_knowledge": "PM_DESIGN_INPUT_ONLY_NOT_NEW_SOURCE_VERIFICATION",
            "options": [
                {"option_id": "ISOLATED_CONTROLLER_CLUSTER", "exact_provisional_refs": list(DELAYED_CONTROLLER_FRONTIER),
                 "proposed_source_unit_count": 3,
                 "advantage": "Directly addresses the retained controller citations.",
                 "risk": "May omit the parent delayed-trigger concept needed to interpret controller cases coherently.",
                 "selected_for_future_scope_design": False, "source_verified": False},
                {"option_id": "PARENT_CONTEXT_BEFORE_CONTROLLER_CLUSTER",
                 "minimum_context_to_evaluate": "603.7",
                 "retained_controller_frontier": list(DELAYED_CONTROLLER_FRONTIER),
                 "additional_parent_or_sibling_scope": "UNKNOWN_REQUIRES_DEDICATED_DESIGN_AND_FUTURE_SOURCE_VERIFICATION",
                 "exact_final_allowlist_known": False,
                 "advantage": "Treat delayed-controller rules within the delayed-trigger family they rely on.",
                 "risk": "Required parent or sibling scope cannot be established from retained citations alone.",
                 "selected_for_future_scope_design": True, "source_verified": False},
            ],
            "preferred_approach": "PARENT_CONTEXT_BEFORE_CONTROLLER_CLUSTER",
            "decision_state": "PROVISIONAL_DESIGN_JUDGMENT",
            "automatic_scope_expansion": False,
            "projection_authorized": False,
        },
        "staged_source_coverage_strategy": [
            {"sequence": 1, "stage": "TRIGGER_FOUNDATION",
             "concepts": ["triggered_ability_form", "trigger_event_detection", "automatic_triggering"],
             "exact_future_source_allowlist": "NOT_DERIVED_REQUIRES_DEDICATED_DESIGN",
             "execution_supported": False, "evidence_status": PM_INPUT, "source_verified": False},
            {"sequence": 2, "stage": "STACK_AND_CONTROLLER_FOUNDATION",
             "concepts": ["trigger_stack_placement", "triggered_ability_controller_attribution", "trigger_ordering", "APNAP_ordering"],
             "exact_future_source_allowlist": "NOT_DERIVED_REQUIRES_DEDICATED_DESIGN",
             "execution_supported": False, "evidence_status": PM_INPUT, "source_verified": False},
            {"sequence": 3, "stage": "DELAYED_TRIGGER_CONTROLLER_CLUSTER",
             "concepts": ["appropriate_603.7_parent_context", "603.7d", "603.7e", "603.7f"],
             "exact_future_source_allowlist": "NOT_DERIVED_PENDING_PARENT_CONTEXT_REVIEW",
             "execution_supported": False, "evidence_status": PM_INPUT, "source_verified": False},
            {"sequence": 4, "stage": "SPECIALIZED_TRIGGER_FAMILIES_DEFERRED",
             "concepts": ["intervening_if", "zone_change_triggers", "state_triggers", "reflexive_triggers", "other_specialized_triggers"],
             "exact_future_source_allowlist": "DEFERRED",
             "execution_supported": False, "evidence_status": PM_INPUT, "source_verified": False},
        ],
        "general_special_relationship": {
            "general_procedure": {"reference": "603", "role": "GENERAL_TRIGGERED_PROCEDURE",
                                  "evidence_status": PM_INPUT, "source_verified": False},
            "mana_exception": {"retained_reference": "605.4a", "role": "TRIGGERED_MANA_EXCEPTION"},
            "relationship_kind": "GENERAL_TRIGGERED_PROCEDURE_PLUS_TRIGGERED_MANA_EXCEPTION",
            "relationship_design_authority": "SCOPING_JUDGMENT_USING_PM_OBSERVATIONS_AND_RETAINED_EXCEPTION",
            "applicability_condition": "QUALIFYING_TRIGGERED_MANA_ABILITY",
            "mana_exception_satisfies_general_trigger_semantics": False,
            "general_stack_statement_is_unconditional": False,
            "mana_exception_overwrites_general_rule": False,
            "new_direct_citation_created": False,
            "runtime_dispatch_created": False,
        },
        "deliberately_unresolved": ["603", "603.7", *DELAYED_CONTROLLER_FRONTIER,
            "general_trigger_event_semantics", "trigger_detection", "general_controller_semantics",
            "APNAP_ordering", "stack_placement", "priority", "delayed_trigger_parent_context",
            "specialized_trigger_families", "real_ability_and_effect_semantics"],
        "limitations": [
            "Retained citations establish shared dependency consumers, not the detailed bodies or minimum source scope of 603.",
            "Each trigger capability remains independently blocked; immediate mana behavior does not close ordinary triggered abilities.",
            "The parent-context preference is provisional and supplies no authorized or independently verified source allowlist.",
        ],
        "design_notes": notes,
    }


@dataclass(frozen=True)
class TriggeredAbilityDependencyDesign(DesignRecord):
    SCHEMA: ClassVar[str] = "gameplay-rules-triggered-ability-dependency-design-v1"
    ID_FIELD: ClassVar[str] = "triggered_procedure_design_id"
    BODY_FIELDS: ClassVar[frozenset[str]] = frozenset(_body([]))

    @staticmethod
    def _validate_body(body):
        _keys(body, TriggeredAbilityDependencyDesign.BODY_FIELDS)
        _strings(body["design_notes"], "design_notes")
        _exact(body, _body(body["design_notes"]), "triggered_procedure_design")


def build_triggered_design(*, design_notes=None):
    return TriggeredAbilityDependencyDesign.create(_body([] if design_notes is None else _json(design_notes)))
