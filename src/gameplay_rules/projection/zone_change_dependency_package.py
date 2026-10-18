"""Strict append-only package for the twelve zone-change dependency rules.

Construction requires the exact external source artifact. Offline loading checks
canonical authored records and independently reproduces their findings from the
five immutable projection components. No source body belongs in this package.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from evidence.contracts import deterministic_json, sha256_identity
from gameplay_rules.errors import GameplayContractError
from gameplay_rules.execution_design.contracts import PROJECTION_ID, PROJECTION_PACKAGE_ID
from gameplay_rules.execution_design.package import load_design_package
from .contracts import ARTIFACT_REVIEW_PACKAGE_ID
from .dependency_package import load_dependency_package, _read, _root
from .object_control_package import load_object_control_package
from .package import load_projection_package
from .zone_change_package import load_zone_change_package, package_manifest as zone_change_manifest
from .zone_change_reports import (
    DEPENDENCY_PROJECTION_ID, DEPENDENCY_PACKAGE_ID, OBJECT_CONTROL_PROJECTION_ID,
    OBJECT_CONTROL_PACKAGE_ID, OBJECT_CONTROL_ANOMALY_ID,
)
from .zone_change_dependency_contracts import ZoneChangeDependencyProjection
from .zone_change_dependency_reports import (
    CANONICAL_MAIN, DESIGN_PACKAGE_ID, HISTORICAL_ACQUISITION_ID,
    DirectDependencyClosureReview, ZoneChangeDependencyReadinessReassessment,
    ZoneChangeDependencyCompositeCoverage, build_zone_change_dependency_reports,
)
from .zone_change_dependency_scope import SELECTED_REFERENCES
from .zone_change_dependency_source import build_zone_change_dependency_source

ZONE_CHANGE_PROJECTION_ID = "sha256:0b32e8c16fc2089949d50c0ece4b2afb7b69355f2573f041cfc8b932aa4db141"
ZONE_CHANGE_PACKAGE_ID = "sha256:4836f6ea330cc40365540f85541160ef2251ff6ed88f7959f9d9e594031f7875"
PACKAGE_SCHEMA = "gameplay-cr-zone-change-direct-dependency-package-v1"
RECORD_TYPES = {
    "projection.json": ZoneChangeDependencyProjection,
    "closure-review.json": DirectDependencyClosureReview,
    "zone-change-readiness-reassessment.json": ZoneChangeDependencyReadinessReassessment,
    "composite-coverage.json": ZoneChangeDependencyCompositeCoverage,
}


def _fail(message="invalid zone-change direct dependency package integrity or boundary"):
    raise GameplayContractError("zone_change_dependency_package", message)


def _pairs(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            _fail("duplicate JSON field")
        result[key] = value
    return result


def _nonfinite(_value):
    _fail("non-finite JSON value")


def _prior_evidence(*, projection_root, design_root, dependency_root, object_control_root,
                    zone_change_root, artifact_review_root, source_root, discovery_root):
    roots = {"artifact_review_root": artifact_review_root, "source_root": source_root,
             "discovery_root": discovery_root}
    original = load_projection_package(projection_root, **roots)
    design = load_design_package(design_root, projection_root=projection_root, **roots)
    dependency = load_dependency_package(dependency_root, projection_root=projection_root,
                                         design_root=design_root, **roots)
    control = load_object_control_package(object_control_root, projection_root=projection_root,
        design_root=design_root, dependency_root=dependency_root, **roots)
    zone = load_zone_change_package(zone_change_root, projection_root=projection_root,
        design_root=design_root, dependency_root=dependency_root,
        object_control_root=object_control_root, **roots)
    raw = {name: (record.serialize() + "\n").encode("utf-8") for name, record in zone.items()}
    if (zone["projection.json"].identity != ZONE_CHANGE_PROJECTION_ID or
            zone_change_manifest(zone, raw)["package_id"] != ZONE_CHANGE_PACKAGE_ID):
        _fail("exact merged zone-change projection and package required")
    return original, design, dependency, control, zone


def build_zone_change_dependency_package(artifact_path, *, projection_root, design_root,
        dependency_root, object_control_root, zone_change_root,
        artifact_review_root, source_root, discovery_root):
    """Read actual exact source and return four authored records; write nothing."""
    projection = build_zone_change_dependency_source(artifact_path,
        artifact_review_root=artifact_review_root, source_root=source_root, discovery_root=discovery_root)
    original, design, dependency, control, zone = _prior_evidence(
        projection_root=projection_root, design_root=design_root, dependency_root=dependency_root,
        object_control_root=object_control_root, zone_change_root=zone_change_root,
        artifact_review_root=artifact_review_root, source_root=source_root, discovery_root=discovery_root)
    return {"projection.json": projection,
            **build_zone_change_dependency_reports(projection, original, design, dependency, control, zone)}


def package_manifest(records, raw_files):
    """Bind canonical records, exact scope, and all five separate components."""
    if set(records) != set(RECORD_TYPES) or set(raw_files) != set(RECORD_TYPES):
        _fail("exactly four authored records required")
    for name, cls in RECORD_TYPES.items():
        if type(records[name]) is not cls:
            _fail("typed authored records required")
        records[name].verify()
        if raw_files[name] != (records[name].serialize() + "\n").encode("utf-8"):
            _fail("noncanonical record bytes")
    projection = records["projection.json"]
    closure = records["closure-review.json"]
    reassessment = records["zone-change-readiness-reassessment.json"]
    composite = records["composite-coverage.json"]
    projection_value = projection.to_dict()
    for report in (closure, reassessment, composite):
        if report.zone_change_dependency_projection_id != projection.identity:
            _fail("report belongs to another projection")
        if report.to_dict()["source_binding"] != projection_value["source_binding"]:
            _fail("report source binding differs from projection")
    if (reassessment.closure_review_id != closure.identity or
            composite.closure_review_id != closure.identity or
            composite.zone_change_readiness_reassessment_id != reassessment.identity):
        _fail("report chain belongs to another evidence set")
    refs = [row["rule_reference"] for row in projection_value["rules"]]
    composite_value = composite.to_dict()
    components = composite_value["projection_components"]
    prior_projection_ids = [PROJECTION_ID, DEPENDENCY_PROJECTION_ID,
                            OBJECT_CONTROL_PROJECTION_ID, ZONE_CHANGE_PROJECTION_ID]
    prior_package_ids = [PROJECTION_PACKAGE_ID, DEPENDENCY_PACKAGE_ID,
                        OBJECT_CONTROL_PACKAGE_ID, ZONE_CHANGE_PACKAGE_ID]
    if (tuple(refs) != tuple(SELECTED_REFERENCES) or len(refs) != 12 or len(components) != 5 or
            components[-1] != {"projection_id": projection.identity,
                "package_binding": "THIS_ENCLOSING_ZONE_CHANGE_DEPENDENCY_PACKAGE",
                "projected_references": refs, "mutated": False}):
        _fail("exact selected scope and five-component binding required")
    if any(component["projection_id"] != prior_projection_ids[index] or
           component["package_id"] != prior_package_ids[index] or component["mutated"] is not False
           for index, component in enumerate(components[:-1])):
        _fail("exact immutable prior component identities required")
    component_refs = [row["projected_references"] for row in components]
    all_refs = [reference for group in component_refs for reference in group]
    if ([len(group) for group in component_refs] != [20, 12, 7, 12, 12] or
            len(all_refs) != 63 or len(set(all_refs)) != 63 or
            composite_value["projected_references"] != all_refs or
            composite_value["total_projected_rule_count"] != 63):
        _fail("exactly 63 distinct source units across five projections required")
    body = {
        "schema_version": PACKAGE_SCHEMA, "canonical_base": CANONICAL_MAIN,
        "prior_artifact_review_package_id": ARTIFACT_REVIEW_PACKAGE_ID,
        "foundational_projection_package_id": PROJECTION_PACKAGE_ID,
        "foundational_projection_id": PROJECTION_ID,
        "execution_design_package_id": DESIGN_PACKAGE_ID,
        "dependency_projection_package_id": DEPENDENCY_PACKAGE_ID,
        "dependency_projection_id": DEPENDENCY_PROJECTION_ID,
        "object_control_projection_package_id": OBJECT_CONTROL_PACKAGE_ID,
        "object_control_projection_id": OBJECT_CONTROL_PROJECTION_ID,
        "object_control_source_anomaly_id": OBJECT_CONTROL_ANOMALY_ID,
        "zone_change_projection_package_id": ZONE_CHANGE_PACKAGE_ID,
        "zone_change_projection_id": ZONE_CHANGE_PROJECTION_ID,
        "zone_change_dependency_projection_id": projection.identity,
        "closure_review_id": closure.identity,
        "zone_change_readiness_reassessment_id": reassessment.identity,
        "composite_coverage_id": composite.identity,
        "source_binding": projection_value["source_binding"],
        "files": {name: {"sha256": hashlib.sha256(raw_files[name]).hexdigest(), "bytes": len(raw_files[name])}
                  for name in sorted(RECORD_TYPES)},
        "selected_rule_count": len(refs), "selected_references": refs,
        "composite_projected_rule_count": composite_value["total_projected_rule_count"],
        "additional_rules_projected": [], "parent_reprojected": False,
        "status": closure.status, "review_state": "PROJECTED_FOR_REVIEW",
        "semantic_closure": closure.semantic_closure,
        "overall_execution_readiness": reassessment.overall_execution_readiness,
        "readiness_code": reassessment.readiness_code, "execution_authorized": False,
        "real_rules_executable": False, "owner_execution_approval": "NOT_GRANTED",
        "source_body_retained": False, "admission_eligible": False,
        "source_policy_clearance": "not_granted",
        "permissions": {key: "NOT_ESTABLISHED" for key in
            ("private_retention", "redistribution", "free_service", "commercial_service", "ai_export")},
        "historical_acquisition_identity": HISTORICAL_ACQUISITION_ID,
    }
    return {**body, "package_id": "sha256:" + sha256_identity({"domain": PACKAGE_SCHEMA, "content": body})}


def load_zone_change_dependency_package(root, *, projection_root, design_root,
        dependency_root, object_control_root, zone_change_root,
        artifact_review_root, source_root, discovery_root):
    """Verify five canonical regular files and independently reproduce reports.

    Caller-supplied lineage roots remain outside retained metadata. Package and
    lineage relocation preserve identities; external source proof is separate.
    """
    try:
        root = _root(root)
        paths = list(root.iterdir())
        if {path.name for path in paths} != set(RECORD_TYPES) | {"manifest.json"}:
            _fail("unexpected or missing package file")
        if any(path.is_symlink() or not path.is_file() for path in paths):
            _fail("regular package files required")
        raw = {name: _read(root / name) for name in RECORD_TYPES}
        records = {name: cls.from_json(raw[name]) for name, cls in RECORD_TYPES.items()}
        manifest_raw = _read(root / "manifest.json")
        manifest = json.loads(manifest_raw, object_pairs_hook=_pairs, parse_constant=_nonfinite)
        expected_manifest = package_manifest(records, raw)
        if (deterministic_json(manifest) != deterministic_json(expected_manifest) or
                manifest_raw != (deterministic_json(expected_manifest) + "\n").encode("utf-8")):
            _fail("manifest differs from canonical package contents")
        original, design, dependency, control, zone = _prior_evidence(
            projection_root=projection_root, design_root=design_root, dependency_root=dependency_root,
            object_control_root=object_control_root, zone_change_root=zone_change_root,
            artifact_review_root=artifact_review_root, source_root=source_root, discovery_root=discovery_root)
        expected = build_zone_change_dependency_reports(records["projection.json"], original,
                                                        design, dependency, control, zone)
        if any(records[name].to_dict() != expected[name].to_dict() for name in expected):
            _fail("closure/zone-change/composite findings do not reproduce")
        return records
    except GameplayContractError:
        raise
    except (OSError, ValueError, TypeError, KeyError, IndexError, RecursionError):
        _fail()


def write_zone_change_dependency_package(root, records):
    """Write a new or empty directory without overwriting retained evidence."""
    raw = {name: (record.serialize() + "\n").encode("utf-8") for name, record in records.items()}
    manifest = package_manifest(records, raw)
    root = Path(root)
    if any(path.is_symlink() for path in (root, *root.parents)):
        _fail("symlink package destination forbidden")
    if root.exists() and (not root.is_dir() or any(root.iterdir())):
        _fail("append-only destination must be a new or empty directory")
    root.mkdir(parents=True, exist_ok=True)
    for name in sorted(raw):
        with (root / name).open("xb") as stream:
            stream.write(raw[name])
    with (root / "manifest.json").open("xb") as stream:
        stream.write((deterministic_json(manifest) + "\n").encode("utf-8"))
    return manifest


def composite_coverage_view(records, manifest):
    """Resolve five component package IDs into a read-only derived view."""
    raw = {name: (record.serialize() + "\n").encode("utf-8") for name, record in records.items()}
    if deterministic_json(manifest) != deterministic_json(package_manifest(records, raw)):
        _fail("exact enclosing manifest required for composite view")
    view = records["composite-coverage.json"].to_dict()
    components = view["projection_components"]
    if (len(components) != 5 or components[4].pop("package_binding", None) !=
            "THIS_ENCLOSING_ZONE_CHANGE_DEPENDENCY_PACKAGE"):
        _fail("composite self-package binding missing")
    components[4]["package_id"] = manifest["package_id"]
    return {"view_kind": "RESOLVED_READ_ONLY_COMPOSITE_VIEW",
            "retained_composite_coverage_id": view["composite_coverage_id"],
            "projection_components": components,
            "total_projected_rule_count": view["total_projected_rule_count"],
            "projected_references": view["projected_references"],
            "execution_authorized": False, "real_rules_executable": False}
