"""Project-authored review contracts; none of these records is executable."""
from __future__ import annotations

from copy import deepcopy


CANDIDATES = ["602.2", "602.2a", "602.2b"]
IMPORTED = [f"601.2{suffix}" for suffix in "bcdefghi"]
PROJECTED_IMPORTED = ["601.2b", "601.2f", "601.2g", "601.2h"]
MANA_FAMILY = ["605.1", "605.1a", "605.1b", "605.2", "605.3", "605.3a",
               "605.3b", "605.3c", "605.4", "605.4a", "605.5", "605.5a", "605.5b"]


def authored_records(binding, inspection):
    """Return independent JSON trees from exact retained bindings and review metadata.

    Imported unprojected stage bodies are deliberately unknown. Range membership
    can be verified without inspecting those bodies or adding their coverage.
    """
    rules = binding["rule_bindings"]
    reviews = binding["review_bindings"]

    def evidence(reference):
        return deepcopy(rules[reference]) if reference in rules else None

    def prior(directory, filename):
        return reviews[f"{directory}/{filename}"]

    direct_design = "gameplay-rules-mana-direct-dependency-design"
    casting = "gameplay-rules-bounded-casting-projection"
    mana = "gameplay-rules-bounded-mana-ability-projection"
    stack = "gameplay-rules-bounded-mana-stack-exception-projection"
    historical = prior(direct_design, "activated-procedure-design.json")

    correspondence = {
        "authority_classes": [
            {"class": "PREVIOUSLY_RETAINED_PROJECTED_SOURCE_EVIDENCE",
             "authority": "UNCHANGED_RETAINED_SOURCE_CORRESPONDENCE",
             "examples": [evidence(ref) for ref in ["605.3", "605.3b", "405.6c", "601.2g"]]},
            {"class": "HISTORICAL_PM_DESIGN_OBSERVATIONS",
             "authority": "PM_SUPPLIED_DESIGN_INPUT_NOT_SOURCE_VERIFIED",
             "record_id": historical, "original_authority_upgraded": False},
            {"class": "NEW_EXACT_SOURCE_INSPECTION",
             "authority": "SOURCE_VERIFIED_REVIEW_ONLY_NOT_PROJECTED",
             "inspection": deepcopy(inspection)},
            {"class": "ARCHITECTURAL_DESIGN_JUDGMENT",
             "authority": "REVIEW_CONTRACT_NOT_SOURCE_RULE",
             "examples": ["local_scope_coherence", "capability_decomposition", "future_recommendation"]},
            {"class": "UNKNOWN_INCOMPLETE_UNSUPPORTED_UNRESOLVED",
             "authority": "NO_POSITIVE_SUPPORT_CLAIM",
             "examples": ["unprojected_import_bodies", "general_timing", "real_ability_recognition", "execution"]},
        ],
        "historical_record_id": historical,
        "historical_package_id": binding["prior_package_ids"][direct_design],
        "historical_evidence_mutated": False,
        "correspondence_findings": [
            {"observation": "parent_and_two_immediate_children", "result": "VERIFIED",
             "new_authority": "EXACT_SOURCE_REVIEW_ONLY"},
            {"observation": "parent_authority_legality_rollback_and_order", "result": "VERIFIED_WITH_REFINEMENT",
             "refinement": "Controller authority includes an owner fallback for an object without a controller and an object-specific exception; it is not a complete permission or timing system."},
            {"observation": "announcement_stack_object_and_controller", "result": "VERIFIED_WITH_REFINEMENT",
             "refinement": "Hidden-zone reveal citation, noncard object identity and stack residence are local context; mana exceptions and controller attribution remain separately bound."},
            {"observation": "casting_range_and_cost_mapping", "result": "VERIFIED_WITH_REFINEMENT",
             "refinement": "Remaining activation steps use the same procedure as 601.2b–i; 601.2f mana-cost references use the activation-cost analogue. This does not identify the actions or implement the imported stages."},
            {"observation": "602.2_to_733", "result": "VERIFIED", "target_coverage": "UNPROJECTED"},
            {"observation": "602.2a_to_701.20a", "result": "VERIFIED", "target_coverage": "UNPROJECTED"},
            {"observation": "complete_activation_supplied_by_local_cluster", "result": "DID_NOT_VERIFY",
             "refinement": "A coherent source boundary is distinct from complete procedural semantics or execution."},
        ],
        "source_inspection_resolves_projected_dependencies": False,
        "locator_authority": "REVIEW_ONLY_NOT_PROJECTED",
        "new_projection_objects": 0, "new_projected_rule_identities": 0,
        "new_registered_projected_source_anchors": 0,
    }

    local_scope = {
        "candidate_references": CANDIDATES[:], "candidate_count": 3,
        "current_projection_allowlist": [],
        "candidate_coverage": "UNPROJECTED",
        "coherence": "COHERENT_LOCAL_SOURCE_BOUNDARY_WITH_OPEN_EXTERNAL_REQUIREMENTS",
        "coherence_authority": "DESIGN_JUDGMENT_AFTER_EXACT_LOCAL_INSPECTION",
        "roles": [
            {"reference": "602.2", "role": "PARENT_PROCEDURE_FRAME",
             "supports": ["activation_stack_and_cost_overview", "object_controller_authority_with_owner_fallback_and_exception",
                          "ordered_steps", "illegal_activation_rollback_reference", "fixed_announcements_and_payments"],
             "does_not_supply": ["ability_kind_recognition", "complete_timing", "rollback_algorithm", "resolution"]},
            {"reference": "602.2a", "role": "ANNOUNCEMENT_AND_ORDINARY_STACK_CONTEXT",
             "supports": ["announcement", "hidden_zone_reveal_reference", "noncard_topmost_stack_object",
                          "ability_text_without_other_characteristics", "activator_as_ability_controller",
                          "residence_until_countered_resolved_or_moved"],
             "does_not_supply": ["stack_runtime", "general_controller_attribution", "mana_exception_classification"]},
            {"reference": "602.2b", "role": "REMAINING_PROCEDURE_REUSE_AND_COST_ANALOGUE",
             "supports": ["601.2b_through_601.2i_import", "601.2f_mana_cost_to_activation_cost_analogue"],
             "does_not_supply": ["missing_imported_stage_bodies", "payment_runtime", "cost_parser", "card_semantics"]},
        ],
        "structural_relationships": [
            {"parent": "602.2", "children": ["602.2a", "602.2b"],
             "kind": "STRUCTURAL_PARENT_CHILD_NOT_NUMBERED_CITATION"}],
        "insufficient_scope_policy": {
            "coherence_is_not_assumed_from_prior_design": True,
            "current_assessment": "NO_LOCAL_BOUNDARY_GAP_FOUND_FOR_REVIEW_ONLY_SOURCE_SCOPE",
            "complete_procedure_scope_sufficient": False,
            "gaps": ["unprojected_imported_stages", "733", "701.20a", "ability_and_card_semantics",
                     "timing_permissions_and_prohibitions", "stack_priority_payment_and_resolution"],
            "if_future_source_or_context_differs": "STOP_FOR_OWNER_SCOPE_REVIEW_WITH_PRECISE_GAP",
            "automatic_scope_expansion": False,
        },
        "outgoing_literal_references": [
            {"origin": "602.2", "target": "733", "kind": "DIRECT_NUMBERED_REFERENCE",
             "coverage": "UNPROJECTED", "capability": "illegal_action_rollback", "status": "UNRESOLVED"},
            {"origin": "602.2a", "target": "701.20a", "kind": "DIRECT_NUMBERED_REFERENCE",
             "coverage": "UNPROJECTED", "capability": "hidden_zone_reveal", "status": "UNRESOLVED"},
            {"origin": "602.2b", "target": "601.2f", "kind": "DIRECT_NUMBERED_REFERENCE_FOR_COST_MAPPING",
             "coverage": "PREVIOUSLY_PROJECTED", "retained_evidence": evidence("601.2f"),
             "projected_origin_reference_state": "ORIGIN_UNPROJECTED_NO_NEW_COVERAGE_EDGE"},
        ],
        "range_import": {"origin": "602.2b", "members": IMPORTED[:],
                         "kind": "LITERAL_RANGE_IMPORT_WITH_SEPARATE_COST_MAPPING_CITATION"},
        "uninspected_outgoing_bodies": ["733", "701.20a", "601.2c", "601.2d", "601.2e", "601.2i"],
        "current_605.3_to_602.2": "UNRESOLVED_PROJECTED_SOURCE_DEPENDENCY",
    }

    responsibilities = [
        ("ability_kind_recognition", "Identify the applicable activated ability before selecting a procedure.",
         ["ability identity", "real Card and ability-kind evidence", "classification evidence"],
         ["605.1a", "605.1b", "115.6", "606.1", "606.2"],
         ["real ability recognition", "target requirement semantics", "loyalty exclusion", "Card/effect semantics"],
         "The three inspected units assume an activated ability; they do not define a general recognizer."),
        ("activation_authority_and_controller", "Distinguish permission to activate an object ability from control of the resulting ability.",
         ["object", "controller or owner fallback", "object-specific exceptions", "activating player"], ["602.2", "602.2a"],
         ["general authority and control", "109.4a controller attribution", "state", "permissions and prohibitions"],
         "Local authority and activator-controller context do not close controller attribution or all permissions."),
        ("announcement_and_ability_identity", "Bind a declaration to a particular ability and retain the reveal requirement when relevant.",
         ["ability text and identity", "activator", "source zone", "reveal evidence if applicable"], ["602.2a"],
         ["701.20a", "real ability/Card semantics", "hidden information handling"],
         "No declaration evaluator, hidden-zone action or executable identity is supplied."),
        ("ability_stack_object_context", "Describe the ordinary activation object and its stack context while preserving qualifying mana exceptions.",
         ["announced ability", "controller", "stack state", "mana-exception qualification"], ["602.2", "602.2a", "605.3b", "405.6c"],
         ["general stack semantics", "countering and movement", "mana-ability recognition"],
         "No object construction, push/pop, responses or unconditional stack placement is supported."),
        ("activation_cost_determination", "Describe activation-cost substitution at the imported total-cost stage.",
         ["ability activation cost", "choices", "applicable modifiers", "cost evidence"], ["602.2b", "601.2b", "601.2f"],
         ["cost-symbol parsing", "cost effects", "real Card semantics", "unprojected casting requirements"],
         "The cost analogue is verified; real calculation, lock-in and mutation remain unsupported."),
        ("casting_procedure_reuse", "Map the remaining activation procedure to the exact imported casting stages.",
         ["601.2b–i member evidence", "activation context", "cost mapping"], ["602.2b", "601.2b", "601.2f", "601.2g", "601.2h"],
         ["601.2c", "601.2d", "601.2e", "601.2i", "casting semantics and runtime"],
         "Import membership is known; four imported bodies and complete semantics remain missing. 601.2a is excluded."),
        ("mana_and_nonmana_payment", "Specify evidence needed for every cost component and a complete payment result.",
         ["determined cost", "mana/nonmana inventory", "ordering and payable components", "payment result evidence"], ["602.2b", "601.2g", "601.2h"],
         ["mana production and pool", "mana payment", "nonmana effects", "cost parsing", "real object state"],
         "Retained payment source and design labels perform no payment, mana-pool update or nonmana action."),
        ("activation_legality_and_timing", "Require legality throughout the proposal and the applicable timing/permission evidence.",
         ["full proposal", "ordered choices", "state", "timing", "permissions", "prohibitions"], ["602.2", "602.2b"],
         ["unprojected imported stages", "general timing and priority", "legality evaluator", "ability-specific restrictions"],
         "The parent supplies failure context, not a complete legality or timing algorithm. 601.2e's historical role is design-only."),
        ("illegal_action_handling_and_rollback", "Describe failure evidence, fixed declarations and the need to restore an illegal activation.",
         ["failure point", "announcements/payments", "state history", "rollback evidence"], ["602.2"],
         ["733", "transaction history", "reversibility rules", "rollback algorithm"],
         "A verified rollback citation does not supply its uninspected target semantics or executable recovery."),
        ("resolution_downstream", "Keep resolution separate from completing the activation procedure.",
         ["ability and effect semantics", "general resolution evidence", "qualifying mana-exception evidence"], ["605.3b", "405.6c", "605.4a"],
         ["effect execution", "general ability resolution", "stack resolution", "mana production"],
         "The inspected local cluster does not implement general resolution; mana immediate-resolution context has its own provenance."),
    ]
    matrix = []
    for name, purpose, inputs, refs, missing, unknown in responsibilities:
        matrix.append({"responsibility": name, "purpose": purpose, "required_evidence_or_inputs": inputs,
                       "inspected_candidate_support": [r for r in refs if r in CANDIDATES],
                       "existing_projected_evidence": [evidence(r) for r in refs if r in rules],
                       "existing_coverage": "PARTIAL_SOURCE_OR_DESIGN_CONTEXT_ONLY",
                       "missing_dependencies": missing, "unknown_or_unsupported": unknown,
                       "semantic_closure": "OPEN", "execution_readiness": "BLOCKED",
                       "implementation_available": False})

    roles = {
        "601.2b": ("Retained casting-choice context must be interpreted for an activation declaration.",
                   ["choice applicability", "real ability semantics", "700.2", "702.47", "118.8", "118.9", "107.3"]),
        "601.2f": ("Retained total-cost context uses activation cost in place of its spell mana-cost concept.",
                   ["real activation-cost basis", "modifiers", "cost calculation"]),
        "601.2g": ("Retained conditional mana-ability opportunity is reused in activation context.",
                   ["classification", "activation", "mana production", "pool and payment integration"]),
        "601.2h": ("Retained total-cost payment context is reused in activation context.",
                   ["all mana/nonmana payment semantics", "payment ordering implementation", "state changes"]),
    }
    import_rows = []
    for ref in IMPORTED:
        covered = ref in PROJECTED_IMPORTED
        purpose, missing = roles.get(ref, (
            "Range membership verified; stage-body purpose and activation adaptation are unknown in this inspection.",
            [f"{ref} source coverage", "stage-body semantics", "activation adaptation", "execution primitives"]))
        import_rows.append({"reference": ref, "relationship": "VERIFIED_MEMBER_OF_602.2b_REMAINING_PROCESS_IMPORT",
                            "coverage": "PROJECTED" if covered else "UNPROJECTED",
                            "retained_evidence": evidence(ref),
                            "body_authority": "PREVIOUSLY_PROJECTED_SOURCE" if covered else "UNKNOWN_NOT_INSPECTED",
                            "activation_relationship": purpose, "unresolved_requirements": missing,
                            "execution_readiness": "BLOCKED"})
    casting_import = {
        "origin": "602.2b", "authority": "NEW_EXACT_SOURCE_INSPECTION_REVIEW_ONLY",
        "qualification": "REMAINING_ACTIVATION_STEPS_USE_THE_SAME_CASTING_PROCEDURE",
        "additional_applicability_qualifier_found": False,
        "range_members": import_rows,
        "excluded_stages": ["601.2a"],
        "cost_mapping": {"stage": "601.2f", "from_concept": "SPELL_MANA_COST",
                         "to_concept": "ABILITY_ACTIVATION_COST", "relationship": "EXPLICIT_ANALOGUE",
                         "costs_calculated": False, "payments_performed": False,
                         "cost_symbol_parser_supplied": False, "card_semantics_supplied": False},
        "projected_members": PROJECTED_IMPORTED[:],
        "unprojected_members": ["601.2c", "601.2d", "601.2e", "601.2i"],
        "stage_review_id": prior(casting, "casting-stage-matrix.json"),
        "historical_legality_stage_observation": {"reference": "601.2e",
            "authority": "OWNER_SUPPLIED_STRUCTURAL_DESIGN_BOUNDARY_NOT_PROJECTED_SOURCE",
            "fresh_body_verification": False},
        "range_verification_projects_missing_members": False,
        "existing_casting_source_is_executable_procedure": False,
        "partial_casting_satisfies_complete_activation": False,
        "casting_and_activation_interchangeable": False,
        "imported_runtime_dispatch": False,
    }

    mana_relationships = {
        "general_procedure": {"references": CANDIDATES[:], "coverage": "UNPROJECTED",
                              "role": "ORDINARY_ACTIVATION_CONTEXT", "execution_readiness": "BLOCKED"},
        "qualifying_activated_mana_exception": {
            "condition": "QUALIFYING_ACTIVATED_MANA_ABILITY_REQUIRES_SEPARATE_CLASSIFICATION",
            "no_stack_evidence": evidence("605.3b"),
            "immediate_resolution_evidence": [evidence("605.3b"), evidence("405.6c")],
            "ordinary_stack_placement_unconditional": False,
            "exception_supplies_complete_activation": False},
        "preserved_relationships": [
            {"origin": "605.3", "target": "602.2", "kind": "DIRECT_NUMBERED_REFERENCE",
             "status": "UNRESOLVED_PROJECTED_SOURCE_DEPENDENCY", "origin_evidence": evidence("605.3")},
            {"origin": "605.3b", "target": "405.6c", "kind": "DIRECT_NUMBERED_REFERENCE",
             "status": "DIRECT_REFERENCE_RESOLVED", "review_id": prior(stack, "consumer-reassessment.json")},
            {"origin": "405.6c", "target": "605", "kind": "SECTION_REFERENCE",
             "status": "SECTION_REFERENCE_RESOLVED_BY_COMPLETE_FAMILY",
             "concrete_members": [evidence(ref) for ref in MANA_FAMILY],
             "review_id": prior(stack, "section-dependency-review.json")},
            {"origin": "605.4a", "target": "405.6c", "kind": "SEMANTIC_OVERLAP_WITHOUT_DIRECT_CR_CITATION",
             "direct_edge_created": False, "origin_evidence": evidence("605.4a")},
        ],
        "additional_effect_context": {"source": evidence("405.6c"),
            "finding": "MANA_PLUS_ADDITIONAL_EFFECT_BOTH_HAVE_IMMEDIATE_RESOLUTION_CONTEXT",
            "finer_ordering_inferred": False, "effect_execution_supported": False},
        "priority_return": {"source": evidence("405.6c"),
            "review_id": prior(stack, "priority-readiness.json"),
            "applicability": "ACTIVATED_MANA_ABILITY_ONLY",
            "condition": "PLAYER_HELD_PRIORITY_IMMEDIATELY_BEFORE_MANA_ABILITY_ACTIVATION",
            "post_resolution_context": "SAME_PLAYER_RECEIVES_PRIORITY",
            "every_mana_activation_grants_priority": False, "triggered_priority_return_inferred": False,
            "general_priority_semantics": "OPEN", "runtime_implemented": False},
        "triggered_mana_evidence": evidence("605.4a"),
        "parent_405.6": "UNPROJECTED_SCOPE_NOT_REOPENED",
        "independently_unresolved": ["classification", "ability_recognition", "target_requirements", "timing",
            "costs", "payment", "mana_production", "effect_semantics", "stack_semantics", "priority_semantics"],
    }

    consumers = [
        ("605.3", ["602.2"], "DIRECT_NUMBERED_REFERENCE", ["605.3", "602.2"],
         "UNRESOLVED_PROJECTED_SOURCE_DEPENDENCY", ["general_activation_procedure", "costs", "legality", "payment"]),
        ("605.3b", ["405.6c"], "DIRECT_NUMBERED_REFERENCE", ["605.3b", "405.6c"],
         "DIRECT_REFERENCE_RESOLVED", ["qualifying_mana_classification", "general_activation", "mana_and_effect_semantics"]),
        ("601.2g", ["605"], "SECTION_REFERENCE", ["601.2g", "605"],
         "SECTION_REFERENCE_RESOLVED_BY_COMPLETE_FAMILY", ["activation", "mana_production", "pool", "payment"]),
        ("bounded_casting", [], "INDIRECT_CONSUMER_ROUTE", ["bounded_casting", "601.2g", "605"],
         "PARTIAL_SOURCE_COVERAGE", ["601.2a", "601.2c", "601.2d", "601.2e", "601.2i", "complete_casting_semantics"]),
        ("madness", ["601.2b", "601.2f", "601.2g", "601.2h"], "INDIRECT_CONSUMER_ROUTE",
         ["702.35b", "bounded_casting", "601.2g", "605"], "INDIRECT_ONLY",
         ["complete_casting", "activation", "trigger_behavior", "zone_and_effect_semantics"]),
        ("109.4a", ["605"], "SEPARATE_CONTROLLER_ATTRIBUTION_BOUNDARY", ["109.4a", "605"],
         "SECTION_REFERENCE_RESOLVED_CONTROLLER_SEMANTICS_OPEN",
         ["hypothetical_stack_controller_attribution", "controller_state", "mana_recognition"]),
    ]
    consumer_rows = []
    for name, literal, kind, route, status, missing in consumers:
        ref = {"madness": "702.35b", "bounded_casting": "601.2"}.get(name, name)
        consumer_rows.append({"consumer": name, "retained_evidence": evidence(ref),
            "existing_literal_references_relevant_here": literal, "relationship_kind": kind,
            "route": route, "source_correspondence": status, "semantic_closure": "OPEN",
            "design_readiness": "BOUNDED_REVIEW_CONTRACT_WITH_UNRESOLVED_REQUIREMENTS",
            "execution_readiness": "BLOCKED", "missing_dependencies": missing,
            "new_direct_edges": [], "historical_dependency_arrays_modified": False})
    consumer_bindings = {
        "rows": consumer_rows,
        "existing_review_ids": [prior(mana, "family-closure-review.json"),
                                prior(stack, "consumer-reassessment.json"),
                                prior(casting, "madness-readiness-reassessment.json")],
        "controller_109.4a_requires_actual_stack_presence": False,
        "unprojected_activation_inspection_closes_consumers": False,
        "shared_triggered_subsystem_outside_scope": {
            "preserved_frontiers": [
                {"origin": "605.4", "targets": ["603"], "evidence": evidence("605.4")},
                {"origin": "109.4b", "targets": ["603", "603.7d", "603.7e", "603.7f"],
                 "evidence": evidence("109.4b")}],
            "capabilities_not_designed_or_implemented": ["trigger_detection", "registration", "ordering",
                "delayed_triggers", "zone_change_triggers", "reflexive_triggers", "general_ability_engine"]},
    }
    readiness = {
        "result": "ACTIVATED_ABILITY_PROCEDURE_DESIGN_COMPLETE",
        "source_correspondence": "REVIEW_ONLY_LOCAL_INSPECTION_COMPLETE",
        "local_source_scope": "COHERENT_FOR_FUTURE_BOUNDED_PROJECTION_REVIEW",
        "complete_activation_semantics": "OPEN", "execution_readiness": "BLOCKED",
        "real_profile": "DESIGN_ONLY / NOT EXECUTABLE",
        "readiness_code": "REAL_EXECUTION_PROFILE_NOT_READY",
        "new_projected_real_source_units": 0, "projected_real_source_units": 85,
        "distinct_existing_projections": 9, "current_projection_allowlist": [],
        "605.3_to_602.2": "UNRESOLVED_PROJECTED_SOURCE_DEPENDENCY",
        "recommendations": [{
            "milestone": "Bounded Activated Ability Procedure Projection",
            "proposed_future_allowlist": CANDIDATES[:], "expected_new_unit_count": 3,
            "expected_total_if_separately_authorized_and_verified": 88,
            "expected_distinct_projections_if_successful": 10,
            "consumer_value": ["Direct source-coverage reassessment of 605.3 → 602.2",
                               "Bounded ordinary activation context beside retained mana exceptions",
                               "Indirect context for 601.2g, bounded casting and Madness"],
            "remaining_dependencies": ["601.2c", "601.2d", "601.2e", "601.2i", "733", "701.20a",
                "real_ability_and_card_semantics", "timing_permissions_and_prohibitions", "stack_and_priority",
                "costs_and_payment", "resolution", "shared_603_subsystem", "109.4a_controller_attribution"],
            "source_requirement": "EXACT_OWNER_SUPPLIED_ARTIFACT_WITH_FRESH_VERIFICATION",
            "stop_conditions": ["artifact_missing_or_mismatched", "ambiguous_or_changed_unit_boundaries",
                "insufficient_local_context", "unexpected_scope_requirement", "preservation_or_validation_failure",
                "any_runtime_or_permission_expansion"],
            "future_milestone_authorized": False, "future_source_projection_authorized": False,
            "future_milestone_begun": False, "owner_approval": "AWAITING_OWNER_APPROVAL",
        }],
        "review_tooling_only": True, "projection_to_engine_path": False,
        "fictional_runtime_unchanged": True, "real_snapshot_created": False,
        "protected_state": ["architecture_v13", "decision_017", "all_inherited_src", "all_prior_gameplay_evidence",
            "85_rule_identities_and_anchors", "nine_projection_identities", "historical_append_only_reviews",
            "Product_Rules", "Tier_A", "Card_Intelligence", "MB2", "canonical_catalog", "collection_data",
            "admission", "publication_workflows", "timeouts"],
        "permissions": {"source_policy_clearance": "not_granted", "private_retention": "NOT_ESTABLISHED",
            "redistribution": "NOT_ESTABLISHED", "free_service": "NOT_ESTABLISHED",
            "commercial_service": "NOT_ESTABLISHED", "ai_export": "NOT_ESTABLISHED"},
    }
    bodies = {
        "source-correspondence.json": correspondence,
        "local-scope.json": local_scope,
        "procedure-responsibilities.json": {"rows": matrix, "contract_kind": "REVIEW_REQUIREMENTS_ONLY"},
        "casting-import.json": casting_import,
        "mana-relationships.json": mana_relationships,
        "consumer-bindings.json": consumer_bindings,
        "readiness.json": readiness,
    }
    return {name: {"schema_version": 1, "findings": findings} for name, findings in bodies.items()}
