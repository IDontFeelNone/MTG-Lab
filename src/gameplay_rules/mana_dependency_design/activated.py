"""Review-only scope for general activation, separate from mana exceptions.

Descriptions of the unprojected 602.2 family are PM design input.  Nothing in
this module announces an ability, creates a stack object, or imports casting
runtime.  A source-coverage candidate is not an authorized projection.
"""
from dataclasses import dataclass
from typing import ClassVar

from .common import DesignRecord, PM_INPUT, _exact, _json, _keys, _strings


ACTIVATED_PROCEDURE_CAPABILITIES = (
    "ability_kind_classification", "activation_authority_and_controller",
    "ability_announcement", "ability_stack_object_creation", "activation_cost",
    "casting_procedure_reuse", "ability_payment", "activation_legality",
    "illegal_activation_rollback", "ability_resolution",
)
ACTIVATED_CANDIDATE_SCOPE = ("602.2", "602.2a", "602.2b")
PROJECTED_CASTING_REUSE = ("601.2b", "601.2f", "601.2g", "601.2h")
UNPROJECTED_CASTING_REUSE = ("601.2c", "601.2d", "601.2e", "601.2i")


def _concepts():
    details = (
        ("ability_kind_classification", "Real ability-kind evidence", ["real_ability_kind"], ["real_card_and_effect_semantics"]),
        ("activation_authority_and_controller", "Authority and controller rules", ["activation_authority", "activated_ability_controller"], ["permanent_and_player_state", "general_controller_semantics"]),
        ("ability_announcement", "Announcement procedure", ["ability_announcement_declaration"], ["proposal_legality", "ability_identity"]),
        ("ability_stack_object_creation", "Stack object creation rules", ["ability_stack_object_identity"], ["general_stack_semantics"]),
        ("activation_cost", "Activation-cost semantics", ["activation_cost_basis"], ["real_card_and_effect_semantics", "cost_declarations"]),
        ("casting_procedure_reuse", "Verified casting-to-activation mapping", ["activation_procedure_stage_mapping"], ["unprojected_casting_stages", "cost_semantics"]),
        ("ability_payment", "All required payment rules", ["locked_activation_cost_payment_plan"], ["mana_payment", "nonmana_payment"]),
        ("activation_legality", "Legality and permission rules", ["activation_legality_evidence"], ["timing", "permissions", "prohibitions"]),
        ("illegal_activation_rollback", "Illegal-action handling", ["illegal_activation_rollback_contract"], ["733", "state_history"]),
        ("ability_resolution", "General effect resolution rules", ["ability_resolution_contract"], ["effect_execution", "stack_resolution"]),
    )
    return [{
        "capability": capability, "evidence_requirements": [requirement],
        "future_primitives": primitives, "semantic_dependencies": dependencies,
        "readiness_status": "BLOCKED", "execution_readiness": "NOT_IMPLEMENTED",
        "implementation_available": False, "execution_supported": False,
        "independently_scoped": True, "implied_ready_capabilities": [],
        "evidence_status": PM_INPUT, "source_verified": False,
    } for capability, requirement, primitives, dependencies in details]


def _body(notes):
    return {
        "evidence_status": PM_INPUT,
        "frontier_reference": "602.2",
        "subsystem": "general_activated_ability_procedure",
        "classification": "LARGE_CORE_SUBSYSTEM",
        "scope_assessment": {
            "source_scope_size": "SMALL_LOCAL_FAMILY_WITH_LARGE_TRANSITIVE_SUBSYSTEM",
            "semantic_responsibility": "GENERAL_ORDERED_ACTIVATION_PROCEDURE",
            "consumer_value": ["605.3", "future_general_activated_abilities"],
            "implementation_risk": "HIGH",
            "design_before_projection_required": True,
            "detailed_subsystem_design_complete": False,
            "local_source_scope_provisionally_coherent": True,
            "projection_ready": False,
            "dedicated_design_milestone_ready": True,
            "source_verified": False,
        },
        "capabilities": _concepts(),
        "candidate_source_scope": {
            "exact_provisional_refs": list(ACTIVATED_CANDIDATE_SCOPE),
            "proposed_source_unit_count": 3,
            "unit_roles": [
                {"rule_reference": "602.2", "role": "PARENT_ORDERED_PROCEDURE_AUTHORITY_LEGALITY_AND_ROLLBACK_CONTEXT"},
                {"rule_reference": "602.2a", "role": "ANNOUNCEMENT_ABILITY_STACK_OBJECT_AND_CONTROLLER_CONTEXT"},
                {"rule_reference": "602.2b", "role": "CASTING_PROCEDURE_REUSE_AND_ACTIVATION_COST_MAPPING"},
            ],
            "coherence_finding": "PROVISIONALLY_COHERENT_LOCAL_SOURCE_COVERAGE_CLUSTER",
            "coherence_rationale": "Keep the proposed parent with both immediate procedure children; its external execution requirements can remain explicit.",
            "exact_source_shape_requires_verification": True,
            "requires_dedicated_design_before_admission": True,
            "source_coverage_implies_execution": False,
            "evidence_status": PM_INPUT, "source_verified": False,
            "coverage_state": "UNPROJECTED", "authorized": False,
        },
        "casting_reuse_design": {
            "evidence_status": PM_INPUT, "source_verified": False,
            "candidate_origin": "602.2b",
            "candidate_imported_range": "601.2b-i",
            "candidate_cost_mapping": "SPELL_MANA_COST_CONCEPT_TO_ABILITY_ACTIVATION_COST_CONCEPT",
            "retained_projected_stage_references": list(PROJECTED_CASTING_REUSE),
            "unprojected_stage_references": list(UNPROJECTED_CASTING_REUSE),
            "range_members": [
                {"rule_reference": "601.2" + suffix,
                 "coverage_state": "PREVIOUSLY_PROJECTED" if "601.2" + suffix in PROJECTED_CASTING_REUSE else "UNPROJECTED_CASTING_STAGE",
                 "import_relationship_status": "PM_DESIGN_OBSERVATION_REQUIRES_FUTURE_SOURCE_VERIFICATION",
                 "execution_supported": False}
                for suffix in "bcdefghi"
            ],
            "existing_casting_projection_satisfies_complete_reuse": False,
            "casting_runtime_imported": False,
        },
        "candidate_outgoing_dependencies": [
            {"originating_candidate_rule": "602.2", "target_reference": "733",
             "concern": "ILLEGAL_ACTION_ROLLBACK",
             "dependency_status": "CANDIDATE_DIRECT_REFERENCE_REQUIRES_SOURCE_VERIFICATION",
             "evidence_status": PM_INPUT, "source_verified": False, "coverage_state": "UNPROJECTED"},
            {"originating_candidate_rule": "602.2a", "target_reference": "701.20a",
             "concern": "HIDDEN_ZONE_REVEAL",
             "dependency_status": "CANDIDATE_DIRECT_REFERENCE_REQUIRES_SOURCE_VERIFICATION",
             "evidence_status": PM_INPUT, "source_verified": False, "coverage_state": "UNPROJECTED"},
        ],
        "general_special_relationship": {
            "general_procedure": {"reference": "602.2", "role": "GENERAL_PROCEDURE",
                                  "concept": "ORDINARY_ACTIVATED_ABILITY_STACK_PROCEDURE",
                                  "evidence_status": PM_INPUT, "source_verified": False},
            "mana_exception": {"retained_reference": "605.3b", "role": "MANA_ABILITY_EXCEPTION",
                               "supporting_unprojected_context": "405.6c"},
            "relationship_kind": "GENERAL_PROCEDURE_PLUS_MANA_ABILITY_EXCEPTION",
            "relationship_design_authority": "SCOPING_JUDGMENT_USING_PM_OBSERVATIONS_AND_RETAINED_EXCEPTION",
            "applicability_condition": "QUALIFYING_ACTIVATED_MANA_ABILITY",
            "general_stack_statement_is_unconditional": False,
            "mana_exception_overwrites_general_rule": False,
            "mana_exception_satisfies_general_activation": False,
            "new_direct_citation_created": False,
            "runtime_dispatch_created": False,
        },
        "deliberately_unresolved": ["733", "701.20a", *UNPROJECTED_CASTING_REUSE,
            "activation_authority", "general_controller_semantics", "ability_stack_objects",
            "real_ability_and_effect_semantics", "ability_payment", "legality", "rollback", "resolution"],
        "limitations": [
            "The local three-unit candidate describes source coverage only; it cannot close general activation.",
            "The casting-stage import and new outgoing reference candidates are PM observations, not newly verified citations.",
            "Retained 605 exceptions remain immutable and separate from the proposed general procedure.",
        ],
        "design_notes": notes,
    }


@dataclass(frozen=True)
class ActivatedAbilityDependencyDesign(DesignRecord):
    SCHEMA: ClassVar[str] = "gameplay-rules-activated-ability-dependency-design-v1"
    ID_FIELD: ClassVar[str] = "activated_procedure_design_id"
    BODY_FIELDS: ClassVar[frozenset[str]] = frozenset(_body([]))

    @staticmethod
    def _validate_body(body):
        _keys(body, ActivatedAbilityDependencyDesign.BODY_FIELDS)
        _strings(body["design_notes"], "design_notes")
        _exact(body, _body(body["design_notes"]), "activated_procedure_design")


def build_activated_design(*, design_notes=None):
    return ActivatedAbilityDependencyDesign.create(_body([] if design_notes is None else _json(design_notes)))
