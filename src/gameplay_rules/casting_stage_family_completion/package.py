"""One append-only, non-executable package for the a/i completion batch.

Offline reconstruction and fresh exact-source reproduction are separate paths.
Every public candidate boundary owns a validated canonical snapshot before use.
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
from gameplay_rules.shared_proposal_legality import package as legality
from gameplay_rules.projection.dependency_package import _read, _root
from gameplay_rules.projection.mana_stack_exception_package import _canonical_candidate
from .reviews import CANONICAL_MAIN, PERMISSIONS, HISTORICAL_RECOMMENDATION

PACKAGE_NAME = "gameplay-rules-casting-stage-family-completion"
PACKAGE_SCHEMA = "gameplay-casting-stage-family-completion-package-v1"
RECORD_DOMAIN = "gameplay-casting-stage-family-completion-record-v1"
RECORD_NAMES = frozenset(("projection.json", "preflight.json", "scope-decision.json",
    "source-correspondence.json", "procedure-map.json", "range-reassessment.json",
    "legality-gap-assessment.json", "consumer-semantic-boundaries.json",
    "composite-coverage.json", "preservation-readiness.json", "subsequent-recommendation.json"))
REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_REVIEW_ROOT = REPOSITORY_ROOT / "reference-reviews"
RETAINED_E_PACKAGE_ID = "sha256:dc2e8b6ee1c79b8c6696f768317d7fa140e6130725ad4993cc0a5547517a3589"


def _fail(message):
    raise GameplayContractError("casting_stage_family_completion_package", message)


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
    """Resolve only explicit self-package placeholders in a privately owned tree."""
    if type(value) is dict:
        if "package_binding" in value:
            if value.pop("package_binding") != "THIS_ENCLOSING_PACKAGE":
                _fail("ENCLOSING_PACKAGE_BINDING_REQUIRED")
            value["package_id"] = package_id
        for child in value.values():
            _resolve_package_bindings(child, package_id)
    elif type(value) is list:
        for child in value:
            _resolve_package_bindings(child, package_id)


def retained_binding():
    """Return fixed defensive metadata; disk history is checked at public boundaries."""
    return json.loads(_retained_binding_bytes())


@cache
def _retained_binding_bytes():
    old = legality._expected_records()
    parent = legality._manifest_validated(old, legality.retained_binding())
    if parent["package_id"] != RETAINED_E_PACKAGE_ID:
        _fail("RETAINED_E_PACKAGE_IDENTITY_INVALID")
    view = _copy(old["composite-coverage.json"]["findings"])
    _resolve_package_bindings(view, RETAINED_E_PACKAGE_ID)
    binding = legality.retained_binding()
    binding["canonical_base"] = CANONICAL_MAIN
    binding["projection_components"] = view["projection_components"]
    binding["rule_bindings"] = view["all_prior_rule_bindings"]
    binding["prior_package_ids"] = _copy(parent["prior_package_ids"])
    projection = old["projection.json"]
    for rule in projection["rules"]:
        binding["rule_bindings"][rule["rule_reference"]] = {
            "retained_package": legality.PACKAGE_NAME, "package_id": RETAINED_E_PACKAGE_ID,
            "projection_id": projection["projection_id"], "rule_id": rule["rule_id"],
            "anchor_identity": rule["source_anchor"]["anchor_id"],
            "source_anchor": _copy(rule["source_anchor"]), "identity_basis": "EXISTING_STANDALONE_ID"}
    binding["prior_package_ids"][legality.PACKAGE_NAME] = RETAINED_E_PACKAGE_ID
    return _bytes(binding)


def _validated_historical_records(review_root):
    from gameplay_rules.shared_proposal_legality.contracts import BoundedSharedProposalLegalityProjection
    root = _root(review_root)
    successors = legality._validated_historical_records(root)
    successors[legality.PACKAGE_NAME] = validate_retained_stage(root,
        name=legality.PACKAGE_NAME, package_schema=legality.PACKAGE_SCHEMA,
        package_id=RETAINED_E_PACKAGE_ID, record_domain=legality.RECORD_DOMAIN,
        record_names=legality.RECORD_NAMES, projection_type=BoundedSharedProposalLegalityProjection)
    return successors


def validate_historical(*, review_root):
    """Check each predecessor through its own fields, domain and enclosing manifest.

    The existing chain checks canonical bytes freshly. e's projection_id and
    review_id fields are distinct; neither is replaced by a similarly shaped ID.
    No inherited source selector or body verifier is invoked.
    """
    successors = _validated_historical_records(review_root)
    retained = successors[legality.PACKAGE_NAME]
    records, parent = retained["records"], retained["manifest"]
    projection = records["projection.json"]
    rule = projection["rules"][0]
    expected = {"projection": "sha256:cfe4da820b091ab63c9e8764003bdb689becc7af125fec712e386260f7b0f2a8",
        "rule": "sha256:071dcf527bf2c39b6be07fa34ac12c813a26a06b7962f1021c4ae8179b0d61d1",
        "anchor": "sha256:672fc046290b004bbac9f0eb677f02ccd64dbc7bc318fed399ba2b20c8f6afe7"}
    observed = {"projection": projection["projection_id"], "rule": rule["rule_id"],
        "anchor": rule["source_anchor"]["anchor_id"]}
    if (_bytes(observed) != _bytes(expected)
            or parent["package_id"] != RETAINED_E_PACKAGE_ID
            or records["subsequent-recommendation.json"]["review_id"] != HISTORICAL_RECOMMENDATION):
        _fail("RETAINED_E_OWN_BINDINGS_OR_RECOMMENDATION_CHANGED")
    historical = parent["historical_acquisition_identity"]
    if historical != "sha256:669d7db9ebcaf97853058fd62f408ce3c6596d5dae0ee72ff39d2ba9df56bb53":
        _fail("HISTORICAL_ACQUISITION_IDENTITY_CHANGED")
    # PR #201's i finding remains review-only history. Check its actual own
    # review_id domain and enclosing package, then compare metadata with the
    # newly verified anchor. Reading this record never reopens any source body.
    design = successors["gameplay-rules-shared-casting-stage-gap-design"]
    design_parent = design["manifest"]
    observation = design["records"]["source-inspection.json"]
    design_domain = "gameplay-shared-casting-stage-gap-design-package-v1"
    review_domain = "gameplay-shared-casting-stage-gap-design-record-v1"
    design_body = {key: value for key, value in design_parent.items() if key != "package_id"}
    observation_body = {key: value for key, value in observation.items() if key != "review_id"}
    if (type(design_parent.get("schema_version")) is not str
            or design_parent["schema_version"] != design_domain
            or design_parent.get("package_id") != "sha256:4ec995686f7ebb851fae1d6a3b732b1669a9f8cbe7d7ad547f939d928b6c729f"
            or design_parent["package_id"] != _identity(design_domain, design_body)
            or type(observation.get("schema_version")) is not int or observation["schema_version"] != 1
            or observation.get("review_id") != "sha256:b238417023f10c4ebfd83340b6a105b95829c599126d5ab7bf52d941b8f23bc9"
            or observation["review_id"] != _identity(review_domain, observation_body)
            or design_parent["record_ids"]["source-inspection.json"] != observation["review_id"]):
        _fail("RETAINED_I_OBSERVATION_OWN_IDENTITY_OR_MANIFEST_BINDING_INVALID")
    spans = [row for row in observation["findings"]["review_spans"] if row["reference"] == "601.2i"]
    citations = [row for row in observation["findings"]["literal_reference_observations"] if row["from"] == "601.2i"]
    from .source import VERIFIED_ANCHORS
    from gameplay_rules.projection.contracts import _json
    anchor = next(row for row in _json(VERIFIED_ANCHORS) if row["rule_reference"] == "601.2i")
    corresponding_fields = ("byte_start", "byte_end", "starting_physical_line", "ending_physical_line",
        "line_count", "owned_example_line_count", "span_sha256")
    expected_citations = {"from": "601.2i", "direct_citations": [], "ranges": [{
        "start": "601.2a", "end": "601.2h", "members": ["601.2" + letter for letter in "abcdefgh"],
        "projected_members": ["601.2b", "601.2f", "601.2g", "601.2h"],
        "unprojected_members": ["601.2a", "601.2c", "601.2d", "601.2e"],
        "status": "REVIEW_ONLY_RANGE_OBSERVED_NOT_PROJECTED_DEPENDENCY"}]}
    if (len(spans) != 1 or len(citations) != 1
            or any(_bytes(spans[0][field]) != _bytes(anchor[field]) for field in corresponding_fields)
            or anchor["span_length"] != spans[0]["byte_end"] - spans[0]["byte_start"]
            or spans[0]["next_marker"] != anchor["following_marker"]["rule_reference"]
            or spans[0]["next_marker_physical_line"] != anchor["following_marker"]["physical_line"]
            or spans[0]["registered_projected_source_anchor"] is not False
            or spans[0]["next_body_inspected_as_boundary_context"] is not False
            or _bytes(citations[0]) != _bytes(expected_citations)):
        _fail("FRESH_I_ANCHOR_AND_HISTORICAL_REVIEW_OBSERVATION_DIFFER")
    return retained_binding()


def _projection():
    from .contracts import create_projection
    from .source import VERIFIED_ANCHORS
    return create_projection(VERIFIED_ANCHORS).to_dict()


def _expected_records():
    return json.loads(_expected_record_bytes())


@cache
def _expected_record_bytes():
    """Cache only fixed authored bytes, never candidate data or successful disk checks."""
    from .reviews import authored_records
    projection = _projection()
    bodies = authored_records(retained_binding(), projection)
    return _bytes({"projection.json": projection,
        **{name: _identify_record(body) for name, body in bodies.items()}})


def validate_records(records):
    raw = _bytes(records)
    # This is the only candidate snapshot. All subsequent paths use these exact
    # validated bytes, including manifest creation, source verification and I/O.
    snapshot = json.loads(raw)
    if type(snapshot) is not dict or set(snapshot) != RECORD_NAMES:
        _fail("EXACT_ELEVEN_AUTHORED_RECORDS_REQUIRED")
    from .contracts import CastingStageFamilyCompletionProjection
    CastingStageFamilyCompletionProjection.from_dict(snapshot["projection.json"])
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
    """Offline fixed reconstruction is not fresh source verification."""
    validate_historical(review_root=review_root)
    return _expected_records()


def build_package(artifact_path, *, review_root):
    from .source import verified_anchors
    from .contracts import create_projection
    validate_historical(review_root=review_root)
    anchors = verified_anchors(artifact_path, review_root=review_root)
    if _bytes(create_projection(anchors).to_dict()) != _bytes(_projection()):
        _fail("FRESH_TWO_UNIT_PROJECTION_DOES_NOT_REPRODUCE")
    return _expected_records()


def _manifest_validated(records, binding):
    projection = records["projection.json"]
    body = {"schema_version": PACKAGE_SCHEMA, "canonical_base": CANONICAL_MAIN,
        "status": "CASTING_STAGE_FAMILY_COMPLETION_PROJECTED", "projection_id": projection["projection_id"],
        "record_ids": {name: value["projection_id" if name == "projection.json" else "review_id"]
            for name, value in sorted(records.items())},
        "files": {name: {"bytes": len(_bytes(value)), "sha256": hashlib.sha256(_bytes(value)).hexdigest()}
            for name, value in sorted(records.items())},
        "source_binding": deepcopy(projection["source_binding"]),
        "prior_package_ids": deepcopy(binding["prior_package_ids"]),
        "historical_acquisition_identity": binding["historical_acquisition_identity"],
        "artifact_verification_identity": binding["artifact_verification_identity"],
        "selected_references": ["601.2a", "601.2i"], "selected_rule_count": 2,
        "projected_rule_count_before": 91, "new_source_units_projected": 2,
        "projected_rule_count_after": 93, "existing_projection_count_before": 13,
        "existing_projection_count_after": 14, "additional_rules_projected": [],
        "stage_coverage": "9/9", "parent_proposal_range_coverage": "4/4",
        "activated_import_range_count": 1, "activated_import_member_count": 8,
        "activated_import_projected_before": 7, "activated_import_projected_after": 8,
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
    """Reject invalid input before any output directory or file is created."""
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
        _fail("EXACT_TWO_UNIT_SOURCE_CORRESPONDENCE_DOES_NOT_REPRODUCE")
    return {"status": "VERIFIED_EXACT_COMPLETE_TWO_UNIT_SOURCE_BATCH",
        "selected_references": ["601.2a", "601.2i"], "selected_rule_count": 2,
        "new_source_units_projected": 2, "projection_id": snapshot["projection.json"]["projection_id"],
        "source_anchors": [deepcopy(row["source_anchor"]) for row in snapshot["projection.json"]["rules"]],
        "source_body_retained": False, "outgoing_numbered_citations": {"601.2a": ["611.2f", "610.5"], "601.2i": []},
        "outgoing_ranges": [{"origin": "601.2i", "start": "601.2a", "end": "601.2h"}],
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
