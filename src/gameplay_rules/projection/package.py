"""Strict offline integrity checks for the two-file review projection package."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path

from evidence.contracts import deterministic_json, sha256_identity
from gameplay_rules.errors import GameplayContractError
from gameplay_rules.source_evidence.artifacts import _open_regular_no_symlinks
from gameplay_rules.source_evidence.artifact_review import verify_artifact_review_package
from .contracts import ARTIFACT_REVIEW_PACKAGE_ID, FoundationalProjection


PACKAGE_SCHEMA = "gameplay-cr-foundational-projection-package-v1"


def _fail():
    raise GameplayContractError("foundational_projection_package", "invalid review package integrity or boundary")


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


def package_manifest(projection, projection_bytes):
    """Bind exact authored JSON bytes, separately from semantic projection ID."""
    if not isinstance(projection, FoundationalProjection):
        _fail()
    projection.verify()
    if projection_bytes != (projection.serialize() + "\n").encode("utf-8"):
        _fail()
    body = {"schema_version": PACKAGE_SCHEMA, "projection_id": projection.identity,
        "prior_artifact_review_package_id": ARTIFACT_REVIEW_PACKAGE_ID,
        "files": {"projection.json": {"sha256": hashlib.sha256(projection_bytes).hexdigest(),
                                       "bytes": len(projection_bytes)}},
        "selected_rule_count": 20, "source_body_retained": False,
        "real_rules_executable": False, "admission_eligible": False,
        "source_policy_clearance": "not_granted"}
    return {**body, "package_id": "sha256:" + sha256_identity({"domain": PACKAGE_SCHEMA, "content": body})}


def load_projection_package(root, *, artifact_review_root, source_root, discovery_root):
    """Validate retained metadata offline; actual span proof requires source access.

    This checks structure, authored scope, lineage and file/content hashes. It
    does not claim that source spans were re-read when the TXT is unavailable.
    """
    try:
        root = Path(root)
        if not root.is_dir() or any(path.is_symlink() for path in (root, *root.parents)):
            _fail()
        paths = list(root.iterdir())
        if {path.name for path in paths} != {"manifest.json", "projection.json"}:
            _fail()
        if any(path.is_symlink() or not path.is_file() for path in paths):
            _fail()
        raw = _read(root / "projection.json")
        projection = FoundationalProjection.from_json(raw)
        manifest = json.loads(_read(root / "manifest.json"), object_pairs_hook=_unique,
                              parse_constant=_nonfinite)
        expected = package_manifest(projection, raw)
        if deterministic_json(manifest) != deterministic_json(expected):
            _fail()
        lineage = verify_artifact_review_package(artifact_review_root,
            source_root=source_root, discovery_root=discovery_root)
        if lineage["package_id"] != ARTIFACT_REVIEW_PACKAGE_ID:
            _fail()
        return projection
    except GameplayContractError:
        raise
    except (OSError, ValueError, TypeError, KeyError, RecursionError):
        _fail()
