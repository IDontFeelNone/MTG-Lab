"""Read-only closure evidence composed from two distinct projection identities.

These reports inspect only validated project-authored metadata. A resolved
reference is an available source-anchored description, never permission to run
real rules. No report constructs a gameplay snapshot or an execution profile.
"""
from __future__ import annotations

from dataclasses import dataclass
import json
from typing import ClassVar, Mapping, Any

from evidence.contracts import Contract, deterministic_json, sha256_identity
from gameplay_rules.errors import GameplayContractError
from gameplay_rules.execution_design.builder import build_records
from gameplay_rules.execution_design.package import package_manifest as design_manifest
from gameplay_rules.execution_design.contracts import PROJECTION_ID, PROJECTION_PACKAGE_ID
from .contracts import FoundationalProjection, _json, _freeze
from .dependency_contracts import DependencyProjection
from .package import package_manifest as foundational_manifest

CANONICAL_MAIN = "71652074fe5640d5b2cb4780c63f6b8bab5642d6"
DESIGN_PACKAGE_ID = "sha256:f20d51ee190b4b23789208d0ae4bfa092d72aa23086fb01251d67b324ddb0687"
DESIGN_REVIEW_ID = "sha256:f1b57c6465e5a9dfcb96ec241e5e83d12cbbdd1d5b47546090c4d8ac44a2b104"
HISTORICAL_ACQUISITION_ID = "sha256:669d7db9ebcaf97853058fd62f408ce3c6596d5dae0ee72ff39d2ba9df56bb53"

_BOUNDARY_FLAGS = {
    "execution_authorized": False, "real_rules_executable": False,
    "source_body_retained": False, "oracle_ingested": False,
    "source_policy_clearance": "not_granted", "owner_execution_approval": "NOT_GRANTED",
}


def _fail(message="invalid dependency report"):
    raise GameplayContractError("foundational_dependency_report", message)


def _unique(values):
    return list(dict.fromkeys(values))


def _json_pairs(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            _fail("duplicate JSON key")
        result[key] = value
    return result


def _nonfinite(_value):
    _fail("non-finite JSON number")


def _validate_review_boundaries(value):
    """Reject execution promotion even when a caller recomputes report hashes."""
    required = {
        "execution_authorized": False, "real_rules_executable": False,
        "semantically_closed_for_execution": False, "execution_ready": False,
        "implementation_primitive_available": False, "real_snapshot_instantiated": False,
        "real_profile_activated": False, "mutated": False,
        "semantic_closure": "SEMANTIC_CLOSURE_OPEN",
        "dependency_closure": "SEMANTIC_CLOSURE_OPEN", "execution_status": "EXECUTION_BLOCKED",
        "overall_execution_readiness": "BLOCKED", "readiness_code": "REAL_EXECUTION_PROFILE_NOT_READY",
        "real_execution_primitives_available": [], "authorized": False,
        "original_projected_rule_count": 20, "new_projected_rule_count": 12,
        "total_projected_rule_count": 32, "direct_references_resolved_count": 5,
    }
    if isinstance(value, dict):
        for key, item in value.items():
            if key in required and deterministic_json(item) != deterministic_json(required[key]):
                _fail("fixed semantic, scope, or execution boundary violated: " + key)
            _validate_review_boundaries(item)
    elif isinstance(value, list):
        for item in value:
            _validate_review_boundaries(item)


@dataclass(frozen=True)
class DependencyReport(Contract):
    """Immutable content-addressed envelope; package loading recomputes findings."""

    _payload: Mapping[str, Any]
    SCHEMA: ClassVar[str]
    ID_FIELD: ClassVar[str]
    BODY_FIELDS: ClassVar[frozenset[str]]

    def __post_init__(self):
        try:
            value = _json(self._payload)
            if set(value) != self.BODY_FIELDS | set(_BOUNDARY_FLAGS) | {"schema_version", self.ID_FIELD}:
                _fail("unexpected report fields")
            if value["schema_version"] != self.SCHEMA:
                _fail("unexpected report schema")
            if any(type(value[key]) is not type(expected) or value[key] != expected
                   for key, expected in _BOUNDARY_FLAGS.items()):
                _fail("fixed review and execution boundaries required")
            if value["game_id"] != "magic" or value["canonical_base"] != CANONICAL_MAIN:
                _fail("unexpected game or canonical base")
            if value["original_projection_id"] != PROJECTION_ID or value["original_package_id"] != PROJECTION_PACKAGE_ID:
                _fail("original projection identity must remain unchanged")
            if value["execution_design_package_id"] != DESIGN_PACKAGE_ID:
                _fail("merged design package identity must remain unchanged")
            _validate_review_boundaries(value)
            content = {key: item for key, item in value.items() if key != self.ID_FIELD}
            if value[self.ID_FIELD] != "sha256:" + sha256_identity({"domain": self.SCHEMA, "content": content}):
                _fail("report identity does not match its contents")
            object.__setattr__(self, "_payload", _freeze(value))
        except GameplayContractError:
            raise
        except (ValueError, TypeError, KeyError, RecursionError):
            _fail()

    @classmethod
    def create(cls, body):
        value = _json(body)
        for key, expected in _BOUNDARY_FLAGS.items():
            if key in value and (type(value[key]) is not type(expected) or value[key] != expected):
                _fail("caller cannot override review and execution boundaries")
        value.update(_BOUNDARY_FLAGS)
        value["schema_version"] = cls.SCHEMA
        value[cls.ID_FIELD] = "sha256:" + sha256_identity({"domain": cls.SCHEMA, "content": value})
        return cls(value)

    @classmethod
    def from_dict(cls, value):
        return cls(value)

    @classmethod
    def from_json(cls, value):
        try:
            return cls.from_dict(json.loads(value, object_pairs_hook=_json_pairs, parse_constant=_nonfinite))
        except GameplayContractError:
            raise
        except (ValueError, TypeError, UnicodeError, RecursionError):
            _fail("malformed report JSON")

    @property
    def identity(self):
        return self._payload[self.ID_FIELD]

    def to_dict(self):
        return _json(self._payload)

    def serialize(self):
        return deterministic_json(self.to_dict())

    def verify(self):
        type(self).from_dict(self.to_dict())
        return self

    def __getattr__(self, name):
        payload = object.__getattribute__(self, "_payload")
        if name in payload:
            return payload[name]
        raise AttributeError(name)


_COMMON_FIELDS = frozenset({
    "game_id", "canonical_base", "original_package_id", "original_projection_id",
    "dependency_projection_id", "execution_design_package_id", "source_binding",
})


@dataclass(frozen=True)
class DirectClosureReview(DependencyReport):
    SCHEMA: ClassVar[str] = "gameplay-cr-direct-foundational-closure-review-v1"
    ID_FIELD: ClassVar[str] = "closure_review_id"
    BODY_FIELDS: ClassVar[frozenset[str]] = _COMMON_FIELDS | frozenset({
        "status", "review_state", "original_unresolved_references", "direct_resolutions",
        "direct_references_resolved_count", "newly_discovered_boundaries",
        "remaining_unresolved_rules", "semantic_closure", "execution_status", "limitations",
    })


@dataclass(frozen=True)
class CompositeCoverage(DependencyReport):
    SCHEMA: ClassVar[str] = "gameplay-cr-foundational-composite-coverage-v1"
    ID_FIELD: ClassVar[str] = "composite_coverage_id"
    BODY_FIELDS: ClassVar[frozenset[str]] = _COMMON_FIELDS | frozenset({
        "view_kind", "closure_review_id", "original_projected_rule_count", "new_projected_rule_count",
        "total_projected_rule_count", "projected_references", "projection_components",
        "direct_dependencies_resolved", "remaining_unresolved_rules", "open_exception_families",
        "newly_discovered_boundaries", "capabilities_affected", "semantic_closure", "execution_status",
        "historical_acquisition_identity", "limitations",
    })


@dataclass(frozen=True)
class ExecutionReadinessReassessment(DependencyReport):
    SCHEMA: ClassVar[str] = "gameplay-cr-dependency-execution-readiness-reassessment-v1"
    ID_FIELD: ClassVar[str] = "execution_readiness_reassessment_id"
    BODY_FIELDS: ClassVar[frozenset[str]] = _COMMON_FIELDS | frozenset({
        "status", "closure_review_id", "composite_coverage_id", "prior_projection_review_id",
        "prior_execution_profile_design_id", "prior_execution_readiness_id", "target_profile_id",
        "affected_rules", "capabilities_affected", "remaining_unresolved_rules", "open_exception_families",
        "newly_discovered_boundaries", "overall_execution_readiness", "readiness_code",
        "real_execution_primitives_available", "real_snapshot_instantiated", "real_profile_activated",
        "deterministic_real_runtime_vectors", "blockers", "next_milestone", "limitations",
    })


def _validate_inputs(projection, foundational_projection, design_records):
    if not isinstance(projection, DependencyProjection) or not isinstance(foundational_projection, FoundationalProjection):
        _fail("typed validated projections required")
    projection.verify()
    foundational_projection.verify()
    original_raw = (foundational_projection.serialize() + "\n").encode("utf-8")
    if (foundational_projection.identity != PROJECTION_ID or
            foundational_manifest(foundational_projection, original_raw)["package_id"] != PROJECTION_PACKAGE_ID):
        _fail("exact merged foundational projection required")
    expected = build_records(foundational_projection)
    if set(design_records) != set(expected):
        _fail("complete merged execution-design evidence required")
    for name in expected:
        if type(design_records[name]) is not type(expected[name]):
            _fail("typed execution-design evidence required")
        design_records[name].verify()
        if design_records[name].to_dict() != expected[name].to_dict():
            _fail("execution-design findings do not reproduce")
    raw = {name: (record.serialize() + "\n").encode("utf-8") for name, record in design_records.items()}
    if design_manifest(design_records, raw)["package_id"] != DESIGN_PACKAGE_ID:
        _fail("exact merged execution-design package required")
    if design_records["projection-review.json"].identity != DESIGN_REVIEW_ID:
        _fail("exact merged projection review required")


def _boundaries(projection):
    """Group authored unresolved boundaries without expanding their contents."""
    grouped = {}
    for rule in projection.to_dict()["rules"]:
        for boundary in rule["unresolved_dependencies"]:
            key = boundary["reference"], boundary["classification"], boundary["status"]
            if key not in grouped:
                grouped[key] = {**boundary, "required_by": []}
            grouped[key]["required_by"].append(rule["rule_reference"])
    return list(grouped.values())


def _families(original):
    groups = {}
    for edge in original.to_dict()["graph"]["edges"]:
        if edge["status"] == "UNPROJECTED_EXCEPTION":
            groups.setdefault(edge["from_reference"], []).append(edge["to_reference"])
    return {reference: {"status": "UNPROJECTED", "references": references,
                        "semantic_closure": "SEMANTIC_CLOSURE_OPEN"}
            for reference, references in groups.items()}


def _adjacency(original, projection):
    graph = {}
    for edge in original.to_dict()["graph"]["edges"]:
        graph.setdefault(edge["from_reference"], []).append(edge["to_reference"])
    for edge in projection.to_dict()["graph"]["edges"]:
        graph.setdefault(edge["from_reference"], []).append(edge["to_reference"])
    graph["407"] = [row["rule_reference"] for row in projection.to_dict()["rules"]
                    if row["rule_reference"].startswith("407.")]
    return graph


def _reachable(graph, start):
    found, pending = set(), [start]
    while pending:
        reference = pending.pop()
        if reference in found:
            continue
        found.add(reference)
        pending.extend(graph.get(reference, ()))
    return found


def _recommendation(families, matrix):
    candidates = []
    names = {"109.4": "Object-Control Exception Family Projection",
             "400.7": "Zone-Change Identity Exception Family Projection"}
    for family, finding in families.items():
        blockers = set(finding["references"])
        affected = [row["capability_id"] for row in matrix["capabilities"]
                    if blockers.intersection(row["blocking_references"])]
        candidates.append({"candidate": names[family], "family": family,
            "known_unprojected_rule_count": len(blockers), "affected_capabilities": affected,
            "scope_size_known": True})
    # Choose a bounded, evidenced family; newly exposed 613 has no reviewed
    # coherent allowlist, and primitive contracts lack semantic closure proof.
    eligible = [row for row in candidates if row["affected_capabilities"]]
    chosen = min(eligible, key=lambda row: (row["known_unprojected_rule_count"], row["family"]))
    return {"candidate": chosen["candidate"], "authorized": False,
        "rationale": (
            f"All five original direct reference gaps are now represented. {chosen['family']} "
            f"still has {chosen['known_unprojected_rule_count']} unprojected exceptions blocking "
            f"{', '.join(chosen['affected_capabilities'])}; it is the smaller known coherent exception "
            "family in retained evidence. The other family is larger, 613 lacks a bounded reviewed "
            "dependency scope, and complete semantic closure does not yet justify primitive contracts."
        ),
        "evaluated_exception_candidates": candidates,
        "other_candidates": [
            {"candidate": "Ability / Continuous-Effect Dependency Design", "scope_size_known": False,
             "reason_deferred": "613 is newly unresolved; no coherent bounded dependency scope has been reviewed."},
            {"candidate": "Core State Semantic Primitive Contracts", "reason_deferred": "Complete dependency and exception closure remains unproven."},
        ]}


def build_dependency_reports(projection, foundational_projection, design_records):
    """Derive three append-only reports from exact validated retained evidence."""
    _validate_inputs(projection, foundational_projection, design_records)
    original = foundational_projection.to_dict()
    dependency = projection.to_dict()
    references = [row["rule_reference"] for row in dependency["rules"]]
    original_references = [row["rule_reference"] for row in original["rules"]]
    if set(references).intersection(original_references) or len(set(references + original_references)) != 32:
        _fail("two distinct source-unit sets totaling exactly 32 are required")
    prior_unresolved = [node["rule_reference"] for node in original["graph"]["nodes"] if node["status"] == "UNRESOLVED"]
    boundary_rows = _boundaries(projection)
    unresolved_rules = _unique(row["reference"] for row in boundary_rows if row["classification"] == "UNRESOLVED_RULE")
    graph = _adjacency(foundational_projection, projection)
    resolutions = []
    for reference in prior_unresolved:
        evidence = ([item for item in references if item.startswith("407.")]
                    if reference == "407" else
                    [item for item in references if item == reference or
                     item.startswith(reference) and item[len(reference):].isalpha()])
        if not evidence or reference == "407" and evidence != ["407.1", "407.2", "407.3", "407.4"]:
            _fail("original direct reference lacks bounded projection evidence")
        dependents = [edge["from_reference"] for edge in original["graph"]["edges"]
                      if edge["to_reference"] == reference and edge["status"] == "UNRESOLVED"]
        resolutions.append({"reference": reference, "status": "DIRECT_REFERENCE_RESOLVED",
            "evidence_references": evidence, "dependency_projection_id": projection.identity,
            "source_dependents": dependents, "semantic_closure": "SEMANTIC_CLOSURE_OPEN",
            "semantically_closed_for_execution": False, "execution_status": "EXECUTION_BLOCKED"})
    common = {"game_id": "magic", "canonical_base": CANONICAL_MAIN,
        "original_package_id": PROJECTION_PACKAGE_ID, "original_projection_id": PROJECTION_ID,
        "dependency_projection_id": projection.identity, "execution_design_package_id": DESIGN_PACKAGE_ID,
        "source_binding": dependency["source_binding"]}
    closure = DirectClosureReview.create({**common,
        "status": "DIRECT_FOUNDATIONAL_DEPENDENCIES_PROJECTED", "review_state": "PROJECTED_FOR_REVIEW",
        "original_unresolved_references": prior_unresolved, "direct_resolutions": resolutions,
        "direct_references_resolved_count": len(resolutions), "newly_discovered_boundaries": boundary_rows,
        "remaining_unresolved_rules": unresolved_rules, "semantic_closure": "SEMANTIC_CLOSURE_OPEN",
        "execution_status": "EXECUTION_BLOCKED",
        "limitations": ["Direct resolution records descriptions and anchors; it does not close execution semantics.",
                        "407 is represented by exactly four selected source units, without a separately projected 407 heading.",
                        "No unresolved boundary is recursively projected or interpreted."]})
    resolved = {row["reference"] for row in resolutions}
    family_rows = _families(foundational_projection)
    matrix = design_records["capability-matrix.json"].to_dict()
    capabilities = []
    for row in matrix["capabilities"]:
        removed = [reference for reference in row["blocking_references"] if reference in resolved]
        if not removed:
            continue
        reachable = set().union(*(_reachable(graph, reference) for reference in row["supporting_rules"]))
        downstream = [boundary for boundary in boundary_rows if boundary["reference"] in reachable]
        capabilities.append({"capability_id": row["capability_id"], "direct_dependencies_resolved": removed,
            "remaining_unprojected_exceptions": [reference for reference in row["blocking_references"] if reference not in resolved],
            "new_downstream_boundaries": downstream,
            "remaining_unresolved_rules": [reference for reference in unresolved_rules if reference in reachable],
            "semantic_closure": "SEMANTIC_CLOSURE_OPEN", "execution_status": "EXECUTION_BLOCKED",
            "implementation_primitive_available": row["implementation_primitive_available"],
            "required_semantic_primitives": row["required_semantic_primitives"]})
    composite = CompositeCoverage.create({**common,
        "view_kind": "DERIVED_READ_ONLY_TWO_PROJECTION_VIEW", "closure_review_id": closure.identity,
        "original_projected_rule_count": len(original_references), "new_projected_rule_count": len(references),
        "total_projected_rule_count": len(original_references) + len(references),
        "projected_references": original_references + references,
        "projection_components": [
            {"projection_id": foundational_projection.identity, "package_id": PROJECTION_PACKAGE_ID,
             "projected_references": original_references, "mutated": False},
            {"projection_id": projection.identity, "package_binding": "THIS_ENCLOSING_DEPENDENCY_PACKAGE",
             "projected_references": references, "mutated": False}],
        "direct_dependencies_resolved": [row["reference"] for row in resolutions],
        "remaining_unresolved_rules": unresolved_rules, "open_exception_families": family_rows,
        "newly_discovered_boundaries": boundary_rows, "capabilities_affected": capabilities,
        "semantic_closure": "SEMANTIC_CLOSURE_OPEN", "execution_status": "EXECUTION_BLOCKED",
        "historical_acquisition_identity": HISTORICAL_ACQUISITION_ID,
        "limitations": ["This view preserves separate projection identities; it is not a replacement projection or runtime input.",
                        "Only known graph reachability is assessed; complete semantic closure remains unknown.",
                        "Nineteen deferred exception bodies and their dependencies are not inspected."]})
    prior_rows = {row["rule_reference"]: row for row in design_records["projection-review.json"].to_dict()["rules"]}
    affected = []
    for reference in ("101.1", "101.2", "101.2a", "108.3", "108.4", "110.2"):
        prior = prior_rows[reference]
        reach = _reachable(graph, reference)
        remaining = [item for item in unresolved_rules if item in reach]
        affected.append({"rule_reference": reference,
            "previous_unresolved_dependencies": prior["unresolved_dependencies"],
            "direct_dependencies_resolved": [item for item in prior["unresolved_dependencies"] if item in resolved],
            "original_direct_reference_status": "DIRECT_REFERENCE_RESOLVED",
            "remaining_original_unresolved_dependencies": [item for item in prior["unresolved_dependencies"] if item not in resolved],
            "remaining_unresolved_rules": remaining,
            "new_downstream_boundaries": [row for row in boundary_rows if row["reference"] in reach],
            "known_dependency_closure": "OPEN" if remaining else "CLOSED_FOR_RECORDED_RULE_REFERENCES_ONLY",
            "dependency_closure": "SEMANTIC_CLOSURE_OPEN", "semantically_closed_for_execution": False,
            "execution_status": "EXECUTION_BLOCKED", "execution_ready": False,
            "required_unimplemented_semantic_primitives": prior["unsupported_required_semantic_primitives"],
            "remaining_unknown_semantic_contexts": prior["unknown_semantic_contexts"]})
    prior_readiness = design_records["readiness.json"].to_dict()
    design = design_records["execution-profile-design.json"].to_dict()
    blockers = ["COMPLETE_SEMANTIC_CLOSURE_UNKNOWN", "REAL_EXECUTION_PRIMITIVES_ABSENT",
        "DETERMINISTIC_REAL_RUNTIME_VECTORS_ABSENT", "OWNER_ACTIVATION_NOT_GRANTED", "CARD_EFFECT_SEMANTICS_ABSENT"]
    blockers += ["UNRESOLVED_RULE:" + item for item in unresolved_rules]
    blockers += ["UNPROJECTED_EXCEPTION:" + item for row in family_rows.values() for item in row["references"]]
    blockers += [row["classification"] + ":" + row["reference"] for row in boundary_rows
                 if row["classification"] in {"EXTERNAL_POLICY", "UNSUPPORTED_VARIANT", "FUTURE_SEMANTIC_PRIMITIVE", "OUT_OF_SCOPE"}]
    reassessment = ExecutionReadinessReassessment.create({**common,
        "status": "APPEND_ONLY_REASSESSMENT_FOR_REVIEW", "closure_review_id": closure.identity,
        "composite_coverage_id": composite.identity, "prior_projection_review_id": DESIGN_REVIEW_ID,
        "prior_execution_profile_design_id": design_records["execution-profile-design.json"].identity,
        "prior_execution_readiness_id": design_records["readiness.json"].identity,
        "target_profile_id": design["target_profile_id"], "affected_rules": affected,
        "capabilities_affected": capabilities, "remaining_unresolved_rules": unresolved_rules,
        "open_exception_families": family_rows, "newly_discovered_boundaries": boundary_rows,
        "overall_execution_readiness": prior_readiness["overall_execution_readiness"],
        "readiness_code": prior_readiness["readiness_code"], "real_execution_primitives_available": [],
        "real_snapshot_instantiated": False, "real_profile_activated": False,
        "deterministic_real_runtime_vectors": "ABSENT", "blockers": _unique(blockers),
        "next_milestone": _recommendation(family_rows, matrix),
        "limitations": ["This append-only assessment does not overwrite or approve the merged execution design.",
                        "Resolution of the original dependency references removes no missing runtime primitive or activation requirement.",
                        "613 remains an uninterpreted downstream dependency; ability-modification execution remains blocked.",
                        "Tournament policy and applicable law are external authority boundaries; no policy document is ingested or legal conclusion issued."]})
    return {"closure-review.json": closure, "composite-coverage.json": composite,
            "execution-readiness-reassessment.json": reassessment}
