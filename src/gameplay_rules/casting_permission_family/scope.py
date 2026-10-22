"""Authored conditional knowledge from the freshly verified closed 601.3 family."""
from gameplay_rules.projection.contracts import _freeze

SELECTED_REFERENCES = ("601.3", "601.3a", "601.3b", "601.3c", "601.3d", "601.3e", "601.3f")

# These descriptions were authored after the complete marker-derived selection
# and source coherence preflight, not supplied as a candidate authorization.
_FINDINGS = {
    "601.3": ("Permission and prohibition at proposal entry",
        "Beginning a casting proposal requires an applicable rule or effect allowing the player to cast the spell, together with the absence of an applicable rule or effect prohibiting that player from casting it.",
        {"entry_requirements": ["RULE_OR_EFFECT_ALLOWS_PLAYER_TO_CAST", "NO_RULE_OR_EFFECT_PROHIBITS_PLAYER_FROM_CASTING"],
         "quantification": "ONLY_IF_NECESSARY_REQUIREMENTS", "sufficiency_for_completed_legal_cast": False},
        ["ALLOWING_RULE_OR_EFFECT", "ALL_APPLICABLE_PROHIBITIONS", "PLAYER_AND_PROPOSED_OBJECT", "RELEVANT_GAME_STATE"]),
    "601.3a": ("Proposal choices affecting a quality-based prohibition",
        "For an effect that prohibits casting spells with specified qualities, the player may consider proposal choices that could change those qualities. If a choice could make that effect cease to prohibit this casting, the player may begin while disregarding that effect.",
        {"applies_to": "QUALITY_BASED_PROHIBITING_EFFECT", "lookahead": "POSSIBLE_PROPOSAL_CHOICES_CHANGING_QUALITIES",
         "condition": "SOME_CHOICE_COULD_REMOVE_THAT_EFFECTS_PROHIBITION", "entry_consequence": "MAY_BEGIN_IGNORING_THAT_EFFECT",
         "ignores_other_prohibitions": False, "chosen_proposal_guaranteed_legal": False},
        ["EXACT_PROHIBITING_EFFECT", "AVAILABLE_PROPOSAL_CHOICES", "CHOICE_EFFECT_ON_QUALITIES", "OTHER_PERMISSION_AND_RESTRICTIONS"]),
    "601.3b": ("Proposal choices enabling a quality-conditioned timing allowance",
        "An effect permitting spells with specified qualities to be cast as though they had flash can support beginning when a proposal choice could change the spell's qualities so that the effect applies.",
        {"applies_to": "QUALITY_CONDITIONED_AS_THOUGH_FLASH_EFFECT", "lookahead": "POSSIBLE_PROPOSAL_CHOICES_CHANGING_QUALITIES",
         "condition": "SOME_CHOICE_COULD_MAKE_THAT_EFFECT_APPLY", "entry_consequence": "MAY_BEGIN_AS_THOUGH_FLASH",
         "general_timing_semantics_resolved": False},
        ["EXACT_TIMING_ALLOWANCE", "AVAILABLE_PROPOSAL_CHOICES", "RESULTING_QUALITIES", "OTHER_PERMISSION_AND_RESTRICTIONS"]),
    "601.3c": ("Cost-conditioned as-though-flash entry",
        "When an effect supplies as-though-flash casting conditional on paying an alternative or additional cost, it permits beginning the proposal as though the spell had flash. Beginning does not establish payment or completion.",
        {"applies_to": "AS_THOUGH_FLASH_EFFECT_CONDITIONAL_ON_ALTERNATIVE_OR_ADDITIONAL_COST_PAYMENT",
         "entry_consequence": "MAY_BEGIN_AS_THOUGH_FLASH", "payment_already_completed_required_by_this_entry_text": False,
         "cost_waived": False, "payment_established": False},
        ["EXACT_COST_CONDITIONED_EFFECT", "APPLICABLE_ALTERNATIVE_OR_ADDITIONAL_COST", "PAYMENT_AND_RESOURCES", "OTHER_PERMISSION_AND_RESTRICTIONS"]),
    "601.3d": ("Conditions for a spell's own conditional flash",
        "For a spell whose flash depends on specified conditions, the controller may begin as though it had flash when those conditions are satisfied.",
        {"applies_to": "SPELL_WOULD_HAVE_FLASH_CONDITIONAL_ON_FACTS", "condition": "SPECIFIED_CONDITIONS_ARE_MET",
         "entry_consequence": "CONTROLLER_MAY_BEGIN_AS_THOUGH_FLASH", "unmet_conditions_waived": False},
        ["CONDITIONAL_FLASH_TEXT", "CONDITION_SATISFACTION", "CONTROLLER", "OTHER_PERMISSION_AND_RESTRICTIONS"]),
    "601.3e": ("Characteristics used for casting-legality determination",
        "Where a rule or effect specifies alternative characteristics or a subset of characteristics for determining whether a card or its copy may be cast, those characteristics replace the object's characteristics for that determination. Continuous effects that would apply with those characteristics are also considered.",
        {"trigger": "RULE_OR_EFFECT_DESIGNATES_ALTERNATIVE_OR_SUBSET_CHARACTERISTICS_FOR_CASTING_LEGALITY",
         "characteristic_use": "REPLACEMENT_FOR_THIS_DETERMINATION", "continuous_effects": "CONSIDER_EFFECTS_APPLICABLE_WITH_THOSE_CHARACTERISTICS",
         "global_characteristic_rewrite": False, "card_interpretation_implemented": False},
        ["DESIGNATING_RULE_OR_EFFECT", "ALTERNATIVE_OR_SUBSET_CHARACTERISTICS", "APPLICABLE_CONTINUOUS_EFFECTS", "OBJECT_AND_STATE_EVIDENCE"]),
    "601.3f": ("Access condition for quality-limited face-down exile casting",
        "For effects allowing quality-limited casting from face-down cards in exile, beginning such a casting requires that the player be able to look at the face-down card. That access alone does not prove that the card qualifies or that casting is otherwise legal.",
        {"applies_to": "QUALITY_LIMITED_CASTING_EFFECT_AMONG_FACE_DOWN_EXILE_CARDS", "necessary_condition": "PLAYER_CAN_LOOK_AT_FACE_DOWN_CARD",
         "look_permission_granted_by_this_rule": False, "access_alone_proves_casting_permission": False},
        ["EXACT_EXILE_CASTING_EFFECT", "CARD_FACE_DOWN_AND_EXILED", "PLAYER_LOOK_ACCESS", "CARD_QUALITIES", "OTHER_PERMISSION_AND_RESTRICTIONS"]),
}
RULE_CONTENT = _freeze({ref: {
    "topic": topic, "knowledge_kind": "BOUNDED_CASTING_PERMISSION_CONTEXT", "paraphrase": prose,
    "direct_dependency_references": [], "outgoing_numbered_ranges": [],
    "family_relationships": ([] if ref == "601.3" else [{"reference": "601.3", "relationship_kind": "STRUCTURAL_PARENT_SUBRULE"}]),
    "findings": facts, "unknown_inputs": unknown,
    "limitations": ["Conditional authored knowledge supplies no particular spell legality adjudication.",
        "Full family source coverage does not establish semantic closure, procedure completion or execution.",
        "Activated-ability applicability is not inferred from the retained b-to-i casting-stage import."],
    "semantic_closure": "OPEN", "execution_readiness": "BLOCKED", "execution_ready": False,
    "runtime_operations_implemented": [],
} for ref, (topic, prose, facts, unknown) in _FINDINGS.items()})
GRAPH_NODES = _freeze([{"reference": ref, "classification": "PROJECTED_SELECTED_RULE"} for ref in SELECTED_REFERENCES])
GRAPH_EDGES = _freeze([{"from_reference": ref, "to_reference": "601.3",
    "relation": "STRUCTURAL_PARENT_SUBRULE", "literal_citation": False} for ref in SELECTED_REFERENCES[1:]])
UNSUPPORTED_DIMENSIONS = _freeze([
    "actual_permission_or_legality_evaluation", "Card_or_Oracle_interpretation", "flash_and_effect_semantics",
    "casting_or_activation_execution", "target_selection_or_allocation", "cost_payment_or_mana_production",
    "trigger_stack_and_priority_execution", "rollback_or_recovery", "gameplay_simulation",
])
