"""Authored mana-classification declarations, never an ability classifier.

The predicates described here are PM scoping input awaiting source review.
Synthetic declarations carry a caller-supplied hypothetical classification;
validation checks data coherence and missing information, not real abilities.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .common import (
    DesignRecord, PM_INPUT, _enum, _exact, _fail, _integer, _json,
    _strings, _text,
)


CLASSIFICATION_STATES = (
    "MANA_ABILITY", "NOT_MANA_ABILITY", "INDETERMINATE", "UNSUPPORTED",
)
KNOWLEDGE_STATES = ("KNOWN_SYNTHETIC_ONLY", "UNKNOWN", "UNSUPPORTED")
ACTIVATION_STATES = ("ELIGIBLE", "INELIGIBLE", "UNKNOWN", "UNSUPPORTED")
TRIGGER_SOURCE_CATEGORIES = (
    "ACTIVATED_MANA_ABILITY_ACTIVATION", "ACTIVATED_MANA_ABILITY_RESOLUTION",
    "MANA_ADDED", "OTHER", "MULTIPLE_DECLARED_RELATIONSHIPS", "UNKNOWN",
    "UNSUPPORTED",
)
_DECLARATION_FLAGS = {
    "fixture_kind": "SYNTHETIC_ONLY",
    "hypothetical_only": True,
    "classification_evaluated": False,
    "classification_source": "CALLER_SUPPLIED_HYPOTHETICAL_DECLARATION",
    "source_evidence_state": "SYNTHETIC_FIXTURE_ONLY",
    "execution_readiness": "NOT_IMPLEMENTED",
    "execution_implied": False,
    "classification_implies_current_output": False,
    "classification_implies_current_activation": False,
}


def _synthetic(value: Any, field: str) -> None:
    _text(value, field, maximum=256)
    if not value.startswith("synthetic-"):
        _fail(field + ": only synthetic fixture references are permitted")


def _tristate(value: Any, field: str) -> None:
    if value is not None and type(value) is not bool:
        _fail(field + ": true, false, or null declaration required")


def _common_declaration(body: dict[str, Any]) -> None:
    for field, value in _DECLARATION_FLAGS.items():
        _exact(body[field], value, field)
    _synthetic(body["synthetic_ability_reference"], "synthetic_ability_reference")
    _enum(body["classification"], CLASSIFICATION_STATES, "classification")
    _strings(body["unknown_fields"], "unknown_fields")
    _strings(body["exclusion_metadata"], "exclusion_metadata")


def _unknowns(body: dict[str, Any], booleans: tuple[str, ...],
              knowledge: tuple[str, ...], additional: tuple[str, ...] = ()) -> list[str]:
    """Inventory missing declaration fields without classifying an ability."""
    fields = [field for field in booleans if body[field] is None]
    fields += [field for field in knowledge if body[field] != "KNOWN_SYNTHETIC_ONLY"]
    fields += [field for field in additional
               if type(body[field]) is not str or body[field] in {"UNKNOWN", "UNSUPPORTED"}]
    return sorted(fields)


def _declared_outcome(body: dict[str, Any], unknown_fields: list[str],
                      possible_exclusions: dict[str, bool]) -> None:
    _exact(body["unknown_fields"], unknown_fields, "unknown_fields")
    if unknown_fields and body["classification"] not in {"INDETERMINATE", "UNSUPPORTED"}:
        _fail("classification: incomplete synthetic inputs must fail closed")
    for exclusion in body["exclusion_metadata"]:
        if exclusion not in possible_exclusions or not possible_exclusions[exclusion]:
            _fail("exclusion_metadata: exclusion does not match the supplied synthetic fields")
    if body["classification"] == "MANA_ABILITY":
        if any(possible_exclusions.values()) or body["exclusion_metadata"]:
            _fail("classification: a declared exclusion cannot accompany hypothetical mana classification")
    if body["classification"] == "NOT_MANA_ABILITY" and not body["exclusion_metadata"]:
        _fail("classification: hypothetical exclusion requires explicit metadata")


_ACTIVATED_BOOLEAN_FIELDS = (
    "has_target", "could_add_mana_on_resolution", "library_movement_in_cost",
    "library_movement_in_effect",
)
_ACTIVATED_KNOWLEDGE_FIELDS = (
    "self_replacement_knowledge", "other_replacement_effect_knowledge",
    "card_effect_semantics_availability",
)
_ACTIVATED_FIELDS = frozenset(_DECLARATION_FLAGS) | {
    "synthetic_ability_reference", "ability_kind", "has_target",
    "could_add_mana_on_resolution", "loyalty_ability_status",
    "library_movement_in_cost", "library_movement_in_effect",
    "self_replacement_knowledge", "other_replacement_effect_knowledge",
    "card_effect_semantics_availability", "classification", "unknown_fields",
    "exclusion_metadata",
}


@dataclass(frozen=True)
class ActivatedManaClassificationInputDesign(DesignRecord):
    """Immutable activated-input fixture with an asserted, unevaluated result."""

    SCHEMA = "synthetic-activated-mana-classification-input-design-v1"
    ID_FIELD = "activated_input_design_id"
    BODY_FIELDS = frozenset(_ACTIVATED_FIELDS)

    @staticmethod
    def _validate_body(body: dict[str, Any]) -> None:
        _common_declaration(body)
        _exact(body["ability_kind"], "ACTIVATED", "ability_kind")
        for field in _ACTIVATED_BOOLEAN_FIELDS:
            _tristate(body[field], field)
        _enum(body["loyalty_ability_status"], ("YES", "NO", "UNKNOWN", "UNSUPPORTED"),
              "loyalty_ability_status")
        for field in _ACTIVATED_KNOWLEDGE_FIELDS:
            _enum(body[field], KNOWLEDGE_STATES, field)
        _declared_outcome(
            body,
            _unknowns(body, _ACTIVATED_BOOLEAN_FIELDS, _ACTIVATED_KNOWLEDGE_FIELDS,
                      ("loyalty_ability_status",)),
            {
                "TARGETED_ABILITY": body["has_target"] is True,
                "CANNOT_ADD_MANA_ON_RESOLUTION": body["could_add_mana_on_resolution"] is False,
                "LOYALTY_ABILITY": body["loyalty_ability_status"] == "YES",
                "LIBRARY_MOVEMENT_IN_COST": body["library_movement_in_cost"] is True,
                "LIBRARY_MOVEMENT_IN_EFFECT": body["library_movement_in_effect"] is True,
            },
        )


def build_activated_classification_input(
    *, synthetic_ability_reference: str = "synthetic-activated-ability-alpha",
    has_target: bool | None = None,
    could_add_mana_on_resolution: bool | None = None,
    loyalty_ability_status: str = "UNKNOWN",
    library_movement_in_cost: bool | None = None,
    library_movement_in_effect: bool | None = None,
    self_replacement_knowledge: str = "UNKNOWN",
    other_replacement_effect_knowledge: str = "UNKNOWN",
    card_effect_semantics_availability: str = "UNKNOWN",
    classification: str = "INDETERMINATE", exclusion_metadata: Any = (),
) -> ActivatedManaClassificationInputDesign:
    """Validate a supplied fictional declaration; never infer classification."""
    body = {
        **_DECLARATION_FLAGS,
        "synthetic_ability_reference": synthetic_ability_reference,
        "ability_kind": "ACTIVATED", "has_target": has_target,
        "could_add_mana_on_resolution": could_add_mana_on_resolution,
        "loyalty_ability_status": loyalty_ability_status,
        "library_movement_in_cost": library_movement_in_cost,
        "library_movement_in_effect": library_movement_in_effect,
        "self_replacement_knowledge": self_replacement_knowledge,
        "other_replacement_effect_knowledge": other_replacement_effect_knowledge,
        "card_effect_semantics_availability": card_effect_semantics_availability,
        "classification": classification,
        "exclusion_metadata": _json(exclusion_metadata),
    }
    body["unknown_fields"] = _unknowns(
        body, _ACTIVATED_BOOLEAN_FIELDS, _ACTIVATED_KNOWLEDGE_FIELDS,
        ("loyalty_ability_status",),
    )
    return ActivatedManaClassificationInputDesign.create(body)


_TRIGGERED_BOOLEAN_FIELDS = (
    "has_target", "triggered_by_activated_mana_ability_activation",
    "triggered_by_activated_mana_ability_resolution", "triggered_by_mana_added",
    "could_add_mana_on_resolution",
)
_TRIGGERED_KNOWLEDGE_FIELDS = (
    "source_semantics_knowledge", "dependency_semantics_knowledge",
)
_TRIGGERED_FIELDS = frozenset(_DECLARATION_FLAGS) | {
    "synthetic_ability_reference", "ability_kind", "has_target",
    "trigger_source_category", "triggered_by_activated_mana_ability_activation",
    "triggered_by_activated_mana_ability_resolution", "triggered_by_mana_added",
    "could_add_mana_on_resolution", "source_semantics_knowledge",
    "dependency_semantics_knowledge", "classification", "unknown_fields",
    "exclusion_metadata",
}


@dataclass(frozen=True)
class TriggeredManaClassificationInputDesign(DesignRecord):
    """A separate triggered-input declaration; it detects no triggers."""

    SCHEMA = "synthetic-triggered-mana-classification-input-design-v1"
    ID_FIELD = "triggered_input_design_id"
    BODY_FIELDS = frozenset(_TRIGGERED_FIELDS)

    @staticmethod
    def _validate_body(body: dict[str, Any]) -> None:
        _common_declaration(body)
        _exact(body["ability_kind"], "TRIGGERED", "ability_kind")
        for field in _TRIGGERED_BOOLEAN_FIELDS:
            _tristate(body[field], field)
        for field in _TRIGGERED_KNOWLEDGE_FIELDS:
            _enum(body[field], KNOWLEDGE_STATES, field)
        _enum(body["trigger_source_category"], TRIGGER_SOURCE_CATEGORIES,
              "trigger_source_category")
        relationship_fields = (
            "triggered_by_activated_mana_ability_activation",
            "triggered_by_activated_mana_ability_resolution", "triggered_by_mana_added",
        )
        categories = TRIGGER_SOURCE_CATEGORIES[:3]
        category = body["trigger_source_category"]
        if category in categories:
            index = categories.index(category)
            if body[relationship_fields[index]] is not True:
                _fail("trigger_source_category: declared category must match its relationship field")
            if any(body[field] is True for field in relationship_fields
                   if field != relationship_fields[index]):
                _fail("trigger_source_category: multiple known relationships require the multiple category")
        if category == "OTHER" and any(body[field] is True for field in relationship_fields):
            _fail("trigger_source_category: OTHER cannot claim a qualifying relationship")
        if category == "MULTIPLE_DECLARED_RELATIONSHIPS" and sum(
                body[field] is True for field in relationship_fields) < 2:
            _fail("trigger_source_category: multiple relationship declarations required")
        _declared_outcome(
            body,
            _unknowns(body, _TRIGGERED_BOOLEAN_FIELDS, _TRIGGERED_KNOWLEDGE_FIELDS,
                      ("trigger_source_category",)),
            {
                "TARGETED_ABILITY": body["has_target"] is True,
                "CANNOT_ADD_MANA_ON_RESOLUTION": body["could_add_mana_on_resolution"] is False,
                "WRONG_TRIGGER_RELATIONSHIP": all(body[field] is False for field in relationship_fields),
            },
        )


def build_triggered_classification_input(
    *, synthetic_ability_reference: str = "synthetic-triggered-ability-alpha",
    has_target: bool | None = None, trigger_source_category: str = "UNKNOWN",
    triggered_by_activated_mana_ability_activation: bool | None = None,
    triggered_by_activated_mana_ability_resolution: bool | None = None,
    triggered_by_mana_added: bool | None = None,
    could_add_mana_on_resolution: bool | None = None,
    source_semantics_knowledge: str = "UNKNOWN",
    dependency_semantics_knowledge: str = "UNKNOWN",
    classification: str = "INDETERMINATE", exclusion_metadata: Any = (),
) -> TriggeredManaClassificationInputDesign:
    """Store distinct trigger relationships without detecting or firing one."""
    body = {
        **_DECLARATION_FLAGS,
        "synthetic_ability_reference": synthetic_ability_reference,
        "ability_kind": "TRIGGERED", "has_target": has_target,
        "trigger_source_category": trigger_source_category,
        "triggered_by_activated_mana_ability_activation": triggered_by_activated_mana_ability_activation,
        "triggered_by_activated_mana_ability_resolution": triggered_by_activated_mana_ability_resolution,
        "triggered_by_mana_added": triggered_by_mana_added,
        "could_add_mana_on_resolution": could_add_mana_on_resolution,
        "source_semantics_knowledge": source_semantics_knowledge,
        "dependency_semantics_knowledge": dependency_semantics_knowledge,
        "classification": classification,
        "exclusion_metadata": _json(exclusion_metadata),
    }
    body["unknown_fields"] = _unknowns(
        body, _TRIGGERED_BOOLEAN_FIELDS, _TRIGGERED_KNOWLEDGE_FIELDS,
        ("trigger_source_category",),
    )
    return TriggeredManaClassificationInputDesign.create(body)


_PERSISTENCE_FIELDS = frozenset({
    "fixture_kind", "hypothetical_only", "classification_evaluated",
    "classification_input_kind", "classification_input", "classification_input_id",
    "classification", "current_activation_eligibility", "current_mana_output_known",
    "current_mana_output_amount", "current_game_state_constraints",
    "classification_recomputed_from_current_state", "activation_evaluated",
    "mana_output_calculated", "execution_readiness", "execution_implied",
})


@dataclass(frozen=True)
class ClassificationPersistenceDesign(DesignRecord):
    """Separately declared output and activation never recalculate classification."""

    SCHEMA = "synthetic-mana-classification-persistence-design-v1"
    ID_FIELD = "persistence_design_id"
    BODY_FIELDS = _PERSISTENCE_FIELDS

    @staticmethod
    def _validate_body(body: dict[str, Any]) -> None:
        for field, expected in {
            "fixture_kind": "SYNTHETIC_ONLY", "hypothetical_only": True,
            "classification_evaluated": False,
            "classification_recomputed_from_current_state": False,
            "activation_evaluated": False, "mana_output_calculated": False,
            "execution_readiness": "NOT_IMPLEMENTED", "execution_implied": False,
        }.items():
            _exact(body[field], expected, field)
        classes = {
            "ACTIVATED": ActivatedManaClassificationInputDesign,
            "TRIGGERED": TriggeredManaClassificationInputDesign,
        }
        _enum(body["classification_input_kind"], classes, "classification_input_kind")
        declaration = classes[body["classification_input_kind"]].from_dict(body["classification_input"])
        _exact(body["classification_input_id"], declaration.identity, "classification_input_id")
        _exact(body["classification"], declaration.classification, "classification")
        _enum(body["current_activation_eligibility"], ACTIVATION_STATES,
              "current_activation_eligibility")
        if type(body["current_mana_output_known"]) is not bool:
            _fail("current_mana_output_known: boolean declaration required")
        if body["current_mana_output_known"]:
            _integer(body["current_mana_output_amount"], "current_mana_output_amount")
        else:
            _exact(body["current_mana_output_amount"], None, "current_mana_output_amount")
        _strings(body["current_game_state_constraints"], "current_game_state_constraints")
        for constraint in body["current_game_state_constraints"]:
            _synthetic(constraint, "current_game_state_constraints")


def build_classification_persistence(
    classification_input: ActivatedManaClassificationInputDesign | TriggeredManaClassificationInputDesign,
    *, current_activation_eligibility: str = "UNKNOWN",
    current_mana_output_known: bool = False,
    current_mana_output_amount: int | None = None,
    current_game_state_constraints: Any = (),
) -> ClassificationPersistenceDesign:
    """Bind manually supplied current-state metadata to one unchanged declaration."""
    if type(classification_input) not in {
            ActivatedManaClassificationInputDesign, TriggeredManaClassificationInputDesign}:
        _fail("classification_input: exact synthetic input contract required")
    classification_input.verify()
    return ClassificationPersistenceDesign.create({
        "fixture_kind": "SYNTHETIC_ONLY", "hypothetical_only": True,
        "classification_evaluated": False,
        "classification_input_kind": classification_input.ability_kind,
        "classification_input": classification_input.to_dict(),
        "classification_input_id": classification_input.identity,
        "classification": classification_input.classification,
        "current_activation_eligibility": current_activation_eligibility,
        "current_mana_output_known": current_mana_output_known,
        "current_mana_output_amount": current_mana_output_amount,
        "current_game_state_constraints": _json(current_game_state_constraints),
        "classification_recomputed_from_current_state": False,
        "activation_evaluated": False, "mana_output_calculated": False,
        "execution_readiness": "NOT_IMPLEMENTED", "execution_implied": False,
    })


def _body() -> dict[str, Any]:
    return {
        "evidence_status": PM_INPUT,
        "release_concept": "2026-09-25",
        "source_605_status": "UNPROJECTED_NOT_SOURCE_VERIFIED",
        "classification_states": list(CLASSIFICATION_STATES),
        "execution_states": ["NOT_IMPLEMENTED", "BLOCKED", "UNSUPPORTED"],
        "classification_and_execution_independent": True,
        "classification_implies_execution": False,
        "classification_implies_mana_production": False,
        "classification_implies_mana_pool_semantics": False,
        "classification_implies_current_activation": False,
        "real_classifier_available": False,
        "real_card_effect_semantics": "ABSENT",
        "input_authority": "SYNTHETIC_DECLARATIONS_ONLY",
        "activated_input_design": {
            "ability_kind": "ACTIVATED",
            "fields": sorted(_ACTIVATED_FIELDS),
            "required_concepts": [
                "target_requirement", "could_add_mana_on_resolution",
                "loyalty_ability_status", "library_movement_in_cost",
                "library_movement_in_effect", "applicable_self_replacement_information",
                "other_replacement_effect_knowledge", "source_evidence_state",
                "card_effect_semantics_availability", "unknown_fields",
            ],
            "replacement_effect_distinction": {
                "self_replacement": "SEPARATE_APPLICABILITY_INFORMATION_REQUIRED",
                "other_replacement_effects": "SEPARATE_KNOWLEDGE_NOT_A_CLASSIFICATION_RUNTIME",
                "source_verification_required": True,
            },
            "candidate_external_references": ["115.6", "606"],
            "reference_status": "CANDIDATE_DIRECT_REFERENCE_REQUIRES_SOURCE_VERIFICATION",
            "excluded_case_design": [
                "TARGETED_ABILITY", "LOYALTY_ABILITY", "LIBRARY_MOVEMENT_IN_COST",
                "LIBRARY_MOVEMENT_IN_EFFECT", "CANNOT_ADD_MANA_ON_RESOLUTION",
            ],
        },
        "triggered_input_design": {
            "ability_kind": "TRIGGERED", "fields": sorted(_TRIGGERED_FIELDS),
            "required_concepts": [
                "target_requirement", "trigger_source_category",
                "activated_mana_ability_activation", "activated_mana_ability_resolution",
                "mana_added", "could_add_mana_on_resolution",
                "source_semantics_knowledge", "dependency_semantics_knowledge",
            ],
            "candidate_external_references": ["115.6"],
            "reference_status": "CANDIDATE_DIRECT_REFERENCE_REQUIRES_SOURCE_VERIFICATION",
            "internal_context": "ACTIVATED_MANA_CLASSIFICATION_REQUIRES_INDEPENDENT_KNOWLEDGE",
            "excluded_case_design": [
                "TARGETED_ABILITY", "WRONG_TRIGGER_RELATIONSHIP",
                "CANNOT_ADD_MANA_ON_RESOLUTION",
            ],
            "trigger_detection_available": False,
        },
        "spells_boundary": {
            "spells_that_add_mana": "DESIGN_EXCLUDED_FROM_ABILITY_CLASSIFICATION",
            "card_text_keyword_matching": "INSUFFICIENT_AUTHORITY",
            "produces_mana_in_ordinary_situation": "INSUFFICIENT_AUTHORITY",
        },
        "persistence_design": {
            "classification": "INDEPENDENT_DECLARED_FIELD",
            "current_activation_eligibility": list(ACTIVATION_STATES),
            "current_mana_output_known": "SEPARATE_BOOLEAN_DECLARATION",
            "current_mana_output_amount": "SUPPLIED_SYNTHETIC_INTEGER_OR_UNKNOWN",
            "current_game_state_constraints": "SYNTHETIC_REFERENCES_ONLY",
            "classification_may_persist_when_output_zero": True,
            "classification_may_persist_when_not_currently_activatable": True,
            "current_output_reclassifies_ability": False,
            "activation_evaluation_available": False,
            "mana_arithmetic_available": False,
        },
        "synthetic_fixture_requirements": [
            "CALLER_SUPPLIES_CLASSIFICATION_NO_INFERENCE",
            "UNKNOWN_REQUIRED_INFORMATION_FAILS_CLOSED",
            "TARGETED_EXCLUSION_REPRESENTABLE_WITH_EXPLICIT_METADATA",
            "CLASSIFICATION_STABLE_WITH_ZERO_OUTPUT_AND_INELIGIBLE_ACTIVATION",
            "ACTIVATED_AND_TRIGGERED_CONTRACTS_DISTINCT",
        ],
        "unsupported_boundaries": [
            "real_ability_classification", "real_card_effect_semantics", "target_semantics",
            "loyalty_semantics", "replacement_effect_execution", "library_movement",
            "activated_ability_execution", "trigger_detection", "mana_production",
            "mana_pool_semantics", "cost_payment",
        ],
        "future_primitives": [
            "ability_kind_evidence", "target_requirement_evidence", "could_add_mana_evidence",
            "loyalty_status_evidence", "library_movement_evidence",
            "classification_replacement_scope_evidence", "trigger_relationship_evidence",
            "classification_unknown_state", "classification_current_output_separation",
        ],
        "readiness": "DESIGN_SCOPED_EXECUTION_BLOCKED",
        "design_notes": [
            "Classification declarations and current output metadata are separate immutable design inputs; "
            "neither evaluates real abilities or grants execution authority."
        ],
    }


@dataclass(frozen=True)
class ManaAbilityClassificationDesign(DesignRecord):
    """A source-unverified scope for future classification knowledge."""

    SCHEMA = "mana-ability-classification-design-v1"
    ID_FIELD = "classification_design_id"
    BODY_FIELDS = frozenset(_body())

    @staticmethod
    def _validate_body(body: dict[str, Any]) -> None:
        expected = _body()
        for field in expected:
            if field != "design_notes":
                _exact(body[field], expected[field], field)
        _strings(body["design_notes"], "design_notes", nonempty=True)


def build_classification_design(*, design_notes: Any = None) -> ManaAbilityClassificationDesign:
    """Build authored classification scope without source, network, or gameplay IO."""
    body = _body()
    if design_notes is not None:
        body["design_notes"] = _json(design_notes)
    return ManaAbilityClassificationDesign.create(body)
