"""Authored casting-stage declarations, with no casting procedure or authority.

Numbered casting references below are the PM's bounded design input. They do
not identify newly projected source units or independently verified CR bytes.
"""
from __future__ import annotations

from dataclasses import dataclass

from typing import Any

from .common import DesignRecord, _enum, _exact, _fail, _json, _strings, _text


CASTING_FRONTIER = ("601.2b", "601.2f", "601.2g", "601.2h")
STAGE_ORDER = (
    "CASTING_CHOICES", "TOTAL_COST_DETERMINATION", "MANA_ABILITY_WINDOW",
    "TOTAL_COST_PAYMENT",
)
_NOTES = (
    "The four cost-related stages describe an alternative-cost subprocedure; "
    "they neither represent the complete casting procedure nor authorize execution."
)


def _body() -> dict[str, Any]:
    return {
        "release_concept": "2026-09-25",
        "evidence_status": "PM_SUPPLIED_DESIGN_INPUT_NOT_SOURCE_VERIFIED",
        "current_casting_frontier": list(CASTING_FRONTIER),
        "semantic_sequence_only": True,
        "executable_state_machine": False,
        "capabilities": {
            "alternative_cost_casting_subprocedure": {
                "stage_ids": list(STAGE_ORDER),
                "representation": "DESIGN_ONLY",
                "execution_readiness": "BLOCKED",
                "implied_capabilities": [],
            },
            "complete_spell_casting": {
                "representation": "OUTSIDE_DESIGN",
                "execution_readiness": "BLOCKED",
                "requires_independent_closure": True,
                "satisfied_by_subprocedure": False,
            },
        },
        "stages": [
            {
                "stage_id": STAGE_ORDER[0], "sequence": 1,
                "future_rule_reference": "601.2b",
                "projection_status": "UNPROJECTED",
                "purpose": "Declare casting choices without making or validating them.",
                "declaration_fields": [
                    "synthetic_spell_reference", "chosen_casting_method",
                    "base_cost_basis", "selected_alternative_cost",
                    "alternative_cost_source", "other_candidate_alternatives",
                    "alternative_cost_interaction", "additional_costs_selected",
                    "variable_values", "modal_choices", "splice_choices",
                    "hybrid_payment_declarations", "phyrexian_payment_declarations",
                    "prior_casting_choice_restrictions", "knowledge_state",
                    "unsupported_choice_families",
                ],
                "knowledge_states": ["KNOWN", "UNKNOWN", "UNSUPPORTED"],
                "base_cost_basis": ["NORMAL_MANA_COST", "SELECTED_ALTERNATIVE_COST"],
                "madness_case": {
                    "base_cost_basis": "SELECTED_ALTERNATIVE_COST",
                    "alternative_cost_source": "madness",
                    "candidate_cost_only": True,
                    "legal_cast_established": False,
                    "mana_cost_discount": False,
                },
                "alternative_cost_conflict": {
                    "selected_alternative_cost": "SINGLE_CANDIDATE_OR_NONE",
                    "other_candidates": "DECLARED_WITHOUT_SELECTION",
                    "interaction_states": [
                        "MUTUALLY_EXCLUSIVE", "UNKNOWN", "UNSUPPORTED",
                    ],
                    "selection_algorithm": "ABSENT",
                    "interaction_semantics_complete": False,
                },
                "execution_supported": False,
            },
            {
                "stage_id": STAGE_ORDER[1], "sequence": 2,
                "future_rule_reference": "601.2f",
                "projection_status": "UNPROJECTED",
                "purpose": "Describe a total-cost expression and its future lock identity.",
                "inputs": [
                    "chosen_base_cost", "additional_costs", "cost_increases",
                    "cost_reductions", "direct_total_cost_modifiers",
                ],
                "expression_only": True,
                "calculation_available": False,
                "execution_supported": False,
            },
            {
                "stage_id": STAGE_ORDER[2], "sequence": 3,
                "future_rule_reference": "601.2g",
                "projection_status": "UNPROJECTED",
                "purpose": "Describe the mana-ability opportunity before cost payment.",
                "condition": "TOTAL_COST_CONTAINS_MANA_PAYMENT",
                "direct_dependency_design_input": "605",
                "dependency_state": "UNRESOLVED_UNPROJECTED",
                "fictional_mana_authority": "DOES_NOT_SATISFY_REAL_605",
                "mana_abilities_available": False,
                "mana_pool_available": False,
                "priority_available": False,
                "execution_supported": False,
            },
            {
                "stage_id": STAGE_ORDER[3], "sequence": 4,
                "future_rule_reference": "601.2h",
                "projection_status": "UNPROJECTED",
                "purpose": "Describe a payment declaration bound to an already locked cost.",
                "input": "EXACT_LOCKED_COST_IDENTITY",
                "payment_execution_available": False,
                "silent_cost_recomputation": "FORBIDDEN",
                "execution_supported": False,
            },
        ],
        "general_casting_boundaries": [
            "move_or_propose_spell", "general_mode_selection", "targeting",
            "legality_check", "casting_permission_and_prohibition",
            "completion_of_casting", "illegal_action_rollback", "stack_semantics",
            "priority", "trigger_consequences",
        ],
        "boundary_support": "UNSUPPORTED",
        "real_card_semantics": "ABSENT",
        "fictional_runtime_authority": "SEPARATE_NOT_REAL_RULE_EVIDENCE",
        "branch_policy": {
            "alternative_cost_selection": "CENTRAL",
            "total_cost_determination": "CENTRAL",
            "mana_ability_opportunity": "CONDITIONAL_ON_MANA_PAYMENT",
            "payment": "CENTRAL",
            "mode_choice": "CONDITIONAL_SYNTHETIC_SPELL_SHAPE",
            "splice": "INCIDENTAL_BRANCH_REQUIRES_SEPARATE_SEMANTICS",
            "variable_values": "CONDITIONAL_SYNTHETIC_SPELL_SHAPE",
            "hybrid_payment": "CONDITIONAL_SYNTHETIC_COST_SHAPE",
            "phyrexian_payment": "CONDITIONAL_SYNTHETIC_COST_SHAPE",
            "unmodeled_relevant_branch": ["INDETERMINATE", "UNSUPPORTED"],
            "confident_executable_outcome": "FORBIDDEN",
        },
        "design_notes": [_NOTES],
    }


@dataclass(frozen=True)
class CastingSubprocedureDesign(DesignRecord):
    """Immutable semantic order; this record has no step/execute interface."""

    SCHEMA = "madness-casting-subprocedure-design-v1"
    ID_FIELD = "casting_design_id"
    BODY_FIELDS = frozenset(_body())

    @staticmethod
    def _validate_body(body: dict[str, Any]) -> None:
        expected = _body()
        for field in expected:
            if field != "design_notes":
                _exact(body[field], expected[field], field)
        _strings(body["design_notes"], "design_notes", nonempty=True)


def build_casting_subprocedure_design(
    *, design_notes: Any = None,
) -> CastingSubprocedureDesign:
    """Build deterministic authored design metadata without source or runtime IO."""
    body = _body()
    if design_notes is not None:
        body["design_notes"] = _json(design_notes)
    return CastingSubprocedureDesign.create(body)


_CHOICE_FIELDS = frozenset({
    "fixture_kind", "synthetic_spell_reference", "base_cost_basis",
    "normal_mana_cost_reference", "selected_alternative_cost_reference",
    "alternative_cost_source", "other_candidate_alternatives",
    "alternative_interaction", "additional_costs_selected", "variable_values",
    "modal_choices", "splice_choices", "hybrid_payment_declarations",
    "phyrexian_payment_declarations", "prior_casting_choice_restrictions",
    "knowledge_state", "relevant_unmodeled_branches", "declaration_outcome",
    "mana_cost_discount", "legal_cast_established",
})
_CHOICE_LIST_FIELDS = (
    "other_candidate_alternatives", "additional_costs_selected", "variable_values",
    "modal_choices", "splice_choices", "hybrid_payment_declarations",
    "phyrexian_payment_declarations", "prior_casting_choice_restrictions",
)


def _synthetic_reference(value: Any, field: str) -> None:
    _text(value, field, maximum=256)
    if not value.startswith("synthetic-"):
        _fail(field + ": synthetic fixture references only")


@dataclass(frozen=True)
class CastingChoiceDeclarationDesign(DesignRecord):
    """Synthetic choice data whose states never attest to a legal cast."""

    SCHEMA = "synthetic-casting-choice-declaration-design-v1"
    ID_FIELD = "choice_design_id"
    BODY_FIELDS = _CHOICE_FIELDS

    @staticmethod
    def _validate_body(body: dict[str, Any]) -> None:
        _exact(body["fixture_kind"], "SYNTHETIC_ONLY", "fixture_kind")
        _synthetic_reference(body["synthetic_spell_reference"], "synthetic_spell_reference")
        _synthetic_reference(body["normal_mana_cost_reference"], "normal_mana_cost_reference")
        _enum(body["base_cost_basis"], {"NORMAL_MANA_COST", "SELECTED_ALTERNATIVE_COST"}, "base_cost_basis")
        if body["base_cost_basis"] == "NORMAL_MANA_COST":
            _exact(body["selected_alternative_cost_reference"], None, "selected_alternative_cost_reference")
            _exact(body["alternative_cost_source"], None, "alternative_cost_source")
        else:
            _synthetic_reference(body["selected_alternative_cost_reference"], "selected_alternative_cost_reference")
            _enum(body["alternative_cost_source"], {"madness", "synthetic-other"}, "alternative_cost_source")
        for field in _CHOICE_LIST_FIELDS:
            _strings(body[field], field)
            for item in body[field]:
                _synthetic_reference(item, field)
        if body["selected_alternative_cost_reference"] in body["other_candidate_alternatives"]:
            _fail("other_candidate_alternatives: selected cost is distinct from other candidates")
        _enum(body["alternative_interaction"], {"MUTUALLY_EXCLUSIVE", "UNKNOWN", "UNSUPPORTED"}, "alternative_interaction")
        _enum(body["knowledge_state"], {"KNOWN", "UNKNOWN", "UNSUPPORTED"}, "knowledge_state")
        _strings(body["relevant_unmodeled_branches"], "relevant_unmodeled_branches")
        for branch in body["relevant_unmodeled_branches"]:
            _enum(branch, {"MODES", "SPLICE", "VARIABLE_VALUES", "HYBRID", "PHYREXIAN", "PRIOR_CHOICE_RESTRICTIONS", "OTHER"}, "relevant_unmodeled_branches")
        _enum(body["declaration_outcome"], {"DECLARED_NOT_EXECUTED", "INDETERMINATE", "UNSUPPORTED"}, "declaration_outcome")
        if (body["relevant_unmodeled_branches"]
                or any(body[field] for field in ("modal_choices", "splice_choices", "variable_values",
                                                "hybrid_payment_declarations", "phyrexian_payment_declarations",
                                                "prior_casting_choice_restrictions"))
                or body["knowledge_state"] != "KNOWN"
                or (body["other_candidate_alternatives"] and body["alternative_interaction"] != "MUTUALLY_EXCLUSIVE")):
            if body["declaration_outcome"] not in {"INDETERMINATE", "UNSUPPORTED"}:
                _fail("declaration_outcome: unmodeled relevant branches must fail closed")
        _exact(body["mana_cost_discount"], False, "mana_cost_discount")
        _exact(body["legal_cast_established"], False, "legal_cast_established")


def build_casting_choice_declaration(
    *, synthetic_spell_reference: str = "synthetic-spell-alpha",
    base_cost_basis: str = "SELECTED_ALTERNATIVE_COST",
    normal_mana_cost_reference: str = "synthetic-normal-cost-alpha",
    selected_alternative_cost_reference: str | None = "synthetic-madness-cost-alpha",
    alternative_cost_source: str | None = "madness",
    other_candidate_alternatives: Any = (),
    alternative_interaction: str = "MUTUALLY_EXCLUSIVE",
    additional_costs_selected: Any = (), variable_values: Any = (),
    modal_choices: Any = (), splice_choices: Any = (),
    hybrid_payment_declarations: Any = (), phyrexian_payment_declarations: Any = (),
    prior_casting_choice_restrictions: Any = (), knowledge_state: str = "KNOWN",
    relevant_unmodeled_branches: Any = (),
    declaration_outcome: str = "DECLARED_NOT_EXECUTED",
) -> CastingChoiceDeclarationDesign:
    """Validate declarations only; the caller supplies every declared outcome."""
    body = {
        "fixture_kind": "SYNTHETIC_ONLY",
        "synthetic_spell_reference": synthetic_spell_reference,
        "base_cost_basis": base_cost_basis,
        "normal_mana_cost_reference": normal_mana_cost_reference,
        "selected_alternative_cost_reference": selected_alternative_cost_reference,
        "alternative_cost_source": alternative_cost_source,
        "other_candidate_alternatives": _json(other_candidate_alternatives),
        "alternative_interaction": alternative_interaction,
        "additional_costs_selected": _json(additional_costs_selected),
        "variable_values": _json(variable_values), "modal_choices": _json(modal_choices),
        "splice_choices": _json(splice_choices),
        "hybrid_payment_declarations": _json(hybrid_payment_declarations),
        "phyrexian_payment_declarations": _json(phyrexian_payment_declarations),
        "prior_casting_choice_restrictions": _json(prior_casting_choice_restrictions),
        "knowledge_state": knowledge_state,
        "relevant_unmodeled_branches": _json(relevant_unmodeled_branches),
        "declaration_outcome": declaration_outcome,
        "mana_cost_discount": False, "legal_cast_established": False,
    }
    return CastingChoiceDeclarationDesign.create(body)
