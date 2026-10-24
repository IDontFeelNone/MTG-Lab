"""Local fictional v1 packet authoring; structural checks confer no authority."""
from __future__ import annotations

import json
import os
from pathlib import Path
import re
import secrets
import stat

from gameplay_rules.source_evidence.artifacts import _open_regular_no_symlinks

from . import validation as v


IDENTITY = re.compile(r"sha256:[0-9a-f]{64}\Z")
DRAFT_BYTE_LIMIT = 1_024_000


def selected_path(value):
    """Keep the established unambiguous, no-symlink local path convention."""
    raw = os.fspath(value)
    if (not isinstance(raw, str) or not raw or "\\" in raw or "//" in raw
            or any(ord(c) < 32 or ord(c) == 127 for c in raw)
            or any(c in ("", ".", "..") for c in raw.lstrip("/").split("/"))):
        v.fail("UNAMBIGUOUS_LOCAL_PATH_REQUIRED")
    return Path(os.path.abspath(raw))


def outside_repository(path):
    if path == v.ROOT or v.ROOT in path.parents:
        v.fail("PILOT_OUTPUT_MUST_BE_OUTSIDE_REPOSITORY")


def open_directory(path):
    """Pin every directory component, as the inherited safe reader does."""
    descriptor = os.open("/", os.O_RDONLY | os.O_DIRECTORY)
    try:
        for component in path.parts[1:]:
            following = os.open(component, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW,
                dir_fd=descriptor)
            os.close(descriptor)
            descriptor = following
        return descriptor
    except BaseException:
        os.close(descriptor)
        raise


def atomic_create(path, raw, *, identical=False):
    """Publish complete bytes without replacement, relative to a pinned directory."""
    outside_repository(path)
    directory = open_directory(path.parent)
    temporary = ".partial-" + secrets.token_hex(16)
    created = False
    try:
        descriptor = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
            0o600, dir_fd=directory)
        created = True
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(raw)
            stream.flush()
            os.fsync(stream.fileno())
        try:
            os.link(temporary, path.name, src_dir_fd=directory, dst_dir_fd=directory,
                follow_symlinks=False)
        except FileExistsError:
            if not identical:
                v.fail("OUTPUT_EXISTS_OVERWRITE_FORBIDDEN")
            # Read the actual pinned destination; do not trust a cached record.
            existing = os.open(path.name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK,
                dir_fd=directory)
            with os.fdopen(existing, "rb") as stream:
                before = os.fstat(stream.fileno())
                if not stat.S_ISREG(before.st_mode) or before.st_nlink != 1:
                    v.fail("REGULAR_UNLINKED_RECORD_REQUIRED")
                data = stream.read(128_001)
                after = os.fstat(stream.fileno())
                fields = ("st_dev", "st_ino", "st_size", "st_mtime_ns", "st_ctime_ns")
                if any(getattr(before, k) != getattr(after, k) for k in fields) or data != raw:
                    v.fail("EXISTING_RECORD_BYTES_MISMATCH")
            return "ALREADY_PRESENT_IDENTICAL"
        return "RECORDED"
    finally:
        if created:
            os.unlink(temporary, dir_fd=directory)
        os.close(directory)


def read_draft_bytes(path):
    """Draft formatting has its own bound; sealed readers remain unchanged."""
    descriptor = _open_regular_no_symlinks(selected_path(path))
    if descriptor is None:
        v.fail("REGULAR_DRAFT_WITHOUT_SYMLINKS_REQUIRED")
    with os.fdopen(descriptor, "rb") as stream:
        before = os.fstat(stream.fileno())
        if before.st_nlink != 1:
            v.fail("HARD_LINKED_DRAFT_FORBIDDEN")
        raw = stream.read(DRAFT_BYTE_LIMIT + 1)
        after = os.fstat(stream.fileno())
        fields = ("st_dev", "st_ino", "st_size", "st_mtime_ns", "st_ctime_ns")
        if any(getattr(before, k) != getattr(after, k) for k in fields):
            v.fail("DRAFT_CHANGED_WHILE_READING")
    if len(raw) > DRAFT_BYTE_LIMIT:
        v.fail("DRAFT_EXCEEDS_BOUNDED_READ_SIZE")
    return raw


def read_draft(path):
    raw = read_draft_bytes(path)
    try:
        envelope = json.loads(raw, object_pairs_hook=v._unique, parse_constant=v._nonfinite)
    except (ValueError, UnicodeError, RecursionError):
        v.fail("MALFORMED_DRAFT_JSON")
    envelope = v.snapshot(envelope)
    if (type(envelope) is not dict or set(envelope) != {"draft_version", "base_packet_id", "packet"}
            or type(envelope["draft_version"]) is not int or envelope["draft_version"] != 1
            or type(envelope["packet"]) is not dict):
        v.fail("EXPLICIT_DRAFT_ENVELOPE_REQUIRED")
    if "packet_id" in envelope["packet"]:
        v.fail("DRAFT_MUST_NOT_SUPPLY_PACKET_ID")
    base = envelope["base_packet_id"]
    if base is not None and (type(base) is not str or not IDENTITY.fullmatch(base)):
        v.fail("EXPLICIT_BASE_IDENTITY_REQUIRED")
    return envelope


class Workspace:
    """One explicitly selected local directory; no registry or mutable truth store."""
    def __init__(self, root):
        self.root = selected_path(root)
        outside_repository(self.root)
        os.close(open_directory(self.root))  # Existing explicit directory required.
        self.packets = self.root / "packets"

    def bindings(self):
        # Each operation reads actual retained bytes; a reused workspace grants no
        # cached authorization after a retained contract or binding changes.
        package = v.load_package()
        return package, package["contract.json"], v.retained_rules()

    def packet_path(self, identity):
        if type(identity) is not str or not IDENTITY.fullmatch(identity):
            v.fail("EXPLICIT_PACKET_IDENTITY_REQUIRED")
        return self.packets / (identity[7:] + ".json")

    def load_history(self, value):
        history = {}
        pending = list(value["history"]["supersedes_packet_ids"])
        while pending:
            identity = pending.pop()
            if identity in history:
                continue
            packet = v.canonical_read(self.packet_path(identity))
            v.check_identity(packet, v.PACKET_DOMAIN, "packet_id")
            if packet["packet_id"] != identity:
                v.fail("RECORD_FILENAME_IDENTITY_MISMATCH")
            history[identity] = packet
            pending.extend(packet["history"]["supersedes_packet_ids"])
        return history

    def validate(self, value):
        value = v.snapshot(value)
        package, contract, rules = self.bindings()
        # Schema/own identity first, before following untrusted history references.
        try:
            v.StrictValidator(contract).validate(value)
        except Exception as error:
            v.fail("PACKET_SCHEMA: " + type(error).__name__)
        v.check_identity(value, v.PACKET_DOMAIN, "packet_id")
        history = self.load_history(value)
        packet = v.validate_packet(value, contract=contract, rules=rules, history=history)
        retained_roots = {package[name]["packet_id"]: v._canonical_candidate(package[name])
            for name in v.PACKET_NAMES}
        # The pilot offers a linear authoring workflow. Import cannot bypass
        # explicit parent selection for a correction or introduce history merges.
        for row in (packet, *history.values()):
            parents = row["history"]["supersedes_packet_ids"]
            if len(parents) > 1:
                v.fail("PILOT_LINEAR_HISTORY_REQUIRED")
            if not parents and row["revision"] != 1:
                v.fail("PILOT_ROOT_REVISION_ONE_REQUIRED")
            # Empty ancestry is not proof of fresh review material. Only exact
            # freshly validated examples establish pilot roots; all edits must
            # retain explicit history, including imported reachable ancestors.
            if not parents and retained_roots.get(row["packet_id"]) != v._canonical_candidate(row):
                v.fail("PILOT_EDITED_ROOT_REQUIRES_EXPLICIT_PARENT: record the unchanged example, then draft --base")
        return packet, history

    def read(self, identity):
        packet = v.canonical_read(self.packet_path(identity))
        if type(packet) is not dict or packet.get("packet_id") != identity:
            v.fail("RECORD_FILENAME_IDENTITY_MISMATCH")
        return self.validate(packet)

    def draft(self, *, example=None, base=None, output):
        if example is not None:
            if example not in v.PACKET_NAMES:
                v.fail("EXPLICIT_RETAINED_FICTIONAL_EXAMPLE_REQUIRED")
            package, _, _ = self.bindings()
            packet = v.snapshot(package[example])
        else:
            packet, _ = self.read(base)
            packet["revision"] += 1
            packet["history"]["supersedes_packet_ids"] = [base]
        del packet["packet_id"]
        envelope = {"draft_version": 1, "base_packet_id": base, "packet": packet}
        path = selected_path(output)
        if path == self.packets or self.packets in path.parents:
            v.fail("EDITABLE_DRAFT_CANNOT_BE_A_SEALED_RECORD")
        raw = (json.dumps(envelope, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode()
        if len(raw) > DRAFT_BYTE_LIMIT:
            raw = v._canonical_candidate(envelope)
        if len(raw) > DRAFT_BYTE_LIMIT:
            v.fail("DRAFT_EXCEEDS_BOUNDED_READ_SIZE")
        atomic_create(path, raw)
        return {"status": "EDITABLE_FICTIONAL_DRAFT", "base_packet_id": base}

    def record(self, *, draft=None, sealed=None):
        if draft is not None:
            envelope = v.snapshot(read_draft(draft))
            packet = envelope["packet"]  # Privately owned input, never caller data.
            base_id = envelope["base_packet_id"]
            if type(packet.get("history")) is not dict:
                v.fail("PACKET_SCHEMA: history object required")
            if base_id is None:
                if packet.get("revision") != 1 or packet.get("history", {}).get("supersedes_packet_ids") != []:
                    v.fail("ROOT_DRAFT_REQUIRES_REVISION_ONE_WITHOUT_PARENT")
            else:
                base, _ = self.read(base_id)
                if (type(packet.get("revision")) is not int or packet["revision"] != base["revision"] + 1
                        or packet.get("history", {}).get("supersedes_packet_ids") != [base_id]):
                    v.fail("DRAFT_LIFECYCLE_MUST_MATCH_EXPLICIT_BASE")
            v.seal_packet(packet)
        else:
            packet = v.canonical_read(selected_path(sealed))
        packet, _ = self.validate(packet)
        raw = v._canonical_candidate(packet)
        if len(raw) > 128_000:
            v.fail("PACKET_EXCEEDS_BOUNDED_READ_SIZE")
        # No directory or packet output before validation succeeds.
        directory = open_directory(self.root)
        try:
            try:
                os.mkdir("packets", mode=0o700, dir_fd=directory)
            except FileExistsError:
                pass
        finally:
            os.close(directory)
        path = self.packet_path(packet["packet_id"])
        status = atomic_create(path, raw, identical=True)
        readback, _ = self.read(packet["packet_id"])
        if v._canonical_candidate(readback) != raw:
            v.fail("READBACK_BYTES_MISMATCH")
        return {"status": status, "packet_id": packet["packet_id"], "revision": packet["revision"],
            "structural_validity": "VALID", "execution_authority": "BLOCKED"}

    def inspect(self, identity, *, history=False):
        packet, ancestors = self.read(identity)
        if not history:
            return render(packet, ancestors)
        ordered = []
        seen = set()
        def visit(row):
            if row["packet_id"] in seen:
                return
            seen.add(row["packet_id"])
            for parent in row["history"]["supersedes_packet_ids"]:
                visit(ancestors[parent])
            ordered.append(render(row, ancestors))
        visit(packet)
        return "\n\n".join(ordered)


def render(packet, ancestors):
    """Render supplied prose and references only; derive no gameplay reasoning."""
    lines = [packet["scenario_label"],
        f'Packet: {packet["packet_id"]} | lineage: {packet["lineage_id"]} | revision: {packet["revision"]}',
        'Structural validity: VALID (format and references only; fictional claims unverified)',
        'Execution authority: BLOCKED',
        'Authored evidence conditions: reported per claim and step below',
        f'Contract: {packet["contract_id"]}',
        'Question: ' + json.dumps(packet["question"], ensure_ascii=False)]
    def rows(label, values):
        lines.append(label + ":")
        lines.extend(json.dumps(row, ensure_ascii=False, sort_keys=True, indent=2) for row in values)
        if not values:
            lines.append("(none supplied)")
    rows("Fictional contexts", packet["contexts"])
    rows("Authored claims, attribution, assumptions and evidence conditions", packet["claims"])
    rows("Applicable choices (no selection or compatibility inference)", packet["choices"])
    rows("Authored alternative-specific reasoning and dependencies", packet["reasoning"])
    rows("Retained rule/version context (does not verify fictional assertions)", packet["rule_evidence"])
    rows("Authored limitations: missing, unsupported, conflict, compatibility and scope", packet["limitations"])
    rows("Authored bounded conclusion", [packet["conclusion"]])
    lines.append("Explicit parent packet identities: " + json.dumps(packet["history"]["supersedes_packet_ids"]))
    for observation in packet["history"]["review_observations"]:
        origins = [row for row in ancestors.values()
            if any(old["observation_id"] == observation["observation_id"]
                for old in row["history"]["review_observations"])]
        origin = min(origins, key=lambda row: row["revision"]) if origins else packet
        lines.append(f'Fictional reviewer observation in packet {packet["packet_id"]} revision {packet["revision"]}; '
            f'originating packet {origin["packet_id"]} revision {origin["revision"]}:')
        lines.append(json.dumps(observation, ensure_ascii=False, sort_keys=True, indent=2))
    if not packet["history"]["review_observations"]:
        lines.append("Fictional reviewer observations: (none in this revision; ancestors remain immutable)")
    return "\n".join(lines)
