"""Finite current implementation successors, separate from historical evidence.

Historical fixtures and gameplay source verifiers keep their original contracts.
Only the exact two authorized original rows select this milestone's successors;
unrelated rows retain their original checks, including PR #205's finite ledger.
"""
import hashlib
import json
from pathlib import Path

import validation_performance_preservation as previous

ROOT = Path(__file__).resolve().parents[1]
BASE = "f66c912a2fbffe80c4c60241e555dfeeb4ba0c36"
TREE = "d98d291da9a542f0396ce399043279fed88ec20d"
LEDGER_PATH = "tests/query_attachment_performance_implementation_changes.json"
LEDGER_SHA256 = "f4abaced652f79acf737813ffdb6a6ce34f5b3d930f973f8c02a39d42a5acc40"
REPLACEMENT_PATHS = frozenset({
    "src/query/engine.py", "src/repository/legacy_profile.py",
})
NEW_SOURCE_PATHS = frozenset()
NEW_TOOL_PATHS = frozenset({"scripts/measure_query_attachment_performance.py"})

regular_bytes = previous.regular_bytes
assert_original_git_blob = previous.assert_original_git_blob


def _check_pin(raw, pin):
    if (type(raw) is not bytes or type(pin) is not dict
            or type(pin.get("bytes")) is not int
            or len(raw) != pin["bytes"]
            or hashlib.sha256(raw).hexdigest() != pin.get("sha256")):
        raise AssertionError("Current bytes do not match the exact authorized pin")


def ledger():
    raw = regular_bytes(LEDGER_PATH)
    if hashlib.sha256(raw).hexdigest() != LEDGER_SHA256:
        raise AssertionError("Finite query/attachment implementation ledger changed")
    value = json.loads(raw)
    if (value["canonical_base"] != BASE or value["canonical_tree"] != TREE
            or value["purpose"] != "FINITE_AUTHORIZED_IMPLEMENTATION_SUCCESSORS_ONLY"
            or {item["path"] for item in value["replacements"]} != REPLACEMENT_PATHS
            or len(value["replacements"]) != len(REPLACEMENT_PATHS)
            or {item["path"] for item in value["additions"]} != NEW_SOURCE_PATHS | NEW_TOOL_PATHS
            or len(value["additions"]) != len(NEW_SOURCE_PATHS | NEW_TOOL_PATHS)):
        raise AssertionError("Exact bounded query/attachment implementation ledger required")
    return value


def _replacement(row):
    item = next((item for item in ledger()["replacements"]
                 if item["path"] == row["path"]), None)
    if item is None:
        return None
    original = {"path": item["path"], "sha256": item["original"]["sha256"]}
    if "bytes" in row:
        original["bytes"] = item["original"]["bytes"]
    if row != original:
        raise AssertionError("Historical row must match the exact authorized original")
    return item["replacement"]


def assert_hash_row(row, root=ROOT):
    """Explicit adapter for historical path/hash rows and hash-map entries."""
    if (type(row) is not dict or set(row) != {"path", "sha256"}
            or type(row["path"]) is not str or type(row["sha256"]) is not str):
        raise AssertionError("Exact historical path/hash row schema required")
    pin = _replacement(row)
    raw = regular_bytes(row["path"], root)
    if pin is not None:
        _check_pin(raw, pin)
    elif hashlib.sha256(raw).hexdigest() != row["sha256"]:
        raise AssertionError("Unrelated historical file bytes changed")


def assert_retained_row(row, root=ROOT):
    """Explicit adapter for historical path/hash/length rows; no coercion."""
    if (type(row) is not dict or set(row) != {"path", "bytes", "sha256"}
            or type(row["path"]) is not str or type(row["sha256"]) is not str
            or type(row["bytes"]) is not int):
        raise AssertionError("Exact historical path/hash/length row schema required")
    pin = _replacement(row)
    if pin is None:
        previous.assert_retained_row(row, root)
    else:
        _check_pin(regular_bytes(row["path"], root), pin)


def assert_current_implementation(root=ROOT):
    """Require current replacements, exact additions and retained evidence bytes."""
    value = ledger()
    for item in value["replacements"]:
        _check_pin(regular_bytes(item["path"], root), item["replacement"])
    for row in value["additions"]:
        _check_pin(regular_bytes(row["path"], root), row)
    for row in [value["prior_implementation_ledger"], *value["historical_fixtures"]]:
        _check_pin(regular_bytes(row["path"], root), row)


def is_query_attachment_performance_addition(path, root=ROOT):
    """Only individually enumerated additions are removed from historical views."""
    return path.relative_to(root).as_posix() in NEW_SOURCE_PATHS | NEW_TOOL_PATHS


def assert_authorized_addition(path, root=ROOT):
    """Require actual pinned bytes before omitting a named new tool from history."""
    name = path.relative_to(root).as_posix()
    if name not in NEW_SOURCE_PATHS | NEW_TOOL_PATHS:
        raise AssertionError("Only the exact authorized addition may be adapted")
    item = next(item for item in ledger()["additions"] if item["path"] == name)
    _check_pin(regular_bytes(name, root), item)


def historical_inventory_row(row, root=ROOT):
    """Adapt one actual current inventory row after checking its exact successor.

    The original aggregate inventory digest remains unchanged. A source row is
    replaced by its exact ledger original only after both the supplied current
    row and actual disk bytes match the one authorized replacement.
    """
    if (type(row) is not dict or set(row) != {"path", "bytes", "sha256"}
            or type(row["path"]) is not str or type(row["sha256"]) is not str
            or type(row["bytes"]) is not int):
        raise AssertionError("Exact current path/hash/length row schema required")
    item = next((item for item in ledger()["replacements"]
                 if item["path"] == row["path"]), None)
    if item is None:
        return row
    if row != {"path": item["path"], **item["replacement"]}:
        raise AssertionError("Current inventory row must match the exact authorized replacement")
    original = {"path": item["path"], "bytes": item["original"]["bytes"],
                "sha256": item["original"]["sha256"]}
    assert_retained_row(original, root)
    return original
