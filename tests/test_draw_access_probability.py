"""Independent exact arithmetic, enumeration, bounds and public CLI checks."""
import copy
from decimal import Inexact, localcontext
from fractions import Fraction
from itertools import combinations, product
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from probability.draw_access import (ASSUMPTIONS, INPUT_VERSION, MAX_INPUT_BYTES,
    DrawAccessError, assess_draw_access, canonical_json, parse_draw_access, validate_draw_access)

ROOT = Path(__file__).resolve().parents[1]


def request(size=60, groups=((4, 1),), seen=(7,)):
    return {'schema_version': INPUT_VERSION, 'deck_size': size,
            'groups': [{'group_id': 'group-' + str(i), 'copies': copies, 'minimum': minimum}
                       for i, (copies, minimum) in enumerate(groups)],
            'schedule': [{'label': 'sample-' + str(i), 'cards_seen': count} for i, count in enumerate(seen)],
            'assumptions': dict(ASSUMPTIONS)}


def fraction(row):
    value = row['probability']
    return Fraction(int(value['numerator']), int(value['denominator']))


class DrawAccessProbabilityTests(unittest.TestCase):
    def test_four_of_sixty_in_seven_matches_hypergeometric(self):
        from math import comb
        result = assess_draw_access(request())
        self.assertEqual(fraction(result['results'][0]), 1 - Fraction(comb(56, 7), comb(60, 7)))
        self.assertEqual(result['results'][0]['probability']['decimal'], '0.399499625745')

    def test_single_group_thresholds_match_independent_complement_formula(self):
        from math import comb
        for size in range(1, 11):
            for copies in range(size + 1):
                for minimum in range(copies + 1):
                    seen = min(4, size)
                    missing = sum(comb(copies, k) * comb(size - copies, seen - k)
                                  for k in range(minimum) if 0 <= seen - k <= size - copies)
                    expected = 1 - Fraction(missing, comb(size, seen))
                    self.assertEqual(fraction(assess_draw_access(request(size, ((copies, minimum),), (seen,)))['results'][0]), expected)

    def test_two_and_three_group_joint_events_match_exhaustive_small_decks(self):
        for counts in ((2, 2), (1, 2, 2), (0, 2, 1), (2, 1, 1)):
            size = sum(counts) + 1
            labels = tuple(group for group, count in enumerate(counts) for _ in range(count)) + (-1,)
            for minimums in product(*(range(min(2, count) + 1) for count in counts)):
                groups = tuple(zip(counts, minimums))
                for seen in range(size + 1):
                    hands = tuple(combinations(range(size), seen))
                    hits = sum(all(sum(labels[index] == group for index in hand) >= minimum
                                   for group, minimum in enumerate(minimums)) for hand in hands)
                    actual = fraction(assess_draw_access(request(size, groups, (seen,)))['results'][0])
                    self.assertEqual(actual, Fraction(hits, len(hands)))

    def test_joint_event_does_not_assume_independent_group_access(self):
        r = assess_draw_access(request(4, ((1, 1), (1, 1)), (2,)))
        self.assertEqual(fraction(r['results'][0]), Fraction(1, 6))
        self.assertNotEqual(fraction(r['results'][0]), Fraction(1, 2) ** 2)

    def test_zero_certainty_and_impossible_events(self):
        for arguments, expected in [((4, ((2, 1),), (0,)), 0),
                                    ((4, ((2, 0),), (0,)), 1),
                                    ((4, ((0, 0),), (4,)), 1),
                                    ((4, ((2, 2), (2, 2)), (3,)), 0),
                                    ((4, ((2, 2), (2, 2)), (4,)), 1)]:
            self.assertEqual(fraction(assess_draw_access(request(*arguments))['results'][0]), expected)

    def test_access_is_monotone_in_cards_seen_and_target_copies(self):
        rows = assess_draw_access(request(60, ((4, 1), (3, 1)), tuple(range(21))))['results']
        odds = list(map(fraction, rows))
        self.assertEqual(odds, sorted(odds))
        copies_odds = [fraction(assess_draw_access(request(60, ((copies, 1),), (7,)))['results'][0]) for copies in range(1, 21)]
        self.assertEqual(copies_odds, sorted(copies_odds))

    def test_exact_fraction_strings_and_rounding_ignore_ambient_decimal_context(self):
        expected = assess_draw_access(request())
        with localcontext() as context:
            context.prec = 2
            context.traps[Inexact] = True
            self.assertEqual(assess_draw_access(request()), expected)
        self.assertIs(type(expected['results'][0]['probability']['numerator']), str)

    def test_api_input_and_results_are_independently_owned(self):
        value = request(); before = copy.deepcopy(value)
        first = assess_draw_access(value); saved = copy.deepcopy(first)
        self.assertEqual(value, before)
        first['input']['groups'][0]['copies'] = 0
        first['limitations'].clear(); first['results'][0]['probability']['numerator'] = '0'
        self.assertEqual(value, before)
        self.assertEqual(assess_draw_access(value), saved)

    def test_members_have_individual_identities_and_exact_group_copy_totals(self):
        value = request()
        value['groups'][0]['members'] = [{'card_id': 'caller:alpha', 'copies': 2},
                                         {'card_id': 'caller:beta', 'copies': 2}]
        result = assess_draw_access(value)
        self.assertEqual(fraction(result['results'][0]), fraction(assess_draw_access(request())['results'][0]))
        self.assertEqual(result['input']['groups'][0]['members'], value['groups'][0]['members'])
        self.assertNotEqual(result['input_id'], assess_draw_access(request())['input_id'])

    def test_overlap_duplicate_and_contradictory_members_reject(self):
        value = request(60, ((4, 1), (2, 1)))
        value['groups'][0]['members'] = [{'card_id': 'caller:a', 'copies': 4}]
        value['groups'][1]['members'] = [{'card_id': 'caller:a', 'copies': 2}]
        with self.assertRaises(DrawAccessError): assess_draw_access(value)
        for members in ([{'card_id': 'a', 'copies': 2}] * 2,
                        [{'card_id': 'a', 'copies': 3}], [],
                        [{'card_id': 'a', 'copies': 0}],
                        [{'card_id': 'a', 'copies': True}]):
            changed = request(); changed['groups'][0]['members'] = members
            with self.subTest(members=members), self.assertRaises(DrawAccessError): assess_draw_access(changed)

    def test_group_and_member_declaration_order_normalize_identically(self):
        value = request(60, ((4, 1), (2, 1)))
        value['groups'][0]['members'] = [{'card_id': 'b', 'copies': 2}, {'card_id': 'a', 'copies': 2}]
        expected = assess_draw_access(value)
        value['groups'][0]['members'].reverse(); value['groups'].reverse()
        self.assertEqual(assess_draw_access(value), expected)
        self.assertEqual(canonical_json(expected), canonical_json(assess_draw_access(value)))

    def test_ordinary_ordered_labels_are_assumptions_and_equal_counts_are_valid(self):
        value = request(seen=(7, 7, 9, 10))
        for label, entry in zip(('Opening hand', 'Caller window', 'Turn 3', 'Turn 4'), value['schedule']): entry['label'] = label
        result = assess_draw_access(value)
        self.assertEqual([r['label'] for r in result['results']], [r['label'] for r in value['schedule']])
        self.assertEqual(result['results'][0]['probability'], result['results'][1]['probability'])
        self.assertFalse(result['real_gameplay_authorized'])
        self.assertIn('caller declarations', result['limitations'][0])

    def test_request_and_nested_closed_schemas_reject_unknown_or_missing_fields(self):
        for path in ((), ('groups', 0), ('schedule', 0), ('assumptions',)):
            value = request(); row = value
            for key in path: row = row[key]
            row['approved'] = True
            with self.subTest(path=path), self.assertRaises(DrawAccessError): assess_draw_access(value)
        for field in request():
            value = request(); del value[field]
            with self.subTest(field=field), self.assertRaises(DrawAccessError): assess_draw_access(value)

    def test_numeric_types_and_bounds_reject_without_coercion(self):
        cases = [('deck_size', (-1, 0, 121, True, 60.0, '60', None)),
                 ('copies', (-1, 61, True, 4.0, '4', None)),
                 ('minimum', (-1, 5, True, 1.0, '1', None)),
                 ('cards_seen', (-1, 21, True, 7.0, '7', None))]
        for field, invalids in cases:
            for invalid in invalids:
                value = request()
                row = value if field == 'deck_size' else value['schedule'][0] if field == 'cards_seen' else value['groups'][0]
                row[field] = invalid
                with self.subTest(field=field, value=invalid), self.assertRaises(DrawAccessError): assess_draw_access(value)
        with self.assertRaises(DrawAccessError): assess_draw_access(request(4, ((2, 1),), (5,)))

    def test_collections_must_have_bounded_unambiguous_shapes(self):
        for field in ('groups', 'schedule'):
            for invalid in (None, {}, 'x', (), [], [None], [1]):
                value = request(); value[field] = invalid
                with self.subTest(field=field, value=invalid), self.assertRaises(DrawAccessError): assess_draw_access(value)
        for value in (request(groups=((1, 1),) * 4), request(4, ((3, 1), (3, 1))), request(seen=(7,) * 22)):
            with self.assertRaises(DrawAccessError): assess_draw_access(value)
        for invalid in (None, [], True, 'request'):
            with self.assertRaises(DrawAccessError): assess_draw_access(invalid)

    def test_ambiguous_group_labels_and_malformed_schedules_reject(self):
        for invalid in ('', ' padded ', 'line\nbreak', 'a' * 81, None, True):
            value = request(); value['schedule'][0]['label'] = invalid
            with self.subTest(label=invalid), self.assertRaises(DrawAccessError): assess_draw_access(value)
        for value in (request(seen=(8, 7)), request(groups=((2, 1), (2, 1)))):
            if len(value['groups']) == 2: value['groups'][1]['group_id'] = value['groups'][0]['group_id']
            with self.assertRaises(DrawAccessError): assess_draw_access(value)
        value = request(seen=(7, 8)); value['schedule'][1]['label'] = value['schedule'][0]['label']
        with self.assertRaises(DrawAccessError): assess_draw_access(value)

    def test_group_and_member_identifier_types_and_unknown_fields_reject(self):
        for invalid in ('', ' padded ', 'a' * 129, 'line\nbreak', None, 1, True, '\ud800'):
            value = request(); value['groups'][0]['members'] = [{'card_id': invalid, 'copies': 4}]
            with self.subTest(identifier=repr(invalid)), self.assertRaises(DrawAccessError): assess_draw_access(value)
        for invalid in ('', 'a' * 65, None, 1, True):
            value = request(); value['groups'][0]['group_id'] = invalid
            with self.assertRaises(DrawAccessError): assess_draw_access(value)
        value = request(); value['groups'][0]['members'] = [{'card_id': 'a', 'copies': 4, 'approved': True}]
        with self.assertRaises(DrawAccessError): assess_draw_access(value)

    def test_smallest_deck_and_full_draw_are_supported(self):
        rows = assess_draw_access(request(1, ((1, 1),), (0, 1)))['results']
        self.assertEqual(list(map(fraction, rows)), [0, 1])

    def test_fractions_remain_authoritative_when_twelve_place_display_rounds(self):
        from math import comb
        row = assess_draw_access(request(120, ((20, 20),), (20,)))['results'][0]
        self.assertEqual(fraction(row), Fraction(1, comb(120, 20)))
        self.assertEqual(row['probability']['decimal'], '0.000000000000')
        self.assertGreater(fraction(row), 0)

    def test_sampling_assumptions_are_required_and_never_promote_authority(self):
        for field, invalid in (('sampling', 'with-replacement'), ('group_disjointness', 'inferred')):
            value = request(); value['assumptions'][field] = invalid
            with self.assertRaises(DrawAccessError): assess_draw_access(value)
        value = request(); value['schema_version'] = 'other'
        with self.assertRaises(DrawAccessError): assess_draw_access(value)

    def test_parser_rejects_duplicate_keys_nonfinite_invalid_unicode_and_deep_json(self):
        for raw in ('{"schema_version":1,"schema_version":2}', '{"x":{"a":1,"a":2}}',
                    'NaN', 'Infinity', b'\xff', '[', '[' * 2000 + '0' + ']' * 2000,
                    b'x' * (MAX_INPUT_BYTES + 1), '\ud800', None, bytearray(b'{}')):
            with self.subTest(kind=type(raw).__name__), self.assertRaises(DrawAccessError): parse_draw_access(raw)
        self.assertEqual(parse_draw_access(canonical_json(request())), validate_draw_access(request()))

    def test_input_identity_binds_quantities_requirements_labels_and_assumptions(self):
        original = assess_draw_access(request())
        for key, value in (('copies', 5), ('minimum', 2)):
            changed = request(); changed['groups'][0][key] = value
            report = assess_draw_access(changed)
            self.assertNotEqual(original['input_id'], report['input_id'])
            self.assertNotEqual(original['report_id'], report['report_id'])
        changed = request(); changed['schedule'][0]['label'] = 'different assumption'
        self.assertNotEqual(original['input_id'], assess_draw_access(changed)['input_id'])

    def test_maximum_bounds_are_supported_with_three_groups_and_full_schedule(self):
        value = request(120, ((40, 1), (40, 1), (40, 1)), tuple(range(21)))
        report = assess_draw_access(value)
        self.assertEqual(len(report['results']), 21)
        self.assertLessEqual(len(canonical_json(report).encode()), 65536)
        self.assertEqual(fraction(report['results'][0]), 0)
        self.assertLessEqual(fraction(report['results'][-1]), 1)

    def test_public_module_cli_file_stdin_and_api_are_identical_and_read_only(self):
        value = request(); raw = canonical_json(value).encode()
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'input.json'; path.write_bytes(raw)
            before = path.read_bytes()
            command = [sys.executable, '-B', '-m', 'probability', 'draw-access', '--input']
            for argument in (str(path), '-'):
                run = subprocess.run(command + [argument], input=raw, capture_output=True, cwd=ROOT)
                self.assertEqual(run.returncode, 0, run.stderr)
                self.assertEqual(run.stderr, b'')
                self.assertEqual(run.stdout, (canonical_json(assess_draw_access(value)) + '\n').encode())
            self.assertEqual(path.read_bytes(), before)
            self.assertEqual(list(Path(directory).iterdir()), [path])

    def test_cli_rejects_invalid_or_unavailable_inputs_without_partial_success(self):
        command = [sys.executable, '-B', '-m', 'probability', 'draw-access', '--input']
        for argument, raw in (('-', b'{'), ('-', b'x' * (MAX_INPUT_BYTES + 1)), ('/missing/draw-access-input.json', b'')):
            run = subprocess.run(command + [argument], input=raw, capture_output=True, cwd=ROOT)
            self.assertEqual(run.returncode, 2)
            result = json.loads(run.stdout)
            self.assertEqual(result['status'], 'INVALID_DRAW_ACCESS_INPUT')
            self.assertNotIn('results', result); self.assertEqual(run.stderr, b'')


if __name__ == '__main__':
    unittest.main()
