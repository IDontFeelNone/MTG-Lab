"""Immutable consumer requirements; inferred needs are never new CR citations."""
from dataclasses import dataclass

from .activated import ActivatedAbilityDependencyDesign
from .classification import ManaClassificationDependencyDesign
from .common import DesignRecord, PM_INPUT, _exact, _fail, _hash, _json, _strings
from .evidence import RETAINED_BINDING
from .stack import StackExceptionDependencyDesign
from .triggered import TriggeredAbilityDependencyDesign


CONSUMER_ORDER = ("605.1a", "605.1b", "605.3", "605.3b", "605.4", "109.4b", "601.2g")
DESIGN_ID_FIELDS = (
    "classification_design_id", "activated_procedure_design_id",
    "triggered_procedure_design_id", "stack_context_design_id",
)
_CITATIONS = {
    "605.1a": ["115.6", "606"],
    "605.1b": ["115.6", "605.1a"],
    "605.3": ["602.2"],
    "605.3b": ["405.6c"],
    "605.4": ["603"],
    "109.4b": ["603", "603.7d", "603.7e", "603.7f"],
    "601.2g": ["605"],
}
_NEEDS = {
    "605.1a": (["target_requirement_semantics", "loyalty_ability_classification",
                 "real_ability_and_card_semantics"],
                ["target_requirement_not_chosen_target_count", "library_movement_semantics",
                 "self_replacement_semantics", "ability_kind_semantics"]),
    "605.1b": (["target_requirement_semantics", "trigger_relationship_semantics",
                 "real_ability_and_card_semantics"],
                ["trigger_event_detection", "activated_mana_ability_classification"]),
    "605.3": (["general_activated_ability_procedure"],
               ["activation_authority", "announcement", "ability_stack_object", "payment",
                "legality", "rollback", "mana_ability_exception_preservation"]),
    "605.3b": (["mana_ability_stack_exception_context"],
                ["general_stack_semantics", "priority", "activated_mana_immediate_resolution"]),
    "605.4": (["general_triggered_ability_subsystem"],
               ["triggered_ability_classification", "trigger_event_detection",
                "trigger_registration", "triggered_mana_exception_preservation"]),
    "109.4b": (["triggered_ability_controller_attribution",
                 "delayed_trigger_controller_attribution"],
                ["general_triggered_ability_subsystem", "delayed_trigger_semantics",
                 "shared_trigger_source_and_event_contracts"]),
    "601.2g": (["mana_ability_classification", "activated_mana_ability_activation_window",
                 "activated_mana_ability_immediate_resolution", "mana_payment_opportunity"],
                ["target_requirement_semantics", "loyalty_ability_classification",
                 "general_activated_ability_procedure", "mana_ability_stack_exception_context",
                 "general_triggered_ability_subsystem", "mana_production_semantics",
                 "mana_pool_semantics", "payment_integration", "complete_casting_gaps"]),
}


def _consumer_rows(binding):
    rows = []
    for reference in CONSUMER_ORDER:
        capabilities, boundaries = _NEEDS[reference]
        rows.append({
            "consumer_reference": reference,
            "consumer_evidence": _json(binding["consumers"][reference]),
            "existing_direct_citations": list(_CITATIONS[reference]),
            "citation_basis": "UNCHANGED_RETAINED_PROJECTION_REFERENCES",
            "required_capabilities": list(capabilities),
            "remaining_semantic_boundaries": list(boundaries),
            "capability_requirement_status": PM_INPUT,
            "capability_requirements_are_new_direct_citations": False,
            "section_reference_state": (
                "SECTION_REFERENCE_RESOLVED_BY_COMPLETE_FAMILY" if reference == "601.2g"
                else "NOT_A_SECTION_605_CONSUMER"),
            "broad_605_reference_rewritten": False,
            "retained_rule_mutated": False,
            "semantic_closure": "OPEN", "execution_readiness": "BLOCKED",
            "required_primitives_available": False,
        })
    return rows


def _body(binding, classification_id, activated_id, triggered_id, stack_id, notes):
    _exact(binding, RETAINED_BINDING, "retained_evidence_binding")
    return {
        "retained_evidence_binding": _json(binding),
        "classification_design_id": classification_id,
        "activated_procedure_design_id": activated_id,
        "triggered_procedure_design_id": triggered_id,
        "stack_context_design_id": stack_id,
        "consumer_bindings": _consumer_rows(binding),
        "indirect_dependency_flows": [
            {"flow_id": "madness_casting_mana_dependencies",
             "relationship_kind": "INDIRECT_DEPENDENCY_FLOW",
             "path": ["702.35b", "bounded_casting_projection", "601.2g", "605",
                      "mana_direct_dependency_groups"],
             "flow_interpretation_status": PM_INPUT,
             "new_direct_madness_to_frontier_citation": False,
             "execution_readiness": "BLOCKED"},
            {"flow_id": "mana_controller_classification_dependencies",
             "relationship_kind": "INDIRECT_DEPENDENCY_FLOW",
             "consumer_reference": "109.4a",
             "consumer_evidence": _json(binding["consumers"]["109.4a"]),
             "existing_direct_citations": ["605"],
             "section_reference_state": "SECTION_REFERENCE_RESOLVED_BY_COMPLETE_FAMILY",
             "required_future_primitive": "hypothetical_stack_controller_attribution",
             "general_controller_source_scope": "REQUIRES_SEPARATE_SOURCE_REVIEW",
             "actual_stack_presence_required": False,
             "new_direct_frontier_citation": False,
             "flow_interpretation_status": PM_INPUT,
             "execution_readiness": "BLOCKED"},
        ],
        "shared_subsystem_policy": {
            "triggered_subsystem_id": "general_triggered_ability_subsystem",
            "shared_consumers": ["605.4", "109.4b"],
            "separate_mana_and_controller_trigger_models_permitted": False,
            "controller_attribution_distinct_from_casting_opportunity": True,
            "one_consumer_readiness_closes_another": False,
        },
        "authority_boundary": {
            "existing_citation_evidence": "RETAINED_REPOSITORY_PROJECTION_ONLY",
            "new_unprojected_body_observations": PM_INPUT,
            "new_direct_cr_citations_created": [],
            "existing_direct_dependency_arrays_rewritten": False,
            "source_coverage_implies_execution": False,
            "fictional_authority_finding": "FICTIONAL_MANA_DOES_NOT_SATISFY_REAL_605",
            "fictional_mana_satisfies_real_605": False,
        },
        "design_notes": notes,
    }


@dataclass(frozen=True)
class ManaDependencyConsumerMatrix(DesignRecord):
    SCHEMA = "gameplay-rules-mana-direct-dependency-consumer-matrix-v1"
    ID_FIELD = "consumer_matrix_id"
    BODY_FIELDS = frozenset({
        "retained_evidence_binding", *DESIGN_ID_FIELDS, "consumer_bindings",
        "indirect_dependency_flows", "shared_subsystem_policy", "authority_boundary", "design_notes",
    })

    @staticmethod
    def _validate_body(body):
        for field in DESIGN_ID_FIELDS:
            _hash(body[field], field)
        _strings(body["design_notes"], "design_notes")
        _exact(body, _body(body["retained_evidence_binding"],
            *(body[field] for field in DESIGN_ID_FIELDS), body["design_notes"]), "consumer_matrix")


def _validate_inputs(classification, activated, triggered, stack):
    for record, expected in (
        (classification, ManaClassificationDependencyDesign),
        (activated, ActivatedAbilityDependencyDesign),
        (triggered, TriggeredAbilityDependencyDesign),
        (stack, StackExceptionDependencyDesign),
    ):
        if type(record) is not expected:
            _fail("concrete immutable dependency designs required")
        record.verify()


def build_consumer_matrix(binding, classification, activated, triggered, stack, *, design_notes=None):
    _validate_inputs(classification, activated, triggered, stack)
    return ManaDependencyConsumerMatrix.create(_body(
        _json(binding), classification.identity, activated.identity,
        triggered.identity, stack.identity, [] if design_notes is None else design_notes))
