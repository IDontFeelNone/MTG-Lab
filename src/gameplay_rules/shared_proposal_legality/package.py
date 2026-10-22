"""Canonical append-only package for one non-executable proposal-legality unit.

Offline reconstruction verifies retained evidence without reopening its source.
Fresh reproduction has a separate e-only source boundary and selector.
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
from gameplay_rules.activated_ability_projection import package as activated
from gameplay_rules.shared_target_declaration import package as declaration
from gameplay_rules.shared_target_allocation import package as allocation
from gameplay_rules.projection.dependency_package import _read, _root
from gameplay_rules.projection.mana_stack_exception_package import _canonical_candidate
from .reviews import CANONICAL_MAIN, DESIGN_ID, DESIGN_NAME, DESIGN_REVIEWS, PERMISSIONS

PACKAGE_NAME = "gameplay-rules-bounded-shared-proposal-legality"
PACKAGE_SCHEMA = "gameplay-bounded-shared-proposal-legality-package-v1"
RECORD_DOMAIN = "gameplay-bounded-shared-proposal-legality-record-v1"
RECORD_NAMES = frozenset(("projection.json", "design-source-correspondence.json",
    "casting-parent-reassessment.json", "activated-import-reassessment.json",
    "consumer-semantic-boundaries.json", "composite-coverage.json",
    "preservation-readiness.json", "subsequent-recommendation.json", "recovery-dependency.json"))
REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_REVIEW_ROOT = REPOSITORY_ROOT / "reference-reviews"
INHERITED_TOOL_SHA256 = "d2788448d15a06107c11e9734d4ed82c5a9dca75868cf38a062cb329b5b72f53"


def _fail(message):
    raise GameplayContractError("shared_proposal_legality_package", message)


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
    """Retain PR #201's fixed offline validator without invoking source access."""
    return allocation._historical_tool()


def retained_binding():
    """Return a defensive copy of fixed contract-derived metadata, never authority from a cache."""
    return json.loads(_retained_binding_bytes())


@cache
def _retained_binding_bytes():
    """Cache only metadata derived from immutable authored contracts.

    No default review directory is read during fixed reconstruction: a caller's
    selected history is checked independently at each public disk boundary.
    """
    old = allocation._expected_records()
    parent = allocation._manifest_validated(old, allocation.retained_binding())
    package_id = parent["package_id"]
    view = _copy(old["composite-coverage.json"]["findings"])

    def resolve(value):
        if type(value) is dict:
            if "package_binding" in value:
                if value.pop("package_binding") != "THIS_ENCLOSING_PACKAGE":
                    _fail("RETAINED_ENCLOSING_PACKAGE_BINDING_INVALID")
                value["package_id"] = package_id
            for child in value.values():
                resolve(child)
        elif type(value) is list:
            for child in value:
                resolve(child)

    resolve(view)
    binding = activated.retained_binding()
    binding["canonical_base"] = CANONICAL_MAIN
    binding["projection_components"] = view["projection_components"]
    binding["rule_bindings"] = view["all_prior_rule_bindings"]
    binding["prior_package_ids"] = _copy(parent["prior_package_ids"])
    procedure = activated._expected_records()["procedure-responsibilities.json"]["findings"]
    binding["responsibility_names"] = [row["responsibility"] for row in procedure["rows"]]
    projection = old["projection.json"]
    for rule in projection["rules"]:
        binding["rule_bindings"][rule["rule_reference"]] = {
            "retained_package": allocation.PACKAGE_NAME, "package_id": package_id,
            "projection_id": projection["projection_id"], "rule_id": rule["rule_id"],
            "anchor_identity": rule["source_anchor"]["anchor_id"],
            "source_anchor": _copy(rule["source_anchor"]),
            "identity_basis": "EXISTING_STANDALONE_ID"}
    binding["prior_package_ids"][allocation.PACKAGE_NAME] = package_id
    return _bytes(binding)


def _validated_historical_records(review_root):
    """Freshly verify the same 150 files, extending the bounded c/d checks."""
    from gameplay_rules.shared_target_allocation.contracts import BoundedSharedTargetAllocationProjection
    root = _root(review_root)
    successors = allocation._validated_historical_records(root)
    successors[allocation.PACKAGE_NAME] = validate_retained_stage(root,
        name=allocation.PACKAGE_NAME, package_schema=allocation.PACKAGE_SCHEMA,
        package_id="sha256:56ad746cd5c87c0fac1b864289283135b4d4adb10ee441fbaa970a1dcefb1678",
        record_domain=allocation.RECORD_DOMAIN, record_names=allocation.RECORD_NAMES,
        projection_type=BoundedSharedTargetAllocationProjection)
    return successors


def validate_historical(*, review_root):
    """Check d's own schema, domains and manifest, preserving every prior binding.

    Every retained file is read and checked against existing pins or a fixed
    manifest identity. PR #201's integer-schema reviews retain their distinct
    own review domain and enclosing package domain.
    No inherited source verifier or source selector is called.
    """
    root = _root(review_root)
    successors = _validated_historical_records(root)
    records = successors[allocation.PACKAGE_NAME]["records"]
    parent = successors[allocation.PACKAGE_NAME]["manifest"]
    expected_package = "sha256:56ad746cd5c87c0fac1b864289283135b4d4adb10ee441fbaa970a1dcefb1678"
    if (type(parent.get("schema_version")) is not str
            or parent["schema_version"] != allocation.PACKAGE_SCHEMA
            or type(parent.get("package_id")) is not str
            or parent["package_id"] != expected_package):
        _fail("RETAINED_PR203_PACKAGE_BINDING_INVALID")
    body = {key: value for key, value in parent.items() if key != "package_id"}
    if parent["package_id"] != _identity(allocation.PACKAGE_SCHEMA, body):
        _fail("RETAINED_PR203_PACKAGE_OWN_IDENTITY_INVALID")
    for filename, record in records.items():
        identity_field = "projection_id" if filename == "projection.json" else "review_id"
        domain = ("gameplay-cr-bounded-shared-target-allocation-projection-v1"
            if filename == "projection.json" else allocation.RECORD_DOMAIN)
        own_body = {key: value for key, value in record.items() if key != identity_field}
        own = _identity(domain, own_body)
        schema_valid = (record.get("schema_version") == domain
            if filename == "projection.json" else
            type(record.get("schema_version")) is int and record["schema_version"] == 1)
        if (not schema_valid or type(record.get(identity_field)) is not str
                or record[identity_field] != own
                or _bytes(parent["record_ids"][filename]) != _bytes(own)):
            _fail("RETAINED_PR203_OWN_IDENTITY_OR_MANIFEST_BINDING_INVALID")
    projection = records["projection.json"]
    rule = projection["rules"][0]
    pins = ((projection["projection_id"], "sha256:bd5739a5d9afe5e06d6eb662cbe0b5c4c5b87711f502d039e980c51c6c7f4f66"),
        (rule["rule_id"], "sha256:54b3b3d770276044bb519285cb6f202ce236656bd82a20d4a1fc16ec57e8d1d5"),
        (rule["source_anchor"]["anchor_id"], "sha256:c39fda4f934f1a6d13a863a984a128dee24513bc26d2d2f28b3ea2b3e6aa30c7"))
    if any(_bytes(actual) != _bytes(expected) for actual, expected in pins):
        _fail("RETAINED_PR203_PROJECTION_RULE_OR_ANCHOR_PIN_INVALID")
    inspection_raw = _read(root / DESIGN_NAME / "source-inspection.json")
    inspection = json.loads(inspection_raw)
    own_body = {key: value for key, value in inspection.items() if key != "review_id"}
    if (type(inspection.get("schema_version")) is not int or inspection["schema_version"] != 1
            or inspection.get("review_id") != DESIGN_REVIEWS["source-inspection.json"]
            or inspection["review_id"] != _identity("gameplay-shared-casting-stage-gap-design-record-v1", own_body)
            or inspection_raw != _bytes(inspection)):
        _fail("RETAINED_E_OBSERVATION_AUTHORITY_INVALID")
    spans = [row for row in inspection["findings"]["review_spans"] if row["reference"] == "601.2e"]
    citations = [row for row in inspection["findings"]["literal_reference_observations"] if row["from"] == "601.2e"]
    from .source import VERIFIED_ANCHORS
    from gameplay_rules.projection.contracts import _json
    anchor = _json(VERIFIED_ANCHORS)[0]
    correspondence = {"byte_start": "byte_start", "byte_end": "byte_end",
        "starting_physical_line": "starting_physical_line", "ending_physical_line": "ending_physical_line",
        "line_count": "line_count", "owned_example_line_count": "owned_example_line_count",
        "span_sha256": "span_sha256"}
    if (len(spans) != 1 or len(citations) != 1
            or any(_bytes(spans[0][old]) != _bytes(anchor[new]) for old, new in correspondence.items())
            or spans[0]["next_marker"] != anchor["following_marker"]["rule_reference"]
            or spans[0]["next_marker_physical_line"] != anchor["following_marker"]["physical_line"]
            or spans[0]["registered_projected_source_anchor"] is not False
            or spans[0]["next_body_inspected_as_boundary_context"] is not False
            or _bytes(citations[0]) != _bytes({"from": "601.2e", "direct_citations": [{"target": "733", "status": "REVIEW_ONLY_CITATION_OBSERVED", "projected_target": False, "future_context": "Recovery semantics remain an external frontier; checkpoint description is possible without resolving recovery."}], "ranges": []})):
        _fail("FRESH_E_ANCHOR_AND_HISTORICAL_REVIEW_OBSERVATION_DIFFER")
    return retained_binding()


def _projection():
    from .contracts import create_projection
    from .source import VERIFIED_ANCHORS
    return create_projection(VERIFIED_ANCHORS).to_dict()


def _expected_records():
    return json.loads(_expected_record_bytes())


@cache
def _expected_record_bytes():
    """Fixed authored canonical bytes only; no mutable candidate or source is cached."""
    from .reviews import authored_records
    projection = _projection()
    bodies = authored_records(retained_binding(), projection)
    return _bytes({"projection.json": projection,
        **{name: _identify_record(body) for name, body in bodies.items()}})


def validate_records(records):
    raw = _bytes(records)
    # Own exactly the captured content before reconstruction can yield to a
    # caller. Every check and consumer must use this snapshot, never a later
    # copy of the caller's live dictionary.
    records = json.loads(raw)
    if type(records) is not dict or set(records) != RECORD_NAMES:
        _fail("EXACT_NINE_AUTHORED_RECORDS_REQUIRED")
    from .contracts import BoundedSharedProposalLegalityProjection
    BoundedSharedProposalLegalityProjection.from_dict(records["projection.json"])
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
        _fail("FRESH_E_PROJECTION_DOES_NOT_REPRODUCE")
    return _expected_records()


def manifest(records, *, review_root=DEFAULT_REVIEW_ROOT):
    records = validate_records(records)
    validate_historical(review_root=review_root)
    return _manifest_validated(records, retained_binding())



def _manifest_validated(records, binding):
    """Pure manifest construction after the caller has validated all inputs."""
    projection = records["projection.json"]
    body = {"schema_version": PACKAGE_SCHEMA, "canonical_base": CANONICAL_MAIN,
        "status": "BOUNDED_SHARED_PROPOSAL_LEGALITY_PROJECTED",
        "projection_id": projection["projection_id"],
        "record_ids": {name: value["projection_id" if name == "projection.json" else "review_id"]
            for name, value in sorted(records.items())},
        "files": {name: {"bytes": len(_bytes(value)), "sha256": hashlib.sha256(_bytes(value)).hexdigest()}
            for name, value in sorted(records.items())},
        "source_binding": projection["source_binding"], "prior_package_ids": binding["prior_package_ids"],
        "historical_acquisition_identity": binding["historical_acquisition_identity"],
        "artifact_verification_identity": binding["artifact_verification_identity"],
        "selected_references": ["601.2e"], "selected_rule_count": 1,
        "projected_rule_count_before": 90, "new_source_units_projected": 1,
        "projected_rule_count_after": 91, "existing_projection_count_before": 12,
        "existing_projection_count_after": 13, "additional_rules_projected": [],
        "activated_import_member_count": 8, "activated_import_projected_before": 6,
        "activated_import_projected_after": 7, "activated_import_complete": False,
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
        _fail("EXACT_E_SOURCE_CORRESPONDENCE_DOES_NOT_REPRODUCE")
    rule = records["projection.json"]["rules"][0]
    return {"status": "VERIFIED_EXACT_COMPLETE_E_ONLY_SOURCE_UNIT",
        "selected_references": ["601.2e"], "selected_rule_count": 1,
        "new_source_units_projected": 1, "projection_id": records["projection.json"]["projection_id"],
        "source_anchor": rule["source_anchor"], "source_body_retained": False,
        "outgoing_numbered_citations": ["733"], "outgoing_ranges": [],
        "design_source_correspondence_review_id": records["design-source-correspondence.json"]["review_id"]}


def current_view(records):
    """Resolve typed enclosing-package bindings to the actual manifest identity.

    The immutable authored records avoid circular content hashes. This read-only
    view binds their current e rows to the verified enclosing manifest instead.
    """
    result = validate_records(records)
    validate_historical(review_root=DEFAULT_REVIEW_ROOT)
    metadata = _manifest_validated(result, retained_binding())
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
