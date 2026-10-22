"""Fresh fixed-manifest checks shared by the bounded casting-stage packages.

Only immutable identity contracts are reusable. Every call reads the actual
selected files; this module caches no successful validation or candidate data.
"""
from __future__ import annotations

import hashlib
import json

from evidence.contracts import sha256_identity
from gameplay_rules.errors import GameplayContractError
from gameplay_rules.projection.dependency_package import _read, _root
from gameplay_rules.projection.mana_stack_exception_package import _canonical_candidate


def _fail(message):
    raise GameplayContractError("retained_stage_package", message)


def _bytes(value):
    return _canonical_candidate(value)


def _identity(domain, content):
    return "sha256:" + sha256_identity({"domain": domain, "content": content})


def _canonical_record(path):
    raw = _read(path)
    value = json.loads(raw)
    if type(value) is not dict or _bytes(value) != raw:
        _fail("RETAINED_CANONICAL_RECORD_BYTES_REQUIRED")
    return value, raw


def _validate_retained_stage(root, *, name, package_schema, package_id, record_domain,
                        record_names, projection_type):
    """Check actual bytes against a fixed manifest identity and own contracts.

    The fixed package identity binds the exact canonical manifest, including all
    record identities, byte lengths and hashes. Checking those bindings freshly
    preserves exact historical content without regenerating authored findings.
    """
    directory = _root(root / name)
    if {path.name for path in directory.iterdir()} != set(record_names) | {"manifest.json"}:
        _fail("RETAINED_SUCCESSOR_FILE_SET_CHANGED")
    parent, _ = _canonical_record(directory / "manifest.json")
    body = {key: value for key, value in parent.items() if key != "package_id"}
    if (type(parent.get("schema_version")) is not str
            or parent["schema_version"] != package_schema
            or type(parent.get("package_id")) is not str
            or parent["package_id"] != package_id
            or parent["package_id"] != _identity(package_schema, body)):
        _fail("RETAINED_SUCCESSOR_PACKAGE_OWN_IDENTITY_INVALID")
    if (type(parent.get("files")) is not dict or set(parent["files"]) != set(record_names)
            or type(parent.get("record_ids")) is not dict
            or set(parent["record_ids"]) != set(record_names)):
        _fail("RETAINED_SUCCESSOR_MANIFEST_BINDINGS_INVALID")
    records = {}
    for filename in sorted(record_names):
        record, raw = _canonical_record(directory / filename)
        expected_file = {"bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}
        if _bytes(parent["files"][filename]) != _bytes(expected_file):
            _fail("RETAINED_SUCCESSOR_CANONICAL_FILE_BINDING_INVALID")
        projected = filename == "projection.json"
        identity_field = "projection_id" if projected else "review_id"
        domain = projection_type.SCHEMA if projected else record_domain
        schema = record.get("schema_version")
        schema_valid = (type(schema) is str and schema == domain if projected else
            type(schema) is int and schema == 1)
        own_body = {key: value for key, value in record.items() if key != identity_field}
        if (not schema_valid or type(record.get(identity_field)) is not str
                or record[identity_field] != _identity(domain, own_body)
                or type(parent["record_ids"][filename]) is not str
                or parent["record_ids"][filename] != record[identity_field]):
            _fail("RETAINED_SUCCESSOR_RECORD_OWN_IDENTITY_OR_DOMAIN_INVALID")
        if projected:
            projection_type.from_dict(record)
        records[filename] = record
    return {"manifest": parent, "records": records}



def validate_retained_stage(root, **contract):
    """Read a stage with explicit own-domain, schema and fixed manifest pins."""
    try:
        return _validate_retained_stage(root, **contract)
    except GameplayContractError:
        raise
    except (OSError, ValueError, TypeError, KeyError, AttributeError, UnicodeError, RecursionError):
        _fail("RETAINED_HISTORICAL_CONTRACT_INVALID")
