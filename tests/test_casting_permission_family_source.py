"""Closed-family source checks; fictional bytes never establish source authority."""
import copy
import os
from pathlib import Path
import unittest
from unittest.mock import patch

from gameplay_rules.errors import GameplayContractError
from gameplay_rules.projection.contracts import _json
from gameplay_rules.casting_permission_family import source

ROOT = Path(__file__).resolve().parents[1]


def fictional_source():
    rows = [b'fictional unrelated line\r\n' for _ in range(2501)]
    for ref, first, last, _, _, _, following, next_line, _ in source.FAMILY_SPEC:
        rows[first-1] = (ref + ('. ' if ref[-1].isdigit() else ' ') + 'Authored fictional statement.\r\n').encode()
        for n in range(first, last):
            rows[n] = b'Example: Authored fictional illustration.\r\n'
        rows[last] = b'\xc2\xa0\r\n'
    rows[2500] = b'601.4. Uninspected fictional boundary.\r\n'
    return rows


class CastingPermissionFamilySourceTests(unittest.TestCase):
    def test_frozen_inventory_and_owned_complete_blocks_are_member_driven(self):
        data = b''.join(fictional_source())
        inventory = source.marker_inventory(data)
        anchors = source.locate_anchors(data)
        self.assertEqual(inventory['selected_unit_count'], 7)
        self.assertEqual([a['rule_reference'] for a in anchors], list(source.SELECTED_REFERENCES))
        for spec, anchor in zip(source.FAMILY_SPEC, anchors):
            with self.subTest(reference=spec[0]):
                self.assertEqual(anchor['line_count'], spec[2]-spec[1]+1)
                self.assertEqual(anchor['owned_example_line_count'], spec[8])
                self.assertFalse(anchor['following_marker']['body_inspected_as_boundary_context'])
                self.assertEqual(data[anchor['byte_start']:anchor['byte_end']].count(b'Example: '), spec[8])
                self.assertFalse(data[anchor['byte_start']:anchor['byte_end']].endswith(b'\r\n'))
        with self.assertRaises(GameplayContractError):
            source.verify_bytes(data)

    def test_each_owned_example_and_separator_is_required(self):
        for spec in source.FAMILY_SPEC:
            rows = fictional_source()
            rows[spec[2]] = b'Extra unowned continuation.\r\n'
            with self.subTest(reference=spec[0]), self.assertRaises(GameplayContractError):
                source.locate_anchors(b''.join(rows))
            if spec[8]:
                rows = fictional_source()
                rows[spec[1]] = b'Unmarked continuation.\r\n'
                with self.subTest(example_owner=spec[0]), self.assertRaises(GameplayContractError):
                    source.locate_anchors(b''.join(rows))

    def test_marker_only_inventory_rejects_missing_duplicate_extra_children_and_sibling_601_30(self):
        for change in ('missing','duplicate','child','601.30'):
            rows = fictional_source()
            if change == 'missing': rows[2484] = b'fictional missing marker\r\n'
            elif change == 'duplicate': rows[10] = b'601.3. Duplicate marker.\r\n'
            elif change == 'child': rows[2499] = b'601.3g New unapproved child.\r\n'
            else: rows[2500] = b'601.30. Sibling, never a subrule.\r\n'
            with self.subTest(change=change), self.assertRaises(GameplayContractError):
                source.marker_inventory(b''.join(rows))

    def test_boundary_body_is_not_selected_but_owned_internal_line_endings_are_hashed(self):
        rows = fictional_source()
        first = source.locate_anchors(b''.join(rows))
        rows[2500] = b'601.4. A completely different boundary body.\r\n'
        second = source.locate_anchors(b''.join(rows))
        # Artifact hash/own identity change, while the selected raw spans do not.
        self.assertEqual([a['span_sha256'] for a in first], [a['span_sha256'] for a in second])
        rows[2484] = rows[2484].replace(b'\r\n',b'\n')
        third = source.locate_anchors(b''.join(rows))
        self.assertNotEqual(second[1]['span_sha256'],third[1]['span_sha256'])

    def test_metadata_snapshot_rejects_type_coercion_and_owns_input(self):
        candidate = _json(source.VERIFIED_ANCHORS)
        snapshot = source.validate_spans(candidate)
        candidate[0]['byte_start'] = 0
        self.assertEqual(snapshot[0]['byte_start'], 301086)
        for value in (True,301086.0,'301086'):
            candidate = _json(source.VERIFIED_ANCHORS)
            candidate[0]['byte_start'] = value
            with self.subTest(value=value), self.assertRaises(GameplayContractError):
                source.validate_spans(candidate)

    def test_lineage_failure_precedes_body_locator(self):
        with patch.object(source,'_verified_bytes',side_effect=GameplayContractError('fixture','invalid')), patch.object(source,'verify_bytes') as locator:
            with self.assertRaises(GameplayContractError):
                source.verified_anchors('fictional.txt',review_root=ROOT/'reference-reviews')
            locator.assert_not_called()

    def test_real_fresh_source_reproduction_of_every_admitted_unit(self):
        selected = os.environ.get(source.SOURCE_ENV)
        if not selected:
            self.skipTest('source-dependent: owner TXT absent; offline metadata/fictional fixtures are not fresh verification')
        anchors = source.verified_anchors(selected,review_root=ROOT/'reference-reviews')
        self.assertEqual(source.validate_spans(anchors),_json(source.VERIFIED_ANCHORS))
        self.assertEqual(len(anchors),7)
