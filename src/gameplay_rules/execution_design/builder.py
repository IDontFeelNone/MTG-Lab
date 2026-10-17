"""Reproduce a design/review layer from verified retained metadata only.

The external source TXT is deliberately not an input. Nothing in this module
constructs an executable snapshot, registers a profile, or evaluates gameplay.
"""
from __future__ import annotations

from evidence.contracts import sha256_identity
from gameplay_rules.errors import GameplayContractError
from gameplay_rules.projection import load_projection_package
from gameplay_rules.projection.package import package_manifest as projection_package_manifest
from gameplay_rules.projection.scope import SELECTED_REFERENCES
from .contracts import (PROJECTION_ID, PROJECTION_PACKAGE_ID, SOURCE_BINDING,
    FoundationalProjectionReview, RealRulesCapabilityMatrix,
    RealRulesExecutionProfileDesign, RealRulesActivationGateDesign, RealRulesExecutionReadiness)
from .gates import review_rule, assess_activation
from .scope import (ACTIVATION_REQUIREMENTS, CAPABILITY_CONTENT, DESIGN_VERSION,
                    FUTURE_ENGINE_TARGET, PROFILE_TARGET, UNSUPPORTED_CAPABILITIES)


def _unique(values):
    return list(dict.fromkeys(values))


def _aggregate(rows, field):
    return _unique(item for row in rows for item in row[field])


def _closure(rows, field):
    return "OPEN" if any(row[field] == "OPEN" for row in rows) else "UNKNOWN"


def build_review(projection):
    rows = [review_rule(projection, reference) for reference in SELECTED_REFERENCES]
    unresolved = _aggregate(rows, "unresolved_dependencies")
    exceptions = _aggregate(rows, "unprojected_exceptions")
    return FoundationalProjectionReview.create({
        "game_id": "magic", "review_version": "foundational-execution-design-review-v1",
        "projection_package_id": PROJECTION_PACKAGE_ID, "projection_id": PROJECTION_ID,
        "source_binding": dict(SOURCE_BINDING),
        "reviewer_class": "PROJECT_AUTHORED_EXECUTION_DESIGN_REVIEW", "reviewed_on": "2026-10-17",
        "review_status": "REVIEWED_FOR_EXECUTION_DESIGN", "rules": rows,
        "dependency_findings": {
            "scope": "RETAINED_GRAPH_WITH_INCOMPLETE_SEMANTIC_COVERAGE",
            "unresolved": unresolved, "projected_endpoints": list(SELECTED_REFERENCES),
            "full_closure": "NOT_PROVEN", "retained_cycles": [["101.2", "101.2a"]],
            "transitive_dependencies_propagated": True,
            "empty_known_dependency_set_is_not_execution_closure": True,
        },
        "exception_findings": {
            "unprojected": exceptions,
            "109.4": ["109.4" + suffix for suffix in "abcdefg"],
            "400.7": ["400.7" + suffix for suffix in "abcdefghijkm"],
            "other_unknown_semantic_contexts": _aggregate(rows, "unknown_semantic_contexts"),
            "full_closure": "NOT_PROVEN", "unknown_is_not_closed": True,
        },
        "execution_readiness_findings": {
            "overall": "BLOCKED", "rules_reviewed": 20,
            "reference_only": ["108.1"],
            "descriptive_state_model_candidates": [row["rule_reference"] for row in rows if row["state_model_candidate"]],
            "partially_ready_designs": [row["rule_reference"] for row in rows if row["execution_readiness"] == "PARTIALLY_READY"],
            "execution_ready_rules": [], "available_real_primitives": [],
            "execution_approval": "NOT_GRANTED",
        },
        "limitations": [
            "This is a project-authored review for execution design, not owner or execution approval.",
            "PARTIALLY_READY describes bounded vocabulary/state-model candidates; execution_ready remains false.",
            "Retained source-anchor evidence is checked offline; this review does not claim fresh access to official source bytes.",
            "Known graph endpoints are not complete semantic dependency or exception closure.",
        ],
        "unsupported_dimensions": list(UNSUPPORTED_CAPABILITIES),
    })


def build_capability_matrix(review):
    review.verify()
    reviewed = {row["rule_reference"]: row for row in review.to_dict()["rules"]}
    capabilities = []
    for content in CAPABILITY_CONTENT:
        supporting = [reviewed[reference] for reference in content["supporting_rules"]]
        partial = all(row["execution_readiness"] == "PARTIALLY_READY" for row in supporting)
        capabilities.append({
            **content,
            "dependency_closure": _closure(supporting, "dependency_closure"),
            "exception_closure": _closure(supporting, "exception_closure"),
            "implementation_primitive_available": False, "execution_supported": False,
            "execution_readiness": "PARTIALLY_READY" if partial else "BLOCKED",
            "blocking_references": _unique(_aggregate(supporting, "unresolved_dependencies")
                                           + _aggregate(supporting, "unprojected_exceptions")),
            "required_semantic_primitives": _aggregate(supporting, "required_semantic_primitives"),
            "unknown_semantic_contexts": _aggregate(supporting, "unknown_semantic_contexts"),
        })
    return RealRulesCapabilityMatrix.create({
        "game_id": "magic", "matrix_version": "real-rules-capability-design-v1",
        "projection_id": PROJECTION_ID, "projection_review_id": review.identity,
        "capabilities": capabilities, "overall_execution_readiness": "BLOCKED",
        "coverage_policy": {
            "projection_presence_does_not_support_execution": True,
            "partially_ready_means_descriptive_state_model_candidate_only": True,
            "real_execution_primitives_available": [],
            "unsupported_and_unknown_remain_distinct": True,
        },
    })


def required_rule_set_identity(review):
    """Identify future requirements, not a real executable rules snapshot."""
    return "sha256:" + sha256_identity({
        "domain": "gameplay-real-rule-set-requirements-v1",
        "content": {"projection_id": PROJECTION_ID, "projection_review_id": review.identity,
            "rules": [{"rule_reference": row["rule_reference"],
                       "source_span_sha256": row["source_anchor"]["span_sha256"],
                       "required_semantic_primitives": row["required_semantic_primitives"]}
                      for row in review.to_dict()["rules"]]},
    })


def build_profile_design(review, matrix):
    review.verify()
    matrix.verify()
    if matrix.projection_review_id != review.identity or matrix.projection_id != review.projection_id:
        raise GameplayContractError("execution_design_binding", "capability matrix belongs to another projection review")
    rows = review.to_dict()["rules"]
    capabilities = matrix.to_dict()["capabilities"]
    rule_set_id = required_rule_set_identity(review)
    return RealRulesExecutionProfileDesign.create({
        "game_id": "magic", "design_version": DESIGN_VERSION,
        "target_profile_id": PROFILE_TARGET, "target_label": "DESIGN_TARGET_NOT_EXECUTABLE",
        "engine_compatibility_target": {
            "observed_engine_contract": "gameplay-kernel-v1",
            "observed_execution_profile": "fictional-two-player-v1",
            "target_engine_contract": FUTURE_ENGINE_TARGET,
            "target_implementation_status": "NOT_IMPLEMENTED", "compatible_with_current_runtime": False,
        },
        "source_binding": dict(SOURCE_BINDING), "foundational_projection_id": PROJECTION_ID,
        "foundational_package_id": PROJECTION_PACKAGE_ID,
        "required_projection_review_id": review.identity,
        "required_execution_approval_review_id": None, "required_rule_set_id": rule_set_id,
        "capability_matrix_id": matrix.identity,
        "capability_coverage": {
            "available_execution_capabilities": [],
            "descriptive_state_model_candidates": [row["capability_id"] for row in capabilities
                                                     if row["execution_readiness"] == "PARTIALLY_READY"],
            "blocked_capabilities": [row["capability_id"] for row in capabilities
                                     if row["execution_readiness"] == "BLOCKED"],
            "reference_only": ["source_authority"], "none_is_activated": True,
        },
        "required_dependency_closure": [{"rule_reference": row["rule_reference"],
            "required": "CLOSED", "assessed": row["dependency_closure"],
            "known_graph": row["known_dependency_closure"],
            "unresolved": row["unresolved_dependencies"]} for row in rows if row["direct_runtime_relevance"] != "NONE"],
        "required_exception_closure": [{"rule_reference": row["rule_reference"],
            "required": "CLOSED", "assessed": row["exception_closure"],
            "known_graph": row["known_exception_closure"],
            "unprojected": row["unprojected_exceptions"]} for row in rows if row["direct_runtime_relevance"] != "NONE"],
        "required_semantic_primitives": _aggregate(rows, "required_semantic_primitives"),
        "unsupported_capabilities": list(UNSUPPORTED_CAPABILITIES),
        "unknown_capabilities": _unique(["complete_semantic_dependency_closure", "complete_semantic_exception_closure",
                                          *_aggregate(rows, "unknown_semantic_contexts")]),
        "activation_requirements": list(ACTIVATION_REQUIREMENTS),
        "source_evidence_requirements": {
            "exact_artifact": dict(SOURCE_BINDING), "retained_metadata_lineage_verified": True,
            "source_anchor_evidence": "RETAINED_VERIFIED_SOURCE_ANCHORS_NO_FRESH_SOURCE_ACCESS_CLAIM",
            "offline_design_reproducible": True, "external_txt_required_for_design": False,
            "future_activation_requires_bound_anchor_verification_evidence": True,
            "broader_source_content_permissions": "NOT_ESTABLISHED",
        },
        "projection_approval_requirements": {
            "design_review_id": review.identity, "design_review_status": review.review_status,
            "separate_execution_approval_required": True, "execution_approval": "NOT_GRANTED",
            "explicit_owner_activation_required": True,
            "projection_presence_is_not_execution_approval": True,
        },
        "future_snapshot_design": {
            "proposed_schema": "gameplay-real-rules-snapshot-v1", "status": "DESIGN_ONLY",
            "snapshot_instantiated": False,
            "required_bindings": ["game_id", "exact_source_release", "artifact_hash", "artifact_verification_id",
                "artifact_correspondence_review_id", "projection_package_id", "projection_id",
                "design_review_id", "execution_approval_review_id", "execution_profile_id",
                "rules_snapshot_schema_version", "engine_contract_version", "rule_set_id",
                "primitive_registry_id_and_version", "capability_matrix_id", "closure_assessment_id",
                "deterministic_test_vector_evidence_id", "owner_activation_receipt_id"],
            "loader_policy": "A separately authorized real loader must reject missing or incompatible bound evidence; the fictional loader stays unchanged and rejects real designs.",
            "primitive_mapping_policy": "Explicit versioned primitive registry entries must cite reviewed rule references and exact source anchors; prose or vocabulary labels do not implement primitives.",
            "capability_policy": "Only capabilities matched to implemented, tested primitives may be claimed supported; unknown result-relevant capabilities block definitive rulings.",
            "exception_policy": "Every runtime-used rule requires CLOSED dependency and exception closure; OPEN or UNKNOWN closure denies use.",
            "replay_policy": "Pin snapshot/profile, engine, primitive registry, state/action/Card-semantic versions and all evidence identities; never substitute a later release or fictional fallback.",
        },
        "proof_trace_design": {
            "status": "DESIGN_ONLY", "result_instantiated": False,
            "chain": ["future_LegalityResult", "versioned_executable_primitive", "required_rule_set_id",
                      "projection_review_id", "reviewed_projection_rule_reference", "exact_source_anchor",
                      "official_artifact_hash_and_release"],
            "source_artifact_hash": SOURCE_BINDING["artifact_hash"], "projection_id": PROJECTION_ID,
            "projection_review_id": review.identity, "required_rule_set_id": rule_set_id,
            "anchor_binding": "EXACT_RETAINED_SOURCE_ANCHORS", "unsupported_policy": "INDETERMINATE_OR_UNSUPPORTED",
        },
        "release_update_policy": {
            "implicit_latest_allowed": False, "mutation_allowed": False, "cross_profile_fallback": False,
            "new_release_requires": ["new_artifact_identity", "new_projection_identities", "new_projection_reviews",
                                     "new_closure_assessments", "new_primitive_compatibility_evidence",
                                     "new_real_execution_profile_revision", "new_activation_authorization"],
            "old_replays": "PINNED_IMMUTABLE_IDENTITIES",
        },
        "epistemic_policy": {"unresolved_or_unmodeled_result": "INDETERMINATE_OR_UNSUPPORTED",
                             "definitive_legality_without_closure": False},
        "status": "DESIGN_ONLY",
        "limitations": [
            "This target is a future design, incompatible with the existing fictional runtime.",
            "No real snapshot, execution profile, semantic primitive, Card semantics or legality result is instantiated.",
            "All current real-rule execution use remains blocked; a later milestone and owner activation are required.",
        ],
    })


def build_records(projection):
    review = build_review(projection)
    matrix = build_capability_matrix(review)
    design = build_profile_design(review, matrix)
    evidence, assessment = assess_activation(projection, review, matrix, design)
    activation = RealRulesActivationGateDesign.create({
        "game_id": "magic", "gate_version": "real-rules-activation-gates-v1",
        "profile_design_id": design.identity, "projection_review_id": review.identity,
        "required_rule_set_id": design.required_rule_set_id, "requirements": list(ACTIVATION_REQUIREMENTS),
        "current_evidence": evidence, "assessment": assessment,
        "structural_proof_policy": {
            "fictional_boolean_fixtures_only": True, "all_requirements_are_conjunctive": True,
            "requirements_satisfied_is_not_runtime_activation": True,
            "this_design_can_never_issue_an_activation_receipt": True,
        },
        "limitations": ["These are deterministic design/structural gates, not an activated runtime or a verifier of future owner attestations.",
                        "Caller assertions may only add blockers to the real design; they cannot replace missing semantic or approval evidence."],
    })
    rows = review.to_dict()["rules"]
    readiness = RealRulesExecutionReadiness.create({
        "game_id": "magic", "assessment_version": "real-execution-readiness-assessment-v1",
        "projection_review_id": review.identity, "profile_design_id": design.identity,
        "capability_matrix_id": matrix.identity, "activation_gate_design_id": activation.identity,
        "overall_execution_readiness": "BLOCKED", "readiness_code": "REAL_EXECUTION_PROFILE_NOT_READY",
        "per_rule_states": {row["rule_reference"]: row["execution_readiness"] for row in rows},
        "unresolved_dependencies": _aggregate(rows, "unresolved_dependencies"),
        "unprojected_exceptions": _aggregate(rows, "unprojected_exceptions"),
        "unknown_semantic_contexts": _aggregate(rows, "unknown_semantic_contexts"),
        "blockers": _unique([*assessment["blockers"], "EXECUTION_APPROVAL_NOT_GRANTED",
                             "REAL_SEMANTIC_PRIMITIVES_NOT_IMPLEMENTED", "COMPLETE_CLOSURE_NOT_PROVEN"]),
        "next_milestone": {"candidate": "Foundational Dependency & Exception Projection",
            "rationale": "Five unresolved references and nineteen unprojected exceptions dominate closure; use a separately authorized exact allowlist before proposing real primitives or activation.",
            "authorized": False},
        "limitations": ["PARTIALLY_READY rows are descriptive state-model candidates, never execution-ready behavior.",
                        "This assessment is reproducible from retained metadata; no new CR source prose or Oracle content is inspected.",
                        "No real execution approval, runtime activation or Tier-0 change is made."],
    })
    return {"projection-review.json": review, "capability-matrix.json": matrix,
            "execution-profile-design.json": design, "activation-gates.json": activation,
            "readiness.json": readiness}


def build_design_package(*, projection_root, artifact_review_root, source_root, discovery_root):
    """Verify all retained inputs and return records; never write source/data."""
    projection = load_projection_package(projection_root, artifact_review_root=artifact_review_root,
        source_root=source_root, discovery_root=discovery_root)
    manifest = projection_package_manifest(projection, (projection.serialize() + "\n").encode("utf-8"))
    if manifest["package_id"] != PROJECTION_PACKAGE_ID or projection.identity != PROJECTION_ID:
        raise GameplayContractError("execution_design_binding", "exact merged projection package required")
    return build_records(projection)
