"""Authored start/completion knowledge for one non-executable casting batch."""
from gameplay_rules.projection.contracts import _freeze

SELECTED_REFERENCES = ("601.2a", "601.2i")
STAGE_REFERENCES = tuple("601.2" + letter for letter in "abcdefghi")
RULE_CONTENT = _freeze({
    "601.2a": {
        "topic": "Casting proposal start, stack entry and initial effect timing",
        "knowledge_kind": "BOUNDED_CASTING_START_CONTEXT",
        "paraphrase": "A casting proposal begins with the player relocating the card or card copy "
            "to the top of the stack. Its associated characteristics and proposing-player control "
            "are described, together with stack-entry timing for specified characteristic changes "
            "and ability-granting effects. Residence ends through resolution, countering or another "
            "rule or effect moving the spell.",
        "direct_dependency_references": ["611.2f", "610.5"],
        "outgoing_numbered_ranges": [],
        "family_relationships": [{"reference": "601.2", "relationship_kind": "RETAINED_PARENT_EXPLICIT_A_TO_D_RANGE_MEMBER"}],
        "findings": {
            "proposal_start": {"subject": "CARD_OR_COPY_OF_CARD", "actor": "PROPOSING_PLAYER",
                "movement": "CURRENT_LOCATION_TO_TOP_OF_STACK", "associated_characteristics": True,
                "controller": "PROPOSING_PLAYER", "casting_complete_at_start": False},
            "start_effect_context": {
                "continuous_characteristic_changes": "BEGIN_AT_STACK_ENTRY_AS_CASTING_STARTS",
                "continuous_effect_reference": "611.2f",
                "one_shot_ability_gain": "APPLIES_AT_STACK_ENTRY_AS_CASTING_STARTS",
                "one_shot_effect_reference": "610.5", "effect_semantics": "UNRESOLVED",
                "effect_application_implemented": False},
            "stack_residence": {"ends_on": ["RESOLUTION", "COUNTERING", "OTHER_RULE_OR_EFFECT_RELOCATION"],
                "stack_execution_implemented": False},
            "activated_applicability": {"included_in_literal_602_2B_IMPORT": False,
                "reason": "THE_SINGLE_LITERAL_IMPORT_STARTS_AT_B",
                "new_literal_activation_to_a_reference": False},
            "unknown_inputs": ["START_PERMISSION_AND_LEGAL_COMPLETION_CRITERIA", "CARD_OR_EFFECT_INFORMATION",
                "APPLICABLE_GAME_STATE", "611_2F_EFFECT_SEMANTICS", "610_5_EFFECT_SEMANTICS"],
        },
        "limitations": [
            "This start-stage description does not establish that a particular proposal may begin or finish legally.",
            "Both literal effect references remain unprojected; timing context supplies no effect-application machinery.",
            "Stack entry during a proposal is distinct from the later point at which the spell becomes cast.",
            "The activated-ability procedure's literal b-to-i import excludes this spell-start unit.",
        ],
        "semantic_closure": "OPEN", "execution_readiness": "BLOCKED", "execution_ready": False,
        "runtime_operations_implemented": [],
    },
    "601.2i": {
        "topic": "Conditional casting completion, cast-time changes, trigger consequence and priority context",
        "knowledge_kind": "BOUNDED_CASTING_COMPLETION_CONTEXT",
        "paraphrase": "Completion of the preceding a-through-h stages precedes application of "
            "cast-time characteristic modifications and the spell becoming cast. Cast or stack-entry "
            "trigger consequences occur at this completion point. Priority returns to the controller "
            "only under the stated condition that the controller held it before casting.",
        "direct_dependency_references": [],
        "outgoing_numbered_ranges": [{"start": "601.2a", "end": "601.2h",
            "members": list(STAGE_REFERENCES[:-1])}],
        "family_relationships": [{"reference": "601.2", "relationship_kind": "STRUCTURAL_RETAINED_PARENT_CONTEXT"}],
        "findings": {
            "completion": {"condition": "PRECEDING_A_THROUGH_H_STAGES_COMPLETED",
                "characteristic_changes": "CAST_TIME_MODIFICATIONS_APPLY_BEFORE_SPELL_BECOMES_CAST",
                "then": "SPELL_BECOMES_CAST", "stage_coverage_proves_condition_satisfied": False,
                "effect_application_implemented": False},
            "trigger_consequence": {"events": ["SPELL_CAST", "SPELL_PUT_ON_STACK"],
                "trigger_time_context": "THIS_COMPLETION_POINT", "detection_implemented": False,
                "ordering_implemented": False, "placement_implemented": False},
            "priority_context": {"recipient": "SPELL_CONTROLLER",
                "condition": "CONTROLLER_HAD_PRIORITY_BEFORE_CASTING",
                "unconditional_priority_return": False, "priority_handling_implemented": False},
            "activated_applicability": {"included_in_literal_602_2B_IMPORT": True,
                "import_relationship": "SINGLE_B_TO_I_RANGE",
                "own_a_to_h_range_creates_activation_to_a_citation": False,
                "spell_specific_facts_apply_unchanged_to_abilities": "NOT_ESTABLISHED"},
            "unknown_inputs": ["ACTUAL_COMPLETION_OF_PRECEDING_STAGES", "CAST_TIME_CHARACTERISTIC_EFFECTS",
                "APPLICABLE_TRIGGER_ABILITIES", "PRIOR_PRIORITY_STATE", "GENERAL_PRIORITY_SEMANTICS"],
        },
        "limitations": [
            "Complete source coverage of the prerequisite range does not prove a proposed action completed those stages.",
            "Trigger consequence supplies no detection, ordering, placement or shared-triggered subsystem implementation.",
            "Priority is conditional on the controller having priority before casting; no unconditional return is inferred.",
            "The a-through-h range does not add a literal activated-ability citation to a or transfer all spell facts unchanged.",
            "Neither this source nor the combined stage map supplies casting, stack, effects or priority execution.",
        ],
        "semantic_closure": "OPEN", "execution_readiness": "BLOCKED", "execution_ready": False,
        "runtime_operations_implemented": [],
    },
})
GRAPH_NODES = _freeze([
    {"reference": "601.2a", "classification": "PROJECTED_SELECTED_RULE"},
    {"reference": "601.2i", "classification": "PROJECTED_SELECTED_RULE"},
    *[{"reference": ref, "classification": "UNRESOLVED_RULE", "status": "UNRESOLVED",
        "coverage_state": "UNPROJECTED"} for ref in ("611.2f", "610.5")],
])
GRAPH_EDGES = _freeze([
    *[{"from_reference": "601.2a", "to_reference": ref, "relation": "DIRECT_NUMBERED_REFERENCE",
        "classification": "UNRESOLVED_RULE", "status": "UNRESOLVED"} for ref in ("611.2f", "610.5")],
    {"from_reference": "601.2i", "relation": "EXPLICIT_NUMBERED_RANGE",
        "range_start": "601.2a", "range_end": "601.2h", "members": list(STAGE_REFERENCES[:-1]),
        "status": "SOURCE_MEMBER_COVERAGE_COMPLETE", "semantic_closure": "OPEN"},
])
UNSUPPORTED_DIMENSIONS = _freeze([
    "actual_game_legality_adjudication", "proposal_validation", "Card_or_Oracle_interpretation",
    "target_parsing_selection_or_allocation", "casting_and_activation_execution", "costs_and_payment",
    "mana_production", "effect_application", "stack_and_priority", "trigger_detection_placement_and_ordering",
    "rollback_or_state_restoration", "real_gameplay_simulation",
])
