"""Closed review-only casting-stage package validation and source reproduction.

This script owns no projected rule, source-anchor registration or runtime route.
Offline checks validate retained metadata; only verify_source reads the external
owner-controlled artifact. No official text or source path is returned.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
import hashlib
import json
import os
from pathlib import Path
import re

from evidence.contracts import sha256_identity
from gameplay_rules.errors import GameplayContractError
from gameplay_rules.activated_ability_design import package as historical_design
from gameplay_rules.activated_ability_projection import package as historical_projection
from gameplay_rules.activated_ability_projection.contracts import BoundedActivatedAbilityProjection
from gameplay_rules.projection.dependency_package import _read, _root
from gameplay_rules.projection.mana_stack_exception_package import _canonical_candidate
from gameplay_rules.projection.source import _verified_bytes
from gameplay_rules.projection.bounded_mana_source import _physical_lines
from gameplay_rules.projection.contracts import (
    ARTIFACT_HASH, ARTIFACT_BYTE_LENGTH, EFFECTIVE_DATE, VERIFICATION_RESULT_ID,
)

CANONICAL_MAIN = "8c2a79ecce9ae7e6ff8e7959c57271e02bf1a4cb"
PACKAGE_NAME = "gameplay-rules-shared-casting-stage-gap-design"
PACKAGE_SCHEMA = "gameplay-shared-casting-stage-gap-design-package-v1"
RECORD_DOMAIN = "gameplay-shared-casting-stage-gap-design-record-v1"
SOURCE_ENV = "MTGLAB_SHARED_CASTING_STAGE_SOURCE"
RECORD_NAMES = frozenset(("source-inspection.json", "gap-matrix.json",
    "consumer-dependencies.json", "scope-recommendation.json", "readiness.json"))
# Review-owned pins bind the exact authored records independently of their
# candidate manifests. A coherent rehash cannot replace the reviewed findings.
PINNED_RECORDS = {'consumer-dependencies.json': ('sha256:d6543775e61d816bc11434f608df7bf497420db49e40bbe1d8be38481d841265', '5cc131a601cfc9e9167c11364f16735e29b81918599c7700661fe8b57bf99c2f'), 'gap-matrix.json': ('sha256:cc01606c8b108280ca76dccb89ce700eea565a9091f9c900a368ec860dc3a457', '20b8cae5877b338ed638b93915ed069bf604c3b6a33a2c634e85bf7b5d6acf59'), 'readiness.json': ('sha256:f7f51e9b5d0103580f7530cdf8c6d5425496cbe6aba75f6cc343a3b1f803db69', '0872cad10dd587196a996294adf915e41a879d44e3e1725868dab2025053b997'), 'scope-recommendation.json': ('sha256:d07657a9b7d732ef6255d973d8e027687454d2e1e671f18dd113bad72662319b', '88cc523d505932ad5a107d34235018ba6b63313ebb1d519ff7b599735d52c938'), 'source-inspection.json': ('sha256:b238417023f10c4ebfd83340b6a105b95829c599126d5ab7bf52d941b8f23bc9', '4e6dfb070c85e300ae61010afca1578a6cee3a28933cc5ee1e95fcf2c3005a23')}
PR199_PACKAGE_ID = "sha256:cfe499b63d673af2337beac94134d30b1dac2a14097e244e79742670ed2ec1b1"
PR200_PACKAGE_ID = "sha256:02667e58da72701b7464275184de452a1ec53f34b7dedc80ca3cde8c595a7ff4"
PR200_PROJECTION_ID = "sha256:adaeae6e9da7956facbbe8db13c3f1a597328d184071bd6b6d61780c15957553"
REFERENCES = ("601.2c", "601.2d", "601.2e", "601.2i")
REVIEW_SPANS = (
    {"reference": "601.2c", "starting_physical_line": 2467, "ending_physical_line": 2468,
     "line_count": 2, "byte_start": 296470, "byte_end": 298440,
     "span_sha256": "sha256:6209ab42af52680707d5d42a8054e3b3681d050440ff8dc31f4cf86d0556a08e"},
    {"reference": "601.2d", "starting_physical_line": 2470, "ending_physical_line": 2470,
     "line_count": 1, "byte_start": 298444, "byte_end": 298686,
     "span_sha256": "sha256:6f9f37717e4f0594579bc0cf3fd938c7d56cc49deaa165c7c011400e46e38fbc"},
    {"reference": "601.2e", "starting_physical_line": 2472, "ending_physical_line": 2472,
     "line_count": 1, "byte_start": 298690, "byte_end": 298921,
     "span_sha256": "sha256:6b30c02c87f09a559eba9525cc331b65ddf668783d526e9f27f52a8447b11249"},
    {"reference": "601.2i", "starting_physical_line": 2481, "ending_physical_line": 2481,
     "line_count": 1, "byte_start": 300741, "byte_end": 301082,
     "span_sha256": "sha256:483c59e2092745af49cee6e5aa79339b165456084f22b33164dd4a24f6caa596"},
)
_BOUNDARIES = (("601.2d", 2470), ("601.2e", 2472), ("601.2f", 2474), ("601.3", 2483))
_CITATION = re.compile(rb"(?<![0-9A-Za-z.])([1-9][0-9]{2}(?:\.[0-9]+[a-z]?)?)(?![0-9A-Za-z]|\.[0-9A-Za-z])")


def _fail(message):
    raise GameplayContractError("shared_casting_stage_gap_design", message)


def _bytes(value):
    return _canonical_candidate(value)


def _identity(domain, content):
    return "sha256:" + sha256_identity({"domain": domain, "content": content})


def _unique(pairs):
    value = {}
    for key, item in pairs:
        if key in value:
            _fail("DUPLICATE_JSON_FIELD")
        value[key] = item
    return value


def _nonfinite(_value):
    _fail("NONFINITE_JSON_NUMBER")


def _document(path):
    try:
        raw = _read(path)
        value = json.loads(raw, object_pairs_hook=_unique, parse_constant=_nonfinite)
        if type(value) is not dict or _bytes(value) != raw:
            _fail("CANONICAL_PLAIN_JSON_REQUIRED")
        return value, raw
    except (OSError, TypeError, ValueError, UnicodeError, RecursionError):
        _fail("CANONICAL_PLAIN_JSON_REQUIRED")


def validate_records(records):
    """Validate own schemas/domains before fixed content and byte fingerprints."""
    _bytes(records)
    if type(records) is not dict or set(records) != RECORD_NAMES:
        _fail("EXACT_FIVE_REVIEW_RECORDS_REQUIRED")
    if set(PINNED_RECORDS) != RECORD_NAMES:
        _fail("REVIEW_RECORD_PINS_NOT_CONFIGURED")
    for name, record in records.items():
        if (type(record) is not dict or type(record.get("schema_version")) is not int
                or record["schema_version"] != 1 or type(record.get("review_id")) is not str
                or type(record.get("record_type")) is not str
                or record["record_type"] != name.removesuffix(".json")
                or type(record.get("findings")) is not dict):
            _fail("REVIEW_SCHEMA_OR_OWN_IDENTITY_INVALID")
        body = {key: value for key, value in record.items() if key != "review_id"}
        if record["review_id"] != _identity(RECORD_DOMAIN, body):
            _fail("REVIEW_OWN_IDENTITY_MISMATCH")
        expected_id, expected_sha256 = PINNED_RECORDS[name]
        if (record["review_id"] != expected_id
                or hashlib.sha256(_bytes(record)).hexdigest() != expected_sha256):
            _fail("EXACT_AUTHORED_REVIEW_CONTENT_REQUIRED")
    # The source reproduction result must bind the fingerprints actually named
    # by this package, not merely a parallel set of helper constants.
    source = records["source-inspection.json"]["findings"]
    spans = source.get("review_spans")
    if type(spans) is not list or len(spans) != 4:
        _fail("EXACT_FOUR_REVIEW_SPANS_REQUIRED")
    for candidate, expected, (boundary, terminal_line) in zip(spans, REVIEW_SPANS, _BOUNDARIES):
        if type(candidate) is not dict:
            _fail("REVIEW_SPAN_SCHEMA_INVALID")
        selected = {key: candidate.get(key) for key in expected}
        if _bytes(selected) != _bytes(expected):
            _fail("SOURCE_RECORD_REVIEW_FINGERPRINT_BINDING_MISMATCH")
        if (candidate.get("next_marker") != boundary
                or type(candidate.get("next_marker_physical_line")) is not int
                or candidate["next_marker_physical_line"] != terminal_line
                or candidate.get("next_body_inspected_as_boundary_context") is not False
                or candidate.get("registered_projected_source_anchor") is not False):
            _fail("SOURCE_RECORD_REVIEW_BOUNDARY_BINDING_MISMATCH")
    return deepcopy(records)


def _historical_envelope(root, name, module, expected_id):
    parent, raw = _document(root / name / "manifest.json")
    if (type(parent.get("schema_version")) is not str
            or parent["schema_version"] != module.PACKAGE_SCHEMA
            or type(parent.get("package_id")) is not str
            or parent["package_id"] != expected_id):
        _fail("HISTORICAL_PACKAGE_BINDING_MISMATCH")
    body = {key: value for key, value in parent.items() if key != "package_id"}
    if parent["package_id"] != _identity(module.PACKAGE_SCHEMA, body):
        _fail("HISTORICAL_PACKAGE_IDENTITY_MISMATCH")
    for filename in sorted(module.RECORD_NAMES):
        record, record_raw = _document(root / name / filename)
        if filename == "projection.json":
            domain, field = BoundedActivatedAbilityProjection.SCHEMA, "projection_id"
            BoundedActivatedAbilityProjection.from_dict(record)
        else:
            domain, field = module.RECORD_DOMAIN, "review_id"
            if (type(record.get("schema_version")) is not int or record["schema_version"] != 1):
                _fail("HISTORICAL_REVIEW_INTEGER_SCHEMA_REQUIRED")
        if type(record.get(field)) is not str:
            _fail("HISTORICAL_OWN_IDENTITY_FIELD_REQUIRED")
        own_body = {key: value for key, value in record.items() if key != field}
        own = _identity(domain, own_body)
        if record[field] != own:
            _fail("HISTORICAL_OWN_IDENTITY_MISMATCH")
        if type(parent.get("record_ids")) is not dict or type(parent["record_ids"].get(filename)) is not str or parent["record_ids"][filename] != own:
            _fail("HISTORICAL_OWN_MANIFEST_BINDING_MISMATCH")
        item = parent.get("files", {}).get(filename)
        expected = {"bytes": len(record_raw), "sha256": hashlib.sha256(record_raw).hexdigest()}
        if type(item) is not dict or _bytes(item) != _bytes(expected):
            _fail("HISTORICAL_CANONICAL_BYTE_BINDING_MISMATCH")
        if filename == "projection.json" and own != PR200_PROJECTION_ID:
            _fail("HISTORICAL_PROJECTION_IDENTITY_CHANGED")
    return parent



def _validate_additional_package_identities(root, binding):
    """Recompute six remaining own manifest identities using actual contracts.

    Each implementation below explicitly hashes its manifest body in its own
    PACKAGE_SCHEMA domain. Selecting that constant is deliberate, rather than
    trusting the schema_version or another identity found in candidate JSON.
    """
    from gameplay_rules.execution_design import package as execution_package
    from gameplay_rules.projection import package as foundation_package
    from gameplay_rules.casting_design import package as casting_design_package
    from gameplay_rules.source_evidence import review as source_review
    from gameplay_rules.source_evidence import closure as discovery_review
    from gameplay_rules.source_evidence import artifact_review
    contracts = (
        ("gameplay-rules-execution-profile-design", execution_package.PACKAGE_SCHEMA),
        ("gameplay-rules-foundational-projection", foundation_package.PACKAGE_SCHEMA),
        ("gameplay-rules-madness-casting-design", casting_design_package.PACKAGE_SCHEMA),
        ("gameplay-rules-source-versioning", source_review.PACKAGE_SCHEMA),
        ("gameplay-rules-release-discovery-closure", discovery_review.PACKAGE_SCHEMA),
        ("gameplay-rules-artifact-verification", artifact_review.PACKAGE_SCHEMA),
    )
    for name, domain in contracts:
        value, _ = _document(root / name / "manifest.json")
        body = {key: item for key, item in value.items() if key != "package_id"}
        expected = binding["prior_package_ids"][name]
        if (type(value.get("schema_version")) is not str or value["schema_version"] != domain
                or type(value.get("package_id")) is not str
                or value["package_id"] != _identity(domain, body)
                or value["package_id"] != expected):
            _fail("ADDITIONAL_HISTORICAL_PACKAGE_OWN_IDENTITY_INVALID")
        files = value.get("files")
        if type(files) is not dict:
            _fail("ADDITIONAL_HISTORICAL_MANIFEST_FILES_INVALID")
        for filename, metadata in files.items():
            raw = _read(root / name / filename)
            canonical_binding = {"bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}
            if type(metadata) is not dict or _bytes(metadata) != _bytes(canonical_binding):
                _fail("ADDITIONAL_HISTORICAL_CANONICAL_BYTE_BINDING_INVALID")

def validate_historical(*, review_root):
    """Validate exact retained bytes, schema-owned identities and manifest paths."""
    root = _root(review_root)
    # This verifies the 58 selected historical review identities using their
    # actual contracts and domains, plus all 115 pre-PR200 evidence bytes.
    binding = historical_projection.verify_prior_packages(root)
    _validate_additional_package_identities(root, binding)
    historical_design.load_package(root / historical_design.PACKAGE_NAME, review_root=root)
    historical_projection.load_package(root / historical_projection.PACKAGE_NAME, review_root=root)
    prior = _historical_envelope(root, historical_design.PACKAGE_NAME, historical_design, PR199_PACKAGE_ID)
    current = _historical_envelope(root, historical_projection.PACKAGE_NAME, historical_projection, PR200_PACKAGE_ID)
    if current["projection_id"] != PR200_PROJECTION_ID:
        _fail("HISTORICAL_PROJECTION_PACKAGE_BINDING_CHANGED")
    packages = deepcopy(binding["prior_package_ids"])
    packages[historical_projection.PACKAGE_NAME] = current["package_id"]
    if packages[historical_design.PACKAGE_NAME] != prior["package_id"]:
        _fail("HISTORICAL_DESIGN_PACKAGE_BINDING_CHANGED")
    return {"prior_package_ids": packages,
        "historical_acquisition_identity": binding["historical_acquisition_identity"],
        "artifact_verification_identity": binding["artifact_verification_identity"],
        "historical_review_binding_count": 58,
        "pr199_review_binding_count": 7, "pr200_review_binding_count": 9,
        "pr200_projection_identity": PR200_PROJECTION_ID,
        "pr200_historical_pins_identity": "sha256:" + historical_projection.PINS_SHA256}



def _validate_context_bindings(records, *, review_root):
    """Validate only the four projection families named by this design's rows.

    The two older seal implementations define literal domains; their schemas
    happen to equal those projection domains, which is checked explicitly here.
    No domain or own identity field is inferred from a foreign record.
    """
    from gameplay_rules.projection.bounded_casting_contracts import (
        BoundedCastingProjection, RULE_ID_DOMAIN as casting_rule_domain,
    )
    from gameplay_rules.activated_ability_projection.contracts import RULE_ID_DOMAIN as activation_rule_domain
    root = _root(review_root)
    binding = historical_projection.retained_binding()
    contracts = (
        ("gameplay-rules-bounded-casting-projection", BoundedCastingProjection.SCHEMA,
         "gameplay-cr-bounded-casting-projection-package-v1", casting_rule_domain, BoundedCastingProjection),
        ("gameplay-rules-bounded-mana-classification-projection", "gameplay-bounded-mana-classification-projection-v1",
         "gameplay-bounded-mana-classification-package-v1", "bounded-mana-classification-rule-v1", None),
        ("gameplay-rules-bounded-mana-stack-exception-projection", "gameplay-bounded-mana-stack-exception-projection-v1",
         "gameplay-bounded-mana-stack-exception-package-v1", "bounded-mana-stack-exception-rule-v1", None),
        (historical_projection.PACKAGE_NAME, BoundedActivatedAbilityProjection.SCHEMA,
         historical_projection.PACKAGE_SCHEMA, activation_rule_domain, BoundedActivatedAbilityProjection),
    )
    contexts = {}
    for name, domain, package_domain, rule_domain, contract in contracts:
        value, raw = _document(root / name / "projection.json")
        parent, _ = _document(root / name / "manifest.json")
        if contract is not None:
            contract.from_dict(value)
        own_body = {key: item for key, item in value.items() if key != "projection_id"}
        parent_body = {key: item for key, item in parent.items() if key != "package_id"}
        expected_package = PR200_PACKAGE_ID if name == historical_projection.PACKAGE_NAME else binding["prior_package_ids"][name]
        if (value.get("schema_version") != domain or type(value.get("projection_id")) is not str
                or value["projection_id"] != _identity(domain, own_body)
                or parent.get("schema_version") != package_domain
                or parent.get("package_id") != _identity(package_domain, parent_body)
                or parent["package_id"] != expected_package
                or (name != "gameplay-rules-bounded-casting-projection"
                    and parent.get("projection_id") != value["projection_id"])
                or parent.get("record_ids", {}).get("projection.json") != value["projection_id"]
                or _bytes(parent.get("files", {}).get("projection.json")) != _bytes({
                    "bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()})):
            _fail("RETAINED_CONTEXT_PROJECTION_OR_MANIFEST_IDENTITY_INVALID")
        rules = {}
        for rule in value["rules"]:
            body = {key: item for key, item in rule.items() if key != "rule_id"}
            if (type(rule.get("rule_id")) is not str
                    or rule["rule_id"] != _identity(rule_domain, body)
                    or rule["rule_reference"] in rules):
                _fail("RETAINED_CONTEXT_RULE_OWN_IDENTITY_INVALID")
            rules[rule["rule_reference"]] = rule["rule_id"]
        contexts[name] = {"package_id": parent["package_id"],
            "projection_id": value["projection_id"], "rules": rules}
    # These review-owned field shapes are finite; traversal only finds their
    # occurrences. The schema/identity contract map above never comes from data.
    def check(item):
        if type(item) is list:
            for child in item:
                check(child)
        elif type(item) is dict:
            name = item.get("retained_package")
            if name in contexts:
                context = contexts[name]
                for field in ("package_id", "projection_id"):
                    if field in item and _bytes(item[field]) != _bytes(context[field]):
                        _fail("RETAINED_CONTEXT_REFERENCE_BINDING_MISMATCH")
                if "rule_reference" in item and context["rules"].get(item["rule_reference"]) != item.get("rule_id"):
                    _fail("RETAINED_CONTEXT_RULE_REFERENCE_BINDING_MISMATCH")
                if "filename" in item:
                    record, _ = _document(root / name / item["filename"])
                    if item.get("review_id") != record.get("review_id"):
                        _fail("RETAINED_CONTEXT_REVIEW_REFERENCE_BINDING_MISMATCH")
                if "stage_matrix_id" in item:
                    matrix, _ = _document(root / name / "casting-stage-matrix.json")
                    if item["stage_matrix_id"] != matrix["review_id"]:
                        _fail("RETAINED_CASTING_STAGE_MATRIX_BINDING_MISMATCH")
            for child in item.values():
                check(child)
    check(records)

def manifest(records):
    """Bind fixed typed records; no projected source anchors are registered."""
    records = validate_records(records)
    body = {
        "schema_version": PACKAGE_SCHEMA, "canonical_base": CANONICAL_MAIN,
        "status": "REVIEW_ONLY_DESIGN", "review_only": True, "non_executable": True,
        "record_ids": {name: records[name]["review_id"] for name in sorted(records)},
        "files": {name: {"bytes": len(_bytes(value)), "sha256": hashlib.sha256(_bytes(value)).hexdigest()}
            for name, value in sorted(records.items())},
        "source_inspection_scope": list(REFERENCES),
        "source_inspection_metadata": "REVIEW_BYTE_SPANS_NOT_REGISTERED_PROJECTED_SOURCE_ANCHORS",
        "artifact_verification_identity": VERIFICATION_RESULT_ID,
        "prior_package_ids": {**historical_projection.retained_binding()["prior_package_ids"],
            historical_projection.PACKAGE_NAME: PR200_PACKAGE_ID},
        "historical_acquisition_identity": historical_projection.retained_binding()["historical_acquisition_identity"],
        "historical_pins_identity": "sha256:" + historical_projection.PINS_SHA256,
        "activated_ability_design_package_identity": PR199_PACKAGE_ID,
        "activated_ability_projection_package_identity": PR200_PACKAGE_ID,
        "activated_ability_projection_identity": PR200_PROJECTION_ID,
        "offline_validation": "NOT_FRESH_SOURCE_REPRODUCTION",
        "current_projection_allowlist": [], "new_source_units_projected": 0,
        "new_projected_rule_identities": 0, "new_registered_projected_source_anchors": 0,
        "projected_rule_count_before": 88, "projected_rule_count_after": 88,
        "existing_projection_count_before": 10, "existing_projection_count_after": 10,
        "source_coverage_graph_changed": False, "execution_readiness": "BLOCKED",
        "source_policy_clearance": "not_granted",
        "permissions": {name: "NOT_ESTABLISHED" for name in (
            "private_retention", "redistribution", "free_service", "commercial_service", "ai_export")},
        "future_milestone_authorized": False, "future_source_projection_authorized": False,
        "future_milestone_begun": False,
    }
    return {**body, "package_id": _identity(PACKAGE_SCHEMA, body)}


def load_package(root, *, review_root):
    """Offline exact canonical package verification, with no source-byte claim."""
    root = _root(root)
    if {path.name for path in root.iterdir()} != RECORD_NAMES | {"manifest.json"}:
        _fail("EXACT_REVIEW_PACKAGE_FILE_SET_REQUIRED")
    records = {name: _document(root / name)[0] for name in sorted(RECORD_NAMES)}
    validate_records(records)
    candidate, raw = _document(root / "manifest.json")
    if raw != _bytes(manifest(records)):
        _fail("MANIFEST_CANONICAL_CONTENT_MISMATCH")
    validate_historical(review_root=review_root)
    _validate_context_bindings(records, review_root=review_root)
    return records


def write_package(root, records, *, review_root):
    """Validate all boundaries before creating any output directory or file."""
    records = validate_records(records)
    validate_historical(review_root=review_root)
    _validate_context_bindings(records, review_root=review_root)
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


def verify_source(records, artifact_path, *, review_root):
    """Reproduce only four review fingerprints using original artifact bytes."""
    validate_records(records)
    validate_historical(review_root=review_root)
    _validate_context_bindings(records, review_root=review_root)
    root = Path(review_root)
    try:
        data = _verified_bytes(artifact_path,
            artifact_review_root=root / "gameplay-rules-artifact-verification",
            source_root=root / "gameplay-rules-source-versioning",
            discovery_root=root / "gameplay-rules-release-discovery-closure")
    except (OSError, TypeError, ValueError, GameplayContractError):
        _fail("SOURCE_ARTIFACT_OR_VERIFICATION_LINEAGE_INVALID")
    lines = _physical_lines(data)
    observed = []
    for expected, (next_reference, terminal_line) in zip(REVIEW_SPANS, _BOUNDARIES):
        first = expected["starting_physical_line"] - 1
        last = expected["ending_physical_line"] - 1
        marker = expected["reference"].encode("ascii") + b" "
        terminal_marker = next_reference.encode("ascii") + (b". " if next_reference[-1].isdigit() else b" ")
        if (not lines[first][1].startswith(marker)
                or not lines[terminal_line - 1][1].startswith(terminal_marker)
                or terminal_line - 1 != last + 2 or lines[last + 1][1] != b"\xc2\xa0"):
            _fail("SHARED_CASTING_STAGE_SCOPE_INSUFFICIENT")
        if last > first and (last != first + 1 or not lines[last][1].startswith(b"Example: ")):
            _fail("SHARED_CASTING_STAGE_SCOPE_INSUFFICIENT")
        start = lines[first][0]
        end = lines[last][0] + len(lines[last][1])
        block = data[start:end]
        row = {"reference": expected["reference"],
            "starting_physical_line": first + 1, "ending_physical_line": last + 1,
            "line_count": last - first + 1, "byte_start": start, "byte_end": end,
            "span_sha256": "sha256:" + hashlib.sha256(block).hexdigest()}
        if _bytes(row) != _bytes(expected):
            _fail("REVIEW_ONLY_SOURCE_SPAN_MISMATCH")
        body = block[len(marker):]
        citations = tuple(match.group(1).decode("ascii") for match in _CITATION.finditer(body))
        if citations != {"601.2c": (), "601.2d": (), "601.2e": ("733",), "601.2i": ("601.2a",)}[expected["reference"]]:
            _fail("REVIEW_ONLY_REFERENCE_OBSERVATION_MISMATCH")
        if expected["reference"] == "601.2i" and body.count(b"601.2a\xe2\x80\x93h") != 1:
            _fail("REVIEW_ONLY_RANGE_OBSERVATION_MISMATCH")
        observed.append(row)
    return {"status": "VERIFIED_EXACT_FOUR_REVIEW_FINGERPRINTS",
        "authority": "NEWLY_VERIFIED_REVIEW_ONLY_SOURCE_OBSERVATIONS",
        "artifact_hash": ARTIFACT_HASH, "byte_length": ARTIFACT_BYTE_LENGTH,
        "effective_date": EFFECTIVE_DATE, "artifact_verification_identity": VERIFICATION_RESULT_ID,
        "review_spans": observed, "source_body_retained": False,
        "new_source_units_projected": 0, "registered_projected_source_anchors_added": 0,
        "execution_readiness": "BLOCKED"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("validate", "verify-source"))
    parser.add_argument("--review-root", type=Path, default=Path("reference-reviews"))
    parser.add_argument("--package", type=Path)
    args = parser.parse_args()
    package = args.package or args.review_root / PACKAGE_NAME
    try:
        records = load_package(package, review_root=args.review_root)
        result = {"status": "VALID_OFFLINE_METADATA_NOT_FRESH_SOURCE_REPRODUCTION",
            "package_id": manifest(records)["package_id"]}
        if args.command == "verify-source":
            selector = os.environ.get(SOURCE_ENV)
            if selector is None:
                result["source_reproduction"] = "SKIPPED_SOURCE_SELECTOR_UNCONFIGURED"
            else:
                result["source_reproduction"] = verify_source(records, selector, review_root=args.review_root)
        print(json.dumps(result, sort_keys=True, separators=(",", ":")))
    except (GameplayContractError, OSError, TypeError, ValueError):
        parser.exit(1, "shared casting-stage gap review validation failed\n")


if __name__ == "__main__":
    main()
