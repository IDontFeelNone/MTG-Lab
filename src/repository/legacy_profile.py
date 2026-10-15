"""Explicit, in-place, non-production Tier A compatibility attachment.

Control metadata binds existing bytes, not permission or admission authority.
No acquisition, copying, writer, activation or fallback is provided here.
"""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
import hashlib
import json
import math
import os
from pathlib import Path
import re
import stat

from repository.snapshots import SnapshotError, _directory, _relative, canonical_json

PROFILE = "legacy-public-compatibility-v1"
TIER = "CATALOG_QUERY_COLLECTION"
PRECEDENCE = "typed-first-exact-entity-type-id"
OPERATIONS = ("LOCAL_PRIVATE_PROCESSING", "PRIVATE_OPERATOR_RETENTION",
              "EXISTING_PUBLIC_GIT_COMPATIBILITY", "NEW_PUBLIC_REPOSITORY_REDISTRIBUTION",
              "FREE_PUBLIC_APPLICATION_SERVICE", "COMMERCIAL_OR_PAID_SERVICE", "AI_OR_MODEL_EXPORT")
AUTHORITY = {"production_eligible": False, "approval_state": "not_granted",
             "source_policy_clearance": "not_granted", "data_processing_permission_established": False}
CAPABILITIES = {"catalog_query_collection": "available", "full_query_audit": "unsupported",
                "historical_admission_replay": "unsupported", "gameplay_rules": "unsupported",
                "mechanical_evidence": "outside_tier_a", "product_collation": "unsupported"}
PATTERNS = ("game.json", "cards/*/card.json", "printings/*/printing.json", "products/*/product.json",
            "identifiers/*.json", "identifiers/**/*.json", "finishes/*.json", "treatments/*.json", "rarities/*.json",
            "product_versions/**/*.json", "packs/**/*.json", "slots/**/*.json", "sheets/*.json",
            "print_sheets/**/*.json", "sources/*.json")
PLACEMENTS = {"CORE_CATALOG_CONTENT", "SOURCE_EVIDENCE_REFERENCE", "AUDIT_CONTEXT"}
_SHA = re.compile(r"^sha256:[0-9a-f]{64}$")
_HEX = re.compile(r"^[0-9a-f]{64}$")
_ID = re.compile(r"^[a-z0-9][a-z0-9._-]*$")
MAX_BYTES = 32 * 1024 * 1024


def identity(domain, value):
    return "sha256:" + hashlib.sha256(canonical_json({"domain": "mtg-lab:" + PROFILE + ":" + domain,
                                                      "value": value})).hexdigest()


def profile_identity(document):
    return identity("control", {k: v for k, v in document.items() if k != "profile_id"})


def closure_identity(files):
    return identity("closure", files)


def namespace_patterns(game):
    return tuple("data/canonical/games/" + game + "/" + pattern for pattern in PATTERNS)


def strict_json(raw, name):
    def pairs(values):
        out = {}
        for key, value in values:
            if key in out:
                raise ValueError("duplicate key")
            out[key] = value
        return out
    def constant(value):
        raise ValueError("nonfinite number")
    def number(value):
        parsed = float(value)
        if not math.isfinite(parsed):
            raise ValueError("nonfinite number")
        return parsed
    try:
        value = json.loads(raw, object_pairs_hook=pairs, parse_constant=constant, parse_float=number)
        if not isinstance(value, dict):
            raise ValueError("object required")
        return value
    except (ValueError, UnicodeError, RecursionError):
        raise SnapshotError("invalid compatibility JSON", code="invalid_json", relative_path=name) from None


def _path(root, name):
    _relative(name)
    path = root / name
    if any(p.is_symlink() for p in (path, *path.parents)):
        raise SnapshotError("selected path contains a symlink", code="symlink", relative_path=name)
    return path


def _read(root, name):
    path = _path(root, name)
    try:
        descriptor = os.open(path, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0))
        with os.fdopen(descriptor, "rb") as stream:
            before = os.fstat(stream.fileno())
            if not stat.S_ISREG(before.st_mode) or before.st_size > MAX_BYTES:
                raise SnapshotError("unsupported selected file", code="unsafe_file", relative_path=name)
            raw = stream.read(MAX_BYTES + 1)
            after = os.fstat(stream.fileno())
        if len(raw) != before.st_size or (before.st_mtime_ns, before.st_size) != (after.st_mtime_ns, after.st_size):
            raise SnapshotError("selected file changed while reading", code="integrity_mismatch", relative_path=name)
        return raw
    except FileNotFoundError:
        raise SnapshotError("selected file is missing", code="missing_file", relative_path=name) from None
    except OSError:
        raise SnapshotError("selected file could not be read", code="filesystem_error", relative_path=name) from None


def _validate_control_fields(doc, game, expected):
    keys = {"profile", "contract_version", "game", "capability_tier", "data_root", "games_root", "profile_id",
            "closure_id", "files", "namespaces", "game_namespaces", "absent", "query_snapshot_id", "entity_counts",
            "precedence", "capabilities", "permissions", "incompleteness", "historical_prestate_reference", *AUTHORITY}
    if set(doc) != keys:
        raise SnapshotError("unsupported compatibility metadata", code="invalid_manifest")
    if doc["profile"] != PROFILE or doc["contract_version"] != "v1":
        raise SnapshotError("unsupported compatibility profile", code="unsupported_version")
    if doc["game"] != game:
        raise SnapshotError("compatibility game mismatch", code="wrong_game")
    if (doc["capability_tier"] != TIER or doc["precedence"] != PRECEDENCE or doc["capabilities"] != CAPABILITIES
            or any(doc[k] != v or type(doc[k]) != type(v) for k, v in AUTHORITY.items())
            or doc["permissions"] != dict.fromkeys(OPERATIONS, "NOT_ESTABLISHED")):
        raise SnapshotError("unsupported compatibility scope or authority", code="unsupported_capability")
    if doc["data_root"] != "data" or doc["games_root"] != "data/canonical/games" or doc["game_namespaces"] != [game]:
        raise SnapshotError("unsupported compatibility roots", code="scope_mismatch")
    if not _SHA.fullmatch(str(expected)) or doc["profile_id"] != expected or profile_identity(doc) != expected:
        raise SnapshotError("compatibility profile identity mismatch", code="identity_mismatch")
    if not _SHA.fullmatch(str(doc["query_snapshot_id"])):
        raise SnapshotError("invalid expected query identity", code="invalid_manifest")
    if not isinstance(doc["entity_counts"], dict) or not doc["entity_counts"] or any(
            not isinstance(k, str) or type(v) is not int or v < 0 for k, v in doc["entity_counts"].items()):
        raise SnapshotError("invalid entity census", code="invalid_manifest")
    incomplete = doc["incompleteness"]
    expected_states = {"typed_materialization": "incomplete", "gameplay_rules": "unsupported",
                       "optional_knowledge_state": "absent", "product_collation": "unsupported",
                       "mechanical_evidence": "outside_tier_a"}
    if (not isinstance(incomplete, dict) or set(incomplete) != {*expected_states, "product_slots", "finish_references"}
            or any(incomplete[k] != v for k, v in expected_states.items())
            or type(incomplete["product_slots"]) is not int or incomplete["product_slots"] != 0):
        raise SnapshotError("unsupported completeness claims", code="invalid_manifest")
    finishes = incomplete["finish_references"]
    if (not isinstance(finishes, dict) or set(finishes) != {"status", "unresolved_by_identifier"}
            or finishes["status"] != "incomplete"
            or not isinstance(finishes["unresolved_by_identifier"], dict)
            or any(not _ID.fullmatch(k) or type(v) is not int or v < 0
                   for k, v in finishes["unresolved_by_identifier"].items())):
        raise SnapshotError("invalid Finish incompleteness", code="invalid_manifest")
    historical = doc["historical_prestate_reference"]
    if not isinstance(historical, str) or not _HEX.fullmatch(historical):
        raise SnapshotError("invalid informational prestate reference", code="invalid_manifest")
    files = doc["files"]
    if not isinstance(files, list) or not 1 <= len(files) <= 256:
        raise SnapshotError("invalid compatibility inventory", code="invalid_manifest")
    prefix = "data/canonical/games/" + game + "/"
    for row in files:
        if not isinstance(row, dict) or set(row) != {"path", "sha256", "byte_length", "placement"}:
            raise SnapshotError("invalid dependency binding", code="invalid_manifest")
        name = row["path"]
        _relative(name)
        if (row["placement"] not in PLACEMENTS or not _HEX.fullmatch(str(row["sha256"]))
                or type(row["byte_length"]) is not int or not 0 <= row["byte_length"] <= MAX_BYTES):
            raise SnapshotError("invalid dependency binding", code="invalid_manifest")
        placement = "AUDIT_CONTEXT" if name.startswith("data/audit/") and name.endswith(".json") else (
            "SOURCE_EVIDENCE_REFERENCE" if name.startswith(prefix + "sources/") else "CORE_CATALOG_CONTENT")
        if (placement == "SOURCE_EVIDENCE_REFERENCE" and not _matches(name, prefix + "sources/*.json")) or row["placement"] != placement or (placement == "CORE_CATALOG_CONTENT" and
                name != "data/canonical/state.json" and not any(_matches(name, pattern) for pattern in namespace_patterns(game)[:-1])):
            raise SnapshotError("dependency outside Tier A", code="scope_mismatch", relative_path=name)
    if sum(row["placement"] == "AUDIT_CONTEXT" for row in files) != 2:
        raise SnapshotError("Tier A requires exactly two selected audit contexts", code="scope_mismatch")
    paths = [r["path"] for r in files]
    if not {"data/canonical/state.json", prefix + "game.json"} <= set(paths):
        raise SnapshotError("required mixed representation missing", code="scope_mismatch")
    if paths != sorted(paths) or len(set(p.casefold() for p in paths)) != len(paths):
        raise SnapshotError("duplicate or unordered selected paths", code="duplicate_path")
    if doc["closure_id"] != closure_identity(files):
        raise SnapshotError("closure identity mismatch", code="identity_mismatch")
    if doc["absent"] != ["data/canonical/knowledge/state.json"]:
        raise SnapshotError("optional knowledge absence must be bound", code="scope_mismatch")
    namespaces = doc["namespaces"]
    if not isinstance(namespaces, list) or [n.get("pattern") for n in namespaces] != list(namespace_patterns(game)):
        raise SnapshotError("reader namespaces must be fully bound", code="scope_mismatch")
    for entry in namespaces:
        if set(entry) != {"pattern", "paths"} or not isinstance(entry["paths"], list):
            raise SnapshotError("invalid namespace inventory", code="invalid_manifest")
        for name in entry["paths"]:
            _relative(name)
            if not _matches(name, entry["pattern"]):
                raise SnapshotError("namespace member mismatch", code="scope_mismatch")
        if entry["paths"] != sorted(entry["paths"]) or len(set(p.casefold() for p in entry["paths"])) != len(entry["paths"]):
            raise SnapshotError("duplicate namespace member", code="duplicate_path")
        selected = sorted(p for p in paths if _matches(p, entry["pattern"]))
        # Source namespace may declare known unselected metadata paths; none is read.
        if not entry["pattern"].endswith("/sources/*.json") and selected != entry["paths"]:
            raise SnapshotError("unselected entity namespace member", code="scope_mismatch")
        if not set(selected) <= set(entry["paths"]):
            raise SnapshotError("selected source missing from namespace", code="scope_mismatch")


def _validate_control(doc, game, expected):
    try:
        _validate_control_fields(doc, game, expected)
    except SnapshotError:
        raise
    except (TypeError, KeyError, AttributeError, ValueError):
        raise SnapshotError("malformed compatibility control metadata", code="invalid_manifest") from None


def _matches(name, pattern):
    # Glob segments, unlike fnmatch('*'), must not cross a path separator.
    expression = re.escape(pattern).replace(r"\*\*/", "(?:[^/]+/)*").replace(r"\*", "[^/]*")
    return re.fullmatch(expression, name) is not None


@dataclass(frozen=True)
class LegacyCompatibilityAttachment:
    root: Path
    control_path: str
    _document: bytes = field(repr=False)

    @property
    def binding(self):
        return json.loads(self._document)

    @property
    def game(self):
        return self.binding["game"]

    @property
    def data_root(self):
        return self.root / "data"

    @property
    def games_root(self):
        return self.root / "data/canonical/games"

    def _name(self, path):
        try:
            name = Path(path).relative_to(self.root).as_posix()
        except ValueError:
            raise SnapshotError("read outside selected roots", code="scope_mismatch") from None
        _relative(name)
        return name

    def require_capability(self, capability):
        if capability != "catalog_query_collection":
            raise SnapshotError("capability is not available in Tier A", code="unsupported_capability")

    def require(self, path):
        name = self._name(path)
        if name not in {r["path"] for r in self.binding["files"]}:
            raise SnapshotError("dependency is not selected", code="unsupported_capability", relative_path=name)
        _path(self.root, name)

    def read_bytes(self, path):
        name = self._name(path)
        self.require(path)
        row = next(r for r in self.binding["files"] if r["path"] == name)
        raw = _read(self.root, name)
        if len(raw) != row["byte_length"] or hashlib.sha256(raw).hexdigest() != row["sha256"]:
            raise SnapshotError("selected dependency changed", code="integrity_mismatch", relative_path=name)
        return raw

    def read_json(self, path):
        return strict_json(self.read_bytes(path), self._name(path))

    def paths(self, root, pattern):
        base = self._name(root)
        return tuple(self.root / r["path"] for r in self.binding["files"] if _matches(r["path"], base + "/" + pattern))

    def verify_unchanged(self):
        if _directory(self.root) != self.root:
            raise SnapshotError("attachment root changed", code="scope_mismatch")
        current = strict_json(_read(self.root, self.control_path), self.control_path)
        if canonical_json(current) != self._document:
            raise SnapshotError("compatibility control changed", code="identity_mismatch")
        _validate_control(current, self.game, current["profile_id"])
        games = self.games_root
        _path(self.root, "data/canonical/games")
        try:
            children = sorted(p.name for p in games.iterdir() if p.is_dir() or p.is_symlink())
            if children != current["game_namespaces"]:
                raise SnapshotError("game namespace changed", code="scope_mismatch")
            for entry in current["namespaces"]:
                _path(self.root, entry["pattern"].split("*", 1)[0].rstrip("/"))
                observed = sorted(p.relative_to(self.root).as_posix() for p in self.root.glob(entry["pattern"]))
                for name in observed:
                    _path(self.root, name)
                if observed != entry["paths"]:
                    raise SnapshotError("selected namespace changed", code="inventory_mismatch")
            for name in current["absent"]:
                path = _path(self.root, name)
                if path.exists():
                    raise SnapshotError("bound absence changed", code="scope_mismatch", relative_path=name)
        except OSError:
            raise SnapshotError("namespace inspection failed", code="filesystem_error") from None
        # Check case/normalization ambiguity at every selected ancestor, including
        # empty namespace directories. This inspects names, never excluded bytes.
        selected_names = {}
        for name in [r["path"] for r in current["files"]] + [n["pattern"].split("*", 1)[0].rstrip("/") for n in current["namespaces"]]:
            path = self.root / name
            while path != self.root and path.is_relative_to(self.root):
                selected_names.setdefault(path.parent, set()).add(path.name.casefold())
                path = path.parent
        for parent, wanted in selected_names.items():
            if parent.is_dir():
                counts = Counter(p.name.casefold() for p in parent.iterdir())
                if any(counts[name] > 1 for name in wanted):
                    raise SnapshotError("casefold path collision in selected namespace", code="duplicate_path")
        for row in current["files"]:
            strict_json(self.read_bytes(self.root / row["path"]), row["path"])

    def validate_query(self, snapshot):
        if snapshot.snapshot_id != self.binding["query_snapshot_id"] or dict(Counter(x.entity_type for x in snapshot.entities)) != self.binding["entity_counts"]:
            raise SnapshotError("query result differs from reviewed profile", code="query_mismatch")


def attach_legacy_compatibility(root, *, control_path, game, expected_profile_id):
    """Attach one explicit in-place closure; never select defaults or acquire data."""
    if not isinstance(game, str) or not _ID.fullmatch(game):
        raise SnapshotError("invalid requested game", code="wrong_game")
    root = _directory(root, missing_code="missing_compatibility_root")
    _relative(control_path)
    doc = strict_json(_read(root, control_path), control_path)
    _validate_control(doc, game, expected_profile_id)
    result = LegacyCompatibilityAttachment(root, control_path, canonical_json(doc))
    result.verify_unchanged()
    return result
