"""Immutable, non-executable cost expressions and payment design declarations.

The model declares future data and consistency boundaries. It never evaluates
mana, chooses objects, changes a game state, or performs a cost payment.
"""
from __future__ import annotations

from dataclasses import dataclass

from typing import Any

from .common import DesignRecord, _enum, _exact, _fail, _hash, _json, _keys, _strings
from .stages import (
    CastingChoiceDeclarationDesign, CastingSubprocedureDesign,
    _synthetic_reference, build_casting_choice_declaration,
    build_casting_subprocedure_design,
)


COST_COMPONENT_TYPES = (
    "MANA", "TAPPING", "SACRIFICING", "DISCARDING", "LIFE",
    "GENERIC_NONMANA", "UNKNOWN", "UNSUPPORTED",
)
COST_STATES = ("UNDETERMINED", "DETERMINED", "LOCKED")
BASE_COST_BASES = ("NORMAL_MANA_COST", "SELECTED_ALTERNATIVE_COST")
PAYMENT_GROUPS = ("ORDINARY", "RANDOM_OR_LIBRARY_TO_PUBLIC_ZONE")
_NOTES = (
    "The model declares a chosen cost basis, later modifiers, lock-in, and "
    "payment evidence fields without calculating or paying any real cost."
)


def _body(casting_design_id: str) -> dict[str, Any]:
    return {
        "release_concept": "2026-09-25",
        "casting_design_id": casting_design_id,
        "evidence_status": "PM_SUPPLIED_DESIGN_INPUT_NOT_SOURCE_VERIFIED",
        "expression_contract": {
            "base_cost_basis": list(BASE_COST_BASES),
            "basis_cardinality": "EXACTLY_ONE",
            "normal_mana_cost": "SYMBOLIC_REFERENCE_ONLY",
            "selected_alternative_cost": "SYMBOLIC_REFERENCE_ONLY",
            "madness_cost_basis": "SELECTED_ALTERNATIVE_COST",
            "alternative_cost_is_discount": False,
            "ordered_expression_terms": [
                "selected_base_cost", "additional_costs", "cost_increases",
                "cost_reductions", "direct_total_cost_modifiers", "locked_total_cost",
            ],
            "reduction_order": "DECLARED_UNEVALUATED_SEQUENCE",
            "component_fields": [
                "synthetic_component_id", "cost_type", "symbolic_obligation",
                "knowledge_state", "payment_order_class",
            ],
            "component_taxonomy": list(COST_COMPONENT_TYPES),
            "knowledge_states": ["KNOWN", "UNKNOWN", "UNSUPPORTED"],
            "calculation": "ABSENT",
            "real_card_input": "FORBIDDEN",
            "layers": "UNIMPLEMENTED",
        },
        "lock_contract": {
            "states": list(COST_STATES),
            "state_machine": False,
            "determination": "AUTHORED_DECLARATION_ONLY",
            "lock_point": "AFTER_TOTAL_COST_DETERMINATION_AND_DIRECT_MODIFIERS",
            "locked_cost_identity": "CONTENT_IDENTITY_OF_EXACT_LOCKED_DECLARATION",
            "payment_required_state": "LOCKED",
            "payment_identity_binding": "EXACT_IDENTITY_EQUALITY",
            "recompute_during_payment": "FORBIDDEN",
            "runtime_locking": "ABSENT",
        },
        "payment_contract": {
            "fields": [
                "locked_total_cost_identity", "component_inventory",
                "ordered_payment_groups", "component_payment_states",
                "unpayable_cost_condition", "random_element_boundary",
                "library_to_public_zone_boundary", "result_state",
            ],
            "component_states": ["PAID", "UNPAID", "UNKNOWN", "UNSUPPORTED"],
            "states_describe": "DECLARED_EVIDENCE_NOT_EXECUTED_PAYMENT",
            "ordered_groups": [
                {
                    "group": PAYMENT_GROUPS[0], "sequence": 1,
                    "components": "ORDINARY_COMPONENTS",
                    "within_group_order": "DECLARED_ONLY",
                },
                {
                    "group": PAYMENT_GROUPS[1], "sequence": 2,
                    "components": ["RANDOM_ELEMENTS", "LIBRARY_TO_PUBLIC_ZONE"],
                    "within_group_order": "DECLARED_ONLY",
                },
            ],
            "partial_payment": "FORBIDDEN",
            "unpayable_cost": "CANNOT_BE_PAID",
            "unresolved_component": "INDETERMINATE_OR_UNSUPPORTED",
            "payment_execution": "ABSENT",
            "randomization": "ABSENT",
            "library_inspection": "ABSENT",
            "object_movement": "ABSENT",
            "game_state_mutation": "ABSENT",
        },
        "synthetic_proofs": [
            {
                "fixture_id": "synthetic-madness-cost-basis-v1",
                "spell_reference": "synthetic-spell-alpha",
                "normal_mana_cost_reference": "synthetic-normal-cost-alpha",
                "selected_alternative_cost_reference": "synthetic-madness-cost-alpha",
                "base_cost_basis": "SELECTED_ALTERNATIVE_COST",
                "alternative_cost_source": "madness",
                "selected_alternatives": 1,
                "other_candidate_alternatives": ["synthetic-other-alternative-beta"],
                "alternative_interaction": "UNKNOWN",
                "result": "INDETERMINATE",
                "cost_calculated": False,
                "payment_performed": False,
                "legal_cast_established": False,
            },
            {
                "fixture_id": "synthetic-ordinary-base-cost-v1",
                "spell_reference": "synthetic-spell-beta",
                "base_cost_basis": "NORMAL_MANA_COST",
                "selected_alternative_cost_reference": None,
                "result": "DESIGN_DECLARATION_ONLY",
                "cost_calculated": False,
                "payment_performed": False,
            },
            {
                "fixture_id": "synthetic-conditional-branches-v1",
                "branches": ["VARIABLE_VALUE", "HYBRID", "PHYREXIAN", "SPLICE", "MODES"],
                "relevance": "UNKNOWN",
                "result": "UNSUPPORTED",
                "legal_cast_established": False,
            },
        ],
        "runtime_operations": [],
        "execution_readiness": "BLOCKED",
        "design_notes": [_NOTES],
    }


@dataclass(frozen=True)
class CostModelDesign(DesignRecord):
    """A symbolic data contract, with no total-cost or payment evaluator."""

    SCHEMA = "madness-casting-cost-design-v1"
    ID_FIELD = "cost_design_id"
    BODY_FIELDS = frozenset(_body("sha256:" + "0" * 64))

    @staticmethod
    def _validate_body(body: dict[str, Any]) -> None:
        _hash(body["casting_design_id"], "casting_design_id")
        expected = _body(body["casting_design_id"])
        for field in expected:
            if field != "design_notes":
                _exact(body[field], expected[field], field)
        _strings(body["design_notes"], "design_notes", nonempty=True)


def build_cost_design(
    casting_design: CastingSubprocedureDesign | None = None,
    *, design_notes: Any = None,
) -> CostModelDesign:
    """Bind the symbolic cost design to an immutable casting design identity."""
    if casting_design is None:
        casting_design = build_casting_subprocedure_design()
    if not isinstance(casting_design, CastingSubprocedureDesign):
        # Preserve a typed design-only boundary rather than accepting runtime
        # objects which happen to expose an identity-shaped attribute.
        _fail("casting_design: CastingSubprocedureDesign required")
    body = _body(casting_design.identity)
    if design_notes is not None:
        body["design_notes"] = _json(design_notes)
    return CostModelDesign.create(body)


_COMPONENT_FIELDS = frozenset({
    "synthetic_component_id", "cost_type", "symbolic_obligation", "payment_order_class",
})
_DEFAULT_COMPONENTS = (
    {
        "synthetic_component_id": "synthetic-mana-component-alpha",
        "cost_type": "MANA", "symbolic_obligation": "synthetic-symbolic-mana-alpha",
        "payment_order_class": "ORDINARY",
    },
    {
        "synthetic_component_id": "synthetic-nonmana-component-beta",
        "cost_type": "GENERIC_NONMANA",
        "symbolic_obligation": "synthetic-symbolic-nonmana-beta",
        "payment_order_class": "ORDINARY",
    },
)


def _components(value: Any) -> None:
    if not isinstance(value, list) or not value or len(value) > 256:
        _fail("components: bounded nonempty symbolic inventory required")
    identifiers = []
    for row in value:
        _keys(row, _COMPONENT_FIELDS, "component")
        _synthetic_reference(row["synthetic_component_id"], "synthetic_component_id")
        _synthetic_reference(row["symbolic_obligation"], "symbolic_obligation")
        _enum(row["cost_type"], COST_COMPONENT_TYPES, "cost_type")
        _enum(row["payment_order_class"], {"ORDINARY", "RANDOM", "LIBRARY_TO_PUBLIC_ZONE"}, "payment_order_class")
        identifiers.append(row["synthetic_component_id"])
    if len(set(identifiers)) != len(identifiers):
        _fail("components: duplicate component identity")


@dataclass(frozen=True)
class CostExpressionDeclarationDesign(DesignRecord):
    """A synthetic declared expression and lock state, without cost arithmetic."""

    SCHEMA = "synthetic-cost-expression-declaration-design-v1"
    ID_FIELD = "cost_expression_design_id"
    BODY_FIELDS = frozenset({
        "fixture_kind", "choice_declaration", "choice_design_id", "state",
        "base_cost_basis", "components", "cost_calculated", "runtime_lock_performed",
    })

    @staticmethod
    def _validate_body(body: dict[str, Any]) -> None:
        _exact(body["fixture_kind"], "SYNTHETIC_ONLY", "fixture_kind")
        choice = CastingChoiceDeclarationDesign.from_dict(body["choice_declaration"])
        _exact(body["choice_design_id"], choice.identity, "choice_design_id")
        _enum(body["state"], COST_STATES, "state")
        _exact(body["base_cost_basis"], choice.base_cost_basis, "base_cost_basis")
        _components(body["components"])
        _exact(body["cost_calculated"], False, "cost_calculated")
        _exact(body["runtime_lock_performed"], False, "runtime_lock_performed")


def build_cost_expression_declaration(
    choice: CastingChoiceDeclarationDesign | None = None,
    *, state: str = "LOCKED", components: Any = None,
) -> CostExpressionDeclarationDesign:
    """Record a supplied symbolic expression; no cost value is determined."""
    if choice is None:
        choice = build_casting_choice_declaration()
    if not isinstance(choice, CastingChoiceDeclarationDesign):
        _fail("choice: synthetic CastingChoiceDeclarationDesign required")
    return CostExpressionDeclarationDesign.create({
        "fixture_kind": "SYNTHETIC_ONLY",
        "choice_declaration": choice.to_dict(), "choice_design_id": choice.identity,
        "state": state, "base_cost_basis": choice.base_cost_basis,
        "components": _json(_DEFAULT_COMPONENTS if components is None else components),
        "cost_calculated": False, "runtime_lock_performed": False,
    })


@dataclass(frozen=True)
class PaymentPlanDesign(DesignRecord):
    """Synthetic payment declarations checked for consistency, never performed."""

    SCHEMA = "synthetic-payment-plan-design-v1"
    ID_FIELD = "payment_plan_design_id"
    BODY_FIELDS = frozenset({
        "fixture_kind", "locked_cost_declaration", "locked_total_cost_identity",
        "component_inventory", "ordered_payment_groups", "component_payment_states",
        "partial_payment", "unpayable_cost_condition", "result_state",
        "random_element_boundary", "library_to_public_zone_boundary",
        "payment_executed", "cost_recomputed", "gameplay_executed",
    })

    @staticmethod
    def _validate_body(body: dict[str, Any]) -> None:
        _exact(body["fixture_kind"], "SYNTHETIC_ONLY", "fixture_kind")
        cost = CostExpressionDeclarationDesign.from_dict(body["locked_cost_declaration"])
        _exact(cost.state, "LOCKED", "locked_cost_declaration.state")
        _exact(body["locked_total_cost_identity"], cost.identity, "locked_total_cost_identity")
        inventory = _json(cost.components)
        _exact(body["component_inventory"], inventory, "component_inventory")
        identifiers = [row["synthetic_component_id"] for row in inventory]
        _keys(body["component_payment_states"], identifiers, "component_payment_states")
        states = list(body["component_payment_states"].values())
        for state in states:
            _enum(state, {"PAID", "UNPAID", "UNKNOWN", "UNSUPPORTED"}, "component_payment_states")
        _exact(body["partial_payment"], "FORBIDDEN", "partial_payment")
        if "PAID" in states and any(state != "PAID" for state in states):
            _fail("component_payment_states: partial payment is forbidden")
        expected_groups = [
            {"group": PAYMENT_GROUPS[0], "sequence": 1,
             "component_ids": [row["synthetic_component_id"] for row in inventory if row["payment_order_class"] == "ORDINARY"]},
            {"group": PAYMENT_GROUPS[1], "sequence": 2,
             "component_ids": [row["synthetic_component_id"] for row in inventory if row["payment_order_class"] != "ORDINARY"]},
        ]
        _exact(body["ordered_payment_groups"], expected_groups, "ordered_payment_groups")
        if type(body["unpayable_cost_condition"]) is not bool:
            _fail("unpayable_cost_condition: boolean declaration required")
        _enum(body["result_state"], {"DECLARATION_ONLY", "UNPAYABLE", "INDETERMINATE", "UNSUPPORTED"}, "result_state")
        if body["unpayable_cost_condition"]:
            if "PAID" in states:
                _fail("component_payment_states: unpayable costs cannot be paid")
            _exact(body["result_state"], "UNPAYABLE", "result_state")
        elif body["result_state"] == "UNPAYABLE":
            _fail("result_state: UNPAYABLE requires an explicit condition")
        unmodeled = (
            cost.choice_declaration["relevant_unmodeled_branches"]
            or cost.choice_declaration["declaration_outcome"] in {"INDETERMINATE", "UNSUPPORTED"}
            or any(row["cost_type"] in {"UNKNOWN", "UNSUPPORTED"} or row["payment_order_class"] != "ORDINARY" for row in inventory)
            or any(state in {"UNKNOWN", "UNSUPPORTED"} for state in states)
        )
        if unmodeled and not body["unpayable_cost_condition"]:
            if body["result_state"] not in {"INDETERMINATE", "UNSUPPORTED"}:
                _fail("result_state: unmodeled relevant branches must fail closed")
        for field, order_class in (("random_element_boundary", "RANDOM"), ("library_to_public_zone_boundary", "LIBRARY_TO_PUBLIC_ZONE")):
            expected = "PRESENT_UNSUPPORTED" if any(row["payment_order_class"] == order_class for row in inventory) else "NOT_PRESENT_IN_FIXTURE"
            _exact(body[field], expected, field)
        for field in ("payment_executed", "cost_recomputed", "gameplay_executed"):
            _exact(body[field], False, field)


def build_payment_plan(
    locked_cost: CostExpressionDeclarationDesign,
    *, locked_total_cost_identity: str | None = None,
    payment_states: Any = None, unpayable: bool = False,
    result_state: str = "DECLARATION_ONLY",
) -> PaymentPlanDesign:
    """Bind supplied declarations to one exact cost; never infer a paid result."""
    if not isinstance(locked_cost, CostExpressionDeclarationDesign):
        _fail("locked_cost: synthetic CostExpressionDeclarationDesign required")
    inventory = _json(locked_cost.components)
    if payment_states is None:
        payment_states = {row["synthetic_component_id"]: "UNPAID" for row in inventory}
    return PaymentPlanDesign.create({
        "fixture_kind": "SYNTHETIC_ONLY", "locked_cost_declaration": locked_cost.to_dict(),
        "locked_total_cost_identity": locked_cost.identity if locked_total_cost_identity is None else locked_total_cost_identity,
        "component_inventory": inventory,
        "ordered_payment_groups": [
            {"group": PAYMENT_GROUPS[0], "sequence": 1,
             "component_ids": [row["synthetic_component_id"] for row in inventory if row["payment_order_class"] == "ORDINARY"]},
            {"group": PAYMENT_GROUPS[1], "sequence": 2,
             "component_ids": [row["synthetic_component_id"] for row in inventory if row["payment_order_class"] != "ORDINARY"]},
        ],
        "component_payment_states": _json(payment_states), "partial_payment": "FORBIDDEN",
        "unpayable_cost_condition": unpayable, "result_state": result_state,
        "random_element_boundary": "PRESENT_UNSUPPORTED" if any(row["payment_order_class"] == "RANDOM" for row in inventory) else "NOT_PRESENT_IN_FIXTURE",
        "library_to_public_zone_boundary": "PRESENT_UNSUPPORTED" if any(row["payment_order_class"] == "LIBRARY_TO_PUBLIC_ZONE" for row in inventory) else "NOT_PRESENT_IN_FIXTURE",
        "payment_executed": False, "cost_recomputed": False, "gameplay_executed": False,
    })
