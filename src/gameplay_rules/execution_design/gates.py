"""Deterministic design gates; none authorizes or performs gameplay execution.

Known graph closure and complete semantic closure are different. This release's
small projection establishes only the former. Unknown closure stays a blocker.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

from gameplay_rules.errors import GameplayContractError
from gameplay_rules.projection.contracts import FoundationalProjection
from gameplay_rules.projection.scope import SELECTED_REFERENCES
from .contracts import PROJECTION_ID, SOURCE_BINDING
from .scope import ACTIVATION_REQUIREMENTS, RULE_REVIEW_CONTENT


def _fail(message):
    raise GameplayContractError("real_rules_design_gate", message)


def _projection(projection):
    if not isinstance(projection, FoundationalProjection):
        _fail("verified foundational projection contract required")
    projection.verify()
    if projection.identity != PROJECTION_ID:
        _fail("foundational projection identity differs")


def closure_findings(projection, reference):
    """Walk the retained graph, including cycles, without reading other rules."""
    _projection(projection)
    if reference not in SELECTED_REFERENCES:
        _fail("only the twenty projected rules may be reviewed")
    graph = projection.to_dict()["graph"]
    nodes = {row["rule_reference"]: row["status"] for row in graph["nodes"]}
    adjacent = {}
    for edge in graph["edges"]:
        adjacent.setdefault(edge["from_reference"], []).append(edge["to_reference"])
    def reachable(start):
        visited, pending = set(), [start]
        while pending:
            current = pending.pop()
            if current in visited:
                continue
            visited.add(current)
            pending.extend(adjacent.get(current, ()))
        return visited

    visited = reachable(reference)
    prerequisites = [item for item in SELECTED_REFERENCES if item != reference and item in visited]
    unresolved = [row["rule_reference"] for row in graph["nodes"]
                  if row["rule_reference"] in visited and row["status"] == "UNRESOLVED"]
    exceptions = [row["rule_reference"] for row in graph["nodes"]
                  if row["rule_reference"] in visited and row["status"] == "UNPROJECTED_EXCEPTION"]
    # An exception can itself be unresolved (104.3a), or projected but blocked
    # by another unresolved rule (101.2a -> 113.10). Neither is a closed known
    # exception merely because its target lacks UNPROJECTED_EXCEPTION status.
    exception_open = bool(exceptions) or any(
        nodes[item] != "PROJECTED"
        for edge in graph["edges"]
        if edge["from_reference"] in visited and edge["relation"] == "EXCEPTION"
        for item in reachable(edge["to_reference"])
    )
    # No path in a deliberately incomplete graph proves complete CR semantics.
    # CLOSED below refers only to enumerated graph endpoints, never execution.
    return {
        "prerequisite_rules": prerequisites,
        "unresolved_dependencies": unresolved,
        "unprojected_exceptions": exceptions,
        "known_dependency_closure": "OPEN" if unresolved else "CLOSED",
        "known_exception_closure": "OPEN" if exception_open else "CLOSED",
        "dependency_closure": "OPEN" if unresolved else "UNKNOWN",
        "exception_closure": "OPEN" if exception_open else "UNKNOWN",
    }


def review_rule(projection, reference):
    """Classify an existing projection record; do not project another rule."""
    findings = closure_findings(projection, reference)
    content = RULE_REVIEW_CONTENT[reference]
    roles = list(content["semantic_roles"])
    if findings["unresolved_dependencies"] and "BLOCKED_BY_DEPENDENCY" not in roles:
        roles.append("BLOCKED_BY_DEPENDENCY")
    if findings["unprojected_exceptions"] and "BLOCKED_BY_EXCEPTION_SET" not in roles:
        roles.append("BLOCKED_BY_EXCEPTION_SET")
    blockers = ["DESIGN_ONLY_NO_RUNTIME_PROMOTION", "EXECUTION_APPROVAL_NOT_GRANTED"]
    blockers.extend("UNRESOLVED_DEPENDENCY:" + item for item in findings["unresolved_dependencies"])
    blockers.extend("UNPROJECTED_EXCEPTION:" + item for item in findings["unprojected_exceptions"])
    blockers += ["COMPLETE_DEPENDENCY_CLOSURE_NOT_PROVEN", "COMPLETE_EXCEPTION_CLOSURE_NOT_PROVEN"]
    blockers.extend("UNIMPLEMENTED_SEMANTIC_PRIMITIVE:" + item
                    for item in content["required_semantic_primitives"])
    blockers.extend("UNKNOWN_SEMANTIC_CONTEXT:" + item for item in content["unknown_semantic_contexts"])
    if reference == "108.1":
        blockers.append("REFERENCE_AUTHORITY_NEVER_GAMEPLAY_BEHAVIOR")
    # PARTIALLY_READY labels descriptive state vocabulary only. The independent
    # execution_ready flag remains false, and every execution gate stays denied.
    partial = (content["state_model_candidate"] and not findings["unresolved_dependencies"]
               and not findings["unprojected_exceptions"])
    source = next(row for row in projection.to_dict()["rules"] if row["rule_reference"] == reference)
    return {
        "rule_reference": reference, "projection_id": projection.identity,
        "source_anchor": source["source_anchor"],
        **content, "semantic_roles": roles, **findings,
        "unsupported_required_semantic_primitives": list(content["required_semantic_primitives"]),
        "implementation_now_safe": False, "execution_ready": False,
        "execution_readiness": "PARTIALLY_READY" if partial else "BLOCKED",
        "blockers": blockers,
    }


@dataclass(frozen=True)
class RuleGateEvidence:
    """Structural evidence inputs, not approvals or a runtime capability token."""

    source_release: str = "2026-09-25"
    source_anchor_verified: bool = False
    projection_review_complete: bool = False
    dependency_closure: str = "UNKNOWN"
    exception_closure: str = "UNKNOWN"
    implemented_primitives: tuple[str, ...] = ()
    unknown_capabilities: tuple[str, ...] = ()

    def __post_init__(self):
        if not isinstance(self.source_release, str) or self.source_release in {"current", "latest", ""}:
            _fail("explicit rules release required")
        for value in (self.source_anchor_verified, self.projection_review_complete):
            if type(value) is not bool:
                _fail("typed evidence booleans required")
        if self.dependency_closure not in {"OPEN", "CLOSED", "UNKNOWN"} or self.exception_closure not in {"OPEN", "CLOSED", "UNKNOWN"}:
            _fail("explicit closure state required")
        for name in ("implemented_primitives", "unknown_capabilities"):
            values = getattr(self, name)
            if not isinstance(values, (tuple, list)) or any(not isinstance(item, str) or not item for item in values) or len(set(values)) != len(values):
                _fail("distinct semantic evidence identifiers required")
            object.__setattr__(self, name, tuple(values))


def evaluate_rule_gate(projection, reference, evidence, *, review=None):
    """Evidence may add blockers; it cannot close omitted real-rule semantics.

    Even caller claims of CLOSED/implemented cannot override the retained open
    graph, unknown semantic coverage, missing real primitive registry, or the
    absence of an execution-approval review. This is not a promotion method.
    """
    from .contracts import FoundationalProjectionReview
    if not isinstance(evidence, RuleGateEvidence):
        _fail("typed rule gate evidence required")
    row = review_rule(projection, reference)
    blockers = list(row["blockers"])
    reviewed = isinstance(review, FoundationalProjectionReview)
    if reviewed:
        review.verify()
        reviewed = review.projection_id == projection.identity and review.review_status == "REVIEWED_FOR_EXECUTION_DESIGN"
        if reviewed:
            reviewed_anchor = next(item["source_anchor"] for item in review.to_dict()["rules"]
                                   if item["rule_reference"] == reference)
            reviewed = reviewed_anchor == row["source_anchor"]
    if not reviewed or not evidence.projection_review_complete:
        blockers.append("PROJECTION_REVIEW_MISSING")
    if not evidence.source_anchor_verified:
        blockers.append("SOURCE_ANCHOR_VERIFICATION_MISSING")
    if evidence.source_release != SOURCE_BINDING["effective_date"]:
        blockers.append("INCOMPATIBLE_RULES_RELEASE")
    if evidence.dependency_closure != "CLOSED":
        blockers.append("DEPENDENCY_CLOSURE_EVIDENCE_" + evidence.dependency_closure)
    if evidence.exception_closure != "CLOSED":
        blockers.append("EXCEPTION_CLOSURE_EVIDENCE_" + evidence.exception_closure)
    blockers.extend("UNKNOWN_CAPABILITY:" + item for item in evidence.unknown_capabilities)
    return {"rule_reference": reference, "execution_ready": False,
            "execution_readiness": row["execution_readiness"],
            "dependency_closure": row["dependency_closure"],
            "exception_closure": row["exception_closure"],
            "blocking_references": row["unresolved_dependencies"] + row["unprojected_exceptions"],
            "blockers": list(dict.fromkeys(blockers)), "decision": "DENIED_DESIGN_ONLY"}


def evaluate_activation_requirements(conditions):
    """Conjunction proof of the eleven requirements, with no activation output.

    A structural fictional fixture can satisfy all eleven booleans. Its result
    still denies activation. Real design assessment derives these conditions
    from bound records below rather than accepting a human prose assertion.
    """
    if not isinstance(conditions, Mapping) or set(conditions) != set(ACTIVATION_REQUIREMENTS):
        _fail("all eleven activation requirements must be explicit")
    if any(type(value) is not bool for value in conditions.values()):
        _fail("activation conditions require strict booleans")
    failed = [name for name in ACTIVATION_REQUIREMENTS if not conditions[name]]
    return {"activation_denied": True, "status": "DENIED_DESIGN_ONLY",
            "requirements_satisfied": not failed, "failed_requirements": failed,
            "blockers": ["DESIGN_ONLY_NOT_AN_ACTIVATION_AUTHORITY", *failed]}


def assess_activation(projection, review, matrix, design, *, claimed_conditions=None):
    """Derive current evidence from immutable records, then apply all gates.

    Optional claims can only withhold evidence, never manufacture owner approval,
    primitives, a complete review, or closure. No runtime profile is returned.
    """
    from .contracts import (FoundationalProjectionReview, RealRulesCapabilityMatrix,
                            RealRulesExecutionProfileDesign)
    _projection(projection)
    for value, cls in ((review, FoundationalProjectionReview), (matrix, RealRulesCapabilityMatrix),
                       (design, RealRulesExecutionProfileDesign)):
        if not isinstance(value, cls):
            _fail("typed design evidence required")
        value.verify()
    bindings_match = (design.required_projection_review_id == review.identity
                      and matrix.projection_review_id == review.identity
                      and design.capability_matrix_id == matrix.identity
                      and design.foundational_projection_id == projection.identity)
    if not bindings_match:
        _fail("execution design evidence identities differ")
    from .builder import required_rule_set_identity
    if design.required_rule_set_id != required_rule_set_identity(review):
        _fail("required rule-set identity differs from the reviewed requirements")
    rules = review.to_dict()["rules"]
    anchors = {row["rule_reference"]: row["source_anchor"] for row in projection.to_dict()["rules"]}
    if any(row["source_anchor"] != anchors[row["rule_reference"]] for row in rules):
        _fail("reviewed source anchors differ from the exact foundational projection")
    conditions = {
        "source_artifact_verified": design.to_dict()["source_binding"] == SOURCE_BINDING,
        "projection_package_verified": design.foundational_projection_id == PROJECTION_ID,
        "projection_review_complete": review.review_status == "REVIEWED_FOR_EXECUTION_DESIGN",
        "runtime_used_rules_ready": all(row["execution_ready"] for row in rules if row["direct_runtime_relevance"] != "NONE"),
        "dependency_closure_satisfied": all(row["dependency_closure"] == "CLOSED" for row in rules if row["direct_runtime_relevance"] != "NONE"),
        "exception_closure_satisfied": all(row["exception_closure"] == "CLOSED" for row in rules if row["direct_runtime_relevance"] != "NONE"),
        "semantic_primitives_implemented": False,
        "capability_matrix_matches_implementation": all(not row["execution_supported"] and not row["implementation_primitive_available"] for row in matrix.to_dict()["capabilities"]),
        "exact_rules_release_pinned": design.source_binding["effective_date"] == SOURCE_BINDING["effective_date"],
        "deterministic_test_vectors_passed": False,
        "explicit_owner_activation": False,
    }
    if claimed_conditions is not None:
        evaluate_activation_requirements(claimed_conditions)
        conditions = {name: conditions[name] and claimed_conditions[name] for name in ACTIVATION_REQUIREMENTS}
    return conditions, evaluate_activation_requirements(conditions)
