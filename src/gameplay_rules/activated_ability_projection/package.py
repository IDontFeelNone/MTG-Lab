"""Closed append-only projection package; no entry point grants execution.

Fresh source reproduction and offline metadata reconstruction remain distinct.
All candidates are checked against the finite authored contract before output.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from evidence.contracts import deterministic_json, sha256_identity
from gameplay_rules.errors import GameplayContractError
from gameplay_rules.projection.dependency_package import _read, _root
from gameplay_rules.projection.mana_stack_exception_package import _canonical_candidate
from gameplay_rules.activated_ability_design import package as design

CANONICAL_MAIN = "2aa01764db0cfbcd89bc3a30a4433c4f24ea5893"
PACKAGE_NAME = "gameplay-rules-bounded-activated-ability-procedure-projection"
PACKAGE_SCHEMA = "gameplay-bounded-activated-ability-procedure-package-v1"
RECORD_DOMAIN = "gameplay-bounded-activated-ability-procedure-record-v1"
PINS_SHA256 = "9cc186e74977b66142109faf244fccfe640005041c1b21c1e007a5e751275f2b"
RECORD_NAMES = frozenset(("projection.json", "design-source-correspondence.json",
    "local-scope.json", "procedure-responsibilities.json", "casting-import.json",
    "cost-analogy.json", "mana-relationships.json", "consumer-reassessment.json",
    "composite-coverage.json", "overall-readiness.json"))
DESIGN_PACKAGE = "gameplay-rules-activated-ability-procedure-design"


def _fail(message):
    raise GameplayContractError("bounded_activated_ability_package", message)


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
    return _copy(_pins()["binding"])


def validate_review_bindings(binding, *, review_root):
    """Use inherited contracts and seven explicitly named integer-schema records.

    PR #199's integer schema is deliberately separate from its hash domain.
    Own identity fields and parent manifest paths are never inferred or scanned.
    """
    try:
        _canonical_candidate(binding)
        old_contracts = design._review_binding_contracts()
        new_names = {DESIGN_PACKAGE + "/" + name for name in design.RECORD_NAMES}
        names = set(old_contracts) | new_names
        if (type(binding) is not dict or type(binding.get("review_bindings")) is not dict
                or set(binding["review_bindings"]) != names
                or type(binding.get("prior_package_ids")) is not dict):
            _fail("MISSING_OR_UNSUPPORTED_REVIEW_BINDING_SELECTION")
        selections = binding["review_bindings"]
        if any(type(value) is not str for value in selections.values()):
            _fail("REVIEW_BINDING_IDENTITY_STRING_REQUIRED")
        if len(set(selections.values())) != len(names):
            _fail("AMBIGUOUS_REVIEW_BINDING_SELECTION")
        legacy = _copy(binding)
        legacy["review_bindings"] = {name: selections[name] for name in old_contracts}
        design.validate_review_bindings(legacy, review_root=review_root)
        root = _root(review_root)
        parent, _ = design._historical_json(root / DESIGN_PACKAGE / "manifest.json")
        if (type(parent.get("schema_version")) is not str
                or parent["schema_version"] != design.PACKAGE_SCHEMA
                or type(parent.get("package_id")) is not str
                or type(binding["prior_package_ids"].get(DESIGN_PACKAGE)) is not str
                or parent["package_id"] != binding["prior_package_ids"][DESIGN_PACKAGE]):
            _fail("REVIEW_PARENT_PACKAGE_BINDING_MISMATCH")
        body = {key: value for key, value in parent.items() if key != "package_id"}
        if parent["package_id"] != "sha256:" + sha256_identity({
                "domain": design.PACKAGE_SCHEMA, "content": body}):
            _fail("REVIEW_PARENT_PACKAGE_IDENTITY_INVALID")
        for filename in sorted(design.RECORD_NAMES):
            record, raw = design._historical_json(root / DESIGN_PACKAGE / filename)
            if (type(record.get("schema_version")) is not int or record["schema_version"] != 1
                    or type(record.get("review_id")) is not str):
                _fail("UNSUPPORTED_OR_MISSING_REVIEW_OWN_IDENTITY")
            body = {key: value for key, value in record.items() if key != "review_id"}
            own = "sha256:" + sha256_identity({"domain": design.RECORD_DOMAIN, "content": body})
            if record["review_id"] != own or selections[DESIGN_PACKAGE + "/" + filename] != own:
                _fail("REVIEW_BINDING_DOES_NOT_NAME_OWN_IDENTITY")
            if (type(parent.get("record_ids")) is not dict
                    or type(parent["record_ids"].get(filename)) is not str
                    or parent["record_ids"][filename] != own):
                _fail("REVIEW_OWN_MANIFEST_BINDING_MISMATCH")
            files = parent.get("files")
            item = files.get(filename) if type(files) is dict else None
            if (type(item) is not dict or set(item) != {"bytes", "sha256"}
                    or type(item["bytes"]) is not int or item["bytes"] != len(raw)
                    or type(item["sha256"]) is not str
                    or item["sha256"] != hashlib.sha256(raw).hexdigest()):
                _fail("REVIEW_MANIFEST_CANONICAL_BYTES_MISMATCH")
        # Contract validity does not authorize replacement historical findings.
        # Bind the closed selected evidence to exact canonical-main bytes too,
        # even when this validator is called outside verify_prior_packages.
        pins = _pins()["protected_files"]
        for selection in sorted(names):
            package_name, filename = selection.split("/")
            for relative in (selection, package_name + "/manifest.json"):
                raw = _read(root / relative)
                if hashlib.sha256(raw).hexdigest() != pins["reference-reviews/" + relative]:
                    _fail("HISTORICAL_REVIEW_EXPECTED_CONTENT_CHANGED")
        if _canonical_candidate(binding) != _bytes(retained_binding()):
            _fail("EXACT_RETAINED_BINDING_REQUIRED")
        return _copy(selections)
    except GameplayContractError as error:
        if error.code == "bounded_activated_ability_package":
            raise
        _fail("INVALID_HISTORICAL_REVIEW_BINDING_CONTRACT")
    except (OSError, ValueError, TypeError, KeyError, AttributeError, UnicodeError, RecursionError):
        _fail("INVALID_HISTORICAL_REVIEW_BINDING_CONTRACT")


def verify_prior_packages(review_root):
    root = _root(review_root)
    groups = {}
    for name, digest in _pins()["protected_files"].items():
        if name.startswith("reference-reviews/"):
            relative = Path(name[len("reference-reviews/"):])
            groups.setdefault(relative.parts[0], {})[relative.name] = digest
    if len(groups) != 18 or sum(map(len, groups.values())) != 115:
        _fail("EXACT_PRIOR_EVIDENCE_INVENTORY_REQUIRED")
    for name, files in groups.items():
        package = _root(root / name)
        if {path.name for path in package.iterdir()} != set(files):
            _fail("PRIOR_GAMEPLAY_EVIDENCE_FILE_SET_CHANGED")
        for filename, digest in files.items():
            if hashlib.sha256(_read(package / filename)).hexdigest() != digest:
                _fail("PRIOR_GAMEPLAY_EVIDENCE_BYTES_CHANGED")
    binding = retained_binding()
    validate_review_bindings(binding, review_root=root)
    return binding


def verify_preservation(repo_root):
    root = _root(repo_root)
    pins = _pins()
    for name, digest in pins["protected_files"].items():
        if hashlib.sha256(_read(root / name)).hexdigest() != digest:
            _fail("CANONICAL_BASE_PROTECTED_BYTES_CHANGED")
    verify_prior_packages(root / "reference-reviews")
    return {"canonical_base": CANONICAL_MAIN, "inherited_source_files_preserved": 339,
        "inherited_gameplay_evidence_files_preserved": 115,
        "inherited_gameplay_evidence_directories_preserved": 18,
        "protected_files_preserved": 454, "projected_real_source_units": 88,
        "distinct_existing_projections": 10, "selected_references": ["602.2", "602.2a", "602.2b"]}


def _identify_record(body):
    value = _copy(body)
    if type(value) is not dict:
        _fail("PLAIN_JSON_RECORD_BODY_REQUIRED")
    value.pop("review_id", None)
    return {**value, "review_id": "sha256:" + sha256_identity({
        "domain": RECORD_DOMAIN, "content": value})}


def _projection():
    from .contracts import create_projection
    from .source import VERIFIED_ANCHORS
    return create_projection(VERIFIED_ANCHORS).to_dict()


def _expected_records(binding=None):
    from .reviews import authored_records
    binding = retained_binding() if binding is None else _copy(binding)
    projection = _projection()
    bodies = authored_records(binding, projection)
    return {"projection.json": projection, **{name: _identify_record(body) for name, body in bodies.items()}}


def rebuild_package(*, review_root):
    """Reconstruct fixed metadata offline, without claiming fresh source access."""
    return _expected_records(binding=verify_prior_packages(review_root))


def build_package(artifact_path, *, review_root):
    from .source import verified_anchors
    from .contracts import create_projection
    binding = verify_prior_packages(review_root)
    anchors = verified_anchors(artifact_path, review_root=review_root)
    if _canonical_candidate(create_projection(anchors).to_dict()) != _bytes(_projection()):
        _fail("FRESH_PROJECTION_DOES_NOT_REPRODUCE")
    return _expected_records(binding=binding)


def _validate_records(records):
    raw = _canonical_candidate(records)
    if type(records) is not dict or set(records) != RECORD_NAMES:
        _fail("EXACT_TEN_AUTHORED_RECORDS_REQUIRED")
    from .contracts import BoundedActivatedAbilityProjection
    projection = records["projection.json"]
    # The closed expected bytes below additionally reject rehashed invalid content.
    BoundedActivatedAbilityProjection.from_dict(projection)
    for name, record in records.items():
        if name == "projection.json":
            continue
        if (type(record) is not dict or type(record.get("review_id")) is not str
                or type(record.get("schema_version")) is not int or record["schema_version"] != 1):
            _fail("RECORD_IDENTITY_REQUIRED")
        if _canonical_candidate(record) != _bytes(_identify_record(record)):
            _fail("RECORD_IDENTITY_DOES_NOT_REPRODUCE")
    if raw != _bytes(_expected_records()):
        _fail("AUTHORED_RECORDS_DO_NOT_REPRODUCE")
    return records


def manifest(records):
    _validate_records(records)
    binding = retained_binding()
    projection = records["projection.json"]
    body = {"schema_version": PACKAGE_SCHEMA, "canonical_base": CANONICAL_MAIN,
        "status": "BOUNDED_ACTIVATED_ABILITY_PROCEDURE_PROJECTED",
        "projection_id": projection["projection_id"],
        "record_ids": {name: value["projection_id" if name == "projection.json" else "review_id"]
            for name, value in sorted(records.items())},
        "files": {name: {"bytes": len(_bytes(value)), "sha256": hashlib.sha256(_bytes(value)).hexdigest()}
            for name, value in sorted(records.items())},
        "source_binding": projection["source_binding"],
        "prior_package_ids": binding["prior_package_ids"],
        "historical_acquisition_identity": binding["historical_acquisition_identity"],
        "artifact_verification_identity": binding["artifact_verification_identity"],
        "canonical_base_preservation_pins_identity": "sha256:" + PINS_SHA256,
        "selected_references": ["602.2", "602.2a", "602.2b"], "selected_rule_count": 3,
        "projected_rule_count_before": 85, "new_source_units_projected": 3,
        "projected_rule_count_after": 88, "existing_projection_count_before": 9,
        "existing_projection_count_after": 10, "additional_rules_projected": [],
        "historical_anchors_changed": False, "historical_dependency_arrays_changed": False,
        "non_executable": True, "semantic_closure": "OPEN", "execution_readiness": "BLOCKED",
        "real_profile": "DESIGN_ONLY / NOT EXECUTABLE",
        "readiness_code": "REAL_EXECUTION_PROFILE_NOT_READY", "execution_authorized": False,
        "real_snapshot_created": False, "admission_eligible": False, "source_body_retained": False,
        "source_policy_clearance": "not_granted",
        "permissions": {name: "NOT_ESTABLISHED" for name in
            ("private_retention", "redistribution", "free_service", "commercial_service", "ai_export")},
        "offline_reproduction": "NOT_FRESH_SOURCE_VERIFICATION",
        "future_milestone_authorized": False, "future_source_projection_authorized": False,
        "future_milestone_begun": False}
    return {**body, "package_id": "sha256:" + sha256_identity({"domain": PACKAGE_SCHEMA, "content": body})}


def write_package(root, records, *, review_root):
    """Reject invalid or foreign candidates before creating output directories."""
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
    root = _root(root)
    if {path.name for path in root.iterdir()} != RECORD_NAMES | {"manifest.json"}:
        _fail("EXTRA_OR_MISSING_PACKAGE_FILE")
    expected = rebuild_package(review_root=review_root)
    for name, value in {**expected, "manifest.json": manifest(expected)}.items():
        if _read(root / name) != _bytes(value):
            _fail("PACKAGE_CANONICAL_BYTES_DO_NOT_REPRODUCE")
    return expected


def verify_source(records, artifact_path, *, review_root):
    _validate_records(records)
    expected = build_package(artifact_path, review_root=review_root)
    if _canonical_candidate(records) != _bytes(expected):
        _fail("EXACT_SOURCE_REPRODUCTION_FAILED")
    return {"status": "VERIFIED_EXACT_SOURCE_BLOCKS", "selected_rule_count": 3,
        "new_source_units_projected": 3, "projection_id": records["projection.json"]["projection_id"],
        "source_body_retained": False}


def composite_view(records):
    metadata = manifest(records)
    view = _copy(records["composite-coverage.json"]["findings"])
    component = view["projection_components"][-1]
    if component.pop("package_binding", None) != "THIS_ENCLOSING_PACKAGE":
        _fail("SELF_PACKAGE_BINDING_REQUIRED")
    component["package_id"] = metadata["package_id"]
    return view
