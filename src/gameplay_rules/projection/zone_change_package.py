"""Strict append-only zone-change exception package and offline reproduction.

Fresh construction reads the externally verified TXT. Offline loading proves
canonical authored metadata and exact immutable lineage, without claiming a
fresh inspection of source bytes that are deliberately absent from the package.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from evidence.contracts import deterministic_json, sha256_identity
from gameplay_rules.errors import GameplayContractError
from gameplay_rules.execution_design.package import load_design_package
from gameplay_rules.execution_design.contracts import PROJECTION_ID, PROJECTION_PACKAGE_ID
from .contracts import ARTIFACT_REVIEW_PACKAGE_ID
from .dependency_package import load_dependency_package, _read, _root
from .object_control_package import load_object_control_package
from .package import load_projection_package
from .zone_change_contracts import ZoneChangeProjection
from .zone_change_reports import (
    CANONICAL_MAIN, DEPENDENCY_PROJECTION_ID, DEPENDENCY_PACKAGE_ID,
    OBJECT_CONTROL_PROJECTION_ID, OBJECT_CONTROL_PACKAGE_ID, OBJECT_CONTROL_ANOMALY_ID,
    DESIGN_PACKAGE_ID, HISTORICAL_ACQUISITION_ID, FamilyClosureReview,
    ZoneChangeReadinessReassessment, ZoneChangeCompositeCoverage, build_zone_change_reports,
)
from .zone_change_source import build_zone_change_source
from .zone_change_scope import SELECTED_REFERENCES

PACKAGE_SCHEMA = "gameplay-cr-zone-change-exception-package-v1"
RECORD_TYPES = {
    "projection.json": ZoneChangeProjection,
    "family-closure-review.json": FamilyClosureReview,
    "zone-change-readiness-reassessment.json": ZoneChangeReadinessReassessment,
    "composite-coverage.json": ZoneChangeCompositeCoverage,
}


def _fail(message="invalid zone-change package integrity or boundary"):
    raise GameplayContractError("zone_change_package", message)


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
                    artifact_review_root, source_root, discovery_root):
    roots = {"artifact_review_root": artifact_review_root, "source_root": source_root,
             "discovery_root": discovery_root}
    original = load_projection_package(projection_root, **roots)
    design = load_design_package(design_root, projection_root=projection_root, **roots)
    dependency = load_dependency_package(dependency_root, projection_root=projection_root,
                                         design_root=design_root, **roots)
    control = load_object_control_package(object_control_root, projection_root=projection_root,
        design_root=design_root, dependency_root=dependency_root, **roots)
    return original, design, dependency, control


def build_zone_change_package(artifact_path, *, projection_root, design_root, dependency_root,
                              object_control_root, artifact_review_root, source_root, discovery_root):
    """Require actual exact source and return four authored records; write nothing."""
    projection = build_zone_change_source(artifact_path, artifact_review_root=artifact_review_root,
                                         source_root=source_root, discovery_root=discovery_root)
    original, design, dependency, control = _prior_evidence(projection_root=projection_root,
        design_root=design_root, dependency_root=dependency_root, object_control_root=object_control_root,
        artifact_review_root=artifact_review_root, source_root=source_root, discovery_root=discovery_root)
    return {"projection.json": projection,
            **build_zone_change_reports(projection, original, design, dependency, control)}


def package_manifest(records, raw_files):
    """Bind four canonical records and preserve all four component identities."""
    if set(records) != set(RECORD_TYPES) or set(raw_files) != set(RECORD_TYPES):
        _fail("exactly four authored records required")
    for name, cls in RECORD_TYPES.items():
        if type(records[name]) is not cls:
            _fail("typed authored records required")
        records[name].verify()
        if raw_files[name] != (records[name].serialize() + "\n").encode("utf-8"):
            _fail("noncanonical record bytes")
    projection = records["projection.json"]
    family = records["family-closure-review.json"]
    reassessment = records["zone-change-readiness-reassessment.json"]
    composite = records["composite-coverage.json"]
    for report in (family, reassessment, composite):
        if report.zone_change_projection_id != projection.identity:
            _fail("report belongs to another projection")
        if report.to_dict()["source_binding"] != projection.to_dict()["source_binding"]:
            _fail("report source binding differs from projection")
    if (reassessment.family_closure_review_id != family.identity or
            composite.family_closure_review_id != family.identity or
            composite.zone_change_readiness_reassessment_id != reassessment.identity):
        _fail("report chain belongs to another evidence set")
    refs = [row["rule_reference"] for row in projection.to_dict()["rules"]]
    family_value = family.to_dict()
    composite_value = composite.to_dict()
    if (tuple(refs) != tuple(SELECTED_REFERENCES) or
            family_value["direct_family_coverage"]["references"] != refs or
            family_value["direct_family_coverage"]["expected_count"] != len(refs) or
            family_value["direct_family_coverage"]["projected_count"] != len(refs) or
            family_value["lettering_review"] != projection.to_dict()["lettering_policy"] or
            composite_value["projection_components"][-1] != {
                "projection_id": projection.identity, "package_binding": "THIS_ENCLOSING_ZONE_CHANGE_PACKAGE",
                "projected_references": refs, "mutated": False}):
        _fail("exact direct family and new component binding required")
    body = {
        "schema_version": PACKAGE_SCHEMA, "canonical_base": CANONICAL_MAIN,
        "prior_artifact_review_package_id": ARTIFACT_REVIEW_PACKAGE_ID,
        "foundational_projection_package_id": PROJECTION_PACKAGE_ID, "foundational_projection_id": PROJECTION_ID,
        "execution_design_package_id": DESIGN_PACKAGE_ID,
        "dependency_projection_package_id": DEPENDENCY_PACKAGE_ID, "dependency_projection_id": DEPENDENCY_PROJECTION_ID,
        "object_control_projection_package_id": OBJECT_CONTROL_PACKAGE_ID,
        "object_control_projection_id": OBJECT_CONTROL_PROJECTION_ID,
        "object_control_source_anomaly_id": OBJECT_CONTROL_ANOMALY_ID,
        "zone_change_projection_id": projection.identity, "family_closure_review_id": family.identity,
        "zone_change_readiness_reassessment_id": reassessment.identity, "composite_coverage_id": composite.identity,
        "source_binding": projection.to_dict()["source_binding"],
        "files": {name: {"sha256": hashlib.sha256(raw_files[name]).hexdigest(), "bytes": len(raw_files[name])}
                  for name in sorted(RECORD_TYPES)},
        "selected_rule_count": len(refs), "selected_references": refs,
        "composite_projected_rule_count": composite_value["total_projected_rule_count"],
        "additional_rules_projected": [], "parent_reprojected": False,
        "lettering_policy": projection.to_dict()["lettering_policy"],
        "status": family_value["status"], "family_status": family_value["direct_family_coverage"]["status"],
        "review_state": "PROJECTED_FOR_REVIEW", "semantic_closure": family_value["semantic_closure"],
        "overall_execution_readiness": reassessment.overall_execution_readiness,
        "readiness_code": reassessment.readiness_code, "execution_authorized": False,
        "real_rules_executable": False, "owner_execution_approval": "NOT_GRANTED",
        "source_body_retained": False, "admission_eligible": False, "source_policy_clearance": "not_granted",
        "permissions": {key: "NOT_ESTABLISHED" for key in
            ("private_retention", "redistribution", "free_service", "commercial_service", "ai_export")},
        "historical_acquisition_identity": HISTORICAL_ACQUISITION_ID,
    }
    return {**body, "package_id": "sha256:" + sha256_identity({"domain": PACKAGE_SCHEMA, "content": body})}


def load_zone_change_package(root, *, projection_root, design_root, dependency_root,
                             object_control_root, artifact_review_root, source_root, discovery_root):
    """Verify exactly five canonical regular files and reproduce every finding.

    All roots are caller-supplied and remain outside retained metadata. Relocation
    preserves identities. Rechecking external source spans is a separate verifier.
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
        original, design, dependency, control = _prior_evidence(projection_root=projection_root,
            design_root=design_root, dependency_root=dependency_root, object_control_root=object_control_root,
            artifact_review_root=artifact_review_root, source_root=source_root, discovery_root=discovery_root)
        expected = build_zone_change_reports(records["projection.json"], original, design, dependency, control)
        if any(records[name].to_dict() != expected[name].to_dict() for name in expected):
            _fail("family/zone-change/composite findings do not reproduce")
        return records
    except GameplayContractError:
        raise
    except (OSError, ValueError, TypeError, KeyError, IndexError, RecursionError):
        _fail()


def write_zone_change_package(root, records):
    """Write only a new or empty directory; never overwrite retained evidence."""
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
    """Resolve four literal component package IDs without writing a projection."""
    raw = {name: (record.serialize() + "\n").encode("utf-8") for name, record in records.items()}
    if deterministic_json(manifest) != deterministic_json(package_manifest(records, raw)):
        _fail("exact enclosing manifest required for composite view")
    view = records["composite-coverage.json"].to_dict()
    components = view["projection_components"]
    if len(components) != 4 or components[3].pop("package_binding", None) != "THIS_ENCLOSING_ZONE_CHANGE_PACKAGE":
        _fail("composite self-package binding missing")
    components[3]["package_id"] = manifest["package_id"]
    return {"view_kind": "RESOLVED_READ_ONLY_COMPOSITE_VIEW", "retained_composite_coverage_id": view["composite_coverage_id"],
            "projection_components": components, "total_projected_rule_count": view["total_projected_rule_count"],
            "projected_references": view["projected_references"], "execution_authorized": False,
            "real_rules_executable": False}
