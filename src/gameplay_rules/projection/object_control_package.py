"""Strict six-file append-only object-control exception evidence package.

Fresh construction requires the exact external source artifact. Offline loading
checks canonical metadata, exact immutable ancestors, and reproducible findings;
it does not claim to have freshly inspected external source spans.
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
from .package import load_projection_package
from .object_control_contracts import ObjectControlProjection, SourceAnomaly
from .object_control_reports import (
    CANONICAL_MAIN, DEPENDENCY_PROJECTION_ID, DEPENDENCY_PACKAGE_ID,
    DESIGN_PACKAGE_ID, HISTORICAL_ACQUISITION_ID,
    FamilyClosureReview, ControlReadinessReassessment, ObjectControlCompositeCoverage,
    build_object_control_reports,
)
from .object_control_source import build_object_control_source

PACKAGE_SCHEMA = "gameplay-cr-object-control-exception-package-v1"
RECORD_TYPES = {
    "projection.json": ObjectControlProjection,
    "source-anomaly.json": SourceAnomaly,
    "family-closure-review.json": FamilyClosureReview,
    "control-readiness-reassessment.json": ControlReadinessReassessment,
    "composite-coverage.json": ObjectControlCompositeCoverage,
}


def _fail(message="invalid object-control package integrity or boundary"):
    raise GameplayContractError("object_control_package", message)


def _pairs(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            _fail("duplicate JSON field")
        result[key] = value
    return result


def _nonfinite(_value):
    _fail("non-finite JSON value")


def _prior_evidence(*, projection_root, design_root, dependency_root,
                    artifact_review_root, source_root, discovery_root):
    roots = {"artifact_review_root": artifact_review_root, "source_root": source_root,
             "discovery_root": discovery_root}
    original = load_projection_package(projection_root, **roots)
    design = load_design_package(design_root, projection_root=projection_root, **roots)
    dependency = load_dependency_package(dependency_root, projection_root=projection_root,
                                         design_root=design_root, **roots)
    return original, design, dependency


def build_object_control_package(artifact_path, *, projection_root, design_root, dependency_root,
                                 artifact_review_root, source_root, discovery_root):
    """Read actual verified source and return five authored records; write nothing."""
    projection, anomaly = build_object_control_source(artifact_path,
        artifact_review_root=artifact_review_root, source_root=source_root, discovery_root=discovery_root)
    original, design, dependency = _prior_evidence(projection_root=projection_root,
        design_root=design_root, dependency_root=dependency_root,
        artifact_review_root=artifact_review_root, source_root=source_root, discovery_root=discovery_root)
    return {"projection.json": projection, "source-anomaly.json": anomaly,
            **build_object_control_reports(projection, anomaly, original, design, dependency)}


def package_manifest(records, raw_files):
    """Bind canonical bytes and separate identities without a circular package ID."""
    if set(records) != set(RECORD_TYPES) or set(raw_files) != set(RECORD_TYPES):
        _fail("exactly five authored records required")
    for name, cls in RECORD_TYPES.items():
        if not isinstance(records[name], cls):
            _fail("typed authored records required")
        records[name].verify()
        if raw_files[name] != (records[name].serialize() + "\n").encode("utf-8"):
            _fail("noncanonical record bytes")
    projection = records["projection.json"]
    anomaly = records["source-anomaly.json"]
    family = records["family-closure-review.json"]
    reassessment = records["control-readiness-reassessment.json"]
    composite = records["composite-coverage.json"]
    if (anomaly.to_dict()["source_binding"] != projection.to_dict()["source_binding"] or
            anomaly.to_dict()["enumerated_refs"] !=
            [row["rule_reference"] for row in projection.to_dict()["rules"]]):
        _fail("source anomaly must bind the same artifact and exact selected family")
    for report in (family, reassessment, composite):
        if report.object_control_projection_id != projection.identity or report.source_anomaly_id != anomaly.identity:
            _fail("report belongs to another projection or source anomaly")
        if report.to_dict()["source_binding"] != projection.to_dict()["source_binding"]:
            _fail("report source binding differs from projection")
    if (reassessment.family_closure_review_id != family.identity or
            composite.family_closure_review_id != family.identity or
            composite.control_readiness_reassessment_id != reassessment.identity):
        _fail("report chain belongs to another evidence set")
    body = {
        "schema_version": PACKAGE_SCHEMA, "canonical_base": CANONICAL_MAIN,
        "prior_artifact_review_package_id": ARTIFACT_REVIEW_PACKAGE_ID,
        "foundational_projection_package_id": PROJECTION_PACKAGE_ID,
        "foundational_projection_id": PROJECTION_ID,
        "execution_design_package_id": DESIGN_PACKAGE_ID,
        "dependency_projection_package_id": DEPENDENCY_PACKAGE_ID,
        "dependency_projection_id": DEPENDENCY_PROJECTION_ID,
        "object_control_projection_id": projection.identity, "source_anomaly_id": anomaly.identity,
        "family_closure_review_id": family.identity,
        "control_readiness_reassessment_id": reassessment.identity,
        "composite_coverage_id": composite.identity,
        "source_binding": projection.to_dict()["source_binding"],
        "files": {name: {"sha256": hashlib.sha256(raw_files[name]).hexdigest(),
                         "bytes": len(raw_files[name])} for name in sorted(RECORD_TYPES)},
        "selected_rule_count": 7, "composite_projected_rule_count": 39,
        "additional_rules_projected": [], "parent_reprojected": False,
        "status": "OBJECT_CONTROL_EXCEPTION_FAMILY_PROJECTED",
        "family_status": "DIRECT_EXCEPTION_FAMILY_REPRESENTED", "review_state": "PROJECTED_FOR_REVIEW",
        "semantic_closure": "SEMANTIC_CLOSURE_OPEN", "overall_execution_readiness": "BLOCKED",
        "readiness_code": "REAL_EXECUTION_PROFILE_NOT_READY", "execution_authorized": False,
        "real_rules_executable": False, "owner_execution_approval": "NOT_GRANTED",
        "source_body_retained": False, "admission_eligible": False,
        "source_policy_clearance": "not_granted",
        "permissions": {key: "NOT_ESTABLISHED" for key in
            ("private_retention", "redistribution", "free_service", "commercial_service", "ai_export")},
        "historical_acquisition_identity": HISTORICAL_ACQUISITION_ID,
    }
    return {**body, "package_id": "sha256:" + sha256_identity({"domain": PACKAGE_SCHEMA, "content": body})}


def load_object_control_package(root, *, projection_root, design_root, dependency_root,
                                artifact_review_root, source_root, discovery_root):
    """Verify six canonical files offline and reconstruct every review finding."""
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
        original, design, dependency = _prior_evidence(projection_root=projection_root,
            design_root=design_root, dependency_root=dependency_root,
            artifact_review_root=artifact_review_root, source_root=source_root, discovery_root=discovery_root)
        expected = build_object_control_reports(records["projection.json"], records["source-anomaly.json"],
                                                original, design, dependency)
        if any(records[name].to_dict() != expected[name].to_dict() for name in expected):
            _fail("family/control/composite findings do not reproduce")
        return records
    except GameplayContractError:
        raise
    except (OSError, ValueError, TypeError, KeyError, RecursionError):
        _fail()


def write_object_control_package(root, records):
    """Write only a new or empty directory; never overwrite existing evidence."""
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
    """Resolve all three literal component package IDs in a read-only derived view.

    The retained record uses an enclosing-package binding for its own component,
    avoiding a self-referential content hash. The manifest supplies that identity.
    This helper writes nothing and creates no replacement projection.
    """
    raw = {name: (record.serialize() + "\n").encode("utf-8") for name, record in records.items()}
    if deterministic_json(manifest) != deterministic_json(package_manifest(records, raw)):
        _fail("exact enclosing manifest required for composite view")
    view = records["composite-coverage.json"].to_dict()
    components = view["projection_components"]
    if len(components) != 3 or components[2].pop("package_binding", None) != "THIS_ENCLOSING_OBJECT_CONTROL_PACKAGE":
        _fail("composite self-package binding missing")
    components[2]["package_id"] = manifest["package_id"]
    return {"view_kind": "RESOLVED_READ_ONLY_COMPOSITE_VIEW", "retained_composite_coverage_id": view["composite_coverage_id"],
            "projection_components": components, "total_projected_rule_count": view["total_projected_rule_count"],
            "projected_references": view["projected_references"], "execution_authorized": False,
            "real_rules_executable": False}
