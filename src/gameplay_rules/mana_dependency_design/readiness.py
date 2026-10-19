"""Append-only readiness analysis; existing source coverage grants no runtime."""
from dataclasses import dataclass

from .common import DesignRecord, PM_INPUT, _exact, _fail, _hash, _json, _strings
from .consumers import DESIGN_ID_FIELDS, ManaDependencyConsumerMatrix, _validate_inputs
from .evidence import RETAINED_BINDING
from .grouping import ManaDependencyGrouping


CAPABILITY_ORDER = (
    "mana_ability_classification", "activated_mana_ability_activation_window",
    "activated_mana_ability_immediate_resolution", "triggered_mana_ability_immediate_resolution",
    "mana_ability_controller_attribution", "mana_payment_opportunity",
    "mana_production_semantics", "mana_pool_semantics", "target_requirement_semantics",
    "loyalty_ability_classification", "loyalty_ability_execution",
    "mana_ability_stack_exception_context", "general_activated_ability_procedure",
    "general_triggered_ability_subsystem",
)
REASSESSMENT_ORDER = (
    "mana_ability_classification", "activated_mana_ability_behavior",
    "triggered_mana_ability_behavior", "object_control",
    "alternative_cost_casting_subprocedure", "complete_spell_casting", "madness",
)


def _capability(name, existing_refs, dependencies, primitives, boundaries, consumers):
    return {
        "capability_id": name,
        "existing_source_context": existing_refs,
        "evidence_requirements": ["PINNED_RETAINED_CONSUMER_IDENTITIES",
            "FUTURE_SOURCE_VERIFICATION_OF_UNPROJECTED_DEPENDENCIES",
            "INDEPENDENT_REAL_SEMANTIC_PRIMITIVE_REVIEW"],
        "source_coverage": ("EXISTING_RETAINED_CONTEXT_WITH_OPEN_DEPENDENCIES" if existing_refs
                            else "UNPROJECTED_BODY_DESIGN_ONLY"),
        "dependency_body_observation_status": PM_INPUT,
        "semantic_dependencies": dependencies,
        "required_future_primitives": primitives,
        "unsupported_boundaries": boundaries,
        "retained_consumer_references": consumers,
        "semantic_closure": "OPEN", "execution_readiness": "BLOCKED",
        "implementation_status": "NOT_IMPLEMENTED", "required_primitives_available": False,
        "implied_ready_capabilities": [], "execution_supported": False,
    }


def _capabilities():
    return [
        _capability("mana_ability_classification", ["605.1", "605.1a", "605.1b", "605.2", "605.5", "605.5a", "605.5b"],
            ["target_requirement_semantics", "loyalty_ability_classification", "ability_kind_semantics",
             "library_movement_semantics", "replacement_effect_semantics", "trigger_relationship_semantics"],
            ["target_requirement_evidence", "loyalty_category_evidence", "ability_kind_evidence",
             "unknown_classification_state"],
            ["real_ability_classification", "real_card_effect_semantics", "target_grammar",
             "replacement_effect_execution", "trigger_detection"], ["605.1a", "605.1b", "601.2g", "109.4a"]),
        _capability("activated_mana_ability_activation_window", ["605.3", "605.3a"],
            ["mana_ability_classification", "general_activated_ability_procedure", "priority",
             "casting_or_activation_payment_context", "rule_or_effect_payment_request"],
            ["mana_activation_context", "mana_payment_request_context"],
            ["current_activation_eligibility", "priority_runtime", "casting_runtime", "payment"], ["601.2g"]),
        _capability("activated_mana_ability_immediate_resolution", ["605.3b", "605.3c"],
            ["general_activated_ability_procedure", "mana_ability_stack_exception_context", "effect_execution"],
            ["activated_mana_immediate_sequence", "same_ability_resolution_guard"],
            ["activation", "resolution", "stack_runtime", "response_windows", "countering"], ["605.3b", "601.2g"]),
        _capability("triggered_mana_ability_immediate_resolution", ["605.4", "605.4a"],
            ["general_triggered_ability_subsystem", "trigger_relationship_semantics", "effect_execution"],
            ["triggered_mana_causality", "triggered_mana_immediate_sequence"],
            ["trigger_detection", "trigger_ordering", "effect_execution", "stack_and_priority_context"], ["605.4", "601.2g"]),
        _capability("mana_ability_controller_attribution", ["109.4a"],
            ["mana_ability_classification", "general_ability_controller_semantics", "ability_subtype_semantics"],
            ["hypothetical_stack_controller_attribution", "ability_source_controller_evidence"],
            ["controller_assignment", "general_controller_source_scope", "actual_stack_object_creation"], ["109.4a"]),
        _capability("mana_payment_opportunity", ["601.2g", "605.3a"],
            ["mana_ability_classification", "activated_mana_ability_activation_window",
             "activated_mana_ability_immediate_resolution", "payment_integration"],
            ["mana_payment_opportunity_context", "locked_cost_identity_binding"],
            ["payment", "cost_calculation", "complete_casting", "real_ability_activation"], ["601.2g"]),
        _capability("mana_production_semantics", [],
            ["real_card_and_effect_semantics", "mana_type_amount_recipient_semantics",
             "output_restrictions", "replacement_effect_semantics"],
            ["mana_output_evidence", "mana_recipient_evidence", "mana_restriction_evidence"],
            ["mana_generation", "output_calculation", "replacement_execution", "pool_mutation"], ["601.2g"]),
        _capability("mana_pool_semantics", [],
            ["mana_production_semantics", "mana_resource_semantics", "spending_restrictions", "payment_integration"],
            ["future_mana_resource_contract", "future_spending_constraint_contract"],
            ["pool_representation", "pool_clearing", "mana_transformations", "special_purpose_mana",
             "mana_history", "spending", "payment"], ["601.2g"]),
        _capability("target_requirement_semantics", [],
            ["115.6", "ability_target_grammar", "keyword_defined_targets", "real_card_and_effect_semantics"],
            ["required_target_declaration_evidence", "chosen_target_count_separation"],
            ["target_parser", "target_selection", "target_legality", "arbitrary_card_text_recognition"], ["605.1a", "605.1b"]),
        _capability("loyalty_ability_classification", [],
            ["606.1", "606.2", "activation_cost_symbol_evidence", "ability_kind_semantics"],
            ["loyalty_activation_cost_symbol_evidence", "unknown_loyalty_category_state"],
            ["loyalty_activation", "loyalty_counter_payment", "broad_606_section_closure"], ["605.1a"]),
        _capability("loyalty_ability_execution", [],
            ["loyalty_ability_classification", "606.3", "606.4", "606.5", "606.6", "priority",
             "stack_state", "main_phase", "activation_history", "payment"],
            ["loyalty_activation_history", "loyalty_counter_cost_contract"],
            ["timing_evaluation", "loyalty_counter_mutation", "permanent_controller_state", "payment"], ["605.1a"]),
        _capability("mana_ability_stack_exception_context", ["605.3b", "605.4a"],
            ["405.6c", "general_activated_ability_procedure", "general_triggered_ability_subsystem"],
            ["general_procedure_exception_applicability", "mana_no_stack_context"],
            ["general_stack_objects", "resolution_queue", "priority", "response_windows", "countering"], ["605.3b"]),
        _capability("general_activated_ability_procedure", [],
            ["602.2", "602.2a", "602.2b", "casting_procedure_reuse", "activation_authority",
             "payment", "legality", "rollback"],
            ["activated_ability_announcement_contract", "ability_stack_object_contract",
             "activation_cost_identity", "activation_authority_evidence", "illegal_action_contract"],
            ["ability_activation", "stack_creation", "unprojected_casting_stages", "payment", "rollback"], ["605.3"]),
        _capability("general_triggered_ability_subsystem", [],
            ["603", "trigger_event_detection", "trigger_registration", "controller_attribution",
             "stack_placement", "ordering", "delayed_trigger_semantics"],
            ["shared_trigger_event_contract", "shared_trigger_controller_evidence",
             "delayed_trigger_controller_evidence", "trigger_ordering_contract"],
            ["trigger_detection", "trigger_stack_placement", "APNAP_ordering", "delayed_triggers",
             "zone_change_triggers", "reflexive_triggers"], ["605.4", "109.4b"]),
    ]


def _reassessments():
    scopes = (
        ("mana_ability_classification", ["605.1a", "605.1b"],
         ["115.6_UNPROJECTED", "606_CLASSIFICATION_UNPROJECTED", "ABILITY_LIBRARY_REPLACEMENT_SEMANTICS_OPEN"]),
        ("activated_mana_ability_behavior", ["605.3", "605.3b", "601.2g"],
         ["602.2_UNPROJECTED", "405.6c_UNPROJECTED", "PRIORITY_ACTIVATION_AND_EFFECT_RUNTIME_ABSENT"]),
        ("triggered_mana_ability_behavior", ["605.4"],
         ["603_UNPROJECTED", "TRIGGER_DETECTION_AND_SEQUENCING_ABSENT"]),
        ("object_control", ["109.4a", "109.4b"],
         ["HYPOTHETICAL_STACK_ATTRIBUTION_ABSENT", "GENERAL_TRIGGERED_CONTROLLER_SEMANTICS_OPEN",
          "603.7d_e_f_UNPROJECTED", "OTHER_CONTROL_DEPENDENCIES_OPEN"]),
        ("alternative_cost_casting_subprocedure", ["601.2g"],
         ["MANA_CLASSIFICATION_DEPENDENCIES_OPEN", "COST_CHOICE_DEPENDENCIES_UNPROJECTED",
          "PAYMENT_INTEGRATION_ABSENT", "UNPROJECTED_CASTING_STAGES"]),
        ("complete_spell_casting", ["601.2g"],
         ["UNPROJECTED_CASTING_STAGES", "CASTING_PERMISSION_AND_LEGALITY_OPEN",
          "STACK_PRIORITY_AND_ROLLBACK_ABSENT", "COMPLETION_AND_CAST_TRIGGERS_ABSENT"]),
        ("madness", ["702.35b", "601.2g"],
         ["INDIRECT_CASTING_DEPENDENCIES_OPEN", "DISCARD_REPLACEMENT_EXILE_AND_TRIGGER_RUNTIME_ABSENT",
          "OPTIONAL_CAST_AND_PUBLIC_ZONE_FALLBACK_ABSENT"]),
    )
    common_blockers = ["REAL_CARD_AND_EFFECT_SEMANTICS_ABSENT", "REQUIRED_SEMANTIC_PRIMITIVES_ABSENT",
        "DETERMINISTIC_RUNTIME_VECTORS_ABSENT", "OWNER_ACTIVATION_NOT_GRANTED"]
    return [{"capability_id": name, "retained_consumers": refs,
             "source_coverage": "EXISTING_PROJECTIONS_UNCHANGED_NO_DEPENDENCY_UNITS_ADDED",
             "blocker_interpretation_status": PM_INPUT,
             "blockers": specific + common_blockers,
             "dependency_closure": "OPEN", "semantic_closure": "OPEN",
             "required_primitives_available": False, "execution_readiness": "EXECUTION_BLOCKED",
             "execution_supported": False}
            for name, refs, specific in scopes]


def _body(binding, classification_id, activated_id, triggered_id, stack_id, consumers_id, grouping_id, notes):
    _exact(binding, RETAINED_BINDING, "retained_evidence_binding")
    capabilities = _capabilities()
    return {
        "retained_evidence_binding": _json(binding),
        "classification_design_id": classification_id, "activated_procedure_design_id": activated_id,
        "triggered_procedure_design_id": triggered_id, "stack_context_design_id": stack_id,
        "consumer_matrix_id": consumers_id, "grouping_id": grouping_id,
        "dependency_body_observation_status": PM_INPUT,
        "capabilities": capabilities,
        "capability_separation": {
            "classification_implies_execution": False, "target_requirement_implies_target_parser": False,
            "chosen_target_count_determines_target_requirement": False,
            "loyalty_classification_implies_loyalty_execution": False,
            "stack_exception_implies_general_stack_semantics": False,
            "mana_exception_implies_general_activated_procedure": False,
            "triggered_mana_exception_implies_general_triggered_procedure": False,
            "one_capability_readiness_implies_another": False,
        },
        "section_resolution": {
            "601.2g": binding["section_reference_resolution"]["601.2g"],
            "109.4a": binding["section_reference_resolution"]["109.4a"],
            "prior_605_family_closure_review_id": binding["family_closure_review_id"],
            "section_resolution_implies_semantic_closure": False,
            "section_resolution_implies_execution": False,
            "broad_606_section_resolved": False,
            "hypothetical_stack_controller_attribution": "UNRESOLVED_FUTURE_PRIMITIVE",
            "historical_direct_dependency_arrays_rewritten": False,
        },
        "general_and_special_procedures": {
            "activated_general_role": "GENERAL_PROCEDURE", "activated_special_role": "MANA_ABILITY_EXCEPTION",
            "triggered_general_role": "GENERAL_TRIGGERED_PROCEDURE", "triggered_special_role": "TRIGGERED_MANA_EXCEPTION",
            "general_stack_requirement_unconditionally_applied_to_mana_abilities": False,
            "special_case_supplies_general_procedure_closure": False,
            "controller_and_mana_trigger_consumers_share_one_future_subsystem": True,
            "interpretation_status": PM_INPUT,
        },
        "readiness_reassessments": _reassessments(),
        "required_future_primitives": list(dict.fromkeys(
            primitive for row in capabilities for primitive in row["required_future_primitives"])),
        "real_execution_primitives_available": [],
        "production_pool_payment_boundaries": {
            "mana_production_semantics": "BLOCKED_ABSENT", "mana_pool_semantics": "BLOCKED_ABSENT",
            "payment_integration": "BLOCKED_ABSENT", "pool_representation_decided": False,
            "pool_clearing_rules_decided": False, "spending_restrictions_decided": False,
            "mana_transformations_decided": False, "special_purpose_mana_decided": False,
        },
        "fictional_authority": {
            "finding": "FICTIONAL_MANA_DOES_NOT_SATISFY_REAL_605",
            "fictional_mana_satisfies_real_605": False, "fictional_runtime_authority_inherited": False,
            "accepted_real_execution_authority_proofs": [], "fictional_profile_changed": False,
        },
        "remaining_unprojected_numbered_boundaries": list(binding["existing_unprojected_references"]),
        "new_body_scope_candidates": {
            "status": PM_INPUT, "source_verified": False,
            "references": ["606.1", "606.2", "606.3", "606.4", "606.5", "606.6",
                           "405.6", "602.2a", "602.2b", "603.7", "701.20a"],
            "new_verified_direct_references": [],
        },
        "projected_rule_count_before": 81, "source_projections_added": 0,
        "projected_rule_count_after": 81,
        "overall_readiness": "EXECUTION_BLOCKED",
        "target_profile_id": "magic-comprehensive-rules-20260925-v1",
        "real_execution_profile_readiness": "REAL_EXECUTION_PROFILE_NOT_READY",
        "historical_acquisition_identity": binding["historical_acquisition_identity"],
        "architecture": {"fits_v13": True, "tier_zero_change": False, "runtime_changed": False},
        "limitations": [
            "Only the retained outgoing citation relationships have verified-source authority; new target-body descriptions remain PM design input.",
            "Classification-only loyalty context does not resolve the entire 606 section or supply loyalty execution.",
            "Existing 605 section coverage remains resolved without closing classification, activation, controller, casting, or trigger semantics.",
            "The next scope is provisional and requires exact future artifact verification; it is not authorized or started.",
            "No real ability, target, controller, cost, mana output, or pool is evaluated or changed.",
        ],
        "design_notes": notes,
    }


@dataclass(frozen=True)
class ManaDependencyReadiness(DesignRecord):
    SCHEMA = "gameplay-rules-mana-direct-dependency-readiness-v1"
    ID_FIELD = "readiness_id"
    BODY_FIELDS = frozenset(_body(_json(RETAINED_BINDING), "", "", "", "", "", "", []))

    @staticmethod
    def _validate_body(body):
        for field in (*DESIGN_ID_FIELDS, "consumer_matrix_id", "grouping_id"):
            _hash(body[field], field)
        _strings(body["design_notes"], "design_notes")
        _exact(body, _body(body["retained_evidence_binding"],
            *(body[field] for field in DESIGN_ID_FIELDS), body["consumer_matrix_id"],
            body["grouping_id"], body["design_notes"]), "dependency_readiness")


def build_readiness(binding, classification, activated, triggered, stack, consumers, grouping, *, design_notes=None):
    _validate_inputs(classification, activated, triggered, stack)
    _exact(_json(binding), RETAINED_BINDING, "retained_evidence_binding")
    for record, expected in ((consumers, ManaDependencyConsumerMatrix), (grouping, ManaDependencyGrouping)):
        if type(record) is not expected:
            _fail("concrete immutable matrix and grouping required")
        record.verify()
        for field, design in zip(DESIGN_ID_FIELDS, (classification, activated, triggered, stack)):
            _exact(record.to_dict()[field], design.identity, "readiness_" + field)
    _exact(_json(consumers.retained_evidence_binding), binding, "readiness_consumer_binding")
    _exact(grouping.consumer_matrix_id, consumers.identity, "readiness_consumer_matrix_id")
    return ManaDependencyReadiness.create(_body(
        _json(binding), classification.identity, activated.identity, triggered.identity,
        stack.identity, consumers.identity, grouping.identity, [] if design_notes is None else design_notes))
