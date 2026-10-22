"""Finite implementation successors; historical fixture bytes remain authoritative.

The ledger comes from the exact canonical Git base. Current implementation
checks accept only the explicitly pinned successor; historical fixture checks
retain their original rows, counts and digests. This helper grants no gameplay,
source, admission or publication authority.
"""
import hashlib
import json
from pathlib import Path, PurePosixPath
import stat

ROOT = Path(__file__).resolve().parents[1]
BASE = "bdccc4e9be2f6ff2aec7b5764baa022e15f51cfe"
TREE = "6afe49701cd99b7b6f124a979fbe332c91bb4c71"
LEDGER_PATH = "tests/validation_performance_implementation_changes.json"
LEDGER_SHA256 = "89fd37eb6f94182a118420ecdc8ed4aa52fd66d3f83c75fa1abb2a2c2e167322"
NEW_SOURCE_PATHS = frozenset({"src/gameplay_rules/retained_stage_validation.py"})
NEW_TOOL_PATHS = frozenset({"scripts/profile_validation_capacity.py"})
REPLACEMENT_PATHS = frozenset({
    "src/gameplay_rules/shared_target_declaration/package.py",
    "src/gameplay_rules/shared_target_allocation/package.py",
    "src/gameplay_rules/shared_proposal_legality/package.py",
})


def regular_bytes(relative, root=ROOT):
    """Read an exact repository member without following a symlink boundary."""
    if (type(relative) is not str or not relative
            or PurePosixPath(relative).is_absolute()
            or any(part in ("", ".", "..") for part in relative.split("/"))):
        raise AssertionError("Canonical relative repository path required")
    root = Path(root).absolute()
    path = root / relative
    for ancestor in (path, *path.parents):
        if ancestor.is_symlink():
            raise AssertionError("Protected repository member must not cross a symlink")
        if ancestor == root:
            break
    try:
        if not stat.S_ISREG(path.stat(follow_symlinks=False).st_mode):
            raise AssertionError("Protected repository member must be a regular file")
        return path.read_bytes()
    except OSError as exc:
        raise AssertionError("Protected repository member is unavailable") from exc


def ledger():
    """Check the ledger's exact bytes separately from historical fixtures."""
    raw = regular_bytes(LEDGER_PATH)
    if hashlib.sha256(raw).hexdigest() != LEDGER_SHA256:
        raise AssertionError("Finite authorized implementation ledger changed")
    value = json.loads(raw)
    if (value["canonical_base"] != BASE or value["canonical_tree"] != TREE
            or value["purpose"] != "FINITE_AUTHORIZED_IMPLEMENTATION_SUCCESSORS_ONLY"
            or {row["path"] for row in value["replacements"]} != REPLACEMENT_PATHS
            or len(value["replacements"]) != len(REPLACEMENT_PATHS)
            or {row["path"] for row in value["additions"]} != NEW_SOURCE_PATHS | NEW_TOOL_PATHS
            or len(value["additions"]) != len(NEW_SOURCE_PATHS | NEW_TOOL_PATHS)):
        raise AssertionError("Exact bounded implementation ledger required")
    return value


def _check_pin(raw, pin):
    if (type(pin["bytes"]) is not int or len(raw) != pin["bytes"]
            or hashlib.sha256(raw).hexdigest() != pin["sha256"]):
        raise AssertionError("Protected canonical bytes do not match their explicit pin")


def assert_original_git_blob(raw, pin):
    """Reproduce an original entry from Git bytes during base reconciliation.

    Ordinary shallow/disposable validation uses the immutable ledger and fixture
    rows; this explicit check additionally reproduces the original Git object.
    """
    if type(raw) is not bytes:
        raise AssertionError("Original Git blob bytes required")
    _check_pin(raw, pin)
    git_identity = hashlib.sha1(b"blob " + str(len(raw)).encode("ascii") + b"\0" + raw).hexdigest()
    if git_identity != pin["git_blob"]:
        raise AssertionError("Original canonical Git blob identity does not reproduce")


def assert_retained_row(row, root=ROOT):
    """Require the exact historical row, then its one authorized current pin.

    Unrelated rows continue requiring their original bytes. The current check
    never accepts an old implementation merely because it was once canonical.
    """
    if type(row) is not dict or set(row) != {"path", "bytes", "sha256"}:
        raise AssertionError("Original historical path/hash/length row required")
    replacements = {item["path"]: item for item in ledger()["replacements"]}
    pin = row
    if row["path"] in replacements:
        item = replacements[row["path"]]
        original = item["original"]
        if row != {"path": item["path"], "bytes": original["bytes"], "sha256": original["sha256"]}:
            raise AssertionError("Historical row must match the exact authorized original")
        pin = item["replacement"]
    _check_pin(regular_bytes(row["path"], root), pin)


def assert_current_implementation(root=ROOT):
    """Check every successor and exact added implementation/tool independently."""
    value = ledger()
    for row in value["replacements"]:
        _check_pin(regular_bytes(row["path"], root), row["replacement"])
    for row in value["additions"]:
        _check_pin(regular_bytes(row["path"], root), row)
    for name, pin in value["document_appendices"].items():
        raw = regular_bytes(name, root)
        if len(raw) != pin["baseline_bytes"] + pin["appendix_bytes"]:
            raise AssertionError("Exact current operational appendix required")
        historical_document_before_validation_performance_append(name, raw)


def is_validation_performance_addition(path, root=ROOT):
    """Select only the named helper/tool; neighboring additions stay visible."""
    return path.relative_to(root).as_posix() in NEW_SOURCE_PATHS | NEW_TOOL_PATHS


def historical_document_before_validation_performance_append(name, raw):
    """Verify all inherited bytes and remove only this exact operational suffix."""
    documents = ledger()["document_appendices"]
    if type(name) is not str or name not in documents or type(raw) is not bytes:
        raise AssertionError("Named canonical operational document bytes required")
    pin = documents[name]
    length = pin["baseline_bytes"]
    if len(raw) not in (length, length + pin["appendix_bytes"]):
        raise AssertionError("Only the exact validation-performance appendix is permitted")
    baseline, appendix = raw[:length], raw[length:]
    _check_pin(baseline, {"bytes": length, "sha256": pin["baseline_sha256"]})
    if appendix:
        _check_pin(appendix, {"bytes": pin["appendix_bytes"], "sha256": pin["appendix_sha256"]})
    return baseline
