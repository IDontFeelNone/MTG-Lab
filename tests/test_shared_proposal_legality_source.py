"""E-only original-byte boundaries; invented fixtures have no source authority."""
import hashlib
import os
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch

from gameplay_rules.errors import GameplayContractError
from gameplay_rules.projection.contracts import _json
from gameplay_rules.shared_proposal_legality.contracts import create_projection
from gameplay_rules.shared_proposal_legality import source
from gameplay_rules.shared_proposal_legality.source import (
    SOURCE_ENV, VERIFIED_ANCHORS, anchor_identity, locate_anchors,
    validate_spans, verify_bytes, verified_anchors,
)

ROOT = Path(__file__).resolve().parents[1]


def fictional_source(terminator=b"\n"):
    return terminator * 2471 + terminator.join((
        b"601.2e invented checkpoint fixture with recovery reference 733", b"\xc2\xa0",
        b"601.2f arbitrary uninspected body",
    ))


class SharedProposalLegalitySourceTests(unittest.TestCase):
    def test_complete_raw_unit_excludes_terminator_separator_and_following_marker(self):
        for terminator in (b"\n", b"\r\n", b"\r"):
            with self.subTest(terminator=terminator):
                raw = fictional_source(terminator)
                anchor = locate_anchors(raw)[0]
                block = raw[anchor["byte_start"]:anchor["byte_end"]]
                self.assertEqual(block, b"601.2e invented checkpoint fixture with recovery reference 733")
                self.assertEqual(anchor["byte_start"], 2471 * len(terminator))
                self.assertEqual(raw[anchor["byte_end"]:anchor["byte_end"] + len(terminator)], terminator)
                self.assertEqual(anchor["line_count"], 1)
                self.assertEqual(anchor["owned_example_line_count"], 0)
                self.assertEqual(anchor["starting_physical_line"], 2472)
                self.assertEqual(anchor["ending_physical_line"], 2472)
                self.assertEqual(anchor["span_length"], len(block))
                self.assertEqual(anchor["span_sha256"], "sha256:" + hashlib.sha256(block).hexdigest())
                self.assertEqual(anchor["anchor_id"], anchor_identity(anchor))

    def test_mixed_original_terminators_preserve_exact_byte_offsets(self):
        raw = b"\r\n" * 2471 + b"601.2e invented checkpoint fixture with recovery reference 733\r\xc2\xa0\n601.2f ignored"
        anchor = locate_anchors(raw)[0]
        self.assertEqual(anchor["byte_start"], 4942)
        self.assertEqual(raw[anchor["byte_start"]:anchor["byte_end"]], b"601.2e invented checkpoint fixture with recovery reference 733")
        self.assertEqual(anchor["following_marker"]["physical_line"], 2474)

    def test_extra_owned_example_continuation_or_separator_change_stops(self):
        for raw in (
            fictional_source().replace(b"\xc2\xa0\n", b"Example: invented extra\n\xc2\xa0\n"),
            fictional_source().replace(b"\xc2\xa0\n", b"invented continuation\n\xc2\xa0\n"),
            fictional_source().replace(b"\xc2\xa0", b" "),
            fictional_source().replace(b"\xc2\xa0\n", b""),
        ):
            with self.subTest(size=len(raw)), self.assertRaisesRegex(
                    GameplayContractError, "SHARED_PROPOSAL_LEGALITY_SCOPE_INSUFFICIENT"):
                locate_anchors(raw)

    def test_wrong_scope_or_following_markers_and_numbered_citations_stop(self):
        for raw in (
            fictional_source().replace(b"601.2e ", b"601.2c "),
            fictional_source().replace(b"601.2e ", b"601.2e. "),
            fictional_source().replace(b"601.2f ", b"601.2f. "),
            fictional_source().replace(b"601.2f ", b"601.2i "),
            fictional_source().replace(b"invented checkpoint fixture with recovery reference 733", b"invented checkpoint fixture with recovery reference 603"),
            fictional_source().replace(b"invented checkpoint fixture with recovery reference 733", b"invented checkpoint fixture with recovery reference 733 and 601.2b-601.2i"),
        ):
            with self.subTest(size=len(raw)), self.assertRaisesRegex(
                    GameplayContractError, "SHARED_PROPOSAL_LEGALITY_SCOPE_INSUFFICIENT"):
                locate_anchors(raw)

    def test_recovery_citation_is_required_exactly_once_and_no_numbered_range_is_admitted(self):
        for replacement in (b"invented checkpoint without citation", b"invented 733a citation",
                            b"invented 733.1 citation", b"invented 733 and 733 citations",
                            b"invented 733-734 range", b"invented 733 to 734 range",
                            b"invented 733 and 601.2f citation", b"invented 733 and 115.6 citation"):
            changed = fictional_source().replace(
                b"invented checkpoint fixture with recovery reference 733", replacement)
            with self.subTest(replacement=replacement), self.assertRaisesRegex(
                    GameplayContractError, "SHARED_PROPOSAL_LEGALITY_SCOPE_INSUFFICIENT"):
                locate_anchors(changed)

    def test_following_body_and_all_other_bodies_are_not_content_inspected(self):
        raw = fictional_source()
        changed = raw.replace(b"arbitrary uninspected body", b"603 733 601.2i changed neighboring content")
        changed = changed.replace(b"\n", b"601.2c 603 ignored\n", 1)
        before, after = locate_anchors(raw)[0], locate_anchors(changed)[0]
        for field in ("line_count", "span_sha256", "span_length", "owned_example_line_count"):
            self.assertEqual(before[field], after[field])
        self.assertFalse(after["following_marker"]["body_inspected"])
        # An f marker alone establishes the boundary; its body need not exist.
        prefix_only = raw[:raw.index(b"601.2f ") + 7]
        self.assertEqual(locate_anchors(prefix_only)[0]["span_sha256"], before["span_sha256"])

    def test_synthetic_structure_never_establishes_real_source_or_projection(self):
        with self.assertRaisesRegex(GameplayContractError, "VERIFIED_SOURCE_ARTIFACT_MISMATCH"):
            verify_bytes(fictional_source())
        with self.assertRaises(GameplayContractError):
            create_projection(locate_anchors(fictional_source()))

    def test_wrong_artifact_fails_before_any_body_inspection(self):
        with patch.object(source, "locate_anchors") as locate:
            with self.assertRaisesRegex(GameplayContractError, "VERIFIED_SOURCE_ARTIFACT_MISMATCH"):
                verify_bytes(fictional_source())
            locate.assert_not_called()

    def test_structurally_valid_but_wrong_fingerprint_fails_even_after_artifact_mock(self):
        raw = fictional_source()
        with patch.object(source, "ARTIFACT_BYTE_LENGTH", len(raw)), patch.object(
                source, "ARTIFACT_HASH", "sha256:" + hashlib.sha256(raw).hexdigest()):
            with self.assertRaisesRegex(GameplayContractError, "SHARED_PROPOSAL_LEGALITY_SCOPE_INSUFFICIENT"):
                verify_bytes(raw)

    def test_nonbytes_empty_truncated_and_missing_following_marker_rejected(self):
        for invalid in (None, True, 1, 1.0, "invented", bytearray(b"invented"), b"", b"601.2e invented"):
            with self.subTest(kind=type(invalid)), self.assertRaises(GameplayContractError):
                verify_bytes(invalid)
            with self.subTest(kind=type(invalid)), self.assertRaises(GameplayContractError):
                locate_anchors(invalid)
        for raw in (fictional_source()[:fictional_source().index(b"\xc2\xa0")],
                    fictional_source()[:fictional_source().index(b"601.2f ")]):
            with self.assertRaisesRegex(GameplayContractError, "SHARED_PROPOSAL_LEGALITY_SCOPE_INSUFFICIENT"):
                locate_anchors(raw)

    def test_json_distinct_anchor_types_fail_even_after_rehash(self):
        for field in ("line_count", "owned_example_line_count", "starting_physical_line",
                      "ending_physical_line", "byte_start", "byte_end", "span_length"):
            for replacement in (True, False, float(_json(VERIFIED_ANCHORS)[0][field])):
                candidate = _json(VERIFIED_ANCHORS)
                candidate[0][field] = replacement
                candidate[0]["anchor_id"] = anchor_identity(candidate[0])
                with self.subTest(field=field, replacement=replacement), self.assertRaises(GameplayContractError):
                    validate_spans(candidate)

    def test_wrong_identity_span_scope_and_boundary_metadata_fail(self):
        for field, replacement in (
            ("anchor_id", "sha256:" + "0" * 64), ("rule_reference", "601.2c"),
            ("line_count", 2), ("owned_example_line_count", 1),
            ("byte_end", 298920), ("span_sha256", "sha256:" + "2" * 64),
            ("artifact_hash", "sha256:" + "1" * 64),
            ("following_marker", {"rule_reference": "601.2f", "physical_line": 2474, "body_inspected": 0}),
        ):
            candidate = _json(VERIFIED_ANCHORS)
            candidate[0][field] = replacement
            if field != "anchor_id":
                candidate[0]["anchor_id"] = anchor_identity(candidate[0])
            with self.subTest(field=field), self.assertRaises(GameplayContractError):
                validate_spans(candidate)
        for candidate in ([], _json(VERIFIED_ANCHORS) * 2, tuple(_json(VERIFIED_ANCHORS)), None):
            with self.subTest(kind=type(candidate)), self.assertRaises(GameplayContractError):
                validate_spans(candidate)

    def test_identity_helper_rejects_invalid_structures(self):
        for value in (None, [], 1, True, 1.0, "anchor"):
            with self.subTest(kind=type(value)), self.assertRaises(GameplayContractError):
                anchor_identity(value)

    def test_configured_missing_invalid_or_mismatched_artifact_fails(self):
        with tempfile.TemporaryDirectory() as temporary:
            candidate = Path(temporary) / "invented.fixture"
            candidate.write_bytes(fictional_source())
            for path in (None, "", True, Path(temporary), Path(temporary) / "missing", candidate):
                with self.subTest(kind=type(path)), self.assertRaises(GameplayContractError):
                    verified_anchors(path, review_root=ROOT / "reference-reviews")

    def test_missing_or_altered_retained_lineage_fails_before_source_locator(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            artifact = directory / "invented.fixture"
            artifact.write_bytes(fictional_source())
            review = directory / "review"
            review.mkdir()
            with patch.object(source, "locate_anchors") as locate:
                with self.assertRaisesRegex(GameplayContractError, "SOURCE_ARTIFACT_OR_VERIFICATION_LINEAGE_INVALID"):
                    verified_anchors(artifact, review_root=review)
                locate.assert_not_called()
            for name in ("gameplay-rules-artifact-verification", "gameplay-rules-source-versioning",
                         "gameplay-rules-release-discovery-closure"):
                shutil.copytree(ROOT / "reference-reviews" / name, review / name)
            result = review / "gameplay-rules-artifact-verification" / "artifact-verification-result.json"
            raw = result.read_bytes()
            result.write_bytes(raw.replace(b"6289f9e138c248f33b950842fd079f9dc9d4be431a9ac8dc1effb4a18ec502b3", b"0" * 64))
            self.assertNotEqual(result.read_bytes(), raw)
            with patch.object(source, "locate_anchors") as locate:
                with self.assertRaisesRegex(GameplayContractError, "SOURCE_ARTIFACT_OR_VERIFICATION_LINEAGE_INVALID"):
                    verified_anchors(artifact, review_root=review)
                locate.assert_not_called()

    def test_actual_fresh_e_only_source_reproduction(self):
        configured = os.environ.get(SOURCE_ENV)
        if configured is None:
            self.skipTest("e-only owner source selector unconfigured; offline checks are not fresh reproduction")
        anchors = verified_anchors(configured, review_root=ROOT / "reference-reviews")
        self.assertEqual(anchors, _json(VERIFIED_ANCHORS))
        self.assertEqual(create_projection(anchors).serialize(), create_projection(VERIFIED_ANCHORS).serialize())


if __name__ == "__main__":
    unittest.main()
