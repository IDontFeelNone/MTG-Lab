"""Physical-copy oracle, exact benchmarks, bounded work and public interface tests."""
import copy
from decimal import Inexact, localcontext
from fractions import Fraction
from itertools import combinations, product
import json
from pathlib import Path
import random
import subprocess
import sys
import unittest
from unittest.mock import patch

from probability.draw_access import (assess_draw_access, ASSUMPTIONS as DRAW_ASSUMPTIONS,
                                     INPUT_VERSION as DRAW_VERSION, canonical_json)
from probability.resource_assignment import (ASSUMPTIONS, INPUT_VERSION, MAX_INPUT_BYTES,
    MAX_VECTORS, MAX_WORK, ResourceAssignmentError, assess_resource_assignment,
    parse_resource_assignment, validate_resource_assignment)

ROOT = Path(__file__).resolve().parents[1]


def request(rows=(((), True, 4), ((), False, 56)), seen=7, demands=(), target=1, mode='observe'):
    return dict(schema_version=INPUT_VERSION, population_id='caller:population', complete=True,
                population_size=sum(c for _, _, c in rows), cards_seen=seen,
                resource_kinds=[k for k, _ in demands], demands=dict(demands),
                target=dict(minimum=target, mode=mode),
                classes=[dict(copies=c, resources=list(r), target=t) for r, t, c in rows],
                assumptions=dict(ASSUMPTIONS))


def exact(report):
    value = report['probability']
    return Fraction(int(value['numerator']), int(value['denominator']))


def physical_oracle(raw):
    """Independent exhaustive physical hands and recursive unused-copy placement.

    No production normalization, binomial weights, count vectors, augmenting
    paths or Hall inequalities participate in this oracle.
    """
    deck = [(tuple(row['resources']), row['target']) for row in raw['classes'] for _ in range(row['copies'])]
    jobs = [('resource', kind) for kind, count in raw['demands'].items() for _ in range(count)]
    if raw['target']['mode'] == 'reserve':
        jobs += [('target', None)] * raw['target']['minimum']

    def place(hand, pending, used):
        if not pending:
            return True
        category, kind = pending[0]
        for index, (resources, target) in enumerate(hand):
            if index not in used and (target if category == 'target' else kind in resources):
                if place(hand, pending[1:], used | {index}):
                    return True
        return False

    favorable = total = 0
    for hand in combinations(deck, raw['cards_seen']):
        total += 1
        if raw['target']['mode'] == 'observe' and sum(t for _, t in hand) < raw['target']['minimum']:
            continue
        favorable += place(hand, jobs, set())
    return favorable, total


class ResourceAssignmentTests(unittest.TestCase):
    def test_exhaustive_small_physical_populations(self):
        descriptors = [((), False), ((), True), (('A',), False), (('B',), False), (('A', 'B'), True)]
        scenarios = hands = 0
        for quantities in product(range(3), repeat=5):
            if not sum(quantities):
                continue
            rows = tuple((resources, target, count) for (resources, target), count in zip(descriptors, quantities))
            for a, b in ((0, 0), (1, 0), (1, 1), (2, 1), (2, 2), (3, 0)):
                for mode in ('observe', 'reserve'):
                    for seen in range(sum(quantities) + 1):
                        raw = request(rows, seen, (('A', a), ('B', b)), mode=mode)
                        n, d = physical_oracle(raw)
                        result = assess_resource_assignment(raw)
                        self.assertEqual((result['favorable_physical_hands'], result['total_physical_hands']), (str(n), str(d)))
                        scenarios += 1; hands += d
        self.assertEqual(scenarios, 17484)
        self.assertEqual(hands, 201672)

    def test_seeded_independent_oracle_varied_targets_and_zero_demands(self):
        rng = random.Random(24920261119)
        descriptors = [(r, t) for r in ((), ('A',), ('B',), ('A', 'B')) for t in (False, True)]
        for _ in range(150):
            selected = rng.sample(descriptors, rng.randrange(1, 6))
            rows = tuple((r, t, rng.randrange(1, 3)) for r, t in selected)
            raw = request(rows, rng.randrange(sum(c for _, _, c in rows) + 1),
                          (('A', rng.randrange(4)), ('B', rng.randrange(4))),
                          target=rng.randrange(5), mode=rng.choice(('observe', 'reserve')))
            n, d = physical_oracle(raw)
            self.assertEqual(exact(assess_resource_assignment(raw)), Fraction(n, d))

    def test_reviewed_fixed_flexible_comparison(self):
        fixed = request((((), True, 4), ((), False, 32), (('A',), False, 12), (('B',), False, 12)),
                        9, (('A', 1), ('B', 1)))
        flexible = request((((), True, 4), ((), False, 32), (('A',), False, 8), (('B',), False, 8), (('A', 'B'), False, 8)),
                           9, (('A', 1), ('B', 1)))
        a, b = exact(assess_resource_assignment(fixed)), exact(assess_resource_assignment(flexible))
        self.assertEqual(a, Fraction(1334229119, 3695785665))
        self.assertEqual(b, Fraction(82162489, 194515035))
        self.assertEqual(b - a, Fraction(226858172, 3695785665))

    def test_one_flexible_copy_cannot_pay_two_jobs(self):
        raw = request(((('A', 'B'), True, 1), ((), False, 1)), 2, (('A', 1), ('B', 1)))
        self.assertEqual(exact(assess_resource_assignment(raw)), 0)

    def test_multiple_assignments_count_each_hand_once(self):
        raw = request(((('A', 'B'), False, 4),), 2, (('A', 1), ('B', 1)), target=0)
        result = assess_resource_assignment(raw)
        self.assertEqual(result['favorable_physical_hands'], '6')
        self.assertEqual(exact(result), 1)

    def test_target_overlap_observe_and_reserve(self):
        raw = request(((('A',), True, 1), ((), False, 1)), 1, (('A', 1),))
        self.assertEqual(exact(assess_resource_assignment(raw)), Fraction(1, 2))
        raw['target']['mode'] = 'reserve'
        self.assertEqual(exact(assess_resource_assignment(raw)), 0)
        raw['classes'][0]['copies'] = 2; raw['population_size'] = 3; raw['cards_seen'] = 2
        self.assertEqual(exact(assess_resource_assignment(raw)), Fraction(1, 3))

    def test_reserved_target_choice_must_not_be_greedy(self):
        raw = request(((('A',), True, 1), ((), True, 1)), 2, (('A', 1),), mode='reserve')
        self.assertEqual(exact(assess_resource_assignment(raw)), 1)

    def test_exact_binomial_weights(self):
        raw = request(((('A',), True, 2), ((), False, 3)), 2, (('A', 1),))
        result = assess_resource_assignment(raw)
        self.assertEqual(result['favorable_physical_hands'], '7')
        self.assertEqual(result['total_physical_hands'], '10')
        self.assertEqual(exact(result), Fraction(7, 10))

    def test_resource_free_reduces_to_existing_draw_access(self):
        for size in (1, 7, 60, 120):
            for copies in (0, min(4, size)):
                for minimum in range(min(4, copies) + 1):
                    for seen in (0, min(7, size), min(20, size)):
                        draw = dict(schema_version=DRAW_VERSION, deck_size=size,
                                    groups=[dict(group_id='target', copies=copies, minimum=minimum)],
                                    schedule=[dict(label='window', cards_seen=seen)], assumptions=dict(DRAW_ASSUMPTIONS))
                        p = assess_draw_access(draw)['results'][0]['probability']
                        for mode in ('observe', 'reserve'):
                            raw = request((((), True, copies), ((), False, size - copies)), seen, target=minimum, mode=mode)
                            self.assertEqual(exact(assess_resource_assignment(raw)), Fraction(int(p['numerator']), int(p['denominator'])))

    def test_empty_requirements_zero_sample_and_impossible_events(self):
        for mode in ('observe', 'reserve'):
            for seen in (0, 1, 2):
                raw = request((((), False, 2),), seen, target=0, mode=mode)
                self.assertEqual(exact(assess_resource_assignment(raw)), 1)
                raw['target']['minimum'] = 4
                result = assess_resource_assignment(raw)
                self.assertEqual(result['event'], 'IMPOSSIBLE')
                self.assertEqual(result['status'], 'CALCULATED')
                self.assertEqual(exact(result), 0)

    def test_maximum_supported_population_sample_demands_and_target(self):
        raw = request(((('A',), False, 40), (('B',), False, 40), ((), True, 40)),
                      20, (('A', 3), ('B', 3)), target=4, mode='reserve')
        result = assess_resource_assignment(raw)
        self.assertGreater(exact(result), 0)
        self.assertLessEqual(result['computation']['estimated_work_units'], MAX_WORK)
        self.assertLess(exact(result), 1)

    def test_five_classes_accepted_within_budget(self):
        raw = request((((), False, 32), ((), True, 4), (('A',), False, 8), (('B',), False, 8), (('A', 'B'), False, 8)),
                      9, (('A', 1), ('B', 1)))
        result = assess_resource_assignment(raw)
        self.assertEqual(result['computation']['count_vectors'], result['computation']['vectors_evaluated'])
        self.assertLessEqual(result['computation']['count_vectors'], MAX_VECTORS)

    def test_vector_budget_refusal_before_matching(self):
        raw = request((((), False, 24), ((), True, 24), (('A',), False, 24), (('B',), False, 24), (('A', 'B'), True, 24)),
                      20, (('A', 1), ('B', 1)))
        with patch('probability.resource_assignment._matching', side_effect=AssertionError('must not execute')):
            with self.assertRaises(ResourceAssignmentError) as context:
                assess_resource_assignment(raw)
        self.assertEqual(context.exception.code, 'RESOURCE_BUDGET_REFUSAL')
        self.assertNotIn('probability', context.exception.as_dict())

    def test_work_budget_refusal_and_repeatability(self):
        raw = request((((), False, 23), ((), True, 24), (('A',), False, 24), (('B',), False, 24), (('A', 'B'), True, 24)),
                      19, (('A', 3), ('B', 3)), target=4, mode='reserve')
        errors = []
        for _ in range(2):
            with self.assertRaises(ResourceAssignmentError) as context:
                assess_resource_assignment(raw)
            errors.append(context.exception.as_dict())
        self.assertEqual(errors[0], errors[1])
        self.assertEqual(errors[0]['code'], 'RESOURCE_BUDGET_REFUSAL')

    def test_invalid_types_values_and_unsupported_bounds(self):
        changes = [('population_size', 0, 'INVALID_INPUT'), ('population_size', 121, 'UNSUPPORTED_SCOPE'),
                   ('population_size', True, 'INVALID_INPUT'), ('cards_seen', -1, 'INVALID_INPUT'),
                   ('cards_seen', 21, 'UNSUPPORTED_SCOPE'), ('cards_seen', 7.0, 'INVALID_INPUT'),
                   ('cards_seen', '7', 'INVALID_INPUT'), ('cards_seen', None, 'INVALID_INPUT'),
                   ('complete', False, 'INVALID_INPUT'), ('complete', 1, 'INVALID_INPUT'),
                   ('schema_version', 'future', 'UNSUPPORTED_SCOPE'), ('population_id', '', 'INVALID_INPUT')]
        for field, value, code in changes:
            raw = request(); raw[field] = value
            with self.subTest(field=field, value=value), self.assertRaises(ResourceAssignmentError) as context:
                assess_resource_assignment(raw)
            self.assertEqual(context.exception.code, code)
        for raw in (None, [], 3, True, {'extra': 1}):
            with self.assertRaises(ResourceAssignmentError): assess_resource_assignment(raw)

    def test_population_completeness_and_no_invented_filler(self):
        raw = request(); raw['classes'][0]['copies'] -= 1
        with self.assertRaises(ResourceAssignmentError): assess_resource_assignment(raw)
        raw = request((((), False, 2),), 3, target=0)
        with self.assertRaises(ResourceAssignmentError): assess_resource_assignment(raw)
        raw = request((((), False, 0),), 0, target=0)
        with self.assertRaises(ResourceAssignmentError): assess_resource_assignment(raw)

    def test_closed_nested_objects_and_boolean_membership(self):
        for field in ('target', 'assumptions', 'demands'):
            raw = request(); raw[field]['extra'] = True
            with self.assertRaises(ResourceAssignmentError): assess_resource_assignment(raw)
        for field, bad in (('copies', True), ('copies', -1), ('target', 1), ('resources', 'A'), ('resources', [False])):
            raw = request(); raw['classes'][0][field] = bad
            with self.assertRaises(ResourceAssignmentError): assess_resource_assignment(raw)
        raw = request(); raw['classes'][0]['extra'] = 0
        with self.assertRaises(ResourceAssignmentError): assess_resource_assignment(raw)

    def test_unsupported_kinds_demands_targets_and_semantics(self):
        for raw in (request(demands=(('A', 4),)), request(target=5), request(mode='automatic'),
                    request(demands=(('A', 0), ('B', 0), ('C', 0)))):
            with self.assertRaises(ResourceAssignmentError) as context: assess_resource_assignment(raw)
            self.assertEqual(context.exception.code, 'UNSUPPORTED_SCOPE')
        for bad in (-1, True, 0.5):
            raw = request(demands=(('A', 0),)); raw['demands']['A'] = bad
            with self.assertRaises(ResourceAssignmentError): assess_resource_assignment(raw)
        raw = request(); raw['assumptions']['availability'] = 'infer-from-turn'
        with self.assertRaises(ResourceAssignmentError) as context: assess_resource_assignment(raw)
        self.assertEqual(context.exception.code, 'UNSUPPORTED_SCOPE')

    def test_duplicate_equivalence_rows_and_resources_reject(self):
        for raw in (request((((), False, 1), ((), False, 1)), 1, target=0),
                    request(((('A', 'A'), True, 2),), 1, (('A', 1),)),
                    request(((('B',), True, 2),), 1, (('A', 1),))):
            with self.assertRaises(ResourceAssignmentError): assess_resource_assignment(raw)
        raw = request(); raw['resource_kinds'] = ['A', 'A']; raw['demands'] = {'A': 0}
        with self.assertRaises(ResourceAssignmentError): assess_resource_assignment(raw)

    def test_maximum_class_count_and_invalid_lists(self):
        descriptors = (((), False, 1), ((), True, 1), (('A',), False, 1), (('A',), True, 1),
                       (('B',), False, 1), (('B',), True, 1))
        raw = request(descriptors, 1, (('A', 0), ('B', 0)))
        with self.assertRaises(ResourceAssignmentError) as context: assess_resource_assignment(raw)
        self.assertEqual(context.exception.code, 'UNSUPPORTED_SCOPE')
        for value in ([], (), None, 'bad'):
            raw = request(); raw['classes'] = value
            with self.assertRaises(ResourceAssignmentError): assess_resource_assignment(raw)

    def test_json_parser_adversarial_inputs(self):
        for raw in (b'\xff', '{', '{"schema_version":1,"schema_version":2}', '[NaN]', '[Infinity]',
                    '[' * 1100 + '0' + ']' * 1100, ' ' * (MAX_INPUT_BYTES + 1), 3, None):
            with self.assertRaises(ResourceAssignmentError): parse_resource_assignment(raw)
        self.assertEqual(parse_resource_assignment(canonical_json(request())), validate_resource_assignment(request()))

    def test_determinism_immutability_and_normalization(self):
        raw = request(((('B', 'A'), True, 4), ((), False, 56)), 7, (('B', 1), ('A', 1)))
        before = copy.deepcopy(raw)
        result = assess_resource_assignment(raw)
        raw['classes'].reverse(); raw['resource_kinds'].reverse(); raw['classes'][1]['resources'].reverse()
        self.assertEqual(assess_resource_assignment(raw), result)
        self.assertEqual(assess_resource_assignment(before), result)
        normalized = validate_resource_assignment(before)
        normalized['classes'].clear()
        self.assertEqual(before['classes'][0]['copies'], 4)
        result['input']['target']['minimum'] = 0
        self.assertEqual(before['target']['minimum'], 1)

    def test_decimal_presentation_independent_of_context(self):
        result = assess_resource_assignment(request())
        with localcontext() as context:
            context.prec = 1; context.traps[Inexact] = True
            self.assertEqual(assess_resource_assignment(request()), result)
        self.assertEqual(result['probability']['decimal'], '0.399499625745')

    def test_tiny_nonzero_is_not_reported_as_impossible(self):
        raw = request((((), True, 4), (('A',), False, 3), (('B',), False, 3), ((), False, 110)),
                      10, (('A', 3), ('B', 3)), target=4, mode='reserve')
        result = assess_resource_assignment(raw)
        self.assertGreater(exact(result), 0)
        self.assertTrue(result['probability']['nonzero'])
        self.assertEqual(result['probability']['decimal'], '0.000000000000')
        self.assertEqual(result['event'], 'POSSIBLE')

    def test_cli_parity_and_structured_refusals(self):
        for raw, status in ((request(), 0), ({}, 2)):
            process = subprocess.run([sys.executable, '-B', '-m', 'probability', 'resource-assignment', '--input', '-'],
                                     input=canonical_json(raw), capture_output=True, text=True, cwd=ROOT, timeout=10)
            self.assertEqual(process.returncode, status, process.stderr)
            expected = assess_resource_assignment(raw) if not status else dict(schema_version='declared-resource-assignment-report-v1',
                status='REFUSED', code='INVALID_INPUT', reason='closed object fields required', real_gameplay_authorized=False)
            self.assertEqual(json.loads(process.stdout), expected)
        process = subprocess.run([sys.executable, '-B', '-m', 'probability', 'resource-assignment', '--input', '/nonexistent/input.json'],
                                 capture_output=True, text=True, cwd=ROOT, timeout=10)
        self.assertEqual(process.returncode, 2)
        self.assertNotIn('/nonexistent', process.stdout)
        self.assertEqual(json.loads(process.stdout)['reason'], 'input file unavailable')


if __name__ == '__main__':
    unittest.main()
