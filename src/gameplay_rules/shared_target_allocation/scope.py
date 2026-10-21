"""Authored conditional declaration knowledge; no arithmetic or allocation engine."""
from gameplay_rules.projection.contracts import _freeze

SELECTED_REFERENCES = ("601.2d",)
RULE_CONTENT = _freeze({"601.2d": {
    "topic": "Casting-stage conditional target allocation declaration",
    "knowledge_kind": "BOUNDED_SHARED_TARGET_ALLOCATION_CONTEXT",
    "paraphrase": "When a spell requires its casting player to apportion an effect among "
        "at least one target, that player declares the apportionment. Every target within "
        "that required distribution receives a minimum of one unit of the distributed thing.",
    "direct_dependency_references": [],
    "outgoing_numbered_ranges": [],
    "family_relationships": [{"reference": "601.2", "relationship_kind": "STRUCTURAL_RETAINED_PARENT_CONTEXT"}],
    "findings": {
        "casting_provenance": {"actor": "CASTING_PLAYER", "subject": "SPELL",
            "activated_ability_relevance": "RETAINED_602_2B_CASTING_STAGE_RANGE_IMPORT",
            "procedures_interchangeable": False},
        "conditional_allocation_declaration": {
            "condition": "SPELL_REQUIRES_PLAYER_TO_DIVIDE_OR_DISTRIBUTE_AN_EFFECT_AMONG_ONE_OR_MORE_TARGETS",
            "distribution_operations": ["DIVIDE", "DISTRIBUTE"],
            "distributed_subject": "AN_EFFECT",
            "illustrative_effect_kinds": ["DAMAGE", "COUNTERS"],
            "illustrations_exhaust_effect_kinds": False,
            "recipient_scope": "THE_ONE_OR_MORE_TARGETS_OF_THAT_REQUIRED_DISTRIBUTION",
            "minimum_recipient_count": 1,
            "declaration": "PLAYER_ANNOUNCES_THE_DIVISION",
            "each_relevant_target_minimum": 1,
            "minimum_unit": "WHATEVER_IS_BEING_DIVIDED",
            "minimum_applies_only_within_required_distribution": True,
            "minimum_applies_to_all_targets_of_all_spells_or_abilities": False,
            "recognition_implemented": False,
            "arithmetic_or_allocation_solver_implemented": False},
        "recipient_declaration_distinction": {
            "retained_recipient_declaration": "601.2c",
            "relationship": "STRUCTURAL_AND_SEMANTIC_CONTEXT_NOT_LITERAL_CITATION",
            "recipient_declaration_is_allocation_declaration": False,
            "recipient_selection_implemented": False},
        "unknown_inputs": {"actual_targets": "UNKNOWN", "actual_quantities": "UNKNOWN",
            "Card_or_effect_semantics": "UNKNOWN", "applicable_state": "UNKNOWN",
            "whether_a_particular_spell_requires_distribution": "UNKNOWN"},
    },
    "limitations": [
        "The minimum applies only to each target of the conditionally required distribution, without a rule for every spell or ability target.",
        "Damage and counters illustrate effect kinds; no damage or counter application is implemented.",
        "Recipient declaration comes from retained 601.2c context; no literal cross-citation is invented and c is not re-projected.",
        "Actual targets, quantities, Card/effect semantics and applicable state are not supplied by this knowledge.",
        "Casting provenance is preserved; activation relevance comes only through the retained 602.2b import.",
        "No requirement recognition, target choice, compatibility solver, allocation arithmetic, legality decision, resolution or execution is supplied.",
    ],
    "semantic_closure": "OPEN", "execution_readiness": "BLOCKED", "execution_ready": False,
    "runtime_operations_implemented": [],
}})
GRAPH_NODES = _freeze([{"reference": "601.2d", "classification": "PROJECTED_SELECTED_RULE"}])
GRAPH_EDGES = _freeze([])
UNSUPPORTED_DIMENSIONS = _freeze([
    "card_and_effect_interpretation", "target_requirement_recognition", "legal_target_generation",
    "actual_target_choice", "target_legality_adjudication", "mandatory_choice_compatibility_solver",
    "arithmetic_or_allocation_solving", "damage_or_counter_application", "effect_resolution",
    "general_casting_and_activation_execution", "costs_and_payment", "mana_production",
    "stack_and_priority", "trigger_detection_placement_and_ordering", "casting_completion",
    "rollback", "real_gameplay_simulation",
])
