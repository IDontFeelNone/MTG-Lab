"""Scope comparisons and one unauthorised future milestone recommendation."""
from dataclasses import dataclass

from .common import DesignRecord, PM_INPUT, _exact, _fail, _hash, _strings
from .consumers import DESIGN_ID_FIELDS, ManaDependencyConsumerMatrix, _validate_inputs


PROPOSED_CLASSIFICATION_SCOPE = ("115.6", "606.1", "606.2")
GROUP_ORDER = ("mana_classification_dependencies", "mana_stack_exception_context",
               "general_activated_ability_procedure", "general_triggered_ability_subsystem")


def _groups():
    rows = (
        ("A", GROUP_ORDER[0], ["115.6", "606"], "BOUNDED_CLASSIFICATION_DEPENDENCIES",
         ["115.6", "606.1", "606.2"], ["605.1a", "605.1b"],
         "Target requirement and loyalty classification can improve the two classification consumers without importing targeting or loyalty execution.",
         ["target_grammar", "real_ability_and_card_semantics", "loyalty_ability_execution",
          "broad_606_section_resolution"]),
        ("B", GROUP_ORDER[1], ["405.6c"], "BOUNDED_STACK_CONTEXT",
         ["405.6c"], ["605.3b", "605.4a"],
         "The supplied child description and retained 605 framing provisionally support a child-only context candidate; parent hierarchy alone does not justify another unit.",
         ["general_stack_semantics", "priority", "response_windows", "resolution_queue"]),
        ("C", GROUP_ORDER[2], ["602.2"], "LARGE_CORE_SUBSYSTEM",
         ["602.2", "602.2a", "602.2b"], ["605.3"],
         "The local activation cluster imports authority, stack-object creation, casting stages, legality, costs, and rollback; further subsystem design precedes source admission.",
         ["activation_authority", "unprojected_casting_stages", "payment", "legality",
          "rollback", "resolution"]),
        ("D", GROUP_ORDER[3], ["603"], "LARGE_SHARED_CORE_SUBSYSTEM",
         [], ["605.4", "109.4b"],
         "Trigger detection, controller attribution, placement, ordering, and delayed triggers need one shared staged subsystem design; a whole-section import is unjustified.",
         ["trigger_event_detection", "trigger_registration", "controller_attribution",
          "trigger_stack_placement", "ordering", "delayed_triggers", "specialized_triggers"]),
    )
    return [{
        "group_id": group_id, "capability_group": capability, "verified_frontier_members": members,
        "classification": size, "provisional_local_source_scope": scope,
        "primary_consumers": consumers, "scope_judgment": rationale,
        "deliberately_open_boundaries": boundaries, "body_observation_status": PM_INPUT,
        "candidate_source_units_verified": False, "execution_readiness": "BLOCKED",
        "source_coverage_implies_execution": False,
    } for group_id, capability, members, size, scope, consumers, rationale, boundaries in rows]


def _comparisons():
    return [
        {"candidate": "Bounded Mana Classification Dependency Projection", "kind": "PROJECTION",
         "provisional_source_allowlist": list(PROPOSED_CLASSIFICATION_SCOPE), "proposed_source_unit_count": 3,
         "coherence": "BOUNDED_TWO_CLASSIFICATION_CONCERNS_WITH_EXPLICIT_PARTIAL_606_COVERAGE",
         "immediate_value": "TWO_DIRECT_CLASSIFICATION_CONSUMERS_AND_INDIRECT_CASTING_CONTROLLER_PATHS",
         "subsystem_expansion_risk": "LOW_WITH_UNKNOWN_TARGET_GRAMMAR_AND_606_BEHAVIOR_LEFT_OPEN",
         "selection_state": "RECOMMENDED_NOT_AUTHORIZED",
         "decision_rationale": "The target-count nuance and loyalty category address both classification consumers with a coherent narrow scope; no general ability procedure is imported."},
        {"candidate": "Bounded Mana Stack-Exception Projection", "kind": "PROJECTION",
         "provisional_source_allowlist": ["405.6c"], "proposed_source_unit_count": 1,
         "coherence": "PROVISIONAL_CHILD_WITH_RETAINED_605_EXCEPTION_CONTEXT",
         "immediate_value": "OVERLAPS_EXISTING_605_NO_STACK_EVIDENCE",
         "subsystem_expansion_risk": "LOW_IF_GENERAL_STACK_AND_PRIORITY_REMAIN_OPEN",
         "selection_state": "DEFERRED_ALTERNATIVE",
         "decision_rationale": "Useful local context, but its overlap with already projected immediate behavior gives less new classification coverage than the selected candidate."},
        {"candidate": "Activated Ability Procedure Design", "kind": "DESIGN",
         "provisional_source_allowlist": [], "proposed_source_unit_count": 0,
         "coherence": "LARGE_602_2_LOCAL_CLUSTER_WITH_CASTING_REUSE",
         "immediate_value": "GENERAL_ACTIVATION_AND_605_3",
         "subsystem_expansion_risk": "HIGH_CASTING_PAYMENT_LEGALITY_ROLLBACK_INTERACTIONS",
         "selection_state": "DEFERRED_ALTERNATIVE",
         "decision_rationale": "Separate design remains necessary before its local candidate source scope can be admitted; it is broader than the present classification gaps."},
        {"candidate": "Triggered Ability Dependency Design", "kind": "DESIGN",
         "provisional_source_allowlist": [], "proposed_source_unit_count": 0,
         "coherence": "LARGE_SHARED_603_SUBSYSTEM_WITH_STAGED_SOURCE_OPTIONS",
         "immediate_value": "SHARED_605_4_AND_109_4B_CONTROLLER_REQUIREMENTS",
         "subsystem_expansion_risk": "HIGH_EVENT_ORDERING_STACK_DELAYED_TRIGGER_INTERACTIONS",
         "selection_state": "DEFERRED_ALTERNATIVE",
         "decision_rationale": "High shared value warrants a dedicated design later; it need not precede the bounded independent classification evidence."},
    ]


def _next_milestone():
    return {
        "candidate": "Bounded Mana Classification Dependency Projection",
        "exact_proposed_source_allowlist": list(PROPOSED_CLASSIFICATION_SCOPE),
        "proposed_source_unit_count": 3,
        "source_unit_rationales": [
            {"rule_reference": "115.6", "reason": "Represent required targets separately from how many targets were chosen for both 605.1a and 605.1b."},
            {"rule_reference": "606.1", "reason": "Supply the immediate loyalty category context connecting activated abilities to the selected classification criterion."},
            {"rule_reference": "606.2", "reason": "Supply the proposed loyalty-symbol activation-cost classification criterion needed by 605.1a."},
        ],
        "body_observation_status": PM_INPUT,
        "exact_scope_requires_future_source_verification": True,
        "target_consumers": ["605.1a", "605.1b"],
        "indirect_beneficiaries": ["601.2g", "109.4a", "madness"],
        "deliberately_unresolved": ["broad_606_section_reference", "606.3", "606.4", "606.5", "606.6",
            "target_grammar_and_recognition", "target_legality", "keyword_defined_targets",
            "loyalty_activation_and_payment", "real_card_and_effect_semantics", "602.2", "405.6c", "603"],
        "broad_606_section_resolved_by_classification_scope": False,
        "expected_606_relationship": "CLASSIFICATION_CONTEXT_REPRESENTED_SECTION_REMAINS_OPEN",
        "verified_txt_required": True, "source_release_concept": "2026-09-25",
        "expected_anchor_type": "MULTI_LINE_RULE_BLOCK_ANCHOR",
        "expected_span_policy": "EXACT_RULE_BLOCK_RAW_BYTES_EXCLUDING_FINAL_LINE_TERMINATOR",
        "internal_terminators": "PRESERVE_RAW_BYTES", "final_terminator": "EXCLUDED",
        "example_ownership_required": "UNAMBIGUOUS_OR_STOP", "one_line_blocks_permitted": True,
        "scope_or_source_discrepancy_action": "STOP_FOR_SEPARATE_REVIEW_NO_AUTOMATIC_EXPANSION",
        "execution_blockers": ["unresolved_target_grammar", "loyalty_behavior_unprojected",
            "real_ability_and_card_semantics_absent", "required_semantic_primitives_absent",
            "deterministic_runtime_vectors_absent", "owner_activation_not_granted"],
        "source_coverage_implies_execution": False, "authorized": False, "started": False,
    }


def _body(classification_id, activated_id, triggered_id, stack_id, consumers_id, notes):
    return {
        "classification_design_id": classification_id,
        "activated_procedure_design_id": activated_id,
        "triggered_procedure_design_id": triggered_id,
        "stack_context_design_id": stack_id, "consumer_matrix_id": consumers_id,
        "dependency_groups": _groups(), "candidate_comparison": _comparisons(),
        "selection_criteria": ["smallest_coherent_source_scope", "immediate_source_coverage_value",
            "multiple_consumer_reuse", "subsystem_expansion_risk", "explicit_fail_closed_boundaries"],
        "selection_policy": {
            "rule_count_alone_decides": False, "largest_shared_dependency_automatically_wins": False,
            "generic_single_ability_engine_group_created": False,
            "activated_and_triggered_subsystems_independent": True,
            "recommended_milestone_count": 1,
        },
        "next_milestone": _next_milestone(), "design_notes": notes,
    }


@dataclass(frozen=True)
class ManaDependencyGrouping(DesignRecord):
    SCHEMA = "gameplay-rules-mana-direct-dependency-grouping-v1"
    ID_FIELD = "grouping_id"
    BODY_FIELDS = frozenset({*DESIGN_ID_FIELDS, "consumer_matrix_id", "dependency_groups",
        "candidate_comparison", "selection_criteria", "selection_policy", "next_milestone", "design_notes"})

    @staticmethod
    def _validate_body(body):
        for field in (*DESIGN_ID_FIELDS, "consumer_matrix_id"):
            _hash(body[field], field)
        _strings(body["design_notes"], "design_notes")
        _exact(body, _body(*(body[field] for field in DESIGN_ID_FIELDS),
            body["consumer_matrix_id"], body["design_notes"]), "dependency_grouping")


def build_dependency_grouping(classification, activated, triggered, stack, consumers, *, design_notes=None):
    _validate_inputs(classification, activated, triggered, stack)
    if type(consumers) is not ManaDependencyConsumerMatrix:
        _fail("concrete immutable consumer matrix required")
    consumers.verify()
    records = (classification, activated, triggered, stack)
    for field, record in zip(DESIGN_ID_FIELDS, records):
        _exact(consumers.to_dict()[field], record.identity, "grouping_" + field)
    return ManaDependencyGrouping.create(_body(
        *(record.identity for record in records), consumers.identity,
        [] if design_notes is None else design_notes))
