"""Fixed authored evidence for the five reviewed casting source units.

Only explicit source citations become direct numbered dependencies.  The
unselected casting stages remain structural boundaries, and no declaration in
this module performs a casting, cost, payment, or game-state operation.
"""
from .contracts import _freeze


SELECTED_REFERENCES = ("601.2", "601.2b", "601.2f", "601.2g", "601.2h")
BOUNDED_CASTING_SELECTED_REFERENCES = SELECTED_REFERENCES
SELECTED_STAGE_REFERENCES = ("601.2b", "601.2f", "601.2g", "601.2h")
UNPROJECTED_SIBLING_REFERENCES = (
    "601.2a", "601.2c", "601.2d", "601.2e", "601.2i",
)
UNRESOLVED_RULE_REFERENCES = (
    "601.2a", "601.2c", "601.2d", "601.3", "733", "700.2",
    "702.47", "118.8", "118.9", "107.3", "605",
)
PARENT_DIRECT_REFERENCES = (
    "601.2a", "601.2b", "601.2c", "601.2d", "601.2f", "601.2g",
    "601.2h", "601.3", "733",
)


def _stage(reference):
    selected = reference in SELECTED_STAGE_REFERENCES
    return {
        "reference": reference,
        "classification": "PROJECTED_RULE" if selected else "UNPROJECTED_CASTING_STAGE",
        "status": "SELECTED_AND_PROJECTED" if selected else "UNPROJECTED_CASTING_STAGE",
        "coverage_state": "PROJECTED" if selected else "UNPROJECTED",
        "parent_reference": "601.2",
        "parent_explicitly_cites_stage": reference in PARENT_DIRECT_REFERENCES,
        "relationship_basis": (
            "PARENT_EXPLICIT_NUMBERED_REFERENCE"
            if reference in PARENT_DIRECT_REFERENCES else "STRUCTURAL_SIBLING_BOUNDARY"
        ),
        "execution_relevance": "UNKNOWN_OR_INCOMPLETE",
        "execution_readiness": "BLOCKED",
        "execution_ready": False,
        "satisfied_by_parent_projection": False,
    }


SIBLING_STAGE_MATRIX = _freeze([
    {
        "reference": "601.2", "classification": "PROJECTED_RULE",
        "status": "PARENT_CONTEXT_PROJECTED", "coverage_state": "PROJECTED",
        "execution_relevance": "INCOMPLETE_PROCEDURAL_CONTEXT",
        "execution_readiness": "BLOCKED", "execution_ready": False,
        "satisfies_unprojected_stages": False,
    },
    *[_stage("601.2" + suffix) for suffix in "abcdefghi"],
])
CASTING_STAGE_MATRIX = SIBLING_STAGE_MATRIX


def _projected(reference, relation="DIRECT_NUMBERED_REFERENCE"):
    return {
        "reference": reference, "classification": "PROJECTED_RULE",
        "status": "PROJECTED_IN_THIS_MILESTONE", "relation": relation,
    }


def _unresolved(reference):
    return {
        "reference": reference,
        "classification": "UNRESOLVED_RULE", "status": "UNRESOLVED",
        "coverage_state": "UNPROJECTED", "relation": "DIRECT_NUMBERED_REFERENCE",
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


def _rule(topic, paraphrase, category, tags, direct, dependencies, subsystems,
          primitives, distinctions, limitations):
    return {
        "topic": topic, "paraphrase": paraphrase, "semantic_category": category,
        "domain_classification": "CORE_GAME_SUBSYSTEM", "concept_tags": tags,
        "direct_dependency_references": direct, "dependencies": dependencies,
        "unresolved_dependencies": [_unresolved(ref) for ref in direct
                                    if ref in UNRESOLVED_RULE_REFERENCES],
        "sibling_stage_relationships": list(SIBLING_STAGE_MATRIX),
        "subsystem_boundaries": [_subsystem(ref) for ref in subsystems],
        "required_future_semantic_primitives": [_primitive(ref) for ref in primitives],
        "semantic_distinctions": dict(distinctions, descriptive_only=True,
                                      runtime_operations_implemented=[],
                                      complete_casting_procedure_represented=False),
        "exception_subrule_boundaries": [], "limitations": limitations,
        "coverage_state": "BOUNDED_CASTING_SOURCE_PROJECTED",
        "review_state": "PROJECTED_FOR_REVIEW", "semantic_closure_state": "OPEN",
        "execution_readiness": "BLOCKED", "execution_ready": False,
    }


RULE_CONTENT = _freeze({
    "601.2": _rule(
        "Ordered casting procedure and incomplete stage coverage",
        "Casting takes a spell, card, or copy from its former location to the stack and requires "
        "its costs to be paid through an ordered procedure. The proposal and cost stages form "
        "parts of that procedure; permission to begin and the ability to finish every required "
        "step legally constrain it. Failure to complete a required step calls for undoing the "
        "casting proposal under a separate rule.",
        "CASTING_PROCEDURE_CONTEXT",
        ["casting", "ordered_procedure", "previous_location", "stack_proposal", "proposal_stages",
         "cost_stages", "casting_permission", "legality", "rollback", "incomplete_stage_coverage"],
        list(PARENT_DIRECT_REFERENCES),
        [_projected(ref, "EXPLICITLY_REFERENCED_SELECTED_STAGE") for ref in SELECTED_STAGE_REFERENCES],
        ["spell_proposal", "zone_move_execution", "stack_semantics", "casting_permission",
         "casting_legality", "target_declaration", "division_and_distribution", "cost_determination",
         "cost_payment", "casting_completion", "cast_triggers", "illegal_action_rollback"],
        ["casting_proposal_declaration", "ordered_casting_stage_contract", "casting_permission_evidence",
         "casting_legality_evidence", "casting_completion_evidence", "casting_rollback_contract"],
        {"relationship": "ORDERED_PROCEDURE_WITH_UNPROJECTED_STAGES",
         "movement_description": {"origin": "previous_location", "destination": "stack",
                                  "subject_kinds": ["spell", "card", "copy"]},
         "cost_payment_required": True, "legal_permission_to_begin_required": True,
         "required_step_failure": "ROLLBACK_BOUNDARY",
         "explicit_proposal_stage_references": ["601.2a", "601.2b", "601.2c", "601.2d"],
         "explicit_cost_stage_references": ["601.2f", "601.2g", "601.2h"],
         "selected_stage_references": list(SELECTED_STAGE_REFERENCES),
         "unprojected_stage_references": list(UNPROJECTED_SIBLING_REFERENCES),
         "legality_stage_boundary": "601.2e",
         "structural_siblings_without_parent_direct_citation": ["601.2e", "601.2i"],
         "parent_projection_satisfies_unselected_stages": False,
         "five_units_establish_complete_casting": False},
        ["This parent supplies procedural framing without projecting any unselected stage body.",
         "The legality-stage boundary remains material even though it is outside the parent's cited proposal and cost ranges.",
         "No stack proposal, legal-permission decision, casting step, or rollback operation is implemented."]),
    "601.2b": _rule(
        "Casting declarations and constraints on cost choices",
        "The casting declaration records modes, splice use with chosen cards revealed from hand, "
        "alternative or additional costs, "
        "variable values, and applicable hybrid or Phyrexian payment choices. A variable whose "
        "value depends on a choice normally made later brings that choice into this stage. "
        "Earlier casting choices can constrain these declarations. Multiple alternative methods "
        "or multiple alternative costs cannot simply be combined for one spell; the later total-cost "
        "stage uses the declarations.",
        "CASTING_CHOICE_DECLARATION",
        ["casting_choices", "modes", "splice", "alternative_cost", "additional_cost", "variable_values",
         "hybrid_declaration", "phyrexian_declaration", "prior_choice_restrictions", "exclusive_alternatives"],
        ["700.2", "702.47", "118.8", "118.9", "601.2f", "107.3"],
        [_projected("601.2", "SELECTED_PARENT_CONTEXT"),
         _projected("601.2f", "LATER_TOTAL_COST_STAGE")],
        ["mode_selection", "splice", "alternative_casting_methods", "alternative_cost_selection",
         "additional_cost_selection", "variable_cost_choice", "hybrid_payment_declarations",
         "phyrexian_payment_declarations", "prior_casting_choice_constraints", "real_card_semantics"],
        ["casting_choice_declaration", "selected_alternative_base_cost", "additional_cost_declaration",
         "alternative_method_exclusion_evidence", "variable_value_declaration",
         "hybrid_payment_declaration", "phyrexian_payment_declaration", "prior_choice_constraint_evidence"],
        {"relationship": "DECLARATIONS_FOR_LATER_TOTAL_COST_DETERMINATION",
         "mode_choice": "DESCRIPTIVE_ONLY", "splice_declaration": "DESCRIPTIVE_ONLY",
         "splice_cards_revealed_from": "HAND", "splice_reveal_implemented": False,
         "alternative_cost_declaration": "DESCRIPTIVE_ONLY",
         "additional_cost_declaration": "DESCRIPTIVE_ONLY",
         "base_cost_basis": ["NORMAL_MANA_COST", "SELECTED_ALTERNATIVE_COST"],
         "alternative_cost_replaces_normal_mana_cost_basis": True,
         "madness_cost_as_mana_cost_discount": False,
         "multiple_alternative_casting_methods_per_spell": False,
         "multiple_alternative_costs_per_spell": False,
         "alternative_interactions_fully_resolved": False,
         "variable_values": "DECLARED_WITH_REQUIRED_DEPENDENT_CHOICES",
         "normally_later_choice_needed_for_variable": "BRING_CHOICE_FORWARD_TO_THIS_STAGE",
         "hybrid_choice": "DECLARE_INTENDED_NONHYBRID_PAYMENT_EQUIVALENT",
         "phyrexian_choice": "DECLARE_CORRESPONDING_COLORED_MANA_OR_LIFE_FOR_EACH_APPLICABLE_SYMBOL",
         "prior_choices_may_restrict_current_choices": True,
         "later_total_cost_stage": "601.2f"},
        ["The declarations are authored semantic evidence, with no mode, splice, variable, hybrid, or Phyrexian operation.",
         "An alternative cost is a candidate base-cost replacement rather than a subtraction from the normal mana cost.",
         "Referenced choice and cost families remain unresolved; no complete alternative-method interaction algorithm is supplied."]),
    "601.2f": _rule(
        "Composition and lock-in of the total casting cost",
        "The total starts with either the normal mana cost or the chosen alternative cost, then "
        "accounts for additional costs, increases, and reductions. The player chooses the sequence "
        "when several reductions apply, and the mana portion has a zero lower bound. Effects that directly change the resulting "
        "total are considered after those ordinary components. Once determined, the total is locked "
        "and later changes do not alter it.",
        "CASTING_TOTAL_COST_DETERMINATION",
        ["normal_mana_cost", "alternative_base_cost", "additional_cost", "cost_increase", "cost_reduction",
         "reduction_order", "mana_zero_floor", "direct_total_modifier", "locked_total_cost"],
        ["601.2b"],
        [_projected("601.2", "SELECTED_PARENT_CONTEXT"),
         _projected("601.2b", "EARLIER_COST_DECLARATIONS")],
        ["total_cost_determination", "additional_cost_semantics", "cost_increase_semantics",
         "cost_reduction_semantics", "cost_reduction_ordering", "direct_total_cost_modifiers",
         "cost_locking_runtime", "real_card_and_effect_semantics"],
        ["base_cost_basis_declaration", "symbolic_total_cost_expression", "cost_modifier_order_evidence",
         "mana_cost_zero_floor_evidence", "locked_total_cost_identity"],
        {"relationship": "BASE_COST_COMPONENTS_THEN_DIRECT_MODIFIERS_THEN_LOCK",
         "base_cost_basis": ["NORMAL_MANA_COST", "SELECTED_ALTERNATIVE_COST"],
         "selected_base_count": 1, "madness_cost_as_mana_cost_discount": False,
         "ordinary_components": ["selected_base", "all_additional_costs", "cost_increases", "cost_reductions"],
         "reduction_order_may_matter": True, "mana_portion_lower_bound": 0,
         "reduction_application_order": "PLAYER_CHOOSES_ANY_ORDER",
         "direct_total_cost_modifiers_after_ordinary_components": True,
         "cost_lock": "FINAL_TOTAL_LOCKED_AFTER_DETERMINATION",
         "later_changes_alter_locked_total": False,
         "earlier_declaration_stage": "601.2b", "cost_calculation_implemented": False},
        ["Cost composition and lock-in are descriptions; no amount is computed and no cost effect is applied.",
         "No real Card text, cost-modification evaluator, layer runtime, or cost-locking runtime is supplied."]),
    "601.2g": _rule(
        "Conditional mana-ability opportunity before payment",
        "A total cost that requires a mana payment gives the casting player an opportunity to "
        "use mana abilities before paying that cost. The referenced mana-ability system remains "
        "outside the selected source scope.",
        "CASTING_MANA_ABILITY_WINDOW",
        ["determined_total_cost", "mana_payment_condition", "mana_ability_opportunity", "before_payment"],
        ["605"], [_projected("601.2", "SELECTED_PARENT_CONTEXT")],
        ["mana_abilities", "mana_production", "mana_pool_semantics", "ability_activation", "priority",
         "mana_payment"],
        ["mana_payment_requirement_evidence", "prepayment_mana_ability_opportunity"],
        {"relationship": "CONDITIONAL_PREPAYMENT_MANA_ABILITY_OPPORTUNITY",
         "condition": "DETERMINED_TOTAL_COST_CONTAINS_MANA_PAYMENT",
         "opportunity_actor": "casting_player", "opportunity_before_cost_payment": True,
         "mana_ability_dependency": "605", "real_605_satisfied_by_fictional_mana": False,
         "mana_ability_execution_implemented": False},
        ["The opportunity is represented without mana abilities, production, pools, activation, priority, or payment.",
         "Fictional mana behavior supplies no authority for real rule 605."]),
    "601.2h": _rule(
        "Payment groups and all-or-nothing cost requirements",
        "The payer handles ordinary components first, choosing their order within that group. "
        "Components involving randomness or moving library objects to a public zone belong to "
        "the remaining group and may be ordered within that group. Every required component "
        "must be payable and paid in full; a partial payment does not satisfy a cost.",
        "CASTING_TOTAL_COST_PAYMENT",
        ["total_cost_payment", "ordinary_payment_group", "later_payment_group", "random_element_cost",
         "library_to_public_zone_cost", "within_group_order", "partial_payment_forbidden", "unpayable_cost"],
        [], [_projected("601.2", "SELECTED_PARENT_CONTEXT")],
        ["cost_payment", "mana_payment", "nonmana_payment", "random_cost_handling",
         "library_to_public_zone_movement", "sacrificing", "tapping", "discard", "life_payment",
         "zone_move_execution"],
        ["locked_cost_payment_binding", "payment_component_inventory", "ordered_payment_groups",
         "complete_payment_evidence", "unpayable_cost_evidence"],
        {"relationship": "ORDINARY_GROUP_BEFORE_RANDOM_OR_LIBRARY_PUBLIC_GROUP",
         "payment_subject": "total_cost",
         "payment_groups": [
             {"order": 1, "name": "ORDINARY", "component_order": "ANY_ORDER",
              "excludes": ["random_element", "library_to_public_zone_movement"]},
             {"order": 2, "name": "RANDOM_OR_LIBRARY_TO_PUBLIC_ZONE", "component_order": "ANY_ORDER",
              "includes": ["random_element", "library_to_public_zone_movement"]},
         ],
         "partial_payment_allowed": False, "unpayable_cost_may_be_paid": False,
         "payment_execution_implemented": False,
         "example_content_retained": False},
        ["Payment grouping and completeness requirements are represented without performing any payment.",
         "No library inspection, randomization, sacrifice, tap, discard, life payment, or object movement is supplied.",
         "Any example included in the verified source block contributes only to its hash and span; its prose is not retained."]),
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
    for ref in UNPROJECTED_SIBLING_REFERENCES:
        if any(entry["reference"] == ref for entry in result):
            # The direct-citation node already records this unresolved stage.
            # Its stage classification remains explicit in the separate matrix.
            continue
        result.append({
            "reference": ref, "classification": "UNPROJECTED_CASTING_STAGE",
            "status": "UNPROJECTED", "coverage_state": "UNPROJECTED",
            "relation": "STRUCTURAL_SIBLING_BOUNDARY",
        })
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
                            ("subsystem_boundaries", "SUBSYSTEM_BOUNDARY"),
                            ("required_future_semantic_primitives", "REQUIRES_FUTURE_PRIMITIVE"))
    for entry in RULE_CONTENT[ref][field]
] + [
    {"from_reference": "601.2", "to_reference": ref,
     "relation": "STRUCTURAL_SIBLING_BOUNDARY", "classification": "UNPROJECTED_CASTING_STAGE",
     "status": "UNPROJECTED"}
    for ref in UNPROJECTED_SIBLING_REFERENCES if ref not in PARENT_DIRECT_REFERENCES
])
UNSUPPORTED_DIMENSIONS = (
    "real_execution", "real_gameplay_rules_snapshot", "real_execution_profile", "owner_activation",
    "complete_spell_casting", "spell_proposal", "stack_placement", "stack_semantics", "mode_selection",
    "splice", "target_selection", "division_and_distribution", "variable_value_execution",
    "hybrid_payment_execution", "phyrexian_payment_execution", "alternative_cost_execution",
    "additional_cost_execution", "cost_increase_execution", "cost_reduction_execution",
    "total_cost_computation", "cost_locking_runtime", "mana_abilities", "mana_production",
    "mana_pool_semantics", "mana_payment", "nonmana_payment", "sacrificing", "tapping", "discard",
    "life_payment", "random_cost_handling", "library_movement", "zone_movement_runtime",
    "casting_legality", "casting_permission", "illegal_action_rollback", "casting_completion",
    "cast_triggers", "priority", "madness_runtime", "real_card_semantics", "real_effect_semantics",
    "oracle_ingestion", "simulation", "general_cr_parser", "recursive_projection",
    "full_semantic_closure", "source_prose_retention_or_redistribution",
)
