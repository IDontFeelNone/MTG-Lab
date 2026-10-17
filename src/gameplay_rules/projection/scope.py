"""Project-authored scope for the non-executable foundational projection.

Only the twenty named source units are projected. Graph placeholders record
known boundaries without importing, paraphrasing, or resolving their content.
The graph is a reviewed local dependency record, not a claim of full closure.
"""

SELECTED_REFERENCES = (
    "101.1", "101.2", "101.2a", "101.3", "102.1", "102.2",
    "108.1", "108.3", "108.4", "108.4a", "109.1", "109.3", "109.4",
    "110.1", "110.2", "110.2a", "400.1", "400.2", "400.3", "400.7",
)

RULE_CONTENT = {
    "101.1": {
        "topic": "Local precedence of card wording",
        "paraphrase": (
            "A direct conflict between a card's wording and a general rule is "
            "settled in favor of the card for that particular circumstance. "
            "Concession is a protected exception to this precedence."
        ),
        "limitations": [
            "The concession dependency at 104.3a remains unresolved.",
            "This record supplies neither card interpretation nor a conflict resolver.",
        ],
        "concept_tags": ["precedence", "card_wording", "concession_boundary"],
    },
    "101.2": {
        "topic": "Prohibitions in conflicts",
        "paraphrase": (
            "If an effect prohibits an action that a rule or another effect "
            "permits or requires, the prohibition wins that conflict. The "
            "ability modification boundary is recorded separately at 101.2a."
        ),
        "limitations": [
            "Ability addition and removal cannot be resolved by this priority statement.",
            "No effect evaluation or executable permission decision is provided.",
        ],
        "concept_tags": ["precedence", "permission", "prohibition"],
    },
    "101.2a": {
        "topic": "Ability modification boundary",
        "paraphrase": (
            "Giving an object an ability and taking an ability away lie outside "
            "the permission-versus-prohibition priority described by 101.2."
        ),
        "limitations": [
            "The relevant ability interaction dependency at 113.10 remains unresolved.",
            "This exception does not define how ability modifications interact.",
        ],
        "concept_tags": ["ability_modification", "precedence_exception"],
    },
    "101.3": {
        "topic": "Instructions that cannot be completed",
        "paraphrase": (
            "An instruction's unachievable portions are skipped. A consequence "
            "written on the card may still apply; absent such a consequence, "
            "the skipped portion produces no result."
        ),
        "limitations": [
            "Feasibility, instruction parsing, and card-specific consequences are not evaluated.",
        ],
        "concept_tags": ["instructions", "impossibility", "partial_completion"],
    },
    "102.1": {
        "topic": "Participant and turn roles",
        "paraphrase": (
            "A game participant is a player. The participant taking the "
            "current turn has the active role, while every remaining "
            "participant has a nonactive role."
        ),
        "limitations": [
            "Turn advancement and priority procedures are outside this projection.",
        ],
        "concept_tags": ["player", "active_player", "nonactive_player"],
    },
    "102.2": {
        "topic": "Opponent in a two-person game",
        "paraphrase": (
            "For a game with two participants, each participant treats the "
            "other one as their opponent."
        ),
        "limitations": [
            "Multiplayer and team opponent relationships are not projected.",
        ],
        "concept_tags": ["player", "opponent", "two_player_scope"],
    },
    "108.1": {
        "topic": "Authority for card wording",
        "paraphrase": (
            "The wording assigned to a card is determined from its Oracle "
            "reference, which is available through Wizards' Gatherer service."
        ),
        "limitations": [
            "This is an authority reference only; no Oracle content is acquired or interpreted.",
            "No real Card semantics are supplied.",
        ],
        "concept_tags": ["card_wording", "oracle_authority", "external_data_boundary"],
    },
    "108.3": {
        "topic": "Ownership assigned by game origin",
        "paraphrase": (
            "A card's game owner is the participant whose starting deck "
            "contained it, the participant who introduced it from outside "
            "the game, or the participant who placed it in the command zone "
            "for the start. Real-world legal title ordinarily has no "
            "game-rules significance; ante is an exception governed outside "
            "this subset."
        ),
        "limitations": [
            "The ante reference at 407 remains unresolved.",
            "This ownership description supplies no deck, command-zone setup, or outside-game procedure.",
        ],
        "concept_tags": ["card_owner", "starting_deck", "outside_game", "command_zone", "ante_boundary"],
    },
    "108.4": {
        "topic": "When a card has control information",
        "paraphrase": (
            "A card has control information only when it is serving as a "
            "permanent or a spell. The corresponding permanent or spell "
            "rules determine who controls it."
        ),
        "limitations": [
            "Permanent control is represented only by the selected 110.2 and 110.2a records.",
            "Spell control at 112.2 remains unresolved.",
        ],
        "concept_tags": ["card_controller", "permanent", "spell_boundary"],
    },
    "108.4a": {
        "topic": "Owner fallback for a controller query",
        "paraphrase": (
            "When a request needs the controller of a card that has none, "
            "the answer uses that card's owner instead."
        ),
        "limitations": [
            "The fallback answers the request; it does not give the card a controller.",
        ],
        "concept_tags": ["card_controller", "card_owner", "query_fallback"],
    },
    "109.1": {
        "topic": "Kinds covered by the object vocabulary",
        "paraphrase": (
            "The object category covers a card, a card copy, a token, a "
            "spell, a permanent, an emblem, and an ability while on the stack."
        ),
        "limitations": [
            "Listing an object kind does not implement its behavior or project its defining rules.",
        ],
        "concept_tags": ["object", "card", "card_copy", "token", "spell", "permanent", "emblem", "stack_ability"],
    },
    "109.3": {
        "topic": "Characteristics vocabulary",
        "paraphrase": (
            "An object can carry some or all of the characteristic labels "
            "enumerated here as data tags. Information outside that "
            "vocabulary belongs to other categories: who owns or controls "
            "the object, its tapped condition, its chosen targets, and an "
            "Aura's attachment relationship are examples."
        ),
        "limitations": [
            "These are descriptive data labels, not implemented card attributes or behavior.",
            "No characteristic calculation, state transition, targeting, or attachment semantics are projected.",
        ],
        "concept_tags": [
            "characteristics", "name", "mana_cost", "color", "color_indicator",
            "card_type", "subtype", "supertype", "rules_text", "abilities",
            "power", "toughness", "loyalty", "defense", "hand_modifier", "life_modifier",
            "owner_is_separate", "controller_is_separate", "state_is_separate",
        ],
    },
    "109.4": {
        "topic": "Zone boundary for object control",
        "paraphrase": (
            "The baseline model assigns controllers only to objects in the "
            "stack or battlefield zones; objects elsewhere have no "
            "controller under that baseline. The listed subordinate "
            "exceptions remain outside this projection."
        ),
        "limitations": [
            "Rules 109.4a through 109.4g remain individually recorded, unprojected exceptions.",
            "The baseline must not be treated as a complete controller lookup policy.",
        ],
        "concept_tags": ["object_controller", "stack", "battlefield", "incomplete_exception_boundary"],
    },
    "110.1": {
        "topic": "Permanent membership and duration",
        "paraphrase": (
            "A battlefield card or token qualifies as a permanent for its "
            "stay there, with no inherent time limit. Entering that zone "
            "establishes this status; leaving it ends the status."
        ),
        "limitations": [
            "Zone movement and token lifecycle behavior are not implemented.",
        ],
        "concept_tags": ["permanent", "battlefield", "card", "token", "zone_membership"],
    },
    "110.2": {
        "topic": "Permanent ownership and default control",
        "paraphrase": (
            "A permanent represented by a card uses that card's owner. "
            "Token ownership has a separate dependency. Every permanent "
            "has a controller, initially the participant whose control it "
            "entered under unless a relevant instruction changes that default."
        ),
        "limitations": [
            "Token ownership at 111.2 remains unresolved.",
            "Later control changes and continuous-effect interactions are outside the selected subset.",
        ],
        "concept_tags": ["permanent_owner", "permanent_controller", "entry_control", "token_ownership_boundary"],
    },
    "110.2a": {
        "topic": "Control from a battlefield placement instruction",
        "paraphrase": (
            "When an effect directs a participant to place an object into "
            "the battlefield, that participant receives control on entry "
            "by default. A different control assignment in the effect "
            "takes priority over that default."
        ),
        "limitations": [
            "No placement instruction is parsed or executed.",
            "This entry default does not resolve other control-changing rules.",
        ],
        "concept_tags": ["entry_control", "effect_instruction", "default_override"],
    },
    "400.1": {
        "topic": "Zone inventory and sharing",
        "paraphrase": (
            "Each participant has a separate graveyard, library, and hand. "
            "Battlefield, command, exile, and stack are common locations. "
            "These form the ordinary seven-location inventory; older cards "
            "can also involve ante, a shared location."
        ),
        "limitations": [
            "The inventory does not implement any zone, ante procedure, or movement operation.",
        ],
        "concept_tags": ["zone", "library", "hand", "battlefield", "graveyard", "stack", "exile", "command", "ante", "shared_zone", "player_zone"],
    },
    "400.2": {
        "topic": "Zone visibility categories",
        "paraphrase": (
            "The public category covers command and exile, the stack and "
            "battlefield, and graveyards plus ante. This category normally "
            "lets every participant inspect a card's face, while specific "
            "face-down permissions create exceptions. Hand and library stay "
            "in the hidden category even when their entire contents have "
            "been revealed."
        ),
        "limitations": [
            "Face-down permissions and reveal procedures are outside this projection.",
            "Zone category alone cannot determine an individual card's visibility.",
        ],
        "concept_tags": ["public_zone", "hidden_zone", "face_down_boundary", "revealed_hidden_zone"],
    },
    "400.3": {
        "topic": "Owner-specific destination correction",
        "paraphrase": (
            "A proposed move into another participant's library, hand, or "
            "graveyard uses the matching location belonging to the object's "
            "owner instead."
        ),
        "limitations": [
            "This describes a destination constraint without executing or validating a move.",
        ],
        "concept_tags": ["zone_destination", "owner", "library", "hand", "graveyard"],
    },
    "400.7": {
        "topic": "Identity boundary across zones",
        "paraphrase": (
            "Crossing between zones ordinarily starts a fresh object "
            "identity, without carrying a link to the prior identity or "
            "its history. The selected record leaves the enumerated "
            "exception cases unprojected."
        ),
        "limitations": [
            "Rules 400.7a through 400.7k and 400.7m remain individually recorded, unprojected exceptions.",
            "The baseline cannot be used as a complete zone-change identity algorithm.",
        ],
        "concept_tags": ["zone_change", "object_identity", "incomplete_exception_boundary"],
    },
}

_UNRESOLVED_REFERENCES = ("104.3a", "111.2", "112.2", "113.10", "407")
_CONTROL_EXCEPTIONS = tuple(f"109.4{letter}" for letter in "abcdefg")
_ZONE_CHANGE_EXCEPTIONS = tuple(f"400.7{letter}" for letter in "abcdefghijkm")

GRAPH_NODES = [
    {"rule_reference": reference, "status": "PROJECTED"}
    for reference in SELECTED_REFERENCES
] + [
    {"rule_reference": reference, "status": "UNRESOLVED"}
    for reference in _UNRESOLVED_REFERENCES
] + [
    {"rule_reference": reference, "status": "UNPROJECTED_EXCEPTION"}
    for reference in _CONTROL_EXCEPTIONS + _ZONE_CHANGE_EXCEPTIONS
]

GRAPH_EDGES = [
    {"from_reference": "101.1", "to_reference": "104.3a", "relation": "EXCEPTION", "status": "UNRESOLVED"},
    {"from_reference": "101.2", "to_reference": "101.2a", "relation": "EXCEPTION", "status": "PROJECTED"},
    {"from_reference": "101.2a", "to_reference": "101.2", "relation": "DEPENDS_ON", "status": "PROJECTED"},
    {"from_reference": "101.2a", "to_reference": "113.10", "relation": "REFERENCES", "status": "UNRESOLVED"},
    {"from_reference": "102.2", "to_reference": "102.1", "relation": "DEPENDS_ON", "status": "PROJECTED"},
    {"from_reference": "108.3", "to_reference": "102.1", "relation": "DEPENDS_ON", "status": "PROJECTED"},
    {"from_reference": "108.3", "to_reference": "407", "relation": "REFERENCES", "status": "UNRESOLVED"},
    {"from_reference": "108.4", "to_reference": "110.2", "relation": "REFERENCES", "status": "PROJECTED"},
    {"from_reference": "108.4", "to_reference": "112.2", "relation": "REFERENCES", "status": "UNRESOLVED"},
    {"from_reference": "108.4a", "to_reference": "108.4", "relation": "DEPENDS_ON", "status": "PROJECTED"},
    {"from_reference": "108.4a", "to_reference": "108.3", "relation": "DEPENDS_ON", "status": "PROJECTED"},
    {"from_reference": "109.3", "to_reference": "109.1", "relation": "DEPENDS_ON", "status": "PROJECTED"},
    {"from_reference": "109.4", "to_reference": "109.1", "relation": "DEPENDS_ON", "status": "PROJECTED"},
    {"from_reference": "109.4", "to_reference": "108.4", "relation": "REFERENCES", "status": "PROJECTED"},
    {"from_reference": "109.4", "to_reference": "400.1", "relation": "DEPENDS_ON", "status": "PROJECTED"},
    {"from_reference": "110.1", "to_reference": "109.1", "relation": "DEPENDS_ON", "status": "PROJECTED"},
    {"from_reference": "110.1", "to_reference": "400.1", "relation": "DEPENDS_ON", "status": "PROJECTED"},
    {"from_reference": "110.2", "to_reference": "110.1", "relation": "DEPENDS_ON", "status": "PROJECTED"},
    {"from_reference": "110.2", "to_reference": "108.3", "relation": "DEPENDS_ON", "status": "PROJECTED"},
    {"from_reference": "110.2", "to_reference": "111.2", "relation": "REFERENCES", "status": "UNRESOLVED"},
    {"from_reference": "110.2a", "to_reference": "110.2", "relation": "DEPENDS_ON", "status": "PROJECTED"},
    {"from_reference": "400.1", "to_reference": "109.1", "relation": "DEPENDS_ON", "status": "PROJECTED"},
    {"from_reference": "400.2", "to_reference": "400.1", "relation": "DEPENDS_ON", "status": "PROJECTED"},
    {"from_reference": "400.3", "to_reference": "400.1", "relation": "DEPENDS_ON", "status": "PROJECTED"},
    {"from_reference": "400.3", "to_reference": "108.3", "relation": "DEPENDS_ON", "status": "PROJECTED"},
    {"from_reference": "400.7", "to_reference": "400.1", "relation": "DEPENDS_ON", "status": "PROJECTED"},
    {"from_reference": "400.7", "to_reference": "109.1", "relation": "DEPENDS_ON", "status": "PROJECTED"},
] + [
    {"from_reference": "109.4", "to_reference": reference, "relation": "EXCEPTION", "status": "UNPROJECTED_EXCEPTION"}
    for reference in _CONTROL_EXCEPTIONS
] + [
    {"from_reference": "400.7", "to_reference": reference, "relation": "EXCEPTION", "status": "UNPROJECTED_EXCEPTION"}
    for reference in _ZONE_CHANGE_EXCEPTIONS
]

UNSUPPORTED_DIMENSIONS = (
    "executable_rules",
    "real_gameplay_rules_snapshot",
    "real_execution_profile",
    "gameplay_rules_engine_changes",
    "fictional_execution_profile_changes",
    "oracle_ingestion",
    "real_card_semantics",
    "mana_processing",
    "turn_timing_and_priority",
    "casting_procedures",
    "state_based_actions",
    "simulation",
    "general_or_full_comprehensive_rules_parser",
    "full_dependency_closure",
    "unprojected_exception_interpretation",
    "source_prose_retention_or_redistribution",
)
