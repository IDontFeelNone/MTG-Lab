"""Append-only, read-only evidence for the bounded 400.7 exception family.

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
from .contracts import FoundationalProjection, _freeze, _json
from .dependency_reports import (
    DESIGN_PACKAGE_ID, DESIGN_REVIEW_ID, HISTORICAL_ACQUISITION_ID, _families, _unique,
)
from .object_control_package import package_manifest as object_control_manifest
from .object_control_reports import (
    DEPENDENCY_PROJECTION_ID, DEPENDENCY_PACKAGE_ID, build_object_control_reports,
)
from .zone_change_contracts import ZoneChangeProjection
from .zone_change_scope import SELECTED_REFERENCES, PARENT_REFERENCE

CANONICAL_MAIN = "0d32501048b5fd5c3f4a4c51e00920715aefb8ef"
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
    "zone_change_projection_id", "source_binding",
})


def _fail(message="invalid zone-change report"):
    raise GameplayContractError("zone_change_report", message)


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
        "zone_change_projected_rule_count": 12, "total_projected_rule_count": 51,
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
class ZoneChangeReport(Contract):
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
class FamilyClosureReview(ZoneChangeReport):
    SCHEMA: ClassVar[str] = "gameplay-cr-zone-change-family-closure-review-v1"
    ID_FIELD: ClassVar[str] = "family_closure_review_id"
    BODY_FIELDS: ClassVar[frozenset[str]] = _COMMON | frozenset({
        "status", "review_state", "parent_reference", "prior_unprojected_exceptions",
        "exception_findings", "direct_family_coverage", "parent_reassessment", "lettering_review",
        "newly_unresolved_rules", "new_boundaries", "dependency_graph", "semantic_closure",
        "execution_status", "limitations",
    })


@dataclass(frozen=True)
class ZoneChangeReadinessReassessment(ZoneChangeReport):
    SCHEMA: ClassVar[str] = "gameplay-cr-zone-change-readiness-reassessment-v1"
    ID_FIELD: ClassVar[str] = "zone_change_readiness_reassessment_id"
    BODY_FIELDS: ClassVar[frozenset[str]] = _COMMON | frozenset({
        "status", "family_closure_review_id", "prior_projection_review_id",
        "prior_capability_matrix_id", "prior_dependency_reassessment_id",
        "prior_object_control_reassessment_id", "target_profile_id", "capability_id",
        "affected_rules", "zone_change_dimensions", "prior_zone_change_blockers",
        "direct_reference_gaps_now_represented", "newly_unresolved_rules", "remaining_unresolved_rules",
        "unsupported_subsystems", "required_semantic_primitives", "real_execution_primitives_available",
        "complete_zone_change_semantics", "dependency_closure", "semantic_closure",
        "overall_execution_readiness", "readiness_code", "execution_status",
        "real_snapshot_instantiated", "real_profile_activated", "blockers", "next_milestone", "limitations",
    })


@dataclass(frozen=True)
class ZoneChangeCompositeCoverage(ZoneChangeReport):
    SCHEMA: ClassVar[str] = "gameplay-cr-zone-change-composite-coverage-v1"
    ID_FIELD: ClassVar[str] = "composite_coverage_id"
    BODY_FIELDS: ClassVar[frozenset[str]] = _COMMON | frozenset({
        "view_kind", "family_closure_review_id", "zone_change_readiness_reassessment_id",
        "foundational_projected_rule_count", "dependency_projected_rule_count",
        "object_control_projected_rule_count", "zone_change_projected_rule_count",
        "total_projected_rule_count", "projected_references", "projection_components",
        "direct_dependencies_resolved", "represented_exception_families", "remaining_unresolved_rules",
        "newly_unresolved_rules", "object_control_dependencies", "zone_change_dependencies",
        "open_exception_families", "open_semantic_boundaries", "unsupported_variants",
        "historical_acquisition_identity", "semantic_closure", "execution_status", "limitations",
    })


def _validate_evidence(projection, original, design, dependency_records, object_control_records):
    if not isinstance(projection, ZoneChangeProjection) or not isinstance(original, FoundationalProjection):
        _fail("typed validated new and foundational projections required")
    projection.verify()
    if not isinstance(object_control_records, Mapping) or set(object_control_records) != {
            "projection.json", "source-anomaly.json", "family-closure-review.json",
            "control-readiness-reassessment.json", "composite-coverage.json"}:
        _fail("complete merged object-control evidence required")
    control = object_control_records["projection.json"]
    anomaly = object_control_records["source-anomaly.json"]
    expected = {"projection.json": control, "source-anomaly.json": anomaly,
                **build_object_control_reports(control, anomaly, original, design, dependency_records)}
    if any(type(object_control_records[name]) is not type(expected[name]) or
           object_control_records[name].to_dict() != expected[name].to_dict() for name in expected):
        _fail("merged object-control evidence does not reproduce")
    raw = {name: (record.serialize() + "\n").encode("utf-8")
           for name, record in object_control_records.items()}
    if (control.identity != OBJECT_CONTROL_PROJECTION_ID or anomaly.identity != OBJECT_CONTROL_ANOMALY_ID or
            object_control_manifest(object_control_records, raw)["package_id"] != OBJECT_CONTROL_PACKAGE_ID):
        _fail("exact merged object-control projection, anomaly, and package required")
    return dependency_records["projection.json"], control


def _group_boundaries(projection):
    grouped = {}
    for rule in projection.to_dict()["rules"]:
        for field in ("unresolved_dependencies", "subsystem_boundaries", "required_future_semantic_primitives"):
            for row in rule[field]:
                key = row["reference"], row["classification"], row["status"]
                grouped.setdefault(key, {**row, "required_by": []})
                if rule["rule_reference"] not in grouped[key]["required_by"]:
                    grouped[key]["required_by"].append(rule["rule_reference"])
    return list(grouped.values())


def _next_milestone(newly_unresolved, dimensions):
    candidates = [
        {"candidate": "Zone-Change Direct Dependency Projection", "target_references": newly_unresolved,
         "known_explicit_reference_count": len(newly_unresolved), "source_unit_scope_requires_review": True,
         "reason": "Four exact explicit reference targets are newly exposed by the represented exception family; review a bounded coherent source-unit scope before projection."},
        {"candidate": "Core Control Dependency Projection", "source_unit_scope_requires_review": True,
         "reason": "603, 603.7d-f, 605, and 114 still require an exact bounded source-unit scope."},
        {"candidate": "Ability / Continuous-Effect Dependency Design", "target_references": ["613"],
         "source_unit_scope_requires_review": True,
         "reason": "The broad continuous-effect target needs design and scope review; it is not a finite authorized projection allowlist."},
        {"candidate": "Core State Semantic Primitive Contracts", "eligible": False,
         "reason": "Dependency and complete semantic closure are still open."},
    ]
    affected = [row["dimension"] for row in dimensions
                if set(row["unresolved_rules"]).intersection(newly_unresolved)]
    if newly_unresolved != ["611.3d", "704.5m", "702.35", "123.5"] or not affected:
        _fail("next-milestone recommendation requires the evidenced finite direct-reference targets")
    return {"candidate": candidates[0]["candidate"], "authorized": False,
        "rationale": "The twelve direct exceptions are represented. Their four explicit numbered targets are the smallest newly evidenced finite reference frontier and block " +
            ", ".join(affected) + ". The next milestone must first review an exact bounded source-unit allowlist; this recommendation authorizes neither that inspection nor projection. Core control and 613 require broader scope design, while primitive contracts lack semantic closure.",
        "evaluated_candidates": candidates}


def build_zone_change_reports(projection, foundational_projection, design_records,
                              dependency_records, object_control_records):
    """Derive the family, parent, capability, and four-component review evidence."""
    dependency, control = _validate_evidence(projection, foundational_projection, design_records,
                                            dependency_records, object_control_records)
    new = projection.to_dict()
    original = foundational_projection.to_dict()
    components = [foundational_projection, dependency, control, projection]
    component_refs = [[row["rule_reference"] for row in item.to_dict()["rules"]] for item in components]
    references = component_refs[-1]
    all_references = [reference for group in component_refs for reference in group]
    prior_families = _families(foundational_projection)
    if (tuple(references) != tuple(SELECTED_REFERENCES) or references != prior_families[PARENT_REFERENCE]["references"] or
            [len(group) for group in component_refs] != [20, 12, 7, 12] or
            len(set(all_references)) != 51 or len(all_references) != 51):
        _fail("four distinct exact source-unit sets and complete 12-unit direct family required")
    prior_composite = object_control_records["composite-coverage.json"].to_dict()
    prior_reassessment = object_control_records["control-readiness-reassessment.json"].to_dict()
    boundaries = _group_boundaries(projection)
    newly_unresolved = _unique(row["reference"] for row in boundaries if row["classification"] == "UNRESOLVED_RULE")
    subsystem_rows = [row for row in boundaries if row["classification"] in
                      {"UNRESOLVED_SUBSYSTEM", "UNSUPPORTED_KEYWORD_SUBSYSTEM"}]
    subsystems = _unique(row["reference"] for row in subsystem_rows)
    primitives = _unique(row["reference"] for row in boundaries if row["classification"] == "FUTURE_SEMANTIC_PRIMITIVE")
    remaining = _unique(prior_composite["remaining_unresolved_rules"] + newly_unresolved)
    if set(remaining).intersection(all_references):
        _fail("unresolved numbered dependencies must remain unprojected")
    dependency_open = bool(remaining)
    semantic_open = bool(boundaries) or not primitives
    if not dependency_open or not semantic_open:
        _fail("recorded unresolved source and semantic boundaries must remain open")
    common = {"game_id": "magic", "canonical_base": CANONICAL_MAIN,
        "foundational_projection_id": foundational_projection.identity, "foundational_package_id": PROJECTION_PACKAGE_ID,
        "dependency_projection_id": dependency.identity, "dependency_package_id": DEPENDENCY_PACKAGE_ID,
        "execution_design_package_id": DESIGN_PACKAGE_ID, "object_control_projection_id": control.identity,
        "object_control_package_id": OBJECT_CONTROL_PACKAGE_ID,
        "object_control_source_anomaly_id": OBJECT_CONTROL_ANOMALY_ID,
        "zone_change_projection_id": projection.identity, "source_binding": new["source_binding"]}
    findings = []
    for rule in new["rules"]:
        findings.append({"rule_reference": rule["rule_reference"], "rule_id": rule["rule_id"],
            "reference_status": "EXCEPTION_REFERENCE_PROJECTED",
            "explicit_source_rule_dependencies": rule["direct_dependency_references"],
            "unresolved_rules": [row["reference"] for row in rule["unresolved_dependencies"]
                                 if row["classification"] == "UNRESOLVED_RULE"],
            "subsystem_boundaries": rule["subsystem_boundaries"],
            "required_future_semantic_primitives": rule["required_future_semantic_primitives"],
            "semantic_distinctions": rule["semantic_distinctions"], "dependency_closure": "OPEN",
            "exception_semantics_closed": False, "semantic_closure": "SEMANTIC_CLOSURE_OPEN",
            "execution_ready": False, "execution_status": "EXECUTION_BLOCKED"})
    parent = {"rule_reference": PARENT_REFERENCE, "original_projection_id": foundational_projection.identity,
        "mutated": False, "parent_reprojected": False,
        "direct_exception_enumeration": "DIRECT_EXCEPTION_FAMILY_REPRESENTED",
        "prior_unprojected_direct_exception_count": len(prior_families[PARENT_REFERENCE]["references"]),
        "projected_exception_references": references, "unprojected_direct_exception_references": [],
        "explicit_dependency_closure": "OPEN" if newly_unresolved else "CLOSED_FOR_RECORDED_REFERENCES_ONLY",
        "dependency_closure": "OPEN", "unresolved_rules": newly_unresolved,
        "semantic_subsystem_closure": "OPEN", "historical_object_lookup_semantics": "UNIMPLEMENTED",
        "zone_movement_semantics": "UNIMPLEMENTED", "public_hidden_zone_behavior": "UNRESOLVED",
        "required_future_semantic_primitives": primitives, "required_primitives_available": False,
        "complete_zone_change_semantics": "UNKNOWN", "semantic_closure": "SEMANTIC_CLOSURE_OPEN",
        "execution_ready": False, "execution_status": "EXECUTION_BLOCKED"}
    family = FamilyClosureReview.create({**common,
        "status": "ZONE_CHANGE_EXCEPTION_FAMILY_PROJECTED", "review_state": "PROJECTED_FOR_REVIEW",
        "parent_reference": PARENT_REFERENCE, "prior_unprojected_exceptions": prior_families[PARENT_REFERENCE]["references"],
        "exception_findings": findings,
        "direct_family_coverage": {"expected_count": len(SELECTED_REFERENCES), "projected_count": len(references),
            "references": references, "status": "DIRECT_EXCEPTION_FAMILY_REPRESENTED",
            "additional_rules_projected": [], "parent_reprojected": False,
            "exception_semantics_closed": False, "execution_ready": False},
        "parent_reassessment": parent, "lettering_review": new["lettering_policy"],
        "newly_unresolved_rules": newly_unresolved, "new_boundaries": boundaries,
        "dependency_graph": new["graph"], "semantic_closure": "SEMANTIC_CLOSURE_OPEN",
        "execution_status": "EXECUTION_BLOCKED", "limitations": [
            "Direct exception enumeration coverage is complete only for the twelve authorized source units.",
            "Expected CR lettering omits l; no source anomaly, missing unit, or correction is inferred.",
            "The foundational parent and every prior package remain byte-identical; this parent reassessment is read-only.",
            "Representation of an exception is neither semantic closure nor implemented behavior."]})
    matrix = design_records["capability-matrix.json"].to_dict()
    capability = next(row for row in matrix["capabilities"] if row["capability_id"] == "zone_change_identity")
    dimension_scopes = [
        ("default_new_object_identity", ["109.1", "400.1", "400.7"], ["zone_movement", "object_identity", "public_hidden_zone_behavior"]),
        ("spell_to_permanent_effect_continuity", ["400.7a"], ["continuous_effects", "spell_resolution", "control_changes"]),
        ("granted_static_ability_continuity", ["400.7b"], ["static_abilities", "continuous_effects", "granted_abilities"]),
        ("prevention_continuity", ["400.7c"], ["prevention_effects", "damage", "damage_source_continuity"]),
        ("spell_history_access", ["400.7d"], ["spell_to_permanent_history_access", "costs_paid", "mana_spent"]),
        ("zone_change_trigger_object_tracking", ["400.7e"], ["zone_change_triggers", "public_zone_object_tracking"]),
        ("aura_sba_tracking", ["400.7f"], ["aura_attachment", "simultaneous_zone_movement", "state_based_action_movement"]),
        ("cast_permission_granted_ability_continuity", ["400.7g"], ["cast_permission_identity_bridge", "casting"]),
        ("cast_permission_other_effect_findability", ["400.7h"], ["cast_permission_effect_object_lookup", "effect_continuity"]),
        ("land_play_permission_identity_bridge", ["400.7i"], ["land_play_permission_identity_bridge", "land_play"]),
        ("same_effect_cost_object_tracking", ["400.7j"], ["same_effect_public_zone_object_lookup", "cost_movement_public_zone_object_lookup", "public_zone_object_tracking"]),
        ("madness", ["400.7k"], ["madness", "discard", "triggered_abilities"]),
        ("sticker_continuity", ["400.7m"], ["public_zone_sticker_retention", "sticker_effect_new_object_continuity", "new_object_identity"]),
        ("public_zone_constraints", references, ["public_hidden_zone_behavior", "public_zone_object_tracking"]),
        ("complete_semantic_closure", [PARENT_REFERENCE, *references], ["unknown_complete_semantic_context"]),
    ]
    lookup = {row["rule_reference"]: row for row in new["rules"]}
    dimensions = []
    for name, scope, open_boundaries in dimension_scopes:
        local_refs = _unique(row["reference"] for reference in scope for row in
                            lookup.get(reference, {}).get("unresolved_dependencies", [])
                            if row["classification"] == "UNRESOLVED_RULE")
        dimensions.append({"dimension": name, "supporting_projected_references": scope,
            "descriptive_coverage": "REPRESENTED_WITH_OPEN_BOUNDARIES", "open_semantic_boundaries": open_boundaries,
            "unresolved_rules": local_refs, "dependency_closure": "OPEN", "semantic_closure": "SEMANTIC_CLOSURE_OPEN",
            "execution_supported": False, "implementation_primitive_available": False,
            "execution_status": "EXECUTION_BLOCKED"})
    all_primitives = _unique(capability["required_semantic_primitives"] + primitives)
    affected = [{"rule_reference": PARENT_REFERENCE, "component_projection_id": foundational_projection.identity,
        "assessment": parent}, *findings]
    blockers = ["COMPLETE_ZONE_CHANGE_SEMANTICS_UNKNOWN", "REAL_EXECUTION_PRIMITIVES_ABSENT",
        "CARD_EFFECT_SEMANTICS_ABSENT", "DETERMINISTIC_REAL_RUNTIME_VECTORS_ABSENT", "OWNER_ACTIVATION_NOT_GRANTED"]
    blockers += ["UNRESOLVED_RULE:" + reference for reference in remaining]
    blockers += [row["classification"] + ":" + row["reference"] for row in subsystem_rows]
    blockers += ["FUTURE_SEMANTIC_PRIMITIVE:" + primitive for primitive in all_primitives]
    reassessment = ZoneChangeReadinessReassessment.create({**common,
        "status": "APPEND_ONLY_ZONE_CHANGE_REASSESSMENT_FOR_REVIEW", "family_closure_review_id": family.identity,
        "prior_projection_review_id": DESIGN_REVIEW_ID,
        "prior_capability_matrix_id": design_records["capability-matrix.json"].identity,
        "prior_dependency_reassessment_id": dependency_records["execution-readiness-reassessment.json"].identity,
        "prior_object_control_reassessment_id": object_control_records["control-readiness-reassessment.json"].identity,
        "target_profile_id": design_records["execution-profile-design.json"].to_dict()["target_profile_id"],
        "capability_id": "zone_change_identity", "affected_rules": affected, "zone_change_dimensions": dimensions,
        "prior_zone_change_blockers": capability["blocking_references"],
        "direct_reference_gaps_now_represented": [reference for reference in capability["blocking_references"] if reference in references],
        "newly_unresolved_rules": newly_unresolved, "remaining_unresolved_rules": remaining,
        "unsupported_subsystems": subsystems, "required_semantic_primitives": all_primitives,
        "real_execution_primitives_available": [], "complete_zone_change_semantics": "UNKNOWN",
        "dependency_closure": "OPEN", "semantic_closure": "SEMANTIC_CLOSURE_OPEN",
        "overall_execution_readiness": prior_reassessment["overall_execution_readiness"],
        "readiness_code": prior_reassessment["readiness_code"], "execution_status": "EXECUTION_BLOCKED",
        "real_snapshot_instantiated": False, "real_profile_activated": False,
        "blockers": _unique(blockers), "next_milestone": _next_milestone(newly_unresolved, dimensions),
        "limitations": ["This append-only capability review does not modify PR 187's design package or activate its target profile.",
            "Historical access and bounded findability do not equate the old object and the new object.",
            "Casting-ability continuity and other-effect findability are separate; playing a land is not casting.",
            "Unknown complete semantics, unprojected dependencies, and absent primitives block runtime."]})
    family_rows = {key: value for key, value in prior_composite["open_exception_families"].items() if key != PARENT_REFERENCE}
    represented = {**prior_composite["represented_exception_families"], PARENT_REFERENCE: {
        "references": references, "reference_status": "EXCEPTION_REFERENCE_PROJECTED",
        "exception_semantics_closed": False, "execution_ready": False}}
    package_ids = [PROJECTION_PACKAGE_ID, DEPENDENCY_PACKAGE_ID, OBJECT_CONTROL_PACKAGE_ID]
    composite = ZoneChangeCompositeCoverage.create({**common,
        "view_kind": "DERIVED_READ_ONLY_FOUR_PROJECTION_VIEW", "family_closure_review_id": family.identity,
        "zone_change_readiness_reassessment_id": reassessment.identity,
        "foundational_projected_rule_count": len(component_refs[0]), "dependency_projected_rule_count": len(component_refs[1]),
        "object_control_projected_rule_count": len(component_refs[2]), "zone_change_projected_rule_count": len(references),
        "total_projected_rule_count": len(all_references), "projected_references": all_references,
        "projection_components": [
            {"projection_id": item.identity, "package_id": package_ids[index],
             "projected_references": component_refs[index], "mutated": False}
            for index, item in enumerate(components[:-1])] + [
            {"projection_id": projection.identity, "package_binding": "THIS_ENCLOSING_ZONE_CHANGE_PACKAGE",
             "projected_references": references, "mutated": False}],
        "direct_dependencies_resolved": prior_composite["direct_dependencies_resolved"],
        "represented_exception_families": represented, "remaining_unresolved_rules": remaining,
        "newly_unresolved_rules": newly_unresolved,
        "object_control_dependencies": object_control_records["family-closure-review.json"].to_dict()["newly_unresolved_rules"],
        "zone_change_dependencies": newly_unresolved, "open_exception_families": family_rows,
        "open_semantic_boundaries": prior_composite["open_semantic_boundaries"] + boundaries,
        "unsupported_variants": prior_composite["unsupported_variants"],
        "historical_acquisition_identity": HISTORICAL_ACQUISITION_ID,
        "semantic_closure": "SEMANTIC_CLOSURE_OPEN", "execution_status": "EXECUTION_BLOCKED",
        "limitations": ["The four component projection and package identities stay separate; this view creates no replacement projection.",
            "The enclosing manifest resolves the new component's package identity without a circular content hash.",
            "No remaining numbered rule or subsystem is recursively projected or interpreted.",
            "Fifty-one represented source units establish no execution readiness or source-policy permission."]})
    return {"family-closure-review.json": family, "zone-change-readiness-reassessment.json": reassessment,
            "composite-coverage.json": composite}
