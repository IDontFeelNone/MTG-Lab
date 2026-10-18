"""Append-only offline package for non-executable Madness casting design.

The package contains authored design metadata and retained-evidence identities.
It neither reads a source artifact nor creates real-rule source anchors. Loading
independently rebuilds every finding from the immutable repository evidence so
that coherently rehashed, altered findings do not acquire review authority.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from evidence.contracts import deterministic_json, sha256_identity
from gameplay_rules.errors import GameplayContractError
from gameplay_rules.projection.dependency_package import _read, _root
from gameplay_rules.projection.zone_change_dependency_reports import HISTORICAL_ACQUISITION_ID

from .anchors import MultiLineSourceAnchorDesign
from .builder import MadnessCastingReadiness, ProjectionFrontierDesign, build_design_package
from .common import CANONICAL_MAIN, FLAGS, _json
from .costs import CostModelDesign
from .evidence import RETAINED_BINDING
from .stages import CastingSubprocedureDesign


PACKAGE_SCHEMA = "gameplay-madness-casting-dependency-design-package-v1"
RECORD_TYPES = {
    "source-anchor-design.json": MultiLineSourceAnchorDesign,
    "casting-subprocedure-design.json": CastingSubprocedureDesign,
    "cost-design.json": CostModelDesign,
    "madness-readiness.json": MadnessCastingReadiness,
    "projection-frontier.json": ProjectionFrontierDesign,
}


def _fail(message="invalid Madness casting design package integrity or boundary"):
    raise GameplayContractError("madness_casting_design_package", message)


def _unique(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            _fail("duplicate JSON field")
        result[key] = value
    return result


def _nonfinite(_value):
    _fail("non-finite JSON value")


def _validate_records(records):
    if not isinstance(records, dict) or set(records) != set(RECORD_TYPES):
        _fail("exactly five authored design records required")
    for name, cls in RECORD_TYPES.items():
        if type(records[name]) is not cls:
            _fail("typed authored design records required")
        records[name].verify()


def _check_links(value, identities):
    """All present design-identity links must identify this evidence set."""
    if isinstance(value, dict):
        for key, item in value.items():
            if key in identities and item != identities[key]:
                _fail("design record belongs to another design evidence set")
            _check_links(item, identities)
    elif isinstance(value, list):
        for item in value:
            _check_links(item, identities)


def package_manifest(records, raw_files):
    """Bind canonical authored bytes, immutable evidence, and unchanged coverage."""
    try:
        _validate_records(records)
        if not isinstance(raw_files, dict) or set(raw_files) != set(RECORD_TYPES):
            _fail("exactly five canonical record byte sequences required")
        identities = {record.ID_FIELD: record.identity for record in records.values()}
        if len(identities) != len(RECORD_TYPES):
            _fail("distinct design identity fields required")
        for name, record in records.items():
            if (type(raw_files[name]) is not bytes or len(raw_files[name]) > 128_000 or
                    raw_files[name] != (record.serialize() + "\n").encode("utf-8")):
                _fail("noncanonical or oversized record bytes")
            _check_links(record.to_dict(), identities)
        if records["cost-design.json"].casting_design_id != records["casting-subprocedure-design.json"].identity:
            _fail("cost model belongs to another casting subprocedure design")
        body = {
            "schema_version": PACKAGE_SCHEMA,
            **_json(FLAGS),
            "canonical_base": CANONICAL_MAIN,
            "retained_evidence_binding": _json(RETAINED_BINDING),
            "record_ids": identities,
            "files": {
                name: {"sha256": hashlib.sha256(raw_files[name]).hexdigest(),
                       "bytes": len(raw_files[name])}
                for name in sorted(RECORD_TYPES)
            },
            "projected_rule_count_before": 63,
            "projected_rule_count_after": 63,
            "additional_rules_projected": [],
            "source_artifact_required": False,
            "source_anchors_created": False,
            "source_authority": "RETAINED_REPOSITORY_EVIDENCE_AND_PM_DESIGN_INPUT_ONLY",
            "overall_execution_readiness": "BLOCKED",
            "readiness_code": "REAL_EXECUTION_PROFILE_NOT_READY",
            "historical_acquisition_identity": HISTORICAL_ACQUISITION_ID,
        }
        return {**body, "package_id": "sha256:" + sha256_identity({"domain": PACKAGE_SCHEMA, "content": body})}
    except GameplayContractError:
        raise
    except (ValueError, TypeError, KeyError, AttributeError, UnicodeError, RecursionError):
        _fail()


def load_design_package(root, *, review_root):
    """Verify six canonical files and reproduce all findings without source TXT.

    Package paths and explicitly supplied retained-review paths never enter the
    retained records. Relocation therefore preserves every design identity.
    """
    try:
        root = _root(root)
        paths = list(root.iterdir())
        if {path.name for path in paths} != set(RECORD_TYPES) | {"manifest.json"}:
            _fail("unexpected or missing package file")
        if any(path.is_symlink() or not path.is_file() for path in paths):
            _fail("regular package files required")
        raw_files = {name: _read(root / name) for name in RECORD_TYPES}
        records = {name: cls.from_json(raw_files[name]) for name, cls in RECORD_TYPES.items()}
        manifest_raw = _read(root / "manifest.json")
        manifest = json.loads(manifest_raw, object_pairs_hook=_unique, parse_constant=_nonfinite)
        expected_manifest = package_manifest(records, raw_files)
        if (deterministic_json(manifest) != deterministic_json(expected_manifest) or
                manifest_raw != (deterministic_json(expected_manifest) + "\n").encode("utf-8")):
            _fail("manifest differs from canonical design package contents")
        expected = build_design_package(review_root=review_root)
        if (set(expected) != set(RECORD_TYPES) or any(
                records[name].to_dict() != expected[name].to_dict() for name in RECORD_TYPES)):
            _fail("design findings do not reproduce from retained repository evidence")
        return records
    except GameplayContractError:
        raise
    except (OSError, ValueError, TypeError, KeyError, AttributeError, UnicodeError, RecursionError):
        _fail()


def write_design_package(root, records):
    """Write a new or empty directory without replacing retained evidence."""
    try:
        _validate_records(records)
        raw_files = {name: (record.serialize() + "\n").encode("utf-8")
                     for name, record in records.items()}
        manifest = package_manifest(records, raw_files)
        root = Path(root)
        if any(path.is_symlink() for path in (root, *root.parents)):
            _fail("symlink package destination forbidden")
        if root.exists() and (not root.is_dir() or any(root.iterdir())):
            _fail("append-only destination must be a new or empty directory")
        root.mkdir(parents=True, exist_ok=True)
        for name in sorted(raw_files):
            with (root / name).open("xb") as stream:
                stream.write(raw_files[name])
        with (root / "manifest.json").open("xb") as stream:
            stream.write((deterministic_json(manifest) + "\n").encode("utf-8"))
        return manifest
    except GameplayContractError:
        raise
    except (OSError, ValueError, TypeError, KeyError, AttributeError, UnicodeError, RecursionError):
        _fail()
