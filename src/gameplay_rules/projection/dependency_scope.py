"""Fixed authored scope for twelve review-only foundational dependencies.

Only the allowlisted source units receive descriptions. Boundary records are
closure questions, not projections of their referenced rules or authorities.
No source wording, examples, runtime behavior, or policy documents are stored.
"""
from types import MappingProxyType


SELECTED_REFERENCES = (
    "104.3a", "111.2", "112.2", "112.2a", "113.10", "113.10a",
    "113.10b", "113.10c", "407.1", "407.2", "407.3", "407.4",
)
DEPENDENCY_SELECTED_REFERENCES = SELECTED_REFERENCES


def _freeze(value):
    if isinstance(value, dict):
        return MappingProxyType({key: _freeze(item) for key, item in value.items()})
    if isinstance(value, list):
        return tuple(_freeze(item) for item in value)
    return value


def _dependency(reference, classification="PROJECTED_RULE", status="PROJECTED_FOR_REVIEW"):
    if classification == "PROJECTED_RULE" and reference in {"102.1", "108.3", "400.1"}:
        status = "PROJECTED_IN_FOUNDATIONAL"
    return {"reference": reference, "classification": classification, "status": status}


def _open(reference, classification="FUTURE_SEMANTIC_PRIMITIVE"):
    return _dependency(reference, classification,
                       "UNRESOLVED" if classification == "UNRESOLVED_RULE" else "OUT_OF_SCOPE")


def _rule(topic, paraphrase, semantic_category, tags, dependencies, unresolved, boundaries, limitations):
    return {
        "topic": topic, "paraphrase": paraphrase, "semantic_category": semantic_category,
        "concept_tags": tags, "dependencies": dependencies, "unresolved_dependencies": unresolved,
        "exception_subrule_boundaries": boundaries, "limitations": limitations,
        "coverage_state": "SEMANTIC_CLOSURE_OPEN", "review_state": "PROJECTED_FOR_REVIEW",
    }


def _subrule(reference):
    return {"reference": reference, "relationship": "SELECTED_SUBRULE", "status": "PROJECTED_FOR_REVIEW"}


RULE_CONTENT = _freeze({
    "104.3a": _rule(
        "Voluntary concession boundary",
        "A participant may voluntarily concede at any point. Conceding makes that participant "
        "leave immediately and records their loss.",
        "GAME_ENDING_BOUNDARY", ["concession", "voluntary_choice", "immediate_departure", "loss"],
        [_dependency("102.1")], [_open("concession_transition")], [],
        ["No concession action, priority check, loss transition, or game-ending procedure is implemented.",
         "Multiplayer departure consequences and state-based actions remain outside this scope."]),
    "111.2": _rule(
        "Token creator ownership and entry control",
        "A token belongs to the participant who created it, and its battlefield entry assigns "
        "control to that creator.",
        "OWNERSHIP_AND_CONTROL", ["token", "creator", "owner", "entry_control"],
        [_dependency("102.1"), _dependency("400.1")], [_open("token_creation")], [],
        ["No token creation, token lifecycle, or control-changing behavior is implemented.",
         "Rules 111.1 and 111.3 onward are unprojected; this is not complete token semantics."]),
    "112.2": _rule(
        "Spell ownership and default control",
        "For a spell represented by a card, ownership follows that card. For a copied spell, "
        "ownership follows the participant whose control it entered the stack under. The participant "
        "who placed a spell on the stack normally controls it, and a spell always has a controller.",
        "OWNERSHIP_AND_CONTROL", ["spell", "owner", "controller", "spell_copy", "stack"],
        [_dependency("108.3"), _dependency("400.1")], [_open("spell_copy_and_casting")],
        [_subrule("112.2a")],
        ["No spell casting, stack operation, copying, or control transition is implemented.",
         "The selected ownership subrule does not establish complete copy or casting semantics."]),
    "112.2a": _rule(
        "Ownership of a created card copy with casting permission",
        "If an effect tells a participant to create a card copy and permits that participant to "
        "cast it, the resulting copy belongs to that instructed participant.",
        "OWNERSHIP_EXCEPTION", ["card_copy", "owner", "effect_instruction", "casting_permission"],
        [_dependency("112.2")], [_open("spell_copy_and_casting"), _open("card_effect_interpretation")], [],
        ["No card copying, casting permission evaluation, or casting procedure is implemented.",
         "Rules 707 and 601 are outside the allowlist and receive no projection."]),
    "113.10": _rule(
        "Language for ability changes",
        "An effect may grant an object an ability or take one away. Granting language uses "
        "gains, has, or equivalent wording; removal language uses loses.",
        "ABILITY_MODIFICATION", ["effect", "ability_addition", "ability_removal", "wording_relationship"],
        [], [_open("card_effect_interpretation"), _open("ability_modification")],
        [_subrule("113.10a"), _subrule("113.10b"), _subrule("113.10c")],
        ["The recorded wording relationship is descriptive and provides no effect parser or evaluator.",
         "No general continuous-effect or ability-modification execution is supplied."]),
    "113.10a": _rule(
        "Activation instructions carried by an added ability",
        "When an effect grants an activated ability and supplies instructions for its activation, "
        "those instructions belong to the granted ability.",
        "ABILITY_MODIFICATION", ["activated_ability", "ability_addition", "activation_instructions"],
        [_dependency("113.10")], [_open("ability_activation"), _open("card_effect_interpretation")], [],
        ["No activation, cost, timing, or instruction evaluation is implemented."]),
    "113.10b": _rule(
        "Removal includes repeated instances",
        "Removing a particular ability clears every occurrence of that ability on the affected object.",
        "ABILITY_MODIFICATION", ["ability_removal", "all_instances"],
        [_dependency("113.10")], [_open("ability_modification")], [],
        ["This describes the extent of removal without calculating characteristics or processing layers.",
         "No identity comparison or executable representation of abilities is supplied."]),
    "113.10c": _rule(
        "Ordering boundary for competing ability changes",
        "For competing additions and removals of one ability, recency generally determines which "
        "change applies. This provisional ordering description depends on rule 613.",
        "ABILITY_MODIFICATION_ORDERING", ["ability_addition", "ability_removal", "ordering", "continuous_effect_boundary"],
        [_dependency("113.10")], [_open("613", "UNRESOLVED_RULE"), _open("ability_modification")], [],
        ["Rule 613 is explicitly unresolved and is neither projected nor interpreted here.",
         "Recency is not a complete newest-wins algorithm; ability-modification execution stays blocked.",
         "No layer or continuous-effect evaluator is implemented."]),
    "407.1": _rule(
        "Optional legacy Ante variation and separate authority",
        "Ante is an optional legacy way to play involving stakes. Its availability is constrained "
        "by applicable law and separate rules, and tournament policy prohibits the variation.",
        "VARIANT_AND_POLICY_BOUNDARY", ["ante", "optional_variant", "legacy", "external_policy"],
        [], [_open("ante_variant", "UNSUPPORTED_VARIANT"),
             _open("tournament_policy", "EXTERNAL_POLICY"), _open("applicable_law", "EXTERNAL_POLICY")], [],
        ["This is descriptive source-rule context, not a legal conclusion or policy clearance.",
         "Tournament rules and legal materials are not ingested; their authority is separate from gameplay.",
         "Ante execution is unsupported."]),
    "407.2": _rule(
        "Ante setup, visibility, and ownership consequence",
        "In an Ante game, every participant randomly contributes a deck card to the ante zone after the starting "
        "player is determined and before opening draws. Ante cards are inspectable by all "
        "participants; when the game ends, its winner acquires ownership of the Ante cards.",
        "VARIANT_DESCRIPTIVE_PROCEDURE", ["ante", "setup", "random_selection", "visibility", "ownership_transfer"],
        [_dependency("407.1"), _dependency("108.3"), _dependency("400.1")],
        [_open("ante_variant", "UNSUPPORTED_VARIANT"), _open("ante_state_and_ownership"),
         _open("zone_inspection")], [],
        ["No random selection, setup, winner determination, real ownership transfer, or Ante state is implemented.",
         "The description does not establish permission to run the variation or resolve legal ownership."]),
    "407.3": _rule(
        "Special-card restriction in the Ante variation",
        "Only cards bearing the specified instruction to exclude them from non-Ante play can "
        "change Ante-zone membership or card ownership. Outside Ante play those cards are excluded "
        "from decks and sideboards and cannot enter from outside the game.",
        "VARIANT_CARD_RESTRICTION", ["ante", "special_card_restriction", "deck_boundary", "outside_game"],
        [_dependency("407.1")], [_open("ante_variant", "UNSUPPORTED_VARIANT"),
             _open("deck_policy", "EXTERNAL_POLICY"), _open("card_effect_interpretation")], [],
        ["No real cards, card wording, deck-legality engine, or sideboard checks are supplied.",
         "The source-rule restriction remains descriptive; deck and tournament policy are separate authorities."]),
    "407.4": _rule(
        "Ante action meaning and owner restriction",
        "Anteing an object describes moving it from its current location into the ante zone. Only the "
        "participant who owns that object may perform that action on it.",
        "VARIANT_ACTION_BOUNDARY", ["ante", "zone_movement", "owner_restriction"],
        [_dependency("407.1"), _dependency("108.3"), _dependency("400.1")],
        [_open("ante_variant", "UNSUPPORTED_VARIANT"), _open("ante_state_and_ownership")], [],
        ["No Ante action, move validation, ownership runtime, or legal conclusion is implemented."]),
})

NEW_BOUNDARIES = _freeze([
    _open("613", "UNRESOLVED_RULE"),
    _open("tournament_policy", "EXTERNAL_POLICY"),
    _open("applicable_law", "EXTERNAL_POLICY"),
    _open("deck_policy", "EXTERNAL_POLICY"),
    _open("ante_variant", "UNSUPPORTED_VARIANT"),
    _open("concession_transition"), _open("token_creation"), _open("spell_copy_and_casting"),
    _open("card_effect_interpretation"), _open("ability_activation"),
    _open("ability_modification"), _open("ante_state_and_ownership"), _open("zone_inspection"),
])

_FOUNDATIONAL_REFERENCES = ("102.1", "108.3", "400.1")
GRAPH_NODES = _freeze([
    {"reference": reference, "classification": "PROJECTED_RULE", "status": "PROJECTED_FOR_REVIEW"}
    for reference in SELECTED_REFERENCES
] + [
    {"reference": reference, "classification": "PROJECTED_RULE", "status": "PROJECTED_IN_FOUNDATIONAL"}
    for reference in _FOUNDATIONAL_REFERENCES
] + list(NEW_BOUNDARIES))

GRAPH_EDGES = _freeze([
    {"from_reference": reference, "to_reference": entry["reference"],
     "relation": "DEPENDS_ON", "classification": entry["classification"], "status": entry["status"]}
    for reference in SELECTED_REFERENCES
    for field in ("dependencies", "unresolved_dependencies")
    for entry in RULE_CONTENT[reference][field]
] + [
    {"from_reference": reference, "to_reference": entry["reference"],
     "relation": "SELECTED_SUBRULE", "classification": "PROJECTED_RULE", "status": entry["status"]}
    for reference in SELECTED_REFERENCES
    for entry in RULE_CONTENT[reference]["exception_subrule_boundaries"]
])

UNSUPPORTED_DIMENSIONS = (
    "real_execution", "real_gameplay_rules_snapshot", "real_execution_profile", "owner_activation",
    "ownership_runtime", "spell_control_runtime", "token_runtime", "concession_runtime",
    "ability_modification_runtime", "ante_runtime", "continuous_effect_evaluation",
    "card_effect_semantics", "real_card_semantics", "oracle_ingestion", "tournament_policy_ingestion",
    "legal_conclusions", "deck_legality_engine", "mana_priority_casting_layers_state_based_actions",
    "simulation", "general_cr_parser", "recursive_projection", "full_semantic_closure",
    "deferred_exception_interpretation", "source_prose_retention_or_redistribution",
)
