"""Authored checkpoint knowledge; no legality decision or recovery execution."""
from gameplay_rules.projection.contracts import _freeze

SELECTED_REFERENCES = ("601.2e",)
RULE_CONTENT = _freeze({"601.2e": {
    "topic": "Casting proposal-legality checkpoint and conditional recovery frontier",
    "knowledge_kind": "BOUNDED_SHARED_PROPOSAL_LEGALITY_CHECKPOINT_CONTEXT",
    "paraphrase": "The game evaluates whether casting the proposed spell is permitted. "
        "An illegal proposal requires a return to the point preceding that spell's "
        "casting proposal, with recovery delegated to the unresolved numbered reference.",
    "direct_dependency_references": ["733"], "outgoing_numbered_ranges": [],
    "family_relationships": [{"reference": "601.2", "relationship_kind": "STRUCTURAL_RETAINED_PARENT_CONTEXT"}],
    "findings": {
        "checkpoint": {"actor_or_mechanism": "THE_GAME", "checked_object": "PROPOSED_SPELL",
            "question": "WHETHER_THE_PROPOSED_SPELL_CAN_LEGALLY_BE_CAST",
            "criteria_supplied": False, "actual_legality": "UNKNOWN_OR_UNSUPPORTED",
            "absence_of_detected_violation_proves_legality": False},
        "conditional_failure": {"condition": "PROPOSED_SPELL_IS_ILLEGAL",
            "source_prescribed_consequence": "GAME_RETURNS_TO_BEFORE_THAT_SPELLS_CASTING_WAS_PROPOSED",
            "return_point": "MOMENT_BEFORE_CASTING_OF_THAT_SPELL_WAS_PROPOSED",
            "literal_recovery_reference": "733", "recovery_mechanics": "UNRESOLVED",
            "recovery_execution": "BLOCKED", "state_restoration_supported": False,
            "pre_activation_recovery_context_interchangeable": False},
        "legal_outcome_branch": {"expressly_stated": False,
            "positive_literal_e_to_f_reference": False, "successful_continuation_guaranteed": False},
        "procedure_context": {"authority": "RETAINED_STRUCTURAL_CONTEXT_ONLY",
            "declarations": ["601.2c", "601.2d"], "later_cost_stage": "601.2f",
            "literal_outgoing_context_citations": [], "procedure_order_establishes_legality": False},
        "casting_provenance": {"subject": "SPELL", "activated_ability_relevance": "RETAINED_602_2B_CASTING_STAGE_RANGE_IMPORT",
            "unrestricted_activated_ability_legality_rule_inferred": False},
        "unknown_inputs": {"legality_criteria": "UNKNOWN_OR_UNSUPPORTED", "Card_or_effect_information": "UNKNOWN",
            "applicable_game_state": "UNKNOWN", "execution_machinery": "UNIMPLEMENTED"},
    },
    "limitations": [
        "Checkpoint existence and a source-prescribed conditional consequence are descriptive knowledge only.",
        "No criteria or actual-game legality decision follows from this unit or from absence of a detected violation.",
        "The literal recovery target remains unprojected and its mechanics unresolved; no rollback or restoration is supported.",
        "Structural procedure order is contextual inference and supplies neither a positive literal continuation citation nor a success guarantee.",
        "Casting and pre-activation recovery contexts remain distinct; activated relevance comes through the retained single import.",
    ],
    "semantic_closure": "OPEN", "execution_readiness": "BLOCKED", "execution_ready": False,
    "runtime_operations_implemented": [],
}})
GRAPH_NODES = _freeze([
    {"reference": "601.2e", "classification": "PROJECTED_SELECTED_RULE"},
    {"reference": "733", "classification": "UNRESOLVED_RULE", "status": "UNRESOLVED",
        "coverage_state": "UNPROJECTED"},
])
GRAPH_EDGES = _freeze([{"from_reference": "601.2e", "to_reference": "733", "relation": "DIRECT_NUMBERED_REFERENCE",
    "classification": "UNRESOLVED_RULE", "status": "UNRESOLVED"}])
UNSUPPORTED_DIMENSIONS = _freeze([
    "actual_game_legality_adjudication", "proposal_validation", "Card_or_Oracle_interpretation",
    "target_parsing_selection_or_allocation", "casting_and_activation_execution", "costs_and_payment",
    "mana_production", "stack_and_priority", "trigger_detection_placement_and_ordering",
    "casting_completion", "rollback_or_state_restoration", "real_gameplay_simulation",
])
