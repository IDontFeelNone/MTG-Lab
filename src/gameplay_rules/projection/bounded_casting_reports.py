"""Append-only correspondence, dependency and readiness evidence.

All findings are derived from the five typed records and independently verified
retained packages. Source coverage cannot grant runtime or gameplay authority.
"""
from __future__ import annotations

from pathlib import Path

from gameplay_rules.casting_design.evidence import RETAINED_BINDING
from .contracts import _json, _exact
from .dependency_package import _read
from .zone_change_dependency_reports import ZoneChangeDependencyCompositeCoverage
from .bounded_casting_contracts import (
    BoundedCastingProjection, BoundedCastingReview, CANONICAL_MAIN, SOURCE_BINDING,
    BOUNDARY_FLAGS, PRIOR_PACKAGE_IDS, DESIGN_IDS,
)
from .bounded_casting_scope import (
    SELECTED_REFERENCES, SELECTED_STAGE_REFERENCES, SIBLING_STAGE_MATRIX,
    UNPROJECTED_SIBLING_REFERENCES, NEW_BOUNDARIES, UNSUPPORTED_DIMENSIONS,
)

HISTORICAL_ACQUISITION_ID = RETAINED_BINDING["historical_acquisition_identity"]
TARGET_PROFILE = "magic-comprehensive-rules-20260925-v1"
READINESS_BLOCKERS = (
    "unresolved_direct_numbered_dependencies", "unprojected_casting_stages",
    "real_card_and_effect_semantics", "real_605_semantics", "casting_legality",
    "illegal_action_rollback", "real_semantic_primitives", "deterministic_runtime_vectors",
    "owner_activation", "casting_permission", "stack_semantics", "priority",
)
NEXT_MILESTONE = {
    "candidate": "Mana Ability Dependency Design", "center_reference": "605",
    "exact_proposed_scope": ["605 dependency and authority boundary design"],
    "existing_evidence_bindings": ["601.2g", "existing_object_control_605_frontier"],
    "rationale": "The newly verified conditional mana window and retained control frontier share "
                 "605. A separate design can bound that subsystem without inheriting authority "
                 "from fictional mana or expanding the casting projection.",
    "source_txt_required": False,
    "source_basis": "RETAINED_VERIFIED_FRONTIER_ONLY_NOT_NEW_605_SOURCE_KNOWLEDGE",
    "future_source_projection_requires_verified_artifact": True,
    "new_source_units_authorized": 0, "authorized": False, "started": False,
}


def _unique(values):
    return list(dict.fromkeys(values))


def _review(kind, projection, findings):
    return BoundedCastingReview.create({
        "game_id": "magic", "canonical_base": CANONICAL_MAIN,
        "review_kind": kind, "status": "APPEND_ONLY_REVIEW",
        "bounded_casting_projection_id": projection.identity,
        "source_binding": SOURCE_BINDING, "prior_package_ids": PRIOR_PACKAGE_IDS,
        "design_ids": DESIGN_IDS, "findings": findings, "boundary_flags": BOUNDARY_FLAGS,
    })


def _frontier(rules):
    """Resolve only exact selected targets; never expand another source unit."""
    selected = set(rules)
    return [{"from_reference": reference, "from_rule_id": row["rule_id"],
             "target_reference": target,
             "reference_state": "DIRECT_REFERENCE_RESOLVED" if target in selected else "UNRESOLVED",
             "coverage_state": "PROJECTED_IN_THIS_MILESTONE" if target in selected else "UNPROJECTED",
             "evidence_basis": "VERIFIED_SELECTED_SOURCE_BLOCK_CITATION"}
            for reference, row in rules.items() for target in row["direct_dependency_references"]]


def _correspondence(rules):
    # The historical observations remain design input in their original package.
    # This new review supplies separately anchored verification and refinements.
    observations = (
        ("mode_choice", "601.2b", "VERIFIED", "Modal declarations are represented; 700.2 remains open."),
        ("splice_declaration", "601.2b", "VERIFIED", "Splice is a declared branch; 702.47 remains open."),
        ("alternative_cost_basis", "601.2b", "VERIFIED", "The declared alternative cost supplies the later base-cost choice; the retained Madness relationship does not turn it into a discount."),
        ("additional_costs", "601.2b", "VERIFIED", "Additional-cost declarations are distinct from the selected base."),
        ("variable_values", "601.2b", "VERIFIED_WITH_REFINEMENT", "A later variable-defining choice may be brought into this stage."),
        ("hybrid_choices", "601.2b", "VERIFIED", "A payment form is declared without executing payment."),
        ("phyrexian_choices", "601.2b", "VERIFIED", "Life-versus-mana declarations remain descriptive."),
        ("multiple_alternative_cost_exclusion", "601.2b", "VERIFIED", "Two alternative methods or two alternative costs cannot be combined indiscriminately."),
        ("prior_choice_restrictions", "601.2b", "VERIFIED", "Earlier casting choices can constrain current declarations."),
        ("total_cost_composition", "601.2f", "VERIFIED_WITH_REFINEMENT", "The symbolic composition also preserves reduction ordering and the mana floor."),
        ("cost_lock", "601.2f", "VERIFIED_WITH_REFINEMENT", "Direct total-cost adjustments precede locking; later cost changes do not revise that locked value."),
        ("mana_ability_window", "601.2g", "VERIFIED", "A mana-containing total has a prepayment opportunity; real 605 is unresolved."),
        ("payment_ordering", "601.2h", "VERIFIED", "Ordinary components precede random or library-to-public components, with free order within groups."),
        ("partial_payment_prohibition", "601.2h", "VERIFIED", "A partial payment cannot satisfy the total."),
        ("unpayable_costs", "601.2h", "VERIFIED", "A cost that cannot be paid has no valid payment."),
        ("parent_permission_and_rollback", "601.2", "FOUND_ADDITIONAL_BOUNDARY", "The parent exposes 601.3 and 733 plus unprojected procedural stages."),
    )
    rows = [{"observation": name, "historical_authority": "PM_SUPPLIED_DESIGN_INPUT_NOT_SOURCE_VERIFIED",
             "finding": status, "rule_reference": reference, "rule_id": rules[reference]["rule_id"],
             "source_anchor": rules[reference]["source_anchor"], "project_authored_assessment": assessment}
            for name, reference, status, assessment in observations]
    alternative = next(row for row in rows if row["observation"] == "alternative_cost_basis")
    alternative["supporting_rule_identities"] = [
        {"rule_reference": "601.2f", "rule_id": rules["601.2f"]["rule_id"],
         "evidence_state": "SELECTED_AND_PROJECTED"},
        {**_json(next(row for row in RETAINED_BINDING["madness_rules"] if row["rule_reference"] == "702.35b")),
         "evidence_state": "EXISTING_PROJECTED_EVIDENCE_UNCHANGED"},
    ]
    physical = []
    for reference in SELECTED_REFERENCES:
        anchor = rules[reference]["source_anchor"]
        expected_multiple = reference in {"601.2", "601.2b", "601.2f"}
        physical.append({"rule_reference": reference, "expected_multiline": expected_multiple,
                         "actual_line_count": anchor["line_count"],
                         "finding": "DID_NOT_VERIFY" if expected_multiple and anchor["line_count"] == 1 else "VERIFIED",
                         "reviewed_contract_compatible": True,
                         "reason": "One-line blocks are explicitly permitted; separators are excluded."
                                   if anchor["line_count"] == 1 else
                                   "An adjacent owned example contributes an internal source line terminator."})
    counts = {status: sum(row["finding"] == status for row in rows)
              for status in ("VERIFIED", "VERIFIED_WITH_REFINEMENT", "DID_NOT_VERIFY", "FOUND_ADDITIONAL_BOUNDARY")}
    return {
        "historical_design_package_id": PRIOR_PACKAGE_IDS["madness_casting_dependency_design"],
        "historical_design_id": DESIGN_IDS["casting_design_id"],
        "historical_design_authority_unchanged": "PM_SUPPLIED_DESIGN_INPUT_NOT_SOURCE_VERIFIED",
        "new_evidence_authority": "EXACT_ARTIFACT_AND_SELECTED_BLOCKS_VERIFIED",
        "observations": rows, "semantic_observation_counts": counts,
        "semantic_observations_contradicted": [], "physical_shape_observations": physical,
        "historical_design_package_mutated": False,
        "example_ownership": {"rule_reference": "601.2h", "state": "UNAMBIGUOUS_SELECTED_RULE_OWNERSHIP",
            "basis": "DIRECT_ADJACENCY_BEFORE_SEPARATOR_AND_NEXT_NUMBERED_UNIT",
            "included_in_block_hash": True, "example_prose_retained": False},
        "limitations": ["Verification of selected source knowledge supplies no executable casting behavior.",
                        "The earlier physical-shape expectation is preserved as an unverified expectation, not padded with separators."],
    }


def build_bounded_casting_reviews(projection, *, review_root):
    """Rebuild five read-only reports after checking all seven prior packages."""
    if type(projection) is not BoundedCastingProjection:
        from .bounded_casting_contracts import _fail
        _fail("projection", "typed bounded projection required")
    projection.verify()
    from .bounded_casting_package import _prior_design
    design = _prior_design(review_root)
    coverage = ZoneChangeDependencyCompositeCoverage.from_json(_read(
        Path(review_root) / "gameplay-rules-zone-change-direct-dependencies/composite-coverage.json")).to_dict()
    _exact(coverage["total_projected_rule_count"], 63, "prior_coverage")
    rules = {row["rule_reference"]: row for row in projection.to_dict()["rules"]}
    frontier = _frontier(rules)
    explicit_unresolved = _unique(row["target_reference"] for row in frontier if row["reference_state"] == "UNRESOLVED")
    remaining = _unique([ref for ref in coverage["remaining_unresolved_rules"] if ref not in rules]
                        + explicit_unresolved + list(UNPROJECTED_SIBLING_REFERENCES))
    matrix = _json(SIBLING_STAGE_MATRIX)
    for row in matrix:
        row["evidence_state"] = "SELECTED_SOURCE_PROJECTED" if row["reference"] in rules else "UNPROJECTED_STRUCTURAL_BOUNDARY"
        if row["reference"] in rules:
            row["rule_id"] = rules[row["reference"]]["rule_id"]
    common_readiness = {
        "target_profile_id": TARGET_PROFILE, "semantic_closure": "OPEN",
        "dependency_closure": "OPEN", "execution_readiness": "EXECUTION_BLOCKED",
        "execution_ready": False, "required_primitives_available": False,
        "real_execution_primitives_available": [], "runtime_implemented": False,
        "readiness_code": "REAL_EXECUTION_PROFILE_NOT_READY",
    }
    stages = {
        "rows": matrix, "parent_reference": "601.2",
        "selected_stage_references": list(SELECTED_STAGE_REFERENCES),
        "unprojected_stage_references": list(UNPROJECTED_SIBLING_REFERENCES),
        "explicit_numbered_dependency_findings": frontier,
        "verified_unresolved_direct_references": explicit_unresolved,
        "structural_only_unprojected_stages": ["601.2e", "601.2i"],
        "parent_projection_satisfies_siblings": False,
        "legality_stage_boundary": {"reference": "601.2e", "coverage_state": "UNPROJECTED_CASTING_STAGE",
                                    "role": "LEGALITY_CHECK_GAP", "role_basis": "OWNER_SUPPLIED_STRUCTURAL_DESIGN_BOUNDARY_NOT_PROJECTED_SOURCE"},
        **common_readiness,
    }
    retained = _json(RETAINED_BINDING)
    selected_rule_ids = [{"rule_reference": ref, "rule_id": rules[ref]["rule_id"]} for ref in SELECTED_REFERENCES]
    dimensions = (
        ("discard_replacement", ["702.35a"], "RETAINED_DESCRIPTION_RUNTIME_ABSENT"),
        ("exile", ["702.35a"], "RETAINED_DESCRIPTION_RUNTIME_ABSENT"),
        ("trigger", ["702.35a"], "RETAINED_DESCRIPTION_RUNTIME_ABSENT"),
        ("optional_cast_choice", ["702.35a"], "RETAINED_DESCRIPTION_RUNTIME_ABSENT"),
        ("alternative_cost_selection", ["702.35b", "601.2b"], "SOURCE_COVERAGE_IMPROVED"),
        ("cost_determination", ["601.2f"], "SOURCE_COVERAGE_IMPROVED"),
        ("mana_ability_window", ["601.2g"], "SOURCE_REPRESENTED_605_OPEN"),
        ("payment", ["601.2h"], "SOURCE_COVERAGE_IMPROVED"),
        ("casting_legality", ["601.2", "601.2e", "601.3"], "UNPROJECTED_LEGALITY_AND_PERMISSION_BOUNDARIES"),
        ("target_and_mode_requirements", ["601.2b", "601.2c", "700.2"], "PARTIAL_COVERAGE_TARGET_STAGE_AND_MODES_OPEN"),
        ("stack_placement", ["601.2", "601.2a"], "PARENT_DESCRIPTION_STAGE_UNPROJECTED"),
        ("casting_completion", ["601.2i"], "UNPROJECTED_CASTING_STAGE"),
        ("rollback", ["601.2", "733"], "PARENT_DESCRIPTION_ROLLBACK_DEPENDENCY_OPEN"),
        ("public_zone_fallback", ["702.35a", "702.35c", "400.7k"], "RETAINED_LOOKUP_EVIDENCE_RUNTIME_ABSENT"),
    )
    madness = {
        "capability_id": "madness", "prior_readiness_id": design["madness-readiness.json"].identity,
        "retained_madness_rules": retained["madness_rules"],
        "retained_zone_change_lookup": retained["zone_change_lookup"],
        "new_selected_casting_rules": selected_rule_ids,
        "dimensions": [{"dimension": name, "source_references": refs, "source_coverage": state,
                        "semantic_closure": "OPEN", "execution_readiness": "EXECUTION_BLOCKED"}
                       for name, refs, state in dimensions],
        "alternative_cost_source_coverage": "REPRESENTED_WITH_OPEN_DEPENDENCIES",
        "unresolved_numbered_references": remaining, "blockers": list(READINESS_BLOCKERS),
        "fictional_mana_satisfies_real_605": False, **common_readiness,
    }
    casting = {
        "capabilities": [
            {"capability_id": "alternative_cost_casting_subprocedure",
             "source_coverage": "REPRESENTED_WITH_OPEN_DEPENDENCIES",
             "selected_stages": list(SELECTED_STAGE_REFERENCES),
             "unresolved_direct_references": explicit_unresolved,
             "implies_complete_spell_casting": False, **common_readiness},
            {"capability_id": "complete_spell_casting", "source_coverage": "INCOMPLETE",
             "missing_stages": list(UNPROJECTED_SIBLING_REFERENCES),
             "unresolved_permission_and_rollback": ["601.3", "733"], **common_readiness},
        ],
        "verified_dependency_frontier": frontier, "remaining_unresolved_rules": remaining,
        "unprojected_sibling_stages": list(UNPROJECTED_SIBLING_REFERENCES),
        "complete_casting_gaps": ["initial_spell_movement_and_stack_proposal", "target_declaration",
            "division_and_distribution", "legality_checking", "casting_completion", "cast_triggers",
            "stack_semantics", "casting_permission_and_prohibition", "illegal_action_rollback", "priority"],
        "unresolved_subsystems": _json(NEW_BOUNDARIES), "unsupported_dimensions": list(UNSUPPORTED_DIMENSIONS),
        "blockers": list(READINESS_BLOCKERS), "fictional_mana_satisfies_real_605": False,
        "payment_executed": False, "cost_calculation_implemented": False,
        "next_milestone": NEXT_MILESTONE, **common_readiness,
    }
    components = _json(coverage["projection_components"])
    # Resolve the former enclosing-package marker to the prior immutable package.
    components[-1].pop("package_binding", None)
    components[-1]["package_id"] = PRIOR_PACKAGE_IDS["zone_change_direct_dependencies"]
    components.append({"projection_id": projection.identity,
        "package_binding": "THIS_ENCLOSING_BOUNDED_CASTING_PACKAGE",
        "projected_references": list(SELECTED_REFERENCES), "mutated": False})
    references = coverage["projected_references"] + list(SELECTED_REFERENCES)
    if len(references) != 68 or len(set(references)) != 68 or len(components) != 6:
        from .bounded_casting_contracts import _fail
        _fail("composite", "six distinct projections and exactly 68 source units required")
    composite = {
        "view_kind": "READ_ONLY_SIX_PROJECTION_COMPOSITE", "previous_projected_rule_count": 63,
        "new_projected_rule_count": 5, "total_projected_rule_count": len(references),
        "component_rule_counts": [20, 12, 7, 12, 12, 5], "projected_references": references,
        "projection_components": components, "component_identities_preserved": True,
        "prior_design_package_id": PRIOR_PACKAGE_IDS["madness_casting_dependency_design"],
        "remaining_unresolved_rules": remaining,
        "historical_acquisition_identity": HISTORICAL_ACQUISITION_ID,
        "historical_anchors_converted": False, "source_policy_clearance": "not_granted",
        **common_readiness,
    }
    return {
        "design-source-correspondence.json": _review("design_source_correspondence", projection, _correspondence(rules)),
        "casting-stage-matrix.json": _review("casting_stage_matrix", projection, stages),
        "madness-readiness-reassessment.json": _review("madness_readiness_reassessment", projection, madness),
        "casting-readiness-reassessment.json": _review("casting_readiness_reassessment", projection, casting),
        "composite-coverage.json": _review("composite_coverage", projection, composite),
    }
