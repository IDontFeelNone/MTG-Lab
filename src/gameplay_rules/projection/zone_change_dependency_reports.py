"""Append-only, read-only evidence for the bounded zone-change direct dependencies.

These reports compose validated descriptions. They never supply zone movement,
identity lookup, effect interpretation, or an execution-profile admission path.
"""
from __future__ import annotations

from dataclasses import dataclass
import json
from typing import Any, ClassVar, Mapping

from evidence.contracts import Contract, deterministic_json, sha256_identity
from gameplay_rules.errors import GameplayContractError
from gameplay_rules.execution_design.contracts import PROJECTION_ID, PROJECTION_PACKAGE_ID
from .contracts import _freeze, _json
from .dependency_reports import (
    DESIGN_PACKAGE_ID, HISTORICAL_ACQUISITION_ID, _unique,
)
from .object_control_reports import (
    DEPENDENCY_PROJECTION_ID, DEPENDENCY_PACKAGE_ID,
)
from .zone_change_dependency_contracts import ZoneChangeDependencyProjection, ZONE_CHANGE_PROJECTION_ID, ZONE_CHANGE_PACKAGE_ID
from .zone_change_reports import build_zone_change_reports
from .zone_change_package import package_manifest as zone_change_manifest
from .zone_change_dependency_scope import SELECTED_REFERENCES

PARENT_REFERENCE = "400.7"

CANONICAL_MAIN = "fe6eb895914decb3c0f5fdcda74cd595173cff93"
OBJECT_CONTROL_PROJECTION_ID = "sha256:f4b75e686bfb5202f54818dc4fc9247a49a6e6ef84e2d57f070e990c25b6cce9"
OBJECT_CONTROL_PACKAGE_ID = "sha256:f8cf8053b8bf9e7cc9471520eb02cc3e1e29a716f99a2ac623ec36b40343acab"
OBJECT_CONTROL_ANOMALY_ID = "sha256:4825f549d8e7a59935ac23ab0d5d068e11deb55adcb163bdc18f1f8658c0b74e"

_FLAGS = {
    "execution_authorized": False, "real_rules_executable": False,
    "source_body_retained": False, "oracle_ingested": False,
    "source_policy_clearance": "not_granted", "owner_execution_approval": "NOT_GRANTED",
}
_COMMON = frozenset({
    "game_id", "canonical_base", "foundational_projection_id", "foundational_package_id",
    "dependency_projection_id", "dependency_package_id", "execution_design_package_id",
    "object_control_projection_id", "object_control_package_id", "object_control_source_anomaly_id",
    "zone_change_projection_id", "zone_change_package_id", "zone_change_dependency_projection_id", "source_binding",
})


def _fail(message="invalid zone-change report"):
    raise GameplayContractError("zone_change_dependency_report", message)


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
    """Prevent promotion even if a caller recomputes a report identity."""
    fixed = {
        **_FLAGS, "execution_ready": False, "execution_supported": False,
        "exception_semantics_closed": False, "semantically_closed_for_execution": False,
        "implementation_primitive_available": False, "required_primitives_available": False,
        "real_snapshot_instantiated": False, "real_profile_activated": False,
        "mutated": False, "authorized": False, "correction_applied": False,
        "source_anomaly": False, "missing_source_unit_inferred": False,
        "complete_zone_change_semantics": "UNKNOWN", "dependency_closure": "OPEN",
        "semantic_closure": "SEMANTIC_CLOSURE_OPEN", "execution_status": "EXECUTION_BLOCKED",
        "overall_execution_readiness": "BLOCKED", "readiness_code": "REAL_EXECUTION_PROFILE_NOT_READY",
        "real_execution_primitives_available": [], "foundational_projected_rule_count": 20,
        "dependency_projected_rule_count": 12, "object_control_projected_rule_count": 7,
        "zone_change_projected_rule_count": 12, "zone_change_dependency_projected_rule_count": 12,
        "total_projected_rule_count": 63, "resolved_count": 4,
    }
    if isinstance(value, dict):
        for key, item in value.items():
            if key in fixed and deterministic_json(item) != deterministic_json(fixed[key]):
                _fail("fixed scope or execution boundary violated: " + key)
            _boundaries(item)
    elif isinstance(value, list):
        for item in value:
            _boundaries(item)


@dataclass(frozen=True)
class ZoneChangeDependencyReport(Contract):
    """Immutable domain-separated review; package loading reproduces findings."""

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
                "object_control_projection_id": OBJECT_CONTROL_PROJECTION_ID,
                "object_control_package_id": OBJECT_CONTROL_PACKAGE_ID,
                "object_control_source_anomaly_id": OBJECT_CONTROL_ANOMALY_ID,
                "zone_change_projection_id": ZONE_CHANGE_PROJECTION_ID,
                "zone_change_package_id": ZONE_CHANGE_PACKAGE_ID,
            }.items():
                if type(value[key]) is not type(expected) or value[key] != expected:
                    _fail("exact prior identities and boundaries required: " + key)
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
class DirectDependencyClosureReview(ZoneChangeDependencyReport):
    SCHEMA: ClassVar[str] = "gameplay-cr-zone-change-direct-closure-review-v1"
    ID_FIELD: ClassVar[str] = "closure_review_id"
    BODY_FIELDS: ClassVar[frozenset[str]] = _COMMON | frozenset({
        "status", "review_state", "prior_family_closure_review_id", "direct_reference_findings",
        "resolved_count", "affected_exception_reassessments", "parent_reassessment",
        "new_numbered_dependencies", "remaining_unresolved_rules", "semantic_closure",
        "execution_status", "limitations",
    })


@dataclass(frozen=True)
class ZoneChangeDependencyReadinessReassessment(ZoneChangeDependencyReport):
    SCHEMA: ClassVar[str] = "gameplay-cr-zone-change-direct-readiness-reassessment-v1"
    ID_FIELD: ClassVar[str] = "zone_change_readiness_reassessment_id"
    BODY_FIELDS: ClassVar[frozenset[str]] = _COMMON | frozenset({
        "status", "closure_review_id", "prior_zone_change_readiness_reassessment_id",
        "target_profile_id", "capability_id", "affected_rules", "zone_change_dimensions",
        "direct_reference_gaps_now_represented", "newly_unresolved_rules", "remaining_unresolved_rules",
        "unsupported_subsystems", "required_semantic_primitives", "real_execution_primitives_available",
        "complete_zone_change_semantics", "dependency_closure", "semantic_closure",
        "overall_execution_readiness", "readiness_code", "execution_status",
        "real_snapshot_instantiated", "real_profile_activated", "blockers", "next_milestone", "limitations",
    })


@dataclass(frozen=True)
class ZoneChangeDependencyCompositeCoverage(ZoneChangeDependencyReport):
    SCHEMA: ClassVar[str] = "gameplay-cr-zone-change-direct-composite-coverage-v1"
    ID_FIELD: ClassVar[str] = "composite_coverage_id"
    BODY_FIELDS: ClassVar[frozenset[str]] = _COMMON | frozenset({
        "view_kind", "closure_review_id", "zone_change_readiness_reassessment_id",
        "foundational_projected_rule_count", "dependency_projected_rule_count",
        "object_control_projected_rule_count", "zone_change_projected_rule_count",
        "zone_change_dependency_projected_rule_count", "total_projected_rule_count",
        "projected_references", "projection_components", "direct_dependencies_resolved",
        "represented_exception_families", "remaining_unresolved_rules", "newly_unresolved_rules",
        "object_control_dependencies", "zone_change_dependencies", "open_exception_families",
        "open_semantic_boundaries", "unsupported_variants", "historical_acquisition_identity",
        "semantic_closure", "execution_status", "limitations",
    })


def _validate_evidence(projection, original, design, dependency, control, zone):
    if type(projection) is not ZoneChangeDependencyProjection:
        _fail("typed bounded direct-dependency projection required")
    projection.verify()
    expected = {"projection.json": zone["projection.json"],
                **build_zone_change_reports(zone["projection.json"], original, design, dependency, control)}
    if (set(zone) != set(expected) or any(type(zone[name]) is not type(expected[name]) or
            zone[name].to_dict() != expected[name].to_dict() for name in expected)):
        _fail("complete prior zone-change evidence must reproduce")
    raw = {name: (record.serialize() + "\n").encode("utf-8") for name, record in zone.items()}
    if (zone["projection.json"].identity != ZONE_CHANGE_PROJECTION_ID or
            zone_change_manifest(zone, raw)["package_id"] != ZONE_CHANGE_PACKAGE_ID):
        _fail("exact merged zone-change identities required")


def _next_milestone(newly_unresolved):
    candidates = [
        {"candidate": "Core Control Dependency Projection",
         "reason": "603, 605, and 114 still require a separately reviewed bounded source-unit scope."},
        {"candidate": "Madness Casting Dependency Design", "target_references": newly_unresolved,
         "reason": "The selected Madness family identifies four exact unprojected casting references, allowing a bounded design review."},
        {"candidate": "Ability / Continuous-Effect Dependency Design", "target_references": ["613"],
         "reason": "Static-effect context is represented, but layers and general continuous effects need broader design and scope review."},
        {"candidate": "Core State Semantic Primitive Contracts", "eligible": False,
         "reason": "Complete semantic closure remains unknown and runtime contracts would be premature."},
    ]
    if newly_unresolved != ["601.2b", "601.2f", "601.2g", "601.2h"]:
        _fail("next recommendation must follow the actual new reference frontier")
    return {"candidate": candidates[1]["candidate"], "authorized": False,
        "rationale": "The four prior direct targets are represented. The complete selected Madness family now exposes a precise four-reference casting frontier. A non-executable design review can bound that frontier before any future projection; control and continuous effects require broader scope decisions, and state primitives still lack semantic closure.",
        "evaluated_candidates": candidates}


def build_zone_change_dependency_reports(projection, original, design, dependency, control, zone):
    """Derive direct reference evidence without promoting any runtime capability."""
    _validate_evidence(projection, original, design, dependency, control, zone)
    new = projection.to_dict()
    prior_family = zone["family-closure-review.json"].to_dict()
    prior_readiness = zone["zone-change-readiness-reassessment.json"].to_dict()
    prior_composite = zone["composite-coverage.json"].to_dict()
    components = [original, dependency["projection.json"], control["projection.json"], zone["projection.json"], projection]
    component_refs = [[row["rule_reference"] for row in item.to_dict()["rules"]] for item in components]
    all_refs = [reference for group in component_refs for reference in group]
    if ([len(group) for group in component_refs] != [20, 12, 7, 12, 12] or
            len(all_refs) != 63 or len(set(all_refs)) != 63 or
            tuple(component_refs[-1]) != SELECTED_REFERENCES):
        _fail("five separate authorized projections totaling exactly 63 units required")
    new_lookup = {row["rule_reference"]: row for row in new["rules"]}
    old_lookup = {row["rule_reference"]: row for row in zone["projection.json"].to_dict()["rules"]}
    target_scopes = {
        "611.3d": (["611.3d"], ["611.3", "611.3a", "611.3b"]),
        "704.5m": (["704.5m"], []),
        "702.35": (["702.35a", "702.35b", "702.35c"], []),
        "123.5": (["123.5", "123.5a", "123.5b", "123.5c"], []),
    }
    prior_targets = _unique(ref for rule in old_lookup.values() for ref in rule["direct_dependency_references"])
    if prior_targets != list(target_scopes):
        _fail("four explicit targets must be derived from merged exception records")
    findings = []
    for target, (represented, context) in target_scopes.items():
        evidence = [new_lookup[ref] for ref in represented + context]
        findings.append({"target_reference": target,
            "status": "DIRECT_REFERENCE_RESOLVED" if len(evidence) == len(represented + context) else "UNRESOLVED",
            "represented_references": represented, "context_references": context,
            "evidence_rule_ids": [row["rule_id"] for row in evidence],
            "representation_kind": "COMPLETE_SELECTED_FAMILY" if target in {"702.35", "123.5"} else "EXACT_RULE_WITH_REQUIRED_CONTEXT",
            "semantic_closure": "SEMANTIC_CLOSURE_OPEN", "execution_ready": False,
            "execution_status": "EXECUTION_BLOCKED"})
    explicit = []
    for rule in new["rules"]:
        for target in rule["direct_dependency_references"]:
            represented = target in all_refs
            explicit.append({"from_reference": rule["rule_reference"], "target_reference": target,
                "status": "DIRECT_REFERENCE_RESOLVED" if represented else "UNRESOLVED",
                "projection_state": "PROJECTED" if represented else "UNPROJECTED",
                "component": "THIS_PROJECTION" if target in new_lookup else "PRIOR_PROJECTION" if represented else "NONE"})
    newly_unresolved = _unique(row["target_reference"] for row in explicit if row["status"] == "UNRESOLVED")
    remaining = _unique([ref for ref in prior_composite["remaining_unresolved_rules"] if ref not in target_scopes] + newly_unresolved)
    if set(remaining).intersection(all_refs):
        _fail("remaining numbered boundaries must be unprojected")
    affected = []
    for reference in ("400.7b", "400.7f", "400.7k", "400.7m"):
        prior = old_lookup[reference]
        targets = prior["direct_dependency_references"]
        scope = _unique(ref for target in targets for group in target_scopes[target] for ref in group)
        selected = [new_lookup[ref] for ref in scope]
        unresolved = _unique(ref for row in selected for ref in row["direct_dependency_references"] if ref not in all_refs)
        subsystems = _unique(row["reference"] for rule in [prior, *selected] for row in rule["subsystem_boundaries"])
        primitives = _unique(row["reference"] for rule in [prior, *selected] for row in rule["required_future_semantic_primitives"])
        affected.append({"rule_reference": reference, "prior_rule_id": prior["rule_id"],
            "previous_explicit_dependencies": targets,
            "newly_projected_dependency_evidence": [{"rule_reference": row["rule_reference"], "rule_id": row["rule_id"]} for row in selected],
            "direct_reference_status": "DIRECT_REFERENCE_RESOLVED",
            "remaining_unresolved_numbered_dependencies": unresolved,
            "remaining_semantic_subsystem_boundaries": subsystems,
            "required_future_semantic_primitives": primitives,
            "direct_numbered_blockers_reduced": bool(targets and selected),
            "dependency_closure": "OPEN", "semantic_closure": "SEMANTIC_CLOSURE_OPEN",
            "execution_ready": False, "execution_status": "EXECUTION_BLOCKED", "mutated": False})
    parent = {"rule_reference": PARENT_REFERENCE, "original_projection_id": original.identity,
        "prior_parent_reassessment_id": zone["family-closure-review.json"].identity,
        "direct_exception_family_represented": prior_family["direct_family_coverage"]["projected_count"] == 12,
        "four_direct_dependency_targets_represented": all(row["status"] == "DIRECT_REFERENCE_RESOLVED" for row in findings),
        "direct_dependency_targets": prior_targets, "unresolved_direct_dependency_targets": [],
        "remaining_unresolved_numbered_dependencies": newly_unresolved,
        "complete_zone_change_semantics": "UNKNOWN", "dependency_closure": "OPEN",
        "semantic_closure": "SEMANTIC_CLOSURE_OPEN", "required_primitives_available": False,
        "execution_ready": False, "execution_status": "EXECUTION_BLOCKED",
        "parent_reprojected": False, "mutated": False}
    common = {"game_id": "magic", "canonical_base": CANONICAL_MAIN,
        "foundational_projection_id": original.identity, "foundational_package_id": PROJECTION_PACKAGE_ID,
        "dependency_projection_id": dependency["projection.json"].identity, "dependency_package_id": DEPENDENCY_PACKAGE_ID,
        "execution_design_package_id": DESIGN_PACKAGE_ID,
        "object_control_projection_id": control["projection.json"].identity, "object_control_package_id": OBJECT_CONTROL_PACKAGE_ID,
        "object_control_source_anomaly_id": OBJECT_CONTROL_ANOMALY_ID,
        "zone_change_projection_id": zone["projection.json"].identity, "zone_change_package_id": ZONE_CHANGE_PACKAGE_ID,
        "zone_change_dependency_projection_id": projection.identity, "source_binding": new["source_binding"]}
    closure = DirectDependencyClosureReview.create({**common,
        "status": "ZONE_CHANGE_DIRECT_DEPENDENCIES_PROJECTED", "review_state": "PROJECTED_FOR_REVIEW",
        "prior_family_closure_review_id": zone["family-closure-review.json"].identity,
        "direct_reference_findings": findings, "resolved_count": sum(row["status"] == "DIRECT_REFERENCE_RESOLVED" for row in findings),
        "affected_exception_reassessments": affected, "parent_reassessment": parent,
        "new_numbered_dependencies": explicit, "remaining_unresolved_rules": remaining,
        "semantic_closure": "SEMANTIC_CLOSURE_OPEN", "execution_status": "EXECUTION_BLOCKED",
        "limitations": ["Four explicit references are represented by twelve coherent selected source units; direct representation does not establish semantic closure.",
            "The selected static-effect exception preserves the 611.3a/b relationship; 611.3c is intentionally outside scope.",
            "All reassessments are append-only; every prior rule record and retained package is unchanged."]})
    boundaries = [row for rule in new["rules"] for row in rule["subsystem_boundaries"]]
    subsystems = _unique(prior_readiness["unsupported_subsystems"] + [row["reference"] for row in boundaries])
    primitives = _unique(prior_readiness["required_semantic_primitives"] +
        [row["reference"] for rule in new["rules"] for row in rule["required_future_semantic_primitives"]])
    dimension_extra = {
        "granted_static_ability_continuity": ["611.3", "611.3a", "611.3b", "611.3d"],
        "aura_sba_tracking": ["704.5m"], "madness": ["702.35a", "702.35b", "702.35c"],
        "sticker_continuity": ["123.5", "123.5a", "123.5b", "123.5c"],
        "public_zone_constraints": list(SELECTED_REFERENCES),
        "complete_semantic_closure": list(SELECTED_REFERENCES),
    }
    dimensions = []
    for old in prior_readiness["zone_change_dimensions"]:
        row = _json(old)
        extra = dimension_extra.get(row["dimension"], [])
        row["supporting_projected_references"] = _unique(row["supporting_projected_references"] + extra)
        row["unresolved_rules"] = _unique([ref for ref in row["unresolved_rules"] if ref not in target_scopes] +
            [ref for selected_ref in extra for ref in new_lookup[selected_ref]["direct_dependency_references"] if ref not in all_refs])
        row["open_semantic_boundaries"] = _unique(row["open_semantic_boundaries"] +
            [boundary["reference"] for selected_ref in extra for boundary in new_lookup[selected_ref]["subsystem_boundaries"]])
        row["new_dependency_evidence"] = extra
        dimensions.append(row)
    blockers = ["COMPLETE_ZONE_CHANGE_SEMANTICS_UNKNOWN", "REAL_EXECUTION_PRIMITIVES_ABSENT",
        "CARD_EFFECT_SEMANTICS_ABSENT", "DETERMINISTIC_REAL_RUNTIME_VECTORS_ABSENT", "OWNER_ACTIVATION_NOT_GRANTED"]
    blockers += ["UNRESOLVED_RULE:" + ref for ref in remaining]
    blockers += ["UNRESOLVED_SUBSYSTEM:" + ref for ref in subsystems]
    blockers += ["FUTURE_SEMANTIC_PRIMITIVE:" + ref for ref in primitives]
    reassessment = ZoneChangeDependencyReadinessReassessment.create({**common,
        "status": "APPEND_ONLY_ZONE_CHANGE_DIRECT_DEPENDENCY_REASSESSMENT_FOR_REVIEW",
        "closure_review_id": closure.identity,
        "prior_zone_change_readiness_reassessment_id": zone["zone-change-readiness-reassessment.json"].identity,
        "target_profile_id": prior_readiness["target_profile_id"], "capability_id": "zone_change_identity",
        "affected_rules": [*affected, parent], "zone_change_dimensions": dimensions,
        "direct_reference_gaps_now_represented": prior_targets, "newly_unresolved_rules": newly_unresolved,
        "remaining_unresolved_rules": remaining, "unsupported_subsystems": subsystems,
        "required_semantic_primitives": primitives, "real_execution_primitives_available": [],
        "complete_zone_change_semantics": "UNKNOWN", "dependency_closure": "OPEN",
        "semantic_closure": "SEMANTIC_CLOSURE_OPEN", "overall_execution_readiness": "BLOCKED",
        "readiness_code": "REAL_EXECUTION_PROFILE_NOT_READY", "execution_status": "EXECUTION_BLOCKED",
        "real_snapshot_instantiated": False, "real_profile_activated": False, "blockers": _unique(blockers),
        "next_milestone": _next_milestone(newly_unresolved),
        "limitations": ["Historical information, public-zone findability, casting/play bridges, and same-effect/cost tracking remain descriptive only.",
            "Continuous effects, casting, triggers, movement, Aura legality, SBAs, stickers, meld, and merge have no runtime primitives.",
            "No execution profile, real snapshot, Card semantics, or owner activation is supplied."]})
    package_ids = [PROJECTION_PACKAGE_ID, DEPENDENCY_PACKAGE_ID, OBJECT_CONTROL_PACKAGE_ID, ZONE_CHANGE_PACKAGE_ID]
    current_boundaries = [row for row in prior_composite["open_semantic_boundaries"]
                          if not (row["classification"] == "UNRESOLVED_RULE" and row["reference"] in target_scopes)]
    current_boundaries += [{**boundary, "required_by": [rule["rule_reference"]]}
                          for rule in new["rules"] for field in ("unresolved_dependencies", "subsystem_boundaries", "required_future_semantic_primitives")
                          for boundary in rule[field]]
    composite = ZoneChangeDependencyCompositeCoverage.create({**common,
        "view_kind": "DERIVED_READ_ONLY_FIVE_PROJECTION_VIEW", "closure_review_id": closure.identity,
        "zone_change_readiness_reassessment_id": reassessment.identity,
        "foundational_projected_rule_count": 20, "dependency_projected_rule_count": 12,
        "object_control_projected_rule_count": 7, "zone_change_projected_rule_count": 12,
        "zone_change_dependency_projected_rule_count": 12, "total_projected_rule_count": len(all_refs),
        "projected_references": all_refs,
        "projection_components": [{"projection_id": item.identity, "package_id": package_ids[index],
            "projected_references": component_refs[index], "mutated": False} for index, item in enumerate(components[:-1])] +
            [{"projection_id": projection.identity, "package_binding": "THIS_ENCLOSING_ZONE_CHANGE_DEPENDENCY_PACKAGE",
              "projected_references": component_refs[-1], "mutated": False}],
        "direct_dependencies_resolved": prior_composite["direct_dependencies_resolved"] + prior_targets,
        "represented_exception_families": prior_composite["represented_exception_families"],
        "remaining_unresolved_rules": remaining, "newly_unresolved_rules": newly_unresolved,
        "object_control_dependencies": prior_composite["object_control_dependencies"],
        "zone_change_dependencies": newly_unresolved,
        "open_exception_families": prior_composite["open_exception_families"],
        "open_semantic_boundaries": current_boundaries, "unsupported_variants": prior_composite["unsupported_variants"],
        "historical_acquisition_identity": HISTORICAL_ACQUISITION_ID,
        "semantic_closure": "SEMANTIC_CLOSURE_OPEN", "execution_status": "EXECUTION_BLOCKED",
        "limitations": ["All five projection and package identities stay distinct; this is a read-only view, not a replacement projection.",
            "The enclosing manifest resolves the fifth package identity without a circular content hash.",
            "Sixty-three projected real source units establish neither execution readiness nor source-policy permission."]})
    return {"closure-review.json": closure, "zone-change-readiness-reassessment.json": reassessment,
            "composite-coverage.json": composite}
