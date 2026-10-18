"""Fixed authored scope for seven review-only object-control exceptions.

Only the authorized exception lines receive semantic descriptions. Referenced
subsystems stay unresolved; these records contain no runtime implementation.
"""
from .contracts import _freeze


SELECTED_REFERENCES = (
    "109.4a", "109.4b", "109.4c", "109.4d", "109.4e", "109.4f", "109.4g",
)
OBJECT_CONTROL_SELECTED_REFERENCES = SELECTED_REFERENCES
PARENT_REFERENCE = "109.4"
CORE_REFERENCES = SELECTED_REFERENCES[:3]
VARIANT_REFERENCES = SELECTED_REFERENCES[3:]
UNRESOLVED_RULE_REFERENCES = (
    "605", "603", "603.7d", "603.7e", "603.7f", "114",
    "901.6", "902.6", "904.7", "905.5",
)


def _unresolved(reference):
    return {"reference": reference, "classification": "UNRESOLVED_RULE", "status": "UNRESOLVED"}


def _variant(reference):
    return {"reference": reference, "classification": "UNSUPPORTED_VARIANT", "status": "UNSUPPORTED"}


def _primitive(reference):
    return {"reference": reference, "classification": "FUTURE_SEMANTIC_PRIMITIVE", "status": "UNIMPLEMENTED"}


def _rule(topic, paraphrase, domain, tags, targets, variants, primitives, limitations):
    return {
        "topic": topic, "paraphrase": paraphrase, "semantic_category": "OBJECT_CONTROL_EXCEPTION",
        "domain_classification": domain, "concept_tags": tags,
        "dependencies": [{"reference": PARENT_REFERENCE, "classification": "PROJECTED_RULE",
                          "status": "PROJECTED_IN_FOUNDATIONAL"}],
        "direct_dependency_references": targets,
        "unresolved_dependencies": [_unresolved(reference) for reference in targets],
        "variant_boundaries": [_variant(reference) for reference in variants],
        "required_future_semantic_primitives": [_primitive(reference) for reference in primitives],
        "exception_subrule_boundaries": [], "limitations": limitations,
        "coverage_state": "EXCEPTION_REFERENCE_PROJECTED", "review_state": "PROJECTED_FOR_REVIEW",
        "exception_semantics_closed": False, "execution_ready": False,
    }


RULE_CONTENT = _freeze({
    "109.4a": _rule(
        "Controller boundary for a mana ability",
        "A mana ability uses the controller determination that would apply to it on the stack, "
        "even when it is not there.",
        "CORE_GAME_SUBSYSTEM", ["controller", "mana_ability", "off_stack_ability"],
        ["605"], [], ["mana_ability_control"],
        ["Rule 605 remains unresolved and receives no projection.",
         "Mana abilities, mana production, activation, triggered mana abilities, targets, costs, and priority remain unsupported."]),
    "109.4b": _rule(
        "Controller boundary while a triggered ability awaits stack placement",
        "A triggered ability awaiting stack placement follows the participant who controlled its source "
        "when it triggered. Delayed triggered abilities require their separate controller rules.",
        "CORE_GAME_SUBSYSTEM", ["controller", "triggered_ability", "source_controller", "delayed_trigger"],
        ["603", "603.7d", "603.7e", "603.7f"], [], ["trigger_control", "delayed_trigger_control"],
        ["Rules 603 and 603.7d through 603.7f remain unresolved and receive no projection.",
         "No trigger detection, delayed-trigger processing, stack placement, APNAP ordering, priority, or state-based actions are implemented."]),
    "109.4c": _rule(
        "Controller boundary for an emblem",
        "For an emblem, control is assigned to the participant responsible for its placement in the command zone.",
        "CORE_GAME_SUBSYSTEM", ["controller", "emblem", "command_zone_placement"],
        ["114"], [], ["emblem_control"],
        ["Rule 114 remains unresolved and receives no projection.",
         "No emblem creation, emblem abilities, command-zone processing, or Card/effect semantics are implemented."]),
    "109.4d": _rule(
        "Planar controller boundary in Planechase",
        "In Planechase, a face-up plane card or phenomenon card follows the designated planar controller; "
        "the active participant ordinarily fills that designation.",
        "CASUAL_VARIANT_SUBSYSTEM", ["controller", "plane", "phenomenon", "planar_controller", "Planechase"],
        ["901.6"], ["Planechase"], ["planar_controller"],
        ["Rule 901.6 remains unresolved and receives no projection; Planechase remains unsupported.",
         "Planar-controller designation, its active-player relationship, and reassignment when that controller would leave are downstream boundaries only.",
         "No controller reassignment, departure procedure, or casual-variant runtime is implemented."]),
    "109.4e": _rule(
        "Ownership-based control of a Vanguard card",
        "Within Vanguard, control of a Vanguard card follows its ownership.",
        "CASUAL_VARIANT_SUBSYSTEM", ["controller", "owner", "Vanguard"],
        ["902.6"], ["Vanguard"], ["vanguard_control"],
        ["Rule 902.6 remains unresolved and receives no projection; Vanguard remains unsupported.",
         "No Vanguard setup, card processing, or variant control runtime is implemented."]),
    "109.4f": _rule(
        "Ownership-based control of an Archenemy scheme",
        "Within Archenemy, a scheme's control follows its ownership.",
        "CASUAL_VARIANT_SUBSYSTEM", ["controller", "owner", "scheme", "Archenemy"],
        ["904.7"], ["Archenemy"], ["scheme_control"],
        ["Rule 904.7 remains unresolved and receives no projection; Archenemy remains unsupported.",
         "No scheme decks, scheme actions, multiplayer-team processing, or variant control runtime is implemented."]),
    "109.4g": _rule(
        "Ownership-based control of a Conspiracy Draft card",
        "Within Conspiracy Draft, control of a conspiracy card follows its ownership.",
        "CASUAL_VARIANT_SUBSYSTEM", ["controller", "owner", "conspiracy", "Conspiracy Draft"],
        ["905.5"], ["Conspiracy Draft"], ["conspiracy_control"],
        ["Rule 905.5 remains unresolved and receives no projection; Conspiracy Draft remains unsupported.",
         "No draft behavior, hidden agenda, multiplayer processing, or variant control runtime is implemented."]),
})

NEW_BOUNDARIES = _freeze([
    *[_unresolved(reference) for reference in UNRESOLVED_RULE_REFERENCES],
    *[_variant(reference) for reference in ("Planechase", "Vanguard", "Archenemy", "Conspiracy Draft")],
    *[_primitive(reference) for reference in (
        "mana_ability_control", "trigger_control", "delayed_trigger_control", "emblem_control",
        "planar_controller", "vanguard_control", "scheme_control", "conspiracy_control")],
])
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
                            ("variant_boundaries", "VARIANT_BOUNDARY"),
                            ("required_future_semantic_primitives", "REQUIRES_FUTURE_PRIMITIVE"))
    for entry in RULE_CONTENT[reference][field]
])
UNSUPPORTED_DIMENSIONS = (
    "real_execution", "real_gameplay_rules_snapshot", "real_execution_profile", "owner_activation",
    "controller_query_runtime", "ownership_runtime", "permanent_control_runtime", "spell_control_runtime",
    "token_runtime", "mana_ability_control", "trigger_control", "delayed_trigger_control", "emblem_control",
    "planar_controller", "vanguard_control", "scheme_control", "conspiracy_control", "casual_variant_runtime",
    "mana_triggers_stack_priority_casting_resolving_state_based_actions_multiplayer",
    "card_effect_semantics", "real_card_semantics", "oracle_ingestion", "simulation",
    "general_cr_parser", "recursive_projection", "full_semantic_closure", "source_correction",
    "source_prose_retention_or_redistribution",
)
