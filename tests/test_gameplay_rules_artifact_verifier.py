"""Offline verifier tests use only short, project-authored fictional text."""
from __future__ import annotations

from dataclasses import FrozenInstanceError
import hashlib
import io
import json
import os
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from gameplay_rules.errors import GameplayContractError
from gameplay_rules.source_evidence.artifacts import (
    ArtifactVerificationRequest, ArtifactVerificationResult,
    FICTIONAL_PROFILE_VERSION, REAL_PROFILE_VERSION,
    build_artifact_verification_request, verify_local_artifact,
)
from gameplay_rules.source_evidence.verify import main


FICTIONAL_TEXT = (
    "Fictional Duel Comprehensive Rules\n"
    "These project-authored fictional rules are effective as of March 14, 2032.\n"
    "fictional.71. Empower Beacon\n"
    "This deliberately tiny test document is not official rules or a usable rules corpus.\n"
).encode("utf-8")
_CANDIDATE = "sha256:" + "1" * 64
_SOURCE = "sha256:" + "2" * 64
_OBSERVATION = "sha256:" + "3" * 64
_OTHER = "sha256:" + "4" * 64


def fictional_request(**changes):
    return build_artifact_verification_request(
        game_id="fictional-source-contract", release_candidate_id=_CANDIDATE,
        discovery_source_reference_id=_SOURCE, observation_id=_OBSERVATION,
        verification_profile_version=FICTIONAL_PROFILE_VERSION, **changes)


class GameplayRulesArtifactVerifierTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="mtglab-fictional-txt-")
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.path = self.root / "fictional-20320314.txt"
        self.path.write_bytes(FICTIONAL_TEXT)
        self.request = fictional_request()

    def verify(self, path=None, request=None, **changes):
        request = self.request if request is None else request
        context = dict(expected_request_id=request.identity, expected_release_candidate_id=_CANDIDATE,
                       expected_discovery_source_reference_id=_SOURCE, game_id="fictional-source-contract")
        context.update(changes)
        return verify_local_artifact(self.path if path is None else path, request, **context)

    def test_exact_fictional_bytes_verify_hash_and_length(self):
        result = self.verify()
        self.assertEqual(result.status, "VERIFIED_EXPECTED_ARTIFACT")
        self.assertEqual(result.artifact_hash, "sha256:" + hashlib.sha256(FICTIONAL_TEXT).hexdigest())
        self.assertEqual(result.byte_length, len(FICTIONAL_TEXT))
        self.assertEqual(result.effective_date, "2032-03-14")
        self.assertTrue(all(marker["matched"] for marker in result.checked_markers))

    def test_same_bytes_and_request_have_same_identity_without_wall_clock(self):
        first, second = self.verify(), self.verify()
        self.assertEqual(first.identity, second.identity)
        self.assertIsNone(first.observed_at)

    def test_relocation_changes_neither_identity_nor_semantics(self):
        relocated = self.root / "relocated"
        relocated.mkdir()
        other = relocated / self.path.name
        other.write_bytes(FICTIONAL_TEXT)
        self.assertEqual(self.verify().to_dict(), self.verify(path=other).to_dict())

    def test_changed_bytes_change_hash_and_result_identity(self):
        old = self.verify()
        self.path.write_bytes(FICTIONAL_TEXT + b"Another original fictional note.\n")
        new = self.verify()
        self.assertEqual(new.status, "VERIFIED_EXPECTED_ARTIFACT")
        self.assertNotEqual(old.artifact_hash, new.artifact_hash)
        self.assertNotEqual(old.identity, new.identity)

    def test_request_is_immutable_and_integrity_bound(self):
        with self.assertRaises((FrozenInstanceError, AttributeError, TypeError)):
            self.request._payload = {}
        payload = self.request.to_dict()
        payload["effective_date"] = "2032-03-15"
        with self.assertRaises(GameplayContractError): ArtifactVerificationRequest.from_dict(payload)

    def test_result_is_immutable_and_defensive(self):
        result = self.verify()
        payload = result.to_dict()
        payload["checked_markers"][0]["matched"] = False
        self.assertTrue(result.checked_markers[0]["matched"])
        with self.assertRaises(GameplayContractError): ArtifactVerificationResult.from_dict(payload)

    def test_result_is_metadata_only_and_not_projection_authority(self):
        result = self.verify()
        self.assertEqual(result.independent_verification_status, "ARTIFACT_BYTES_VERIFIED_LOCALLY")
        for field in ("content_retained", "source_body_copied", "network_used", "projection_authorized", "admission_eligible"):
            self.assertIs(getattr(result, field), False)
        encoded = json.dumps(result.to_dict())
        self.assertNotIn(str(self.root), encoded)
        self.assertNotIn(FICTIONAL_TEXT.decode(), encoded)
        self.assertNotIn("source_body", {key for key in result.to_dict() if key != "source_body_copied"})

    def test_explicit_observation_time_is_retained_input(self):
        result = self.verify(observed_at="2032-03-15T01:02:03Z")
        self.assertEqual(result.observed_at, "2032-03-15T01:02:03Z")
        self.assertNotEqual(result.identity, self.verify().identity)

    def test_title_required(self):
        self.path.write_bytes(FICTIONAL_TEXT.replace(b"Fictional Duel Comprehensive Rules", b"Fictional alternative"))
        self.assertEqual(self.verify().status, "MISSING_EXPECTED_MARKER")

    def test_effective_date_required(self):
        self.path.write_bytes(FICTIONAL_TEXT.replace(b"effective as of", b"authored on"))
        self.assertEqual(self.verify().status, "MISSING_EXPECTED_MARKER")

    def test_wrong_effective_date_is_explicit(self):
        self.path.write_bytes(FICTIONAL_TEXT.replace(b"March 14, 2032", b"March 15, 2032"))
        self.assertEqual(self.verify().status, "WRONG_EFFECTIVE_DATE")

    def test_multiple_conflicting_effective_dates_do_not_pass(self):
        self.path.write_bytes(FICTIONAL_TEXT + b"This draft is effective as of March 15, 2032.\n")
        self.assertEqual(self.verify().status, "WRONG_EFFECTIVE_DATE")

    def test_rule_marker_required_and_heading_must_be_bound(self):
        for replacement in (b"fictional.710. Empower Beacon", b"xfictional.71. Empower Beacon",
                            b"fictional.71. Another heading\nEmpower Beacon elsewhere"):
            with self.subTest(replacement=replacement):
                self.path.write_bytes(FICTIONAL_TEXT.replace(b"fictional.71. Empower Beacon", replacement))
                self.assertEqual(self.verify().status, "MISSING_EXPECTED_MARKER")

    def test_required_marker_can_cross_stream_boundary(self):
        prefix = b"X" * (64 * 1024 - 10) + b"\n"
        self.path.write_bytes(prefix + FICTIONAL_TEXT)
        self.assertEqual(self.verify().status, "VERIFIED_EXPECTED_ARTIFACT")

    def test_stream_tail_does_not_manufacture_rule_line_boundary(self):
        header = FICTIONAL_TEXT.split(b"fictional.71.")[0]
        offset = 64 * 1024 - 512
        # The marker is deliberately embedded in a long non-rule line. The
        # second read's bounded tail starts exactly at that embedded marker.
        body = header + b"x" * (offset - len(header)) + b"fictional.71. Empower Beacon\n"
        self.path.write_bytes(body + b"x" * (64 * 1024 - len(body)) + b"more fictional bytes\n")
        self.assertEqual(self.verify().status, "MISSING_EXPECTED_MARKER")

    def test_utf8_bom_allowed_exact_bytes_still_hashed(self):
        body = b"\xef\xbb\xbf" + FICTIONAL_TEXT
        self.path.write_bytes(body)
        self.assertEqual(self.verify().artifact_hash, "sha256:" + hashlib.sha256(body).hexdigest())

    def test_invalid_encoding_and_control_characters_fail(self):
        for body in (FICTIONAL_TEXT + b"\xff", FICTIONAL_TEXT + b"\x00", FICTIONAL_TEXT + b"\x01"):
            with self.subTest(body=body[-1:]):
                self.path.write_bytes(body)
                self.assertEqual(self.verify().status, "MALFORMED_TEXT")

    def test_binary_media_disguised_as_txt_is_not_text(self):
        self.path.write_bytes(b"%PDF-1.7\n" + FICTIONAL_TEXT)
        self.assertEqual(self.verify().status, "WRONG_MEDIA_TYPE")

    def test_non_txt_type_is_unsupported(self):
        path = self.root / "fictional-20320314.pdf"
        path.write_bytes(FICTIONAL_TEXT)
        self.assertEqual(self.verify(path=path).status, "UNSUPPORTED_ARTIFACT_TYPE")

    def test_wrong_filename_family_is_explicit(self):
        path = self.root / "fictional-20320315.txt"
        path.write_bytes(FICTIONAL_TEXT)
        self.assertEqual(self.verify(path=path).status, "WRONG_ARTIFACT_REFERENCE")

    def test_missing_file_is_structured(self):
        self.assertEqual(self.verify(path=self.root / "missing-20320314.txt").status, "ARTIFACT_UNAVAILABLE")

    def test_oversized_file_rejected_before_read(self):
        with self.path.open("wb") as stream: stream.truncate(self.request.max_bytes + 1)
        self.assertEqual(self.verify().status, "ARTIFACT_TOO_LARGE")

    def test_expected_hash_mismatch_keeps_observed_exact_hash(self):
        request = fictional_request(expected_artifact_hash=_OTHER)
        result = self.verify(request=request)
        self.assertEqual(result.status, "HASH_MISMATCH")
        self.assertEqual(result.artifact_hash, "sha256:" + hashlib.sha256(FICTIONAL_TEXT).hexdigest())

    def test_plain_dict_cannot_masquerade_as_verified_request(self):
        with self.assertRaises(GameplayContractError):
            verify_local_artifact(self.path, self.request.to_dict(), expected_request_id=self.request.identity,
                                  expected_release_candidate_id=_CANDIDATE,
                                  expected_discovery_source_reference_id=_SOURCE, game_id="fictional-source-contract")

    def test_stale_or_changed_context_rejected_before_local_io(self):
        for change in ({"expected_request_id": _OTHER}, {"expected_release_candidate_id": _OTHER},
                       {"expected_discovery_source_reference_id": _OTHER}, {"game_id": "another-game"}):
            with self.subTest(change=change), patch("gameplay_rules.source_evidence.artifacts._open_regular_no_symlinks", side_effect=AssertionError("unexpected I/O")):
                with self.assertRaises(GameplayContractError): self.verify(**change)

    def test_altered_profile_or_markers_cannot_be_rehashed_into_acceptance(self):
        for field, value in (("verification_profile_version", "unreviewed-v1"), ("verification_profile_id", _OTHER),
                             ("max_bytes", self.request.max_bytes + 1), ("content_retained", True),
                             ("artifact_filename_pattern", "*.txt")):
            payload = self.request.to_dict()
            for envelope in ("artifact_verification_request_id", "schema_version", "metadata_only", "admission_eligible", "projection_authorized"):
                payload.pop(envelope)
            payload[field] = value
            with self.subTest(field=field), self.assertRaises(GameplayContractError): ArtifactVerificationRequest.create(payload)

    def test_real_profile_is_fixed_metadata_without_actual_artifact(self):
        request = build_artifact_verification_request(game_id="magic", release_candidate_id=_CANDIDATE,
                                                     discovery_source_reference_id=_SOURCE, observation_id=_OBSERVATION)
        self.assertEqual(request.verification_profile_version, REAL_PROFILE_VERSION)
        self.assertEqual(request.effective_date, "2026-09-25")
        self.assertEqual(request.artifact_family, "20260925")
        self.assertEqual(request.artifact_filename_pattern, "*20260925*.txt")
        self.assertEqual({record["value"] for record in request.required_markers}, {
            "Magic: The Gathering Comprehensive Rules", "September 25, 2026", "701.71", "Empower Jace"})
        self.assertIsNone(request.expected_artifact_hash)

    def test_request_identifies_exact_verifier_and_result_contract(self):
        self.assertEqual(self.request.verifier_module, "gameplay_rules.source_evidence.verify")
        self.assertEqual(self.request.verifier_api, "gameplay_rules.source_evidence.artifacts.verify_local_artifact")
        self.assertEqual(self.request.result_schema_version, ArtifactVerificationResult.SCHEMA)
        payload = self.request.to_dict()
        for envelope in ("artifact_verification_request_id", "schema_version", "metadata_only", "admission_eligible", "projection_authorized"):
            payload.pop(envelope)
        payload["verifier_module"] = "another.module"
        with self.assertRaises(GameplayContractError): ArtifactVerificationRequest.create(payload)

    def test_symlink_file_and_symlink_ancestor_rejected(self):
        link = self.root / "linked-20320314.txt"
        link.symlink_to(self.path)
        directory_link = self.root / "directory-link"
        actual = self.root / "actual"
        actual.mkdir()
        (actual / self.path.name).write_bytes(FICTIONAL_TEXT)
        directory_link.symlink_to(actual, target_is_directory=True)
        for path in (link, directory_link / self.path.name):
            with self.subTest(path=path), self.assertRaises(GameplayContractError): self.verify(path=path)

    def test_non_regular_input_rejected_without_blocking(self):
        fifo = self.root / "pipe-20320314.txt"
        os.mkfifo(fifo)
        for path in (self.root, fifo):
            with self.subTest(path=path), self.assertRaises(GameplayContractError): self.verify(path=path)

    def test_ambiguous_paths_fail_without_exposing_path(self):
        for path in (str(self.root) + "/../escape.txt", str(self.root) + "/./fictional-20320314.txt",
                     str(self.root) + "//fictional-20320314.txt", "bad\\path.txt", "bad\x00path.txt", "bad\npath.txt"):
            with self.subTest(path=repr(path)), self.assertRaises(GameplayContractError) as raised:
                self.verify(path=path)
            self.assertNotIn(str(self.root), str(raised.exception))

    def test_no_network_rawstore_or_filesystem_writes(self):
        before = {path.name: path.read_bytes() for path in self.root.iterdir()}
        original_open = os.open
        open_flags = []

        def read_only_open(path, flags, *args, **kwargs):
            open_flags.append(flags)
            return original_open(path, flags, *args, **kwargs)

        with patch("socket.socket", side_effect=AssertionError("network forbidden")), \
             patch("acquisition.framework.RawSnapshotStore.store", side_effect=AssertionError("raw retention forbidden")), \
             patch("os.open", side_effect=read_only_open), \
             patch("pathlib.Path.write_bytes", side_effect=AssertionError("body copy forbidden")), \
             patch("pathlib.Path.write_text", side_effect=AssertionError("body copy forbidden")):
            self.assertEqual(self.verify().status, "VERIFIED_EXPECTED_ARTIFACT")
        self.assertTrue(open_flags)
        self.assertTrue(all(not flags & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC) for flags in open_flags))
        self.assertEqual(before, {path.name: path.read_bytes() for path in self.root.iterdir()})

    def test_input_drift_during_verification_is_not_success(self):
        original_fstat = os.fstat
        calls = 0

        def changed_stat(descriptor):
            nonlocal calls
            calls += 1
            record = original_fstat(descriptor)
            if calls != 3:
                return record
            return SimpleNamespace(st_dev=record.st_dev, st_ino=record.st_ino, st_size=record.st_size,
                                   st_mtime_ns=record.st_mtime_ns + 1, st_ctime_ns=record.st_ctime_ns)

        with patch("os.fstat", side_effect=changed_stat):
            self.assertEqual(self.verify().status, "ARTIFACT_CHANGED_DURING_VERIFICATION")

    def test_cli_emits_only_metadata_and_requires_explicit_context(self):
        request_path = self.root / "request.json"
        request_path.write_text(json.dumps(self.request.to_dict()), encoding="utf-8")
        arguments = [str(self.path), "--request", str(request_path), "--expected-request-id", self.request.identity,
                     "--release-candidate-id", _CANDIDATE, "--discovery-source-reference-id", _SOURCE,
                     "--game-id", "fictional-source-contract"]
        output = io.StringIO()
        with patch("sys.stdout", output): exit_status = main(arguments)
        self.assertEqual(exit_status, 0)
        result = ArtifactVerificationResult.from_json(output.getvalue())
        self.assertEqual(result.identity, self.verify().identity)
        self.assertNotIn(str(self.root), output.getvalue())

    def test_cli_blocked_context_does_not_leak_path_or_content(self):
        request_path = self.root / "request.json"
        request_path.write_text(json.dumps(self.request.to_dict()), encoding="utf-8")
        arguments = [str(self.path), "--request", str(request_path), "--expected-request-id", _OTHER,
                     "--release-candidate-id", _CANDIDATE, "--discovery-source-reference-id", _SOURCE,
                     "--game-id", "fictional-source-contract"]
        output = io.StringIO()
        with patch("sys.stdout", output): self.assertEqual(main(arguments), 2)
        self.assertNotIn(str(self.root), output.getvalue())
        self.assertEqual(json.loads(output.getvalue())["error"], "ARTIFACT_VERIFICATION_BLOCKED")


if __name__ == "__main__":
    unittest.main()
