"""Project-authored descriptive knowledge from the complete selected c unit."""
from gameplay_rules.projection.contracts import _freeze

SELECTED_REFERENCES = ("601.2c",)
RULE_CONTENT = _freeze({"601.2c": {
    "topic": "Casting-stage target declaration",
    "knowledge_kind": "BOUNDED_SHARED_TARGET_DECLARATION_CONTEXT",
    "paraphrase": "The casting player declares appropriate object or player recipients for the spell's "
        "required targets, accounting for earlier choices. Variable counts are declared before recipients "
        "and remain fixed once determined. Reuse depends on distinct targeting instances. Mandatory-target "
        "effects are satisfied as far as compatible with all prohibitions. Selected recipients become "
        "targets, with related trigger occurrence and deferred placement described separately.",
    "direct_dependency_references": [],
    "outgoing_numbered_ranges": [],
    "family_relationships": [{"reference": "601.2", "relationship_kind": "STRUCTURAL_RETAINED_PARENT_CONTEXT"}],
    "findings": {
        "casting_provenance": {"actor": "CASTING_PLAYER", "subject": "SPELL",
            "activated_ability_relevance": "RETAINED_602_2B_CASTING_STAGE_RANGE_IMPORT",
            "procedures_interchangeable": False},
        "required_recipient_declaration": {"recipients": ["OBJECT", "PLAYER"],
            "condition": "EACH_TARGET_REQUIRED_BY_THE_SPELL",
            "recipient_constraint": "APPROPRIATE_TO_THE_TARGET_REQUIREMENT"},
        "earlier_choice_conditions": {
            "some_target_requirements": {"possible_conditions": ["ALTERNATIVE_COST_CHOSEN",
                "ADDITIONAL_COST_CHOSEN", "PARTICULAR_MODE_CHOSEN"],
                "condition_absent": "CAST_AS_THOUGH_THOSE_TARGETS_WERE_NOT_REQUIRED"},
            "alternative_target_requirements": {"possible_conditions": ["ALTERNATIVE_COST_CHOSEN",
                "ADDITIONAL_COST_CHOSEN"]},
            "recognition_implemented": False},
        "target_count": {"variable_count": "ANNOUNCE_COUNT_BEFORE_IDENTIFYING_RECIPIENTS",
            "spell_text_can_define_count": True,
            "determined_count": "FIXED_EVEN_IF_DETERMINING_INFORMATION_CHANGES",
            "count_algorithm_implemented": False},
        "recipient_reuse": {"instance_basis": "OCCURRENCE_OF_THE_WORD_TARGET_IN_SPELL_TEXT",
            "within_one_targeting_instance": "NO_REPEATED_RECIPIENT",
            "across_distinct_targeting_instances": "SAME_RECIPIENT_MAY_BE_CHOSEN_ONCE_PER_INSTANCE",
            "cross_instance_condition": "RECIPIENT_MEETS_EACH_INSTANCE_CRITERIA",
            "owned_example_role": "CONFIRMS_DISTINCT_INSTANCE_REUSE_AND_SAME_INSTANCE_PROHIBITION",
            "owned_example_is_separate_source_unit": False},
        "mandatory_and_prohibited_choices": {
            "objective": "COMPLY_WITH_MAXIMUM_POSSIBLE_NUMBER_OF_MANDATORY_TARGET_EFFECTS",
            "constraint": "VIOLATE_NO_RULE_OR_EFFECT_PROHIBITING_THAT_TARGET_CHOICE",
            "compatibility_solver_implemented": False},
        "becoming_targeted": {"recipients": "CHOSEN_OBJECTS_AND_OR_PLAYERS",
            "consequence": "EACH_BECOMES_A_TARGET_OF_THE_SPELL",
            "related_trigger_condition": "AN_ABILITY_TRIGGERS_WHEN_A_CHOSEN_RECIPIENT_BECOMES_TARGET_OF_A_SPELL",
            "related_trigger_occurrence": "TRIGGERS_FOR_BECOMING_A_SPELL_TARGET_OCCUR_AT_THIS_STAGE",
            "trigger_placement": "DEFERRED_UNTIL_THE_SPELL_FINISHES_BEING_CAST",
            "trigger_detection_implemented": False, "trigger_placement_implemented": False,
            "universal_activated_mana_trigger_or_priority_rule": False},
        "three_target_concepts": {"concepts": ["REQUIRING_TARGETS", "ACTUAL_CHOSEN_TARGET_COUNT", "TARGETED_STATUS"],
            "retained_115_6_context": "A_REQUIREMENT_CAN_PERSIST_WITH_ZERO_CHOSEN_TARGETS_WHILE_TARGETED_STATUS_REQUIRES_ONE_OR_MORE",
            "zero_chosen_proves_no_requirement": False,
            "zero_chosen_establishes_mana_ability_eligibility": False,
            "relationship_to_115_6": "RETAINED_SEMANTIC_CONTEXT_NOT_LITERAL_CITATION"},
    },
    "limitations": [
        "The complete owned example belongs to this one source unit and is represented only through authored findings.",
        "Target requirements are assumed; no Card/effect parser, recognizer, target generator, choice algorithm or legality adjudication is supplied.",
        "The casting evidence and retained activation import have distinct provenance; no blanket vocabulary substitution follows.",
        "Trigger consequences are descriptive; detection, placement, ordering, casting completion, stack and priority remain unimplemented.",
        "Distribution, compatibility solving, costs, payment, mana production, rollback and gameplay execution remain unsupported.",
    ],
    "semantic_closure": "OPEN", "execution_readiness": "BLOCKED", "execution_ready": False,
    "runtime_operations_implemented": [],
}})
GRAPH_NODES = _freeze([{"reference": "601.2c", "classification": "PROJECTED_SELECTED_RULE"}])
GRAPH_EDGES = _freeze([])
UNSUPPORTED_DIMENSIONS = _freeze([
    "card_and_effect_interpretation", "target_requirement_recognition", "legal_target_generation",
    "actual_target_choice", "target_legality_adjudication", "mandatory_choice_compatibility_solver",
    "distribution_allocation", "general_casting_and_activation_execution", "costs_and_payment",
    "mana_production", "stack_and_priority", "trigger_detection_placement_and_ordering",
    "casting_completion", "rollback", "real_gameplay_simulation",
])
