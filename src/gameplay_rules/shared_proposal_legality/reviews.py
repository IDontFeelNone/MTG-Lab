"""Closed authored e assessments with explicit historical and current provenance."""
from copy import deepcopy
from gameplay_rules.errors import GameplayContractError
from gameplay_rules.projection.mana_stack_exception_package import _canonical_candidate
from gameplay_rules.shared_target_allocation.reviews import DESIGN_NAME, DESIGN_ID, DESIGN_REVIEWS, PERMISSIONS

CANONICAL_MAIN = "a21cda0c22092a77ec07097d7b155e7a71bd8de2"


def authored_records(binding, projection):
    _canonical_candidate(binding)
    _canonical_candidate(projection)
    if type(binding) is not dict or type(projection) is not dict:
        raise GameplayContractError("shared_proposal_legality_reviews", "PLAIN_JSON_RECORDS_REQUIRED")
    rule = projection["rules"][0]
    new = {"rule_reference": "601.2e", "rule_id": rule["rule_id"],
        "projection_id": projection["projection_id"], "package_binding": "THIS_ENCLOSING_PACKAGE",
        "anchor_identity": rule["source_anchor"]["anchor_id"], "source_anchor": deepcopy(rule["source_anchor"])}

    def old(reference):
        return {"rule_reference": reference, **deepcopy(binding["rule_bindings"][reference])}

    def record(name, findings):
        return {"schema_version": 1, "record_type": name.removesuffix(".json"),
            "canonical_base": CANONICAL_MAIN, "status": "BOUNDED_SHARED_PROPOSAL_LEGALITY_PROJECTED",
            "non_executable": True, "source_body_retained": False,
            "semantic_closure": "OPEN", "execution_readiness": "BLOCKED", "findings": findings}

    correspondence = {
        "merged_design_package": DESIGN_NAME, "merged_design_package_id": DESIGN_ID,
        "merged_design_review_ids": deepcopy(DESIGN_REVIEWS),
        "historical_observation": {"record": "gap-matrix.json", "reference": "601.2e",
            "authority": "RETAINED_PR201_REVIEW_ONLY_SOURCE_OBSERVATION", "historical_coverage": "UNPROJECTED",
            "historical_record_modified": False, "source_inspection_record": "source-inspection.json",
            "source_inspection_review_id": DESIGN_REVIEWS["source-inspection.json"],
            "historical_raw_fingerprint_matches_new_anchor": True, "historical_registered_projected_source_anchor": False},
        "fresh_authority": "OWNER_AUTHORIZED_E_ONLY_COMPLETE_UNIT_SOURCE_VERIFICATION",
        "projected_evidence": deepcopy(new),
        "complete_unit": {"physical_lines": [2472, 2472], "line_count": 1, "owned_example_lines": 0,
            "span_length": 231, "original_byte_interval": [298690, 298921],
            "raw_span_sha256": "6b30c02c87f09a559eba9525cc331b65ddf668783d526e9f27f52a8447b11249",
            "internal_line_endings_preserved": True, "final_line_terminator_excluded": True,
            "following_separator_excluded": True, "next_marker": "601.2f",
            "next_marker_physical_line": 2474, "next_marker_body_inspected": False},
        "material_clauses_verified": ["game_is_the_checking_mechanism", "proposed_spell_is_checked",
            "question_is_whether_proposed_spell_can_legally_be_cast", "failure_condition_is_illegal_proposed_spell",
            "failure_prescribes_return_to_moment_before_casting_that_spell_was_proposed", "literal_reference_is_733",
            "no_express_positive_legal_outcome_branch"],
        "literal_outgoing_numbered_citations": ["733"], "literal_outgoing_ranges": [],
        "design_summary_mechanically_promoted": False, "source_provenance": "CASTING_A_SPELL",
        "activation_relevance": "RETAINED_602.2b_RANGE_IMPORT",
        "historical_d_following_e_body_uninspected_statement_changed": False,
        "additional_source_unit_required_for_bounded_knowledge": False,
        "stop_code": "SHARED_PROPOSAL_LEGALITY_SCOPE_INSUFFICIENT", "offline_metadata_is_fresh_source_reproduction": False,
    }
    parent = {
        "origin_reference": "601.2", "target_reference": "601.2e",
        "state": "STRUCTURAL_SIBLING_SOURCE_COVERAGE_PROJECTED", "assessment_level": "SOURCE_COVERAGE_ONLY",
        "relationship": "STRUCTURAL_SIBLING_WITHOUT_RETAINED_PARENT_DIRECT_CITATION",
        "origin_evidence": old("601.2"), "target_evidence": deepcopy(new),
        "retained_parent_literal_direct_citation_to_e": False, "parent_to_e_direct_reference_resolved": False,
        "source_provenance": {"explicit_proposal_range": ["601.2a", "601.2d"],
            "explicit_cost_range": ["601.2f", "601.2h"], "other_retained_references": ["601.3", "733"],
            "parent_individually_enumerates_e": False,
            "design_gap_matrix_review_id": DESIGN_REVIEWS["gap-matrix.json"]},
        "proposal_range_members": ["601.2a", "601.2b", "601.2c", "601.2d"],
        "projected_proposal_members": ["601.2b", "601.2c", "601.2d"], "unprojected_proposal_members": ["601.2a"],
        "cost_range_members": ["601.2f", "601.2g", "601.2h"],
        "proposal_range_expanded": False, "proposal_range_complete": False, "parent_procedure_complete": False,
        "historical_dependency_arrays_changed": False, "historical_unresolved_records_changed": False,
        "historical_coverage_counts_changed": False,
    }
    projected = ["601.2b", "601.2c", "601.2d", "601.2e", "601.2f", "601.2g", "601.2h"]
    missing = ["601.2i"]
    imported = {
        "origin_reference": "602.2b", "origin_evidence": old("602.2b"),
        "relationship_kind": "ONE_RANGE_IMPORT_WITH_EIGHT_MEMBER_ROWS", "range_import_count": 1,
        "range_start": "601.2b", "range_end": "601.2i", "member_count": 8,
        "range_members": [{"reference": "601.2" + suffix,
            "relationship": "MEMBER_OF_SINGLE_602.2b_CASTING_RANGE_IMPORT",
            "coverage": "PROJECTED" if suffix != "i" else "UNPROJECTED",
            "body_authority": "NEW_E_ONLY_SOURCE_PROJECTION" if suffix == "e" else
                "RETAINED_PROJECTED_SOURCE" if suffix != "i" else "RETAINED_PR201_REVIEW_ONLY_OBSERVATION",
            "projected_evidence": deepcopy(new) if suffix == "e" else old("601.2" + suffix) if suffix != "i" else None,
            "semantic_closure": "OPEN", "execution_readiness": "BLOCKED"} for suffix in "bcdefghi"],
        "projected_members": projected, "unprojected_members": missing,
        "projected_member_count_before": 6, "projected_member_count_after": 7,
        "member_coverage": "7/8", "all_range_members_projected": False,
        "range_state": "PARTIAL_SOURCE_COVERAGE", "excluded_stages": ["601.2a"],
        "literal_direct_reference_edges_inferred_from_membership": [], "additional_applicability_qualifier_found": False,
        "casting_and_activation_interchangeable": False,
        "spell_specific_checkpoint_generalized_to_unrestricted_ability_rule": False,
        "separate_cost_analogy": {"origin": "602.2b", "target": "601.2f", "state": "DIRECT_REFERENCE_RESOLVED",
            "relationship": "SEPARATE_LITERAL_COST_ANALOGY", "origin_evidence": old("602.2b"), "target_evidence": old("601.2f")},
        "historical_four_five_six_of_eight_records_modified": False,
        "source_bodies_imported_into_projection": 0, "runtime_dispatch_created": False,
    }
    recovery = {
        "origin_reference": "601.2e", "origin_evidence": deepcopy(new), "target_reference": "733",
        "relationship": "DIRECT_NUMBERED_REFERENCE", "state": "UNRESOLVED", "target_source_coverage": "UNPROJECTED",
        "semantic_recovery_closure": "OPEN", "recovery_execution": "BLOCKED",
        "target_node": {"reference": "733", "classification": "UNRESOLVED_RULE", "status": "UNRESOLVED", "coverage_state": "UNPROJECTED"},
        "source_prescribed_conditional_consequence": deepcopy(rule["findings"]["conditional_failure"]),
        "target_body_inspected": False, "target_projected": False, "state_restoration_supported": False,
        "separate_pre_activation_recovery_context": {"origin": "602.2", "context_interchangeable_with_e": False},
        "preserved_dependencies": [
            {"origin": origin, "target": target, "state": "UNRESOLVED", "target_source_coverage": "UNPROJECTED",
                "origin_evidence": old(origin)} for origin, target in
            (("601.2", "733"), ("602.2", "733"), ("602.2a", "701.20a"))],
        "additional_consumer_resolves_recovery": False,
    }
    # Retained descriptions are read as structured evidence; no historical source body is reopened.
    from gameplay_rules.shared_target_allocation import package as allocation
    inherited = allocation._expected_records()
    consumers = deepcopy(inherited["consumer-semantic-boundaries.json"]["findings"])
    consumers.pop("allocation_declaration")
    consumers.pop("unprojected_e_i_origins_create_projected_edges")
    consumers["proposal_checkpoint"] = {"source_evidence": deepcopy(new), **deepcopy(rule["findings"])}
    consumers["context_relationships"] = [{"reference": ref, "kind": kind, "literal_citation_from_e": False,
        **({"evidence": old(ref)} if ref in binding["rule_bindings"] else {"coverage": "UNPROJECTED"})}
        for ref, kind in (("601.2c", "RETAINED_RECIPIENT_DECLARATION"), ("601.2d", "RETAINED_ALLOCATION_DECLARATION"),
            ("601.2f", "STRUCTURAL_LATER_COST_STAGE"), ("601.2i", "RETAINED_REVIEW_ONLY_COMPLETION_CONTEXT"),
            ("601.3", "RETAINED_PARENT_DEPENDENCY"), ("603", "RETAINED_TRIGGER_FRONTIER"),
            ("602.2b", "INCOMING_SINGLE_RANGE_IMPORT"), ("115.6", "RETAINED_TARGET_CLASSIFICATION"))]
    consumers["target_concepts"].pop("relationship_to_d")
    consumers["target_concepts"]["relationship_to_e"] = "RETAINED_CLASSIFICATION_CONTEXT_WITHOUT_LITERAL_E_CITATION"
    consumers["madness"].pop("new_direct_d_citation")
    consumers["madness"]["new_direct_e_citation"] = False
    consumers["preserved_relationships"].insert(1, deepcopy(recovery["preserved_dependencies"][0]))
    consumers["unsupported_operations"] += ["actual_game_legality_adjudication", "proposal_validator", "state_restoration"]
    consumers["knowledge_does_not_establish_legality_casting_activation_or_recovery_completion"] = True
    components = deepcopy(binding["projection_components"])
    components.append({"name": "bounded_shared_proposal_legality", "projection_id": projection["projection_id"],
        "package_binding": "THIS_ENCLOSING_PACKAGE", "projected_references": ["601.2e"]})
    references = [ref for row in components for ref in row["projected_references"]]
    if len(components) != 13 or len({row["projection_id"] for row in components}) != 13 or len(references) != 91 or len(set(references)) != 91:
        raise GameplayContractError("shared_proposal_legality_reviews", "EXACT_91_13_COVERAGE_REQUIRED")
    composite = {"view_kind": "READ_ONLY_THIRTEEN_PROJECTION_COMPOSITE", "projection_components": components,
        "projected_references": references, "previous_count": 90, "new_count": 1,
        "total_projected_rule_count": 91, "previous_projection_count": 12, "total_projection_count": 13,
        "projection_component_counts": [len(row["projected_references"]) for row in components],
        "all_prior_rule_bindings": deepcopy(binding["rule_bindings"]), "new_rule_binding": deepcopy(new),
        "prior_rule_bindings_changed": False, "monolithic_projection_created": False, "additional_rules_projected": []}
    readiness = {
        "source_coverage_achieved": {"admission": ["601.2e"], "added_units": 1, "total_units": 91,
            "distinct_projections": 13, "activated_import": "7/8", "parent_e_relationship": parent["relationship"]},
        "retained_review_only_knowledge": ["601.2i"], "semantic_responsibilities": "ALL_TEN_OPEN / EXECUTION_BLOCKED",
        "execution_supported": False, "execution_readiness": "BLOCKED", "real_profile": "DESIGN_ONLY / NOT EXECUTABLE",
        "readiness_code": "REAL_EXECUTION_PROFILE_NOT_READY", "real_snapshot_created": False,
        "real_execution_profile_activated": False, "admission_eligible": False, "runtime_implemented": False,
        "source_policy_clearance": "not_granted", "permissions": deepcopy(PERMISSIONS),
        "baseline_preservation": {"canonical_base": CANONICAL_MAIN, "source_files": 361,
            "gameplay_evidence_files": 150, "gameplay_evidence_directories": 22, "protected_files": 511,
            "sorted_protected_rows_sha256": "ab6257aa1e9e960a6a81728cb68637a4a7ce5379212dff83a85ce363bbe9defd",
            "independent_guard_fixture_sha256": "ef2bb3484803d44f9e1ad20e1be1c27b15d3901d3b4e1b86b1476662c0c4e094",
            "protected_prior_fixture_count": 6, "protected_document_count": 13,
            "inherited_review_tool": "scripts/shared_casting_stage_gap_design.py", "inherited_review_tool_bytes": 27105,
            "inherited_review_tool_sha256": "d2788448d15a06107c11e9734d4ed82c5a9dca75868cf38a062cb329b5b72f53",
            "historical_inventory_inherited_bytes": 83080, "historical_inventory_segments": [69051,3400,1989,3400,5240],
            "historical_inventory_sha256": "434a05abdba31305dc8ff917ec530aeb8b08c9fdcfa9054fbaaaf47476ac334d",
            "controlled_inventory_files": 82, "controlled_inventory_sha256": "210a951e39781044205cb25b6551809a2c4c3450086cc4c74be37c83da8320d5"},
        "protected_identities": {"historical_acquisition": binding["historical_acquisition_identity"],
            "shared_casting_stage_design_package": DESIGN_ID, "c": old("601.2c"), "d": old("601.2d")},
        "historical_projections_reviews_anchors_manifests_changed": False,
        "historical_88_10_4of8_89_11_5of8_90_12_6of8_and_future_flags_changed": False,
        "historical_d_following_e_body_uninspected_statement_changed": False,
        "required_validation": ["offline_package", "actual_e_only_reproduction", "focused_and_historical_tests",
            "complete_discovery", "actual_publication_with_full_nested_discovery", "final_head_hosted_push_and_PR_logs"],
        "hosted_success_inferred_from_local_checks": False, "owner_final_merge_approval": True,
        "future_milestone_authorized": False, "future_source_projection_authorized": False, "future_milestone_begun": False,
    }
    recommendation = {
        "authority": "ARCHITECTURAL_REASSESSMENT_USING_NEW_E_AND_RETAINED_EVIDENCE_ONLY",
        "fresh_additional_body_inspection": [], "recommendation_count": 1,
        "recommendation": {"milestone": "Proposal-legality criteria dependency scope design",
            "kind": "REVIEW_ONLY_RETAINED_EVIDENCE_DESIGN", "proposed_allowlist": [], "expected_added_source_units": 0,
            "smallest_useful_question": "Which retained dependency and missing-input categories prevent a supported proposal-legality decision after checkpoint coverage?",
            "boundary": "Classify retained references and unknown criteria, Card/effect information and state requirements; propose one separately approvable bounded investigation without inspecting new bodies.",
            "dependencies": ["new e checkpoint and conditional733 frontier", "retained parent601.3 and proposal a-d context", "retained import and runtime limitations"],
            "explicit_exclusions": ["601.2a", "601.2i", "601.3 body", "733 or children", "701.20a", "603", "606", "source_projection", "runtime", "rollback", "Card_or_Oracle_ingestion"],
            "useful_reasoning_gain": "Separate criteria evidence gaps from the existence of a checkpoint before selecting any further projection.",
            "requires_separate_owner_authorization": True, "future_milestone_authorized": False,
            "future_source_projection_authorized": False, "future_milestone_begun": False},
    }
    return {name: record(name, value) for name, value in {
        "design-source-correspondence.json": correspondence, "casting-parent-reassessment.json": parent,
        "activated-import-reassessment.json": imported, "recovery-dependency.json": recovery,
        "consumer-semantic-boundaries.json": consumers, "composite-coverage.json": composite,
        "preservation-readiness.json": readiness, "subsequent-recommendation.json": recommendation}.items()}
