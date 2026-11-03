"""Hypothetical substitution tests; no game observations or semantic approvals."""
from copy import deepcopy
from dataclasses import FrozenInstanceError
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from card_rules_pilot import contract as c, mana_scenario as api, mana_scenario_policy as p
from card_rules_pilot import land_explanation, land_decision
from land_test_support import ROOT, current_catalog_intact
from test_land_decision import decision_arguments, cli_arguments


def scenario(count=None, colors=None):
    rows = []
    if count is not None: rows.append(dict(dimension='controlled_swamp_count', value=count))
    if colors is not None: rows.append(dict(dimension='commander_color_identity', value=colors))
    return p.make_scenario(rows).to_dict()


def descriptor(pattern='swamp_count_dependent'):
    # Pure synthetic policy premise, not evidence admission or a new Card reading.
    return dict(pattern=pattern, dependencies=['controlled_swamp_count', 'available_payment'],
        written_instruction='Add {B} for each Swamp you control.', written_cost='{2}, {T}',
        ownership='no_additional_effect', damage_clause=None)


class ScenarioContractTests(unittest.TestCase):
    def test_counts_zero_one_and_positive_finite_bound(self):
        for count in (0, 1, 2, 5, 37, p.COUNT_LIMIT):
            result = p.compute(descriptor=descriptor(), scenario=scenario(count=count))
            self.assertEqual(result['state'], 'SUPPLIED')
            self.assertEqual(result['conditional_written_output'], dict(kind='HYPOTHETICAL_WRITTEN_QUANTITY', quantity=count, mana_symbol='B'))
            self.assertEqual(result['written_cost'], '{2}, {T}')
            self.assertFalse(result['canonical_admission'])
            self.assertEqual(result['execution_authority'], 'BLOCKED')
            self.assertEqual(result['missing_inputs'], [])
        missing = p.compute(descriptor=descriptor(), scenario=scenario())
        self.assertEqual(missing['state'], 'UNSPECIFIED')
        self.assertIsNone(missing['conditional_written_output'])
        self.assertEqual(missing['missing_inputs'], ['controlled_swamp_count'])

    def test_invalid_counts_strict_types_and_bounds(self):
        for value in (-1, True, False, 1.0, '5', None, [], {}, p.COUNT_LIMIT + 1, 2**64):
            with self.subTest(value=value), self.assertRaises(ValueError):
                p.make_scenario([dict(dimension='controlled_swamp_count', value=value)])

    def test_colors_explicit_empty_and_missing(self):
        desc = dict(pattern='commander_color_context_dependent', dependencies=['commander_color_identity'],
            written_instruction='Restricted written color choice', written_cost='{T}', ownership='no_additional_effect', damage_clause=None)
        for colors in ([], ['W'], ['B'], ['W', 'B'], list(p.COLORS)):
            value = p.compute(descriptor=desc, scenario=scenario(colors=colors))
            self.assertEqual(value['state'], 'SUPPLIED')
            self.assertEqual(value['conditional_written_output']['colors'], colors)
            self.assertTrue(value['conditional_written_output']['empty_set_does_not_establish_actual_unusability'])
        value = p.compute(descriptor=desc, scenario=scenario())
        self.assertEqual(value['state'], 'UNSPECIFIED'); self.assertIsNone(value['conditional_written_output'])
        for colors in (['W', 'W'], ['C'], ['X'], ['white'], ['B', 'W'], 'WB', [True], None, {}):
            with self.subTest(colors=colors), self.assertRaises(ValueError):
                p.make_scenario([dict(dimension='commander_color_identity', value=colors)])

    def test_conflicts_do_not_select_a_value_and_duplicate_entries_reject(self):
        values = [dict(dimension='controlled_swamp_count', value=n) for n in (0, 5)]
        value = p.compute(descriptor=descriptor(), scenario=p.make_scenario(values).to_dict())
        self.assertEqual(value['state'], 'CONFLICTING'); self.assertIsNone(value['conditional_written_output'])
        self.assertEqual(value['supplied_assumptions'], values)
        with self.assertRaises(ValueError): p.make_scenario([values[0], values[0]])
        colors = p.make_scenario([dict(dimension='commander_color_identity', value=x) for x in ([], ['W'])]).to_dict()
        desc = dict(pattern='commander_color_context_dependent', dependencies=['commander_color_identity'],
            written_instruction='Restricted choice', written_cost='{T}', ownership='no_additional_effect', damage_clause=None)
        self.assertEqual(p.compute(descriptor=desc, scenario=colors)['state'], 'CONFLICTING')

    def test_strict_closed_canonical_input_and_independent_views(self):
        doc = p.make_scenario([]); raw = doc.to_json()
        doc.to_dict()['assumptions'].append(dict(dimension='controlled_swamp_count', value=7))
        self.assertEqual(doc.to_json(), raw)
        self.assertEqual(p.parse_scenario(raw.encode()).to_json(), raw)
        for raw in (b'{"schema_version":1,"schema_version":2}\n', b'{}', b'{"value":NaN}\n'):
            with self.assertRaises(ValueError): p.parse_scenario(raw)
        for value in ({}, {'assumptions': []}, True, {'state': 'observed'}):
            with self.assertRaises(ValueError): p.validate_scenario(value)
        changed = doc.to_dict(); changed['observed_game_state'] = {}
        changed = c.seal(p.INPUT_VERSION, changed, 'scenario_id')
        with self.assertRaises(ValueError): p.validate_scenario(changed)
        for dimension in ('available_payment', 'legal_target_land', 'net_mana', 'untapped', 'commander'):
            with self.assertRaisesRegex(ValueError, 'UNSUPPORTED'):
                p.make_scenario([dict(dimension=dimension, value=0)])
        desc = descriptor(); desc['card_name'] = 'prepared answer'
        with self.assertRaises(ValueError): p.compute(descriptor=desc, scenario=scenario(count=5))


class ActualManaScenarioTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.intact = current_catalog_intact(unittest.TestCase())
        cls.consumer = api.load_mana_scenarios(**decision_arguments()) if cls.intact else None

    def admitted(self):
        if self.intact: return True
        # Real expanded writer catalog rejects, without fixture substitution.
        with self.assertRaises(ValueError): api.load_mana_scenarios(**decision_arguments())
        return False

    def row(self, sid, inputs=None):
        return self.consumer.evaluate(sid, inputs).to_dict()['subjects'][0]

    def test_all_nine_subjects_four_comparisons_and_preserved_ownership(self):
        if not self.admitted(): return
        self.assertEqual(self.consumer.subject_ids, land_decision.SUBJECT_IDS)
        for sid in self.consumer.subject_ids:
            row = self.row(sid)
            self.assertEqual(row['calculation']['state'], 'UNSPECIFIED')
            self.assertEqual(row['provenance']['candidate_id'], dict(land_decision.CANDIDATE_IDS)[sid])
            self.assertEqual(row['calculation']['execution_authority'], 'BLOCKED')
        port = self.row('port-utility')['calculation']; mana = self.row('port-mana')['calculation']
        self.assertEqual(port['written_cost'], '{1}, {T}'); self.assertIsNone(port['conditional_written_output'])
        self.assertEqual(mana['written_cost'], '{T}'); self.assertEqual(mana['conditional_written_output']['mana_symbol'], 'C')
        city = self.row('city-damage-trigger')['calculation']; citadel = self.row('citadel-color-choice')['calculation']
        self.assertEqual(city['ownership'], 'separate_triggered_ability'); self.assertIsNone(city['conditional_written_output'])
        self.assertEqual(citadel['ownership'], 'same_ability_additional_effect'); self.assertEqual(citadel['written_cost'], '{T}')
        self.assertIsNotNone(citadel['conditional_damage_clause_not_executed'])
        self.assertIsNone(self.row('citadel-colorless')['calculation']['conditional_damage_clause_not_executed'])
        for name in self.consumer.comparison_names:
            self.assertIsNotNone(self.consumer.compare(name).to_dict()['comparison'])

    def test_actual_count_colors_comparisons_and_no_context_leakage(self):
        if not self.admitted(): return
        for count in (0, 1, 5, 19):
            row = self.row('coffers-mana', scenario(count=count))['calculation']
            self.assertEqual(row['conditional_written_output']['quantity'], count)
            self.assertEqual(row['written_cost'], '{2}, {T}')
        for colors in ([], ['W', 'B'], list(p.COLORS)):
            row = self.row('tower-mana', scenario(colors=colors))['calculation']
            self.assertEqual(row['conditional_written_output']['colors'], colors)
        for name, inputs, subject in (('variable-output', scenario(count=5), 'snow-wastes-mana'),
                ('color-context', scenario(colors=['W', 'B']), 'city-mana')):
            value = self.consumer.compare(name, inputs).to_dict()
            other = next(r for r in value['subjects'] if r['subject_id'] == subject)
            self.assertEqual(other['calculation']['supplied_assumptions'], [])
            self.assertEqual(other['calculation']['state'], 'UNSPECIFIED')
            self.assertEqual(value['state'], 'SUPPLIED')
        conflicting = p.make_scenario([dict(dimension='controlled_swamp_count', value=n) for n in (0, 5)]).to_dict()
        compared = self.consumer.compare('variable-output', conflicting).to_dict()
        self.assertEqual(compared['state'], 'CONFLICTING')
        self.assertIsNone(next(r for r in compared['subjects'] if r['subject_id'] == 'coffers-mana')['calculation']['conditional_written_output'])
        self.assertEqual(next(r for r in compared['subjects'] if r['subject_id'] == 'snow-wastes-mana')['calculation']['conditional_written_output']['quantity'], 1)
        for sid, inputs in (('tower-mana', scenario(count=5)), ('coffers-mana', scenario(colors=[])),
                ('port-utility', scenario(count=0)), ('city-mana', scenario(colors=['W']))):
            with self.assertRaisesRegex(ValueError, 'UNSUPPORTED'): self.consumer.evaluate(sid, inputs)
        with self.assertRaises(ValueError): self.consumer.compare('variable-output', scenario(count=5, colors=[]))
        for sid in ('foreign', True, None, []):
            with self.assertRaisesRegex(ValueError, 'UNSUPPORTED'): self.consumer.evaluate(sid)
        with self.assertRaises(ValueError): self.consumer.compare('best-land')

    def test_generic_results_independent_of_card_and_subject_labels(self):
        if not self.admitted(): return
        # Four different admitted subjects share the same generic fixed-output
        # calculation despite different labels, source bindings and siblings.
        results = [self.row(sid)['calculation'] for sid in ('snow-wastes-mana', 'port-mana', 'citadel-colorless')]
        self.assertTrue(all(r == results[0] for r in results))
        before = p.policy_document(); changed = p.policy_document(); changed.clear()
        self.assertEqual(p.policy_document(), before)

    def test_no_fabricated_gameplay_and_material_unknowns(self):
        if not self.admitted(): return
        for sid in self.consumer.subject_ids:
            calc = self.row(sid)['calculation']
            self.assertIn('actual mana production', calc['unsupported_conclusions'])
            self.assertIn('net usable mana', calc['unsupported_conclusions'])
            self.assertIn('payment feasibility', calc['unsupported_conclusions'])
            self.assertIn('legal action', calc['unsupported_conclusions'])
            self.assertTrue(calc['unknown_game_inputs'])
            self.assertNotIn('actual_output', calc)

    def test_reports_exact_validation_ownership_size_and_readable_parity(self):
        if not self.admitted(): return
        documents = [self.consumer.evaluate(sid) for sid in self.consumer.subject_ids] + [self.consumer.check()]
        documents += [self.consumer.evaluate('coffers-mana', scenario(count=n)) for n in (0, 5)]
        documents += [self.consumer.evaluate('tower-mana', scenario(colors=x)) for x in ([], ['W', 'B'])]
        documents += [self.consumer.compare(name, scenario(count=5) if name == 'variable-output' else scenario(colors=['W', 'B']) if name == 'color-context' else None) for name in self.consumer.comparison_names]
        for doc in documents:
            value = doc.to_dict(); rendered = api.render_mana_scenario(doc)
            self.assertLessEqual(len(doc.to_json().encode()), api.REPORT_LIMIT)
            self.assertLessEqual(len(rendered.encode()), api.READABLE_LIMIT)
            self.assertEqual(self.consumer.validate_report(value).to_json(), doc.to_json())
            self.assertEqual(self.consumer.parse_report(doc.to_json().encode()).to_json(), doc.to_json())
            for row in value['subjects']:
                self.assertIn(row['accepted_explanation_id'], rendered)
                for unknown in row['calculation']['unknown_game_inputs']: self.assertIn(unknown, rendered)
                self.assertIn(row['calculation']['calculation_id'], rendered)
            changed = deepcopy(value); changed['subjects'][0]['calculation']['conditional_written_output'] = {'actual_mana': 999}
            changed['subjects'][0]['calculation'] = c.seal(p.RESULT_VERSION, changed['subjects'][0]['calculation'], 'calculation_id')
            changed = c.seal(api.REPORT_VERSION, changed, 'report_id')
            with self.assertRaises(ValueError): self.consumer.validate_report(changed)
            value.clear(); self.assertTrue(doc.to_dict())
        with self.assertRaises(FrozenInstanceError): self.consumer._snapshot = b'{}'
        with self.assertRaises(TypeError): api.ManaScenarioConsumer(b'{}')
        with self.assertRaises(ValueError): self.consumer.parse_report(b'{"kind":1,"kind":2}\n')

    def test_detailed_evidence_historical_explanation_and_single_admission(self):
        if not self.admitted(): return
        with patch.object(land_explanation, 'load_land_explanations', wraps=land_explanation.load_land_explanations) as load:
            batch = api.load_mana_scenarios(**decision_arguments())
            self.assertEqual(load.call_count, 1)
            for sid in batch.subject_ids: batch.evaluate(sid)
            self.assertEqual(load.call_count, 1)
        overview = batch.detailed(batch.check().to_dict()['full_evidence_reference'])
        self.assertEqual(hashlib.sha256(overview.to_json().encode()).hexdigest(), land_decision.OVERVIEW_SHA256)
        original = land_explanation.load_land_explanations(**decision_arguments())
        for sid in batch.subject_ids:
            self.assertEqual(self.row(sid)['accepted_explanation_id'], original.explain_subject(sid).to_dict()['report_id'])
        reference = batch.check().to_dict()['full_evidence_reference']; reference['bytes'] += 1
        with self.assertRaises(ValueError): batch.detailed(reference)

    def test_actual_tampered_evidence_and_owner_decision_reject_fresh_admission(self):
        if not self.admitted(): return
        for root_key, filename in (('cohort_root', 'interpretations.json'), ('decision_root', land_decision.OWNER_RECORD)):
            with tempfile.TemporaryDirectory() as directory:
                root = Path(directory) / 'evidence'; shutil.copytree(decision_arguments()[root_key], root)
                before = api.load_mana_scenarios(**decision_arguments(**{root_key: root})).evaluate('coffers-mana', scenario(count=5)).to_json()
                path = root / filename; record = c.read_json(path)
                own = 'interpretations_id' if root_key == 'cohort_root' else 'decision_id'
                if root_key == 'cohort_root':
                    record['candidates'][0]['descriptive_readings']['output']['written_instruction'] = 'foreign'
                    candidate = record['candidates'][0]; record['candidates'][0] = c.seal(candidate['schema_version'], candidate, 'candidate_id')
                else: record['scope']['accepted'] = []
                record = c.seal(record['schema_version'], record, own); path.write_bytes(c.canonical(record))
                if root_key == 'cohort_root':
                    from card_rules_pilot import land_authored
                    (root / 'manifest.json').write_bytes(c.canonical(land_authored.build_manifest(c.read_json(root / 'plan.json'), record)))
                with self.assertRaises(ValueError): api.load_mana_scenarios(**decision_arguments(**{root_key: root}))
                self.assertEqual(self.consumer.evaluate('coffers-mana', scenario(count=5)).to_json(), before)
        with self.assertRaises(ValueError): api.load_mana_scenarios(**decision_arguments(expected_decision_id='sha256:'+'0'*64))

    def test_real_cli_determinism_conflicts_errors_and_read_only(self):
        if not self.admitted(): return
        def run(*options):
            return subprocess.run([sys.executable, '-m', 'card_rules_pilot.mana_scenario_cli', '--review-root', str(ROOT/'reference-reviews'), 'subject', *cli_arguments(), 'coffers-mana', *options], cwd=ROOT, capture_output=True, env=dict(os.environ, PYTHONPATH=str(ROOT/'src'), PYTHONDONTWRITEBYTECODE='1'))
        def snapshot():
            return {str(path): hashlib.sha256(path.read_bytes()).hexdigest() for root in (ROOT/'data/review', ROOT/'reference-reviews') for path in root.rglob('*') if path.is_file()}
        before = snapshot()
        doc = self.consumer.evaluate('coffers-mana', scenario(count=5))
        result = run('--swamp-count', '5', '--json'); self.assertEqual(result.returncode, 0, result.stderr); self.assertEqual(result.stdout, doc.to_json().encode())
        result = run('--swamp-count', '5'); self.assertEqual(result.stdout.decode(), api.render_mana_scenario(doc))
        result = run('--swamp-count', '0', '--swamp-count', '5', '--json'); self.assertEqual(result.returncode, 3); self.assertEqual(json.loads(result.stdout)['state'], 'CONFLICTING')
        for value in ('-1', 'true', '1.0', '01', '1000001'):
            result = run('--swamp-count', value); self.assertEqual(result.returncode, 2); self.assertEqual(result.stdout, b'')
        self.consumer.check(); self.consumer.provenance('coffers-mana')
        self.assertEqual(snapshot(), before)

if __name__ == '__main__': unittest.main()
