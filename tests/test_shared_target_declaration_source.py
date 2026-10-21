"""Complete c-only boundaries; structural fixtures contain invented text only."""
import hashlib
import os
from pathlib import Path
import tempfile
import unittest

from gameplay_rules.errors import GameplayContractError
from gameplay_rules.projection.contracts import _json
from gameplay_rules.shared_target_declaration.contracts import create_projection
from gameplay_rules.shared_target_declaration.source import (
    SOURCE_ENV, VERIFIED_ANCHORS, anchor_identity, locate_anchors,
    validate_spans, verify_bytes, verified_anchors,
)

ROOT = Path(__file__).resolve().parents[1]


def fictional_source(terminator=b"\n"):
    return terminator * 2466 + terminator.join((
        b"601.2c invented declaration fixture", b"Example: invented owned fixture",
        b"\xc2\xa0", b"601.2d arbitrary uninspected body",
    ))


class SharedTargetDeclarationSourceTests(unittest.TestCase):
    def test_complete_block_preserves_internal_terminator_and_excludes_final_one(self):
        for terminator in (b"\n", b"\r\n", b"\r"):
            with self.subTest(terminator=terminator):
                raw = fictional_source(terminator)
                anchor = locate_anchors(raw)[0]
                block = raw[anchor["byte_start"]:anchor["byte_end"]]
                self.assertIn(terminator, block)
                self.assertFalse(block.endswith(terminator))
                self.assertEqual(anchor["line_count"], 2)
                self.assertEqual(anchor["owned_example_line_count"], 1)
                self.assertEqual(anchor["ending_physical_line"], 2468)
                self.assertEqual(anchor["span_length"], len(block))
                self.assertEqual(anchor["span_sha256"], "sha256:" + hashlib.sha256(block).hexdigest())
                self.assertEqual(anchor["anchor_id"], anchor_identity(anchor))

    def test_missing_example_or_extra_owned_line_stops(self):
        for raw in (
            fictional_source().replace(b"Example: invented owned fixture\n", b""),
            fictional_source().replace(b"Example: ", b"Continuation: "),
            fictional_source().replace(b"\xc2\xa0\n", b"Example: invented extra\n\xc2\xa0\n"),
            fictional_source().replace(b"\xc2\xa0", b" "),
        ):
            with self.subTest(size=len(raw)), self.assertRaisesRegex(
                    GameplayContractError, "SHARED_TARGET_DECLARATION_SCOPE_INSUFFICIENT"):
                locate_anchors(raw)

    def test_wrong_scope_markers_and_numbered_outgoing_reference_stop(self):
        for raw in (
            fictional_source().replace(b"601.2c ", b"601.2b "),
            fictional_source().replace(b"601.2d ", b"601.2d. "),
            fictional_source().replace(b"601.2d ", b"601.2e "),
            fictional_source().replace(b"invented declaration fixture", b"invented 603 fixture"),
        ):
            with self.subTest(size=len(raw)), self.assertRaisesRegex(
                    GameplayContractError, "SHARED_TARGET_DECLARATION_SCOPE_INSUFFICIENT"):
                locate_anchors(raw)

    def test_following_body_is_not_inspected_or_included(self):
        raw = fictional_source()
        changed = raw.replace(b"arbitrary uninspected body", b"603 733 601.2i changed neighboring content")
        before, after = locate_anchors(raw)[0], locate_anchors(changed)[0]
        for field in ("byte_start", "byte_end", "line_count", "span_sha256", "span_length"):
            self.assertEqual(before[field], after[field])
        self.assertFalse(after["following_marker"]["body_inspected"])

    def test_structural_fixture_is_never_real_source_or_admitted_projection(self):
        with self.assertRaisesRegex(GameplayContractError, "VERIFIED_SOURCE_ARTIFACT_MISMATCH"):
            verify_bytes(fictional_source())
        with self.assertRaises(GameplayContractError):
            create_projection(locate_anchors(fictional_source()))

    def test_nonbytes_or_truncated_source_is_rejected(self):
        for invalid in (None, True, 1, 1.0, "invented", bytearray(b"invented"), b"", b"601.2c invented"):
            with self.subTest(kind=type(invalid)), self.assertRaises(GameplayContractError):
                verify_bytes(invalid)
            with self.subTest(kind=type(invalid)), self.assertRaises(GameplayContractError):
                locate_anchors(invalid)

    def test_json_distinct_anchor_metadata_fails_even_after_own_rehash(self):
        for field in ("line_count", "owned_example_line_count", "starting_physical_line",
                      "ending_physical_line", "byte_start", "byte_end", "span_length"):
            for replacement in (True, False, float(_json(VERIFIED_ANCHORS)[0][field])):
                candidate = _json(VERIFIED_ANCHORS)
                candidate[0][field] = replacement
                candidate[0]["anchor_id"] = anchor_identity(candidate[0])
                with self.subTest(field=field, replacement=replacement), self.assertRaises(GameplayContractError):
                    validate_spans(candidate)

    def test_anchor_identity_scope_truncation_and_boundary_substitutions_fail(self):
        for field, replacement in (
            ("anchor_id", "sha256:" + "0" * 64), ("rule_reference", "601.2d"),
            ("line_count", 1), ("owned_example_line_count", 0),
            ("byte_end", 298000), ("artifact_hash", "sha256:" + "1" * 64),
            ("following_marker", {"rule_reference": "601.2d", "physical_line": 2470, "body_inspected": 0}),
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

    def test_actual_fresh_c_only_source_reproduction(self):
        configured = os.environ.get(SOURCE_ENV)
        if configured is None:
            self.skipTest("c-only owner source selector unconfigured; offline checks are not fresh reproduction")
        anchors = verified_anchors(configured, review_root=ROOT / "reference-reviews")
        self.assertEqual(anchors, _json(VERIFIED_ANCHORS))
        self.assertEqual(create_projection(anchors).serialize(), create_projection(VERIFIED_ANCHORS).serialize())


if __name__ == "__main__":
    unittest.main()
