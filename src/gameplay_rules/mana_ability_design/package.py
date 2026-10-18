"""Append-only offline package for the non-executable 605 dependency design.

Six authored records bind immutable retained rule identities and explicitly
unverified PM design observations. A loader independently rebuilds every record
from that fixed evidence, preventing coherently rehashed findings from acquiring
authority. Neither construction nor loading reads an external CR artifact.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from evidence.contracts import deterministic_json, sha256_identity
from gameplay_rules.errors import GameplayContractError
from gameplay_rules.projection.dependency_package import _read, _root

from .behavior import ManaAbilityBehaviorDesign
from .classification import ManaAbilityClassificationDesign
from .common import CANONICAL_MAIN, FLAGS, _json
from .consumers import ManaAbilityConsumerMatrix
from .controller import ManaAbilityControllerDesign
from .evidence import HISTORICAL_ACQUISITION_ID, RETAINED_BINDING
from .frontier import ManaAbilityProjectionFrontier
from .readiness import ManaAbilityReadiness


PACKAGE_SCHEMA = "gameplay-mana-ability-dependency-design-package-v1"
RECORD_TYPES = {
    "classification-design.json": ManaAbilityClassificationDesign,
    "behavior-design.json": ManaAbilityBehaviorDesign,
    "controller-design.json": ManaAbilityControllerDesign,
    "consumer-bindings.json": ManaAbilityConsumerMatrix,
    "projection-frontier.json": ManaAbilityProjectionFrontier,
    "readiness.json": ManaAbilityReadiness,
}


def _fail(message="invalid mana-ability design package integrity or boundary"):
    raise GameplayContractError("mana_ability_design_package", message)


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
        _fail("exactly six authored design records required")
    for name, cls in RECORD_TYPES.items():
        if type(records[name]) is not cls:
            _fail("typed authored design records required")
        records[name].verify()


def _check_links(value, identities):
    """Every present design-identity link belongs to this exact evidence set."""
    if isinstance(value, dict):
        for key, item in value.items():
            if key in identities and item != identities[key]:
                _fail("design record belongs to another design evidence set")
            _check_links(item, identities)
    elif isinstance(value, list):
        for item in value:
            _check_links(item, identities)


def package_manifest(records, raw_files=None):
    """Bind canonical authored bytes, eight prior packages and unchanged count."""
    try:
        _validate_records(records)
        canonical = {name: (record.serialize() + "\n").encode("utf-8")
                     for name, record in records.items()}
        if raw_files is None:
            raw_files = canonical
        if not isinstance(raw_files, dict) or set(raw_files) != set(RECORD_TYPES):
            _fail("exactly six canonical record byte sequences required")
        identities = {record.ID_FIELD: record.identity for record in records.values()}
        if (len(identities) != len(RECORD_TYPES) or
                len(set(identities.values())) != len(RECORD_TYPES)):
            _fail("distinct design identities and identity fields required")
        for name, record in records.items():
            if (type(raw_files[name]) is not bytes or len(raw_files[name]) > 128_000 or
                    raw_files[name] != canonical[name]):
                _fail("noncanonical or oversized record bytes")
            _check_links(record.to_dict(), identities)
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
            "projected_rule_count_before": 68,
            "projected_rule_count_after": 68,
            "additional_rules_projected": [],
            "source_artifact_required": False,
            "source_anchors_created": False,
            "source_authority": "RETAINED_REPOSITORY_EVIDENCE_AND_PM_DESIGN_INPUT_ONLY",
            "fictional_authority_finding": "FICTIONAL_MANA_DOES_NOT_SATISFY_REAL_605",
            "source_coverage": "DESIGN_SCOPED",
            "overall_execution_readiness": "BLOCKED",
            "readiness_code": "REAL_EXECUTION_PROFILE_NOT_READY",
            "historical_acquisition_identity": HISTORICAL_ACQUISITION_ID,
        }
        return {**body, "package_id": "sha256:" + sha256_identity({
            "domain": PACKAGE_SCHEMA, "content": body})}
    except GameplayContractError:
        raise
    except (ValueError, TypeError, KeyError, AttributeError, UnicodeError, RecursionError):
        _fail()


def load_design_package(root, *, review_root):
    """Verify seven canonical regular files and rebuild every finding offline.

    Package and lineage paths never enter design identities. Offline success
    establishes reproducible design metadata, not new 605 source verification.
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
        manifest = json.loads(manifest_raw, object_pairs_hook=_unique,
                              parse_constant=_nonfinite)
        expected_manifest = package_manifest(records, raw_files)
        if (deterministic_json(manifest) != deterministic_json(expected_manifest) or
                manifest_raw != (deterministic_json(expected_manifest) + "\n").encode("utf-8")):
            _fail("manifest differs from canonical design package contents")
        from .builder import build_design_package
        expected = build_design_package(review_root=review_root)
        if (set(expected) != set(RECORD_TYPES) or any(
                records[name].to_dict() != expected[name].to_dict() for name in RECORD_TYPES)):
            _fail("design findings do not reproduce from retained repository evidence")
        return records
    except GameplayContractError:
        raise
    except (OSError, ValueError, TypeError, KeyError, AttributeError,
            UnicodeError, RecursionError):
        _fail()


def write_design_package(root, records):
    """Write a new or empty directory without replacing any retained evidence."""
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
    except (OSError, ValueError, TypeError, KeyError, AttributeError,
            UnicodeError, RecursionError):
        _fail()
