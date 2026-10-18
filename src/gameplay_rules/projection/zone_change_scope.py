"""Fixed authored scope for twelve non-executable zone-change exceptions.

The descriptions preserve distinct continuity relationships and unresolved
boundaries. They neither implement those relationships nor infer dependencies.
"""
from .contracts import _freeze


SELECTED_REFERENCES = (
    "400.7a", "400.7b", "400.7c", "400.7d", "400.7e", "400.7f",
    "400.7g", "400.7h", "400.7i", "400.7j", "400.7k", "400.7m",
)
ZONE_CHANGE_SELECTED_REFERENCES = SELECTED_REFERENCES
PARENT_REFERENCE = "400.7"
UNRESOLVED_RULE_REFERENCES = ("611.3d", "704.5m", "702.35", "123.5")
LETTERING_POLICY = _freeze({
    "classification": "EXPECTED_CR_SUBRULE_LETTERING",
    "selected_references": SELECTED_REFERENCES,
    "omitted_reference": "400.7l", "omitted_reference_present": False,
    "expected_omission": True, "source_anomaly": False,
    "missing_source_unit_inferred": False, "correction_applied": False,
    "convention": "CR_SUBRULE_LETTERS_SKIP_L_AND_O",
})


def _unresolved(reference):
    return {"reference": reference, "classification": "UNRESOLVED_RULE", "status": "UNRESOLVED"}


def _subsystem(reference):
    classification = "UNSUPPORTED_KEYWORD_SUBSYSTEM" if reference == "madness" else "UNRESOLVED_SUBSYSTEM"
    return {"reference": reference, "classification": classification, "status": "UNSUPPORTED"}


def _primitive(reference):
    return {"reference": reference, "classification": "FUTURE_SEMANTIC_PRIMITIVE", "status": "UNIMPLEMENTED"}


def _rule(topic, paraphrase, tags, targets, subsystems, primitives, distinctions, limitations):
    return {
        "topic": topic, "paraphrase": paraphrase,
        "semantic_category": "ZONE_CHANGE_IDENTITY_EXCEPTION",
        "domain_classification": "CORE_GAME_SUBSYSTEM", "concept_tags": tags,
        "dependencies": [{"reference": PARENT_REFERENCE, "classification": "PROJECTED_RULE",
                          "status": "PROJECTED_IN_FOUNDATIONAL"}],
        "direct_dependency_references": targets,
        "unresolved_dependencies": [_unresolved(reference) for reference in targets],
        "subsystem_boundaries": [_subsystem(reference) for reference in subsystems],
        "required_future_semantic_primitives": [_primitive(reference) for reference in primitives],
        "semantic_distinctions": distinctions,
        "exception_subrule_boundaries": [], "limitations": limitations,
        "coverage_state": "EXCEPTION_REFERENCE_PROJECTED", "review_state": "PROJECTED_FOR_REVIEW",
        "exception_semantics_closed": False, "semantic_closure_state": "OPEN", "execution_ready": False,
    }


RULE_CONTENT = _freeze({
    "400.7a": _rule(
        "Effect continuity from a permanent spell to its permanent",
        "Qualifying spell- or ability-generated changes to a permanent spell's characteristics or control "
        "remain applicable to the permanent produced by that spell.",
        ["spell_to_permanent", "effect_continuity", "characteristics", "controller_change"], [],
        ["continuous_effects", "spell_resolution", "characteristics_evaluation", "control_changes", "stack_behavior"],
        ["spell_to_permanent_effect_continuity"],
        {"relationship": "QUALIFYING_EFFECT_CONTINUITY", "general_object_identity_preserved": False,
         "qualifying_effect_origins": ["spells", "activated_abilities", "triggered_abilities"]},
        ["Only the continuity relationship is described; effects and spell resolution remain unsupported.",
         "No characteristics evaluation, controller reassignment, or stack behavior is implemented."]),
    "400.7b": _rule(
        "Granted-static-ability effect continuity",
        "A qualifying static-ability effect granting a battlefield-functional ability to a permanent spell "
        "also applies to the resulting permanent.",
        ["spell_to_permanent", "static_ability", "granted_ability", "effect_continuity"], ["611.3d"],
        ["static_abilities", "continuous_effects", "granted_abilities", "characteristic_layers"],
        ["static_granted_ability_continuity"],
        {"relationship": "QUALIFYING_STATIC_GRANTED_ABILITY_CONTINUITY",
         "granted_ability_functional_zone": "battlefield", "general_object_identity_preserved": False},
        ["Rule 611.3d remains unresolved and unprojected.",
         "Static abilities, continuous effects, layers, and granted abilities remain unsupported."]),
    "400.7c": _rule(
        "Prevention continuity for a permanent spell's damage",
        "Qualifying prevention attached to damage from a permanent spell also covers damage from the permanent "
        "produced by that spell.",
        ["spell_to_permanent", "prevention", "damage", "source_continuity"], [],
        ["prevention_effects", "damage", "spell_resolution", "damage_source_continuity"],
        ["spell_to_permanent_prevention_continuity"],
        {"relationship": "QUALIFYING_PREVENTION_CONTINUITY", "general_object_identity_preserved": False},
        ["Prevention, damage, spell resolution, and source continuity have no runtime implementation.",
         "No numbered damage or prevention dependency is inferred from this semantic boundary."]),
    "400.7d": _rule(
        "Historical spell information accessible to a permanent's ability",
        "A permanent's ability may consult casting history of the spell that produced it, including paid costs "
        "and mana used for those payments.",
        ["spell_to_permanent", "object_history_access", "costs_paid", "mana_spent"], [],
        ["spell_history", "casting", "costs", "mana", "spell_resolution", "card_abilities"],
        ["spell_to_permanent_history_access"],
        {"relationship": "OBJECT_HISTORY_ACCESS", "object_identity_equivalence": False,
         "historical_information": ["costs_paid_to_cast", "mana_spent_to_pay_casting_costs"]},
        ["Historical access does not make the permanent identical to the prior spell object.",
         "No casting, mana, cost, resolution, Card-ability, or historical-query execution is implemented."]),
    "400.7e": _rule(
        "Public-destination findability for a zone-change trigger",
        "A qualifying zone-change triggered ability may locate the resulting object in the move's public "
        "destination associated with its triggering event.",
        ["zone_change", "triggered_ability", "public_zone", "bounded_findability"], [],
        ["zone_change_triggers", "triggered_abilities", "public_zone_object_tracking"],
        ["zone_change_trigger_public_object_lookup"],
        {"relationship": "BOUNDED_NEW_OBJECT_FINDABILITY", "destination_must_be_public": True,
         "general_new_object_rule_overridden": False},
        ["Findability is constrained to the relevant zone-change event and public destination.",
         "Trigger detection, trigger processing, object tracking, and hidden-zone lookup remain unsupported."]),
    "400.7f": _rule(
        "Aura lookup after an enchanted permanent leaves",
        "A qualifying departure trigger can locate new Aura objects in their owners' graveyards when the Auras "
        "leave with the enchanted permanent or subsequently move there through the specified unattached-Aura state action.",
        ["aura", "enchanted_permanent", "leaves_battlefield_trigger", "graveyard", "state_based_action"], ["704.5m"],
        ["aura_attachment", "leaves_the_battlefield_triggers", "simultaneous_zone_movement",
         "state_based_action_movement", "new_object_tracking"],
        ["aura_departure_graveyard_object_lookup"],
        {"relationship": "SPECIALIZED_AURA_NEW_OBJECT_FINDABILITY", "destination": "owners_graveyards",
         "movement_cases": ["simultaneous_with_enchanted_permanent_departure", "unattached_aura_state_based_action"]},
        ["Rule 704.5m remains unresolved and unprojected.",
         "No Aura attachment, departure trigger, simultaneous movement, state action, or tracking is implemented."]),
    "400.7g": _rule(
        "Granted casting ability continues on the resulting stack object",
        "When an effect grants a nonland card a casting ability and the card is cast through it, that granted "
        "ability remains applicable to the resulting stack object.",
        ["nonland", "casting_permission", "granted_casting_ability", "stack_object"], [],
        ["casting", "casting_permissions", "stack_movement", "card_semantics"],
        ["cast_permission_identity_bridge"],
        {"relationship": "GRANTED_CASTING_ABILITY_CONTINUATION", "card_kind": "nonland",
         "findability_of_other_effect_parts": False},
        ["This describes continuation of the granted ability, separately from other-effect-part lookup.",
         "No casting, permissions, stack movement, or Card semantics are implemented."]),
    "400.7h": _rule(
        "Other portions of a casting-permission effect locate the stack object",
        "After a nonland card is cast through an effect's permission, the effect's other portions may locate "
        "the new stack object created by that casting.",
        ["nonland", "casting_permission", "other_effect_parts", "stack_object_findability"], [],
        ["casting", "casting_permissions", "stack_movement", "effect_continuity"],
        ["cast_permission_effect_object_lookup"],
        {"relationship": "OTHER_EFFECT_PARTS_STACK_OBJECT_FINDABILITY", "card_kind": "nonland",
         "granted_casting_ability_continuation": False},
        ["Other portions finding the object is a distinct relationship from granted-ability continuation.",
         "No casting, effect execution, permissions, or stack processing is implemented."]),
    "400.7i": _rule(
        "Other portions of a land-play permission effect locate the land",
        "After a land card is played through an effect's permission, the effect's other portions may locate "
        "the resulting battlefield object.",
        ["land", "land_play_permission", "other_effect_parts", "battlefield_object_findability"], [],
        ["land_play", "land_play_permissions", "battlefield_entry", "turn_timing"],
        ["land_play_permission_identity_bridge"],
        {"relationship": "OTHER_EFFECT_PARTS_LAND_OBJECT_FINDABILITY", "card_kind": "land",
         "land_play_is_casting": False, "destination": "battlefield"},
        ["Playing a land is distinct from casting a spell.",
         "Land play, permissions, battlefield entry, and turn timing remain unsupported."]),
    "400.7j": _rule(
        "Public-zone lookup after movement caused by an effect or a cost",
        "For an effect-caused public-zone move, the effect's other portions may locate the object. For a move "
        "caused by a spell or ability cost, that spell or ability's effects may locate it.",
        ["public_zone", "same_effect_tracking", "cost_caused_movement", "effect_caused_movement"], [],
        ["effects", "costs", "zone_movement", "public_zone_object_tracking", "object_history"],
        ["same_effect_public_zone_object_lookup", "cost_movement_public_zone_object_lookup"],
        {"relationship": "SAME_EFFECT_OR_COST_OBJECT_FINDABILITY", "destination_must_be_public": True,
         "movement_cases": [{"cause": "effect", "lookup_actor": "other_parts_of_same_effect"},
                            {"cause": "spell_or_ability_cost", "lookup_actor": "effects_of_that_spell_or_ability"}]},
        ["Effect-caused movement and spell-or-ability-cost-caused movement remain separate cases.",
         "The broad tracking description does not establish semantic closure or implement effects, costs, movement, or history."]),
    "400.7k": _rule(
        "Madness-specific lookup after the card was not cast",
        "After the madness trigger resolves without casting the exiled card, references to the discarded card "
        "may locate its resulting object if it moved into a public zone.",
        ["madness", "discarded_card", "exile", "public_zone", "object_findability"], ["702.35"],
        ["madness", "discard", "exile_handling", "casting_through_madness", "triggered_abilities"],
        ["madness_public_zone_object_lookup"],
        {"relationship": "MADNESS_SPECIFIC_OBJECT_FINDABILITY", "card_cast_through_madness": False,
         "destination_must_be_public": True},
        ["Rule 702.35 remains unresolved and unprojected; madness is an unsupported keyword subsystem.",
         "No madness, discard, exile handling, casting, or triggered-ability execution is implemented."]),
    "400.7m": _rule(
        "Sticker retention and effect continuity between public zones",
        "Movement between public zones retains an object's stickers, and sticker effects remain applicable "
        "to the new object produced by that movement.",
        ["stickers", "public_to_public_zone", "sticker_retention", "sticker_effect_continuity"], ["123.5"],
        ["stickers", "ticket_costs", "name_stickers", "ability_stickers", "continuous_effects"],
        ["public_zone_sticker_retention", "sticker_effect_new_object_continuity"],
        {"relationship": "STICKER_RETENTION_AND_EFFECT_CONTINUITY", "sticker_retention": True,
         "sticker_effect_continuation": True, "origin_and_destination_must_be_public": True,
         "general_object_identity_preserved": False},
        ["Rule 123.5 remains unresolved and unprojected.",
         "Sticker retention and sticker-effect continuation are distinct from general object identity.",
         "No stickers, tickets, name or ability stickers, or continuous effects are implemented."]),
})


def _unique_boundaries():
    boundaries = []
    seen = set()
    for rule in RULE_CONTENT.values():
        for field in ("unresolved_dependencies", "subsystem_boundaries", "required_future_semantic_primitives"):
            for boundary in rule[field]:
                key = (boundary["reference"], boundary["classification"], boundary["status"])
                if key not in seen:
                    seen.add(key)
                    boundaries.append(boundary)
    return boundaries


NEW_BOUNDARIES = _freeze(_unique_boundaries())
GRAPH_NODES = _freeze([
    {"reference": reference, "classification": "PROJECTED_EXCEPTION", "status": "EXCEPTION_REFERENCE_PROJECTED"}
    for reference in SELECTED_REFERENCES
] + [{"reference": PARENT_REFERENCE, "classification": "PROJECTED_RULE", "status": "PROJECTED_IN_FOUNDATIONAL"}]
  + list(NEW_BOUNDARIES))
GRAPH_EDGES = _freeze([
    {"from_reference": reference, "to_reference": entry["reference"], "relation": relation,
     "classification": entry["classification"], "status": entry["status"]}
    for reference in SELECTED_REFERENCES
    for field, relation in (("dependencies", "EXCEPTION_TO"), ("unresolved_dependencies", "DEPENDS_ON"),
                            ("subsystem_boundaries", "SUBSYSTEM_BOUNDARY"),
                            ("required_future_semantic_primitives", "REQUIRES_FUTURE_PRIMITIVE"))
    for entry in RULE_CONTENT[reference][field]
])
UNSUPPORTED_DIMENSIONS = (
    "real_execution", "real_gameplay_rules_snapshot", "real_execution_profile", "owner_activation",
    "zone_movement_runtime", "object_identity_runtime", "history_query_runtime", "continuous_effects",
    "characteristic_layers", "prevention_effects", "damage", "triggers", "delayed_triggers", "casting",
    "stack_processing", "mana", "costs", "land_play", "state_based_actions", "madness", "stickers",
    "auras", "replacement_effects", "public_and_hidden_zone_tracking", "card_effect_semantics",
    "real_card_semantics", "oracle_ingestion", "simulation", "general_cr_parser", "recursive_projection",
    "full_semantic_closure", "source_correction", "source_prose_retention_or_redistribution",
)
