"""Fixed authored evidence for twelve direct zone-change dependency units.

Numbered relationships reflect only references present in the selected source
lines. Context and subsystem boundaries do not expand the projection allowlist.
"""
from .contracts import _freeze


SELECTED_REFERENCES = (
    "611.3", "611.3a", "611.3b", "611.3d", "704.5m",
    "702.35a", "702.35b", "702.35c", "123.5", "123.5a", "123.5b", "123.5c",
)
ZONE_CHANGE_DEPENDENCY_SELECTED_REFERENCES = SELECTED_REFERENCES
UNRESOLVED_RULE_REFERENCES = ("601.2b", "601.2f", "601.2g", "601.2h")
DIRECT_REFERENCE_TARGETS = ("611.3d", "704.5m", "702.35", "123.5")
REFERENCE_FAMILIES = _freeze({
    "611.3d": ["611.3", "611.3a", "611.3b", "611.3d"],
    "704.5m": ["704.5m"],
    "702.35": ["702.35a", "702.35b", "702.35c"],
    "123.5": ["123.5", "123.5a", "123.5b", "123.5c"],
})


def _projected(reference, relation="DIRECT_NUMBERED_REFERENCE"):
    if reference == "400.7":
        status = "PROJECTED_IN_FOUNDATIONAL"
    elif reference == "400.7k":
        status = "PROJECTED_IN_ZONE_CHANGE_EXCEPTIONS"
    else:
        status = "PROJECTED_IN_THIS_MILESTONE"
    return {"reference": reference, "classification": "PROJECTED_RULE", "status": status,
            "relation": relation}


def _unresolved(reference):
    return {"reference": reference, "classification": "UNRESOLVED_RULE", "status": "UNRESOLVED",
            "coverage_state": "UNPROJECTED", "relation": "DIRECT_NUMBERED_REFERENCE"}


def _subsystem(reference):
    return {"reference": reference, "classification": "UNRESOLVED_SUBSYSTEM", "status": "UNSUPPORTED"}


def _primitive(reference):
    return {"reference": reference, "classification": "FUTURE_SEMANTIC_PRIMITIVE", "status": "UNIMPLEMENTED"}


def _rule(topic, paraphrase, category, tags, direct, dependencies, subsystems, primitives,
          distinctions, limitations):
    return {
        "topic": topic, "paraphrase": paraphrase, "semantic_category": category,
        "domain_classification": "CORE_GAME_SUBSYSTEM", "concept_tags": tags,
        "direct_dependency_references": direct, "dependencies": dependencies,
        "unresolved_dependencies": [_unresolved(ref) for ref in direct
                                    if ref in UNRESOLVED_RULE_REFERENCES],
        "subsystem_boundaries": [_subsystem(ref) for ref in subsystems],
        "required_future_semantic_primitives": [_primitive(ref) for ref in primitives],
        "semantic_distinctions": distinctions, "exception_subrule_boundaries": [],
        "limitations": limitations, "coverage_state": "DEPENDENCY_REFERENCE_PROJECTED",
        "review_state": "PROJECTED_FOR_REVIEW", "semantic_closure_state": "OPEN",
        "execution_readiness": "BLOCKED", "execution_ready": False,
    }


RULE_CONTENT = _freeze({
    "611.3": _rule(
        "Static abilities as continuous-effect generators",
        "An object's static ability can be the origin of a continuous effect.",
        "STATIC_CONTINUOUS_EFFECT_CONTEXT", ["static_ability", "continuous_effect", "effect_origin"],
        [], [], ["static_abilities", "continuous_effects"], ["static_continuous_effect_origin"],
        {"relationship": "STATIC_ABILITY_MAY_GENERATE_CONTINUOUS_EFFECT", "context_only": True},
        ["This supplies descriptive context without a static-ability or continuous-effect evaluator."]),
    "611.3a": _rule(
        "Dynamic applicability of a static continuous effect",
        "A static ability's continuous effect applies according to its text as circumstances change, "
        "rather than selecting one permanently fixed initial collection of objects.",
        "STATIC_CONTINUOUS_EFFECT_APPLICATION", ["dynamic_applicability", "static_ability", "continuous_effect"],
        [], [_projected("611.3", "SELECTED_PARENT_CONTEXT")],
        ["continuous_effects", "object_selection", "characteristic_layers", "characteristic_calculation", "dependency_ordering"],
        ["dynamic_static_continuous_effect_application"],
        {"relationship": "DYNAMIC_TEXT_DETERMINED_APPLICABILITY", "initial_object_set_frozen": False},
        ["No effect evaluation, object selection, layer calculation, or dependency ordering is implemented."]),
    "611.3b": _rule(
        "Ordinary location condition for a static continuous effect",
        "The generating permanent's presence on the battlefield, or the generating object's presence "
        "in the applicable zone, ordinarily sustains the effect's applicability.",
        "STATIC_CONTINUOUS_EFFECT_DURATION", ["static_ability", "appropriate_zone", "battlefield", "duration"],
        [], [_projected("611.3", "SELECTED_PARENT_CONTEXT")],
        ["static_abilities", "zone_sensitive_continuous_effects", "duration_tracking"],
        ["static_continuous_effect_zone_duration"],
        {"relationship": "ORDINARY_GENERATOR_LOCATION_CONDITION", "permanent_location": "battlefield",
         "other_object_location": "appropriate_zone"},
        ["Location-sensitive effects, static abilities, and duration tracking remain unsupported."]),
    "611.3d": _rule(
        "Special duration of a battlefield ability granted with play or casting access",
        "A static effect that supplies land-play access, permanent-spell casting access, or a granted "
        "casting ability can also supply an ability usable only on the battlefield. That battlefield "
        "ability persists for the duration given by the access-granting effect, or through the game's "
        "end when no duration is given, departing from the ordinary dynamic and location conditions.",
        "STATIC_CONTINUOUS_EFFECT_EXCEPTION", ["static_ability", "land_play_permission", "permanent_spell",
        "granted_casting_ability", "battlefield_ability", "special_duration"],
        ["611.3a", "611.3b"],
        [_projected("611.3", "SELECTED_PARENT_CONTEXT"), _projected("611.3a", "EXCEPTION_TO"),
         _projected("611.3b", "EXCEPTION_TO")],
        ["static_abilities", "continuous_effects", "land_play_permissions", "casting", "granted_abilities",
         "battlefield_abilities", "duration_evaluation"],
        ["static_granted_battlefield_ability_duration", "static_granted_ability_continuity"],
        {"relationship": "EXPLICIT_EXCEPTION_TO_SELECTED_DYNAMIC_AND_LOCATION_RULES",
         "exception_to": ["611.3a", "611.3b"],
         "qualifying_access": ["play_land", "cast_permanent_spell", "grant_casting_ability_to_permanent_spell_or_card"],
         "additional_granted_ability_zone": "battlefield_only", "duration": "as_stated_by_granting_effect",
         "unstated_duration": "until_end_of_game", "general_effect_follows_object_rule": False},
        ["Only the special relationship relevant to the existing 400.7b evidence is described.",
         "No land permission, casting, continuous effect, battlefield ability, or duration runtime is supplied."]),
    "704.5m": _rule(
        "Aura state action for an invalid or absent attachment",
        "An Aura attached to an impermissible object or player, or attached to neither, is moved "
        "into the graveyard belonging to its owner.",
        "AURA_STATE_BASED_ACTION", ["aura", "illegal_attachment", "unattached", "owners_graveyard", "state_based_action"],
        [], [], ["aura_attachment_legality", "state_based_action_scheduler", "zone_move_execution",
                 "priority", "simultaneous_state_based_actions"],
        ["aura_attachment_legality_check", "state_based_action_scheduling", "aura_graveyard_zone_move"],
        {"relationship": "AURA_ATTACHMENT_FAILURE_STATE_BASED_ACTION",
         "conditions": ["attached_to_illegal_object_or_player", "not_attached_to_object_or_player"],
         "destination": "owners_graveyard", "supplies_evidence_for": "400.7f"},
        ["The condition and destination are evidence only; Aura legality and all state-action execution remain absent.",
         "No numbered dependency is inferred from the state-action subsystem boundaries."]),
    "702.35a": _rule(
        "Madness as a linked discard replacement and casting trigger",
        "Madness packages two abilities: a static ability available from hand redirects a discard's "
        "destination to exile, then a triggered ability that functions when that replacement applies lets the owner "
        "cast the card for its madness cost instead of its mana cost. Declining that casting sends "
        "the card to the owner's graveyard.",
        "MADNESS_KEYWORD_DEFINITION", ["madness", "two_abilities", "hand", "discard_replacement", "exile",
        "triggered_ability", "optional_casting", "alternative_cost", "graveyard"],
        [], [], ["discard_replacement_behavior", "discard", "exile", "triggered_abilities", "optional_casting",
                 "alternative_costs", "graveyard_movement"],
        ["madness_discard_destination_replacement", "madness_linked_trigger", "madness_optional_alternative_cost_casting",
         "madness_uncast_graveyard_move"],
        {"relationship": "TWO_LINKED_ABILITIES", "ability_count": 2,
         "first_ability": {"kind": "static", "functional_zone": "hand", "discard_occurs": True,
                           "replacement_destination": "exile"},
         "second_ability": {"kind": "triggered", "trigger": "first_ability_applied", "casting_optional": True,
                            "casting_player": "owner", "cost": "madness_cost_instead_of_mana_cost",
                            "uncast_destination": "owners_graveyard"},
         "casting_discount_only": False},
        ["Both linked abilities are described, with no discard, replacement, exile, trigger, casting, cost, or movement runtime."]),
    "702.35b": _rule(
        "Madness casting's unresolved alternative-cost procedure",
        "Casting by means of madness uses the alternative-cost casting procedure identified by four "
        "specific casting subrules, whose content is outside this projection.",
        "MADNESS_CASTING_DEPENDENCY", ["madness", "alternative_cost", "casting_procedure", "unprojected_frontier"],
        ["601.2b", "601.2f", "601.2g", "601.2h"], [],
        ["casting", "alternative_costs", "payment"], ["alternative_cost_casting_procedure"],
        {"relationship": "ALTERNATIVE_COST_CASTING_PROCEDURE_REFERENCE", "numbered_targets_projected": False},
        ["All four casting references remain unresolved and unprojected.",
         "No rule 601 content, casting operation, alternative-cost evaluator, or payment operation is supplied."]),
    "702.35c": _rule(
        "Madness backlink to discarded-card lookup",
        "After the madness trigger has finished, if the card in exile was left uncast and moved "
        "to a public zone, an effect referring to the discarded card may locate the resulting object.",
        "MADNESS_PUBLIC_ZONE_FINDABILITY", ["madness", "trigger_resolution", "uncast", "public_zone", "discarded_card_lookup"],
        ["400.7k"], [_projected("400.7k")],
        ["triggered_abilities", "casting", "zone_move_execution", "public_zone_object_tracking", "effect_execution"],
        ["madness_public_zone_object_lookup"],
        {"relationship": "BIDIRECTIONAL_MADNESS_EXCEPTION_EVIDENCE", "backlink": "400.7k",
         "trigger_resolved": True, "card_cast": False, "destination_must_be_public": True,
         "lookup_actor": "effects_referencing_discarded_card", "general_object_identity_preserved": False},
        ["The existing 400.7k record is linked without being re-projected.",
         "Represented lookup relationships do not supply Madness or object-history execution."]),
    "123.5": _rule(
        "Sticker retention depends on destination visibility",
        "An object's stickers cease to accompany it upon a hidden-zone move. A public-zone move "
        "carries the stickers to the resulting object, where their effects remain applicable, "
        "as a stated exception to the ordinary new-object rule.",
        "STICKER_ZONE_CHANGE_RETENTION", ["stickers", "hidden_zone", "public_zone", "new_object", "effect_continuity"],
        ["400.7"], [_projected("400.7", "EXCEPTION_TO")],
        ["sticker_runtime", "public_and_hidden_zone_tracking", "zone_move_execution", "continuous_effects"],
        ["public_zone_sticker_retention", "sticker_effect_new_object_continuity"],
        {"relationship": "DESTINATION_VISIBILITY_STICKER_RETENTION", "exception_to": ["400.7"],
         "hidden_destination_retains_stickers": False, "public_destination_retains_stickers": True,
         "public_destination_sticker_effects_continue": True, "general_object_identity_preserved": False},
        ["The existing 400.7 record is linked without duplication; no sticker or zone runtime is supplied."]),
    "123.5a": _rule(
        "Sticker combination on a melded permanent",
        "When sticker-bearing cards enter the battlefield within a melded permanent, their stickers "
        "are carried onto that permanent while preserving the stickers' relative timestamp ordering.",
        "STICKER_MELD_CONTINUITY", ["stickers", "meld", "components", "battlefield_entry", "relative_timestamps"],
        [], [_projected("123.5", "SELECTED_PARENT_CONTEXT")],
        ["melded_permanent_composition", "sticker_runtime", "timestamp_ordering", "battlefield_entry"],
        ["meld_component_sticker_combination", "relative_sticker_timestamp_preservation"],
        {"relationship": "MELD_COMPONENT_STICKER_COMBINATION", "component_cards": "one_or_more",
         "result": "melded_permanent", "all_component_stickers_retained": True,
         "relative_timestamp_order_retained": True},
        ["Meld composition and timestamp execution remain unsupported.",
         "No numbered meld rule is inferred or projected."]),
    "123.5b": _rule(
        "Sticker transfer into a merged permanent",
        "A sticker belonging to an object that becomes a component of a merged battlefield "
        "permanent is carried by that merged permanent.",
        "STICKER_MERGE_CONTINUITY", ["stickers", "merge", "component", "battlefield"],
        [], [_projected("123.5", "SELECTED_PARENT_CONTEXT")],
        ["merged_permanent_composition", "sticker_runtime"], ["merged_component_sticker_continuity"],
        {"relationship": "MERGED_COMPONENT_STICKER_CONTINUITY", "result": "merged_permanent",
         "functional_zone": "battlefield", "meld_relationship": False},
        ["Merge composition is distinct from the selected meld case and remains unsupported.",
         "No numbered merge rule is inferred or projected."]),
    "123.5c": _rule(
        "One owner-selected resulting object keeps departing composite stickers",
        "When a sticker-bearing melded or merged permanent leaves the battlefield for another public "
        "zone, its owner selects one resulting object to carry its stickers. Only that selected "
        "object continues to receive those stickers' effects, even when the departure produces "
        "multiple objects.",
        "STICKER_SPLIT_OBJECT_RETENTION", ["stickers", "meld", "merge", "split_object", "owner_choice", "public_zone"],
        [], [_projected("123.5", "SELECTED_PARENT_CONTEXT")],
        ["melded_permanent_composition", "merged_permanent_composition", "choice_processing", "zone_move_execution",
         "sticker_runtime", "continuous_effects"],
        ["composite_departure_resulting_object_enumeration", "owner_sticker_retention_choice",
         "chosen_object_sticker_effect_continuity"],
        {"relationship": "ONE_RESULTING_OBJECT_STICKER_RETENTION", "origin": "battlefield",
         "destination": "another_public_zone", "composite_kinds": ["melded", "merged"],
         "multiple_resulting_objects_possible": True, "retaining_resulting_object_count": 1,
         "choice_actor": "owner", "all_stickers_retained_by_chosen_object": True,
         "sticker_effects_apply_only_to_chosen_object": True, "stickers_always_follow_each_card": False},
        ["Retention is bounded to one chosen result, rather than every resulting object.",
         "No meld, merge, choice, zone movement, or sticker-effect execution is supplied."]),
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
] + [{"reference": "400.7", "classification": "PROJECTED_RULE", "status": "PROJECTED_IN_FOUNDATIONAL"},
     {"reference": "400.7k", "classification": "PROJECTED_RULE", "status": "PROJECTED_IN_ZONE_CHANGE_EXCEPTIONS"}]
  + list(NEW_BOUNDARIES))
GRAPH_EDGES = _freeze([
    {"from_reference": ref, "to_reference": entry["reference"],
     "relation": entry.get("relation", relation), "classification": entry["classification"], "status": entry["status"]}
    for ref in SELECTED_REFERENCES
    for field, relation in (("dependencies", "DEPENDS_ON"), ("unresolved_dependencies", "DEPENDS_ON"),
                            ("subsystem_boundaries", "SUBSYSTEM_BOUNDARY"),
                            ("required_future_semantic_primitives", "REQUIRES_FUTURE_PRIMITIVE"))
    for entry in RULE_CONTENT[ref][field]
])
UNSUPPORTED_DIMENSIONS = (
    "real_execution", "real_gameplay_rules_snapshot", "real_execution_profile", "owner_activation",
    "static_abilities", "continuous_effects", "characteristic_layers", "characteristic_calculation",
    "dependency_ordering", "duration_evaluation", "land_play", "casting", "alternative_costs", "payment",
    "discard", "exile", "replacement_effects", "triggered_abilities", "state_based_actions",
    "aura_attachment_legality", "zone_movement_runtime", "object_history_runtime", "choice_processing",
    "madness_runtime", "sticker_runtime", "meld_runtime", "merge_runtime", "effect_execution",
    "card_effect_semantics", "real_card_semantics", "oracle_ingestion", "simulation", "general_cr_parser",
    "recursive_projection", "full_semantic_closure", "source_prose_retention_or_redistribution",
)
