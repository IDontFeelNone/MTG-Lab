"""Project-authored knowledge for one non-executable activation procedure frame."""
from gameplay_rules.projection.contracts import _freeze

SELECTED_REFERENCES = ("602.2", "602.2a", "602.2b")
IMPORTED_STAGES = tuple("601.2" + letter for letter in "bcdefghi")


def _base(topic, paraphrase, direct, family, findings, limitations):
    return {
        "topic": topic, "paraphrase": paraphrase,
        "knowledge_kind": "BOUNDED_ACTIVATION_PROCEDURE_CONTEXT",
        "direct_dependency_references": direct,
        "family_relationships": family,
        "findings": findings, "limitations": limitations,
        "semantic_closure": "OPEN", "execution_readiness": "BLOCKED",
        "execution_ready": False, "runtime_operations_implemented": [],
    }


RULE_CONTENT = _freeze({
    "602.2": _base(
        "General activation procedure frame",
        "Activation has ordinary stack placement and cost context. Authority belongs to the "
        "source object's controller, falling back to its owner for an object without a controller, "
        "subject to an exception specified by that object. The listed procedure is ordered; "
        "failure to complete it has illegal-action and pre-activation recovery context. "
        "Completed declarations and payments are fixed.",
        ["733"],
        [{"reference": child, "relationship_kind": "STRUCTURAL_SELECTED_CHILD"}
         for child in ("602.2a", "602.2b")],
        {
            "procedure_order": "LISTED_ORDER",
            "ordinary_context": ["STACK", "COSTS", "EVENTUAL_EFFECT_RESOLUTION"],
            "activation_authority": {
                "ordinary_actor": "SOURCE_OBJECT_CONTROLLER",
                "fallback_actor": "SOURCE_OBJECT_OWNER",
                "fallback_condition": "SOURCE_OBJECT_HAS_NO_CONTROLLER",
                "exception": "OBJECT_SPECIFIC_AUTHORITY_EXCEPTION",
                "permission_evaluation_implemented": False,
            },
            "incomplete_procedure": {
                "classification": "ILLEGAL_ACTIVATION",
                "recovery_context": "RETURN_TO_PRE_ACTIVATION_MOMENT",
                "source_reference": "733", "target_coverage": "UNPROJECTED",
                "target_correspondence": "UNRESOLVED", "rollback_implemented": False,
            },
            "announcement_payment_revision": "NO_REVISION_AFTER_MAKING_THEM",
            "mana_exception_context": "QUALIFYING_MANA_EXCEPTIONS_RETAIN_SEPARATE_EVIDENCE",
        },
        ["This frame assumes an activated ability and supplies no general recognizer.",
         "Complete permission, timing, rollback and resolution semantics remain unresolved.",
         "Ordinary stack context is subject to qualifying mana exceptions; no activation is performed."]),
    "602.2a": _base(
        "Activation announcement and ordinary ability-object context",
        "The activator declares the ability. Use from a hidden zone carries card-reveal context. "
        "Ordinarily, the resulting ability is a noncard object at the top of the stack, carries "
        "the originating ability's text without other characteristics, and has the activator "
        "as controller. Its ordinary stack residence ends through countering, resolution or movement.",
        ["701.20a"],
        [{"reference": "602.2", "relationship_kind": "STRUCTURAL_SELECTED_PARENT"}],
        {
            "announcement": "PLAYER_DECLARES_ACTIVATION",
            "hidden_zone_context": {
                "condition": "ACTIVATED_ABILITY_USED_FROM_HIDDEN_ZONE",
                "reveal_context": "CARD_WITH_THAT_ABILITY",
                "source_reference": "701.20a", "target_coverage": "UNPROJECTED",
                "target_correspondence": "UNRESOLVED", "reveal_operation_implemented": False,
            },
            "ordinary_stack_object": {
                "object_kind": "ABILITY_NOT_CARD", "relative_position": "TOPMOST",
                "content": "ORIGINATING_ABILITY_TEXT", "other_characteristics": "NONE",
                "controller_attribution": "ACTIVATOR",
                "residence_end_contexts": ["COUNTERED", "RESOLVED", "MOVED_ELSEWHERE"],
                "qualifying_mana_exceptions_preserved": True,
                "stack_construction_implemented": False,
                "controller_evaluation_implemented": False,
                "unconditional_mana_ability_stack_placement": False,
            },
            "109_4a_controller_boundary": "HYPOTHETICAL_STACK_ATTRIBUTION_REMAINS_SEPARATE",
        },
        ["No reveal, ability construction, controller evaluation or stack operation is supplied.",
         "Qualifying mana abilities retain their independently proven exceptions.",
         "The separate 109.4a attribution boundary does not require actual stack presence."]),
    "602.2b": _base(
        "Remaining procedure import and activation-cost analogy",
        "The remaining activation procedure imports the casting range from 601.2b through "
        "601.2i. The separate explicit reference to 601.2f maps the spell mana-cost concept "
        "to the ability activation-cost concept. Activation and casting retain separate identities.",
        ["601.2f"],
        [{"reference": "602.2", "relationship_kind": "STRUCTURAL_SELECTED_PARENT"}],
        {
            "range_import": {
                "relationship_kind": "CASTING_STAGE_RANGE_IMPORT",
                "start": "601.2b", "end": "601.2i", "members": list(IMPORTED_STAGES),
                "remaining_activation_procedure": True,
                "additional_applicability_qualifier_found": False,
                "imports_601_2a": False,
                "literal_member_citations_invented": False,
                "membership_verifies_missing_member_bodies": False,
                "coverage": "INCOMPLETE_FOUR_OF_EIGHT_MEMBERS_PROJECTED",
            },
            "cost_analogy": {
                "relationship_kind": "SEPARATE_LITERAL_DIRECT_REFERENCE_AND_CONCEPT_ANALOGY",
                "reference": "601.2f", "casting_concept": "SPELL_MANA_COST",
                "activation_concept": "ABILITY_ACTIVATION_COST",
                "mapping": "REPLACE_SPELL_MANA_COST_CONCEPT_WITH_ABILITY_ACTIVATION_COST_CONCEPT",
                "target_coverage": "ALREADY_PROJECTED",
                "actions_interchangeable": False, "cost_calculation_implemented": False,
                "payment_implemented": False,
            },
        },
        ["Range membership supplies no knowledge of the unprojected c/d/e/i bodies.",
         "The historical 601.2e purpose observation retains its original design-only authority.",
         "Neither procedure is implemented; no cost calculation, payment or Card semantics follow."]),
})

GRAPH_NODES = _freeze([
    {"reference": reference, "classification": "PROJECTED_SELECTED_RULE"}
    for reference in SELECTED_REFERENCES
] + [
    {"reference": "733", "classification": "UNPROJECTED_UNRESOLVED_TARGET"},
    {"reference": "701.20a", "classification": "UNPROJECTED_UNRESOLVED_TARGET"},
    {"reference": "601.2f", "classification": "ALREADY_PROJECTED_DIRECT_TARGET"},
])
GRAPH_EDGES = _freeze([
    {"from": "602.2", "to": "733", "relationship_kind": "LITERAL_DIRECT_REFERENCE", "status": "UNRESOLVED"},
    {"from": "602.2a", "to": "701.20a", "relationship_kind": "LITERAL_DIRECT_REFERENCE", "status": "UNRESOLVED"},
    {"from": "602.2b", "to": "601.2f", "relationship_kind": "LITERAL_DIRECT_REFERENCE", "status": "DIRECT_REFERENCE_RESOLVED"},
])
UNSUPPORTED_DIMENSIONS = _freeze([
    "ability_recognition", "complete_activation_authority_and_controller", "ability_identity",
    "general_stack_semantics", "cost_determination", "complete_casting_procedure",
    "mana_and_nonmana_payment", "legality_and_timing", "illegal_action_recovery_and_rollback",
    "downstream_resolution", "shared_triggered_subsystem", "real_card_and_effect_semantics",
])
