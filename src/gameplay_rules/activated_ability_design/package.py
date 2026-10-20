"""Closed, append-only review package for activated-procedure design.

Offline reproduction verifies pinned retained evidence and authored metadata.
Only ``build_package`` and ``verify_source`` inspect the external artifact; no
entry point creates projected source coverage or connects to gameplay execution.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from evidence.contracts import deterministic_json, sha256_identity
from gameplay_rules.errors import GameplayContractError
from gameplay_rules.execution_design.contracts import _freeze, _json
from gameplay_rules.projection.dependency_package import _read, _root
from gameplay_rules.projection.mana_stack_exception_package import _canonical_candidate

CANONICAL_MAIN = "9e1335d53458913dec1907e2922b9e99339cc3c5"
PACKAGE_NAME = "gameplay-rules-activated-ability-procedure-design"
PACKAGE_SCHEMA = "gameplay-activated-ability-procedure-design-package-v1"
RECORD_DOMAIN = "gameplay-activated-ability-procedure-design-record-v1"
PINS_SHA256 = "0af33c540db9295504c44d3f4a3b357ad90dab1209b7f2d787add4d281d977e2"
RECORD_NAMES = frozenset((
    "source-correspondence.json", "local-scope.json",
    "procedure-responsibilities.json", "casting-import.json",
    "mana-relationships.json", "consumer-bindings.json", "readiness.json",
))
FLAGS = _freeze({
    "canonical_base": CANONICAL_MAIN,
    "status": "DESIGN_ONLY", "non_executable": True,
    "execution_readiness": "BLOCKED", "real_profile": "DESIGN_ONLY / NOT EXECUTABLE",
    "execution_authorized": False, "projection_authorized": False,
    "current_projection_allowlist": [], "new_source_units_projected": 0,
    "projected_real_source_units": 85, "distinct_existing_projections": 9,
    "new_projected_rule_identities": 0, "new_registered_projected_source_anchors": 0,
    "source_body_retained": False, "real_snapshot_created": False,
    "source_policy_clearance": "not_granted",
    "permissions": {name: "NOT_ESTABLISHED" for name in (
        "private_retention", "redistribution", "free_service", "commercial_service", "ai_export")},
})


def _fail(message):
    raise GameplayContractError("activated_ability_design_package", message)


def _bytes(value):
    return (deterministic_json(value) + "\n").encode("utf-8")


def _copy(value):
    return json.loads(_canonical_candidate(value))


def _pins():
    raw = _read(Path(__file__).with_name("pins.json"))
    if hashlib.sha256(raw).hexdigest() != PINS_SHA256:
        _fail("CANONICAL_BASE_PIN_BYTES_CHANGED")
    value = json.loads(raw)
    if _canonical_candidate(value) != raw:
        _fail("CANONICAL_BASE_PIN_BYTES_NOT_CANONICAL")
    return value


def retained_binding():
    """Return immutable-input metadata as a detached copy, without fresh proof."""
    return _copy(_pins()["binding"])


def verify_prior_packages(review_root):
    """Check all 107 inherited gameplay-evidence files and their exact file sets."""
    root = _root(review_root)
    groups = {}
    prefix = "reference-reviews/"
    for name, digest in _pins()["protected_files"].items():
        if name.startswith(prefix):
            relative = Path(name[len(prefix):])
            groups.setdefault(relative.parts[0], {})[relative.name] = digest
    for name, files in groups.items():
        package = _root(root / name)
        if {path.name for path in package.iterdir()} != set(files):
            _fail("PRIOR_GAMEPLAY_EVIDENCE_FILE_SET_CHANGED")
        for filename, digest in files.items():
            if hashlib.sha256(_read(package / filename)).hexdigest() != digest:
                _fail("PRIOR_GAMEPLAY_EVIDENCE_BYTES_CHANGED")
    return retained_binding()


def verify_preservation(repo_root):
    """Verify exact canonical-base bytes without depending on mutable fixtures."""
    root = _root(repo_root)
    pins = _pins()
    for name, digest in pins["protected_files"].items():
        path = root / name
        if hashlib.sha256(_read(path)).hexdigest() != digest:
            _fail("CANONICAL_BASE_PROTECTED_BYTES_CHANGED")
    verify_prior_packages(root / "reference-reviews")
    return {"canonical_base": CANONICAL_MAIN, "inherited_source_files_preserved": 333,
            "inherited_gameplay_evidence_files_preserved": 107,
            "inherited_gameplay_evidence_directories_preserved": 17,
            "projected_real_source_units": 85, "distinct_existing_projections": 9}


def identify_record(body):
    """Bind an exact plain-JSON record body; validation never coerces values."""
    value = _copy(body)
    if type(value) is not dict:
        _fail("PLAIN_JSON_RECORD_BODY_REQUIRED")
    value.pop("review_id", None)
    return {**value, "review_id": "sha256:" + sha256_identity({
        "domain": RECORD_DOMAIN, "content": value})}


def _expected_records(binding=None, inspection=None):
    from .inspection import expected_inspection
    from .records import authored_records
    binding = retained_binding() if binding is None else _copy(binding)
    inspection = expected_inspection() if inspection is None else _copy(inspection)
    bodies = authored_records(binding, inspection)
    _canonical_candidate(bodies)
    if type(bodies) is not dict or set(bodies) != RECORD_NAMES:
        _fail("EXACT_SEVEN_AUTHORED_RECORD_BODIES_REQUIRED")
    records = {}
    for name, body in bodies.items():
        if type(body) is not dict or set(body) != {"schema_version", "findings"}:
            _fail("CLOSED_AUTHORED_RECORD_BODY_REQUIRED")
        if type(body["schema_version"]) is not int or body["schema_version"] != 1:
            _fail("EXACT_INTEGER_SCHEMA_VERSION_REQUIRED")
        records[name] = identify_record({**_json(FLAGS), **body, "record_kind": name})
    return records


def rebuild_package(*, review_root):
    """Reproduce metadata offline; this is never fresh attached-source proof."""
    return _expected_records(binding=verify_prior_packages(review_root))


def build_package(artifact_path, *, review_root):
    """Verify exact external bytes and bounded source findings; write nothing."""
    from .inspection import inspect_source
    binding = verify_prior_packages(review_root)
    inspection = inspect_source(artifact_path, review_root=review_root)
    return _expected_records(binding=binding, inspection=inspection)


def _validate_records(records):
    raw = _canonical_candidate(records)
    if type(records) is not dict or set(records) != RECORD_NAMES:
        _fail("EXACT_SEVEN_AUTHORED_RECORDS_REQUIRED")
    for name, record in records.items():
        if type(record) is not dict or type(record.get("review_id")) is not str:
            _fail("RECORD_IDENTITY_REQUIRED")
        if _canonical_candidate(record) != _bytes(identify_record(record)):
            _fail("RECORD_IDENTITY_DOES_NOT_REPRODUCE")
    if raw != _bytes(_expected_records()):
        _fail("AUTHORED_RECORDS_DO_NOT_REPRODUCE")
    return records


def manifest(records):
    """Validate exact findings, types, identities and canonical record bytes."""
    _validate_records(records)
    binding = retained_binding()
    body = {
        "schema_version": PACKAGE_SCHEMA, **_json(FLAGS),
        "record_ids": {name: records[name]["review_id"] for name in sorted(records)},
        "prior_package_ids": binding["prior_package_ids"],
        "historical_acquisition_identity": binding["historical_acquisition_identity"],
        "artifact_verification_identity": binding["artifact_verification_identity"],
        "canonical_base_preservation_pins_identity": "sha256:" + PINS_SHA256,
        "source_inspection_scope": ["602.2", "602.2a", "602.2b"],
        "source_inspection_metadata": "REVIEW_ONLY_NOT_PROJECTED_COVERAGE",
        "offline_reproduction": "NOT_FRESH_SOURCE_VERIFICATION",
        "projected_rule_count_before": 85, "projected_rule_count_after": 85,
        "existing_projection_count_before": 9, "existing_projection_count_after": 9,
        "additional_rules_projected": [], "source_coverage_graph_changed": False,
        "future_milestone_authorized": False, "future_source_projection_authorized": False,
        "future_milestone_begun": False,
        "files": {name: {"bytes": len(_bytes(value)),
                         "sha256": hashlib.sha256(_bytes(value)).hexdigest()}
                  for name, value in sorted(records.items())},
    }
    return {**body, "package_id": "sha256:" + sha256_identity({
        "domain": PACKAGE_SCHEMA, "content": body})}


def write_package(root, records, *, review_root):
    """Reject invalid candidates before any output directory or file is made."""
    _validate_records(records)
    expected = rebuild_package(review_root=review_root)
    if _canonical_candidate(records) != _bytes(expected):
        _fail("AUTHORED_RECORDS_DO_NOT_REPRODUCE")
    metadata = manifest(records)
    root = Path(root)
    if any(path.is_symlink() for path in (root, *root.parents)):
        _fail("SYMLINK_DESTINATION_FORBIDDEN")
    if root.exists() and (not root.is_dir() or any(root.iterdir())):
        _fail("APPEND_ONLY_NEW_OR_EMPTY_DESTINATION_REQUIRED")
    root.mkdir(parents=True, exist_ok=True)
    for name, value in {**records, "manifest.json": metadata}.items():
        with (root / name).open("xb") as stream:
            stream.write(_bytes(value))
    return metadata


def load_package(root, *, review_root):
    """Accept only the exact eight canonical regular files and pinned findings."""
    root = _root(root)
    if {path.name for path in root.iterdir()} != RECORD_NAMES | {"manifest.json"}:
        _fail("EXTRA_OR_MISSING_PACKAGE_FILE")
    expected = rebuild_package(review_root=review_root)
    for name, value in {**expected, "manifest.json": manifest(expected)}.items():
        if _read(root / name) != _bytes(value):
            _fail("PACKAGE_CANONICAL_BYTES_DO_NOT_REPRODUCE")
    return expected


def verify_source(records, artifact_path, *, review_root):
    """Fresh exact-source verification remains separate from offline loading."""
    _validate_records(records)
    expected = build_package(artifact_path, review_root=review_root)
    if _canonical_candidate(records) != _bytes(expected):
        _fail("EXACT_SOURCE_REPRODUCTION_FAILED")
    from .inspection import expected_inspection
    return {"status": "VERIFIED_EXACT_SOURCE_DESIGN_INSPECTION",
            "inspection": expected_inspection(), "new_source_units_projected": 0,
            "source_body_retained": False}
