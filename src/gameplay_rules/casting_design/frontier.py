"""PM observations and a proposed scope; no new source-unit or anchor claims."""
from dataclasses import dataclass

from .common import DesignRecord, _exact, _json, _strings
from .stages import CASTING_FRONTIER
from .anchors import MULTI_LINE_RULE_BLOCK_ANCHOR, RULE_BLOCK_POLICY
from .evidence import EXISTING_UNPROJECTED_REFERENCES

OBSERVATION_AUTHORITY = "PM_SUPPLIED_DESIGN_INPUT_NOT_SOURCE_VERIFIED"
CANDIDATE_STATUS = "CANDIDATE_DIRECT_REFERENCE_REQUIRES_SOURCE_PROJECTION"
PROPOSED_REFERENCES = ("601.2", *CASTING_FRONTIER)
OUTSIDE_CANDIDATE_REFERENCES = ("700.2", "702.47", "118.8", "118.9", "107.3", "605")


def _body():
    observations = [
        {"rule_reference": "601.2b", "authority": OBSERVATION_AUTHORITY,
         "concepts": ["casting_choice_declarations", "modes", "splice", "alternative_costs", "additional_costs",
                      "variable_values", "hybrid_choices", "phyrexian_choices", "prior_choice_restrictions"],
         "candidate_direct_references": ["700.2", "702.47", "118.8", "118.9", "601.2f", "107.3"]},
        {"rule_reference": "601.2f", "authority": OBSERVATION_AUTHORITY,
         "concepts": ["normal_or_alternative_base_cost", "additional_costs", "increases", "reductions",
                      "reduction_order", "direct_modifiers", "total_cost_lock_in"],
         "candidate_direct_references": ["601.2b"]},
        {"rule_reference": "601.2g", "authority": OBSERVATION_AUTHORITY,
         "concepts": ["conditional_mana_ability_opportunity_before_payment"], "candidate_direct_references": ["605"]},
        {"rule_reference": "601.2h", "authority": OBSERVATION_AUTHORITY,
         "concepts": ["payment_order_groups", "random_and_library_public_components_later",
                      "no_partial_payment", "unpayable_cost_cannot_be_paid"], "candidate_direct_references": []},
    ]
    candidate_edges = [{"from_reference": row["rule_reference"], "to_reference": target,
                        "status": CANDIDATE_STATUS, "authority": OBSERVATION_AUTHORITY,
                        "projection_status": "UNPROJECTED", "source_verified": False}
                       for row in observations for target in row["candidate_direct_references"]]
    rationale = {
        "601.2": "Immediate procedural parent supplies scope framing for noncontiguous stages. Its inclusion is a design judgment derived from numbering hierarchy; its body and outgoing references require future verification.",
        "601.2b": "Casting declarations and candidate Madness alternative-cost selection need descriptive representation.",
        "601.2f": "The selected base cost and subsequent modifiers need a total-cost and lock-in description.",
        "601.2g": "The conditional mana-ability opportunity separates determination from payment and exposes the unresolved 605 boundary.",
        "601.2h": "Payment requires descriptive ordering, exact locked-cost binding, and all-or-nothing constraints.",
    }
    return {
        "design_input_authority": OBSERVATION_AUTHORITY,
        "current_casting_frontier": list(CASTING_FRONTIER), "observations": observations,
        "candidate_direct_references": candidate_edges,
        "outside_candidate_references": list(OUTSIDE_CANDIDATE_REFERENCES),
        "all_candidate_references_unprojected": True,
        "madness_minimal_frontier": {
            "central": ["alternative_cost_selection", "total_cost_determination", "payment"],
            "conditional": ["mana_ability_access", "mode_choices", "variable_values", "hybrid_choices", "phyrexian_choices"],
            "incidental_but_not_assumed_absent": ["splice"],
            "relevance_evidence": "SYNTHETIC_DECLARATIONS_ONLY",
            "unmodeled_relevant_branch_outcomes": ["INDETERMINATE", "UNSUPPORTED"],
            "confident_executable_outcome": "FORBIDDEN",
        },
        "current_projection": {"before": 63, "new_real_source_units": 0, "after": 63,
                               "unprojected_references": list(dict.fromkeys([*EXISTING_UNPROJECTED_REFERENCES, *OUTSIDE_CANDIDATE_REFERENCES, "601.2"]))},
        "next_milestone": {
            "candidate": "Bounded Casting Rules Projection", "authorized": False,
            "exact_proposed_source_allowlist": list(PROPOSED_REFERENCES),
            "proposed_source_unit_count": 5, "conditional_future_composite_count": 68,
            "rationale_by_reference": rationale,
            "parent_context_authority": "DESIGN_HIERARCHY_JUDGMENT_NOT_SOURCE_OBSERVATION",
            "parent_body_and_direct_reference_frontier": "UNKNOWN_REQUIRES_SOURCE_VERIFICATION",
            "source_txt_required": True, "expected_anchor_type": MULTI_LINE_RULE_BLOCK_ANCHOR,
            "expected_anchor_policy": RULE_BLOCK_POLICY,
            "one_line_future_units": "PERMITTED_AS_BLOCK_WITH_LINE_COUNT_ONE",
            "verified_source_required_before_any_projection": True,
            "scope_insufficiency": "STOP_FOR_SEPARATE_SCOPE_REVIEW_NEVER_AUTO_EXPAND",
            "deliberately_unresolved_candidate_references": list(OUTSIDE_CANDIDATE_REFERENCES),
            "larger_separate_milestones": ["mana_abilities_605", "general_cost_rules", "general_choice_branches",
                                          "complete_casting_legality_stack_and_permissions", "continuous_effects_613"],
            "unselected_casting_stage_numbered_allowlist_claimed": False,
            "complete_casting_implied": False,
        },
        "limitations": ["PM observations are scoping inputs, not newly verified source relationships.",
                        "Five units are the proposed smallest coherent knowledge scope, not a complete casting algorithm.",
                        "All six outside candidate references and every existing rule blocker remain unprojected in this milestone."],
        "design_notes": ["Add only immediate parent context to the four-stage frontier; no sibling stage or recursive dependency expansion is authorized."],
    }


@dataclass(frozen=True)
class ProjectionFrontierDesign(DesignRecord):
    SCHEMA = "madness-casting-projection-frontier-design-v1"
    ID_FIELD = "projection_frontier_id"
    BODY_FIELDS = frozenset(_body())

    @staticmethod
    def _validate_body(body):
        for key, value in _body().items():
            if key != "design_notes":
                _exact(body[key], value, key)
        _strings(body["design_notes"], "design_notes", nonempty=True)


def build_projection_frontier_design(*, design_notes=None):
    body = _body()
    if design_notes is not None:
        body["design_notes"] = _json(design_notes)
    return ProjectionFrontierDesign.create(body)
