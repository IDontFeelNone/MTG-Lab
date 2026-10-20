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
PINS_SHA256 = "b814f7a84bcc495dd1ddd315a67e75a01537a898393518d204d43d782cae0426"
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


def _review_binding_contracts():
    """Name only the 51 retained reviews used by this bounded design.

    Historical contracts own their schema and identity field. The two later
    report families use their explicit seal schemas. Neither enumeration scans
    a record for a plausible identity or inherits a selection from pins.json.
    """
    from gameplay_rules.projection import (
        bounded_casting_package, bounded_mana_package, dependency_package,
        object_control_package, zone_change_package, zone_change_dependency_package,
    )
    from gameplay_rules.mana_ability_design import package as mana_design_package
    from gameplay_rules.mana_dependency_design import package as direct_design_package

    contracts = {}
    groups = (
        ("gameplay-rules-bounded-casting-projection", bounded_casting_package,
         ("casting-readiness-reassessment.json", "casting-stage-matrix.json",
          "composite-coverage.json", "design-source-correspondence.json",
          "madness-readiness-reassessment.json"), "filename"),
        ("gameplay-rules-bounded-mana-ability-projection", bounded_mana_package,
         ("behavior-readiness.json", "classification-readiness.json",
          "composite-coverage.json", "consumer-reassessment.json",
          "design-source-correspondence.json", "family-closure-review.json",
          "overall-readiness.json"), "filename"),
        ("gameplay-rules-foundational-dependencies", dependency_package,
         ("closure-review.json", "composite-coverage.json",
          "execution-readiness-reassessment.json"), "top"),
        ("gameplay-rules-mana-ability-design", mana_design_package,
         ("classification-design.json", "consumer-bindings.json",
          "projection-frontier.json", "readiness.json"), "field"),
        ("gameplay-rules-mana-direct-dependency-design", direct_design_package,
         ("activated-procedure-design.json", "classification-dependencies.json",
          "consumer-bindings.json", "dependency-groups.json", "readiness.json",
          "stack-context-design.json", "triggered-procedure-design.json"), "field"),
        ("gameplay-rules-object-control-exceptions", object_control_package,
         ("composite-coverage.json", "control-readiness-reassessment.json",
          "family-closure-review.json", "source-anomaly.json"), "top"),
        ("gameplay-rules-zone-change-direct-dependencies", zone_change_dependency_package,
         ("closure-review.json", "composite-coverage.json",
          "zone-change-readiness-reassessment.json"), "top"),
        ("gameplay-rules-zone-change-exceptions", zone_change_package,
         ("composite-coverage.json", "family-closure-review.json",
          "zone-change-readiness-reassessment.json"), "top"),
    )
    for package_name, module, names, location in groups:
        for filename in names:
            contract = module.RECORD_TYPES[filename]
            field = contract.ID_FIELD
            if location == "filename":
                manifest_path = ("record_ids", filename)
            elif location == "field":
                manifest_path = ("record_ids", field)
            else:
                # This historical manifest names the anomaly with an alias.
                manifest_path = ("source_anomaly_id" if field == "anomaly_id" else field,)
            contracts[package_name + "/" + filename] = (
                contract.SCHEMA, field, module.PACKAGE_SCHEMA, manifest_path, contract)

    sealed_groups = (
        ("gameplay-rules-bounded-mana-classification-projection",
         "gameplay-bounded-mana-classification-package-v1",
         (("classification-dependency-review.json",
           "gameplay-bounded-mana-classification-classification-dependency-review-v1"),
          ("composite-coverage.json", "gameplay-bounded-mana-classification-composite-coverage-v1"),
          ("consumer-reassessment.json", "gameplay-bounded-mana-classification-consumer-reassessment-v1"),
          ("design-source-correspondence.json",
           "gameplay-bounded-mana-classification-design-source-correspondence-v1"),
          ("loyalty-readiness.json", "gameplay-bounded-mana-classification-loyalty-readiness-v1"),
          ("overall-readiness.json", "gameplay-bounded-mana-classification-overall-readiness-v1"),
          ("target-readiness.json", "gameplay-bounded-mana-classification-target-readiness-v1"))),
        ("gameplay-rules-bounded-mana-stack-exception-projection",
         "gameplay-bounded-mana-stack-exception-package-v1",
         (("composite-coverage.json", "gameplay-bounded-mana-stack-exception-composite-coverage-v1"),
          ("consumer-reassessment.json", "gameplay-bounded-mana-stack-exception-consumer-reassessment-v1"),
          ("design-source-correspondence.json",
           "gameplay-bounded-mana-stack-exception-design-source-correspondence-v1"),
          ("overall-readiness.json", "gameplay-bounded-mana-stack-exception-overall-readiness-v1"),
          ("parent-scope-review.json", "gameplay-bounded-mana-stack-exception-parent-scope-review-v1"),
          ("priority-readiness.json", "gameplay-bounded-mana-stack-exception-priority-readiness-v1"),
          ("section-dependency-review.json", "gameplay-bounded-mana-stack-exception-section-dependency-review-v1"),
          ("stack-exception-readiness.json", "gameplay-bounded-mana-stack-exception-stack-exception-readiness-v1"))),
    )
    for package_name, package_schema, schemas in sealed_groups:
        for filename, schema in schemas:
            contracts[package_name + "/" + filename] = (
                schema, "review_id", package_schema, ("record_ids", filename), None)
    return contracts


def _historical_json(path):
    """Load only canonical plain JSON from the existing safe bounded reader."""
    raw = _read(path)
    try:
        value = json.loads(raw)
        if type(value) is not dict or _canonical_candidate(value) != raw:
            _fail("HISTORICAL_REVIEW_CANONICAL_JSON_REQUIRED")
    except (GameplayContractError, ValueError, TypeError, UnicodeError, RecursionError):
        _fail("HISTORICAL_REVIEW_CANONICAL_JSON_REQUIRED")
    return value, raw


def validate_review_bindings(binding, *, review_root):
    """Verify each named selection against its own contract and parent manifest.

    Byte pins establish preservation, while these independent finite contracts
    establish provenance meaning. A foreign link remains invalid even if the
    proposed metadata is coherently rehashed. No caller-selected path is opened.
    """
    try:
        _canonical_candidate(binding)
        contracts = _review_binding_contracts()
        if (type(binding) is not dict or type(binding.get("review_bindings")) is not dict
                or set(binding["review_bindings"]) != set(contracts)
                or type(binding.get("prior_package_ids")) is not dict):
            _fail("MISSING_OR_UNSUPPORTED_REVIEW_BINDING_SELECTION")
        selections = binding["review_bindings"]
        if any(type(identity) is not str for identity in selections.values()):
            _fail("REVIEW_BINDING_IDENTITY_STRING_REQUIRED")
        if len(set(selections.values())) != len(contracts):
            _fail("AMBIGUOUS_REVIEW_BINDING_SELECTION")
        root = _root(review_root)
        manifests = {}
        for name, descriptor in contracts.items():
            schema, field, package_schema, manifest_path, contract = descriptor
            package_name, filename = name.split("/")
            package = _root(root / package_name)
            if package_name not in manifests:
                parent, _ = _historical_json(package / "manifest.json")
                if (type(parent.get("schema_version")) is not str
                        or parent["schema_version"] != package_schema
                        or type(parent.get("package_id")) is not str
                        or type(binding["prior_package_ids"].get(package_name)) is not str
                        or parent["package_id"] != binding["prior_package_ids"][package_name]):
                    _fail("REVIEW_PARENT_PACKAGE_BINDING_MISMATCH")
                content = {key: value for key, value in parent.items() if key != "package_id"}
                expected = "sha256:" + sha256_identity({
                    "domain": package_schema, "content": content})
                if parent["package_id"] != expected:
                    _fail("REVIEW_PARENT_PACKAGE_IDENTITY_INVALID")
                manifests[package_name] = parent
            parent = manifests[package_name]
            record, raw = _historical_json(package / filename)
            if (type(record.get("schema_version")) is not str
                    or record["schema_version"] != schema
                    or type(record.get(field)) is not str):
                _fail("UNSUPPORTED_OR_MISSING_REVIEW_OWN_IDENTITY")
            content = {key: value for key, value in record.items() if key != field}
            own_identity = "sha256:" + sha256_identity({"domain": schema, "content": content})
            if record[field] != own_identity or selections[name] != own_identity:
                _fail("REVIEW_BINDING_DOES_NOT_NAME_OWN_IDENTITY")
            if contract is not None:
                validated = contract.from_json(raw)
                if (validated.identity != own_identity
                        or (validated.serialize() + "\n").encode("utf-8") != raw):
                    _fail("HISTORICAL_REVIEW_CONTRACT_MISMATCH")
            declared = parent
            for key in manifest_path:
                if type(declared) is not dict or key not in declared:
                    _fail("MISSING_REVIEW_OWN_MANIFEST_BINDING")
                declared = declared[key]
            if type(declared) is not str or declared != own_identity:
                _fail("REVIEW_OWN_MANIFEST_BINDING_MISMATCH")
            files = parent.get("files")
            metadata = files.get(filename) if type(files) is dict else None
            if (type(metadata) is not dict or set(metadata) != {"bytes", "sha256"}
                    or type(metadata["bytes"]) is not int or metadata["bytes"] != len(raw)
                    or type(metadata["sha256"]) is not str
                    or metadata["sha256"] != hashlib.sha256(raw).hexdigest()):
                _fail("REVIEW_MANIFEST_CANONICAL_BYTES_MISMATCH")
        return _copy(selections)
    except GameplayContractError as error:
        if error.code == "activated_ability_design_package":
            raise
        _fail("INVALID_HISTORICAL_REVIEW_BINDING_CONTRACT")
    except (OSError, ValueError, TypeError, KeyError, AttributeError, UnicodeError, RecursionError):
        _fail("INVALID_HISTORICAL_REVIEW_BINDING_CONTRACT")


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
    binding = retained_binding()
    validate_review_bindings(binding, review_root=root)
    return binding


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
