"""Bounded permission knowledge and append-only relationship reassessments.

Authored explanations use source identities, never Card data or executable cases.
The preceding procedure map and historical findings retain their own identities.
"""
from copy import deepcopy
import json

from gameplay_rules.errors import GameplayContractError
from gameplay_rules.projection.mana_stack_exception_package import _canonical_candidate
from gameplay_rules.shared_proposal_legality.reviews import PERMISSIONS
from .scope import SELECTED_REFERENCES

CANONICAL_MAIN = "d294835929a320fce01fb4025bdb3a4934e2eeaa"
BASE_TREE = "b846d10d3ea2438feba559a42eca7eb6fb485a45"
HISTORICAL_RECOMMENDATION = "sha256:625c55bbd527c78b351ee5cf08c5d749190d8efbb117ac595e2253dc02d626af"
PR207_PACKAGE = "sha256:72536eb1bbbc3422797215a3630a9f512b9d2a0b758e8a852e4903e71e047e82"
PR207_PROJECTION = "sha256:14a1616f247b920f68af5860adce445fa597fe4159de305410de9fa70fc959c2"
PR207_NAME = "gameplay-rules-casting-stage-family-completion"
STAGES = tuple("601.2" + letter for letter in "abcdefghi")
FAMILY = SELECTED_REFERENCES


def _fail(code):
    raise GameplayContractError("casting_permission_family_reviews", code)


def _resolve_historical_self(value):
    """PR207's self references always resolve to PR207, never this package."""
    if type(value) is dict:
        if "package_binding" in value:
            if value.pop("package_binding") != "THIS_ENCLOSING_PACKAGE":
                _fail("RETAINED_SELF_BINDING_INVALID")
            value["package_id"] = PR207_PACKAGE
        for child in value.values():
            _resolve_historical_self(child)
    elif type(value) is list:
        for child in value:
            _resolve_historical_self(child)


def authored_records(binding, projection):
    """Describe the frozen complete family using private canonical input copies."""
    binding = json.loads(_canonical_candidate(binding))
    projection = json.loads(_canonical_candidate(projection))
    if type(binding) is not dict or type(projection) is not dict:
        _fail("PLAIN_JSON_RECORDS_REQUIRED")
    if [row["rule_reference"] for row in projection["rules"]] != list(FAMILY):
        _fail("EXACT_FROZEN_SEVEN_UNIT_FAMILY_REQUIRED")
    rules = {row["rule_reference"]: row for row in projection["rules"]}

    def evidence(reference):
        if reference not in rules:
            return {"rule_reference": reference, **deepcopy(binding["rule_bindings"][reference])}
        rule = rules[reference]
        return {"rule_reference": reference, "rule_id": rule["rule_id"],
            "projection_id": projection["projection_id"], "package_binding": "THIS_ENCLOSING_PACKAGE",
            "anchor_identity": rule["source_anchor"]["anchor_id"],
            "source_anchor": deepcopy(rule["source_anchor"])}

    def record(name, findings):
        return {"schema_version": 1, "record_type": name.removesuffix(".json"),
            "canonical_base": CANONICAL_MAIN, "status": "CASTING_PERMISSION_FAMILY_PROJECTED",
            "non_executable": True, "source_body_retained": False,
            "semantic_closure": "OPEN", "execution_readiness": "BLOCKED", "findings": findings}

    from gameplay_rules.casting_stage_family_completion import package as prior
    previous = prior._expected_records()
    ranges = deepcopy(previous["range-reassessment.json"]["findings"])
    _resolve_historical_self(ranges)
    consumers = deepcopy(previous["consumer-semantic-boundaries.json"]["findings"])
    _resolve_historical_self(consumers)

    scope = {
        "decision_date": "2026-10-22", "authority": "EXPLICIT_OWNER_CURRENT_MILESTONE_INSTRUCTION",
        "selected_milestone": "CASTING-PERMISSION FAMILY BATCH",
        "historical_recommendation": {"package": PR207_NAME, "package_id": PR207_PACKAGE,
            "record": "subsequent-recommendation.json", "review_id": HISTORICAL_RECOMMENDATION,
            "milestone": "Legality-input and semantic-frontier reasoning review",
            "relationship": "NEW_OWNER_SELECTION_APPENDED_WITHOUT_REWRITING_HISTORY",
            "record_unchanged": True, "historical_allowlist": [],
            "historical_future_milestone_authorized": False, "historical_future_milestone_begun": False},
        "source_selection": {"basis": "EXACT_VERIFIED_ARTIFACT_STRUCTURAL_MARKER_INVENTORY",
            "inventory_frozen_before_body_inspection": True, "family_parent": "601.3",
            "ordered_allowlist": list(FAMILY), "unit_count": len(FAMILY),
            "following_sibling_boundary": {"rule_reference": "601.4", "physical_line": 2501,
                "body_inspected": False},
            "ownership": [{"rule_reference": ref, "source_anchor": deepcopy(rules[ref]["source_anchor"])}
                for ref in FAMILY], "naive_prefix_selection_used": False,
            "outgoing_dependency_traversal": False},
        "preflight": {"conclusion": "PASSED",
            "stop_code_if_insufficient": "CASTING_PERMISSION_FAMILY_SCOPE_INSUFFICIENT",
            "exact_artifact_and_retained_lineage_verified_before_body_inspection": True,
            "complete_owned_units_including_continuations_and_examples_inspected": True,
            "literal_citations": {ref: [] for ref in FAMILY},
            "literal_ranges": {ref: [] for ref in FAMILY},
            "structural_relationship": "PARENT_601_3_WITH_SIX_OWN_SUBRULES",
            "semantic_overlap": ["proposal choices", "casting permission and prohibitions",
                "conditional timing", "characteristics considered for casting legality"],
            "indirect_consumer_relevance": ["madness casting context", "retained activation comparison"],
            "coherence_judgment": "Every complete family member supports conditional authored knowledge with the retained casting context. Other systems remain explicit unknowns; no newly admitted outside unit is indispensable to representing what this family states.",
            "additional_source_units_required": [], "additional_source_units_admitted": [],
            "neighbor_or_outgoing_reference_bodies_inspected": False},
        "one_combined_projection_and_package": True, "additional_source_authorized": False,
        "future_milestone_authorized": False, "future_milestone_begun": False,
    }
    correspondence = {
        "fresh_authority": "OWNER_AUTHORIZED_FROZEN_COMPLETE_STRUCTURAL_FAMILY",
        "source_binding": deepcopy(projection["source_binding"]),
        "new_rule_bindings": [evidence(ref) for ref in FAMILY],
        "complete_units": [{"reference": ref, "anchor": deepcopy(rules[ref]["source_anchor"]),
            "literal_numbered_citations": [], "literal_numbered_ranges": []} for ref in FAMILY],
        "original_internal_line_endings_preserved": True,
        "final_terminators_and_separator_lines_excluded": True,
        "source_bodies_or_examples_retained": False, "attachment_path_retained": False,
        "offline_metadata_validation_is_fresh_source_verification": False,
        "fictional_fixtures_supply_source_authority": False,
        "hosted_missing_artifact_means": "EXPLICIT_SOURCE_DEPENDENT_SKIP",
        "historical_marker_observation": {"reference": "601.3", "physical_line": 2483,
            "basis": "PR207_FOLLOWING_BOUNDARY_MARKER_ONLY",
            "prior_body_or_child_inventory_verification": False},
    }
    contributions = [
        ("601.3", "Beginning requires an allowing rule or effect and no prohibiting rule or effect, interpreted with this family's stated qualifications.",
            ["applicable allowing rules or effects", "applicable prohibitions", "player and proposed spell"]),
        ("601.3a", "A quality-based prohibiting effect may be ignored for beginning if some proposal choice could change the relevant qualities so that this effect no longer prohibits casting.",
            ["exact prohibiting effect", "qualities it tests", "available proposal choices and their consequences"]),
        ("601.3b", "A quality-limited as-though-flash effect can support beginning if a possible proposal choice could make that effect apply.",
            ["exact granting effect", "qualities it tests", "available proposal choices and their consequences"]),
        ("601.3c", "An as-though-flash effect conditioned on paying an alternative or additional cost permits beginning with that timing treatment.",
            ["applicable effect", "specified alternative or additional cost", "subsequent declarations and payment facts"]),
        ("601.3d", "If flash depends on conditions, the controller can begin with flash timing when those conditions are met.",
            ["specified conditions", "evidence that the conditions are met", "controller"]),
        ("601.3e", "Where a rule or effect designates alternative or subset characteristics for the casting-legality determination, they replace the object's characteristics for that determination; relevant continuous effects on the object with those characteristics are considered too.",
            ["rule or effect designating the characteristic set", "designated characteristics", "continuous effects applicable with that set"]),
        ("601.3f", "For an effect allowing quality-limited casting from face-down exile, beginning also requires that the player can look at the card.",
            ["applicable casting effect", "face-down exile location", "player's ability to look", "relevant card qualities"]),
    ]
    permission = {
        "question": "What does the verified family establish about beginning a casting proposal, which conditions or choices matter, and what evidence is still needed for a particular proposed spell?",
        "incremental_contributions": [{"reference": ref, "evidence": evidence(ref),
            "bounded_fact": text, "required_Card_effect_state_evidence": inputs,
            "actual_proposed_spell_legality": "UNKNOWN_OR_UNSUPPORTED"} for ref, text, inputs in contributions],
        "retained_context": {"permission_to_begin_and_ordered_procedure": evidence("601.2"),
            "procedure_map": {"package": PR207_NAME, "package_id": PR207_PACKAGE,
                "record": "procedure-map.json", "review_id": previous["procedure-map.json"]["review_id"],
                "stage_source_coverage": "9/9", "map_repeated": False},
            "legality_checkpoint": evidence("601.2e"), "completion": evidence("601.2i")},
        "permission_versus_completion": "These conditions and qualifications concern beginning or the characteristic basis of casting legality. A supported beginning does not establish compatible later choices, passing the retained legality checkpoint, paying costs, or completing the preceding stages required by i.",
        "choice_consistency": "Separate possible choices considered for different effects do not establish that one compatible set of actual choices satisfies them all.",
        "checkpoint_relationship": "The family's criteria inform an authored explanation of permission and casting legality. Its relationship to e is semantic overlap within the retained procedure; e does not literally cite 601.3 and still separately cites 733.",
        "conditional_limits": {"a_ignores_all_prohibitions": False,
            "parent_necessary_conditions_prove_sufficient_permission": False,
            "a_or_b_possible_choice_proves_actual_choice_legal": False,
            "c_cost_condition_is_prepaid_or_waived": False,
            "d_conditions_may_be_merely_possible": False,
            "e_uses_original_and_alternative_sets_in_parallel": False,
            "f_casting_effect_itself_grants_look_permission": False,
            "beginning_guarantees_successful_completion": False},
        "authored_explanatory_cases": [
            {"case": "A prospective quality change avoids one prohibition",
                "hypothetical_assumptions": ["A separately established effect allows the player to cast the hypothetical spell.",
                    "One effect prohibits casting spells with quality Q.",
                    "An available proposal choice could remove Q, and no other prohibition is assumed."],
                "applicable_rule_evidence": [evidence("601.3"), evidence("601.3a"), evidence("601.2e")],
                "bounded_conclusion": "The specified quality prohibition may be ignored for beginning under a. This describes the beginning qualification, not the legality of the actual eventual proposal.",
                "missing_or_unresolved": ["authoritative spell and effect evidence", "actual compatible choices",
                    "legality at e", "full cost and completion evidence"]},
            {"case": "A prospective quality change enables timing treatment",
                "hypothetical_assumptions": ["An effect permits spells with quality R to be cast as though they had flash.",
                    "An available proposal choice could give the hypothetical spell R."],
                "applicable_rule_evidence": [evidence("601.3b"), evidence("601.3")],
                "bounded_conclusion": "The effect can support beginning with as-though-flash treatment under b; the possible choice does not establish a final legal proposal.",
                "missing_or_unresolved": ["exact effect and choice semantics", "other permissions and prohibitions",
                    "consistent actual choices", "general timing semantics"]},
            {"case": "Cost-conditioned timing and condition-dependent flash",
                "hypothetical_assumptions": ["In one hypothetical, an effect grants as-though-flash treatment only if an additional cost is paid.",
                    "In a separate hypothetical, the spell has flash only if state condition S is met, and S is assumed met."],
                "applicable_rule_evidence": [evidence("601.3c"), evidence("601.3d"), evidence("601.2h")],
                "bounded_conclusion": "c allows the first beginning without establishing payment. d allows the separate beginning with flash treatment on the stated satisfied-condition assumption.",
                "missing_or_unresolved": ["effect and condition evidence", "resources and actual payment",
                    "remaining permissions and prohibitions", "successful procedure completion"]},
            {"case": "A designated characteristic set controls the determination",
                "hypothetical_assumptions": ["A rule or effect specifically designates alternative characteristics C for determining whether a hypothetical object can be cast.",
                    "A known hypothetical continuous effect would apply once that object has C."],
                "applicable_rule_evidence": [evidence("601.3e"), evidence("601.2e")],
                "bounded_conclusion": "Use C in place of the object's characteristics for that determination and consider the stated continuous effect. This does not determine the effect's result or actual legality.",
                "missing_or_unresolved": ["authoritative designation and characteristic evidence",
                    "effect applicability and resulting characteristics", "other legality criteria"]},
            {"case": "A hidden exiled card has a separate inspection condition",
                "hypothetical_assumptions": ["An effect allows casting spells with quality T from face-down exile.",
                    "The player cannot look at the hypothetical face-down card."],
                "applicable_rule_evidence": [evidence("601.3f"), evidence("601.3")],
                "bounded_conclusion": "The stated look condition for beginning under that effect is unsatisfied. If looking were separately established, f alone would still not prove positive casting permission or completed legality.",
                "missing_or_unresolved": ["actual look permission", "card qualities and effect scope",
                    "any other casting basis", "remaining permission and legality facts"]},
        ],
        "unknown_or_unsupported": ["actual Card or Oracle meaning", "complete applicable rule and effect set",
            "actual state, timing and priority", "choice compatibility and consequences",
            "target and allocation legality", "effect evaluation", "cost payability and payment",
            "successful checkpoint and completion", "recovery and runtime execution"],
        "real_Card_or_Oracle_data_used": False, "official_examples_retained": False,
        "scenario_system_created": False, "permission_or_legality_evaluator_created": False,
    }
    relationships = {
        "parent_reference_reassessment": {"origin": "601.2", "target": "601.3",
            "relationship": "RETAINED_LITERAL_REFERENCE", "origin_evidence": evidence("601.2"),
            "target_evidence": evidence("601.3"), "historical_record_unchanged": True,
            "historical_status": "UNRESOLVED", "current_status": "DIRECT_REFERENCE_RESOLVED",
            "resolution_level": "INDIVIDUAL_TARGET_SOURCE_COVERAGE_ONLY",
            "complete_family_coverage": "7/7", "semantic_closure": "OPEN",
            "individual_reference_resolution_implies_family_or_semantic_closure": False},
        "family_structure": {"parent": evidence("601.3"),
            "children": [evidence(ref) for ref in FAMILY[1:]],
            "relationship": "STRUCTURAL_PARENT_AND_OWN_SUBRULES", "literal_parent_citations_invented": False},
        "checkpoint_overlap": {"origin": "601.2e", "target_family": "601.3",
            "relationship": "SEMANTIC_OVERLAP_WITH_RETAINED_LEGALITY_CHECKPOINT",
            "literal_601_2e_to_601_3_citation": False,
            "actual_literal_601_2e_reference": {"target": "733", "status": "UNRESOLVED"}},
        "retained_ranges": {"prior_record": "range-reassessment.json",
            "prior_review_id": previous["range-reassessment.json"]["review_id"],
            "package_id": PR207_PACKAGE, "casting_parent": ranges["casting_parent"],
            "activated_import": ranges["activated_import"], "completion_range": ranges["completion_range"],
            "historical_findings_preserved": True,
            "parent_reference_current_reassessment_is_separate": True},
        "activation_boundary": {"601_3_automatically_governs_abilities_via_b_i_import": False,
            "new_literal_activation_to_601_3_edge": False,
            "casting_and_activation_semantics_unconditionally_interchangeable": False},
        "indirect_consumers": {"madness": "INDIRECT_CONSUMER_NO_NEW_LITERAL_CITATION",
            "loyalty": "CLASSIFICATION_DISTINCT_FROM_EXECUTION_AND_MISSING_BROAD_RULES",
            "activated_and_triggered_mana_semantics_interchangeable": False},
        "unresolved_literal_frontiers": [{"origin": origin, "target": target,
            "relationship": "RETAINED_LITERAL_REFERENCE", "state": "UNRESOLVED",
            "source_evidence": evidence(origin), "target_body_inspected": False}
            for origin, target in (("601.2", "733"), ("601.2e", "733"), ("602.2", "733"),
                ("602.2a", "701.20a"), ("601.2a", "611.2f"), ("601.2a", "610.5"))],
        "semantic_frontiers_without_new_literal_citations": ["shared 603 and delayed-trigger rules",
            "broad 606 and missing loyalty rules", "flash and general timing semantics",
            "effect application", "stack and priority", "legality and recovery"],
        "all_outside_frontier_bodies_inspected_or_admitted": False,
        "all_ten_activation_responsibilities": deepcopy(consumers["activated_responsibilities"]),
        "source_coverage_is_actual_permission_legality_completion_or_execution": False,
    }
    components = deepcopy(binding["projection_components"])
    prior_references = [ref for component in components for ref in component["projected_references"]]
    if (len(components) != 14 or len({row["projection_id"] for row in components}) != 14
            or len(prior_references) != 93 or len(set(prior_references)) != 93
            or set(prior_references) != set(binding["rule_bindings"])
            or set(prior_references).intersection(FAMILY)):
        _fail("EXACT_DISJOINT_93_14_RETAINED_INVENTORY_REQUIRED")
    components.append({"name": "casting_permission_family", "projection_id": projection["projection_id"],
        "package_binding": "THIS_ENCLOSING_PACKAGE", "projected_references": list(FAMILY)})
    references = [ref for row in components for ref in row["projected_references"]]
    if (len(components) != 15 or len({row["projection_id"] for row in components}) != 15
            or len(references) != 100 or len(set(references)) != 100):
        _fail("EXACT_100_15_SUCCESSOR_INVENTORY_REQUIRED")
    composite = {
        "view_kind": "READ_ONLY_FIFTEEN_PROJECTION_COMPOSITE", "projection_components": components,
        "projected_references": references, "previous_count": len(prior_references),
        "new_count": len(FAMILY), "total_projected_rule_count": len(set(references)),
        "previous_projection_count": len(components) - 1, "total_projection_count": len(components),
        "all_prior_rule_bindings": deepcopy(binding["rule_bindings"]),
        "new_rule_bindings": [evidence(ref) for ref in FAMILY],
        "stage_coverage": "9/9", "parent_proposal_range_coverage": "4/4",
        "single_activated_import_coverage": "8/8", "i_preceding_range_source_coverage": "8/8",
        "complete_601_3_family_coverage": "7/7", "prior_rule_bindings_changed": False,
        "monolithic_projection_created": False, "additional_rules_projected": [],
        "broad_601_complete": False,
        "preservation_readiness": {
            "protected_PR207_package_id": PR207_PACKAGE, "protected_PR207_projection_id": PR207_PROJECTION,
            "historical_acquisition_identity": binding["historical_acquisition_identity"],
            "historical_packages_own_identities_manifests_and_self_bindings_preserved": True,
            "historical_coverage_allowlists_authorization_flags_recommendations_preserved": True,
            "PR_205_206_performance_implementations_and_ledgers_preserved": True,
            "preservation_method": "EXISTING_GUARDS_AND_DIRECT_CANONICAL_GIT_BLOB_AND_MODE_COMPARISON",
            "whole_repository_freeze_fixture_added": False,
            "all_ten_activation_responsibilities": "OPEN / EXECUTION_BLOCKED", "real_execution": "BLOCKED",
            "real_snapshot_created": False, "real_execution_profile_activated": False,
            "source_policy_clearance": "not_granted", "permissions": deepcopy(PERMISSIONS),
            "Architecture_v13": "ACTIVE APPROVED", "Decision_017": "ACCEPTED",
            "canonical_base": CANONICAL_MAIN, "canonical_base_tree": BASE_TREE,
            "owner_final_merge_approval_required": True, "independent_PM_review_required": True,
            "required_validation": ["focused_contract_identity_mutation_source_semantic_preservation_checks",
                "actual_fresh_reproduction_of_all_seven_units", "one_complete_local_discovery",
                "final_head_hosted_push_and_PR_actual_publication_gates"],
            "offline_metadata_validation_is_fresh_source_verification": False},
    }
    subsequent = {
        "authority": "ASSESSMENT_ONLY_UNAUTHORIZED_UNBEGUN_RECOMMENDATION",
        "recommendation_count": 1, "fresh_additional_body_inspection": [],
        "recommendation": {"milestone": "Proposed-spell evidence packet contract design",
            "useful_reasoning_outcome": "Design a reviewable evidence-packet contract that binds a proposed spell's asserted permission, prohibition, choices and state facts to their evidence while preserving unknown and unsupported outcomes; demonstrate packet completeness with authored fictional examples without deciding legality.",
            "kind": "RETAINED_EVIDENCE_ONLY_DESIGN", "proposed_allowlist": [],
            "expected_added_source_units": 0,
            "boundary": "Specify evidence fields, provenance and uncertainty for future human review. Do not repeat the delivered source or missing-input inventory and do not implement an evaluator.",
            "explicit_exclusions": ["additional_source_body_inspection", "source_projection", "Card_or_Oracle_data",
                "runtime", "permission_or_legality_evaluation", "casting_or_activation_execution"],
            "future_milestone_authorized": False, "future_milestone_begun": False,
            "future_source_projection_authorized": False, "requires_separate_owner_authorization": True},
    }
    return {name: record(name, body) for name, body in {
        "scope-preflight.json": scope, "source-correspondence.json": correspondence,
        "permission-assessment.json": permission, "relationship-reassessment.json": relationships,
        "composite-coverage.json": composite, "subsequent-recommendation.json": subsequent}.items()}
