"""Canonical append-only package for one non-executable target-declaration unit.

Offline reconstruction verifies retained evidence without reopening its source.
Fresh reproduction has a separate c-only source boundary and selector.
"""
from __future__ import annotations

from copy import deepcopy
from functools import cache
import hashlib
import importlib.util
import json
from pathlib import Path

from evidence.contracts import sha256_identity
from gameplay_rules.errors import GameplayContractError
from gameplay_rules.retained_stage_validation import validate_retained_stage
from gameplay_rules.activated_ability_projection import package as activated
from gameplay_rules.projection.dependency_package import _read, _root
from gameplay_rules.projection.mana_stack_exception_package import _canonical_candidate
from .reviews import CANONICAL_MAIN, DESIGN_ID, DESIGN_NAME, DESIGN_REVIEWS, PERMISSIONS

PACKAGE_NAME = "gameplay-rules-bounded-shared-target-declaration"
PACKAGE_SCHEMA = "gameplay-bounded-shared-target-declaration-package-v1"
RECORD_DOMAIN = "gameplay-bounded-shared-target-declaration-record-v1"
RECORD_NAMES = frozenset(("projection.json", "design-source-correspondence.json",
    "casting-parent-reassessment.json", "activated-import-reassessment.json",
    "consumer-semantic-boundaries.json", "composite-coverage.json",
    "preservation-readiness.json", "subsequent-recommendation.json"))
REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_REVIEW_ROOT = REPOSITORY_ROOT / "reference-reviews"
INHERITED_TOOL_SHA256 = "d2788448d15a06107c11e9734d4ed82c5a9dca75868cf38a062cb329b5b72f53"


def _fail(message):
    raise GameplayContractError("shared_target_declaration_package", message)


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


def _historical_tool():
    """Reuse only the immutable inherited tool's offline contracts.

    Its four-body source function is deliberately never called or selected.
    Resolve this one exact repository file, not caller-controlled module paths.
    """
    path = REPOSITORY_ROOT / "scripts" / "shared_casting_stage_gap_design.py"
    raw = _read(path)
    if len(raw) != 27105 or hashlib.sha256(raw).hexdigest() != INHERITED_TOOL_SHA256:
        _fail("INHERITED_REVIEW_TOOL_CHANGED")
    spec = importlib.util.spec_from_file_location("_mtglab_retained_shared_casting_design", path)
    if spec is None or spec.loader is None:
        _fail("INHERITED_OFFLINE_CONTRACT_UNAVAILABLE")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def retained_binding():
    """Return defensive fixed metadata; public operations check current history."""
    return json.loads(_retained_binding_bytes())


@cache
def _retained_binding_bytes():
    """Only immutable contract-derived metadata bytes are cached."""
    old = activated._expected_records()
    view = activated.composite_view(old)
    binding = activated.retained_binding()
    binding["canonical_base"] = CANONICAL_MAIN
    binding["projection_components"] = view["projection_components"]
    binding["rule_bindings"] = view["all_prior_rule_bindings"]
    projection = old["projection.json"]
    package_id = activated.manifest(old)["package_id"]
    for rule in projection["rules"]:
        binding["rule_bindings"][rule["rule_reference"]] = {
            "retained_package": activated.PACKAGE_NAME, "package_id": package_id,
            "projection_id": projection["projection_id"], "rule_id": rule["rule_id"],
            "anchor_identity": rule["source_anchor"]["anchor_id"],
            "identity_basis": "EXISTING_STANDALONE_ID"}
    binding["prior_package_ids"][activated.PACKAGE_NAME] = package_id
    binding["prior_package_ids"][DESIGN_NAME] = DESIGN_ID
    binding["responsibility_names"] = [row["responsibility"] for row in old["procedure-responsibilities.json"]["findings"]["rows"]]
    return _bytes(binding)


def _validated_historical_records(review_root):
    """Freshly verify the baseline and two successors without recursive package reconstruction."""
    from gameplay_rules.activated_ability_projection.contracts import BoundedActivatedAbilityProjection
    try:
        root = _root(review_root)
        binding = activated.verify_prior_packages(root)
        tool = _historical_tool()
        tool._validate_additional_package_identities(root, binding)
        selections = (
            (activated.PACKAGE_NAME, activated.PACKAGE_SCHEMA,
             "sha256:02667e58da72701b7464275184de452a1ec53f34b7dedc80ca3cde8c595a7ff4",
             activated.RECORD_DOMAIN, activated.RECORD_NAMES, BoundedActivatedAbilityProjection),
            (DESIGN_NAME, tool.PACKAGE_SCHEMA, DESIGN_ID,
             tool.RECORD_DOMAIN, tool.RECORD_NAMES, None),
        )
        successors = {name: validate_retained_stage(root, name=name, package_schema=schema,
            package_id=identity, record_domain=domain, record_names=names,
            projection_type=projection_type)
            for name, schema, identity, domain, names, projection_type in selections}
        # Preserve the inherited tool's authored and contextual checks without
        # its recursive older package reconstruction or source functions.
        records = successors[DESIGN_NAME]["records"]
        tool.validate_records(records)
        tool._validate_context_bindings(records, review_root=root)
        return successors
    except GameplayContractError:
        raise
    except (OSError, ValueError, TypeError, KeyError, AttributeError, UnicodeError, RecursionError):
        _fail("RETAINED_HISTORICAL_CONTRACT_INVALID")


def validate_historical(*, review_root):
    """Verify exact retained canonical bytes, own identities and manifest bindings."""
    root = _root(review_root)
    successor = _validated_historical_records(root)[DESIGN_NAME]
    records, parent = successor["records"], successor["manifest"]
    if (type(parent.get("schema_version")) is not str
            or parent["schema_version"] != "gameplay-shared-casting-stage-gap-design-package-v1"
            or type(parent.get("package_id")) is not str or parent["package_id"] != DESIGN_ID):
        _fail("RETAINED_PR201_PACKAGE_BINDING_INVALID")
    body = {key: value for key, value in parent.items() if key != "package_id"}
    if parent["package_id"] != _identity("gameplay-shared-casting-stage-gap-design-package-v1", body):
        _fail("RETAINED_PR201_PACKAGE_OWN_IDENTITY_INVALID")
    for filename, expected_id in DESIGN_REVIEWS.items():
        record = records[filename]
        own_body = {key: value for key, value in record.items() if key != "review_id"}
        own = _identity("gameplay-shared-casting-stage-gap-design-record-v1", own_body)
        if (type(record.get("schema_version")) is not int or record["schema_version"] != 1
                or type(record.get("review_id")) is not str
                or record["review_id"] != own or own != expected_id
                or _bytes(parent["record_ids"][filename]) != _bytes(own)):
            _fail("RETAINED_PR201_REVIEW_OWN_IDENTITY_OR_MANIFEST_BINDING_INVALID")
    return retained_binding()


def _projection():
    from .contracts import create_projection
    from .source import VERIFIED_ANCHORS
    return create_projection(VERIFIED_ANCHORS).to_dict()


def _expected_records():
    return json.loads(_expected_record_bytes())


@cache
def _expected_record_bytes():
    """Cache immutable fixed authored bytes, never caller data or disk success."""
    from .reviews import authored_records
    projection = _projection()
    bodies = authored_records(retained_binding(), projection)
    return _bytes({"projection.json": projection,
        **{name: _identify_record(body) for name, body in bodies.items()}})


def validate_records(records):
    raw = _bytes(records)
    # Capture once before reconstruction or history can yield to the caller.
    # All validation and every later consumer use this private snapshot.
    records = json.loads(raw)
    if type(records) is not dict or set(records) != RECORD_NAMES:
        _fail("EXACT_EIGHT_AUTHORED_RECORDS_REQUIRED")
    from .contracts import BoundedSharedTargetDeclarationProjection
    BoundedSharedTargetDeclarationProjection.from_dict(records["projection.json"])
    for name, record in records.items():
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
    # Canonical byte comparison distinguishes JSON booleans, ints and floats,
    # and rejects coherent foreign rehashes as well as valid but altered claims.
    if raw != _bytes(_expected_records()):
        _fail("EXACT_AUTHORED_RECORD_CONTENT_REQUIRED")
    return records


def rebuild_package(*, review_root):
    """Offline fixed reconstruction; no external source is read."""
    validate_historical(review_root=review_root)
    return _expected_records()


def build_package(artifact_path, *, review_root):
    from .source import verified_anchors
    from .contracts import create_projection
    validate_historical(review_root=review_root)
    anchors = verified_anchors(artifact_path, review_root=review_root)
    if _bytes(create_projection(anchors).to_dict()) != _bytes(_projection()):
        _fail("FRESH_C_PROJECTION_DOES_NOT_REPRODUCE")
    return _expected_records()


def manifest(records, *, review_root=DEFAULT_REVIEW_ROOT):
    records = validate_records(records)
    validate_historical(review_root=review_root)
    return _manifest_validated(records, retained_binding())


def _manifest_validated(records, binding):
    """Construct a manifest after validation, without repeating disk work."""
    projection = records["projection.json"]
    body = {"schema_version": PACKAGE_SCHEMA, "canonical_base": CANONICAL_MAIN,
        "status": "BOUNDED_SHARED_TARGET_DECLARATION_PROJECTED",
        "projection_id": projection["projection_id"],
        "record_ids": {name: value["projection_id" if name == "projection.json" else "review_id"]
            for name, value in sorted(records.items())},
        "files": {name: {"bytes": len(_bytes(value)), "sha256": hashlib.sha256(_bytes(value)).hexdigest()}
            for name, value in sorted(records.items())},
        "source_binding": projection["source_binding"], "prior_package_ids": binding["prior_package_ids"],
        "historical_acquisition_identity": binding["historical_acquisition_identity"],
        "artifact_verification_identity": binding["artifact_verification_identity"],
        "selected_references": ["601.2c"], "selected_rule_count": 1,
        "projected_rule_count_before": 88, "new_source_units_projected": 1,
        "projected_rule_count_after": 89, "existing_projection_count_before": 10,
        "existing_projection_count_after": 11, "additional_rules_projected": [],
        "activated_import_member_count": 8, "activated_import_projected_before": 4,
        "activated_import_projected_after": 5, "activated_import_complete": False,
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


def write_package(root, records, *, review_root):
    """Validate every candidate and retained binding before creating output."""
    records = validate_records(records)
    validate_historical(review_root=review_root)
    metadata = _manifest_validated(records, retained_binding())
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
    root = _root(root)
    if {path.name for path in root.iterdir()} != RECORD_NAMES | {"manifest.json"}:
        _fail("EXACT_PACKAGE_FILE_SET_REQUIRED")
    expected = rebuild_package(review_root=review_root)
    for name, value in {**expected, "manifest.json": _manifest_validated(expected, retained_binding())}.items():
        if _read(root / name) != _bytes(value):
            _fail("PACKAGE_CANONICAL_BYTES_OR_BINDINGS_DO_NOT_REPRODUCE")
    return expected


def verify_source(records, artifact_path, *, review_root):
    records = validate_records(records)
    reproduced = build_package(artifact_path, review_root=review_root)
    if _bytes(records) != _bytes(reproduced):
        _fail("EXACT_C_SOURCE_CORRESPONDENCE_DOES_NOT_REPRODUCE")
    rule = records["projection.json"]["rules"][0]
    return {"status": "VERIFIED_EXACT_COMPLETE_C_ONLY_SOURCE_UNIT",
        "selected_references": ["601.2c"], "selected_rule_count": 1,
        "new_source_units_projected": 1, "projection_id": records["projection.json"]["projection_id"],
        "source_anchor": rule["source_anchor"], "source_body_retained": False,
        "outgoing_numbered_citations": [], "outgoing_ranges": [],
        "design_source_correspondence_review_id": records["design-source-correspondence.json"]["review_id"]}


def current_view(records):
    """Resolve typed enclosing-package bindings to the actual manifest identity.

    The immutable authored records avoid circular content hashes. This read-only
    view binds their current c rows to the verified enclosing manifest instead.
    """
    result = validate_records(records)
    validate_historical(review_root=DEFAULT_REVIEW_ROOT)
    metadata = _manifest_validated(result, retained_binding())
    return _resolved_view(result, metadata)


def _resolved_view(records, metadata):
    """Resolve a private snapshot using its already validated manifest."""
    result = _copy(records)
    def resolve(value):
        if type(value) is dict:
            if "package_binding" in value:
                if value.pop("package_binding") != "THIS_ENCLOSING_PACKAGE":
                    _fail("ENCLOSING_PACKAGE_BINDING_REQUIRED")
                value["package_id"] = metadata["package_id"]
            for child in value.values():
                resolve(child)
        elif type(value) is list:
            for child in value:
                resolve(child)
    resolve(result)
    return {"package_id": metadata["package_id"], "records": result,
        "view_kind": "READ_ONLY_RESOLVED_PACKAGE_BINDINGS_NOT_NEW_CANONICAL_RECORDS"}


def composite_view(records):
    return current_view(records)["records"]["composite-coverage.json"]["findings"]
