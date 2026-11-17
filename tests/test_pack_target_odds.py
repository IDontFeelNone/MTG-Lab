"""Exact finite enumeration, admission, target and minimum-search regressions."""
import copy
from dataclasses import FrozenInstanceError
from fractions import Fraction
from itertools import product
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from simulation import load_pack_simulator, render_pack_report, PackSimulationError
from simulation.pack import ValidatedPackComposition
from probability.pack_odds import (assess_pack_target, parse_pack_odds, validate_pack_odds,
    PackOddsError, _payload, INPUT_VERSION, INDEPENDENCE, MAX_PACKS, MAX_INPUT_BYTES)
from test_pack_simulation import files

ROOT = Path(__file__).resolve().parents[1]
P1 = 'pack_fixture.tst.1.en'
P2 = 'pack_fixture.tst.2.en'
P3 = 'pack_fixture.tst.3.en'


def request(identifier=P1, kind='printing', counts=(0, 1, 7), threshold='0.5', **target):
    result = dict(schema_version=INPUT_VERSION, target=dict(kind=kind, id=identifier, **target),
                  pack_counts=list(counts), independence=INDEPENDENCE)
    if threshold is not None: result['threshold'] = threshold
    return result


def exact(payload):
    value = payload['exact_fraction']
    assert value['encoding'] == 'hexadecimal-integers'
    return Fraction(int(value['numerator'], 16), int(value['denominator'], 16))


class PackTargetOddsTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.data = Path(self.temp.name) / 'data'
        self.reset('v02')

    def reset(self, version):
        if self.data.exists(): shutil.rmtree(self.data)
        shutil.copytree(ROOT / f'tests/fixtures/pack_simulation_{version}/data', self.data)
        self.game = self.data / 'canonical/games/pack_fixture'
        self.pack = 'fictional-variants' if version == 'v02' else 'fictional-definition'

    def mutate(self, relative, function):
        path = self.game / relative; value = json.loads(path.read_text())
        function(value); path.write_text(json.dumps(value))

    def view(self):
        return load_pack_simulator('pack_fixture', data_root=self.data).inspect(
            'fictional-pack', pack_definition_id=self.pack)

    def report(self, value=None):
        return assess_pack_target(self.view(), value or request())

    def benchmark(self, denominator=10):
        self.reset('v0')
        self.mutate('packs/fictional-definition/pack-definition.json', lambda d: d.update(slot_ids=['base-slot']))
        self.mutate('slots/base-slot/slot.json', lambda d: d.update(draw_count=1))
        self.mutate('print_sheets/base-sheet/print-sheet.json', lambda d: d.update(
            entries=[dict(printing_id=P1, weight=1), dict(printing_id=P2, weight=denominator - 1)]))

    def add_treatment(self, treatments=('fictional-fixed',), status='promoted', verified='confirmed'):
        for name in treatments:
            path = self.game / 'treatments' / (name + '.json'); path.parent.mkdir(exist_ok=True)
            path.write_text(json.dumps(dict(id=name, game_id='pack_fixture', name=name)))
        def change(row):
            row['treatments'] = list(treatments)
            assertion = dict(row['assertions'][0]); assertion.update(id='fictional-treatment-assertion',
                path='/treatments', asserted_value=list(treatments), status=status, verification_status=verified)
            row['assertions'].append(assertion)
        self.mutate(f'printings/{P1}/printing.json', change)

    def test_shared_admission_preserves_all_v0_v01_and_v02_golden_reports(self):
        for version, seeds in (('v0', (1,)), ('v01', (1, 2)), ('v02', (0, 1, 97))):
            self.reset(version)
            owner = load_pack_simulator('pack_fixture', data_root=self.data)
            view = owner.inspect('fictional-pack', pack_definition_id=self.pack)
            for seed in seeds:
                generated = owner.generate('fictional-pack', pack_definition_id=self.pack, seed=seed)
                self.assertEqual(generated['input_id'], view.to_dict()['context']['input_id'])
                if version == 'v02':
                    expected = ROOT / f'tests/fixtures/pack_simulation_v02/examples/seed{seed}.json'
                else:
                    expected = ROOT / f'tests/fixtures/pack_simulation_v01/examples/{version}-seed{seed}.json'
                self.assertEqual(render_pack_report(generated), expected.read_text())

    def test_exact_finish_variant_mixture_is_seventy_nine_over_eight_hundred(self):
        r = self.report(request(finish_id='foil'))
        # 90% no foil; 8% guaranteed; 2% two independent 3/4 foil draws.
        self.assertEqual(exact(r['single_pack_probability']), Fraction(8, 100) + Fraction(2, 100) * (1 - Fraction(1, 4) ** 2))
        self.assertEqual(exact(r['single_pack_probability']), Fraction(79, 800))
        self.assertEqual(r['solver']['minimum_packs'], 7)
        self.assertEqual(exact(r['pack_results'][2]['probability']), 1 - Fraction(721, 800) ** 7)

    def test_complete_small_models_match_exhaustive_weighted_outcome_enumeration(self):
        for relative in (self.game / 'slots').glob('*/slot.json'):
            value = json.loads(relative.read_text()); value['draw_count'] = 1; relative.write_text(json.dumps(value))
        view = self.view(); body = view.to_dict()['context']
        for target in (request(P1), request(P2), request(P3), request(P1, finish_id='foil')):
            expected = Fraction(0); weights = dict(body['variant_entries']); total = sum(weights.values())
            for variant, weight in weights.items():
                draws, _ = body['candidates'][variant]
                pools = [entries for _, _, count, entries in draws for _ in range(count)]
                for outcomes in product(*pools):
                    chance = Fraction(weight, total)
                    for (outcome, entry_weight), pool in zip(outcomes, pools):
                        chance *= Fraction(entry_weight, sum(w for _, w in pool))
                    hits = any(outcome[0] == target['target']['id'] and
                               ('finish_id' not in target['target'] or outcome[1] == target['target']['finish_id'])
                               for outcome, _ in outcomes)
                    if hits: expected += chance
            self.assertEqual(exact(assess_pack_target(view, target)['single_pack_probability']), expected)

    def test_slot_draw_count_and_independent_packs_are_exact(self):
        self.benchmark()
        self.mutate('slots/base-slot/slot.json', lambda d: d.update(draw_count=2))
        r = self.report(request(counts=(0, 1, 2), threshold=None))
        self.assertEqual(exact(r['single_pack_probability']), Fraction(19, 100))
        self.assertEqual(exact(r['pack_results'][0]['probability']), 0)
        self.assertEqual(exact(r['pack_results'][2]['probability']), 1 - Fraction(9, 10) ** 4)

    def test_card_to_multiple_printing_union_never_double_counts_finishes(self):
        def change(row):
            row['card_id'] = 'pack_fixture.card1'
            for a in row['assertions']:
                if a['path'] == '/card_id': a['asserted_value'] = row['card_id']
        self.mutate(f'printings/{P2}/printing.json', change)
        for sheet in ('nonfoil-sheet', 'foil-sheet', 'mixed-sheet'):
            self.mutate(f'print_sheets/{sheet}/print-sheet.json', lambda d: d['entries'].append(
                dict(printing_id=P2, finish_id='nonfoil', weight=1)))
        r = self.report(request('pack_fixture.card1', kind='card'))
        self.assertEqual(exact(r['single_pack_probability']), 1)
        matches = r['target_resolution']['matched_outcomes']
        self.assertEqual({v['printing_id'] for v in matches}, {P1, P2})
        self.assertEqual(len(matches), 3)
        self.assertLess(exact(self.report()['single_pack_probability']), 1)

    def test_card_union_supports_legacy_evidenced_identity_joins(self):
        self.benchmark()
        a = self.report(request('pack_fixture.card1', kind='card'))
        self.assertEqual(exact(a['single_pack_probability']), Fraction(1, 10))

    def test_fixed_treatment_evidence_filters_without_invented_weights(self):
        self.add_treatment()
        plain = self.report()
        fixed = self.report(request(treatment_id='fictional-fixed'))
        self.assertEqual(exact(plain['single_pack_probability']), exact(fixed['single_pack_probability']))
        self.assertNotEqual(plain['input_id'], fixed['input_id'])
        self.assertNotEqual(self.report(request(finish_id='foil'))['single_pack_probability'], plain['single_pack_probability'])

    def test_ambiguous_unknown_unreviewed_and_missing_treatments_refuse(self):
        self.add_treatment(('fictional-fixed', 'fictional-alternative'))
        with self.assertRaises(PackOddsError): self.report(request(treatment_id='fictional-fixed'))
        self.reset('v02'); self.add_treatment(status='pending')
        with self.assertRaises((PackOddsError, PackSimulationError)): self.report(request(treatment_id='fictional-fixed'))
        self.reset('v02'); self.add_treatment(verified='unverified')
        with self.assertRaises((PackOddsError, PackSimulationError)): self.report(request(treatment_id='fictional-fixed'))
        self.reset('v02')
        path = self.game / 'treatments/fictional-fixed.json'; path.parent.mkdir()
        path.write_text(json.dumps(dict(id='fictional-fixed', game_id='pack_fixture', name='fictional-fixed')))
        with self.assertRaises(PackOddsError): self.report(request(treatment_id='fictional-fixed'))

    def test_treatment_provenance_and_card_join_cannot_be_forged(self):
        self.add_treatment()
        self.mutate(f'printings/{P1}/printing.json', lambda d: d['assertions'][-1].update(asserted_value=[]))
        with self.assertRaises((PackOddsError, PackSimulationError)): self.report(request(treatment_id='fictional-fixed'))
        self.reset('v02')
        self.mutate(f'printings/{P1}/printing.json', lambda d: d.update(card_id='pack_fixture.card2'))
        with self.assertRaises((PackOddsError, PackSimulationError)): self.report(request('pack_fixture.card1', kind='card'))

    def test_unconfirmed_additional_field_source_is_not_model_authorization(self):
        self.add_treatment()
        original = self.game / 'sources/fictional-definition.json'
        source = json.loads(original.read_text()); source['id'] = 'fictional-treatment-source'
        source['verification_status'] = 'unverified'
        (self.game / 'sources/fictional-treatment-source.json').write_text(json.dumps(source))
        self.mutate(f'printings/{P1}/printing.json', lambda d: d['assertions'][-1].update(source_id='fictional-treatment-source'))
        self.report()  # No treatment conclusion is requested.
        with self.assertRaises(PackOddsError): self.report(request(treatment_id='fictional-fixed'))

    def test_unverified_join_and_declared_empty_treatment_are_distinct(self):
        self.add_treatment(())
        path = self.game / 'treatments/fictional-fixed.json'
        path.parent.mkdir(exist_ok=True)
        path.write_text(json.dumps(dict(id='fictional-fixed', game_id='pack_fixture', name='fictional-fixed')))
        self.assertTrue(self.report(request(treatment_id='fictional-fixed'))['single_pack_probability']['is_zero'])
        def change(row):
            for a in row['assertions']:
                if a['path'] == '/card_id': a['verification_status'] = 'unverified'
        self.mutate(f'printings/{P1}/printing.json', change)
        with self.assertRaises(PackOddsError): self.report(request('pack_fixture.card1', kind='card'))

    def test_legacy_finish_inference_unknown_and_ambiguous_targets_refuse(self):
        self.reset('v0')
        with self.assertRaises(PackOddsError): self.report(request(finish_id='nonfoil'))
        self.reset('v02')
        for target in (request('absent'), request('absent', kind='card'), request(finish_id='absent'), request(treatment_id='absent')):
            with self.subTest(target=target), self.assertRaises(PackOddsError): self.report(target)
        original = self.game / 'cards/pack_fixture.card1/card.json'
        duplicate = self.game / 'cards/duplicate/card.json'; duplicate.parent.mkdir(); duplicate.write_bytes(original.read_bytes())
        with self.assertRaises(PackSimulationError): self.report(request('pack_fixture.card1', kind='card'))

    def test_zero_probability_and_certain_outcomes_are_not_unknown_identity(self):
        self.benchmark()
        zero = self.report(request(P3))
        self.assertTrue(zero['single_pack_probability']['is_zero'])
        self.assertEqual(zero['solver']['status'], 'IMPOSSIBLE_ZERO_PROBABILITY')
        self.mutate('print_sheets/base-sheet/print-sheet.json', lambda d: d.update(entries=[dict(printing_id=P1, weight=1)]))
        certain = self.report(request(threshold='1'))
        self.assertEqual(certain['solver']['minimum_packs'], 1)
        self.assertEqual(exact(certain['pack_results'][0]['probability']), 0)
        self.assertTrue(certain['single_pack_probability']['is_certain'])

    def test_benchmark_one_tenth_requires_seven_packs_and_proves_minimality(self):
        self.benchmark()
        r = self.report(); s = r['solver']
        self.assertEqual(exact(r['single_pack_probability']), Fraction(1, 10))
        self.assertEqual(s['status'], 'REACHED'); self.assertEqual(s['minimum_packs'], 7)
        self.assertLess(exact(s['previous_probability']), Fraction(1, 2))
        self.assertGreaterEqual(exact(s['probability']), Fraction(1, 2))

    def test_threshold_zero_one_and_exact_decimal_rational_equivalence(self):
        self.benchmark()
        self.assertEqual(self.report(request(threshold='0'))['solver']['minimum_packs'], 0)
        self.assertEqual(self.report(request(threshold='1'))['solver']['status'], 'NO_FINITE_SOLUTION')
        a = self.report(); b = self.report(request(threshold={'numerator': '2', 'denominator': '4'}))
        self.assertEqual(a, b)
        value = request(threshold=None)
        self.assertEqual(self.report(value)['solver']['status'], 'NOT_REQUESTED')

    def test_search_bound_exhaustion_is_not_impossibility(self):
        self.benchmark(1000)
        r = self.report(request(counts=(1,), threshold='0.99999'))
        self.assertEqual(r['solver']['status'], 'NOT_REACHED_WITHIN_BOUND')
        self.assertEqual(r['solver']['tested_bound'], MAX_PACKS)
        self.assertGreater(exact(r['single_pack_probability']), 0)
        self.assertLess(exact(r['solver']['probability_at_bound']), Fraction(99999, 100000))

    def test_minimum_search_matches_bounded_linear_reference(self):
        for denominator in (2, 3, 10, 17):
            self.benchmark(denominator)
            for threshold in ('0', '0.1', '0.5', '0.9', '0.99'):
                r = self.report(request(threshold=threshold))
                expected = next(n for n in range(200) if 1 - Fraction(denominator - 1, denominator) ** n >= Fraction(threshold))
                self.assertEqual(r['solver']['minimum_packs'], expected)

    def test_integer_rounding_preserves_tiny_nonzero_and_near_tie(self):
        tiny = Fraction(1, 10 ** 200)
        payload = _payload(tiny)
        self.assertEqual(exact(payload), tiny)
        self.assertEqual(payload['decimal'], '0.000000000000'); self.assertFalse(payload['is_zero'])
        above = Fraction(1, 2 * 10 ** 12) + Fraction(1, 10 ** 150)
        self.assertEqual(_payload(above)['decimal'], '0.000000000001')
        self.assertEqual(_payload(Fraction(1, 2 * 10 ** 12))['decimal'], '0.000000000000')

    def test_rounded_zero_or_one_never_controls_exact_solver_classification(self):
        self.benchmark(10 ** 18)
        rare = self.report(request(counts=(0, 1), threshold='1'))
        self.assertEqual(rare['single_pack_probability']['decimal'], '0.000000000000')
        self.assertFalse(rare['single_pack_probability']['is_zero'])
        self.assertEqual(rare['solver']['status'], 'NO_FINITE_SOLUTION')
        def change(row):
            row['entries'][0]['weight'] = 10 ** 18 - 1
            row['entries'][1]['weight'] = 1
        self.mutate('print_sheets/base-sheet/print-sheet.json', change)
        common = self.report(request(counts=(0, 1), threshold='1'))
        self.assertEqual(common['single_pack_probability']['decimal'], '1.000000000000')
        self.assertFalse(common['single_pack_probability']['is_certain'])
        self.assertEqual(common['solver']['status'], 'NO_FINITE_SOLUTION')

    def test_independence_and_dependent_collation_claims_never_override_admission(self):
        for value in (True, False, None, 'dependent', 'independent'):
            bad = request(); bad['independence'] = value
            with self.assertRaises(PackOddsError): self.report(bad)
        bad = request(); bad['box_guarantees'] = True
        with self.assertRaises(PackOddsError): self.report(bad)
        self.mutate('slots/base-slot/slot.json', lambda d: d.update(replacement=False))
        with self.assertRaises(PackSimulationError): self.view()

    def test_invalid_unselected_variant_never_hides_behind_random_sampling(self):
        self.mutate('packs/variant-c-mixed/pack-definition.json', lambda d: d.update(metadata={'simulation_model': 'dependent-box-model'}))
        with patch('simulation.pack._ticket') as random:
            with self.assertRaises(PackSimulationError): self.view()
            random.assert_not_called()

    def test_inspect_and_generate_share_rejections_for_weights_counts_and_provenance(self):
        cases = [('print_sheets/base-sheet/print-sheet.json', lambda d: d['entries'][0].update(weight=0)),
                 ('slots/base-slot/slot.json', lambda d: d.update(draw_count=True)),
                 ('slots/base-slot/slot.json', lambda d: d.update(draw_count=-1)),
                 ('sources/fictional-definition.json', lambda d: d.update(verification_status='unverified')),
                 ('packs/variant-c-mixed/pack-definition.json', lambda d: d.update(provenance=[]))]
        for path, change in cases:
            self.reset('v02'); self.mutate(path, change)
            for operation in ('inspect', 'generate'):
                with self.subTest(path=path, operation=operation), self.assertRaises(PackSimulationError):
                    owner = load_pack_simulator('pack_fixture', data_root=self.data)
                    kwargs = dict(pack_definition_id=self.pack)
                    if operation == 'generate': kwargs['seed'] = 1
                    getattr(owner, operation)('fictional-pack', **kwargs)

    def test_computation_output_and_view_budgets_refuse_predictably(self):
        self.benchmark()
        for field, limit in (('MAX_INTEGER_BITS', 8), ('MAX_TOTAL_POWER_BITS', 8), ('MAX_REPORT_BYTES', 100)):
            with self.subTest(field=field), patch('probability.pack_odds.' + field, limit), self.assertRaises(PackOddsError) as caught:
                self.report(request(counts=(100,)))
            self.assertEqual(caught.exception.code, 'RESOURCE_LIMIT')
        with patch('simulation.pack.MAX_COMPOSITION_BYTES', 100), self.assertRaises(PackSimulationError): self.view()

    def test_actual_large_exact_output_refuses_without_decimal_limit_changes(self):
        self.benchmark(2 ** 63)
        before = sys.get_int_max_str_digits()
        with self.assertRaises(PackOddsError) as caught:
            self.report(request(counts=(10000,), threshold=None))
        self.assertEqual(caught.exception.code, 'RESOURCE_LIMIT')
        self.assertEqual(sys.get_int_max_str_digits(), before)

    def test_hypothetical_box_arithmetic_is_not_a_verified_box_model(self):
        self.benchmark()
        value = request(); value['box'] = dict(packs_per_box=4, basis='HYPOTHETICAL_CALLER_DECLARATION')
        box = self.report(value)['box_arithmetic']
        self.assertEqual((box['boxes'], box['packs'], box['surplus_packs']), (2, 8, 1))
        for change in (dict(packs_per_box=0), dict(packs_per_box=True), dict(basis='VERIFIED'), dict(verified=True)):
            bad = copy.deepcopy(value); bad['box'].update(change)
            with self.assertRaises(PackOddsError): self.report(bad)

    def test_strict_thresholds_types_and_closed_shapes_refuse(self):
        for value in (0.5, True, None, '-0.1', '1.1', '.5', '5e-1', '50%', '0.1234567890123456789',
                      {'numerator': '1', 'denominator': '0'}, {'numerator': 1, 'denominator': 2},
                      {'numerator': '3', 'denominator': '2'}, {'numerator': '0' * 129, 'denominator': '1'}):
            bad = request(); bad['threshold'] = value
            with self.subTest(value=value), self.assertRaises(PackOddsError): validate_pack_odds(bad)
        for value in ([], [True], [1.0], [10001], [-1], [2, 1], [1, 1], list(range(33)), None):
            bad = request(); bad['pack_counts'] = value
            with self.assertRaises(PackOddsError): validate_pack_odds(bad)

    def test_target_fields_schema_version_and_missing_keys_refuse(self):
        for target in (None, [], {}, {'kind': 'name', 'id': P1}, {'kind': 'printing', 'id': True},
                       {'kind': 'printing', 'id': P1, 'finish_id': None},
                       {'kind': 'printing', 'id': '\ud800'}, {'kind': 'printing', 'id': 'a' * 129}):
            bad = request(); bad['target'] = target
            with self.assertRaises(PackOddsError): validate_pack_odds(bad)
        for key in request():
            if key == 'threshold': continue
            bad = request(); del bad[key]
            with self.assertRaises(PackOddsError): validate_pack_odds(bad)
        for invalid in (None, [], True, 'request'):
            with self.assertRaises(PackOddsError): validate_pack_odds(invalid)
        bad = request(); bad['schema_version'] = 'future'
        with self.assertRaises(PackOddsError): validate_pack_odds(bad)
        for path in ((), ('target',)):
            bad = request(); row = bad
            for key in path: row = row[key]
            row['approved'] = True
            with self.assertRaises(PackOddsError): validate_pack_odds(bad)

    def test_parser_refuses_duplicate_keys_nonfinite_unicode_and_byte_overflow(self):
        for raw in ('{"x":1,"x":2}', '{"x":{"a":1,"a":2}}', 'NaN', 'Infinity', b'\xff', '\ud800',
                    '[' * 2000 + '0' + ']' * 2000, b'x' * (MAX_INPUT_BYTES + 1), None):
            with self.assertRaises(PackOddsError): parse_pack_odds(raw)
        self.assertEqual(parse_pack_odds(json.dumps(request())), validate_pack_odds(request()))

    def test_views_inputs_outputs_and_source_files_remain_immutable(self):
        before = files(self.data); view = self.view(); value = request(); original = copy.deepcopy(value)
        a = assess_pack_target(view, value); saved = copy.deepcopy(a)
        with self.assertRaises(FrozenInstanceError): view._encoded = b'forged'
        with self.assertRaises(PackSimulationError): ValidatedPackComposition(b'{}')
        with self.assertRaises(PackOddsError): assess_pack_target(view.to_dict(), value)
        detached = view.to_dict(); detached['context']['sources'].clear()
        a['target_resolution']['matched_outcomes'].clear(); a['model'].clear()
        self.assertEqual(assess_pack_target(view, value), saved)
        self.assertEqual(value, original); self.assertEqual(files(self.data), before)

    def test_snapshot_is_explicit_not_implicitly_rebound_after_source_changes(self):
        view = self.view(); before = assess_pack_target(view, request())
        self.mutate('sources/fictional-definition.json', lambda d: d.update(verification_status='unverified'))
        self.assertEqual(assess_pack_target(view, request()), before)
        with self.assertRaises(PackSimulationError): self.view()

    def test_weights_target_and_source_changes_bind_distinct_model_report_identities(self):
        before = self.report()
        self.mutate('print_sheets/base-sheet/print-sheet.json', lambda d: d['entries'][0].update(weight=2))
        after = self.report()
        self.assertNotEqual(before['model']['input_id'], after['model']['input_id'])
        self.assertNotEqual(before['report_id'], after['report_id'])
        self.assertNotEqual(after['input_id'], self.report(request(P2))['input_id'])
        self.mutate('sources/fictional-definition.json', lambda d: d.update(notes='New fictional source note only.'))
        self.assertNotEqual(after['model']['composition_id'], self.report()['model']['composition_id'])

    def test_cli_api_json_parity_and_refusal_without_partial_success(self):
        from probability.draw_access import canonical_json
        raw = canonical_json(request()).encode()
        command = [sys.executable, '-B', '-m', 'probability', 'pack-target-odds', '--input', '-',
                   '--game', 'pack_fixture', '--data-root', str(self.data),
                   '--product-id', 'fictional-pack', '--definition-id', self.pack]
        run = subprocess.run(command, input=raw, cwd=ROOT, capture_output=True)
        self.assertEqual(run.returncode, 0, run.stderr)
        self.assertEqual(run.stdout, (canonical_json(self.report()) + '\n').encode())
        self.assertEqual(run.stderr, b'')
        bad = subprocess.run(command, input=b'{}', cwd=ROOT, capture_output=True)
        self.assertEqual(bad.returncode, 2); self.assertEqual(json.loads(bad.stdout)['status'], 'REFUSED')
        self.assertNotIn('single_pack_probability', json.loads(bad.stdout))

    def test_inspection_and_odds_never_sample_or_claim_production_authority(self):
        with patch('simulation.pack._ticket') as random:
            report = self.report()
            random.assert_not_called()
        self.assertFalse(report['production_authorized'])
        self.assertEqual(report['scope'], 'DECLARED_MODEL_ODDS_ONLY_NON_PRODUCTION')

    def test_current_canonical_mb2_and_unavailable_catalog_still_fail_closed(self):
        with self.assertRaises(PackSimulationError):
            load_pack_simulator().inspect('mystery_booster_2', pack_definition_id='invented')
        with self.assertRaises(PackSimulationError):
            load_pack_simulator(data_root=Path(self.temp.name) / 'missing')

    def test_current_mb2_cli_refuses_without_an_invented_pack_or_probability(self):
        command = [sys.executable, '-B', '-m', 'probability', 'pack-target-odds', '--input', '-',
                   '--product-id', 'mystery_booster_2', '--definition-id', 'invented']
        run = subprocess.run(command, input=json.dumps(request()).encode(), cwd=ROOT, capture_output=True)
        self.assertEqual(run.returncode, 2)
        result = json.loads(run.stdout)
        self.assertEqual(result['status'], 'REFUSED'); self.assertEqual(result['code'], 'MODEL_NOT_READY')
        self.assertIn('ADMITTED_PACK_DEFINITION_MISSING', result['reason'])
        self.assertNotIn('single_pack_probability', result)


if __name__ == '__main__':
    unittest.main()
