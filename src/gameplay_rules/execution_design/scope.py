"""Project-authored review scope for a future, inactive real-rules profile.

This data reviews the retained foundational projection; it adds no projected
rules and supplies no executable semantics. Primitive identifiers below name
future contracts, not available implementations. Nothing here authorizes
execution or changes the fictional runtime.
"""

from gameplay_rules.projection.scope import SELECTED_REFERENCES


DESIGN_VERSION = "real-rules-execution-profile-design-v1"
PROFILE_TARGET = "magic-comprehensive-rules-20260925-v1"
FUTURE_ENGINE_TARGET = "gameplay-real-rules-kernel-v1"


RULE_REVIEW_CONTENT = {
    "101.1": {
        "semantic_roles": [
            "PRECEDENCE_SEMANTIC", "BLOCKED_BY_DEPENDENCY",
            "BLOCKED_BY_EXCEPTION_SET",
        ],
        "semantic_role": "Local precedence subject to an unresolved exception",
        "direct_runtime_relevance": "FUTURE_PRECEDENCE",
        "state_model_relevance": False,
        "state_model_candidate": False,
        "required_semantic_primitives": [
            "real_rule_conflict_descriptor_v1",
            "real_card_text_semantics_v1",
            "real_scoped_precedence_evaluation_v1",
        ],
        "unknown_semantic_contexts": [
            "card_text_conflict_interpretation",
            "unresolved_concession_exception",
        ],
        "explanation": (
            "104.3a is unresolved, and executable Card-text semantics do not "
            "exist. This review cannot justify a universal card-overrides-rule "
            "primitive. The precedence relationship remains design evidence only."
        ),
    },
    "101.2": {
        "semantic_roles": [
            "PRECEDENCE_SEMANTIC", "BLOCKED_BY_DEPENDENCY",
            "BLOCKED_BY_EXCEPTION_SET",
        ],
        "semantic_role": "Permission/prohibition conflict boundary",
        "direct_runtime_relevance": "FUTURE_PRECEDENCE",
        "state_model_relevance": False,
        "state_model_candidate": False,
        "required_semantic_primitives": [
            "real_effect_permission_descriptor_v1",
            "real_prohibition_conflict_evaluation_v1",
            "real_ability_modification_boundary_v1",
        ],
        "unknown_semantic_contexts": [
            "structured_effect_interpretation",
            "ability_modification_interaction",
        ],
        "explanation": (
            "A future scoped precedence contract may be modelable, but 101.2a "
            "is a separately identified ability-modification exception. Its "
            "unresolved 113.10 dependency prevents treating this projection "
            "as a complete conflict resolver."
        ),
    },
    "101.2a": {
        "semantic_roles": ["PRECEDENCE_SEMANTIC", "BLOCKED_BY_DEPENDENCY"],
        "semantic_role": "Boundary on the applicability of precedence",
        "direct_runtime_relevance": "FUTURE_PRECEDENCE",
        "state_model_relevance": False,
        "state_model_candidate": False,
        "required_semantic_primitives": ["real_ability_modification_boundary_v1"],
        "unknown_semantic_contexts": ["ability_modification_interaction"],
        "explanation": (
            "113.10 remains unresolved. Recognizing an exception category "
            "does not supply the interaction semantics needed to execute it "
            "or to close the 101.2 precedence boundary."
        ),
    },
    "101.3": {
        "semantic_roles": ["EXECUTION_PRIMITIVE_CANDIDATE"],
        "semantic_role": "Instruction feasibility and partial completion",
        "direct_runtime_relevance": "FUTURE_PRIMITIVE",
        "state_model_relevance": False,
        "state_model_candidate": False,
        "required_semantic_primitives": [
            "real_structured_instruction_descriptor_v1",
            "real_instruction_feasibility_evaluation_v1",
            "real_instruction_consequence_evaluation_v1",
        ],
        "unknown_semantic_contexts": [
            "action_feasibility",
            "partial_instruction_completion",
            "card_specific_instruction_consequences",
        ],
        "explanation": (
            "No generic impossible-instruction executor exists. An action "
            "model, structured instruction semantics, and consequence "
            "evaluation are prerequisites; this projection alone cannot "
            "determine an action's outcome."
        ),
    },
    "102.1": {
        "semantic_roles": ["STATE_MODEL_SEMANTIC"],
        "semantic_role": "Player identity and turn-role vocabulary",
        "direct_runtime_relevance": "FUTURE_STATE_MODEL",
        "state_model_relevance": True,
        "state_model_candidate": True,
        "required_semantic_primitives": ["real_player_role_descriptor_v1"],
        "unknown_semantic_contexts": [],
        "explanation": (
            "The selected vocabulary is a descriptive future state-model "
            "candidate. It supplies no turn advancement or priority behavior, "
            "and no real state contract is implemented or activated."
        ),
    },
    "102.2": {
        "semantic_roles": ["STATE_MODEL_SEMANTIC"],
        "semantic_role": "Two-player opponent relationship",
        "direct_runtime_relevance": "FUTURE_STATE_MODEL",
        "state_model_relevance": True,
        "state_model_candidate": True,
        "required_semantic_primitives": ["real_two_player_relationship_descriptor_v1"],
        "unknown_semantic_contexts": [],
        "explanation": (
            "This descriptive state-model candidate depends on 102.1 and is "
            "limited to a two-player context. It neither infers multiplayer "
            "relationships nor activates a real-rules relationship query."
        ),
    },
    "108.1": {
        "semantic_roles": ["REFERENCE_ONLY"],
        "semantic_role": "External authority for Card wording",
        "direct_runtime_relevance": "NONE",
        "state_model_relevance": False,
        "state_model_candidate": False,
        "required_semantic_primitives": [],
        "unknown_semantic_contexts": [],
        "explanation": (
            "This is source-authority metadata only and must never become "
            "executable gameplay behavior. It authorizes no Oracle ingestion, "
            "Gatherer access, Card parsing, or real Card semantics."
        ),
    },
    "108.3": {
        "semantic_roles": ["STATE_MODEL_SEMANTIC", "BLOCKED_BY_DEPENDENCY"],
        "semantic_role": "Ownership provenance in the game state",
        "direct_runtime_relevance": "FUTURE_STATE_MODEL",
        "state_model_relevance": True,
        "state_model_candidate": False,
        "required_semantic_primitives": [
            "real_ownership_provenance_descriptor_v1",
            "real_game_start_provenance_descriptor_v1",
            "real_outside_game_provenance_descriptor_v1",
        ],
        "unknown_semantic_contexts": [
            "game_start_ownership_provenance",
            "outside_game_ownership_provenance",
            "ante_ownership_boundary",
        ],
        "explanation": (
            "407 remains an unresolved ante dependency. Complete game-start, "
            "command-zone setup, and outside-game provenance semantics are "
            "also absent. A universal ownership query would therefore be "
            "incomplete and unsafe to activate."
        ),
    },
    "108.4": {
        "semantic_roles": ["STATE_MODEL_SEMANTIC", "BLOCKED_BY_DEPENDENCY"],
        "semantic_role": "Card control eligibility and provenance",
        "direct_runtime_relevance": "FUTURE_STATE_MODEL",
        "state_model_relevance": True,
        "state_model_candidate": False,
        "required_semantic_primitives": [
            "real_card_control_descriptor_v1",
            "real_permanent_control_descriptor_v1",
            "real_spell_control_descriptor_v1",
        ],
        "unknown_semantic_contexts": [
            "spell_control",
            "token_ownership",
            "later_control_changes",
        ],
        "explanation": (
            "112.2 spell control remains unresolved. The selected 110.2 "
            "permanent context supplies only partial context and itself "
            "depends on unresolved ownership semantics. No complete Card "
            "control query can be implemented from this subset."
        ),
    },
    "108.4a": {
        "semantic_roles": [
            "STATE_MODEL_SEMANTIC", "EXECUTION_PRIMITIVE_CANDIDATE",
            "BLOCKED_BY_DEPENDENCY",
        ],
        "semantic_role": "Controller-query fallback without control assignment",
        "direct_runtime_relevance": "FUTURE_PRIMITIVE",
        "state_model_relevance": True,
        "state_model_candidate": False,
        "required_semantic_primitives": [
            "real_card_control_descriptor_v1",
            "real_ownership_provenance_descriptor_v1",
            "real_controller_query_fallback_v1",
        ],
        "unknown_semantic_contexts": ["complete_ownership_and_control_queries"],
        "explanation": (
            "The fallback depends on 108.3 and 108.4; both remain incomplete. "
            "A fallback result is not a control-changing operation. It must "
            "remain non-executable until ownership and control prerequisites "
            "and their transitive dependencies are closed."
        ),
    },
    "109.1": {
        "semantic_roles": ["STATE_MODEL_SEMANTIC"],
        "semantic_role": "Object taxonomy vocabulary",
        "direct_runtime_relevance": "FUTURE_STATE_MODEL",
        "state_model_relevance": True,
        "state_model_candidate": True,
        "required_semantic_primitives": ["real_object_taxonomy_descriptor_v1"],
        "unknown_semantic_contexts": [],
        "explanation": (
            "The object vocabulary is a descriptive future state-model "
            "candidate. Naming an object kind implements neither its "
            "lifecycle nor its behavior; no real object runtime is created."
        ),
    },
    "109.3": {
        "semantic_roles": ["STATE_MODEL_SEMANTIC"],
        "semantic_role": "Characteristic labels separated from other state",
        "direct_runtime_relevance": "FUTURE_STATE_MODEL",
        "state_model_relevance": True,
        "state_model_candidate": True,
        "required_semantic_primitives": ["real_characteristic_vocabulary_descriptor_v1"],
        "unknown_semantic_contexts": [],
        "explanation": (
            "Characteristic labels can inform a descriptive future data "
            "contract. This candidate provides no characteristic calculation, "
            "layer evaluation, real Card parsing, or ability semantics. "
            "Vocabulary coverage must not be reported as behavioral coverage."
        ),
    },
    "109.4": {
        "semantic_roles": [
            "STATE_MODEL_SEMANTIC", "BLOCKED_BY_DEPENDENCY",
            "BLOCKED_BY_EXCEPTION_SET",
        ],
        "semantic_role": "Object-control baseline with an open exception family",
        "direct_runtime_relevance": "FUTURE_STATE_MODEL",
        "state_model_relevance": True,
        "state_model_candidate": False,
        "required_semantic_primitives": ["real_object_control_query_v1"],
        "unknown_semantic_contexts": ["unprojected_control_exceptions"],
        "explanation": (
            "109.4a, 109.4b, 109.4c, 109.4d, 109.4e, 109.4f, and 109.4g "
            "remain unprojected exceptions. Their open closure must block "
            "baseline controller lookup. Selected supporting control rules "
            "also have unresolved dependencies; the baseline is not a "
            "complete controller algorithm."
        ),
    },
    "110.1": {
        "semantic_roles": ["STATE_MODEL_SEMANTIC"],
        "semantic_role": "Permanent identity and battlefield membership",
        "direct_runtime_relevance": "FUTURE_STATE_MODEL",
        "state_model_relevance": True,
        "state_model_candidate": True,
        "required_semantic_primitives": ["real_permanent_membership_descriptor_v1"],
        "unknown_semantic_contexts": ["token_lifecycle"],
        "explanation": (
            "Permanent membership is a descriptive future state-model "
            "candidate. Token lifecycle and zone movement semantics remain "
            "incomplete. The candidate cannot create permanents, move "
            "objects, or imply that token behavior has been implemented."
        ),
    },
    "110.2": {
        "semantic_roles": [
            "STATE_MODEL_SEMANTIC", "EXECUTION_PRIMITIVE_CANDIDATE",
            "BLOCKED_BY_DEPENDENCY",
        ],
        "semantic_role": "Permanent ownership and initial control context",
        "direct_runtime_relevance": "FUTURE_STATE_MODEL",
        "state_model_relevance": True,
        "state_model_candidate": False,
        "required_semantic_primitives": [
            "real_ownership_provenance_descriptor_v1",
            "real_token_ownership_descriptor_v1",
            "real_permanent_control_descriptor_v1",
            "real_entry_control_assignment_v1",
        ],
        "unknown_semantic_contexts": [
            "token_ownership",
            "later_control_changes",
            "continuous_effect_control_interactions",
        ],
        "explanation": (
            "111.2 token ownership remains unresolved. The selected ownership "
            "dependency is also incomplete, and later control-changing "
            "semantics lie outside this subset. A partial description does "
            "not establish complete ownership or control behavior."
        ),
    },
    "110.2a": {
        "semantic_roles": [
            "STATE_MODEL_SEMANTIC", "EXECUTION_PRIMITIVE_CANDIDATE",
            "BLOCKED_BY_DEPENDENCY",
        ],
        "semantic_role": "Effect-directed entry-control candidate",
        "direct_runtime_relevance": "FUTURE_PRIMITIVE",
        "state_model_relevance": True,
        "state_model_candidate": False,
        "required_semantic_primitives": [
            "real_structured_effect_instruction_descriptor_v1",
            "real_entry_control_assignment_v1",
            "real_explicit_control_override_v1",
        ],
        "unknown_semantic_contexts": [
            "structured_effect_instructions",
            "explicit_entry_control_overrides",
        ],
        "explanation": (
            "No structured effect instruction system exists. Entry-control "
            "defaults cannot be executed without that system, explicit "
            "override semantics, and closure of 110.2 and its dependencies."
        ),
    },
    "400.1": {
        "semantic_roles": ["STATE_MODEL_SEMANTIC"],
        "semantic_role": "Zone taxonomy and participant/shared-zone descriptors",
        "direct_runtime_relevance": "FUTURE_STATE_MODEL",
        "state_model_relevance": True,
        "state_model_candidate": True,
        "required_semantic_primitives": ["real_zone_taxonomy_descriptor_v1"],
        "unknown_semantic_contexts": ["ante_zone_support"],
        "explanation": (
            "The ordinary zone inventory is a descriptive future state-model "
            "candidate. Ante remains outside ordinary support. Taxonomy "
            "does not implement zone operations, zone movement, or a "
            "complete game state."
        ),
    },
    "400.2": {
        "semantic_roles": [
            "STATE_MODEL_SEMANTIC", "EXECUTION_PRIMITIVE_CANDIDATE",
            "BLOCKED_BY_EXCEPTION_SET",
        ],
        "semantic_role": "Zone visibility categories with unmodeled exceptions",
        "direct_runtime_relevance": "FUTURE_PRIMITIVE",
        "state_model_relevance": True,
        "state_model_candidate": False,
        "required_semantic_primitives": [
            "real_zone_visibility_descriptor_v1",
            "real_object_visibility_evaluation_v1",
        ],
        "unknown_semantic_contexts": [
            "face_down_visibility_exceptions",
            "reveal_visibility_semantics",
        ],
        "explanation": (
            "Face-down permissions and reveal semantics remain unmodeled. "
            "Their unknown exception closure prevents a complete visibility "
            "algorithm; zone-category vocabulary alone cannot determine "
            "what a participant may inspect."
        ),
    },
    "400.3": {
        "semantic_roles": [
            "STATE_MODEL_SEMANTIC", "EXECUTION_PRIMITIVE_CANDIDATE",
            "BLOCKED_BY_DEPENDENCY",
        ],
        "semantic_role": "Ownership-sensitive destination candidate",
        "direct_runtime_relevance": "FUTURE_PRIMITIVE",
        "state_model_relevance": True,
        "state_model_candidate": False,
        "required_semantic_primitives": [
            "real_zone_destination_descriptor_v1",
            "real_ownership_provenance_descriptor_v1",
            "real_proposed_move_descriptor_v1",
        ],
        "unknown_semantic_contexts": ["ownership_resolution", "zone_move_semantics"],
        "explanation": (
            "A future destination contract depends on 400.1 and incomplete "
            "108.3 ownership semantics. It cannot validate or perform a "
            "move, and no move executor is authorized by this design."
        ),
    },
    "400.7": {
        "semantic_roles": [
            "STATE_MODEL_SEMANTIC", "EXECUTION_PRIMITIVE_CANDIDATE",
            "BLOCKED_BY_EXCEPTION_SET",
        ],
        "semantic_role": "Zone-change identity boundary with open exceptions",
        "direct_runtime_relevance": "FUTURE_PRIMITIVE",
        "state_model_relevance": True,
        "state_model_candidate": False,
        "required_semantic_primitives": [
            "real_zone_change_identity_evaluation_v1",
            "real_object_history_link_descriptor_v1",
        ],
        "unknown_semantic_contexts": ["unprojected_zone_change_identity_exceptions"],
        "explanation": (
            "400.7a, 400.7b, 400.7c, 400.7d, 400.7e, 400.7f, 400.7g, "
            "400.7h, 400.7i, 400.7j, 400.7k, and 400.7m remain unprojected "
            "exceptions. Their open closure blocks real zone-change identity "
            "behavior; an unconditional new-object algorithm is unsafe."
        ),
    },
}


CAPABILITY_CONTENT = (
    {
        "capability_id": "players",
        "supporting_rules": ["102.1"],
        "semantic_roles": ["STATE_MODEL_SEMANTIC"],
        "notes": "Player and turn-role vocabulary only; no turn or priority execution.",
    },
    {
        "capability_id": "opponent_relationship",
        "supporting_rules": ["102.1", "102.2"],
        "semantic_roles": ["STATE_MODEL_SEMANTIC"],
        "notes": "Descriptive two-player relationship only; multiplayer remains unsupported.",
    },
    {
        "capability_id": "object_taxonomy",
        "supporting_rules": ["109.1"],
        "semantic_roles": ["STATE_MODEL_SEMANTIC"],
        "notes": "Object-kind labels do not implement the behavior of those kinds.",
    },
    {
        "capability_id": "characteristics_vocabulary",
        "supporting_rules": ["109.1", "109.3"],
        "semantic_roles": ["STATE_MODEL_SEMANTIC"],
        "notes": "Characteristic labels only; calculation and layer evaluation are unsupported.",
    },
    {
        "capability_id": "ownership",
        "supporting_rules": ["108.3", "110.2"],
        "semantic_roles": ["STATE_MODEL_SEMANTIC", "BLOCKED_BY_DEPENDENCY"],
        "notes": "407 and 111.2 are unresolved; complete game-start and outside-game provenance is absent.",
    },
    {
        "capability_id": "control",
        "supporting_rules": ["108.4", "108.4a", "109.4", "110.2", "110.2a"],
        "semantic_roles": [
            "STATE_MODEL_SEMANTIC", "EXECUTION_PRIMITIVE_CANDIDATE",
            "BLOCKED_BY_DEPENDENCY", "BLOCKED_BY_EXCEPTION_SET",
        ],
        "notes": "112.2 and ownership dependencies are unresolved; 109.4a-g remain open and effect/control-change semantics are absent.",
    },
    {
        "capability_id": "permanent_identity",
        "supporting_rules": ["109.1", "110.1"],
        "semantic_roles": ["STATE_MODEL_SEMANTIC"],
        "notes": "Descriptive membership candidate only; token lifecycle and zone movement remain incomplete.",
    },
    {
        "capability_id": "zone_taxonomy",
        "supporting_rules": ["109.1", "400.1"],
        "semantic_roles": ["STATE_MODEL_SEMANTIC"],
        "notes": "Ordinary zone vocabulary only; ante support and zone operations are not implemented.",
    },
    {
        "capability_id": "zone_visibility",
        "supporting_rules": ["400.1", "400.2"],
        "semantic_roles": [
            "STATE_MODEL_SEMANTIC", "EXECUTION_PRIMITIVE_CANDIDATE",
            "BLOCKED_BY_EXCEPTION_SET",
        ],
        "notes": "Unmodeled face-down and reveal conditions prevent complete visibility evaluation.",
    },
    {
        "capability_id": "zone_destination",
        "supporting_rules": ["108.3", "400.1", "400.3"],
        "semantic_roles": [
            "STATE_MODEL_SEMANTIC", "EXECUTION_PRIMITIVE_CANDIDATE",
            "BLOCKED_BY_DEPENDENCY",
        ],
        "notes": "Ownership provenance is incomplete and no zone move may execute.",
    },
    {
        "capability_id": "zone_change_identity",
        "supporting_rules": ["109.1", "400.1", "400.7"],
        "semantic_roles": [
            "STATE_MODEL_SEMANTIC", "EXECUTION_PRIMITIVE_CANDIDATE",
            "BLOCKED_BY_EXCEPTION_SET",
        ],
        "notes": "400.7a-k and 400.7m remain open exceptions; no unconditional new-object behavior is permitted.",
    },
    {
        "capability_id": "rule_precedence",
        "supporting_rules": ["101.1", "101.2", "101.2a"],
        "semantic_roles": [
            "PRECEDENCE_SEMANTIC", "BLOCKED_BY_DEPENDENCY",
            "BLOCKED_BY_EXCEPTION_SET",
        ],
        "notes": "104.3a and 113.10 remain unresolved, and executable Card-text/effect semantics are absent.",
    },
    {
        "capability_id": "impossible_instructions",
        "supporting_rules": ["101.3"],
        "semantic_roles": ["EXECUTION_PRIMITIVE_CANDIDATE"],
        "notes": "No instruction model, feasibility evaluator, or consequence executor exists.",
    },
    {
        "capability_id": "source_authority",
        "supporting_rules": ["108.1"],
        "semantic_roles": ["REFERENCE_ONLY"],
        "notes": "Authority metadata is permanently non-executable and supplies no Oracle or Card semantics.",
    },
)


UNSUPPORTED_CAPABILITIES = (
    "oracle_ingestion",
    "real_card_semantics",
    "mana",
    "priority",
    "casting",
    "stack_resolution",
    "state_based_actions",
    "simulation",
    "multiplayer",
    "full_characteristic_evaluation",
    "real_rule_execution",
    "ante",
    "complete_ownership_resolution",
    "complete_control_resolution",
    "complete_visibility_evaluation",
    "zone_move_execution",
    "general_instruction_execution",
    "general_or_full_comprehensive_rules_parser",
)


ACTIVATION_REQUIREMENTS = (
    "source_artifact_verified",
    "projection_package_verified",
    "projection_review_complete",
    "runtime_used_rules_ready",
    "dependency_closure_satisfied",
    "exception_closure_satisfied",
    "semantic_primitives_implemented",
    "capability_matrix_matches_implementation",
    "exact_rules_release_pinned",
    "deterministic_test_vectors_passed",
    "explicit_owner_activation",
)


assert tuple(RULE_REVIEW_CONTENT) == SELECTED_REFERENCES
