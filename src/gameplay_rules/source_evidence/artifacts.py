"""Metadata-only, offline verification of an explicitly supplied rules TXT.

This module never acquires, stores, normalizes or projects a source document.
The local file remains the caller's responsibility. A successful check establishes
exact bytes and a few bounded markers, not authenticity, permission or approval.
"""
from __future__ import annotations

import codecs
from dataclasses import dataclass
import fnmatch
import hashlib
import os
from pathlib import Path
import re
import stat

from evidence.contracts import sha256_identity
from gameplay_rules.errors import GameplayContractError
from .contracts import (MetadataContract, _date, _enum, _fail, _hash, _int,
                        _keys, _timestamp)


REAL_PROFILE_VERSION = "official-comprehensive-rules-txt-20260925-v1"
FICTIONAL_PROFILE_VERSION = "fictional-comprehensive-rules-txt-20320314-v1"
_MAX_BYTES = 5 * 1024 * 1024
_CHUNK_BYTES = 64 * 1024
_REQUEST_HANDOFF = {
    "verifier_module": "gameplay_rules.source_evidence.verify",
    "verifier_api": "gameplay_rules.source_evidence.artifacts.verify_local_artifact",
    "result_schema_version": "gameplay-rules-artifact-verification-result-v1",
}
_MONTHS = ("January", "February", "March", "April", "May", "June", "July",
           "August", "September", "October", "November", "December")
_PROFILES = {
    REAL_PROFILE_VERSION: {
        "game_id": "magic", "effective_date": "2026-09-25", "artifact_family": "20260925",
        "artifact_filename_pattern": "*20260925*.txt",
        "title": "Magic: The Gathering Comprehensive Rules", "rule_reference": "701.71",
        "rule_heading": "Empower Jace",
    },
    FICTIONAL_PROFILE_VERSION: {
        "game_id": "fictional-source-contract", "effective_date": "2032-03-14",
        "artifact_family": "20320314", "artifact_filename_pattern": "*20320314*.txt",
        "title": "Fictional Duel Comprehensive Rules", "rule_reference": "fictional.71",
        "rule_heading": "Empower Beacon",
    },
}
VERIFICATION_STATUSES = frozenset({
    "VERIFIED_EXPECTED_ARTIFACT", "HASH_MISMATCH", "WRONG_EFFECTIVE_DATE",
    "MISSING_EXPECTED_MARKER", "WRONG_MEDIA_TYPE", "ARTIFACT_TOO_LARGE",
    "MALFORMED_TEXT", "UNSUPPORTED_ARTIFACT_TYPE", "WRONG_ARTIFACT_REFERENCE",
    "ARTIFACT_UNAVAILABLE", "ARTIFACT_CHANGED_DURING_VERIFICATION",
})


def _profile(version):
    if version not in _PROFILES:
        _fail("verification_profile_version", "unsupported verification profile")
    result = dict(_PROFILES[version])
    year, month, day = map(int, result["effective_date"].split("-"))
    result.update({"verification_profile_version": version, "artifact_type": "TXT",
                   "encoding": "UTF-8", "max_bytes": _MAX_BYTES,
                   "effective_date_marker": f"{_MONTHS[month - 1]} {day}, {year}"})
    result["verification_profile_id"] = "sha256:" + sha256_identity({
        "domain": "gameplay-rules-artifact-verification-profile-v1", "content": result})
    return result


def _markers(profile):
    return [{"marker_id": name, "value": profile[name]} for name in
            ("title", "effective_date_marker", "rule_reference", "rule_heading")]


def _request(body):
    _keys(body, {"game_id", "release_candidate_id", "discovery_source_reference_id", "observation_id",
                 "effective_date", "artifact_family", "artifact_filename_pattern", "artifact_type",
                 "verification_profile_version", "verification_profile_id", "required_markers", "max_bytes",
                 "expected_artifact_hash", "content_retained", "source_body_copy_allowed", *_REQUEST_HANDOFF}, "artifact_request")
    profile = _profile(body["verification_profile_version"])
    for field in ("game_id", "effective_date", "artifact_family", "artifact_filename_pattern", "artifact_type",
                  "verification_profile_id", "max_bytes"):
        if type(body[field]) is not type(profile[field]) or body[field] != profile[field]:
            _fail(field, "verification request does not match immutable profile")
    for field in ("release_candidate_id", "discovery_source_reference_id", "observation_id"):
        _hash(body[field], field)
    _hash(body["expected_artifact_hash"], "expected_artifact_hash", nullable=True)
    if body["required_markers"] != _markers(profile):
        _fail("required_markers", "verification markers differ from immutable profile")
    for field, expected in _REQUEST_HANDOFF.items():
        if body[field] != expected:
            _fail(field, "unsupported verifier handoff contract")
    for field in ("content_retained", "source_body_copy_allowed"):
        if body[field] is not False:
            _fail(field, "source retention is forbidden")


@dataclass(frozen=True)
class ArtifactVerificationRequest(MetadataContract):
    SCHEMA = "gameplay-rules-artifact-verification-request-v1"
    ID_FIELD = "artifact_verification_request_id"
    VALIDATOR = staticmethod(_request)


def build_artifact_verification_request(*, game_id, release_candidate_id,
                                        discovery_source_reference_id, observation_id,
                                        verification_profile_version=REAL_PROFILE_VERSION,
                                        expected_artifact_hash=None):
    """Author control metadata, never infer a release or filename from disk."""
    profile = _profile(verification_profile_version)
    return ArtifactVerificationRequest.create({
        "game_id": game_id, "release_candidate_id": release_candidate_id,
        "discovery_source_reference_id": discovery_source_reference_id, "observation_id": observation_id,
        **{name: profile[name] for name in ("effective_date", "artifact_family", "artifact_filename_pattern",
                                            "artifact_type", "verification_profile_version",
                                            "verification_profile_id", "max_bytes")},
        "required_markers": _markers(profile), "expected_artifact_hash": expected_artifact_hash,
        "content_retained": False, "source_body_copy_allowed": False,
        **_REQUEST_HANDOFF,
    })


def _result(body):
    _keys(body, {"game_id", "request_id", "release_candidate_id", "discovery_source_reference_id", "observation_id",
                 "verification_profile_version", "verification_profile_id", "artifact_reference", "artifact_type",
                 "status", "artifact_hash", "byte_length", "effective_date", "encoding", "checked_markers",
                 "observed_at", "independent_verification_status", "content_retained", "source_body_copied",
                 "network_used"}, "artifact_verification_result")
    profile = _profile(body["verification_profile_version"])
    for name in ("game_id", "verification_profile_id", "artifact_type"):
        if body[name] != profile[name]: _fail(name, "verification profile mismatch")
    if body["artifact_reference"] != profile["artifact_filename_pattern"]:
        _fail("artifact_reference", "declared filename pattern required; no local path retained")
    for name in ("request_id", "release_candidate_id", "discovery_source_reference_id", "observation_id"):
        _hash(body[name], name)
    _enum(body["status"], VERIFICATION_STATUSES, "status")
    _hash(body["artifact_hash"], "artifact_hash", nullable=True)
    _int(body["byte_length"], "byte_length", nullable=True)
    if (body["artifact_hash"] is None) != (body["byte_length"] is None):
        _fail("artifact_hash", "complete observed hash and length must be paired")
    _date(body["effective_date"], "effective_date", nullable=True)
    _timestamp(body["observed_at"], "observed_at", nullable=True)
    if body["encoding"] not in {None, "UTF-8"}: _fail("encoding", "unsupported encoding")
    markers = body["checked_markers"]
    if not isinstance(markers, list) or len(markers) != 4: _fail("checked_markers", "exact bounded markers required")
    for record, expected in zip(markers, _markers(profile)):
        _keys(record, {"marker_id", "matched"}, "checked_marker")
        if record["marker_id"] != expected["marker_id"] or type(record["matched"]) is not bool:
            _fail("checked_marker", "unexpected bounded marker")
    verified = body["status"] == "VERIFIED_EXPECTED_ARTIFACT"
    expected_status = "ARTIFACT_BYTES_VERIFIED_LOCALLY" if verified else "NOT_VERIFIED"
    if body["independent_verification_status"] != expected_status:
        _fail("independent_verification_status", "verification result contradiction")
    if verified and (body["artifact_hash"] is None or not body["byte_length"] or
                     body["effective_date"] != profile["effective_date"] or body["encoding"] != "UTF-8" or
                     not all(record["matched"] for record in markers)):
        _fail("status", "success requires exact observed bytes and all expected markers")
    for name in ("content_retained", "source_body_copied", "network_used"):
        if body[name] is not False: _fail(name, "offline metadata-only verification boundary")


@dataclass(frozen=True)
class ArtifactVerificationResult(MetadataContract):
    SCHEMA = "gameplay-rules-artifact-verification-result-v1"
    ID_FIELD = "artifact_verification_result_id"
    VALIDATOR = staticmethod(_result)


def _open_regular_no_symlinks(path):
    """Open each component relative to a pinned directory; refuse symlink races."""
    try:
        raw = os.fspath(path)
    except TypeError:
        raise GameplayContractError("artifact_input_boundary", "explicit local file path required") from None
    if (not isinstance(raw, str) or not raw or "\\" in raw or "//" in raw or
            any(ord(char) < 32 or ord(char) == 127 for char in raw)):
        raise GameplayContractError("artifact_input_boundary", "unambiguous local file path required")
    components = raw.split("/")
    if raw.startswith("/"): components = components[1:]
    if not components or any(component in {"", ".", ".."} for component in components):
        raise GameplayContractError("artifact_input_boundary", "path traversal and empty components forbidden")
    nofollow = getattr(os, "O_NOFOLLOW", None)
    if nofollow is None:
        raise GameplayContractError("artifact_input_boundary", "safe local file opening unavailable")
    directory = os.open("/" if raw.startswith("/") else ".", os.O_RDONLY | os.O_DIRECTORY)
    try:
        for component in components[:-1]:
            try:
                following = os.open(component, os.O_RDONLY | os.O_DIRECTORY | nofollow, dir_fd=directory)
            except FileNotFoundError:
                return None
            except OSError:
                raise GameplayContractError("artifact_input_boundary", "unsafe directory component") from None
            os.close(directory)
            directory = following
        try:
            descriptor = os.open(components[-1], os.O_RDONLY | nofollow | os.O_NONBLOCK, dir_fd=directory)
        except FileNotFoundError:
            return None
        except OSError:
            raise GameplayContractError("artifact_input_boundary", "unsafe local file input") from None
        if not stat.S_ISREG(os.fstat(descriptor).st_mode):
            os.close(descriptor)
            raise GameplayContractError("artifact_input_boundary", "regular local file required")
        return descriptor
    finally:
        os.close(directory)


def verify_local_artifact(path, request, *, expected_request_id, expected_release_candidate_id,
                          expected_discovery_source_reference_id, game_id, observed_at=None):
    """Inspect explicitly pinned local bytes, returning metadata without copying.

    Context pins are mandatory: a stale or substituted request cannot silently
    select another release. An evidence reviewer must separately validate the
    supplied context against its observation/candidate records.
    """
    if not isinstance(request, ArtifactVerificationRequest):
        raise GameplayContractError("artifact_request_binding", "verified request contract required")
    request.verify()
    for field, expected in (("identity", expected_request_id), ("release_candidate_id", expected_release_candidate_id),
                            ("discovery_source_reference_id", expected_discovery_source_reference_id),
                            ("game_id", game_id)):
        if getattr(request, field) != expected:
            raise GameplayContractError("artifact_request_binding", "explicit selected context differs from request")
    _timestamp(observed_at, "observed_at", nullable=True)
    profile = _profile(request.verification_profile_version)
    matched = {record["marker_id"]: False for record in _markers(profile)}

    def result(status, *, digest=None, length=None, effective_date=None, encoding=None):
        return ArtifactVerificationResult.create({
            "game_id": request.game_id, "request_id": request.identity,
            "release_candidate_id": request.release_candidate_id,
            "discovery_source_reference_id": request.discovery_source_reference_id, "observation_id": request.observation_id,
            "verification_profile_version": request.verification_profile_version,
            "verification_profile_id": request.verification_profile_id,
            "artifact_reference": request.artifact_filename_pattern, "artifact_type": "TXT", "status": status,
            "artifact_hash": digest, "byte_length": length, "effective_date": effective_date, "encoding": encoding,
            "checked_markers": [{"marker_id": name, "matched": value} for name, value in matched.items()],
            "observed_at": observed_at,
            "independent_verification_status": "ARTIFACT_BYTES_VERIFIED_LOCALLY" if status == "VERIFIED_EXPECTED_ARTIFACT" else "NOT_VERIFIED",
            "content_retained": False, "source_body_copied": False, "network_used": False,
        })

    # Validate the input boundary even when extension/type would otherwise fail.
    descriptor = _open_regular_no_symlinks(path)
    if descriptor is None: return result("ARTIFACT_UNAVAILABLE")
    with os.fdopen(descriptor, "rb", closefd=True) as source:
        before = os.fstat(source.fileno())
        if Path(os.fspath(path)).suffix.lower() != ".txt": return result("UNSUPPORTED_ARTIFACT_TYPE")
        if not fnmatch.fnmatchcase(Path(os.fspath(path)).name, profile["artifact_filename_pattern"]):
            return result("WRONG_ARTIFACT_REFERENCE")
        if before.st_size > profile["max_bytes"]: return result("ARTIFACT_TOO_LARGE")
        digest, length = hashlib.sha256(), 0
        decoder = codecs.getincrementaldecoder("utf-8-sig")("strict")
        tail = ""
        tail_starts_at_line_boundary = True
        dates = set()
        malformed = wrong_media = False
        first = True
        date_pattern = re.compile(r"\beffective\s+as\s+of\s+(" + "|".join(_MONTHS) + r")\s+([0-9]{1,2}),\s+([0-9]{4})\b", re.IGNORECASE)
        rule_pattern = re.compile(r"(?m)^[ \t]*" + re.escape(profile["rule_reference"]) +
                                  r"\.?(?:[ \t]+|[ \t]*\r?\n[ \t]*)" + re.escape(profile["rule_heading"]) + r"\b")

        def inspect(text):
            nonlocal tail, tail_starts_at_line_boundary, malformed
            if any((ord(char) < 32 and char not in "\r\n\t") or ord(char) == 127 for char in text):
                malformed = True
            window = tail + text
            matched["title"] |= profile["title"] in window
            for match in date_pattern.finditer(window):
                month, day, year = match.groups()
                month_number = next(index for index, name in enumerate(_MONTHS, 1) if name.lower() == month.lower())
                value = f"{int(year):04}-{month_number:02}-{int(day):02}"
                try: _date(value, "observed_effective_date")
                except GameplayContractError: malformed = True
                else: dates.add(value)
            # A truncated search tail must not manufacture a new line start.
            rule_window = window if tail_starts_at_line_boundary else "\uffff" + window
            if rule_pattern.search(rule_window):
                matched["rule_reference"] = matched["rule_heading"] = True
            # Retain only an in-memory bounded search window, never source lines.
            cut = max(0, len(window) - 512)
            if cut:
                tail_starts_at_line_boundary = window[cut - 1] in "\r\n"
            tail = window[cut:]

        while True:
            chunk = source.read(min(_CHUNK_BYTES, profile["max_bytes"] + 1 - length))
            if not chunk: break
            if first:
                wrong_media = chunk.startswith((b"%PDF-", b"PK\x03\x04", b"\xff\xfe", b"\xfe\xff"))
                first = False
            digest.update(chunk)
            length += len(chunk)
            if length > profile["max_bytes"]: return result("ARTIFACT_TOO_LARGE")
            try: inspect(decoder.decode(chunk, final=False))
            except UnicodeError: malformed = True
        try: inspect(decoder.decode(b"", final=True))
        except UnicodeError: malformed = True
        after = os.fstat(source.fileno())
        exact_hash = "sha256:" + digest.hexdigest()
        if (before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns, before.st_ctime_ns) != (
                after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns, after.st_ctime_ns) or length != after.st_size:
            return result("ARTIFACT_CHANGED_DURING_VERIFICATION", digest=exact_hash, length=length)
        if wrong_media: return result("WRONG_MEDIA_TYPE", digest=exact_hash, length=length)
        if malformed: return result("MALFORMED_TEXT", digest=exact_hash, length=length)
        actual_date = next(iter(dates)) if len(dates) == 1 else None
        matched["effective_date_marker"] = dates == {profile["effective_date"]}
        if dates and not matched["effective_date_marker"]:
            return result("WRONG_EFFECTIVE_DATE", digest=exact_hash, length=length, effective_date=actual_date, encoding="UTF-8")
        if not all(matched.values()):
            return result("MISSING_EXPECTED_MARKER", digest=exact_hash, length=length, effective_date=actual_date, encoding="UTF-8")
        if request.expected_artifact_hash is not None and exact_hash != request.expected_artifact_hash:
            return result("HASH_MISMATCH", digest=exact_hash, length=length, effective_date=actual_date, encoding="UTF-8")
        return result("VERIFIED_EXPECTED_ARTIFACT", digest=exact_hash, length=length, effective_date=actual_date, encoding="UTF-8")
