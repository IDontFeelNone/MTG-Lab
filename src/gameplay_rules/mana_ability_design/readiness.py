"""Append-only mana-dependency readiness findings, with no gameplay authority.

The inputs are immutable design contracts and pinned retained evidence.  No
classification, activation, mana arithmetic, controller selection, or payment
occurs here.  In particular, fictional kernel behavior is never evidence that a
real-rule capability is closed.
"""
from __future__ import annotations

from dataclasses import dataclass

from .behavior import ManaAbilityBehaviorDesign
from .classification import ManaAbilityClassificationDesign
from .common import DesignRecord, PM_INPUT, _exact, _fail, _hash, _json, _strings
from .consumers import ManaAbilityConsumerMatrix
from .controller import ManaAbilityControllerDesign
from .evidence import EXISTING_UNPROJECTED_REFERENCES, RETAINED_BINDING
from .frontier import ManaAbilityProjectionFrontier


CAPABILITY_ORDER = (
    "mana_ability_classification",
    "activated_mana_ability_activation_window",
    "activated_mana_ability_immediate_resolution",
    "triggered_mana_ability_immediate_resolution",
    "mana_ability_controller_attribution",
    "mana_payment_opportunity",
    "mana_production_semantics",
    "mana_pool_semantics",
)
REASSESSMENT_ORDER = (
    "mana_abilities", "alternative_cost_casting_subprocedure",
    "complete_spell_casting", "object_control", "madness",
)
CANDIDATE_OUTGOING_REFERENCES = ("115.6", "606", "602.2", "405.6c", "603")


def _capability(name, evidence, dependencies, primitives, boundaries, consumers):
    return {
        "capability_id": name,
        "evidence_requirements": evidence,
        "semantic_dependencies": dependencies,
        "required_future_primitives": primitives,
        "unsupported_boundaries": boundaries,
        "retained_consumer_references": consumers,
        "source_coverage": "DESIGN_SCOPED_605_UNPROJECTED",
        "source_verified": False,
        "semantic_closure": "OPEN",
        "execution_readiness": "BLOCKED",
        "implementation_status": "NOT_IMPLEMENTED",
        "required_primitives_available": False,
        "execution_supported": False,
        "fictional_mana_satisfies_real_605": False,
        "fictional_runtime_authority_inherited": False,
        "implied_ready_capabilities": [],
    }


def _capabilities():
    """Eight independent requirements, without an aggregate support switch."""
    return [
        _capability(
            "mana_ability_classification",
            ["FUTURE_SOURCE_VERIFIED_605_CLASSIFICATION_FAMILY",
             "FUTURE_TARGET_LOYALTY_LIBRARY_REPLACEMENT_SCOPE_EVIDENCE",
             "REAL_ABILITY_AND_EFFECT_SEMANTICS"],
            ["activated_ability_kind", "triggered_ability_kind", "target_knowledge",
             "loyalty_classification", "library_movement_knowledge",
             "classification_replacement_effect_scope", "trigger_relationship_knowledge"],
            ["ability_kind_evidence", "mana_ability_classification_input",
             "classification_unknown_state", "classification_current_output_separation"],
            ["real_ability_classification", "real_card_effect_semantics",
             "replacement_effect_execution", "trigger_detection"],
            ["601.2g", "109.4a"],
        ),
        _capability(
            "activated_mana_ability_activation_window",
            ["RETAINED_601.2g_CONSUMER", "FUTURE_SOURCE_VERIFIED_605_ACTIVATION_WINDOWS"],
            ["mana_ability_classification", "ordinary_priority_context",
             "spell_casting_payment_context", "ability_activation_payment_context",
             "rule_or_effect_payment_request_context"],
            ["activated_mana_activation_context", "mana_payment_request_context"],
            ["priority", "casting_execution", "activated_ability_execution",
             "cost_payment", "current_activation_eligibility_evaluation"],
            ["601.2g"],
        ),
        _capability(
            "activated_mana_ability_immediate_resolution",
            ["FUTURE_SOURCE_VERIFIED_605_ACTIVATED_BEHAVIOR",
             "FUTURE_GENERAL_ACTIVATED_PROCEDURE_REVIEW", "FUTURE_STACK_EXCEPTION_REVIEW"],
            ["mana_ability_classification", "general_activated_ability_semantics",
             "stack_exception_semantics", "effect_execution_semantics"],
            ["activated_mana_immediate_resolution", "same_ability_resolution_guard"],
            ["activated_ability_execution", "effect_execution", "stack_runtime",
             "response_windows", "countering"],
            ["601.2g"],
        ),
        _capability(
            "triggered_mana_ability_immediate_resolution",
            ["FUTURE_SOURCE_VERIFIED_605_TRIGGERED_BEHAVIOR",
             "FUTURE_GENERAL_TRIGGERED_ABILITY_REVIEW"],
            ["mana_ability_classification", "general_triggered_ability_semantics",
             "causal_mana_ability_relationship", "effect_execution_semantics"],
            ["triggered_mana_immediate_sequence", "mana_trigger_causality"],
            ["trigger_detection", "trigger_ordering", "effect_execution",
             "stack_runtime", "priority"],
            ["601.2g"],
        ),
        _capability(
            "mana_ability_controller_attribution",
            ["RETAINED_109.4a_CONSUMER", "FUTURE_SOURCE_VERIFIED_605_CLASSIFICATION",
             "SEPARATE_GENERAL_ABILITY_CONTROLLER_SOURCE_REVIEW"],
            ["mana_ability_classification", "ability_subtype_semantics",
             "general_ability_controller_semantics", "hypothetical_stack_controller_attribution"],
            ["hypothetical_stack_controller_attribution", "ability_source_controller_evidence"],
            ["controller_assignment", "general_ability_control", "trigger_control",
             "delayed_trigger_control", "real_card_effect_semantics"],
            ["109.4a"],
        ),
        _capability(
            "mana_payment_opportunity",
            ["RETAINED_601.2g_CONSUMER", "FUTURE_SOURCE_VERIFIED_605_PAYMENT_OPPORTUNITIES"],
            ["mana_ability_classification", "activated_mana_ability_activation_window",
             "determined_total_cost_mana_condition"],
            ["mana_payment_opportunity_context", "determined_cost_identity_binding"],
            ["cost_evaluation", "payment", "mana_production_semantics",
             "mana_pool_semantics"],
            ["601.2g"],
        ),
        _capability(
            "mana_production_semantics",
            ["SEPARATE_MANA_PRODUCTION_SOURCE_REVIEW", "REAL_CARD_EFFECT_OUTPUT_SEMANTICS"],
            ["effect_execution_semantics", "mana_type_and_quantity_knowledge",
             "conditional_output_semantics", "mana_output_restrictions",
             "replacement_effect_semantics", "mana_recipient_semantics"],
            ["mana_output_description", "conditional_mana_output",
             "mana_restriction_evidence", "mana_recipient_evidence"],
            ["mana_production", "real_card_effect_semantics", "replacement_effect_execution",
             "mana_pool_mutation"],
            ["601.2g"],
        ),
        _capability(
            "mana_pool_semantics",
            ["SEPARATE_MANA_POOL_SOURCE_REVIEW", "FUTURE_PAYMENT_INTEGRATION_REVIEW"],
            ["mana_production_semantics", "mana_resource_semantics", "spending_restrictions",
             "payment_integration"],
            ["future_mana_resource_contract", "future_spending_constraint_contract"],
            ["pool_representation", "pool_clearing", "mana_type_transformations",
             "special_purpose_mana", "mana_history", "mana_spending", "payment"],
            ["601.2g"],
        ),
    ]


def _reassessments(binding):
    """Derive blocked findings from the accepted unprojected dependency state."""
    shared_blockers = [
        "605_UNPROJECTED_AND_UNIMPLEMENTED", "REAL_ABILITY_CARD_EFFECT_SEMANTICS_ABSENT",
        "REQUIRED_FUTURE_PRIMITIVES_ABSENT", "DETERMINISTIC_RUNTIME_VECTORS_ABSENT",
        "OWNER_ACTIVATION_NOT_GRANTED",
    ]
    scopes = (
        ("mana_abilities", "DESIGN_SCOPED", ["601.2g", "109.4a"],
         ["ACTIVATED_AND_TRIGGERED_SEMANTICS_OPEN", "MANA_PRODUCTION_AND_POOL_ABSENT",
          "CLASSIFICATION_DOES_NOT_IMPLY_EXECUTION"]),
        ("alternative_cost_casting_subprocedure", "REPRESENTED_WITH_OPEN_DEPENDENCIES", ["601.2g"],
         ["COST_CHOICE_DEPENDENCIES_UNPROJECTED", "PAYMENT_INTEGRATION_ABSENT",
          "UNPROJECTED_CASTING_STAGES", "LEGALITY_AND_ROLLBACK_OPEN"]),
        ("complete_spell_casting", "PARTIAL_SOURCE_COVERAGE_ONLY", ["601.2g"],
         ["UNPROJECTED_CASTING_STAGES", "CASTING_PERMISSION_AND_LEGALITY_OPEN",
          "STACK_PRIORITY_AND_ROLLBACK_ABSENT", "CAST_COMPLETION_AND_TRIGGERS_ABSENT"]),
        ("object_control", "EXISTING_DESCRIPTIVE_EVIDENCE_WITH_OPEN_605_DEPENDENCY", ["109.4a"],
         ["HYPOTHETICAL_STACK_CONTROLLER_ATTRIBUTION_ABSENT",
          "GENERAL_ABILITY_CONTROLLER_SEMANTICS_OPEN", "OTHER_OBJECT_CONTROL_DEPENDENCIES_OPEN"]),
        ("madness", "EXISTING_PROJECTED_EVIDENCE_WITH_INDIRECT_OPEN_605_DEPENDENCY", ["601.2g"],
         ["INDIRECT_CASTING_DEPENDENCY_OPEN", "DISCARD_REPLACEMENT_AND_EXILE_ABSENT",
          "TRIGGER_AND_OPTIONAL_CAST_SEMANTICS_ABSENT", "PUBLIC_ZONE_FALLBACK_EXECUTION_ABSENT"]),
    )
    result = []
    for name, coverage, consumer_refs, scoped_blockers in scopes:
        consumers = [binding["consumers"][reference] for reference in consumer_refs]
        # The exact retained binding checked by the public builder and contract
        # guarantees these are open references, never implemented 605 evidence.
        open_dependency = any(row["dependency_state"] == "UNRESOLVED" and
                              row["dependency_coverage_state"] == "UNPROJECTED"
                              for row in consumers)
        blockers = shared_blockers + scoped_blockers
        if not open_dependency or not blockers:
            _fail("readiness requires the retained unresolved 605 consumer boundary")
        result.append({
            "capability_id": name,
            "retained_consumer_bindings": _json(consumers),
            "previous_casting_readiness_id": binding["bounded_casting_readiness_id"],
            "source_coverage": coverage,
            "dependency_closure": "OPEN",
            "semantic_closure": "OPEN",
            "required_primitives_available": False,
            "execution_readiness": "EXECUTION_BLOCKED",
            "execution_supported": False,
            "fictional_mana_satisfies_real_605": False,
            "blockers": blockers,
        })
    return result


def _body(binding, classification_id, behavior_id, controller_id, consumers_id, frontier_id):
    capabilities = _capabilities()
    primitives = list(dict.fromkeys(
        primitive for row in capabilities for primitive in row["required_future_primitives"]))
    return {
        "retained_evidence": binding,
        "classification_design_id": classification_id,
        "behavior_design_id": behavior_id,
        "controller_design_id": controller_id,
        "consumer_matrix_id": consumers_id,
        "projection_frontier_id": frontier_id,
        "previous_casting_readiness_id": binding["bounded_casting_readiness_id"],
        "binding_policy": "IMMUTABLE_RETAINED_RULE_IDENTITIES_NO_REPROJECTION",
        "future_605_observation_status": PM_INPUT,
        "capabilities": capabilities,
        "capability_separation": {
            "classification_implies_execution": False,
            "classification_implies_activation": False,
            "classification_implies_controller_attribution": False,
            "classification_implies_mana_production": False,
            "classification_implies_mana_pool": False,
            "activation_window_implies_immediate_resolution": False,
            "immediate_resolution_implies_mana_production": False,
            "mana_payment_opportunity_implies_payment": False,
            "one_capability_readiness_implies_another": False,
        },
        "source_coverage_vs_execution": {
            "mana_ability_source_coverage": "DESIGN_SCOPED",
            "605_coverage_state": "UNPROJECTED",
            "future_projection_may_improve_source_coverage": True,
            "mana_ability_execution": "EXECUTION_BLOCKED",
            "source_coverage_implies_execution": False,
            "future_605_projection_supplies_general_abilities": False,
            "execution_requires_independent_semantic_and_runtime_closure": True,
        },
        "production_pool_payment_boundaries": {
            "mana_production_semantics": "BLOCKED_ABSENT",
            "mana_pool_semantics": "BLOCKED_ABSENT",
            "payment_integration": "BLOCKED_ABSENT",
            "pool_representation_decided": False,
            "pool_clearing_rules_decided": False,
            "spending_restrictions_decided": False,
            "mana_transformations_decided": False,
            "special_purpose_mana_decided": False,
            "mana_history_decided": False,
        },
        "fictional_authority": {
            "finding": "FICTIONAL_MANA_DOES_NOT_SATISFY_REAL_605",
            "fictional_mana_satisfies_real_605": False,
            "fictional_runtime_authority_inherited": False,
            "fictional_kernel_accepted_as_real_evidence": False,
            "fictional_mana_output_accepted_as_real_evidence": False,
            "fictional_controller_behavior_accepted_as_real_evidence": False,
            "architectural_reuse_grants_rules_authority": False,
            "accepted_real_605_execution_authority_proofs": [],
        },
        "consumer_flow": {
            "direct_consumers": _json(binding["consumers"]),
            "madness_flow_kind": "INDIRECT_DEPENDENCY_FLOW",
            "madness_path": ["702.35b", "BOUNDED_CASTING_PROJECTION", "601.2g", "605"],
            "madness_direct_605_citation_created": False,
            "retained_madness_rules": _json(binding["madness_rules"]),
            "retained_zone_change_lookup": _json(binding["zone_change_lookup"]),
            "controller_attribution_separate_from_casting": True,
        },
        "readiness_reassessments": _reassessments(binding),
        "required_future_primitives": primitives,
        "real_execution_primitives_available": [],
        "remaining_unprojected_numbered_boundaries": list(dict.fromkeys(
            [*EXISTING_UNPROJECTED_REFERENCES, *CANDIDATE_OUTGOING_REFERENCES])),
        "candidate_reference_status": "CANDIDATE_DIRECT_REFERENCE_REQUIRES_SOURCE_VERIFICATION",
        "projected_rule_count_before": 68,
        "source_projections_added": 0,
        "projected_rule_count_after": 68,
        "overall_readiness": "EXECUTION_BLOCKED",
        "real_execution_profile_readiness": "REAL_EXECUTION_PROFILE_NOT_READY",
        "limitations": [
            "No real ability is classified, activated, detected, resolved, or assigned a controller.",
            "No mana is produced, pooled, spent, or used to pay a cost.",
            "The two retained consumers impose different future requirements; casting evidence does not close attribution.",
            "The proposed 605 family and outgoing references remain source-unverified design input.",
            "Source coverage, classification, present productivity, activation eligibility, and execution are separate concerns.",
        ],
        "design_notes": [
            "The shared 605 dependency is scoped without new source verification; each consumer and capability remains blocked independently."
        ],
    }


@dataclass(frozen=True)
class ManaAbilityReadiness(DesignRecord):
    """Immutable design findings; identities do not confer execution approval."""

    SCHEMA = "mana-ability-readiness-design-v1"
    ID_FIELD = "readiness_id"
    BODY_FIELDS = frozenset(_body(_json(RETAINED_BINDING), "", "", "", "", ""))

    @staticmethod
    def _validate_body(body):
        id_fields = (
            "classification_design_id", "behavior_design_id", "controller_design_id",
            "consumer_matrix_id", "projection_frontier_id", "previous_casting_readiness_id",
        )
        for field in id_fields:
            _hash(body[field], field)
        _exact(body["retained_evidence"], RETAINED_BINDING, "retained_evidence")
        expected = _body(
            body["retained_evidence"], body["classification_design_id"],
            body["behavior_design_id"], body["controller_design_id"],
            body["consumer_matrix_id"], body["projection_frontier_id"],
        )
        for field, value in expected.items():
            if field != "design_notes":
                _exact(body[field], value, field)
        _strings(body["design_notes"], "design_notes", nonempty=True)


def build_readiness(binding, classification, behavior, controller, consumers, frontier,
                    *, design_notes=None):
    """Bind exact typed, verified design records to retained unresolved evidence."""
    _exact(_json(binding), RETAINED_BINDING, "retained_evidence")
    for record, concrete_type in (
        (classification, ManaAbilityClassificationDesign),
        (behavior, ManaAbilityBehaviorDesign),
        (controller, ManaAbilityControllerDesign),
        (consumers, ManaAbilityConsumerMatrix),
        (frontier, ManaAbilityProjectionFrontier),
    ):
        if type(record) is not concrete_type:
            _fail("readiness requires exact typed non-executable design records")
        record.verify()
    for record in (consumers, frontier):
        for field, expected in (
            ("classification_design_id", classification.identity),
            ("behavior_design_id", behavior.identity),
            ("controller_design_id", controller.identity),
        ):
            _exact(record.to_dict()[field], expected, "readiness_" + field)
    _exact(_json(consumers.retained_evidence_binding), binding, "consumer_retained_evidence")
    _exact(_json(controller.consumer_binding), binding["consumers"]["109.4a"],
           "controller_retained_consumer")
    body = _body(
        _json(binding), classification.identity, behavior.identity, controller.identity,
        consumers.identity, frontier.identity,
    )
    if design_notes is not None:
        body["design_notes"] = _json(design_notes)
    return ManaAbilityReadiness.create(body)
