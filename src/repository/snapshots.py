"""Local fictional snapshot verification and explicit read-only catalog attachment.

This profile grants no admission, production eligibility or source permission.
It never acquires data, extracts archives, writes files or selects a fallback.
"""
from __future__ import annotations

from dataclasses import dataclass, field
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import stat
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker

from schemas import schema_path
from validation import validate_document
from validation.json_schema import load_schema


CONTRACT_VERSION = "canonical-snapshot-fictional-v1"
REPRESENTATION = "typed-card-printing-v1"
VALIDATOR_PROFILE = "fictional-read-only-verifier-v1"
SCHEMA_NAMES = ("canonical-snapshot", "card", "printing", "source-record")
REQUIRED_CHECKS = ("byte-integrity", "entity-schemas", "relationships", "scope-and-capabilities", "source-correspondence")
UNRUN_CHECKS = ("production-admission", "source-permissions", "full-production-consumers")
CAPABILITIES = {"catalog_identity": "available", "mechanical_evidence": "unavailable",
                "rules_execution": "unsupported", "identifier_records": "unavailable"}
MAX_FILES = 256
MAX_FILE_BYTES = 2 * 1024 * 1024
MAX_TOTAL_BYTES = 16 * 1024 * 1024
_ID = re.compile(r"^[a-z0-9][a-z0-9._-]*$")
_SHA = re.compile(r"^[0-9a-f]{64}$")
_PATH = re.compile(r"^[A-Za-z0-9_./-]+$")


class SnapshotError(ValueError):
    """Bounded structured failure; diagnostics contain no source content/absolute path."""

    def __init__(self, message: str, *, code: str = "unverified_attachment", relative_path: str | None = None):
        super().__init__(message)
        self.code = code
        self.relative_path = relative_path

    def as_dict(self) -> dict:
        return {"status": "blocked", "code": self.code, "message": str(self),
                "relative_path": self.relative_path}


def canonical_json(value: Any) -> bytes:
    """Contract serialization; this integer/string profile has no float semantics."""
    def check(item):
        if isinstance(item, float):
            raise SnapshotError("snapshot JSON does not support floating point values", code="invalid_json")
        if isinstance(item, dict):
            if not all(isinstance(key, str) for key in item):
                raise SnapshotError("snapshot object keys must be strings", code="invalid_json")
            for child in item.values():
                check(child)
        elif isinstance(item, (list, tuple)):
            for child in item:
                check(child)
    check(value)
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False,
                      allow_nan=False).encode("utf-8")


def semantic_identity(kind: str, document: dict) -> str:
    return hashlib.sha256(canonical_json({"identity_domain": "mtg-lab:" + kind + ":fictional-v1",
                                          "document": document})).hexdigest()


def _json(raw: bytes, name: str) -> dict:
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ValueError("duplicate key")
            result[key] = value
        return result
    def reject(value):
        raise ValueError("unsupported number")
    try:
        value = json.loads(raw, object_pairs_hook=pairs, parse_float=reject, parse_constant=reject)
        if not isinstance(value, dict):
            raise ValueError("object required")
        return value
    except (ValueError, UnicodeError, RecursionError):
        raise SnapshotError("invalid snapshot JSON", code="invalid_json", relative_path=name) from None


def _relative(name: str) -> PurePosixPath:
    path = PurePosixPath(name)
    if (not name or not _PATH.fullmatch(name) or path.is_absolute() or ".." in path.parts
            or path.as_posix() != name or any(part.endswith(".") for part in path.parts)):
        raise SnapshotError("unsafe or ambiguous snapshot path", code="unsafe_path")
    return path


def _directory(path: Path, *, missing_code: str = "missing_snapshot") -> Path:
    try:
        path = Path(path).absolute()
    except TypeError:
        raise SnapshotError("catalog directory must be an explicit path", code="missing_snapshot") from None
    if any(item.is_symlink() for item in (path, *path.parents)):
        raise SnapshotError("snapshot path contains a symlink", code="symlink")
    if not path.is_dir():
        raise SnapshotError("requested catalog directory is missing", code=missing_code)
    return path.resolve()


def _read_tree(root: Path) -> dict[str, bytes]:
    files, names, total = {}, set(), 0
    def unreadable(error):
        raise SnapshotError("snapshot directory could not be inventoried", code="filesystem_error")
    try:
        for directory, directories, filenames in os.walk(root, followlinks=False, onerror=unreadable):
            for filename in sorted(directories + filenames):
                path = Path(directory) / filename
                name = path.relative_to(root).as_posix()
                _relative(name)
                key = name.casefold()
                if key in names:
                    raise SnapshotError("duplicate normalized snapshot path", code="duplicate_path")
                names.add(key)
                info = path.lstat()
                if stat.S_ISLNK(info.st_mode):
                    raise SnapshotError("snapshot contains a symlink", code="symlink", relative_path=name)
                if stat.S_ISDIR(info.st_mode):
                    continue
                if not stat.S_ISREG(info.st_mode):
                    raise SnapshotError("snapshot contains a nonregular file", code="unsafe_file", relative_path=name)
                total += info.st_size
                if len(files) >= MAX_FILES or info.st_size > MAX_FILE_BYTES or total > MAX_TOTAL_BYTES:
                    raise SnapshotError("snapshot exceeds bounded profile", code="size_limit")
                descriptor = os.open(path, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0))
                with os.fdopen(descriptor, "rb") as stream:
                    if not stat.S_ISREG(os.fstat(stream.fileno()).st_mode):
                        raise SnapshotError("snapshot file type changed", code="unsafe_file")
                    raw = stream.read(MAX_FILE_BYTES + 1)
                if len(raw) != info.st_size:
                    raise SnapshotError("snapshot changed during reading", code="integrity_mismatch", relative_path=name)
                files[name] = raw
        return files
    except OSError:
        raise SnapshotError("snapshot filesystem read failed", code="filesystem_error") from None


def _validate(document: dict, component: str, name: str) -> None:
    schema = load_schema("canonical-snapshot", "v1")
    contract = {"$ref": "#/$defs/" + component, "$defs": schema["$defs"]}
    errors = Draft202012Validator(contract, format_checker=FormatChecker()).iter_errors(document)
    if next(errors, None) is not None:
        raise SnapshotError("snapshot document violates supported contract",
                            code="invalid_validation" if component == "report" else "invalid_manifest", relative_path=name)


def _schema_bindings() -> dict:
    return {"schema_version": "v1", "schemas": [{"name": name, "version": "v1",
            "byte_length": len(schema_path(name, "v1").read_bytes()),
            "sha256": hashlib.sha256(schema_path(name, "v1").read_bytes()).hexdigest()}
            for name in SCHEMA_NAMES]}


def _validator_sha256() -> str:
    return hashlib.sha256(Path(__file__).read_bytes()).hexdigest()


def verify_snapshot(root: Path, *, game: str, expected_snapshot_id: str) -> SnapshotVerification:
    """Independently verify one explicitly pinned, fictional local directory."""
    if not isinstance(game, str) or not _ID.fullmatch(game):
        raise SnapshotError("invalid requested game", code="wrong_game")
    if not isinstance(expected_snapshot_id, str) or not _SHA.fullmatch(expected_snapshot_id):
        raise SnapshotError("expected snapshot identity is required", code="invalid_identity")
    root = _directory(root)
    files = _read_tree(root)

    def document(name, component):
        _relative(name)
        if name not in files:
            raise SnapshotError("required snapshot file is missing", code="missing_file", relative_path=name)
        result = _json(files[name], name)
        if result.get("schema_version") != "v1":
            raise SnapshotError("unsupported snapshot schema version", code="unsupported_version", relative_path=name)
        _validate(result, component, name)
        return result

    def binding(ref, expected_path=None):
        name = ref["path"]
        _relative(name)
        if expected_path is not None and name != expected_path:
            raise SnapshotError("unsupported snapshot dependency path", code="dependency_mismatch")
        if name not in files:
            raise SnapshotError("required snapshot dependency is missing", code="missing_file", relative_path=name)
        if len(files[name]) != ref["byte_length"] or hashlib.sha256(files[name]).hexdigest() != ref["sha256"]:
            raise SnapshotError("snapshot dependency integrity mismatch", code="integrity_mismatch", relative_path=name)
        return name

    if "release-manifest.json" not in files:
        raise SnapshotError("snapshot release manifest is missing", code="missing_file", relative_path="release-manifest.json")
    release = _json(files["release-manifest.json"], "release-manifest.json")
    if release.get("contract_version") != CONTRACT_VERSION:
        raise SnapshotError("unsupported snapshot contract version", code="unsupported_version")
    release = document("release-manifest.json", "release")
    if release["game"] != game:
        raise SnapshotError("snapshot game differs from requested game", code="wrong_game")
    if release["snapshot_id"] != expected_snapshot_id:
        raise SnapshotError("snapshot differs from requested identity", code="identity_mismatch")
    if semantic_identity("release-manifest", {k: v for k, v in release.items() if k != "snapshot_id"}) != release["snapshot_id"]:
        raise SnapshotError("snapshot release identity mismatch", code="identity_mismatch")
    content = document(binding(release["content_manifest"], "content-manifest.json"), "content")
    source = document(binding(release["source_manifest"], "source-manifest.json"), "source")
    report = document(binding(release["validation_report"], "validation-report.json"), "report")
    for item, kind, own_id in ((content, "content-manifest", "content_id"),
                                (source, "source-manifest", "source_manifest_id")):
        if semantic_identity(kind, {k: v for k, v in item.items() if k != own_id}) != item[own_id]:
            raise SnapshotError("snapshot component identity mismatch", code="identity_mismatch")
    for key in ("game", "content_id", "source_manifest_id", "schema_set_id", "policy_id",
                "representation_profile", "entity_inventory", "capabilities"):
        if release[key] != content[key]:
            raise SnapshotError("contradictory snapshot metadata", code="metadata_mismatch")
    if source["game"] != game or source["source_manifest_id"] != content["source_manifest_id"]:
        raise SnapshotError("source manifest scope mismatch", code="source_mismatch")
    if content["source_manifest"] != release["source_manifest"]:
        raise SnapshotError("contradictory source dependency", code="source_mismatch")
    inventory = content["files"]
    paths = [ref["path"] for ref in inventory]
    for name in paths:
        _relative(name)
    if paths != sorted(paths) or len(set(name.casefold() for name in paths)) != len(paths):
        raise SnapshotError("duplicate or unordered manifest inventory", code="duplicate_path")
    controls = {"release-manifest.json", "content-manifest.json", "source-manifest.json", "validation-report.json"}
    if controls & set(paths):
        raise SnapshotError("self-referential snapshot inventory", code="invalid_manifest")
    missing, extra = (controls | set(paths)) - files.keys(), files.keys() - (controls | set(paths))
    if missing or extra:
        raise SnapshotError("snapshot file inventory mismatch", code="missing_file" if missing else "extra_file")
    for ref in inventory:
        binding(ref)
    by_path = {ref["path"]: ref for ref in inventory}
    for key, path in (("policy", "policy.json"), ("schema_bindings", "schema-bindings.json")):
        binding(content[key], path)
        if by_path.get(path) != content[key]:
            raise SnapshotError("required dependency not in content inventory", code="dependency_mismatch")
    policy = document("policy.json", "policy")
    schemas = document("schema-bindings.json", "schemas")
    if schemas != _schema_bindings():
        raise SnapshotError("snapshot schemas incompatible with current contracts", code="incompatible_schema")
    if semantic_identity("schema-set", schemas) != content["schema_set_id"] or semantic_identity("policy", policy) != content["policy_id"]:
        raise SnapshotError("snapshot schema/policy identity mismatch", code="identity_mismatch")
    validation_input = {"content_id": content["content_id"], "schema_set_id": content["schema_set_id"],
                        "policy_id": content["policy_id"], "validator_profile": VALIDATOR_PROFILE,
                        "validator_sha256": _validator_sha256(), "required_checks": list(REQUIRED_CHECKS)}
    validation_id = semantic_identity("validation-input", validation_input)
    if release["validation_input"] != validation_input or release["validation_input_id"] != validation_id:
        raise SnapshotError("snapshot validation inputs incompatible", code="invalid_validation")
    if (report["game"] != game or report["content_id"] != content["content_id"]
            or report["validation_input_id"] != validation_id
            or report["inventory_identity"] != semantic_identity("entity-inventory", content["entity_inventory"])):
        raise SnapshotError("validation report does not bind this snapshot", code="invalid_validation")
    _validate_graph(root, files, content, source, by_path, game)
    if _directory(root) != root or _read_tree(root) != files:
        raise SnapshotError("snapshot changed during verification", code="integrity_mismatch")
    metadata = {key: release[key] for key in ("game", "snapshot_id", "content_id", "source_manifest_id",
                "schema_set_id", "policy_id", "validation_input_id", "representation_profile", "entity_inventory", "capabilities")}
    metadata.update(profile="fictional-snapshot-v1", validation_status="valid_fictional",
                    validation_report_sha256=release["validation_report"]["sha256"],
                    production_eligible=False, approval_state="not_granted", source_policy_clearance="not_granted")
    return SnapshotVerification(root, canonical_json(metadata))


def _validate_graph(root, files, content, source, by_path, game):
    prefix = "data/canonical/games/" + game + "/"
    game_path = prefix + "game.json"
    if game_path not in files:
        raise SnapshotError("explicit game record is required", code="missing_file")
    game_record = _json(files[game_path], game_path)
    if set(game_record) != {"id", "name"} or game_record.get("id") != game or not isinstance(game_record.get("name"), str) or not game_record["name"]:
        raise SnapshotError("game record scope mismatch", code="wrong_game")
    allowed = {game_path, "schema-bindings.json", "policy.json"}
    declared = set()
    for row in source["sources"]:
        if row["source_id"] in declared:
            raise SnapshotError("duplicate source identity", code="source_mismatch")
        declared.add(row["source_id"])
        record_path = prefix + "sources/" + row["source_id"] + ".json"
        evidence = row["evidence"]
        _relative(evidence["path"])
        if (row["record_path"] != record_path or record_path not in files
                or not evidence["path"].startswith("evidence/") or by_path.get(evidence["path"]) != evidence):
            raise SnapshotError("source dependency closure mismatch", code="source_mismatch")
        record = _json(files[record_path], record_path)
        if (record.get("schema_version") != "v1" or record.get("id") != row["source_id"]
                or record.get("content_hash") != evidence["sha256"] or record.get("archival_location") != evidence["path"]
                or record.get("source_classification") != "internal" or record.get("provider") != "Original fictional fixture"
                or not str(record.get("source_location", "")).startswith("urn:mtg-lab:fictional:")):
            raise SnapshotError("source-record correspondence mismatch", code="source_mismatch")
        try:
            validate_document(record, "source-record", "v1")
        except (ValueError, TypeError, KeyError):
            raise SnapshotError("source-record schema invalid", code="source_mismatch") from None
        allowed.update((record_path, evidence["path"]))
    observed = {kind: {"count": 0, "records": []} for kind in ("card", "printing", "identifier")}
    for path in by_path:
        if path in allowed:
            continue
        relative = path.removeprefix(prefix).split("/") if path.startswith(prefix) else []
        if len(relative) != 3 or relative[0] not in {"cards", "printings"} or not _ID.fullmatch(relative[1]):
            raise SnapshotError("unsupported file in fictional representation", code="unsupported_profile")
        kind = "card" if relative[0] == "cards" else "printing"
        if relative[2] != kind + ".json":
            raise SnapshotError("unsupported canonical record path", code="unsupported_profile")
        record = _json(files[path], path)
        if record.get("schema_version") != "v1":
            raise SnapshotError("unsupported canonical schema version", code="unsupported_version")
        if "metadata" in record or record.get("treatments"):
            raise SnapshotError("unsupported optional representation fields", code="unsupported_profile")
        if not isinstance(record.get("provenance"), list) or not all(row.get("source_id") in declared for row in record["provenance"] if isinstance(row, dict)):
            raise SnapshotError("canonical provenance dependency missing", code="source_mismatch")
        observed[kind]["records"].append({"id": relative[1], "sha256": hashlib.sha256(files[path]).hexdigest()})
    for values in observed.values():
        values["records"].sort(key=lambda row: row["id"])
        values["count"] = len(values["records"])
    if observed != content["entity_inventory"] or not observed["card"]["count"] or not observed["printing"]["count"]:
        raise SnapshotError("canonical entity inventory mismatch", code="inventory_mismatch")
    try:
        from repository.canonical import CanonicalRepository
        CanonicalRepository(game, games_root=root / "data/canonical/games")
    except (ValueError, TypeError, KeyError, OSError):
        raise SnapshotError("canonical schemas or relationships invalid", code="invalid_graph") from None


@dataclass(frozen=True)
class SnapshotVerification:
    """Immutable metadata from verification; not itself an attachment/approval."""
    root: Path
    _metadata: bytes = field(repr=False)

    @property
    def binding(self) -> dict:
        return json.loads(self._metadata)

    @property
    def game(self) -> str:
        return self.binding["game"]

    @property
    def snapshot_id(self) -> str:
        return self.binding["snapshot_id"]


@dataclass(frozen=True)
class SnapshotAttachment(SnapshotVerification):
    @property
    def data_root(self) -> Path:
        return self.root / "data"

    @property
    def games_root(self) -> Path:
        return self.data_root / "canonical/games"

    @property
    def canonical_data_root(self) -> Path:
        return self.data_root / "canonical"

    @property
    def evidence_root(self) -> Path:
        return self.root / "evidence"

    def verify_unchanged(self) -> None:
        current = verify_snapshot(self.root, game=self.game, expected_snapshot_id=self.snapshot_id)
        if current._metadata != self._metadata:
            raise SnapshotError("attachment bindings changed", code="identity_mismatch")


def attach_snapshot(root: Path, *, game: str, expected_snapshot_id: str) -> SnapshotAttachment:
    verified = verify_snapshot(root, game=game, expected_snapshot_id=expected_snapshot_id)
    return SnapshotAttachment(verified.root, verified._metadata)


@dataclass(frozen=True)
class LegacyPublicAttachment:
    """Explicit compatibility roots; not an immutable release or new authority."""
    game: str
    data_root: Path
    games_root: Path

    @property
    def binding(self) -> dict:
        return {"profile": "legacy-public-v1", "game": self.game, "snapshot_id": None,
                "validation_status": "existing-reader-contracts"}

    def verify_unchanged(self) -> None:
        if not isinstance(self.game, str) or not _ID.fullmatch(self.game):
            raise SnapshotError("invalid legacy game", code="wrong_game")
        _directory(self.data_root, missing_code="missing_legacy_catalog")
        _directory(self.games_root, missing_code="missing_legacy_catalog")
        _directory(self.games_root / self.game, missing_code="missing_legacy_catalog")


def attach_legacy_public(*, game: str, data_root: Path, games_root: Path | None = None) -> LegacyPublicAttachment:
    data = _directory(data_root, missing_code="missing_legacy_catalog")
    games = _directory(games_root if games_root is not None else data / "canonical/games",
                       missing_code="missing_legacy_catalog")
    result = LegacyPublicAttachment(game, data, games)
    result.verify_unchanged()
    return result
