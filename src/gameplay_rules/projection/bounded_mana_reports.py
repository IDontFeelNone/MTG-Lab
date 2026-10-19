"""Append-only source, family-coverage and readiness reviews for thirteen units.

This module combines the bounded projection with independently checked retained
evidence. Representing the 605 section does not classify an ability, establish
semantic closure, or grant authority to execute any gameplay operation.
"""
from __future__ import annotations

from pathlib import Path

from gameplay_rules.mana_ability_design.evidence import (
    HISTORICAL_ACQUISITION_ID, RETAINED_BINDING,
)
from gameplay_rules.mana_ability_design.package import (
    load_design_package, package_manifest as design_package_manifest,
)
from .contracts import _exact, _json
from .dependency_package import _read
from .bounded_casting_contracts import BoundedCastingReview
from .bounded_mana_contracts import (
    BoundedManaProjection, BoundedManaReview, CANONICAL_MAIN, SOURCE_BINDING,
    BOUNDARY_FLAGS, PRIOR_PACKAGE_IDS, DESIGN_IDS,
)
from .bounded_mana_scope import SELECTED_REFERENCES


TARGET_PROFILE = "magic-comprehensive-rules-20260925-v1"
SECTION_REFERENCE_STATE = "SECTION_REFERENCE_RESOLVED_BY_COMPLETE_FAMILY"
SOURCE_COVERAGE = "REPRESENTED_WITH_OPEN_DEPENDENCIES"
FICTIONAL_AUTHORITY_FINDING = "FICTIONAL_MANA_DOES_NOT_SATISFY_REAL_605"
EXTERNAL_REFERENCES = ("115.6", "606", "602.2", "405.6c", "603")
FAMILY_CHILDREN = {
    "605.1": ["605.1a", "605.1b"], "605.2": [],
    "605.3": ["605.3a", "605.3b", "605.3c"],
    "605.4": ["605.4a"], "605.5": ["605.5a", "605.5b"],
}
CAPABILITY_SOURCE_REFERENCES = {
    "mana_ability_classification": ["605.1", "605.1a", "605.1b", "605.2",
                                    "605.5", "605.5a", "605.5b"],
    "activated_mana_ability_activation_window": ["605.3", "605.3a"],
    "activated_mana_ability_immediate_resolution": ["605.3", "605.3b", "605.3c"],
    "triggered_mana_ability_immediate_resolution": ["605.4", "605.4a"],
    "mana_ability_controller_attribution": ["605.1", "605.1a", "605.1b", "605.3b", "605.4a"],
    "mana_payment_opportunity": ["605.3", "605.3a"],
    "mana_production_semantics": [], "mana_pool_semantics": [],
}
COMMON_READINESS = {
    "target_profile_id": TARGET_PROFILE, "semantic_closure": "OPEN",
    "dependency_closure": "OPEN", "execution_readiness": "EXECUTION_BLOCKED",
    "execution_ready": False, "execution_supported": False,
    "required_primitives_available": False, "real_execution_primitives_available": [],
    "runtime_implemented": False, "readiness_code": "REAL_EXECUTION_PROFILE_NOT_READY",
    "fictional_mana_satisfies_real_605": False,
}
NEXT_MILESTONE = {
    "candidate": "Mana Ability Direct Dependency Design",
    "exact_proposed_scope": list(EXTERNAL_REFERENCES),
    "scope_kind": "VERIFIED_FRONTIER_GROUPING_AND_AUTHORITY_BOUNDARY_DESIGN",
    "rationale": "The verified frontier combines targeting, loyalty, a stack exception and two "
                 "large ability subsystems. A separate design should decide coherent bounded "
                 "projection groups before any of those targets is admitted.",
    "source_txt_required": False,
    "source_basis": "RETAINED_VERIFIED_FRONTIER_ONLY_NOT_NEW_TARGET_SOURCE_KNOWLEDGE",
    "future_source_projection_requires_verified_artifact": True,
    "new_source_units_authorized": 0, "authorized": False, "started": False,
}


def _unique(values):
    return list(dict.fromkeys(values))


def _review(kind, projection, findings):
    return BoundedManaReview.create({
        "game_id": "magic", "canonical_base": CANONICAL_MAIN,
        "review_kind": kind, "status": "APPEND_ONLY_REVIEW",
        "bounded_mana_projection_id": projection.identity,
        "source_binding": SOURCE_BINDING, "prior_package_ids": PRIOR_PACKAGE_IDS,
        "design_ids": DESIGN_IDS, "findings": findings, "boundary_flags": BOUNDARY_FLAGS,
    })


def _bindings(rules, references):
    return [{"rule_reference": ref, "rule_id": rules[ref]["rule_id"]}
            for ref in references]


def _frontier(rules):
    return [{"from_reference": ref, "from_rule_id": rule["rule_id"],
             "target_reference": target,
             "reference_state": "DIRECT_REFERENCE_RESOLVED" if target in rules else "UNRESOLVED",
             "coverage_state": "PROJECTED_IN_THIS_MILESTONE" if target in rules else "UNPROJECTED",
             "evidence_basis": "VERIFIED_SELECTED_SOURCE_BLOCK_CITATION"}
            for ref, rule in rules.items() for target in rule["direct_dependency_references"]]


def _correspondence(rules):
    observations = (
        ("activated_vs_triggered_classification", ["605.1", "605.1a", "605.1b"], "VERIFIED",
         "Separate criteria govern activated and triggered abilities; mana output alone is insufficient."),
        ("no_target_requirements", ["605.1a", "605.1b"], "VERIFIED",
         "Both classes require target knowledge; the targeting definition remains open."),
        ("could_add_mana", ["605.1a", "605.1b"], "VERIFIED",
         "Potential output is a criterion distinct from the current output of the ability."),
        ("loyalty_exclusion", ["605.1a"], "VERIFIED", "The activated criteria exclude loyalty abilities."),
        ("library_movement_exclusion", ["605.1a"], "VERIFIED",
         "Neither the cost nor the effect may move a card across a library boundary."),
        ("replacement_effect_distinction", ["605.1a"], "VERIFIED_WITH_REFINEMENT",
         "Classification disregards other replacement effects but retains self-replacement knowledge."),
        ("triggered_qualifying_relationships", ["605.1b"], "VERIFIED",
         "Activated-mana activation, activated-mana resolution and mana-added events are distinct qualifying branches."),
        ("classification_persistence", ["605.2"], "VERIFIED",
         "An unproductive current state does not by itself remove the rule classification."),
        ("priority_activation_window", ["605.3a"], "VERIFIED", "Priority is an activation-context category."),
        ("spell_payment_activation_window", ["605.3a"], "VERIFIED",
         "Casting that requires mana supplies a separate activation-context category."),
        ("ability_payment_activation_window", ["605.3a"], "VERIFIED",
         "Activating an ability that requires mana supplies another context category."),
        ("rule_or_effect_payment_request", ["605.3a"], "VERIFIED_WITH_REFINEMENT",
         "Payment requests can supply an opportunity during otherwise ongoing casting, activation or resolution."),
        ("activated_no_stack_behavior", ["605.3b"], "VERIFIED",
         "No stack object is created; ordinary stack targeting, countering and responses are unavailable."),
        ("activated_immediate_resolution", ["605.3b"], "VERIFIED",
         "Resolution follows activation immediately, without supplying a resolution runtime."),
        ("reactivation_prohibition", ["605.3c"], "VERIFIED",
         "The same ability cannot be activated again before the ongoing activation resolves."),
        ("triggered_no_stack_behavior", ["605.4a"], "VERIFIED",
         "The triggered mana exception also avoids stack-object behavior."),
        ("triggered_immediate_sequencing", ["605.4a"], "VERIFIED",
         "Resolution follows the causing mana ability immediately."),
        ("triggered_no_priority_wait", ["605.4a"], "VERIFIED",
         "The special sequence does not wait for a priority opportunity."),
        ("explicit_non_mana_cases", ["605.1b", "605.5", "605.5a"], "VERIFIED_WITH_REFINEMENT",
         "Targeted, nonqualifying-trigger and nonproductive-trigger cases are exclusions; the complete triggered criteria remain the governing positive definition."),
        ("exclusion_trigger_wording_requires_family_context", ["605.1b", "605.5a"], "FOUND_ADDITIONAL_BOUNDARY",
         "The exclusion discussion uses an activation-event description, while the positive criteria also name resolution and mana-added branches. Both descriptions are retained without treating the exclusion discussion as an exhaustive definition or making a runtime precedence ruling."),
        ("spell_exclusion", ["605.5", "605.5b"], "VERIFIED",
         "A spell remains outside mana-ability classification even when its effect can add mana."),
        ("other_effects_and_timing_restrictions", ["605.1"], "FOUND_ADDITIONAL_BOUNDARY",
         "Other effects and timing restrictions do not replace the family criteria; present activation eligibility stays separate."),
        ("general_activated_procedure", ["605.3"], "FOUND_ADDITIONAL_BOUNDARY",
         "The exceptions rely on the still-unprojected general activation procedure at 602.2."),
        ("general_triggered_procedure", ["605.4"], "FOUND_ADDITIONAL_BOUNDARY",
         "The exception relies on the still-unprojected triggered-ability subsystem at 603."),
        ("historical_oracle_context", ["605.5b"], "FOUND_ADDITIONAL_BOUNDARY",
         "HISTORICAL_ORACLE_CONTEXT_NOT_INGESTED; no card identities, Oracle records or historical examples are retained."),
    )
    rows = [{"observation": name, "finding": finding,
             "historical_authority": "PM_SUPPLIED_DESIGN_INPUT_NOT_SOURCE_VERIFIED",
             "source_rule_bindings": _bindings(rules, refs),
             "project_authored_assessment": assessment}
            for name, refs, finding, assessment in observations]
    statuses = ("VERIFIED", "VERIFIED_WITH_REFINEMENT", "DID_NOT_VERIFY", "FOUND_ADDITIONAL_BOUNDARY")
    return {
        "historical_design_package_id": PRIOR_PACKAGE_IDS["mana_ability_dependency_design"],
        "historical_design_ids": DESIGN_IDS,
        "historical_design_authority_unchanged": "PM_SUPPLIED_DESIGN_INPUT_NOT_SOURCE_VERIFIED",
        "new_evidence_authority": "EXACT_ARTIFACT_AND_SELECTED_BLOCKS_VERIFIED",
        "observations": rows,
        "semantic_observation_counts": {state: sum(row["finding"] == state for row in rows)
                                        for state in statuses},
        "semantic_observations_contradicted": [],
        "historical_design_package_mutated": False,
        "example_ownership": [{"rule_reference": ref,
            "state": "UNAMBIGUOUS_SELECTED_RULE_OWNERSHIP",
            "basis": "DIRECT_ADJACENCY_BEFORE_SEPARATOR_AND_NEXT_NUMBERED_UNIT",
            "source_anchor": rules[ref]["source_anchor"],
            "included_in_block_hash": True, "example_prose_retained": False}
            for ref in ("605.2", "605.4a")],
        "limitations": ["Source correspondence does not promote the historical design into runtime authority.",
                        "The new review retains only project-authored observations and source-block metadata."],
    }


def _section_reassessment(reference, rules):
    return {
        "rule_reference": reference,
        "historical_consumer_binding": _json(RETAINED_BINDING["consumers"][reference]),
        "previous_explicit_dependency": "605", "previous_dependency_state": "UNRESOLVED",
        "new_section_reference_state": SECTION_REFERENCE_STATE,
        "new_dependency_evidence": _bindings(rules, SELECTED_REFERENCES),
        "concrete_source_unit_named_605_created": False,
        "historical_direct_dependency_array_rewritten": False,
        "historical_rule_reprojected": False, "historical_rule_mutated": False,
        "section_coverage_implies_semantic_closure": False,
        "section_coverage_implies_execution": False, **COMMON_READINESS,
    }


def _capabilities(prior_readiness, rules, frontier):
    capabilities = []
    for old in prior_readiness["capabilities"]:
        row = _json(old)
        name = row["capability_id"]
        refs = CAPABILITY_SOURCE_REFERENCES[name]
        row.update({
            "selected_source_bindings": _bindings(rules, refs),
            "source_coverage": SOURCE_COVERAGE if refs else "OUTSIDE_605_FAMILY_COVERAGE",
            "source_verified": bool(refs), "implementation_status": "NOT_IMPLEMENTED",
            "prior_design_source_coverage": old["source_coverage"],
            "prior_design_evidence_requirements": _json(old["evidence_requirements"]),
            "evidence_requirements": _unique(
                "VERIFIED_SELECTED_605_SOURCE_FAMILY" if refs and
                requirement.startswith("FUTURE_SOURCE_VERIFIED_605") else requirement
                for requirement in old["evidence_requirements"]),
            "verified_unresolved_direct_references": _unique(
                edge["target_reference"] for edge in frontier
                if edge["from_reference"] in refs and edge["reference_state"] == "UNRESOLVED"),
            "source_coverage_implies_execution": False, **COMMON_READINESS,
        })
        capabilities.append(row)
    return capabilities


def build_bounded_mana_reports(projection, *, review_root):
    """Rebuild seven reports after checking the nine immutable prior packages."""
    if type(projection) is not BoundedManaProjection:
        from .bounded_mana_contracts import _fail
        _fail("projection", "typed bounded mana projection required")
    projection.verify()
    root = Path(review_root)
    design = load_design_package(root / "gameplay-rules-mana-ability-design", review_root=root)
    _exact(design_package_manifest(design)["package_id"],
           PRIOR_PACKAGE_IDS["mana_ability_dependency_design"], "mana_design_package")
    coverage = BoundedCastingReview.from_json(_read(
        root / "gameplay-rules-bounded-casting-projection/composite-coverage.json")).to_dict()["findings"]
    _exact(coverage["total_projected_rule_count"], 68, "prior_coverage")
    rules = {row["rule_reference"]: row for row in projection.to_dict()["rules"]}
    _exact(list(rules), SELECTED_REFERENCES, "selected_family")
    frontier = _frontier(rules)
    unresolved = _unique(row["target_reference"] for row in frontier if row["reference_state"] == "UNRESOLVED")
    _exact(unresolved, EXTERNAL_REFERENCES, "verified_external_frontier")
    remaining = _unique([ref for ref in coverage["remaining_unresolved_rules"] if ref != "605"] + unresolved)
    prior_readiness = design["readiness.json"].to_dict()
    capabilities = _capabilities(prior_readiness, rules, frontier)
    by_capability = {row["capability_id"]: row for row in capabilities}
    sections = [_section_reassessment(ref, rules) for ref in ("601.2g", "109.4a")]
    family_rows = [{"rule_reference": ref, "rule_id": rules[ref]["rule_id"],
                    "parent_reference": next((parent for parent, children in FAMILY_CHILDREN.items()
                                              if ref in children), None),
                    "selected_children": FAMILY_CHILDREN.get(ref, []),
                    "coverage_state": "SELECTED_AND_PROJECTED"}
                   for ref in SELECTED_REFERENCES]
    family = {
        "section_reference": "605", "section_heading_is_source_unit": False,
        "synthetic_real_605_rule_created": False,
        "selected_family_references": list(SELECTED_REFERENCES), "rule_count": 13,
        "family_rows": family_rows, "complete_relevant_local_family": True,
        "family_completeness_evidence": "EXACT_ARTIFACT_RELEASE_SPECIFIC_FAMILY_SHAPE_VERIFIED",
        "section_reference_state": SECTION_REFERENCE_STATE,
        "broad_dependency_reassessments": sections,
        "verified_numbered_dependency_findings": frontier,
        "verified_unresolved_direct_references": unresolved,
        "section_resolution_is_concrete_rule_projection": False,
        "section_coverage_implies_semantic_closure": False,
        "section_coverage_implies_execution": False, **COMMON_READINESS,
    }
    consumers = _json(sections)
    consumers[0].update({
        "source_coverage_improvements": ["mana_ability_classification", "special_activation_windows",
                                         "activated_no_stack_and_immediate_behavior"],
        "remaining_unresolved_numbered_dependencies": ["115.6", "606", "602.2", "405.6c", "603"],
        "remaining_semantic_boundaries": ["mana_production_semantics", "mana_pool_semantics",
            "real_ability_and_card_semantics", "payment_integration", "overall_casting_gaps"],
        "required_future_primitives": ["mana_ability_classification_input", "activated_mana_activation_context",
            "activated_mana_immediate_resolution", "mana_payment_opportunity_context"],
    })
    consumers[1].update({
        "source_coverage_improvements": ["mana_ability_classification", "no_actual_stack_behavior"],
        "remaining_unresolved_numbered_dependencies": ["115.6", "606", "602.2", "405.6c", "603"],
        "remaining_semantic_boundaries": ["general_ability_controller_semantics",
            "ability_subtype_semantics", "real_ability_and_card_semantics"],
        "required_future_primitives": ["hypothetical_stack_controller_attribution",
                                       "ability_source_controller_evidence"],
        "actual_stack_presence_required_for_attribution": False,
        "hypothetical_stack_attribution_supplied_by_605": False,
        "controller_attribution_separate_from_casting": True,
    })
    consumer_findings = {
        "prior_consumer_matrix_id": DESIGN_IDS["consumer_matrix_id"],
        "consumer_reassessments": consumers,
        "retained_madness_rules": _json(RETAINED_BINDING["madness_rules"]),
        "retained_zone_change_lookup": _json(RETAINED_BINDING["zone_change_lookup"]),
        "madness_indirect_path": ["702.35b", "BOUNDED_CASTING_PROJECTION", "601.2g", "605"],
        "madness_flow_kind": "INDIRECT_DEPENDENCY_FLOW", "madness_direct_605_citation_created": False,
        "fictional_authority_finding": FICTIONAL_AUTHORITY_FINDING, **COMMON_READINESS,
    }
    classification = {
        **_json(by_capability["mana_ability_classification"]),
        "activated_and_triggered_criteria_distinct": True,
        "produces_mana_alone_is_sufficient": False,
        "classification_implies_current_output": False,
        "classification_implies_current_activation": False,
        "classification_implies_execution": False,
        "classification_current_output_and_activation_separate": True,
        "replacement_effect_scope": "IGNORE_OTHER_REPLACEMENTS_RETAIN_SELF_REPLACEMENT_INFORMATION",
        "spell_that_adds_mana_is_mana_ability": False,
        "historical_oracle_context": "HISTORICAL_ORACLE_CONTEXT_NOT_INGESTED",
    }
    behavior = {
        "capabilities": [_json(by_capability[name]) for name in (
            "activated_mana_ability_activation_window", "activated_mana_ability_immediate_resolution",
            "triggered_mana_ability_immediate_resolution")],
        "activated_behavior_source_references": ["605.3", "605.3a", "605.3b", "605.3c"],
        "triggered_behavior_source_references": ["605.4", "605.4a"],
        "activation_opportunities": ["ordinary_priority", "spell_mana_payment",
            "activated_ability_mana_payment", "rule_requested_mana_payment", "effect_requested_mana_payment"],
        "activation_opportunities_are_semantic_categories_only": True,
        "activated_uses_stack": False, "triggered_uses_stack": False,
        "activated_resolution_relationship": "IMMEDIATELY_AFTER_ACTIVATION",
        "triggered_resolution_relationship": "IMMEDIATELY_AFTER_CAUSING_MANA_ABILITY",
        "same_ability_reactivation_before_resolution_permitted": False,
        "triggered_waits_for_priority": False,
        "general_activated_abilities_covered": False, "general_triggered_abilities_covered": False,
        "verified_dependency_frontier": frontier, **COMMON_READINESS,
    }
    reassessments = []
    for previous in prior_readiness["readiness_reassessments"]:
        row = _json(previous)
        name = row["capability_id"]
        row.update({
            "prior_readiness_id": DESIGN_IDS["readiness_id"],
            "source_coverage": SOURCE_COVERAGE if name != "complete_spell_casting" else "INCOMPLETE",
            "new_section_reference_state": SECTION_REFERENCE_STATE,
            "remaining_unresolved_numbered_dependencies": remaining,
            "blockers": ["605_SOURCE_REPRESENTED_RUNTIME_ABSENT" if item == "605_UNPROJECTED_AND_UNIMPLEMENTED"
                         else item for item in row["blockers"]],
            "historical_consumer_bindings": row.pop("retained_consumer_bindings"),
            **COMMON_READINESS,
        })
        reassessments.append(row)
    overall = {
        "capabilities": capabilities, "readiness_reassessments": reassessments,
        "prior_readiness_id": DESIGN_IDS["readiness_id"],
        "mana_ability_source_coverage": SOURCE_COVERAGE,
        "mana_ability_execution": "EXECUTION_BLOCKED",
        "source_coverage_implies_execution": False,
        "source_coverage_implies_general_activated_abilities": False,
        "source_coverage_implies_general_triggered_abilities": False,
        "one_capability_readiness_implies_another": False,
        "production_pool_payment_boundaries": _json(prior_readiness["production_pool_payment_boundaries"]),
        "fictional_authority": _json(prior_readiness["fictional_authority"]),
        "remaining_unprojected_numbered_boundaries": remaining,
        "verified_dependency_frontier": frontier,
        "required_future_primitives": _json(prior_readiness["required_future_primitives"]),
        "unprojected_casting_stages": ["601.2a", "601.2c", "601.2d", "601.2e", "601.2i"],
        "unresolved_permission_and_rollback": ["601.3", "733"],
        "next_milestone": NEXT_MILESTONE,
        "historical_acquisition_identity": HISTORICAL_ACQUISITION_ID, **COMMON_READINESS,
    }
    components = _json(coverage["projection_components"])
    components[-1].pop("package_binding", None)
    components[-1]["package_id"] = PRIOR_PACKAGE_IDS["bounded_casting_projection"]
    components.append({"projection_id": projection.identity,
        "package_binding": "THIS_ENCLOSING_BOUNDED_MANA_PACKAGE",
        "projected_references": list(SELECTED_REFERENCES), "mutated": False})
    references = coverage["projected_references"] + list(SELECTED_REFERENCES)
    if (len(references) != 81 or len(set(references)) != 81 or "605" in references or
            len(components) != 7 or len({row["projection_id"] for row in components}) != 7):
        from .bounded_mana_contracts import _fail
        _fail("composite", "seven distinct projections and exactly 81 concrete source units required")
    composite = {
        "view_kind": "READ_ONLY_SEVEN_PROJECTION_COMPOSITE", "previous_projected_rule_count": 68,
        "new_projected_rule_count": 13, "total_projected_rule_count": len(references),
        "component_rule_counts": [20, 12, 7, 12, 12, 5, 13],
        "projected_references": references, "projection_components": components,
        "component_identities_preserved": True, "prior_design_package_id": PRIOR_PACKAGE_IDS["mana_ability_dependency_design"],
        "remaining_unresolved_rules": remaining, "resolved_section_references": ["605"],
        "section_reference_resolution": SECTION_REFERENCE_STATE,
        "historical_acquisition_identity": HISTORICAL_ACQUISITION_ID,
        "historical_anchors_converted": False, "source_policy_clearance": "not_granted", **COMMON_READINESS,
    }
    return {
        "design-source-correspondence.json": _review("design_source_correspondence", projection, _correspondence(rules)),
        "family-closure-review.json": _review("family_closure_review", projection, family),
        "consumer-reassessment.json": _review("consumer_reassessment", projection, consumer_findings),
        "classification-readiness.json": _review("classification_readiness", projection, classification),
        "behavior-readiness.json": _review("behavior_readiness", projection, behavior),
        "overall-readiness.json": _review("overall_readiness", projection, overall),
        "composite-coverage.json": _review("composite_coverage", projection, composite),
    }
