"""Separate hypothetical controller attribution from actual stack behavior."""
from __future__ import annotations

from dataclasses import dataclass

from .common import DesignRecord, PM_INPUT, _exact, _fail, _json, _text


_CONSUMER = {
    "rule_reference": "109.4a",
    "rule_id": "sha256:7793b14d8f2af5916dd02316ff0ea817d77b0bf656284c0f56d86b3f743fcea1",
    "projection_id": "sha256:f4b75e686bfb5202f54818dc4fc9247a49a6e6ef84e2d57f070e990c25b6cce9",
    "direct_dependency_references": ["605"],
    "coverage_state": "EXISTING_PROJECTED_EVIDENCE_UNCHANGED",
    "dependency_state": "UNRESOLVED",
    "dependency_coverage_state": "UNPROJECTED",
}


def _body():
    return {
        "consumer_binding": _json(_CONSUMER),
        "retained_consumer_evidence_status": "EXISTING_PROJECTED_EVIDENCE_UNCHANGED",
        "future_605_observation_status": PM_INPUT,
        "attribution_model": {
            "capability": "mana_ability_controller_attribution",
            "primitive_concept": "hypothetical_stack_controller_attribution",
            "retained_consumer_relationship": "DETERMINE_CONTROLLER_AS_THOUGH_ABILITY_WERE_ON_STACK",
            "actual_stack_presence": "DISTINCT_FROM_HYPOTHETICAL_ATTRIBUTION",
            "actual_stack_presence_required": False,
            "hypothetical_stack_controller_attribution": "FUTURE_SEMANTIC_PRIMITIVE",
            "qualifying_mana_ability_no_stack_concept": "PM_INPUT_REQUIRES_FUTURE_SOURCE_VERIFICATION",
            "stack_object_created_for_attribution": False,
            "controller_assigned": False,
            "fictional_controller_authority_inherited": False,
        },
        "subtype_attribution": [
            {
                "ability_subtype": "ACTIVATED",
                "classification_dependency": "ACTIVATED_MANA_ABILITY_CLASSIFICATION",
                "controller_basis": "UNKNOWN_GENERAL_ABILITY_CONTROLLER_SEMANTICS",
                "hypothetical_attribution_required": True,
                "source_review_required": True,
                "execution_supported": False,
            },
            {
                "ability_subtype": "TRIGGERED",
                "classification_dependency": "TRIGGERED_MANA_ABILITY_CLASSIFICATION",
                "controller_basis": "UNKNOWN_GENERAL_TRIGGER_CONTROLLER_SEMANTICS",
                "hypothetical_attribution_required": True,
                "source_review_required": True,
                "execution_supported": False,
            },
            {
                "ability_subtype": "GENERAL_OR_UNKNOWN",
                "classification_dependency": "UNRESOLVED",
                "controller_basis": "UNKNOWN_REQUIRES_SEPARATE_SOURCE_REVIEW",
                "hypothetical_attribution_required": "UNKNOWN",
                "source_review_required": True,
                "execution_supported": False,
            },
            {
                "ability_subtype": "DELAYED_TRIGGER",
                "classification_dependency": "OUTSIDE_THIS_DESIGN",
                "controller_basis": "UNKNOWN_REQUIRES_SEPARATE_SOURCE_REVIEW",
                "hypothetical_attribution_required": "UNKNOWN",
                "source_review_required": True,
                "execution_supported": False,
            },
        ],
        "capability_requirements": {
            "evidence_requirements": [
                "RETAINED_109.4a_RULE_IDENTITY",
                "FUTURE_SOURCE_VERIFIED_605_CLASSIFICATION",
                "SEPARATE_GENERAL_ABILITY_CONTROLLER_SOURCE_REVIEW",
            ],
            "semantic_dependencies": [
                "mana_ability_classification", "ability_subtype_semantics",
                "general_ability_controller_semantics",
                "hypothetical_stack_controller_attribution",
            ],
            "future_primitives": [
                "hypothetical_stack_controller_attribution",
                "ability_source_controller_evidence",
            ],
            "readiness_status": "BLOCKED",
            "implementation_status": "NOT_IMPLEMENTED",
            "unsupported_boundaries": [
                "actual_controller_assignment", "general_ability_control",
                "trigger_control", "delayed_trigger_control", "stack_runtime",
                "real_ability_semantics", "card_effect_semantics",
            ],
            "implied_ready_capabilities": [],
        },
        "boundaries": {
            "mana_ability_classification_implies_controller": False,
            "casting_source_coverage_implies_controller": False,
            "future_605_projection_closes_general_control": False,
            "hypothetical_attribution_requires_actual_stack_object": False,
            "general_controller_semantics": "UNKNOWN_REQUIRES_SEPARATE_SOURCE_REVIEW",
            "runtime_controller_assignment": "ABSENT",
            "source_coverage_implies_execution": False,
        },
        "candidate_numbered_dependencies": [],
        "additional_numbered_dependency_policy": "DO_NOT_INVENT_REFERENCES_FOR_UNVERIFIED_GENERAL_CONTROLLER_BOUNDARIES",
        "design_notes": [
            "The retained 109.4a consumer requires a hypothetical attribution operation; an actual stack object is not a prerequisite.",
            "Activated, triggered, general, and delayed controller semantics remain distinct unresolved review boundaries.",
        ],
    }


@dataclass(frozen=True)
class ManaAbilityControllerDesign(DesignRecord):
    """Controller requirements with no controller selection or assignment."""

    SCHEMA = "mana-ability-controller-design-v1"
    ID_FIELD = "controller_design_id"
    BODY_FIELDS = frozenset(_body())

    @staticmethod
    def _validate_body(body):
        for field, expected in _body().items():
            if field != "design_notes":
                _exact(body[field], expected, field)
        notes = body["design_notes"]
        if not isinstance(notes, list) or not notes or len(notes) > 64:
            _fail("design_notes: bounded nonempty list required")
        for note in notes:
            _text(note, "design_notes")


def build_controller_design(binding, *, design_notes=None):
    """Bind the retained consumer identity; do not determine a controller."""
    try:
        consumer = _json(binding)["consumers"]["109.4a"]
    except (TypeError, KeyError, AttributeError):
        _fail("controller design requires the retained 109.4a consumer binding")
    _exact(consumer, _CONSUMER, "109.4a retained consumer")
    body = _body()
    if design_notes is not None:
        body["design_notes"] = _json(design_notes)
    return ManaAbilityControllerDesign.create(body)
