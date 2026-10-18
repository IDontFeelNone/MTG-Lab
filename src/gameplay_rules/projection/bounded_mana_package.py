"""Append-only, source-anchored package for thirteen bounded mana-ability source units.

Construction requires the exact external artifact. Offline loading checks the
canonical projection metadata, pins the nine prior immutable packages, and
independently rebuilds every authored review. It does not claim to re-read source
bytes, construct a runtime snapshot, or confer gameplay execution authority.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from evidence.contracts import deterministic_json, sha256_identity
from gameplay_rules.errors import GameplayContractError
from gameplay_rules.mana_ability_design.package import (
    load_design_package as load_mana_design_package,
    package_manifest as mana_design_manifest,
)
from .dependency_package import _read, _root
from .bounded_mana_contracts import (
    BoundedManaProjection, BoundedManaReview, CANONICAL_MAIN,
    PRIOR_PACKAGE_IDS, DESIGN_IDS, SELECTED_REFERENCES,
)


PACKAGE_SCHEMA = "gameplay-cr-bounded-mana-projection-package-v1"
HISTORICAL_ACQUISITION_ID = "sha256:669d7db9ebcaf97853058fd62f408ce3c6596d5dae0ee72ff39d2ba9df56bb53"
REVIEW_KINDS = {
    "design-source-correspondence.json": "design_source_correspondence",
    "family-closure-review.json": "family_closure_review",
    "consumer-reassessment.json": "consumer_reassessment",
    "classification-readiness.json": "classification_readiness",
    "behavior-readiness.json": "behavior_readiness",
    "overall-readiness.json": "overall_readiness",
    "composite-coverage.json": "composite_coverage",
}
RECORD_TYPES = {"projection.json": BoundedManaProjection,
                **{name: BoundedManaReview for name in REVIEW_KINDS}}


def _fail(message="invalid bounded mana ability package integrity or boundary"):
    raise GameplayContractError("bounded_mana_package", message)


def _unique(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            _fail("duplicate JSON field")
        result[key] = value
    return result


def _nonfinite(_value):
    _fail("non-finite JSON value")


def _canonical_raw(records):
    if not isinstance(records, dict) or set(records) != set(RECORD_TYPES):
        _fail("exactly eight authored records required")
    for name, cls in RECORD_TYPES.items():
        if type(records[name]) is not cls:
            _fail("typed authored records required")
        records[name].verify()
    return {name: (records[name].serialize() + "\n").encode("utf-8")
            for name in RECORD_TYPES}


def _source_roots(review_root):
    root = Path(review_root)
    return {
        "artifact_review_root": root / "gameplay-rules-artifact-verification",
        "source_root": root / "gameplay-rules-source-versioning",
        "discovery_root": root / "gameplay-rules-release-discovery-closure",
    }


def _prior_design(review_root):
    """The prior design's loader independently pins its eight-package ancestry."""
    records = load_mana_design_package(
        Path(review_root) / "gameplay-rules-mana-ability-design",
        review_root=review_root,
    )
    raw = {name: (record.serialize() + "\n").encode("utf-8")
           for name, record in records.items()}
    manifest = mana_design_manifest(records, raw)
    if (manifest["package_id"] != PRIOR_PACKAGE_IDS["mana_ability_dependency_design"] or
            manifest["record_ids"] != DESIGN_IDS or
            manifest["retained_evidence_binding"]["prior_package_ids"] != {
                key: value for key, value in PRIOR_PACKAGE_IDS.items()
                if key != "mana_ability_dependency_design"}):
        _fail("exact merged design and eight prior package identities required")
    return records


def rebuild_bounded_mana_package(projection, *, review_root):
    """Reproduce authored reviews offline; external source proof stays separate."""
    try:
        if type(projection) is not BoundedManaProjection:
            _fail("typed bounded mana ability projection required")
        projection.verify()
        _prior_design(review_root)
        from .bounded_mana_reports import build_bounded_mana_reports
        records = {"projection.json": projection,
                   **build_bounded_mana_reports(projection, review_root=review_root)}
        package_manifest(records)
        return records
    except GameplayContractError:
        raise
    except (OSError, ValueError, TypeError, KeyError, IndexError, AttributeError,
            UnicodeError, RecursionError):
        _fail()


def build_bounded_mana_package(artifact_path, *, review_root):
    """Read the exact verified external artifact before constructing new records."""
    from .bounded_mana_source import build_bounded_mana_projection
    projection = build_bounded_mana_projection(artifact_path, **_source_roots(review_root))
    return rebuild_bounded_mana_package(projection, review_root=review_root)


def package_manifest(records, raw_files=None):
    """Bind eight canonical authored records and nine unchanged prior packages."""
    try:
        canonical = _canonical_raw(records)
        if raw_files is None:
            raw_files = canonical
        if not isinstance(raw_files, dict) or set(raw_files) != set(RECORD_TYPES):
            _fail("exactly eight canonical record byte sequences required")
        for name in RECORD_TYPES:
            if (type(raw_files[name]) is not bytes or len(raw_files[name]) > 128_000 or
                    raw_files[name] != canonical[name]):
                _fail("noncanonical or oversized record bytes")
        values = {name: record.to_dict() for name, record in records.items()}
        projection = values["projection.json"]
        references = [row["rule_reference"] for row in projection["rules"]]
        if references != list(SELECTED_REFERENCES):
            _fail("exactly thirteen authorized source units required")
        identities = {name: record.identity for name, record in records.items()}
        if len(set(identities.values())) != len(RECORD_TYPES):
            _fail("distinct projection and review identities required")
        for name in set(RECORD_TYPES) - {"projection.json"}:
            review = values[name]
            if (review["bounded_mana_projection_id"] != records["projection.json"].identity or
                    review["source_binding"] != projection["source_binding"] or
                    review["review_kind"] != REVIEW_KINDS[name] or
                    review["prior_package_ids"] != PRIOR_PACKAGE_IDS or
                    review["design_ids"] != DESIGN_IDS):
                _fail("review belongs to another source projection")
        composite = values["composite-coverage.json"]["findings"]
        components = composite["projection_components"]
        if not isinstance(components, list) or len(components) != 7:
            _fail("exactly seven separate projection components required")
        grouped_refs = [item["projected_references"] for item in components]
        combined_refs = [reference for group in grouped_refs for reference in group]
        prior_component_names = (
            "foundational", "direct_foundational_dependencies", "object_control_exceptions",
            "zone_change_exceptions", "zone_change_direct_dependencies", "bounded_casting_projection",
        )
        if (any(components[index]["package_id"] != PRIOR_PACKAGE_IDS[name]
                for index, name in enumerate(prior_component_names)) or
                components[-1]["projection_id"] != records["projection.json"].identity or
                components[-1].get("package_binding") != "THIS_ENCLOSING_BOUNDED_MANA_PACKAGE" or
                len({item["projection_id"] for item in components}) != 7 or
                [len(group) for group in grouped_refs] != [20, 12, 7, 12, 12, 5, 13] or
                grouped_refs[-1] != references or len(combined_refs) != 81 or
                len(set(combined_refs)) != 81 or
                composite["projected_references"] != combined_refs or
                composite["total_projected_rule_count"] != 81):
            _fail("exactly 81 distinct source units across seven separate projections required")
        body = {
            "schema_version": PACKAGE_SCHEMA,
            "canonical_base": CANONICAL_MAIN,
            "prior_package_ids": dict(PRIOR_PACKAGE_IDS),
            "prior_design_ids": dict(DESIGN_IDS),
            "bounded_mana_projection_id": records["projection.json"].identity,
            "record_ids": identities,
            "source_binding": projection["source_binding"],
            "files": {
                name: {"sha256": hashlib.sha256(raw_files[name]).hexdigest(),
                       "bytes": len(raw_files[name])}
                for name in sorted(RECORD_TYPES)
            },
            "selected_rule_count": 13,
            "selected_references": list(SELECTED_REFERENCES),
            "projected_rule_count_before": 68,
            "new_source_units_projected": 13,
            "projected_rule_count_after": 81,
            "composite_projected_rule_count": 81,
            "additional_rules_projected": [],
            "status": "BOUNDED_MANA_ABILITY_RULES_PROJECTED",
            "review_state": "PROJECTED_FOR_REVIEW",
            "semantic_closure": "OPEN",
            "overall_execution_readiness": "BLOCKED",
            "readiness_code": "REAL_EXECUTION_PROFILE_NOT_READY",
            "non_executable": True,
            "execution_authorized": False,
            "real_rules_executable": False,
            "owner_execution_approval": "NOT_GRANTED",
            "real_snapshot_created": False,
            "real_profile_activated": False,
            "source_body_retained": False,
            "historical_anchors_changed": False,
            "oracle_ingested": False,
            "admission_eligible": False,
            "source_policy_clearance": "not_granted",
            "permissions": {key: "NOT_ESTABLISHED" for key in
                ("private_retention", "redistribution", "free_service", "commercial_service", "ai_export")},
            "historical_acquisition_identity": HISTORICAL_ACQUISITION_ID,
        }
        return {**body, "package_id": "sha256:" + sha256_identity({
            "domain": PACKAGE_SCHEMA, "content": body})}
    except GameplayContractError:
        raise
    except (ValueError, TypeError, KeyError, IndexError, AttributeError, UnicodeError, RecursionError):
        _fail()


def load_bounded_mana_package(root, *, review_root):
    """Verify nine canonical regular files and reproduce every review offline.

    A successful offline load means the package metadata and authored findings
    reproduce. Re-reading the exact source artifact is a separate explicit proof.
    Relocated package and lineage paths do not enter retained identities.
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
            _fail("manifest differs from canonical package contents")
        expected = rebuild_bounded_mana_package(records["projection.json"], review_root=review_root)
        if any(records[name].to_dict() != expected[name].to_dict() for name in RECORD_TYPES):
            _fail("authored reviews do not reproduce from immutable retained evidence")
        return records
    except GameplayContractError:
        raise
    except (OSError, ValueError, TypeError, KeyError, IndexError, AttributeError,
            UnicodeError, RecursionError):
        _fail()


def write_bounded_mana_package(root, records):
    """Write only to a new or empty destination without replacing prior evidence."""
    try:
        raw_files = _canonical_raw(records)
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
    except (OSError, ValueError, TypeError, KeyError, IndexError, AttributeError,
            UnicodeError, RecursionError):
        _fail()


def composite_coverage_view(records, manifest):
    """Resolve the seventh package identity in a derived read-only coverage view."""
    try:
        expected = package_manifest(records)
        if deterministic_json(manifest) != deterministic_json(expected):
            _fail("exact enclosing manifest required for composite view")
        findings = records["composite-coverage.json"].to_dict()["findings"]
        components = findings["projection_components"]
        if (len(components) != 7 or components[-1].pop("package_binding", None) !=
                "THIS_ENCLOSING_BOUNDED_MANA_PACKAGE"):
            _fail("seven-component composite self-package binding required")
        components[-1]["package_id"] = manifest["package_id"]
        return {
            "view_kind": "RESOLVED_READ_ONLY_COMPOSITE_VIEW",
            "retained_composite_coverage_id": records["composite-coverage.json"].identity,
            "projection_components": components,
            "total_projected_rule_count": findings["total_projected_rule_count"],
            "projected_references": findings["projected_references"],
            "execution_authorized": False,
            "real_rules_executable": False,
        }
    except GameplayContractError:
        raise
    except (ValueError, TypeError, KeyError, IndexError, AttributeError, UnicodeError, RecursionError):
        _fail()
