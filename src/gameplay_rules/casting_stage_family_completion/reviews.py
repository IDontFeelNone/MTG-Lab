"""Authored source-coverage assessments for the complete numbered stage family.

All procedure descriptions are knowledge, not operations or legality decisions.
Previously projected source is consumed through its retained identity bindings.
"""
from copy import deepcopy
import json

from gameplay_rules.errors import GameplayContractError
from gameplay_rules.projection.mana_stack_exception_package import _canonical_candidate
from gameplay_rules.shared_proposal_legality.reviews import PERMISSIONS

CANONICAL_MAIN = "422ef1f295ba06889b805c8c429c9cbade813c9e"
BASE_TREE = "e176441c99e9c331a2b1589662cff9495e9916d6"
HISTORICAL_RECOMMENDATION = "sha256:eb8fda335b400c05e6a50d18564ac62d77bd6680a1bf8fd471cdf20db9d93fae"
STAGES = tuple("601.2" + letter for letter in "abcdefghi")


def authored_records(binding, projection):
    """Build closed assessments from validated retained and new source identities."""
    binding = json.loads(_canonical_candidate(binding))
    projection = json.loads(_canonical_candidate(projection))
    if type(binding) is not dict or type(projection) is not dict:
        raise GameplayContractError("casting_stage_family_completion_reviews", "PLAIN_JSON_RECORDS_REQUIRED")
    rules = {row["rule_reference"]: row for row in projection["rules"]}
    if set(rules) != {"601.2a", "601.2i"}:
        raise GameplayContractError("casting_stage_family_completion_reviews", "EXACT_TWO_UNIT_BATCH_REQUIRED")

    def old(reference):
        return {"rule_reference": reference, **deepcopy(binding["rule_bindings"][reference])}

    def evidence(reference):
        if reference not in rules:
            return old(reference)
        rule = rules[reference]
        return {"rule_reference": reference, "rule_id": rule["rule_id"],
            "projection_id": projection["projection_id"], "package_binding": "THIS_ENCLOSING_PACKAGE",
            "anchor_identity": rule["source_anchor"]["anchor_id"],
            "source_anchor": deepcopy(rule["source_anchor"])}

    def record(name, findings):
        return {"schema_version": 1, "record_type": name.removesuffix(".json"),
            "canonical_base": CANONICAL_MAIN, "status": "CASTING_STAGE_FAMILY_COMPLETION_PROJECTED",
            "non_executable": True, "source_body_retained": False,
            "semantic_closure": "OPEN", "execution_readiness": "BLOCKED", "findings": findings}

    def members(references, relationship):
        return [{"reference": ref, "relationship": relationship, "coverage": "PROJECTED",
            "projected_evidence": evidence(ref), "semantic_closure": "OPEN",
            "execution_readiness": "BLOCKED"} for ref in references]

    preflight = {
        "conclusion": "PASSED", "stop_code_if_insufficient": "CASTING_STAGE_BATCH_SCOPE_INSUFFICIENT",
        "admission": ["601.2a", "601.2i"], "fresh_body_inspection_allowlist": ["601.2a", "601.2i"],
        "exact_artifact_verified_before_body_inspection": True,
        "retained_verification_lineage_reproduced_before_body_inspection": True,
        "complete_owned_units_verified": True, "internal_line_endings_preserved": True,
        "final_terminators_and_separators_excluded": True,
        "literal_citations": {"601.2a": ["611.2f", "610.5"], "601.2i": []},
        "literal_ranges": [{"origin": "601.2i", "start": "601.2a", "end": "601.2h",
            "members": list(STAGES[:-1])}],
        "unresolved_outgoing_source": ["611.2f", "610.5"],
        "outgoing_targets_body_inspected": False, "recursive_projection_required": False,
        "coherence_judgment": "The start and completion units support a bounded explanation of the numbered sequence with retained parent and b-h evidence. Referenced effect systems remain explicit unresolved frontiers; no extra source unit is indispensable to these conditional descriptions.",
        "useful_knowledge": ["distinguish proposal/start from completion", "explain ordered stage context",
            "complete source coverage of the single activation import", "separate coverage from legality and execution"],
        "relationship_distinctions": ["literal outgoing citations", "literal ranges and normalized members",
            "structural sibling order", "semantic overlap", "indirect consumer relevance"],
        "additional_source_units_required": [], "additional_source_units_admitted": [],
    }
    scope = {
        "decision_date": "2026-10-22", "authority": "EXPLICIT_OWNER_CURRENT_MILESTONE_INSTRUCTION",
        "selected_milestone": "CASTING-STAGE FAMILY COMPLETION BATCH",
        "selected_source_allowlist": ["601.2a", "601.2i"], "one_combined_projection_and_package": True,
        "historical_recommendation": {"package": "gameplay-rules-bounded-shared-proposal-legality",
            "record": "subsequent-recommendation.json", "review_id": HISTORICAL_RECOMMENDATION,
            "milestone": "Proposal-legality criteria dependency scope design", "record_unchanged": True,
            "historical_allowlist": [], "historical_future_milestone_authorized": False,
            "historical_future_milestone_begun": False,
            "relationship": "NEW_CURRENT_SCOPE_REPLACES_UNBEGUN_RECOMMENDATION_WITHOUT_REWRITING_HISTORY"},
        "retained_questions_addressed_in": "legality-gap-assessment.json",
        "additional_source_authorized": False, "subsequent_milestone_authorized": False,
        "subsequent_milestone_begun": False,
    }
    correspondence = {
        "fresh_authority": "OWNER_AUTHORIZED_EXACT_TWO_COMPLETE_SOURCE_UNITS",
        "new_rule_bindings": [evidence(ref) for ref in ("601.2a", "601.2i")],
        "source_binding": deepcopy(projection["source_binding"]),
        "complete_units": [{"reference": ref, "anchor": deepcopy(rules[ref]["source_anchor"])}
            for ref in ("601.2a", "601.2i")],
        "i_retained_review_only_observation": {
            "package": "gameplay-rules-shared-casting-stage-gap-design", "record": "source-inspection.json",
            "package_id": "sha256:4ec995686f7ebb851fae1d6a3b732b1669a9f8cbe7d7ad547f939d928b6c729f",
            "package_identity_domain": "gameplay-shared-casting-stage-gap-design-package-v1",
            "review_id": "sha256:b238417023f10c4ebfd83340b6a105b95829c599126d5ab7bf52d941b8f23bc9",
            "record_identity_domain": "gameplay-shared-casting-stage-gap-design-record-v1",
            "record_own_identity_field": "review_id", "record_schema_version": 1,
            "historical_span": {"reference": "601.2i", "byte_start": 300741, "byte_end": 301082,
                "span_length": 341, "starting_physical_line": 2481, "ending_physical_line": 2481,
                "line_count": 1, "owned_example_line_count": 0,
                "span_sha256": "sha256:483c59e2092745af49cee6e5aa79339b165456084f22b33164dd4a24f6caa596",
                "following_marker": "601.3", "following_marker_physical_line": 2483,
                "following_body_inspected": False, "registered_projected_source_anchor": False},
            "historical_literal_references": {"direct_citations": [],
                "ranges": [{"start": "601.2a", "end": "601.2h", "members": list(STAGES[:-1]),
                    "status": "REVIEW_ONLY_RANGE_OBSERVED_NOT_PROJECTED_DEPENDENCY",
                    "historical_projected_members": ["601.2b", "601.2f", "601.2g", "601.2h"],
                    "historical_unprojected_members": ["601.2a", "601.2c", "601.2d", "601.2e"]}]},
            "historical_registered_projected_source_anchor": False, "fresh_verification_required_and_performed": True,
            "historical_observation_changed": False, "fingerprint_matches_fresh_anchor": True},
        "a_previously_verified_body_finding_assumed": False,
        "source_bodies_or_examples_retained": False, "attachment_path_retained": False,
        "offline_metadata_validation_is_fresh_source_verification": False,
    }
    parent = {
        "origin": "601.2", "origin_evidence": old("601.2"),
        "assessment_level": "SOURCE_COVERAGE_ONLY",
        "proposal_range": {"relationship": "RETAINED_LITERAL_PROPOSAL_RANGE",
            "start": "601.2a", "end": "601.2d", "original_range_provenance_preserved": True,
            "member_rows": members(STAGES[:4], "NORMALIZED_MEMBER_OF_RETAINED_PARENT_PROPOSAL_RANGE"),
            "coverage_before": "3/4", "coverage_after": "4/4"},
        "cost_range": {"relationship": "RETAINED_LITERAL_COST_RANGE", "start": "601.2f", "end": "601.2h",
            "member_rows": members(STAGES[5:8], "NORMALIZED_MEMBER_OF_RETAINED_PARENT_COST_RANGE"),
            "coverage": "3/3", "range_and_evidence_unchanged": True},
        "structural_siblings": [{"reference": ref, "evidence": evidence(ref),
            "relationship": "STRUCTURAL_SIBLING_WITHOUT_RETAINED_PARENT_DIRECT_CITATION",
            "literal_parent_citation_invented": False} for ref in ("601.2e", "601.2i")],
        "preserved_unresolved_literal_references": ["601.3", "733"],
        "stage_coverage_establishes_actual_legality_criteria": False,
        "broad_601_complete": False, "semantic_or_execution_closure": False,
    }
    imported = {
        "origin": "602.2b", "origin_evidence": old("602.2b"),
        "relationship_kind": "ONE_RANGE_IMPORT_WITH_EIGHT_MEMBER_ROWS", "range_import_count": 1,
        "range_start": "601.2b", "range_end": "601.2i", "member_count": 8,
        "range_members": members(STAGES[1:], "MEMBER_OF_SINGLE_602.2b_CASTING_RANGE_IMPORT"),
        "member_coverage_before": "7/8", "member_coverage_after": "8/8",
        "all_range_members_projected": True, "excluded_stages": ["601.2a"],
        "literal_direct_reference_edges_inferred_from_membership": [],
        "casting_and_activation_interchangeable": False,
        "i_range_creates_literal_602_2b_to_a_citation": False,
        "spell_specific_facts_apply_unchanged_to_all_abilities": False,
        "separate_cost_analogy": {"origin": "602.2b", "target": "601.2f",
            "relationship": "SEPARATE_LITERAL_COST_ANALOGY", "state": "DIRECT_REFERENCE_RESOLVED",
            "origin_evidence": old("602.2b"), "target_evidence": old("601.2f")},
        "source_bodies_imported_into_projection": 0, "runtime_dispatch_created": False,
    }
    completed = {
        "origin": "601.2i", "origin_evidence": evidence("601.2i"),
        "relationship_kind": "ONE_LITERAL_PRECEDING_STAGE_RANGE_WITH_EIGHT_MEMBER_ROWS",
        "range_start": "601.2a", "range_end": "601.2h", "range_count": 1, "member_count": 8,
        "range_members": members(STAGES[:-1], "MEMBER_OF_SINGLE_601.2i_PRECEDING_STAGE_RANGE"),
        "source_coverage": "8/8", "range_is_a_literal_activation_to_a_citation": False,
        "semantics": {"condition": "AFTER_THE_PRECEDING_A_THROUGH_H_STAGES",
            "characteristic_change_context": "CAST_TIME_CHARACTERISTIC_MODIFICATIONS_PRECEDE_CAST_COMPLETION",
            "completion": "SPELL_BECOMES_CAST", "trigger_consequence": "CAST_OR_PUT_ON_STACK_ABILITIES_TRIGGER_AT_THIS_TIME",
            "priority_condition": "SPELL_CONTROLLER_HAD_PRIORITY_BEFORE_CASTING",
            "priority_consequence_under_condition": "THAT_CONTROLLER_GETS_PRIORITY",
            "unconditional_priority_return": False},
        "effect_application_implemented": False, "trigger_detection_ordering_or_placement_implemented": False,
        "stack_or_priority_handling_implemented": False,
    }
    ranges = {"casting_parent": parent, "activated_import": imported, "completion_range": completed,
        "numbered_stage_family": {"inventory": list(STAGES), "coverage_before": "7/9", "coverage_after": "9/9",
            "inventory_evidence": "RETAINED_STAGE_FAMILY_EVIDENCE_AND_FRESH_MARKER_PREFIXES_ONLY",
            "broad_601_completeness_claimed": False}}

    stage_descriptions = {
        "a": ("Begin the proposal by placing the card or copy at the top of the stack, with the described characteristics, controller and beginning-effect timing context.",
            "Beginning proposal precedes b's choices; stack residence is not proof that casting is complete.",
            ["card_or_copy_identity", "applicable_characteristics", "controller", "applicable_effects", "611.2f", "610.5"]),
        "b": ("Declare relevant modes, alternative or additional costs, variables and applicable payment choices.",
            "Earlier choices constrain declarations and f later uses the declared cost basis.",
            ["Card_or_effect_requirements", "legal_modes_and_cost_choices", "variable_values", "unresolved_choice_and_cost_families"]),
        "c": ("Declare required target counts and recipients under prior choices and compatible mandatory/prohibited target constraints.",
            "Recipient declaration precedes conditional allocation; described target-trigger placement waits for casting completion.",
            ["target_requirements", "candidate_recipients", "applicable_target_criteria", "state_and_effect_constraints"]),
        "d": ("When distribution among one or more targets is required, declare the allocation with at least one unit for every included target.",
            "Recipient declaration and allocation are separate responsibilities; the condition and relevant recipient set constrain the minimum.",
            ["whether_distribution_is_required", "actual_targets", "quantity", "Card_or_effect_semantics"]),
        "e": ("The game checks whether casting the proposed spell is legal; the illegal branch refers to recovery before proposal through 733.",
            "The checkpoint follows declarations and precedes costs structurally; its source supplies no express successful-continuation guarantee.",
            ["legality_criteria", "Card_or_effect_information", "applicable_game_state", "733_recovery_mechanics"]),
        "f": ("Compose the selected base with additional costs, increases and reductions, then apply direct total modifiers and lock the result.",
            "Uses b's declarations and determines the cost considered by g and paid at h.",
            ["base_cost", "additional_costs", "modifiers", "reduction_order", "effect_semantics"]),
        "g": ("A total cost requiring mana creates an opportunity to use mana abilities before payment.",
            "Its condition depends on the determined total; an opportunity is neither mana production nor successful payment.",
            ["whether_total_requires_mana", "mana_ability_classification", "available_abilities", "resources_and_permissions"]),
        "h": ("Pay all required cost components fully with ordinary components before random or library-to-public-zone components.",
            "Payment is a required preceding stage; its evidence alone does not establish the completion condition or legality.",
            ["payable_resources", "required_cost_components", "permitted_payment_actions", "state_changes"]),
        "i": ("After a-h, apply the described cast-time characteristic changes, complete casting and recognize the stated trigger consequences; priority return retains its prior-priority condition.",
            "The explicit preceding range distinguishes completion from proposal/start and payment alone.",
            ["completed_preceding_stages", "characteristic_changing_effects", "trigger_conditions", "prior_priority_state"]),
    }
    execution = {"a": ["zone_move", "stack_object_construction", "effect_application"],
        "b": ["choice_recognition_and_declaration"], "c": ["target_recognition_selection_and_compatibility", "trigger_detection_and_placement"],
        "d": ["allocation_recognition_and_arithmetic"], "e": ["legality_decision", "rollback_and_state_restoration"],
        "f": ["cost_evaluation_and_lock"], "g": ["mana_production_and_activation"],
        "h": ["cost_payment_and_state_transition"], "i": ["effect_application", "trigger_detection_ordering_and_placement", "stack_and_priority"]}
    procedure = {
        "description_kind": "SOURCE_BACKED_NON_EXECUTABLE_PROCEDURE_MAP", "ordered_references": list(STAGES),
        "rows": [{"reference": "601.2" + letter, "source_evidence": evidence("601.2" + letter),
            "bounded_fact": stage_descriptions[letter][0], "earlier_later_relationship": stage_descriptions[letter][1],
            "order_relationship_kind": "NUMBERED_STRUCTURAL_PROCEDURE_CONTEXT_NOT_INVENTED_LITERAL_CROSS_CITATION",
            "casting_applicability": "CASTING_SOURCE_PROVENANCE",
            "activation_applicability": "EXCLUDED_FROM_LITERAL_B_THROUGH_I_IMPORT" if letter == "a" else "MEMBER_OF_SINGLE_RETAINED_602.2b_RANGE_IMPORT",
            "unknown_required_inputs_or_criteria": stage_descriptions[letter][2],
            "missing_execution_machinery": execution[letter], "actual_legality": "UNKNOWN_OR_UNSUPPORTED",
            "execution_readiness": "BLOCKED"} for letter in "abcdefghi"],
        "explanatory_checks": [
            {"question": "What distinguishes proposal/start from casting completion?",
                "answer": "a provides beginning stack-proposal context; i explicitly depends on a-h and supplies the later cast-completion context. Stack presence or payment alone does not identify completion.",
                "evidence": [evidence(ref) for ref in ("601.2", "601.2a", "601.2h", "601.2i")], "relationship": "STRUCTURAL_SEQUENCE_AND_LITERAL_I_RANGE"},
            {"question": "How do declaration, allocation, checking, costs, mana, payment and completion relate?",
                "answer": "b choices condition c recipients and d allocation; e is a checkpoint without supplied criteria. f determines and locks the total, g gives a conditional mana opportunity, h requires full payment, and i describes completion after the preceding range. Ordering supplies no success guarantee.",
                "evidence": [evidence(ref) for ref in STAGES[1:]], "relationship": "RETAINED_STRUCTURAL_ORDER_WITH_EXPLICIT_CONDITIONS"},
            {"question": "What does activation import and why is a excluded?",
                "answer": "602.2b imports one b-i range with eight members and separately analogizes the activation cost to the spell mana-cost concept at f. a lies outside that literal range; i's own a-h citation creates no new activation-to-a literal edge.",
                "evidence": [old("602.2b"), evidence("601.2i")], "relationship": "ONE_RANGE_IMPORT_AND_SEPARATE_COST_ANALOGY"},
            {"question": "Why do complete stage coverage and payment evidence not establish legality or execution?",
                "answer": "Coverage supplies bounded descriptions, while e supplies no actual criteria and parent permission/legality and unresolved recovery remain. Card/effect information, applicable state, resources and execution machinery are absent.",
                "evidence": [old("601.2"), old("601.2e"), old("601.2h")], "relationship": "SOURCE_COVERAGE_DISTINCT_FROM_SEMANTIC_AND_EXECUTION_CLOSURE"},
        ],
        "real_Card_or_Oracle_data_used": False, "scenario_engine_created": False,
        "query_or_runtime_feature_created": False,
    }
    gap = {
        "assessment_authority": "RETAINED_EVIDENCE_AND_EXACT_NEW_A_I_ONLY",
        "historical_recommendation_review_id": HISTORICAL_RECOMMENDATION,
        "historical_recommendation_preserved": True, "additional_body_inspection": [],
        "checkpoint_evidence": old("601.2e"), "parent_permission_context": old("601.2"),
        "criteria_supplied_by_checkpoint": False, "procedure_order_proves_legality": False,
        "full_payment_proves_legality": False, "absence_of_detected_violation_proves_legality": False,
        "missing_inputs": [
            {"category": "ACTION_AND_OBJECT_INFORMATION", "unknowns": ["real_Card_or_copy_semantics", "ability_kind", "originating_ability", "chosen_modes_costs_variables"]},
            {"category": "APPLICABLE_STATE", "unknowns": ["objects_and_players", "zones_and_controllers", "resources", "prior_priority", "active_effects"]},
            {"category": "LEGALITY_CRITERIA", "unknowns": ["permission_to_begin", "timing", "target_requirements_and_criteria", "prohibitions_and_mandatory_effects", "payability"]},
            {"category": "CONDITIONAL_COMPLETION", "unknowns": ["all_required_stages_completed", "characteristic_modifications", "applicable_trigger_conditions"]},
        ],
        "unresolved_frontiers": [
            {"origin": origin, "target": target, "relationship": relationship, "state": "UNRESOLVED",
                "source_evidence": evidence(origin), "target_body_inspected": False}
            for origin, target, relationship in (("601.2", "601.3", "RETAINED_LITERAL_REFERENCE"),
                ("601.2", "733", "RETAINED_LITERAL_REFERENCE"), ("601.2e", "733", "RETAINED_LITERAL_REFERENCE"),
                ("602.2", "733", "RETAINED_LITERAL_REFERENCE"), ("602.2a", "701.20a", "RETAINED_LITERAL_REFERENCE"),
                ("601.2a", "611.2f", "FRESH_LITERAL_REFERENCE"), ("601.2a", "610.5", "FRESH_LITERAL_REFERENCE"))],
        "semantic_frontiers_without_invented_literal_citations": ["603_and_delayed_trigger_rules",
            "broad_606_and_missing_loyalty_rules", "effect_application", "stack_and_priority", "legality_and_recovery"],
        "actual_proposed_action_legality": "UNKNOWN_OR_UNSUPPORTED", "legality_solved": False,
        "execution_machinery": "UNIMPLEMENTED", "real_execution": "BLOCKED",
    }
    from gameplay_rules.shared_proposal_legality import package as legality
    consumers = deepcopy(legality._expected_records()["consumer-semantic-boundaries.json"]["findings"])
    # These are e's authored self-bindings, so resolve them to e before adding
    # this batch's new self-bound evidence. They must never resolve to our ID.
    def resolve_retained_e(value):
        if type(value) is dict:
            if "package_binding" in value:
                if value.pop("package_binding") != "THIS_ENCLOSING_PACKAGE":
                    raise GameplayContractError("casting_stage_family_completion_reviews", "RETAINED_SELF_BINDING_INVALID")
                value["package_id"] = binding["prior_package_ids"][legality.PACKAGE_NAME]
            for child in value.values():
                resolve_retained_e(child)
        elif type(value) is list:
            for child in value:
                resolve_retained_e(child)
    resolve_retained_e(consumers)
    consumers["context_relationships"] = [{"reference": ref, "kind": kind,
        "literal_citation_from_new_units": False,
        **({"evidence": evidence(ref)} if ref in binding["rule_bindings"] or ref in rules else {"coverage": "UNPROJECTED"})}
        for ref, kind in (("601.2c", "RETAINED_TARGET_DECLARATION"), ("601.2d", "RETAINED_ALLOCATION"),
            ("601.2e", "RETAINED_LEGALITY_CHECKPOINT"), ("602.2b", "RETAINED_SINGLE_RANGE_IMPORT"),
            ("115.6", "RETAINED_TARGET_CLASSIFICATION"), ("603", "SHARED_TRIGGER_FRONTIER"))]
    consumers["new_start_completion_evidence"] = [evidence("601.2a"), evidence("601.2i")]
    consumers["completion_priority_condition"] = "SPELL_CONTROLLER_HAD_PRIORITY_BEFORE_CASTING"
    consumers["completion_priority_unconditional"] = False
    consumers["a_effect_references"] = ["611.2f", "610.5"]
    consumers["madness"]["new_direct_a_or_i_citation"] = False
    consumers["casting_and_activation_vocabulary_unconditionally_interchangeable"] = False
    consumers["source_coverage_is_semantic_or_execution_closure"] = False
    consumers["historical_product_collation_rules_separate"] = True
    consumers["all_ten_responsibilities_remain_open_execution_blocked"] = True

    components = deepcopy(binding["projection_components"])
    components.append({"name": "casting_stage_family_completion", "projection_id": projection["projection_id"],
        "package_binding": "THIS_ENCLOSING_PACKAGE", "projected_references": ["601.2a", "601.2i"]})
    references = [ref for row in components for ref in row["projected_references"]]
    if len(components) != 14 or len({row["projection_id"] for row in components}) != 14 or len(references) != 93 or len(set(references)) != 93:
        raise GameplayContractError("casting_stage_family_completion_reviews", "EXACT_93_14_COVERAGE_REQUIRED")
    composite = {"view_kind": "READ_ONLY_FOURTEEN_PROJECTION_COMPOSITE", "projection_components": components,
        "projected_references": references, "previous_count": 91, "new_count": 2,
        "total_projected_rule_count": 93, "previous_projection_count": 13, "total_projection_count": 14,
        "all_prior_rule_bindings": deepcopy(binding["rule_bindings"]),
        "new_rule_bindings": [evidence(ref) for ref in ("601.2a", "601.2i")],
        "stage_coverage": "9/9", "parent_proposal_range_coverage": "4/4",
        "single_activated_import_coverage": "8/8", "i_preceding_range_source_coverage": "8/8",
        "prior_rule_bindings_changed": False, "monolithic_projection_created": False,
        "additional_rules_projected": [], "broad_601_complete": False}
    readiness = {"source_admission": ["601.2a", "601.2i"], "added_units": 2,
        "total_units": 93, "distinct_projections": 14, "all_ten_responsibilities": "OPEN / EXECUTION_BLOCKED",
        "real_execution": "BLOCKED", "semantic_closure": "OPEN", "execution_supported": False,
        "real_snapshot_created": False, "real_execution_profile_activated": False,
        "source_policy_clearance": "not_granted", "permissions": deepcopy(PERMISSIONS),
        "historical_acquisition_identity": binding["historical_acquisition_identity"],
        "historical_coverage_allowlists_authorization_flags_recommendations_preserved": True,
        "previous_packages_projection_rules_anchors_preserved": True,
        "PR_205_206_performance_implementations_and_ledgers_preserved": True,
        "canonical_base": CANONICAL_MAIN, "canonical_base_tree": BASE_TREE,
        "preservation_method": "EXISTING_PRESERVATION_GUARDS_PLUS_DIRECT_CANONICAL_GIT_BLOB_COMPARISON",
        "whole_repository_freeze_fixture_added": False,
        "Architecture_v13": "ACTIVE APPROVED", "Decision_017": "ACCEPTED",
        "owner_final_merge_approval_required": True, "independent_PM_review_required": True,
        "future_milestone_authorized": False, "future_milestone_begun": False,
        "offline_metadata_is_fresh_source_verification": False,
        "required_validation": ["focused_contract_identity_mutation_range_semantic_preservation_checks",
            "fresh_two_unit_source_reproduction", "complete_local_discovery", "final_head_hosted_push_and_PR_actual_publication_gates"]}
    subsequent = {"authority": "ASSESSMENT_ONLY_UNAUTHORIZED_UNBEGUN_RECOMMENDATION",
        "recommendation_count": 1, "fresh_additional_body_inspection": [],
        "recommendation": {"milestone": "Legality-input and semantic-frontier reasoning review",
            "useful_reasoning_outcome": "Explain which explicit assumed inputs could support a bounded proposal-legality question and which unresolved source criteria still prevent a real decision.",
            "kind": "RETAINED_EVIDENCE_ONLY_DESIGN", "proposed_allowlist": [], "expected_added_source_units": 0,
            "boundary": "Use retained stage, activation and permission evidence to classify required inputs and select one coherent future source question without inspecting bodies or adjudicating legality.",
            "explicit_exclusions": ["additional_source_body_inspection", "source_projection", "Card_or_Oracle_data",
                "runtime", "legality_decisions", "rollback", "execution"],
            "future_milestone_authorized": False, "future_milestone_begun": False,
            "future_source_projection_authorized": False, "requires_separate_owner_authorization": True}}
    return {name: record(name, body) for name, body in {
        "preflight.json": preflight, "scope-decision.json": scope,
        "source-correspondence.json": correspondence, "procedure-map.json": procedure,
        "range-reassessment.json": ranges, "legality-gap-assessment.json": gap,
        "consumer-semantic-boundaries.json": consumers, "composite-coverage.json": composite,
        "preservation-readiness.json": readiness, "subsequent-recommendation.json": subsequent}.items()}
