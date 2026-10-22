"""Invented boundary fixtures and an explicit two-unit actual-source selector."""
import hashlib
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from gameplay_rules.errors import GameplayContractError
from gameplay_rules.projection.contracts import _json
from gameplay_rules.casting_stage_family_completion import source
from gameplay_rules.casting_stage_family_completion.contracts import create_projection
from gameplay_rules.casting_stage_family_completion.source import (
    SOURCE_ENV, VERIFIED_ANCHORS, anchor_identity, locate_anchors,
    validate_spans, verify_bytes, verified_anchors,
)

ROOT = Path(__file__).resolve().parents[1]
REVIEWS = ROOT / "reference-reviews"
MARKERS = {2461: "601.2", 2463: "601.2a", 2465: "601.2b", 2467: "601.2c",
    2470: "601.2d", 2472: "601.2e", 2474: "601.2f", 2476: "601.2g",
    2478: "601.2h", 2481: "601.2i", 2483: "601.3"}


def fictional_source(terminator=b"\n"):
    """All body text is invented. Markers reproduce only release structure."""
    lines = [b""] * 2483
    for line, reference in MARKERS.items():
        marker = (reference + (". " if reference in ("601.2", "601.3") else " ")).encode()
        lines[line - 1] = marker + b"invented uninspected neighboring content"
    lines[2462] = b"601.2a invented fixture refers to 611.2f and 610.5"
    lines[2463] = b"\xc2\xa0"
    lines[2480] = "601.2i invented fixture refers to 601.2a–h".encode()
    lines[2481] = b"\xc2\xa0"
    return terminator.join(lines)


class CastingStageFamilyCompletionSourceTests(unittest.TestCase):
    def test_two_complete_units_keep_original_raw_boundaries(self):
        for terminator in (b"\n", b"\r\n", b"\r"):
            raw = fictional_source(terminator)
            anchors = locate_anchors(raw)
            self.assertEqual([row["rule_reference"] for row in anchors], ["601.2a", "601.2i"])
            for row, line, expected in ((anchors[0], 2463, b"601.2a invented fixture refers to 611.2f and 610.5"),
                    (anchors[1], 2481, "601.2i invented fixture refers to 601.2a–h".encode())):
                with self.subTest(terminator=terminator, reference=row["rule_reference"]):
                    block = raw[row["byte_start"]:row["byte_end"]]
                    self.assertEqual(block, expected)
                    self.assertEqual(row["span_length"], len(block))
                    self.assertEqual(row["span_sha256"], "sha256:" + hashlib.sha256(block).hexdigest())
                    self.assertEqual(row["anchor_id"], anchor_identity(row))
                    self.assertEqual((row["starting_physical_line"], row["ending_physical_line"]), (line, line))
                    self.assertEqual((row["line_count"], row["owned_example_line_count"]), (1, 0))
                    self.assertEqual(raw[row["byte_end"]:row["byte_end"] + len(terminator)], terminator)
                    self.assertIs(row["following_marker"]["body_inspected"], False)

    def test_owned_material_separator_citations_ranges_and_family_inventory_fail_closed(self):
        raw = fictional_source()
        for changed in (
                raw.replace(b"\xc2\xa0\n", b"Example: invented added material\n\xc2\xa0\n", 1),
                raw.replace(b"\xc2\xa0\n", b"invented continuation\n\xc2\xa0\n", 1),
                raw.replace(b"\xc2\xa0", b" ", 1),
                raw.replace(b"611.2f and 610.5", b"611.2f and 610.6"),
                raw.replace(b"611.2f and 610.5", b"611.2f and 610.5 and 733"),
                raw.replace("601.2a–h".encode(), "601.2a–i".encode()),
                raw.replace(b"601.2b ", b"601.2j "),
                raw.replace(b"601.3. ", b"601.4. ")):
            with self.subTest(size=len(changed)), self.assertRaisesRegex(GameplayContractError, "CASTING_STAGE_BATCH_SCOPE_INSUFFICIENT"):
                locate_anchors(changed)

    def test_neighboring_bodies_are_ignored_and_boundary_prefixes_suffice(self):
        before = locate_anchors(fictional_source())
        changed = fictional_source().replace(b"invented uninspected neighboring content", b"603 733 601.3 arbitrary neighbor")
        after = locate_anchors(changed)
        self.assertEqual([row["span_sha256"] for row in before], [row["span_sha256"] for row in after])
        prefix_only = fictional_source().replace(b"invented uninspected neighboring content", b"")
        self.assertEqual([row["span_sha256"] for row in locate_anchors(prefix_only)],
            [row["span_sha256"] for row in before])

    def test_exact_artifact_gate_precedes_body_locator_and_fixtures_confer_no_authority(self):
        raw = fictional_source()
        with patch.object(source, "locate_anchors") as locate:
            with self.assertRaises(GameplayContractError):
                verify_bytes(raw)
            locate.assert_not_called()
        with self.assertRaises(GameplayContractError):
            create_projection(locate_anchors(raw))
        with patch.object(source, "ARTIFACT_BYTE_LENGTH", len(raw)), patch.object(
                source, "ARTIFACT_HASH", "sha256:" + hashlib.sha256(raw).hexdigest()):
            with self.assertRaises(GameplayContractError):
                verify_bytes(raw)

    def test_anchor_metadata_strict_types_and_complete_batch_identity(self):
        for index in (0, 1):
            for field in ("line_count", "owned_example_line_count", "starting_physical_line", "ending_physical_line", "byte_start", "byte_end", "span_length"):
                for replacement in (True, False, float(_json(VERIFIED_ANCHORS)[index][field])):
                    anchors = _json(VERIFIED_ANCHORS)
                    anchors[index][field] = replacement
                    anchors[index]["anchor_id"] = anchor_identity(anchors[index])
                    with self.subTest(index=index, field=field, replacement=replacement), self.assertRaises(GameplayContractError):
                        validate_spans(anchors)
        for anchors in ([], _json(VERIFIED_ANCHORS)[:1], list(reversed(_json(VERIFIED_ANCHORS))), tuple(_json(VERIFIED_ANCHORS)), None):
            with self.subTest(kind=type(anchors)), self.assertRaises(GameplayContractError):
                validate_spans(anchors)

    def test_configured_missing_artifact_or_lineage_fails_before_body_locator(self):
        with tempfile.TemporaryDirectory() as temporary:
            fake = Path(temporary) / "invented.fixture"
            fake.write_bytes(fictional_source())
            for candidate in (None, "", True, Path(temporary), Path(temporary) / "missing", fake):
                with self.subTest(kind=type(candidate)), self.assertRaises(GameplayContractError):
                    verified_anchors(candidate, review_root=REVIEWS)
            with patch.object(source, "locate_anchors") as locate:
                with self.assertRaises(GameplayContractError):
                    verified_anchors(fake, review_root=Path(temporary) / "missing-lineage")
                locate.assert_not_called()

    def test_actual_fresh_two_unit_source_reproduction(self):
        configured = os.environ.get(SOURCE_ENV)
        if configured is None:
            self.skipTest("two-unit owner TXT selector absent; offline metadata and invented fixtures are not fresh-source verification")
        anchors = verified_anchors(configured, review_root=REVIEWS)
        self.assertEqual(anchors, _json(VERIFIED_ANCHORS))
        self.assertEqual(create_projection(anchors).serialize(), create_projection(VERIFIED_ANCHORS).serialize())
        self.assertEqual([(row["byte_start"], row["byte_end"], row["span_length"]) for row in anchors],
            [(294281, 294956, 675), (300741, 301082, 341)])


if __name__ == "__main__":
    unittest.main()
