"""Finite project-authored assessments for the three-unit activation projection.

Historical design findings are copied into new reviews only with explicit
current authority; no historical record or authorization is modified.
"""
from copy import deepcopy

from gameplay_rules.activated_ability_design.inspection import expected_inspection
from gameplay_rules.activated_ability_design.records import authored_records as design_records
from gameplay_rules.activated_ability_design.records import MANA_FAMILY


def authored_records(binding, projection):
    historical = design_records(binding, expected_inspection())
    rules = {item["rule_reference"]: item for item in projection["rules"]}
    design_name = "gameplay-rules-activated-ability-procedure-design"

    def old(reference):
        return deepcopy(binding["rule_bindings"][reference])

    def new(reference):
        rule = rules[reference]
        return {"rule_reference": reference, "rule_id": rule["rule_id"],
            "projection_id": projection["projection_id"],
            "package_binding": "THIS_ENCLOSING_PACKAGE",
            "anchor_identity": rule["source_anchor"]["anchor_id"],
            "source_anchor": deepcopy(rule["source_anchor"])}

    def review(name, findings):
        return {"schema_version": 1, "record_kind": name,
            "canonical_base": binding["canonical_base"],
            "status": "BOUNDED_ACTIVATED_ABILITY_PROCEDURE_PROJECTED",
            "non_executable": True, "source_body_retained": False,
            "semantic_closure": "OPEN", "execution_readiness": "BLOCKED",
            "findings": findings}

    direct = {"origin_reference": "605.3", "target_reference": "602.2",
        "relationship": "LITERAL_DIRECT_NUMBERED_REFERENCE",
        "state": "DIRECT_REFERENCE_RESOLVED", "origin_evidence": old("605.3"),
        "target_evidence": new("602.2"), "historical_dependency_array_rewritten": False,
        "historical_projection_modified": False, "historical_unresolved_review_modified": False,
        "source_correspondence": "RESOLVED", "semantic_closure": "OPEN",
        "design_readiness": "BOUNDED_SOURCE_CONTEXT_WITH_OPEN_REQUIREMENTS",
        "execution_readiness": "BLOCKED"}
    refs = [
        {"origin_reference": "602.2", "target_reference": "733",
         "relationship": "LITERAL_DIRECT_NUMBERED_REFERENCE", "state": "UNRESOLVED",
         "target_coverage": "UNPROJECTED", "origin_evidence": new("602.2")},
        {"origin_reference": "602.2a", "target_reference": "701.20a",
         "relationship": "LITERAL_DIRECT_NUMBERED_REFERENCE", "state": "UNRESOLVED",
         "target_coverage": "UNPROJECTED", "origin_evidence": new("602.2a")},
        {"origin_reference": "602.2b", "target_reference": "601.2f",
         "relationship": "LITERAL_DIRECT_NUMBERED_REFERENCE_FOR_COST_ANALOGY",
         "state": "DIRECT_REFERENCE_RESOLVED", "target_coverage": "PREVIOUSLY_PROJECTED",
         "origin_evidence": new("602.2b"), "target_evidence": old("601.2f")},
    ]
    correspondence = {
        "merged_design_package_id": binding["prior_package_ids"][design_name],
        "merged_design_review_bindings": {name: identity for name, identity in binding["review_bindings"].items()
            if name.startswith(design_name + "/")},
        "historical_fingerprint_authority": "REVIEW_ONLY_NOT_PROJECTED",
        "historical_fingerprints_modified": False,
        "fresh_projection_authority": "OWNER_AUTHORIZED_BOUNDED_SOURCE_PROJECTION",
        "fresh_projected_evidence": [new(reference) for reference in rules],
        "historical_fingerprint_correspondence": expected_inspection(),
        "span_correspondence": "RAW_BYTE_LINE_SPANS_EXCLUDE_FINAL_LINE_TERMINATORS_MATCH_REVIEW_FINGERPRINTS",
        "findings_confirmed": ["parent_and_two_immediate_children", "authority_owner_fallback_and_exception",
            "ordered_procedure_and_fixed_announcements_payments", "illegal_action_reference",
            "announcement_hidden_zone_reveal_and_ordinary_stack_context", "activator_controls_ability",
            "exact_601.2b_through_601.2i_range", "separate_601.2f_cost_analogy"],
        "projection_refinements": ["three_new_content_derived_rule_and_anchor_identities",
            "incoming_605.3_direct_source_correspondence_resolved",
            "outgoing_601.2f_direct_source_correspondence_resolved"],
        "local_source_scope": "COHERENT_THREE_UNIT_PARENT_AND_IMMEDIATE_CHILDREN",
        "new_source_units_projected": 3, "additional_units_required_for_bounded_claim": False,
        "complete_activation_semantics": "OPEN", "semantic_closure": "OPEN",
        "execution_readiness": "BLOCKED", "historical_authority_upgraded": False,
    }
    local = deepcopy(historical["local-scope.json"]["findings"])
    local.update({"current_projection_allowlist": list(rules), "candidate_coverage": "PROJECTED",
        "scope_kind": "EXACT_THREE_UNIT_BOUNDED_PROJECTION", "projected_evidence": [new(ref) for ref in rules],
        "current_605.3_to_602.2": "DIRECT_REFERENCE_RESOLVED",
        "outgoing_literal_references": refs,
        "next_marker": "602.3", "next_marker_body_inspected": False,
        "parent_602_section_projected": False, "complete_procedure_scope_sufficient": False})
    local["insufficient_scope_policy"]["current_assessment"] = "NO_LOCAL_BOUNDARY_GAP_FOUND_FOR_BOUNDED_PROJECTION"
    local["insufficient_scope_policy"]["stop_code"] = "ACTIVATED_ABILITY_PROCEDURE_SCOPE_INSUFFICIENT"
    responsibility = deepcopy(historical["procedure-responsibilities.json"]["findings"])
    for row in responsibility["rows"]:
        row["new_projected_support"] = [new(ref) for ref in row["inspected_candidate_support"]]
        row["state"] = "OPEN / EXECUTION_BLOCKED"
        row["source_coverage"] = "BOUNDED_PROJECTED_CONTEXT_WITH_OPEN_REQUIREMENTS"
    responsibility["all_ten_responsibilities_open"] = True
    responsibility["responsibility_count"] = 10
    responsibility["runtime_operations_created"] = []
    imported = deepcopy(historical["casting-import.json"]["findings"])
    imported.update({"authority": "BOUNDED_PROJECTED_SOURCE",
        "origin_evidence": new("602.2b"),
        "relationship_kind": "ONE_RANGE_IMPORT_WITH_EIGHT_MEMBER_ROWS",
        "range_start": "601.2b", "range_end": "601.2i", "member_count": 8,
        "literal_direct_reference_edges_inferred_from_membership": [],
        "additional_applicability_qualifier_found": False,
        "range_import_count": 1, "source_bodies_imported_into_projection": 0,
        "all_range_members_projected": False,
        "separate_literal_cost_citation": refs[-1]})
    cost = {"origin": new("602.2b"), "stage": old("601.2f"),
        "direct_reference_state": "DIRECT_REFERENCE_RESOLVED",
        "range_relationship_separate_from_literal_cost_citation": True,
        "from_concept": "SPELL_MANA_COST", "to_concept": "ABILITY_ACTIVATION_COST",
        "mapping_direction": "REPLACE_SPELL_MANA_COST_CONCEPT_WITH_ABILITY_ACTIVATION_COST_CONCEPT",
        "activation_and_casting_action_identities": "DISTINCT",
        "costs_calculated": False, "payments_performed": False,
        "card_semantics_supplied": False, "cost_parser_supplied": False,
        "casting_or_activation_runtime_supplied": False,
        "semantic_closure": "OPEN", "execution_readiness": "BLOCKED"}
    mana = deepcopy(historical["mana-relationships.json"]["findings"])
    mana["general_procedure"].update({"coverage": "BOUNDED_PROJECTED_CONTEXT",
        "projected_evidence": [new(ref) for ref in rules]})
    mana["preserved_relationships"][0] = deepcopy(direct)
    mana["qualifying_activated_mana_exception"]["ordinary_stack_placement_unconditional"] = False
    mana["preserved_complete_family_mappings"] = [{"origin": ref,
        "target": "605", "state": "SECTION_REFERENCE_RESOLVED_BY_COMPLETE_FAMILY",
        "origin_evidence": old(ref), "concrete_family_count": 13,
        "concrete_family_bindings": [old(member) for member in MANA_FAMILY],
        "synthetic_605_rule_created": False} for ref in ("601.2g", "109.4a")]
    mana["triggered_mana_no_stack_and_immediate_resolution_evidence"] = old("605.4a")
    mana["direct_117_citation_invented"] = False
    mana["controller_attribution_separate_from_ordinary_stack_placement"] = True
    consumers = deepcopy(historical["consumer-bindings.json"]["findings"])
    consumers["direct_reference_reassessments"] = [deepcopy(direct)]
    consumers["outgoing_reference_assessments"] = deepcopy(refs)
    consumers["unprojected_activation_inspection_closes_consumers"] = False
    consumers["source_projection_closes_consumer_semantics"] = False
    consumers["controller_109.4a_closed_by_602.2a"] = False
    for row in consumers["rows"]:
        row["source_coverage_state"] = "IMPROVED_INDIRECTLY" if row["consumer"] in (
            "601.2g", "bounded_casting", "madness") else "BOUNDED_CONTEXT_WITH_OPEN_REQUIREMENTS"
        if row["consumer"] == "605.3":
            row["source_correspondence"] = "DIRECT_REFERENCE_RESOLVED"
            row["new_target_evidence"] = new("602.2")
        row["new_direct_edges"] = []
    consumers["existing_indirect_routes_preserved"] = True
    components = deepcopy(binding["projection_components"])
    components.append({"name": "bounded_activated_ability_procedure",
        "projection_id": projection["projection_id"], "package_binding": "THIS_ENCLOSING_PACKAGE",
        "projected_references": list(rules)})
    all_refs = [ref for component in components for ref in component["projected_references"]]
    assert len(components) == len({item["projection_id"] for item in components}) == 10
    assert len(all_refs) == len(set(all_refs)) == 88
    assert set(all_refs) - set(binding["rule_bindings"]) == set(rules)
    composite = {"view_kind": "READ_ONLY_TEN_PROJECTION_COMPOSITE",
        "projection_components": components, "projected_references": all_refs,
        "previous_count": 85, "new_count": 3, "total_projected_rule_count": 88,
        "previous_projection_count": 9, "total_projection_count": 10,
        "projection_component_counts": [len(item["projected_references"]) for item in components],
        "projection_identities_preserved": True, "monolithic_projection_created": False,
        "all_prior_rule_bindings": deepcopy(binding["rule_bindings"]),
        "synthetic_605_rule_created": False, "additional_rules_projected": []}
    readiness = {"result": "BOUNDED_ACTIVATED_ABILITY_PROCEDURE_PROJECTED",
        "source_coverage": "EXACT_THREE_UNIT_BOUNDED_PROJECTION",
        "source_correspondence": "IMPROVED", "design_readiness": "BOUNDED_REVIEW_CONTRACT_COMPLETE",
        "semantic_closure": "OPEN", "execution_readiness": "BLOCKED",
        "real_profile": "DESIGN_ONLY / NOT EXECUTABLE", "readiness_code": "REAL_EXECUTION_PROFILE_NOT_READY",
        "new_source_units_projected": 3, "projected_real_source_units": 88,
        "distinct_projections": 10, "all_ten_responsibilities": "OPEN / EXECUTION_BLOCKED",
        "unprojected_literal_targets": ["733", "701.20a"],
        "unprojected_import_members": ["601.2c", "601.2d", "601.2e", "601.2i"],
        "unresolved_shared_triggered_frontiers": ["605.4 -> 603", "109.4b -> 603", "603.7d", "603.7e", "603.7f"],
        "other_open_boundaries": ["ability_recognition", "activation_authority_and_controller", "real_Card_and_effect_semantics",
            "timing_and_permission", "stack_and_priority", "cost_determination", "mana_and_nonmana_payment",
            "mana_production", "rollback", "downstream_resolution", "109.4a_hypothetical_stack_attribution", "606_partial", "613"],
        "remaining_blocker_reassessment": {"range_coverage": "FOUR_OF_EIGHT_MEMBERS_PROJECTED_INCOMPLETE",
            "direct_source_improvements": ["605.3 -> 602.2", "602.2b -> 601.2f"],
            "semantic_closure_from_direct_resolution": False,
            "compared_frontiers": ["shared_imported_casting_stages", "reveal", "illegal_action_recovery",
                "shared_triggered_subsystem", "independent_runtime_semantics"],
            "choice": "REVIEW_SCOPE_BEFORE_SELECTING_FURTHER_SOURCE_UNITS",
            "reason": "The imported range is shared by activation and retained casting consumers; compare its missing stages with independent frontiers before a future bounded source authorization."},
        "next_milestone_recommendation_count": 1,
        "next_milestone": {"milestone": "Shared Casting-Stage Gap Scope Design",
            "scope_kind": "REVIEW_ONLY_NO_SOURCE_PROJECTION", "expected_new_source_units": 0,
            "future_projection_allowlist": [], "source_bodies_inspected_in_current_milestone": [],
            "future_milestone_authorized": False, "future_source_projection_authorized": False,
            "future_milestone_begun": False},
        "real_snapshot_created": False, "real_execution_profile_activated": False,
        "admission_eligible": False, "runtime_implemented": False,
        "source_policy_clearance": "not_granted", "fictional_evidence_satisfies_real_rules": False,
        "permissions": {name: "NOT_ESTABLISHED" for name in
            ("private_retention", "redistribution", "free_service", "commercial_service", "ai_export")},
        "preserved_baseline": {"canonical_base": binding["canonical_base"],
            "source_files": 339, "gameplay_evidence_files": 115, "gameplay_evidence_directories": 18,
            "total_protected_files": 454, "historical_acquisition_identity": binding["historical_acquisition_identity"]}}
    bodies = {"design-source-correspondence.json": correspondence, "local-scope.json": local,
        "procedure-responsibilities.json": responsibility, "casting-import.json": imported,
        "cost-analogy.json": cost, "mana-relationships.json": mana,
        "consumer-reassessment.json": consumers, "composite-coverage.json": composite,
        "overall-readiness.json": readiness}
    return {name: review(name, value) for name, value in bodies.items()}
