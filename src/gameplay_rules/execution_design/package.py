"""Offline verification of the fixed, six-file non-executable design package."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path

from evidence.contracts import deterministic_json, sha256_identity
from gameplay_rules.errors import GameplayContractError
from gameplay_rules.source_evidence.artifacts import _open_regular_no_symlinks
from .builder import build_design_package
from .contracts import (CANONICAL_MAIN, PROJECTION_ID, PROJECTION_PACKAGE_ID, SOURCE_BINDING,
    FoundationalProjectionReview, RealRulesCapabilityMatrix,
    RealRulesExecutionProfileDesign, RealRulesActivationGateDesign, RealRulesExecutionReadiness)


PACKAGE_SCHEMA = "gameplay-real-execution-profile-design-package-v1"
RECORD_TYPES = {
    "projection-review.json": FoundationalProjectionReview,
    "capability-matrix.json": RealRulesCapabilityMatrix,
    "execution-profile-design.json": RealRulesExecutionProfileDesign,
    "activation-gates.json": RealRulesActivationGateDesign,
    "readiness.json": RealRulesExecutionReadiness,
}


def _fail():
    raise GameplayContractError("execution_design_package", "invalid design package integrity or boundary")


def _unique(pairs):
    value = {}
    for key, item in pairs:
        if key in value:
            _fail()
        value[key] = item
    return value


def _nonfinite(_value):
    _fail()


def _read(path):
    descriptor = _open_regular_no_symlinks(path)
    if descriptor is None:
        _fail()
    with os.fdopen(descriptor, "rb") as stream:
        data = stream.read(128_001)
    if len(data) > 128_000:
        _fail()
    return data


def package_manifest(records, raw_files):
    if set(records) != set(RECORD_TYPES) or set(raw_files) != set(RECORD_TYPES):
        _fail()
    for name, cls in RECORD_TYPES.items():
        if not isinstance(records[name], cls):
            _fail()
        records[name].verify()
        if raw_files[name] != (records[name].serialize() + "\n").encode("utf-8"):
            _fail()
    body = {
        "schema_version": PACKAGE_SCHEMA, "canonical_base": CANONICAL_MAIN,
        "foundational_projection_package_id": PROJECTION_PACKAGE_ID,
        "foundational_projection_id": PROJECTION_ID, "source_binding": dict(SOURCE_BINDING),
        "projection_review_id": records["projection-review.json"].identity,
        "execution_profile_design_id": records["execution-profile-design.json"].identity,
        "execution_readiness_id": records["readiness.json"].identity,
        "files": {name: {"sha256": hashlib.sha256(raw_files[name]).hexdigest(),
                         "bytes": len(raw_files[name])} for name in sorted(RECORD_TYPES)},
        "reviewed_rule_count": 20, "status": "DESIGN_ONLY",
        "overall_execution_readiness": "BLOCKED", "real_rules_executable": False,
        "execution_authorized": False, "projection_authorized": False,
        "owner_execution_approval": "NOT_GRANTED", "source_body_retained": False,
        "source_policy_clearance": "not_granted",
    }
    return {**body, "package_id": "sha256:" + sha256_identity({"domain": PACKAGE_SCHEMA, "content": body})}


def load_design_package(root, *, projection_root, artifact_review_root, source_root, discovery_root):
    """Check integrity, cross-record identities and deterministic gate findings.

    Rebuilding from the exact retained projection detects coherent rehashing of
    findings, anchors or gates. The original source TXT is never an input.
    """
    try:
        root = Path(root)
        if not root.is_dir() or any(path.is_symlink() for path in (root, *root.parents)):
            _fail()
        paths = list(root.iterdir())
        if {path.name for path in paths} != set(RECORD_TYPES) | {"manifest.json"}:
            _fail()
        if any(path.is_symlink() or not path.is_file() for path in paths):
            _fail()
        raw = {name: _read(root / name) for name in RECORD_TYPES}
        records = {name: cls.from_json(raw[name]) for name, cls in RECORD_TYPES.items()}
        manifest = json.loads(_read(root / "manifest.json"), object_pairs_hook=_unique, parse_constant=_nonfinite)
        if deterministic_json(manifest) != deterministic_json(package_manifest(records, raw)):
            _fail()
        expected = build_design_package(projection_root=projection_root,
            artifact_review_root=artifact_review_root, source_root=source_root, discovery_root=discovery_root)
        if any(records[name].to_dict() != expected[name].to_dict() for name in RECORD_TYPES):
            _fail()
        return records
    except GameplayContractError:
        raise
    except (OSError, ValueError, TypeError, KeyError, RecursionError):
        _fail()
