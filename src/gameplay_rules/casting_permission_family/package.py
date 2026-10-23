"""One append-only source-projection package for the complete 601.3 family.

Candidate boundaries use private canonical snapshots. Fixed authored caches never
replace fresh on-disk validation of retained history or fresh source reproduction.
"""
from __future__ import annotations

from copy import deepcopy
from functools import cache
import hashlib
import json
from pathlib import Path

from evidence.contracts import sha256_identity
from gameplay_rules.errors import GameplayContractError
from gameplay_rules.retained_stage_validation import validate_retained_stage
from gameplay_rules.casting_stage_family_completion import package as predecessor
from gameplay_rules.projection.dependency_package import _read, _root
from gameplay_rules.projection.mana_stack_exception_package import _canonical_candidate
from .reviews import CANONICAL_MAIN, PERMISSIONS
from .scope import SELECTED_REFERENCES

PACKAGE_NAME = "gameplay-rules-casting-permission-family"
PACKAGE_SCHEMA = "gameplay-casting-permission-family-package-v1"
RECORD_DOMAIN = "gameplay-casting-permission-family-record-v1"
RECORD_NAMES = frozenset(("projection.json", "scope-preflight.json", "source-correspondence.json",
    "permission-assessment.json", "relationship-reassessment.json", "composite-coverage.json",
    "subsequent-recommendation.json"))
REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_REVIEW_ROOT = REPOSITORY_ROOT / "reference-reviews"
RETAINED_STAGE_PACKAGE_ID = "sha256:72536eb1bbbc3422797215a3630a9f512b9d2a0b758e8a852e4903e71e047e82"
RETAINED_STAGE_PROJECTION_ID = "sha256:14a1616f247b920f68af5860adce445fa597fe4159de305410de9fa70fc959c2"
HISTORICAL_RECOMMENDATION_ID = "sha256:625c55bbd527c78b351ee5cf08c5d749190d8efbb117ac595e2253dc02d626af"


def _fail(message):
    raise GameplayContractError("casting_permission_family_package", message)


def _bytes(value):
    return _canonical_candidate(value)


def _copy(value):
    return json.loads(_bytes(value))


def _identity(domain, content):
    return "sha256:" + sha256_identity({"domain": domain, "content": content})


def _identify_record(body):
    value = _copy(body)
    if type(value) is not dict:
        _fail("PLAIN_JSON_RECORD_BODY_REQUIRED")
    value.pop("review_id", None)
    return {**value, "review_id": _identity(RECORD_DOMAIN, value)}


def _resolve_package_bindings(value, package_id):
    predecessor._resolve_package_bindings(value, package_id)


def retained_binding():
    """Return defensive fixed metadata; every public disk boundary checks history."""
    return json.loads(_retained_binding_bytes())


@cache
def _retained_binding_bytes():
    old = predecessor._expected_records()
    parent = predecessor._manifest_validated(old, predecessor.retained_binding())
    if parent["package_id"] != RETAINED_STAGE_PACKAGE_ID:
        _fail("RETAINED_STAGE_PACKAGE_IDENTITY_INVALID")
    view = _copy(old["composite-coverage.json"]["findings"])
    _resolve_package_bindings(view, RETAINED_STAGE_PACKAGE_ID)
    binding = predecessor.retained_binding()
    binding["canonical_base"] = CANONICAL_MAIN
    binding["projection_components"] = view["projection_components"]
    binding["rule_bindings"] = view["all_prior_rule_bindings"]
    binding["prior_package_ids"] = _copy(parent["prior_package_ids"])
    projection = old["projection.json"]
    for rule in projection["rules"]:
        binding["rule_bindings"][rule["rule_reference"]] = {
            "retained_package": predecessor.PACKAGE_NAME, "package_id": RETAINED_STAGE_PACKAGE_ID,
            "projection_id": projection["projection_id"], "rule_id": rule["rule_id"],
            "anchor_identity": rule["source_anchor"]["anchor_id"],
            "source_anchor": _copy(rule["source_anchor"]), "identity_basis": "EXISTING_STANDALONE_ID"}
    binding["prior_package_ids"][predecessor.PACKAGE_NAME] = RETAINED_STAGE_PACKAGE_ID
    # Counts derive from actual immutable inventories, not candidate metadata.
    references = [ref for item in binding["projection_components"] for ref in item["projected_references"]]
    if (len(references) != len(set(references)) or set(references) != set(binding["rule_bindings"])
            or len(references) != 93 or len(binding["projection_components"]) != 14
            or set(SELECTED_REFERENCES) & set(references)):
        _fail("RETAINED_INVENTORY_OR_DISJOINT_FAMILY_INVALID")
    return _bytes(binding)


def validate_historical(*, review_root):
    """Check predecessor chain, actual own identities and enclosing manifests."""
    from gameplay_rules.casting_stage_family_completion.contracts import CastingStageFamilyCompletionProjection
    root = _root(review_root)
    predecessor.validate_historical(review_root=root)
    retained = validate_retained_stage(root,
        name=predecessor.PACKAGE_NAME, package_schema=predecessor.PACKAGE_SCHEMA,
        package_id=RETAINED_STAGE_PACKAGE_ID, record_domain=predecessor.RECORD_DOMAIN,
        record_names=predecessor.RECORD_NAMES, projection_type=CastingStageFamilyCompletionProjection)
    records, parent = retained["records"], retained["manifest"]
    if (records["projection.json"]["projection_id"] != RETAINED_STAGE_PROJECTION_ID
            or records["subsequent-recommendation.json"]["review_id"] != HISTORICAL_RECOMMENDATION_ID
            or parent["historical_acquisition_identity"] !=
                "sha256:669d7db9ebcaf97853058fd62f408ce3c6596d5dae0ee72ff39d2ba9df56bb53"):
        _fail("PROTECTED_HISTORICAL_IDENTITIES_CHANGED")
    return retained_binding()


def _projection():
    from .contracts import create_projection
    from .source import VERIFIED_ANCHORS
    return create_projection(VERIFIED_ANCHORS).to_dict()


def _expected_records():
    return json.loads(_expected_record_bytes())


@cache
def _expected_record_bytes():
    from .reviews import authored_records
    projection = _projection()
    bodies = authored_records(retained_binding(), projection)
    return _bytes({"projection.json": projection,
        **{name: _identify_record(body) for name, body in bodies.items()}})


def validate_records(records):
    raw = _bytes(records)
    snapshot = json.loads(raw)
    if type(snapshot) is not dict or set(snapshot) != RECORD_NAMES:
        _fail("EXACT_COMPLETE_FAMILY_RECORD_SET_REQUIRED")
    from .contracts import CastingPermissionFamilyProjection
    CastingPermissionFamilyProjection.from_dict(snapshot["projection.json"])
    for name, record in snapshot.items():
        if name == "projection.json":
            continue
        if (type(record) is not dict or type(record.get("schema_version")) is not int
                or record["schema_version"] != 1 or type(record.get("review_id")) is not str
                or type(record.get("record_type")) is not str
                or record["record_type"] != name.removesuffix(".json")):
            _fail("REVIEW_SCHEMA_OR_OWN_IDENTITY_INVALID")
        body = {key: value for key, value in record.items() if key != "review_id"}
        if record["review_id"] != _identity(RECORD_DOMAIN, body):
            _fail("REVIEW_OWN_IDENTITY_MISMATCH")
    if raw != _bytes(_expected_records()):
        _fail("EXACT_AUTHORED_RECORD_CONTENT_REQUIRED")
    return snapshot


def rebuild_package(*, review_root):
    """Fixed offline reconstruction establishes no fresh-source reproduction."""
    validate_historical(review_root=review_root)
    return _expected_records()


def build_package(artifact_path, *, review_root):
    from .source import verified_anchors
    from .contracts import create_projection
    validate_historical(review_root=review_root)
    anchors = verified_anchors(artifact_path, review_root=review_root)
    if _bytes(create_projection(anchors).to_dict()) != _bytes(_projection()):
        _fail("FRESH_COMPLETE_FAMILY_PROJECTION_DOES_NOT_REPRODUCE")
    return _expected_records()


def _manifest_validated(records, binding):
    projection = records["projection.json"]
    previous = len(binding["rule_bindings"])
    component_count = len(binding["projection_components"])
    n = len(SELECTED_REFERENCES)
    body = {"schema_version": PACKAGE_SCHEMA, "canonical_base": CANONICAL_MAIN,
        "status": "CASTING_PERMISSION_FAMILY_PROJECTED", "projection_id": projection["projection_id"],
        "record_ids": {name: value["projection_id" if name == "projection.json" else "review_id"]
            for name, value in sorted(records.items())},
        "files": {name: {"bytes": len(_bytes(value)), "sha256": hashlib.sha256(_bytes(value)).hexdigest()}
            for name, value in sorted(records.items())},
        "source_binding": deepcopy(projection["source_binding"]),
        "prior_package_ids": deepcopy(binding["prior_package_ids"]),
        "historical_acquisition_identity": binding["historical_acquisition_identity"],
        "artifact_verification_identity": binding["artifact_verification_identity"],
        "selected_references": list(SELECTED_REFERENCES), "selected_rule_count": n,
        "projected_rule_count_before": previous, "new_source_units_projected": n,
        "projected_rule_count_after": previous+n, "existing_projection_count_before": component_count,
        "existing_projection_count_after": component_count+1, "additional_rules_projected": [],
        "stage_coverage": "9/9", "parent_proposal_range_coverage": "4/4",
        "activated_import_range_count": 1, "activated_import_member_count": 8,
        "activated_import_projected_before": 8, "activated_import_projected_after": 8,
        "activated_import_complete": True, "i_preceding_range_source_coverage": "8/8",
        "self_package_binding_contract": "THIS_ENCLOSING_PACKAGE_RESOLVES_TO_THIS_MANIFEST_PACKAGE_ID",
        "historical_anchors_changed": False, "historical_dependency_arrays_changed": False,
        "non_executable": True, "semantic_closure": "OPEN", "execution_readiness": "BLOCKED",
        "real_profile": "DESIGN_ONLY / NOT EXECUTABLE", "readiness_code": "REAL_EXECUTION_PROFILE_NOT_READY",
        "execution_authorized": False, "real_snapshot_created": False,
        "real_execution_profile_activated": False, "admission_eligible": False,
        "source_body_retained": False, "source_policy_clearance": "not_granted",
        "permissions": deepcopy(PERMISSIONS), "offline_reproduction": "NOT_FRESH_SOURCE_VERIFICATION",
        "future_milestone_authorized": False, "future_source_projection_authorized": False,
        "future_milestone_begun": False}
    return {**body, "package_id": _identity(PACKAGE_SCHEMA, body)}


def manifest(records, *, review_root=DEFAULT_REVIEW_ROOT):
    snapshot = validate_records(records)
    binding = validate_historical(review_root=review_root)
    return _manifest_validated(snapshot, binding)


def write_package(root, records, *, review_root):
    """Validate candidate and history before output directory or file creation."""
    snapshot = validate_records(records)
    binding = validate_historical(review_root=review_root)
    metadata = _manifest_validated(snapshot, binding)
    root = Path(root)
    if any(path.is_symlink() for path in (root, *root.parents)):
        _fail("SYMLINK_DESTINATION_FORBIDDEN")
    if root.exists() and (not root.is_dir() or any(root.iterdir())):
        _fail("APPEND_ONLY_NEW_OR_EMPTY_DESTINATION_REQUIRED")
    root.mkdir(parents=True, exist_ok=True)
    for name, value in {**snapshot, "manifest.json": metadata}.items():
        with (root / name).open("xb") as stream:
            stream.write(_bytes(value))
    return metadata


def load_package(root, *, review_root):
    root = _root(root)
    if {path.name for path in root.iterdir()} != RECORD_NAMES | {"manifest.json"}:
        _fail("EXACT_PACKAGE_FILE_SET_REQUIRED")
    expected = rebuild_package(review_root=review_root)
    for name, value in {**expected, "manifest.json": _manifest_validated(expected, retained_binding())}.items():
        if _read(root / name) != _bytes(value):
            _fail("PACKAGE_CANONICAL_BYTES_OR_BINDINGS_DO_NOT_REPRODUCE")
    return expected


def verify_source(records, artifact_path, *, review_root):
    snapshot = validate_records(records)
    reproduced = build_package(artifact_path, review_root=review_root)
    if _bytes(snapshot) != _bytes(reproduced):
        _fail("EXACT_COMPLETE_FAMILY_SOURCE_CORRESPONDENCE_DOES_NOT_REPRODUCE")
    return {"status": "VERIFIED_EXACT_COMPLETE_CASTING_PERMISSION_FAMILY",
        "selected_references": list(SELECTED_REFERENCES), "selected_rule_count": len(SELECTED_REFERENCES),
        "new_source_units_projected": len(SELECTED_REFERENCES),
        "projection_id": snapshot["projection.json"]["projection_id"],
        "source_anchors": [deepcopy(row["source_anchor"]) for row in snapshot["projection.json"]["rules"]],
        "source_body_retained": False, "outgoing_numbered_citations": {ref: [] for ref in SELECTED_REFERENCES},
        "outgoing_ranges": [],
        "source_correspondence_review_id": snapshot["source-correspondence.json"]["review_id"]}


def current_view(records, *, review_root=DEFAULT_REVIEW_ROOT):
    snapshot = validate_records(records)
    binding = validate_historical(review_root=review_root)
    metadata = _manifest_validated(snapshot, binding)
    _resolve_package_bindings(snapshot, metadata["package_id"])
    return {"package_id": metadata["package_id"], "records": snapshot,
        "view_kind": "READ_ONLY_RESOLVED_PACKAGE_BINDINGS_NOT_NEW_CANONICAL_RECORDS"}


def composite_view(records, *, review_root=DEFAULT_REVIEW_ROOT):
    return current_view(records, review_root=review_root)["records"]["composite-coverage.json"]["findings"]
