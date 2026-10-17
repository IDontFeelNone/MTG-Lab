"""Strict five-file append-only dependency package and deterministic rebuild.

The builder requires the actual externally verified TXT. The offline loader
validates retained metadata, authored scope, exact prior evidence and findings;
it cannot claim that source spans were re-read without that external artifact.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path

from evidence.contracts import deterministic_json, sha256_identity
from gameplay_rules.errors import GameplayContractError
from gameplay_rules.execution_design.package import load_design_package
from gameplay_rules.source_evidence.artifacts import _open_regular_no_symlinks
from .dependency_contracts import DependencyProjection
from .dependency_reports import (
    CANONICAL_MAIN, DESIGN_PACKAGE_ID, HISTORICAL_ACQUISITION_ID,
    DirectClosureReview, CompositeCoverage, ExecutionReadinessReassessment,
    build_dependency_reports,
)
from .dependency_source import build_dependency_projection
from .package import load_projection_package
from .contracts import ARTIFACT_REVIEW_PACKAGE_ID
from gameplay_rules.execution_design.contracts import PROJECTION_ID, PROJECTION_PACKAGE_ID

PACKAGE_SCHEMA = "gameplay-cr-foundational-dependency-package-v1"
RECORD_TYPES = {
    "projection.json": DependencyProjection,
    "closure-review.json": DirectClosureReview,
    "composite-coverage.json": CompositeCoverage,
    "execution-readiness-reassessment.json": ExecutionReadinessReassessment,
}


def _fail(message="invalid dependency package integrity or boundary"):
    raise GameplayContractError("foundational_dependency_package", message)


def _unique(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            _fail("duplicate JSON field")
        result[key] = value
    return result


def _nonfinite(_value):
    _fail("non-finite JSON value")


def _root(root):
    root = Path(root)
    if not root.is_dir() or any(path.is_symlink() for path in (root, *root.parents)):
        _fail("regular package directory without symlink ancestors required")
    return root


def _read(path):
    descriptor = _open_regular_no_symlinks(path)
    if descriptor is None:
        _fail("regular package file without symlinks required")
    with os.fdopen(descriptor, "rb") as stream:
        before = os.fstat(stream.fileno())
        if before.st_nlink != 1:
            _fail("hard-linked package files forbidden")
        data = stream.read(128_001)
        after = os.fstat(stream.fileno())
        if ((before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns, before.st_ctime_ns)
                != (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns, after.st_ctime_ns)):
            _fail("package file changed while reading")
    if len(data) > 128_000:
        _fail("package metadata exceeds bounded size")
    return data


def _prior_evidence(*, projection_root, design_root, artifact_review_root, source_root, discovery_root):
    roots = {"artifact_review_root": artifact_review_root, "source_root": source_root,
             "discovery_root": discovery_root}
    original = load_projection_package(projection_root, **roots)
    design = load_design_package(design_root, projection_root=projection_root, **roots)
    return original, design


def build_dependency_package(artifact_path, *, projection_root, design_root,
                             artifact_review_root, source_root, discovery_root):
    """Re-read exact external source and return four review records; write nothing."""
    projection = build_dependency_projection(artifact_path,
        artifact_review_root=artifact_review_root, source_root=source_root, discovery_root=discovery_root)
    original, design = _prior_evidence(projection_root=projection_root, design_root=design_root,
        artifact_review_root=artifact_review_root, source_root=source_root, discovery_root=discovery_root)
    return {"projection.json": projection,
            **build_dependency_reports(projection, original, design)}


def package_manifest(records, raw_files):
    """Bind canonical bytes and separate identities without a circular package ID."""
    if set(records) != set(RECORD_TYPES) or set(raw_files) != set(RECORD_TYPES):
        _fail("exactly four authored records required")
    for name, cls in RECORD_TYPES.items():
        if not isinstance(records[name], cls):
            _fail("typed authored records required")
        records[name].verify()
        if raw_files[name] != (records[name].serialize() + "\n").encode("utf-8"):
            _fail("noncanonical record bytes")
    projection = records["projection.json"]
    closure = records["closure-review.json"]
    composite = records["composite-coverage.json"]
    reassessment = records["execution-readiness-reassessment.json"]
    for report in (closure, composite, reassessment):
        if report.dependency_projection_id != projection.identity:
            _fail("report belongs to another dependency projection")
    if (composite.closure_review_id != closure.identity or reassessment.closure_review_id != closure.identity
            or reassessment.composite_coverage_id != composite.identity):
        _fail("report chain belongs to another evidence set")
    body = {
        "schema_version": PACKAGE_SCHEMA, "canonical_base": CANONICAL_MAIN,
        "prior_artifact_review_package_id": ARTIFACT_REVIEW_PACKAGE_ID,
        "original_projection_package_id": PROJECTION_PACKAGE_ID,
        "original_projection_id": PROJECTION_ID, "execution_design_package_id": DESIGN_PACKAGE_ID,
        "dependency_projection_id": projection.identity, "closure_review_id": closure.identity,
        "composite_coverage_id": composite.identity,
        "execution_readiness_reassessment_id": reassessment.identity,
        "source_binding": projection.to_dict()["source_binding"],
        "files": {name: {"sha256": hashlib.sha256(raw_files[name]).hexdigest(),
                         "bytes": len(raw_files[name])} for name in sorted(RECORD_TYPES)},
        "selected_rule_count": 12, "composite_projected_rule_count": 32,
        "additional_rules_projected": [], "status": "DIRECT_FOUNDATIONAL_DEPENDENCIES_PROJECTED",
        "review_state": "PROJECTED_FOR_REVIEW", "semantic_closure": "SEMANTIC_CLOSURE_OPEN",
        "overall_execution_readiness": "BLOCKED", "readiness_code": "REAL_EXECUTION_PROFILE_NOT_READY",
        "execution_authorized": False, "real_rules_executable": False,
        "owner_execution_approval": "NOT_GRANTED", "source_body_retained": False,
        "admission_eligible": False, "source_policy_clearance": "not_granted",
        "permissions": {key: "NOT_ESTABLISHED" for key in
            ("private_retention", "redistribution", "free_service", "commercial_service", "ai_export")},
        "historical_acquisition_identity": HISTORICAL_ACQUISITION_ID,
    }
    return {**body, "package_id": "sha256:" + sha256_identity({"domain": PACKAGE_SCHEMA, "content": body})}


def load_dependency_package(root, *, projection_root, design_root,
                            artifact_review_root, source_root, discovery_root):
    """Verify exactly five files offline, reconstructing all append-only findings.

    Relocating this package or its explicitly supplied lineage roots does not
    change its contents or identities. No absolute paths enter retained data.
    Optional fresh span proof is provided by verify_dependency_projection_source.
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
        manifest = json.loads(manifest_raw, object_pairs_hook=_unique, parse_constant=_nonfinite)
        expected_manifest = package_manifest(records, raw)
        if (deterministic_json(manifest) != deterministic_json(expected_manifest) or
                manifest_raw != (deterministic_json(expected_manifest) + "\n").encode("utf-8")):
            _fail("manifest does not match canonical package contents")
        original, design = _prior_evidence(projection_root=projection_root, design_root=design_root,
            artifact_review_root=artifact_review_root, source_root=source_root, discovery_root=discovery_root)
        expected = build_dependency_reports(records["projection.json"], original, design)
        if any(records[name].to_dict() != expected[name].to_dict() for name in expected):
            _fail("closure/composite/reassessment findings do not reproduce")
        return records
    except GameplayContractError:
        raise
    except (OSError, ValueError, TypeError, KeyError, RecursionError):
        _fail()


def write_dependency_package(root, records):
    """Write only a new empty package directory; never replace prior evidence."""
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
