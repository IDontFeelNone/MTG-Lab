"""Read-only exception, capability, and composite evidence for object control.

Only validated project metadata is composed here. A source-unit description is
neither executable semantics nor permission to activate the future profile.
"""
from __future__ import annotations

from dataclasses import dataclass
import json
from typing import Any, ClassVar, Mapping

from evidence.contracts import Contract, deterministic_json, sha256_identity
from gameplay_rules.errors import GameplayContractError
from gameplay_rules.execution_design.contracts import PROJECTION_ID, PROJECTION_PACKAGE_ID
from .contracts import FoundationalProjection, _freeze, _json
from .dependency_package import package_manifest as dependency_manifest
from .dependency_reports import (
    DESIGN_PACKAGE_ID, DESIGN_REVIEW_ID, HISTORICAL_ACQUISITION_ID,
    _families, _unique, _validate_inputs, build_dependency_reports,
)
from .object_control_contracts import ObjectControlProjection, SourceAnomaly
from .object_control_scope import SELECTED_REFERENCES

CANONICAL_MAIN = "f1b72325ec4c84f20063da1945b1f8b7f8721970"
DEPENDENCY_PROJECTION_ID = "sha256:23c7882d3291c0b5bccadff2a4c0422d5680412308cbff2cd0137401fd4fc7f1"
DEPENDENCY_PACKAGE_ID = "sha256:684727e763c228c5eebaacbbde9e19de631f168252f8f592a600ee0a60640a3a"

_FLAGS = {
    "execution_authorized": False, "real_rules_executable": False,
    "source_body_retained": False, "oracle_ingested": False,
    "source_policy_clearance": "not_granted", "owner_execution_approval": "NOT_GRANTED",
}
_COMMON = frozenset({
    "game_id", "canonical_base", "foundational_projection_id", "foundational_package_id",
    "dependency_projection_id", "dependency_package_id", "execution_design_package_id",
    "object_control_projection_id", "source_anomaly_id", "source_binding",
})


def _fail(message="invalid object-control report"):
    raise GameplayContractError("object_control_report", message)


def _pairs(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            _fail("duplicate JSON field")
        result[key] = value
    return result


def _nonfinite(_value):
    _fail("non-finite JSON value")


def _boundaries(value):
    """Reject scope or execution promotion, even with recomputed identities."""
    fixed = {
        **_FLAGS, "execution_ready": False, "execution_supported": False,
        "exception_semantics_closed": False, "semantically_closed_for_execution": False,
        "implementation_primitive_available": False, "real_snapshot_instantiated": False,
        "real_profile_activated": False, "mutated": False, "authorized": False,
        "correction_applied": False, "complete_control_semantics": "UNKNOWN",
        "required_primitives_available": False, "intent_inferred": False,
        "subrule_validity_inferred": False,
        "dependency_closure": "OPEN", "semantic_closure": "SEMANTIC_CLOSURE_OPEN",
        "execution_status": "EXECUTION_BLOCKED", "overall_execution_readiness": "BLOCKED",
        "readiness_code": "REAL_EXECUTION_PROFILE_NOT_READY",
        "real_execution_primitives_available": [],
        "foundational_projected_rule_count": 20, "dependency_projected_rule_count": 12,
        "object_control_projected_rule_count": 7, "total_projected_rule_count": 39,
        "selected_rule_count": 7,
    }
    if isinstance(value, dict):
        for key, item in value.items():
            if key in fixed and deterministic_json(item) != deterministic_json(fixed[key]):
                _fail("fixed scope, review, or execution boundary violated: " + key)
            _boundaries(item)
    elif isinstance(value, list):
        for item in value:
            _boundaries(item)


@dataclass(frozen=True)
class ObjectControlReport(Contract):
    """Immutable, domain-separated report; package loading recomputes findings."""

    _payload: Mapping[str, Any]
    SCHEMA: ClassVar[str]
    ID_FIELD: ClassVar[str]
    BODY_FIELDS: ClassVar[frozenset[str]]

    def __post_init__(self):
        try:
            value = _json(self._payload)
            if set(value) != self.BODY_FIELDS | set(_FLAGS) | {"schema_version", self.ID_FIELD}:
                _fail("unexpected report fields")
            if value["schema_version"] != self.SCHEMA:
                _fail("unexpected report schema")
            for key, expected in {
                **_FLAGS, "game_id": "magic", "canonical_base": CANONICAL_MAIN,
                "foundational_projection_id": PROJECTION_ID,
                "foundational_package_id": PROJECTION_PACKAGE_ID,
                "dependency_projection_id": DEPENDENCY_PROJECTION_ID,
                "dependency_package_id": DEPENDENCY_PACKAGE_ID,
                "execution_design_package_id": DESIGN_PACKAGE_ID,
            }.items():
                if type(value[key]) is not type(expected) or value[key] != expected:
                    _fail("exact prior identities and fixed boundaries required: " + key)
            _boundaries(value)
            content = {key: item for key, item in value.items() if key != self.ID_FIELD}
            expected = "sha256:" + sha256_identity({"domain": self.SCHEMA, "content": content})
            if value[self.ID_FIELD] != expected:
                _fail("report content identity mismatch")
            object.__setattr__(self, "_payload", _freeze(value))
        except GameplayContractError:
            raise
        except (ValueError, TypeError, KeyError, RecursionError):
            _fail()

    @classmethod
    def create(cls, body):
        value = _json(body)
        for key, expected in _FLAGS.items():
            if key in value and (type(value[key]) is not type(expected) or value[key] != expected):
                _fail("caller cannot override fixed boundaries")
        value.update(_FLAGS)
        value["schema_version"] = cls.SCHEMA
        value[cls.ID_FIELD] = "sha256:" + sha256_identity({"domain": cls.SCHEMA, "content": value})
        return cls(value)

    @classmethod
    def from_dict(cls, value):
        return cls(value)

    @classmethod
    def from_json(cls, value):
        try:
            return cls.from_dict(json.loads(value, object_pairs_hook=_pairs, parse_constant=_nonfinite))
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


@dataclass(frozen=True)
class FamilyClosureReview(ObjectControlReport):
    SCHEMA: ClassVar[str] = "gameplay-cr-object-control-family-closure-review-v1"
    ID_FIELD: ClassVar[str] = "family_closure_review_id"
    BODY_FIELDS: ClassVar[frozenset[str]] = _COMMON | frozenset({
        "status", "review_state", "parent_reference", "prior_unprojected_exceptions",
        "exception_findings", "direct_family_coverage", "parent_reassessment",
        "newly_unresolved_rules", "new_boundaries", "dependency_graph",
        "source_quality_observation", "semantic_closure", "execution_status", "limitations",
    })


@dataclass(frozen=True)
class ControlReadinessReassessment(ObjectControlReport):
    SCHEMA: ClassVar[str] = "gameplay-cr-object-control-readiness-reassessment-v1"
    ID_FIELD: ClassVar[str] = "control_readiness_reassessment_id"
    BODY_FIELDS: ClassVar[frozenset[str]] = _COMMON | frozenset({
        "status", "family_closure_review_id", "prior_projection_review_id",
        "prior_capability_matrix_id", "prior_dependency_closure_review_id",
        "prior_dependency_reassessment_id", "target_profile_id", "affected_rules",
        "control_dimensions", "prior_control_blockers", "direct_reference_gaps_now_represented",
        "newly_unresolved_rules", "remaining_unresolved_rules", "unsupported_subsystems",
        "required_semantic_primitives", "real_execution_primitives_available",
        "complete_control_semantics", "dependency_closure", "semantic_closure",
        "overall_execution_readiness", "readiness_code", "execution_status",
        "real_snapshot_instantiated", "real_profile_activated", "blockers",
        "next_milestone", "limitations",
    })


@dataclass(frozen=True)
class ObjectControlCompositeCoverage(ObjectControlReport):
    SCHEMA: ClassVar[str] = "gameplay-cr-object-control-composite-coverage-v1"
    ID_FIELD: ClassVar[str] = "composite_coverage_id"
    BODY_FIELDS: ClassVar[frozenset[str]] = _COMMON | frozenset({
        "view_kind", "family_closure_review_id", "control_readiness_reassessment_id",
        "foundational_projected_rule_count", "dependency_projected_rule_count",
        "object_control_projected_rule_count", "total_projected_rule_count",
        "projected_references", "projection_components", "direct_dependencies_resolved",
        "represented_exception_families", "remaining_unresolved_rules", "newly_unresolved_rules",
        "open_exception_families", "open_semantic_boundaries", "unsupported_variants",
        "historical_acquisition_identity", "semantic_closure", "execution_status", "limitations",
    })


def _validate_evidence(projection, anomaly, original, design, dependency_records):
    if not isinstance(projection, ObjectControlProjection) or not isinstance(anomaly, SourceAnomaly):
        _fail("typed validated object-control projection and source anomaly required")
    if not isinstance(original, FoundationalProjection):
        _fail("typed merged foundational projection required")
    projection.verify()
    anomaly.verify()
    if not isinstance(dependency_records, Mapping) or set(dependency_records) != {
            "projection.json", "closure-review.json", "composite-coverage.json", "execution-readiness-reassessment.json"}:
        _fail("complete merged dependency evidence required")
    dependency = dependency_records["projection.json"]
    _validate_inputs(dependency, original, design)
    expected = {"projection.json": dependency, **build_dependency_reports(dependency, original, design)}
    if set(dependency_records) != set(expected):
        _fail("complete merged dependency evidence required")
    if any(type(dependency_records[name]) is not type(expected[name]) or
           dependency_records[name].to_dict() != expected[name].to_dict() for name in expected):
        _fail("merged dependency evidence does not reproduce")
    raw = {name: (record.serialize() + "\n").encode("utf-8") for name, record in dependency_records.items()}
    if dependency.identity != DEPENDENCY_PROJECTION_ID or dependency_manifest(dependency_records, raw)["package_id"] != DEPENDENCY_PACKAGE_ID:
        _fail("exact merged dependency projection and package required")
    original_parent = next(row for row in original.to_dict()["rules"] if row["rule_reference"] == "109.4")
    if anomaly.to_dict()["parent_source_anchor"] != {
            **original_parent["source_anchor"], "effective_date": original.to_dict()["source_binding"]["effective_date"]}:
        _fail("anomaly observation must bind the unchanged original parent source span")
    return dependency


def _group_boundaries(projection):
    rows = {}
    for rule in projection.to_dict()["rules"]:
        for boundary in (rule["unresolved_dependencies"] + rule["variant_boundaries"] +
                         rule["required_future_semantic_primitives"]):
            key = (boundary["reference"], boundary["classification"], boundary["status"])
            if key not in rows:
                rows[key] = {**boundary, "required_by": []}
            rows[key]["required_by"].append(rule["rule_reference"])
    return list(rows.values())


def _required_primitives(rule):
    """Preserve both original dependency and newer exception metadata forms."""
    direct = [row["reference"] for row in rule.get("required_future_semantic_primitives", [])]
    inherited = [row["reference"] for row in rule.get("unresolved_dependencies", [])
                 if row["classification"] == "FUTURE_SEMANTIC_PRIMITIVE"]
    return _unique(direct + inherited)


def _next_milestone(families, newly_unresolved, matrix):
    core = [reference for reference in newly_unresolved if reference not in {"901.6", "902.6", "904.7", "905.5"}]
    variants = [reference for reference in newly_unresolved if reference not in core]
    zone = families["400.7"]["references"]
    affected = [row["capability_id"] for row in matrix["capabilities"]
                if set(zone).intersection(row["blocking_references"])]
    candidates = [
        {"candidate": "Core Control Dependency Projection", "unresolved_target_references": core,
         "coherent_source_unit_scope_known": False, "eligible": False,
         "reason": "The discovered 603, 605, and 114 family targets have no reviewed bounded source-unit allowlist; six target references do not measure their coherent source scope."},
        {"candidate": "Zone-Change Identity Exception Family Projection", "unprojected_references": zone,
         "coherent_source_unit_scope_known": True, "known_source_unit_count": len(zone),
         "affected_capabilities": affected, "eligible": bool(zone and affected)},
        {"candidate": "Ability / Continuous-Effect Dependency Design", "unresolved_target_references": ["613"],
         "coherent_source_unit_scope_known": False, "eligible": False,
         "reason": "613 remains an uninterpreted family target without a reviewed bounded dependency scope."},
        {"candidate": "Casual Variant Control Dependency Projection", "unresolved_target_references": variants,
         "coherent_source_unit_scope_known": False, "eligible": False,
         "reason": "Four unsupported variants have no authorized support objective or reviewed coherent dependency scope."},
    ]
    eligible = [row for row in candidates if row["eligible"]]
    if len(eligible) != 1:
        _fail("one evidenced bounded next milestone required")
    selected = eligible[0]
    return {"candidate": selected["candidate"], "authorized": False,
        "rationale": f"Object-control exception references are represented, while their subsystem semantics stay open. The remaining {len(zone)}-unit 400.7 exception family is a finite known direct source scope blocking {', '.join(affected)}. Core control and 613 need scope design before a coherent allowlist can be assessed; casual-variant support has no established objective.",
        "evaluated_candidates": candidates}


def build_object_control_reports(projection, source_anomaly, foundational_projection,
                                 design_records, dependency_records):
    """Compose three append-only reports from exactly the three merged ancestors."""
    dependency = _validate_evidence(projection, source_anomaly, foundational_projection,
                                    design_records, dependency_records)
    original = foundational_projection.to_dict()
    new = projection.to_dict()
    dependent = dependency.to_dict()
    references = [row["rule_reference"] for row in new["rules"]]
    prior_references = [row["rule_reference"] for row in original["rules"]]
    dependency_references = [row["rule_reference"] for row in dependent["rules"]]
    all_references = prior_references + dependency_references + references
    if tuple(references) != SELECTED_REFERENCES or len(set(all_references)) != 39 or len(all_references) != 39:
        _fail("three separate source-unit sets totaling exactly 39 required")
    prior_families = _families(foundational_projection)
    if prior_families["109.4"]["references"] != references:
        _fail("selected exceptions must match the complete retained direct parent family")
    families = {reference: row for reference, row in prior_families.items() if reference != "109.4"}
    boundaries = _group_boundaries(projection)
    newly_unresolved = _unique(row["reference"] for row in boundaries if row["classification"] == "UNRESOLVED_RULE")
    prior_closure = dependency_records["closure-review.json"].to_dict()
    prior_reassessment = dependency_records["execution-readiness-reassessment.json"].to_dict()
    prior_composite = dependency_records["composite-coverage.json"].to_dict()
    remaining = _unique(prior_closure["remaining_unresolved_rules"] + newly_unresolved)
    common = {"game_id": "magic", "canonical_base": CANONICAL_MAIN,
        "foundational_projection_id": foundational_projection.identity, "foundational_package_id": PROJECTION_PACKAGE_ID,
        "dependency_projection_id": dependency.identity, "dependency_package_id": DEPENDENCY_PACKAGE_ID,
        "execution_design_package_id": DESIGN_PACKAGE_ID, "object_control_projection_id": projection.identity,
        "source_anomaly_id": source_anomaly.identity, "source_binding": new["source_binding"]}
    exception_findings = []
    for rule in new["rules"]:
        unresolved = [row["reference"] for row in rule["unresolved_dependencies"]
                      if row["classification"] == "UNRESOLVED_RULE"]
        exception_findings.append({"rule_reference": rule["rule_reference"], "rule_id": rule["rule_id"],
            "domain_classification": rule["domain_classification"], "reference_status": "EXCEPTION_REFERENCE_PROJECTED",
            "unresolved_rules": unresolved, "variant_boundaries": rule["variant_boundaries"],
            "required_future_semantic_primitives": rule["required_future_semantic_primitives"],
            "dependency_closure": "OPEN", "exception_semantics_closed": False,
            "semantic_closure": "SEMANTIC_CLOSURE_OPEN", "execution_ready": False,
            "execution_status": "EXECUTION_BLOCKED"})
    parent = {"rule_reference": "109.4", "original_projection_id": foundational_projection.identity,
        "direct_exception_enumeration": "DIRECT_EXCEPTION_FAMILY_REPRESENTED",
        "projected_exception_references": references, "unprojected_direct_exception_references": [],
        "dependency_closure": "OPEN", "unresolved_rules": newly_unresolved,
        "variant_coverage": "DESCRIBED_BUT_UNSUPPORTED", "required_primitives_available": False,
        "complete_control_semantics": "UNKNOWN", "semantic_closure": "SEMANTIC_CLOSURE_OPEN",
        "execution_ready": False, "execution_status": "EXECUTION_BLOCKED"}
    family = FamilyClosureReview.create({**common,
        "status": "OBJECT_CONTROL_EXCEPTION_FAMILY_PROJECTED", "review_state": "PROJECTED_FOR_REVIEW",
        "parent_reference": "109.4", "prior_unprojected_exceptions": prior_families["109.4"]["references"],
        "exception_findings": exception_findings,
        "direct_family_coverage": {"expected_count": len(references), "projected_count": len(references),
            "references": references, "status": "DIRECT_EXCEPTION_FAMILY_REPRESENTED",
            "exception_semantics_closed": False, "execution_ready": False},
        "parent_reassessment": parent, "newly_unresolved_rules": newly_unresolved,
        "new_boundaries": boundaries, "dependency_graph": new["graph"],
        "source_quality_observation": {"source_anomaly_id": source_anomaly.identity,
            "interpretation": "SOURCE_INCONSISTENCY_RETAINED", "correction_applied": False,
            "effect_on_source_usability": "SOURCE_REMAINS_USABLE",
            "effect_on_control_closure": "EVIDENCE_QUALITY_OBSERVATION_ONLY",
            "intent_inferred": False, "subrule_validity_inferred": False},
        "semantic_closure": "SEMANTIC_CLOSURE_OPEN", "execution_status": "EXECUTION_BLOCKED",
        "limitations": ["Seven reference descriptions close only the known direct enumeration gap.",
            "Unresolved subsystems are neither recursively projected nor interpreted.",
            "The parent remains unchanged in the original package; this is a read-only reassessment.",
            "The source count discrepancy is retained without correction or inference about source intent."]})
    matrix = design_records["capability-matrix.json"].to_dict()
    control = next(row for row in matrix["capabilities"] if row["capability_id"] == "control")
    prior_rule_rows = {row["rule_reference"]: row for row in design_records["projection-review.json"].to_dict()["rules"]}
    lookup = {row["rule_reference"]: row for row in original["rules"] + dependent["rules"] + new["rules"]}
    selected_review = ("108.4", "108.4a", "109.4", "110.2", "110.2a", "111.2", "112.2", *SELECTED_REFERENCES)
    resolved = prior_composite["direct_dependencies_resolved"]
    affected = []
    for reference in selected_review:
        rule = lookup[reference]
        prior = prior_rule_rows.get(reference)
        unresolved = [row["reference"] for row in rule.get("unresolved_dependencies", [])
                      if row["classification"] == "UNRESOLVED_RULE"]
        affected.append({"rule_reference": reference,
            "component_projection_id": (projection.identity if reference in references else
                dependency.identity if reference in dependency_references else foundational_projection.identity),
            "reference_status": "EXCEPTION_REFERENCE_PROJECTED" if reference in references else "PROJECTED_FOR_REVIEW",
            "prior_unresolved_dependencies": prior["unresolved_dependencies"] if prior else [],
            "direct_dependencies_represented": [item for item in (prior["unresolved_dependencies"] if prior else []) if item in resolved],
            "direct_exceptions_represented": references if reference == "109.4" else [],
            "local_unresolved_rules": unresolved,
            "required_semantic_primitives": _unique((prior["required_semantic_primitives"] if prior else []) +
                                                    _required_primitives(rule)),
            "retained_component_limitations": rule["limitations"],
            "current_assessment_limitations": [
                "Retained component limitations describe that component's original review scope; resolved reference gaps are reassessed separately here.",
                "A projected description provides neither complete semantic closure nor an implemented control primitive."],
            "dependency_closure": "OPEN",
            "semantic_closure": "SEMANTIC_CLOSURE_OPEN", "execution_ready": False,
            "execution_status": "EXECUTION_BLOCKED"})
    dimension_scopes = [
        ("ownership", ["108.3", "110.2", "111.2", "112.2", "112.2a"],
         ["game_start_and_outside_game_provenance", "ante_ownership_boundary", "token_creation", "spell_copy_and_casting"]),
        ("permanent_control", ["108.4", "109.4", "110.2", "110.2a"],
         ["entry_control_assignment", "structured_effect_instructions", "later_control_changes"]),
        ("spell_control", ["108.4", "112.2"], ["spell_copy_and_casting", "stack_operations"]),
        ("token_control", ["110.2", "111.2"], ["token_creation", "entry_control_assignment", "token_lifecycle"]),
        ("ability_control", ["109.4a", "109.4b"], ["mana_abilities", "triggered_abilities", "delayed_triggered_abilities", "stack_operations"]),
        ("emblem_control", ["109.4c"], ["emblem_creation", "command_zone_semantics"]),
        ("variant_control", ["109.4d", "109.4e", "109.4f", "109.4g"], ["Planechase", "Vanguard", "Archenemy", "Conspiracy Draft"]),
        ("control_change_and_effect_semantics", ["110.2a", "113.10", "113.10c"], ["card_effect_interpretation", "continuous_effect_control_interactions", "613"]),
    ]
    dimensions = [{"dimension": name, "supporting_projected_references": scope,
        "descriptive_coverage": "PARTIAL", "open_semantic_boundaries": open_boundaries,
        "dependency_closure": "OPEN", "semantic_closure": "SEMANTIC_CLOSURE_OPEN",
        "execution_supported": False, "implementation_primitive_available": False,
        "execution_status": "EXECUTION_BLOCKED"} for name, scope, open_boundaries in dimension_scopes]
    dimension_references = _unique(reference for _name, scope, _boundaries in dimension_scopes for reference in scope)
    primitives = _unique(control["required_semantic_primitives"] +
        [primitive for reference in dimension_references for primitive in _required_primitives(lookup[reference])])
    unsupported = _unique(["mana_abilities", "triggered_abilities", "delayed_triggered_abilities", "emblems",
        "Planechase", "Vanguard", "Archenemy", "Conspiracy Draft"])
    blockers = ["COMPLETE_CONTROL_SEMANTICS_UNKNOWN", "REAL_EXECUTION_PRIMITIVES_ABSENT",
        "CARD_EFFECT_SEMANTICS_ABSENT", "DETERMINISTIC_REAL_RUNTIME_VECTORS_ABSENT", "OWNER_ACTIVATION_NOT_GRANTED"]
    blockers += ["UNRESOLVED_RULE:" + reference for reference in remaining]
    blockers += ["UNSUPPORTED_SUBSYSTEM:" + item for item in unsupported]
    blockers += ["UNPROJECTED_EXCEPTION:" + reference for row in families.values() for reference in row["references"]]
    reassessment = ControlReadinessReassessment.create({**common,
        "status": "APPEND_ONLY_CONTROL_REASSESSMENT_FOR_REVIEW", "family_closure_review_id": family.identity,
        "prior_projection_review_id": DESIGN_REVIEW_ID,
        "prior_capability_matrix_id": design_records["capability-matrix.json"].identity,
        "prior_dependency_closure_review_id": dependency_records["closure-review.json"].identity,
        "prior_dependency_reassessment_id": dependency_records["execution-readiness-reassessment.json"].identity,
        "target_profile_id": design_records["execution-profile-design.json"].to_dict()["target_profile_id"],
        "affected_rules": affected, "control_dimensions": dimensions,
        "prior_control_blockers": control["blocking_references"],
        "direct_reference_gaps_now_represented": [reference for reference in control["blocking_references"] if reference in set(resolved + references)],
        "newly_unresolved_rules": newly_unresolved, "remaining_unresolved_rules": remaining,
        "unsupported_subsystems": unsupported, "required_semantic_primitives": primitives,
        "real_execution_primitives_available": [], "complete_control_semantics": "UNKNOWN",
        "dependency_closure": "OPEN", "semantic_closure": "SEMANTIC_CLOSURE_OPEN",
        "overall_execution_readiness": prior_reassessment["overall_execution_readiness"],
        "readiness_code": prior_reassessment["readiness_code"], "execution_status": "EXECUTION_BLOCKED",
        "real_snapshot_instantiated": False, "real_profile_activated": False,
        "blockers": blockers, "next_milestone": _next_milestone(families, newly_unresolved, matrix),
        "limitations": ["Availability of every formerly direct control reference does not close its dependencies or implement a control query.",
            "The control dimensions are review findings, without executable ownership, controller, effect, or variant logic.",
            "Dependency closure is open; complete semantic closure remains unknown.",
            "The target execution profile remains design only and inactive."]})
    old_boundaries = prior_composite["newly_discovered_boundaries"]
    composite = ObjectControlCompositeCoverage.create({**common,
        "view_kind": "DERIVED_READ_ONLY_THREE_PROJECTION_VIEW", "family_closure_review_id": family.identity,
        "control_readiness_reassessment_id": reassessment.identity,
        "foundational_projected_rule_count": len(prior_references), "dependency_projected_rule_count": len(dependency_references),
        "object_control_projected_rule_count": len(references), "total_projected_rule_count": len(all_references),
        "projected_references": all_references,
        "projection_components": [
            {"projection_id": foundational_projection.identity, "package_id": PROJECTION_PACKAGE_ID,
             "projected_references": prior_references, "mutated": False},
            {"projection_id": dependency.identity, "package_id": DEPENDENCY_PACKAGE_ID,
             "projected_references": dependency_references, "mutated": False},
            {"projection_id": projection.identity, "package_binding": "THIS_ENCLOSING_OBJECT_CONTROL_PACKAGE",
             "projected_references": references, "mutated": False}],
        "direct_dependencies_resolved": resolved,
        "represented_exception_families": {"109.4": {"references": references,
            "reference_status": "EXCEPTION_REFERENCE_PROJECTED", "exception_semantics_closed": False,
            "execution_ready": False}},
        "remaining_unresolved_rules": remaining, "newly_unresolved_rules": newly_unresolved,
        "open_exception_families": families, "open_semantic_boundaries": old_boundaries + boundaries,
        "unsupported_variants": ["Ante", "Planechase", "Vanguard", "Archenemy", "Conspiracy Draft"],
        "historical_acquisition_identity": HISTORICAL_ACQUISITION_ID,
        "semantic_closure": "SEMANTIC_CLOSURE_OPEN", "execution_status": "EXECUTION_BLOCKED",
        "limitations": ["This derived inventory binds three separate identities; it is not a replacement projection or runtime input.",
            "The new component package ID is bound by the enclosing manifest to avoid a circular content identity.",
            "400.7 exceptions and 613 are retained as open references without inspecting their source contents.",
            "Projected references do not establish complete semantic coverage or permission to execute."]})
    return {"family-closure-review.json": family, "control-readiness-reassessment.json": reassessment,
            "composite-coverage.json": composite}
