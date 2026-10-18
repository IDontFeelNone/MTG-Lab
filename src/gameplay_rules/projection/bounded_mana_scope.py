"""Fixed authored knowledge for the thirteen authorized mana-ability units.

Numbered citations describe source dependencies; selected parent/child links
describe family structure separately.  None of these records classifies a real
ability or performs activation, resolution, controller, mana, or payment work.
"""
from .contracts import _freeze


SELECTED_REFERENCES = (
    "605.1", "605.1a", "605.1b", "605.2", "605.3", "605.3a", "605.3b",
    "605.3c", "605.4", "605.4a", "605.5", "605.5a", "605.5b",
)
BOUNDED_MANA_SELECTED_REFERENCES = SELECTED_REFERENCES
UNRESOLVED_RULE_REFERENCES = ("115.6", "606", "602.2", "405.6c", "603")

_CHILDREN = {
    "605.1": ("605.1a", "605.1b"),
    "605.3": ("605.3a", "605.3b", "605.3c"),
    "605.4": ("605.4a",),
    "605.5": ("605.5a", "605.5b"),
}
_PARENTS = {child: parent for parent, children in _CHILDREN.items() for child in children}


def _projected(reference, relation="DIRECT_NUMBERED_REFERENCE"):
    return {
        "reference": reference, "classification": "PROJECTED_RULE",
        "status": "PROJECTED_IN_THIS_MILESTONE", "relation": relation,
    }


def _unresolved(reference):
    return {
        "reference": reference, "classification": "UNRESOLVED_RULE",
        "status": "UNRESOLVED", "coverage_state": "UNPROJECTED",
        "relation": "DIRECT_NUMBERED_REFERENCE",
    }


def _subsystem(reference):
    return {
        "reference": reference, "classification": "UNRESOLVED_SUBSYSTEM",
        "status": "UNSUPPORTED",
    }


def _primitive(reference):
    return {
        "reference": reference, "classification": "FUTURE_SEMANTIC_PRIMITIVE",
        "status": "UNIMPLEMENTED",
    }


def _family(reference):
    relationships = []
    if reference in _PARENTS:
        relationships.append(_projected(_PARENTS[reference], "STRUCTURAL_SELECTED_PARENT"))
    relationships.extend(_projected(child, "STRUCTURAL_SELECTED_CHILD")
                         for child in _CHILDREN.get(reference, ()))
    return relationships


def _rule(reference, topic, paraphrase, category, tags, direct, subsystems,
          primitives, distinctions, limitations):
    return {
        "topic": topic, "paraphrase": paraphrase, "semantic_category": category,
        "domain_classification": "CORE_GAME_SUBSYSTEM", "concept_tags": tags,
        "direct_dependency_references": direct,
        "dependencies": [_projected(ref) for ref in direct if ref in SELECTED_REFERENCES],
        "unresolved_dependencies": [_unresolved(ref) for ref in direct
                                    if ref in UNRESOLVED_RULE_REFERENCES],
        "family_relationships": _family(reference),
        "subsystem_boundaries": [_subsystem(ref) for ref in subsystems],
        "required_future_semantic_primitives": [_primitive(ref) for ref in primitives],
        "semantic_distinctions": dict(
            distinctions, descriptive_only=True, runtime_operations_implemented=[],
            classification_execution_implemented=False,
            source_coverage_implies_semantic_closure=False,
            source_coverage_implies_execution=False,
            fictional_mana_satisfies_real_605_execution=False,
        ),
        "exception_subrule_boundaries": [], "limitations": limitations,
        "coverage_state": "BOUNDED_MANA_ABILITY_SOURCE_PROJECTED",
        "review_state": "PROJECTED_FOR_REVIEW", "semantic_closure_state": "OPEN",
        "execution_readiness": "BLOCKED", "execution_ready": False,
    }


RULE_CONTENT = _freeze({
    "605.1": _rule(
        "605.1", "Two criteria families determine mana-ability membership",
        "Mana abilities form a rules-defined subset of activated and triggered abilities. "
        "Membership requires the applicable complete criteria set, while other generated effects "
        "and additional timing restrictions do not by themselves disqualify a qualifying ability.",
        "MANA_ABILITY_CLASSIFICATION_CONTEXT",
        ["mana_ability", "activated_ability", "triggered_ability", "criteria_family",
         "additional_effects", "timing_restrictions", "classification_not_execution"],
        [],
        ["ability_kind_semantics", "real_card_and_effect_semantics", "mana_ability_classification"],
        ["ability_kind_evidence", "mana_ability_criteria_evidence"],
        {"classification_basis": "ONE_COMPLETE_RULE_DEFINED_CRITERIA_SET",
         "criteria_family_references": ["605.1a", "605.1b"],
         "produces_mana_alone_is_sufficient": False,
         "other_generated_effects_alone_remove_classification": False,
         "timing_restrictions_alone_remove_classification": False,
         "classification_implies_current_output": False,
         "classification_implies_execution": False},
        ["The selected children supply distinct activated and triggered criteria; their structural links are not invented direct citations.",
         "No real ability-kind detection or mana-ability classifier is supplied."]),
    "605.1a": _rule(
        "605.1a", "Activated-mana criteria and the replacement-effect distinction",
        "An activated ability qualifies only when it has no target, could supply mana on "
        "resolution, is not a loyalty ability, and neither its payment requirements nor its "
        "effect transfers a card into or out of a library. Evaluate these criteria with "
        "self-replacement effects considered and other applicable replacement effects disregarded.",
        "ACTIVATED_MANA_ABILITY_CLASSIFICATION",
        ["activated_mana_ability", "no_target", "could_add_mana", "loyalty_exclusion",
         "library_movement_exclusion", "self_replacement", "replacement_effect_distinction"],
        ["115.6", "606"],
        ["ability_kind_semantics", "target_knowledge", "loyalty_ability_knowledge",
         "library_movement_semantics", "replacement_effect_semantics", "self_replacement_semantics",
         "potential_mana_output_semantics", "real_card_and_effect_semantics"],
        ["activated_ability_kind_evidence", "target_requirement_evidence", "potential_mana_output_evidence",
         "loyalty_classification_evidence", "cost_library_movement_evidence",
         "effect_library_movement_evidence", "self_replacement_classification_evidence"],
        {"ability_kind": "ACTIVATED", "all_criteria_required": True,
         "requires_target": False, "could_add_mana_to_player_pool_on_resolution": True,
         "is_loyalty_ability": False, "cost_moves_card_to_or_from_library": False,
         "effect_moves_card_to_or_from_library": False,
         "applicable_replacement_effects_considered": "SELF_REPLACEMENT_ONLY",
         "other_applicable_replacement_effects_ignored_for_classification": True,
         "classification_distinct_from_current_mana_output": True,
         "classification_distinct_from_activation_eligibility": True},
        ["Both numbered external criteria dependencies remain unprojected.",
         "The criteria are descriptive evidence; no targeting, loyalty, library, replacement, or output evaluation occurs."]),
    "605.1b": _rule(
        "605.1b", "Triggered-mana criteria require a qualifying trigger relationship",
        "A triggered ability qualifies when it has no target, could supply mana on resolution, "
        "and its trigger is tied to activating or resolving an activated mana ability, or to "
        "mana entering a player's pool. The activated-mana criterion is supplied by the selected "
        "activated classification rule.",
        "TRIGGERED_MANA_ABILITY_CLASSIFICATION",
        ["triggered_mana_ability", "no_target", "could_add_mana", "trigger_source_category",
         "activated_mana_activation", "activated_mana_resolution", "mana_added"],
        ["115.6", "605.1a"],
        ["ability_kind_semantics", "target_knowledge", "trigger_relationship_semantics",
         "activated_mana_ability_classification", "potential_mana_output_semantics",
         "real_card_and_effect_semantics"],
        ["triggered_ability_kind_evidence", "target_requirement_evidence",
         "mana_trigger_relationship_evidence", "potential_mana_output_evidence"],
        {"ability_kind": "TRIGGERED", "all_criteria_required": True,
         "requires_target": False, "could_add_mana_to_player_pool_on_resolution": True,
         "qualifying_trigger_relationships": ["ACTIVATED_MANA_ABILITY_ACTIVATION",
                                               "ACTIVATED_MANA_ABILITY_RESOLUTION", "MANA_ADDED_TO_POOL"],
         "activated_mana_classification_reference": "605.1a",
         "activated_and_triggered_classification_are_distinct": True,
         "trigger_detection_implemented": False},
        ["The selected activated criterion is represented, while the targeting dependency remains unresolved.",
         "No event detection, trigger matching, triggered ability execution, or mana output calculation occurs."]),
    "605.2": _rule(
        "605.2", "Classification persists independently of present mana output",
        "A qualifying mana ability keeps that classification when the current state prevents "
        "it from generating mana. Membership in the rule category is separate from present "
        "activation eligibility and from the output a particular use could produce.",
        "MANA_ABILITY_CLASSIFICATION_PERSISTENCE",
        ["classification_persistence", "current_game_state", "current_output",
         "activation_eligibility", "classification_not_production"],
        [],
        ["mana_ability_classification", "current_activation_eligibility", "mana_production_semantics",
         "real_card_and_effect_semantics"],
        ["persistent_mana_classification_evidence", "current_activation_eligibility_evidence",
         "current_mana_output_evidence"],
        {"classification": "MANA_ABILITY", "current_activation_eligibility": "SEPARATE_UNKNOWN_DIMENSION",
         "current_productive_output": "SEPARATE_UNKNOWN_DIMENSION",
         "inability_to_produce_mana_alone_removes_classification": False,
         "classification_implies_current_output": False,
         "classification_implies_current_activation_eligibility": False,
         "example_content_retained": False},
        ["Current output and activation eligibility are distinctions, not evaluated results.",
         "The source example contributes only to the verified block span and digest; no example text is retained."]),
    "605.3": _rule(
        "605.3", "Activated-mana procedure retains a general activation dependency",
        "Using an activated mana ability depends on the ordinary activated-ability procedure, "
        "with the selected descendants describing special opportunities, immediate behavior, "
        "and a restriction on repeating the same activation.",
        "ACTIVATED_MANA_ABILITY_PROCEDURE_CONTEXT",
        ["activated_mana_ability", "ordinary_activation_dependency", "special_exceptions"],
        ["602.2"],
        ["general_activated_ability_procedure", "real_ability_activation", "priority", "cost_payment"],
        ["activated_ability_procedure_evidence", "mana_activation_exception_evidence"],
        {"ordinary_activation_dependency": "602.2",
         "special_exception_references": ["605.3a", "605.3b", "605.3c"],
         "general_activated_abilities_represented": False,
         "selected_exceptions_satisfy_general_activation": False},
        ["The ordinary activation procedure remains an unresolved large subsystem.",
         "Selected exception coverage does not supply general activation or payment semantics."]),
    "605.3a": _rule(
        "605.3a", "Special opportunities to activate a mana ability",
        "Activated mana abilities have opportunities tied to priority, spell or ability "
        "procedures requiring mana, and a rule's or effect's request for mana payment. "
        "A qualifying request may arise during an ongoing spell or ability procedure, "
        "including its resolution.",
        "ACTIVATED_MANA_ABILITY_ACTIVATION_WINDOW",
        ["priority_opportunity", "spell_payment_opportunity", "ability_payment_opportunity",
         "rule_requested_payment", "effect_requested_payment", "ongoing_procedure"],
        [],
        ["priority", "spell_casting", "real_ability_activation", "rule_execution", "effect_execution",
         "cost_payment", "spell_and_ability_resolution"],
        ["mana_activation_opportunity_evidence", "mana_payment_request_context",
         "ongoing_procedure_context_evidence"],
        {"activation_opportunity_categories": ["ORDINARY_PRIORITY", "SPELL_CASTING_MANA_PAYMENT",
                                              "ABILITY_ACTIVATION_MANA_PAYMENT", "RULE_REQUESTED_MANA_PAYMENT",
                                              "EFFECT_REQUESTED_MANA_PAYMENT"],
         "request_may_occur_during": ["SPELL_CASTING", "SPELL_RESOLUTION", "ABILITY_ACTIVATION",
                                     "ABILITY_RESOLUTION"],
         "eligibility_categories_only": True, "priority_implemented": False,
         "activation_window_evaluation_implemented": False},
        ["These opportunity categories neither grant real permission nor decide current activation eligibility.",
         "Priority, casting, ability procedures, resolution, and payment are not implemented."]),
    "605.3b": _rule(
        "605.3b", "Activated-mana immediate behavior without stack entry",
        "An activated mana ability resolves directly after activation rather than becoming "
        "a stack object. Stack-object targeting, countering, and responses therefore do not "
        "apply to that activation in the ordinary way.",
        "ACTIVATED_MANA_ABILITY_IMMEDIATE_RESOLUTION",
        ["activated_mana_ability", "no_stack_entry", "immediate_resolution",
         "no_stack_target", "no_stack_counter", "no_stack_response"],
        ["405.6c"],
        ["stack_semantics", "real_ability_activation", "ability_resolution", "response_windows",
         "targeting", "countering"],
        ["mana_no_stack_evidence", "immediate_activation_resolution_evidence"],
        {"actual_stack_entry": False, "resolution_sequence": "IMMEDIATELY_AFTER_ACTIVATION",
         "targetable_as_stack_object": False, "counterable_as_stack_object": False,
         "respondable_as_stack_object": False, "stack_exception_reference": "405.6c",
         "stack_bypass_runtime_implemented": False},
        ["The explicit stack-context dependency remains unresolved and unprojected.",
         "No stack object, response window, countering decision, or immediate-resolution operation is created."]),
    "605.3c": _rule(
        "605.3c", "The same mana ability cannot be repeated before resolution",
        "Beginning a mana-ability activation prevents another activation of that same ability "
        "until the first activation finishes resolving. This describes a narrow repeat-use "
        "constraint rather than a complete procedure scheduler.",
        "MANA_ABILITY_REACTIVATION_BOUNDARY",
        ["same_ability", "activation_started", "reactivation_restriction", "resolution_completion"],
        [],
        ["real_ability_activation", "activation_identity", "ability_resolution", "activation_sequencing"],
        ["mana_activation_identity", "same_ability_unresolved_activation_evidence"],
        {"restriction_begins": "ACTIVATION_START", "restricted_subject": "SAME_ABILITY",
         "restriction_ends": "THAT_ACTIVATION_RESOLVED",
         "same_ability_reactivation_before_resolution": False,
         "general_activation_sequence_supplied": False, "activation_lock_implemented": False},
        ["The record does not define a general activation scheduler, reentrancy lock, or runtime event sequence."]),
    "605.4": _rule(
        "605.4", "Triggered-mana behavior retains a general trigger dependency",
        "Triggered mana abilities rely on the ordinary triggered-ability rules while the "
        "selected child supplies their exceptional stack and resolution treatment.",
        "TRIGGERED_MANA_ABILITY_PROCEDURE_CONTEXT",
        ["triggered_mana_ability", "ordinary_trigger_dependency", "special_exception"],
        ["603"],
        ["general_triggered_ability_procedure", "trigger_detection", "trigger_event_semantics",
         "triggered_ability_sequencing"],
        ["triggered_ability_procedure_evidence", "mana_trigger_exception_evidence"],
        {"ordinary_trigger_dependency": "603", "special_exception_reference": "605.4a",
         "general_triggered_abilities_represented": False,
         "selected_exception_satisfies_general_trigger_semantics": False},
        ["The general triggered-ability subsystem remains unresolved; the exception is not trigger detection or execution."]),
    "605.4a": _rule(
        "605.4a", "Triggered-mana immediate sequencing without a priority wait",
        "A qualifying mana trigger resolves directly after the mana ability responsible for "
        "it, without being placed on the stack or waiting for priority. It consequently has "
        "no ordinary stack-object targeting, countering, or response interaction.",
        "TRIGGERED_MANA_ABILITY_IMMEDIATE_RESOLUTION",
        ["triggered_mana_ability", "causing_mana_ability", "no_stack_entry",
         "immediate_trigger_sequence", "no_priority_wait", "no_stack_response"],
        [],
        ["trigger_detection", "trigger_event_semantics", "triggered_ability_sequencing",
         "ability_resolution", "stack_semantics", "priority", "response_windows"],
        ["causal_mana_trigger_evidence", "immediate_trigger_resolution_evidence",
         "mana_no_stack_evidence"],
        {"actual_stack_entry": False, "resolution_sequence": "IMMEDIATELY_AFTER_CAUSING_MANA_ABILITY",
         "waits_for_priority": False, "targetable_as_stack_object": False,
         "counterable_as_stack_object": False, "respondable_as_stack_object": False,
         "trigger_sequence_runtime_implemented": False, "example_content_retained": False},
        ["No trigger detection, immediate sequencing, response, stack, or priority operation is implemented.",
         "The structurally owned source example is anchored as bytes only; no example prose or Card identity is retained."]),
    "605.5": _rule(
        "605.5", "Failure of the criteria and spell identity exclude mana classification",
        "An ability outside both selected criteria sets does not receive mana-ability "
        "classification. Spells are excluded from that category independently of their effects.",
        "MANA_ABILITY_EXCLUSION_CONTEXT",
        ["negative_classification", "criteria_failure", "spell_exclusion"],
        ["605.1a", "605.1b"],
        ["ability_kind_semantics", "mana_ability_classification", "spell_semantics",
         "real_card_and_effect_semantics"],
        ["mana_classification_exclusion_evidence", "spell_ability_kind_distinction"],
        {"criteria_references": ["605.1a", "605.1b"],
         "neither_criteria_set_satisfied": "NOT_MANA_ABILITY",
         "spell_is_mana_ability": False, "source_range_expansion": ["605.1a", "605.1b"]},
        ["The numbered criteria range is represented by its two actual selected members.",
         "Negative evidence is descriptive and does not supply a real classifier."]),
    "605.5a": _rule(
        "605.5a", "Targeted and nonqualifying triggered abilities use ordinary procedures",
        "The exclusions include an ability requiring a target, a potentially mana-producing "
        "trigger with an unsuitable triggering relationship, and a trigger tied to mana-ability "
        "activation that cannot generate mana. Excluded abilities continue to need the ordinary "
        "activated or triggered procedure appropriate to their kind.",
        "EXPLICIT_NON_MANA_ABILITY_EXCLUSIONS",
        ["targeted_ability_exclusion", "wrong_trigger_exclusion", "no_mana_output_exclusion",
         "ordinary_ability_procedure_boundary"],
        [],
        ["target_knowledge", "trigger_relationship_semantics", "potential_mana_output_semantics",
         "general_activated_ability_procedure", "general_triggered_ability_procedure",
         "real_card_and_effect_semantics"],
        ["targeted_ability_exclusion_evidence", "nonqualifying_mana_trigger_evidence",
         "ordinary_ability_kind_procedure_evidence"],
        {"target_required": "NOT_MANA_ABILITY",
         "wrong_trigger_relationship": "NOT_MANA_ABILITY",
         "mana_activation_trigger_without_possible_mana_output": "NOT_MANA_ABILITY",
         "qualifying_trigger_criteria_reference": "605.1b",
         "exclusions_override_selected_complete_trigger_criteria": False,
         "ordinary_procedure": "ACTIVATED_OR_TRIGGERED_AS_APPROPRIATE",
         "ordinary_procedure_is_semantic_boundary_not_numbered_citation": True},
        ["No ordinary-ability numbered reference is invented where the selected block supplies none.",
         "The negative trigger cases must be read with the complete selected triggered criteria; they do not remove its qualifying resolution or mana-added relationships.",
         "No real target, event, potential output, or ordinary ability procedure is evaluated."]),
    "605.5b": _rule(
        "605.5b", "Mana-producing spells remain spells rather than mana abilities",
        "A spell retains spell classification even when resolving it could supply mana. "
        "Its casting and resolution therefore remain spell-procedure concerns, outside "
        "mana-ability classification and immediate-ability behavior.",
        "SPELL_EXCLUSION_FROM_MANA_ABILITIES",
        ["spell_exclusion", "spell_that_adds_mana", "spell_procedure_boundary",
         "historical_oracle_context_not_ingested"],
        [],
        ["spell_semantics", "spell_casting", "spell_resolution", "real_card_and_effect_semantics"],
        ["spell_ability_kind_distinction", "mana_producing_spell_exclusion_evidence"],
        {"spell_is_mana_ability": False, "spell_that_adds_mana_equals_mana_ability": False,
         "spell_casting_and_resolution_remain_separate": True,
         "historical_context": "HISTORICAL_ORACLE_CONTEXT_NOT_INGESTED",
         "oracle_ingested": False, "real_card_identities_retained": False},
        ["Historical reference-data context is not ingested or retained as Card knowledge.",
         "No real spell, Card text, casting behavior, or mana generation is interpreted."]),
})


def _unique_boundaries():
    result = []
    seen = set()
    for rule in RULE_CONTENT.values():
        for field in ("unresolved_dependencies", "subsystem_boundaries", "required_future_semantic_primitives"):
            for entry in rule[field]:
                key = (entry["reference"], entry["classification"], entry["status"])
                if key not in seen:
                    seen.add(key)
                    result.append(entry)
    return result


NEW_BOUNDARIES = _freeze(_unique_boundaries())
GRAPH_NODES = _freeze([
    {"reference": ref, "classification": "PROJECTED_RULE", "status": "PROJECTED_IN_THIS_MILESTONE"}
    for ref in SELECTED_REFERENCES
] + list(NEW_BOUNDARIES))
GRAPH_EDGES = _freeze([
    {"from_reference": ref, "to_reference": entry["reference"],
     "relation": entry.get("relation", relation), "classification": entry["classification"],
     "status": entry["status"]}
    for ref in SELECTED_REFERENCES
    for field, relation in (("dependencies", "DEPENDS_ON"), ("unresolved_dependencies", "DEPENDS_ON"),
                            ("family_relationships", "STRUCTURAL_FAMILY_RELATIONSHIP"),
                            ("subsystem_boundaries", "SUBSYSTEM_BOUNDARY"),
                            ("required_future_semantic_primitives", "REQUIRES_FUTURE_PRIMITIVE"))
    for entry in RULE_CONTENT[ref][field]
])
UNSUPPORTED_DIMENSIONS = (
    "real_execution", "real_gameplay_rules_snapshot", "real_execution_profile", "owner_activation",
    "mana_ability_classification", "real_ability_kind_detection", "target_knowledge_evaluation",
    "loyalty_classification", "library_movement_semantics", "replacement_effect_evaluation",
    "activated_ability_execution", "trigger_detection", "triggered_ability_execution",
    "trigger_event_semantics", "immediate_resolution", "stack_bypass_runtime", "stack_semantics",
    "priority", "response_windows", "countering", "controller_assignment",
    "hypothetical_stack_controller_attribution", "mana_production_semantics", "mana_pool_semantics",
    "mana_spending", "cost_payment", "payment_integration", "complete_spell_casting",
    "activation_sequencing", "real_card_semantics", "real_effect_semantics", "oracle_ingestion",
    "simulation", "general_cr_parser", "recursive_projection", "full_semantic_closure",
    "source_prose_retention_or_redistribution",
)
