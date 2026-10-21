"""Closed authored reassessments for the single target-declaration source unit.

Relationships retain their source, import, contextual or semantic provenance.
These records neither interpret Cards nor implement any gameplay operation.
"""
from copy import deepcopy

CANONICAL_MAIN = "9953142e6b729f8ca34a008dc5e8fcf5b642ad54"
DESIGN_NAME = "gameplay-rules-shared-casting-stage-gap-design"
DESIGN_ID = "sha256:4ec995686f7ebb851fae1d6a3b732b1669a9f8cbe7d7ad547f939d928b6c729f"
DESIGN_REVIEWS = {
    "source-inspection.json": "sha256:b238417023f10c4ebfd83340b6a105b95829c599126d5ab7bf52d941b8f23bc9",
    "gap-matrix.json": "sha256:cc01606c8b108280ca76dccb89ce700eea565a9091f9c900a368ec860dc3a457",
    "consumer-dependencies.json": "sha256:d6543775e61d816bc11434f608df7bf497420db49e40bbe1d8be38481d841265",
    "scope-recommendation.json": "sha256:d07657a9b7d732ef6255d973d8e027687454d2e1e671f18dd113bad72662319b",
    "readiness.json": "sha256:f7f51e9b5d0103580f7530cdf8c6d5425496cbe6aba75f6cc343a3b1f803db69",
}
PERMISSIONS = {name: "NOT_ESTABLISHED" for name in (
    "private_retention", "redistribution", "free_service", "commercial_service", "ai_export")}


def authored_records(binding, projection):
    rule = projection["rules"][0]
    new = {"rule_reference": "601.2c", "rule_id": rule["rule_id"],
        "projection_id": projection["projection_id"],
        "package_binding": "THIS_ENCLOSING_PACKAGE",
        "anchor_identity": rule["source_anchor"]["anchor_id"],
        "source_anchor": deepcopy(rule["source_anchor"])}

    def old(reference):
        return {"rule_reference": reference, **deepcopy(binding["rule_bindings"][reference])}

    def record(name, findings):
        return {"schema_version": 1, "record_type": name.removesuffix(".json"),
            "canonical_base": CANONICAL_MAIN,
            "status": "BOUNDED_SHARED_TARGET_DECLARATION_PROJECTED",
            "non_executable": True, "source_body_retained": False,
            "semantic_closure": "OPEN", "execution_readiness": "BLOCKED",
            "findings": findings}

    correspondence = {
        "merged_design_package": DESIGN_NAME, "merged_design_package_id": DESIGN_ID,
        "merged_design_review_ids": deepcopy(DESIGN_REVIEWS),
        "historical_observation": {"record": "gap-matrix.json", "reference": "601.2c",
            "authority": "RETAINED_PR201_REVIEW_ONLY_SOURCE_OBSERVATION",
            "historical_coverage": "UNPROJECTED", "historical_record_modified": False},
        "fresh_authority": "OWNER_AUTHORIZED_C_ONLY_COMPLETE_UNIT_SOURCE_VERIFICATION",
        "projected_evidence": deepcopy(new),
        "complete_unit": {"physical_lines": [2467, 2468], "line_count": 2,
            "owned_example_lines": 1, "span_length": 1970,
            "internal_line_endings_preserved": True, "final_line_terminator_excluded": True,
            "following_separator_excluded": True, "next_marker": "601.2d",
            "next_marker_physical_line": 2470, "next_marker_body_inspected": False,
            "example_is_separate_source_unit": False},
        "material_clauses_verified": [
            "appropriate_objects_and_players_are_declared",
            "some_target_requirements_depend_on_alternative_or_additional_cost_or_selected_mode",
            "targets_of_an_unmet_target_requirement_condition_are_not_required",
            "cost_choice_can_condition_alternative_target_requirements",
            "variable_target_count_declared_before_recipients_and_can_follow_spell_text",
            "declared_count_stays_fixed_despite_later_information_change",
            "recipient_reuse_is_restricted_within_one_targeting_instance",
            "separate_instances_allow_reuse_only_if_each_instance_criteria_are_met",
            "mandatory_choices_maximize_compliance_subject_to_all_prohibitions",
            "chosen_recipients_become_targets_and_become_target_triggers_occur_at_this_stage",
            "placement_of_those_triggers_waits_for_casting_completion"],
        "literal_outgoing_numbered_citations": [], "literal_outgoing_ranges": [],
        "design_summary_mechanically_promoted": False,
        "source_provenance": "CASTING_A_SPELL", "activation_relevance": "RETAINED_602.2b_RANGE_IMPORT",
        "additional_source_unit_required_for_bounded_knowledge": False,
        "stop_code": "SHARED_TARGET_DECLARATION_SCOPE_INSUFFICIENT",
        "offline_metadata_is_fresh_source_reproduction": False,
    }
    parent = {
        "origin_reference": "601.2", "target_reference": "601.2c",
        "state": "DIRECT_REFERENCE_RESOLVED", "assessment_level": "SOURCE_COVERAGE_ONLY",
        "relationship": "NORMALIZED_MEMBER_OF_EXPLICIT_PROPOSAL_RANGE",
        "origin_evidence": old("601.2"), "target_evidence": deepcopy(new),
        "source_provenance": {"explicit_range_start": "601.2a", "explicit_range_end": "601.2d",
            "parent_individually_enumerates_c": False,
            "retained_stage_matrix_review_id": "sha256:1ff70a9784999534b8be163bedea7b0e726bd5c13c794cef28632a74c71f6747"},
        "proposal_range_members": ["601.2a", "601.2b", "601.2c", "601.2d"],
        "projected_proposal_members": ["601.2b", "601.2c"],
        "unprojected_proposal_members": ["601.2a", "601.2d"],
        "proposal_range_complete": False, "parent_procedure_complete": False,
        "historical_dependency_arrays_changed": False, "historical_unresolved_records_changed": False,
        "historical_coverage_counts_changed": False,
    }
    projected = ["601.2b", "601.2c", "601.2f", "601.2g", "601.2h"]
    missing = ["601.2d", "601.2e", "601.2i"]
    members = []
    for suffix in "bcdefghi":
        reference = "601.2" + suffix
        members.append({"reference": reference,
            "relationship": "MEMBER_OF_SINGLE_602.2b_CASTING_RANGE_IMPORT",
            "coverage": "PROJECTED" if reference in projected else "UNPROJECTED",
            "body_authority": ("NEW_C_ONLY_SOURCE_PROJECTION" if reference == "601.2c" else
                "RETAINED_PROJECTED_SOURCE" if reference in projected else "RETAINED_PR201_REVIEW_ONLY_OBSERVATION"),
            "projected_evidence": deepcopy(new) if reference == "601.2c" else
                old(reference) if reference in projected else None,
            "semantic_closure": "OPEN", "execution_readiness": "BLOCKED"})
    imported = {
        "origin_reference": "602.2b", "origin_evidence": old("602.2b"),
        "relationship_kind": "ONE_RANGE_IMPORT_WITH_EIGHT_MEMBER_ROWS",
        "range_import_count": 1, "range_start": "601.2b", "range_end": "601.2i",
        "member_count": 8, "range_members": members,
        "projected_members": projected, "unprojected_members": missing,
        "projected_member_count_before": 4, "projected_member_count_after": 5,
        "member_coverage": "5/8", "all_range_members_projected": False,
        "range_state": "PARTIAL_SOURCE_COVERAGE", "excluded_stages": ["601.2a"],
        "literal_direct_reference_edges_inferred_from_membership": [],
        "additional_applicability_qualifier_found": False,
        "casting_and_activation_interchangeable": False,
        "separate_cost_analogy": {"origin": "602.2b", "target": "601.2f",
            "state": "DIRECT_REFERENCE_RESOLVED", "relationship": "SEPARATE_LITERAL_COST_ANALOGY",
            "origin_evidence": old("602.2b"), "target_evidence": old("601.2f")},
        "historical_pr200_and_pr201_four_of_eight_records_modified": False,
        "source_bodies_imported_into_projection": 0, "runtime_dispatch_created": False,
    }
    responsibility_names = binding["responsibility_names"]
    consumers = {
        "target_concepts": {
            "requiring_targets": "A target requirement is distinct from how many targets are actually chosen.",
            "actual_chosen_target_count": "The declared count may be zero where permitted; zero alone does not prove absence of a target requirement.",
            "targeted_status": "Retained 115.6 requires one or more actually chosen targets for its targeted-status classification.",
            "zero_count_establishes_mana_ability_eligibility": False,
            "retained_115_6_evidence": old("115.6"),
            "relationship_to_c": "RETAINED_CLASSIFICATION_CONTEXT_WITHOUT_LITERAL_C_CITATION"},
        "context_relationships": [
            {"reference": "601.2b", "kind": "RETAINED_EARLIER_CHOICE_CONTEXT", "literal_citation_from_c": False, "evidence": old("601.2b")},
            {"reference": "601.2d", "kind": "STRUCTURAL_LATER_ALLOCATION_CONTEXT", "literal_citation_from_c": False, "coverage": "UNPROJECTED_REVIEW_ONLY"},
            {"reference": "601.2i", "kind": "RETAINED_COMPLETION_CONTEXT", "literal_citation_from_c": False, "coverage": "UNPROJECTED_REVIEW_ONLY"},
            {"reference": "603", "kind": "SEMANTIC_TRIGGER_REQUIREMENT", "literal_citation_from_c": False, "coverage": "UNPROJECTED"},
            {"reference": "602.2b", "kind": "INCOMING_CONSUMER_RANGE_IMPORT", "literal_citation_from_c": False, "evidence": old("602.2b")}],
        "preserved_relationships": [
            {"origin": "605.3", "target": "602.2", "state": "DIRECT_REFERENCE_RESOLVED", "assessment_level": "SOURCE_COVERAGE_ONLY", "origin_evidence": old("605.3"), "target_evidence": old("602.2")},
            {"origin": "602.2", "target": "733", "state": "UNRESOLVED", "target_coverage": "UNPROJECTED", "origin_evidence": old("602.2")},
            {"origin": "602.2a", "target": "701.20a", "state": "UNRESOLVED", "target_coverage": "UNPROJECTED", "origin_evidence": old("602.2a")}],
        "madness": {"kind": "INDIRECT_CONSUMER", "new_direct_c_citation": False,
            "route": ["retained Madness casting evidence", "bounded casting and mana context", "605.3 to 602.2", "602.2b imported range"], "execution_readiness": "BLOCKED"},
        "trigger_consequence": {"source_evidence": deepcopy(new),
            "condition": "AN_ABILITY_TRIGGERS_WHEN_A_CHOSEN_RECIPIENT_BECOMES_TARGET_OF_A_SPELL",
            "description": "Chosen recipients become targets during this stage; applicable becoming-targeted abilities trigger then, with placement deferred until casting is complete.",
            "descriptive_knowledge_only": True, "detection_implemented": False,
            "placement_implemented": False, "ordering_implemented": False,
            "casting_completion_implemented": False,
            "universal_activated_mana_trigger_or_priority_rule_inferred": False},
        "mana_distinctions": {
            "complete_605_family_source_coverage_establishes_semantic_closure": False,
            "activated_mana_no_stack": old("605.3b"),
            "immediate_resolution_and_conditional_post_activation_priority": old("405.6c"),
            "priority_condition": "PRIORITY_IMMEDIATELY_BEFORE_ACTIVATION",
            "independent_triggered_mana_evidence": old("605.4a"),
            "605_4a_direct_citation_to_405_6c_invented": False,
            "109_4a_hypothetical_stack_controller_distinct_from_actual_stack_presence": True,
            "109_4a_closed_by_602_2a": False, "broad_606_complete": False,
            "unprojected_loyalty_rules": ["606.3", "606.4", "606.5", "606.6"],
            "shared_triggered_dependencies": ["603", "603.7d", "603.7e", "603.7f"]},
        "activated_responsibilities": [{"responsibility": name, "state": "OPEN / EXECUTION_BLOCKED",
            "implementation_available": False} for name in responsibility_names],
        "responsibility_count": 10,
        "unsupported_operations": ["target_parser", "target_requirement_recognizer", "legal_target_set_generation",
            "target_choices", "compatibility_solver", "Card_or_effect_interpretation", "Oracle_ingestion",
            "distribution_allocation", "effect_execution", "casting_or_activation_execution",
            "cost_determination", "payment", "mana_production", "stack", "priority",
            "trigger_detection_placement_or_ordering", "rollback", "casting_completion", "real_gameplay_simulation"],
        "unprojected_d_e_i_origins_create_projected_edges": False,
        "historical_product_collation_rules_separate": True, "synthetic_material_is_real_source_evidence": False,
    }
    components = deepcopy(binding["projection_components"])
    components.append({"name": "bounded_shared_target_declaration",
        "projection_id": projection["projection_id"], "package_binding": "THIS_ENCLOSING_PACKAGE",
        "projected_references": ["601.2c"]})
    references = [ref for component in components for ref in component["projected_references"]]
    if len(components) != 11 or len({item["projection_id"] for item in components}) != 11 or len(references) != 89 or len(set(references)) != 89:
        raise ValueError("exact eleven-projection distinct coverage required")
    composite = {"view_kind": "READ_ONLY_ELEVEN_PROJECTION_COMPOSITE", "projection_components": components,
        "projected_references": references, "previous_count": 88, "new_count": 1,
        "total_projected_rule_count": 89, "previous_projection_count": 10, "total_projection_count": 11,
        "projection_component_counts": [len(item["projected_references"]) for item in components],
        "all_prior_rule_bindings": deepcopy(binding["rule_bindings"]),
        "new_rule_binding": deepcopy(new), "prior_rule_bindings_changed": False,
        "monolithic_projection_created": False, "additional_rules_projected": []}
    readiness = {
        "source_coverage_achieved": {"admission": ["601.2c"], "added_units": 1, "total_units": 89,
            "distinct_projections": 11, "activated_import": "5/8", "parent_c_reference": "DIRECT_REFERENCE_RESOLVED"},
        "retained_review_only_knowledge": ["601.2d", "601.2e", "601.2i"],
        "semantic_responsibilities": "ALL_TEN_OPEN / EXECUTION_BLOCKED",
        "execution_supported": False, "execution_readiness": "BLOCKED",
        "real_profile": "DESIGN_ONLY / NOT EXECUTABLE", "readiness_code": "REAL_EXECUTION_PROFILE_NOT_READY",
        "real_snapshot_created": False, "real_execution_profile_activated": False,
        "admission_eligible": False, "runtime_implemented": False,
        "source_policy_clearance": "not_granted", "permissions": deepcopy(PERMISSIONS),
        "baseline_preservation": {"canonical_base": CANONICAL_MAIN, "source_files": 347,
            "gameplay_evidence_files": 132, "gameplay_evidence_directories": 20, "protected_files": 479,
            "sorted_protected_rows_sha256": "05b68d15be6c6a5f321b1ba633e163f029211353383cc2add816902203152f68",
            "independent_guard_fixture_sha256": "304a26435fe18bfa9a9e093b43f6186c94d4d1d36d9f5986135f0f08058a3cda",
            "inherited_review_tool": "scripts/shared_casting_stage_gap_design.py",
            "inherited_review_tool_bytes": 27105,
            "inherited_review_tool_sha256": "d2788448d15a06107c11e9734d4ed82c5a9dca75868cf38a062cb329b5b72f53",
            "historical_inventory_inherited_bytes": 74440,
            "historical_inventory_segments": [69051, 3400, 1989]},
        "protected_identities": {"historical_acquisition": binding["historical_acquisition_identity"],
            "shared_casting_stage_design_package": DESIGN_ID,
            "activated_ability_design_package": "sha256:cfe499b63d673af2337beac94134d30b1dac2a14097e244e79742670ed2ec1b1",
            "activated_ability_projection": "sha256:adaeae6e9da7956facbbe8db13c3f1a597328d184071bd6b6d61780c15957553",
            "activated_ability_projection_package": binding["prior_package_ids"]["gameplay-rules-bounded-activated-ability-procedure-projection"],
            "activated_ability_historical_pins": "sha256:9cc186e74977b66142109faf244fccfe640005041c1b21c1e007a5e751275f2b"},
        "historical_projections_reviews_anchors_manifests_changed": False,
        "pr201_historical_zero_addition_empty_allowlist_88_ten_four_of_eight_false_future_flags_changed": False,
        "required_validation": ["focused_projection_source_package_identity_reassessment_preservation",
            "complete_discovery", "actual_publication_with_nested_complete_discovery",
            "disposable_remote_writer_publication_and_readback", "final_head_hosted_push_and_PR_gates"],
        "hosted_success_inferred_from_local_checks": False, "owner_final_merge_approval": True,
        "future_milestone_authorized": False, "future_source_projection_authorized": False, "future_milestone_begun": False,
    }
    recommendation = {
        "authority": "ARCHITECTURAL_REASSESSMENT_USING_NEW_C_AND_RETAINED_PR201_DESIGN_ONLY",
        "fresh_additional_body_inspection": [],
        "remaining_import_gaps": missing,
        "comparisons": [
            {"candidate": "601.2d", "coverage": "UNPROJECTED_REVIEW_ONLY", "gain": "Distinguish target recipient declaration from conditional distribution allocation using newly projected c context.", "remaining_limits": "No allocation solver, arithmetic, effect execution or legal-action decision."},
            {"candidate": "601.2e", "coverage": "UNPROJECTED_REVIEW_ONLY", "gain": "Locate proposal legality checkpoint.", "remaining_limits": "Recovery reaches unresolved 733, legality criteria and state semantics."},
            {"candidate": "601.2i", "coverage": "UNPROJECTED_REVIEW_ONLY", "gain": "Describe conditional completion transition.", "remaining_limits": "Its retained a-h prerequisite range is incomplete; triggers, characteristics and priority remain open."},
            {"candidate": "701.20a reveal", "coverage": "UNPROJECTED_RETAINED_FRONTIER", "remaining_limits": "Independent hidden-information semantics do not supply shared declaration/allocation knowledge."},
            {"candidate": "733 rollback", "coverage": "UNPROJECTED_RETAINED_FRONTIER", "remaining_limits": "Recovery needs separately designed transaction and reversibility semantics."},
            {"candidate": "shared triggered subsystem", "coverage": "UNPROJECTED_RETAINED_FRONTIER", "remaining_limits": "603 and delayed-controller dependencies need their own design boundary."},
            {"candidate": "independent runtime", "coverage": "UNSUPPORTED", "remaining_limits": "Source coverage alone supplies no recognizers, state transitions, choices, legality or effects."}],
        "recommendation_count": 1,
        "recommendation": {"milestone": "Bounded Shared Target-Allocation Stage Projection",
            "proposed_allowlist": ["601.2d"], "expected_added_source_units": 1,
            "conditional_resulting_units": 90, "conditional_resulting_projections": 12,
            "conditional_activated_import_coverage": "6/8",
            "useful_reasoning_gain": "Explain conditional allocation declarations separately from c target-recipient declaration, now anchored to projected recipient context.",
            "explicit_exclusions": ["601.2a", "601.2c re-projection", "601.2e", "601.2i", "701.20a", "733", "603", "target_choices", "allocation_solver", "effect_execution", "runtime"],
            "remaining_limitations": "Parent proposal and procedure remain incomplete; e/i imports, reveal, recovery, triggers, costs, payment, priority and Card semantics remain open.",
            "requires_separate_owner_authorization_and_fresh_exact_source_verification": True,
            "future_milestone_authorized": False, "future_source_projection_authorized": False,
            "future_milestone_begun": False},
    }
    return {name: record(name, value) for name, value in {
        "design-source-correspondence.json": correspondence,
        "casting-parent-reassessment.json": parent,
        "activated-import-reassessment.json": imported,
        "consumer-semantic-boundaries.json": consumers,
        "composite-coverage.json": composite,
        "preservation-readiness.json": readiness,
        "subsequent-recommendation.json": recommendation}.items()}
