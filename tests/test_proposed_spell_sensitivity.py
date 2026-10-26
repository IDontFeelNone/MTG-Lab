"""Bounded hypothetical sensitivity over actual admitted fictional evidence."""
from copy import deepcopy
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from gameplay_rules.errors import GameplayContractError
from proposed_spell_packets import conditions as c
from proposed_spell_packets import sensitivity as s
from proposed_spell_packets import validation as v
from proposed_spell_packets.authoring import Workspace


ROOT = Path(__file__).resolve().parents[1]
SAT = 'SATISFIED_UNDER_HYPOTHESIS'
NOT = 'NOT_SATISFIED_UNDER_HYPOTHESIS'
INDET = 'INDETERMINATE_UNDER_HYPOTHESIS'


class MissingInputSensitivityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.seed = tempfile.TemporaryDirectory()
        cls.addClassCleanup(cls.seed.cleanup)
        cls.seed_path = Path(cls.seed.name)
        cls.examples = {name: json.loads((v.PACKAGE_ROOT / name).read_bytes())
                        for name in v.PACKET_NAMES}
        workspace = Workspace(cls.seed_path)
        for name in v.PACKET_NAMES:
            workspace.record(sealed=v.PACKAGE_ROOT / name)

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.directory = self.root / 'pilot'
        shutil.copytree(self.seed_path, self.directory)
        self.workspace = Workspace(self.directory)
        self.serial = 0

    def packet(self, name='packet-b-missing.json'):
        return deepcopy(self.examples[name])

    def path(self, identity):
        return self.directory / 'packets' / (identity[7:] + '.json')

    def successor(self, base):
        packet = deepcopy(base)
        packet['revision'] += 1
        packet['history'].update(supersedes_packet_ids=[base['packet_id']], review_observations=[])
        return packet

    def record(self, packet):
        # Every authored fixture is admitted by the existing actual boundary.
        v.seal_packet(packet)
        self.serial += 1
        path = self.root / ('authored-' + str(self.serial) + '.json')
        path.write_bytes(v._canonical_candidate(packet))
        self.workspace.record(sealed=path)
        return packet

    def add_claim(self, packet, claim_id, value, *, condition='PRESENT', alternative=None,
                  predicate=None, subject=None):
        row = deepcopy(packet['claims'][0])
        row.update(claim_id=claim_id, role='STATE', condition=condition, value=value,
                   alternative_id=alternative, predicate=predicate or ('Opaque key ' + claim_id),
                   subject_id=subject or packet['contexts'][0]['object_id'],
                   limitation_refs=[], rule_context_refs=[])
        row['attribution']['statement_id'] = 'statement-' + claim_id
        if condition in ('UNKNOWN', 'UNSUPPORTED'):
            row['limitation_refs'] = [claim_id + '-limit']
            packet['limitations'].append({'limitation_id': claim_id + '-limit', 'kind': condition,
                'context_ids': ['ctx'], 'claim_refs': [claim_id], 'step_refs': [],
                'description': 'Explicit authored fictional input limitation.'})
        packet['claims'].append(row)
        return row

    @staticmethod
    def leaf(operand_id, refs=None, expected=True):
        return {'operand_id': operand_id, 'claim_refs': refs or [operand_id], 'expected': expected}

    def model(self, packet, leaves=None, alternative=None):
        return c.seal_model({'model_version': c.MODEL_VERSION,
            'authority': 'AUTHORED_FICTIONAL_CONDITION', 'condition_id': 'sensitivity-test',
            'condition_name': 'Explicit fictional sensitivity condition',
            'packet': {key: packet[key] for key in c.PACKET_FIELDS},
            'scope': {'context_id': 'ctx', 'context_version': 1, 'alternative_id': alternative},
            'operator': 'ALL_OF', 'operands': leaves or [self.leaf('premise'), self.leaf('beacon')]})

    def analyze(self, packet, model=None):
        report = s.analyze(self.workspace, packet['packet_id'], model or self.model(packet))
        view = report.to_dict()
        self.assertEqual(report.canonical_bytes, v._canonical_candidate(view))
        self.assertEqual(view['report_id'], v.identity(view['report_version'], view, 'report_id'))
        self.assertEqual(report.report_id, view['report_id'])
        self.assertEqual(view['authority'], 'HYPOTHETICAL_CONDITION_SENSITIVITY_ONLY')
        self.assertEqual(view['execution_authority'], 'BLOCKED')
        self.assertEqual(view['baseline_result_id'], view['baseline']['result_id'])
        self.assertEqual(view['sensitivity']['case_count'], len(view['sensitivity']['cases']))
        for case in view['sensitivity']['cases']:
            self.assertNotIn('result_id', case)
            self.assertTrue(case['hypothetical_result'].endswith('_UNDER_HYPOTHESIS'))
            self.assertTrue(case['aggregate_explanation'])
            self.assertTrue(case['affected_operand_change']['explanation'])
            self.assertEqual(case['evidence_ref']['baseline_result_id'], view['baseline_result_id'])
            self.assertEqual([row['claim_id'] for row in case['assumptions']], case['unknown_claim_ids'])
            self.assertTrue(all(type(row['value']) is bool and row['value'] is case['assumed_value']
                                for row in case['assumptions']))
            for operand in case['operands']:
                self.assertNotIn('assertions', operand)
        return view

    def files(self):
        return {p.relative_to(self.directory).as_posix(): p.read_bytes()
                for p in self.directory.rglob('*') if p.is_file()}

    @staticmethod
    def operand(case, operand_id):
        return next(row for row in case['operands'] if row['operand_id'] == operand_id)

    def test_original_b_actual_cli_baseline_and_false_expectation(self):
        packet = self.packet()
        model = self.model(packet)
        path = self.root / 'model.json'
        path.write_text(json.dumps(model) + '\n')
        command = [sys.executable, '-m', 'proposed_spell_packets', '--workspace', str(self.directory),
                   'sensitivity', packet['packet_id'], '--model', str(path)]
        before = self.files()
        model_bytes = path.read_bytes()
        outputs = []
        for arguments in (command, command + ['--json']):
            process = subprocess.run(arguments, cwd=ROOT, env=dict(os.environ, PYTHONPATH=str(ROOT / 'src')),
                                     capture_output=True, text=True)
            self.assertEqual(process.returncode, 0, process.stdout + process.stderr)
            outputs.append(process.stdout)
        report = self.analyze(packet, model)
        self.assertEqual(json.loads(outputs[1]), report)
        self.assertIn('HYPOTHETICAL_CONDITION_SENSITIVITY_ONLY', outputs[0])
        self.assertIn('INDETERMINATE', outputs[0])
        self.assertIn(SAT, outputs[0])
        self.assertIn(NOT, outputs[0])
        self.assertEqual(report['baseline'], c.evaluate(self.workspace, packet['packet_id'], model).to_dict())
        self.assertEqual(report['baseline']['computed_result'], 'INDETERMINATE')
        self.assertEqual([case['hypothetical_result'] for case in report['sensitivity']['cases']], [SAT, NOT])
        self.assertEqual([case['assumed_value'] for case in report['sensitivity']['cases']], [True, False])
        original = report['baseline']['operands'][1]['assertions'][0]
        self.assertEqual((original['condition'], original['value']), ('UNKNOWN', None))
        false = self.analyze(packet, self.model(packet, [self.leaf('beacon', expected=False)]))
        self.assertEqual([case['hypothetical_result'] for case in false['sensitivity']['cases']], [NOT, SAT])
        self.assertEqual(self.files(), before)
        self.assertEqual(path.read_bytes(), model_bytes)

    def test_multiple_unknowns_complete_uniform_groups_and_independent_case_order(self):
        packet = self.successor(self.packet())
        beacon = next(row for row in packet['claims'] if row['claim_id'] == 'beacon')
        self.add_claim(packet, 'beacon-two', None, condition='UNKNOWN',
                       subject=beacon['subject_id'], predicate=beacon['predicate'])
        self.add_claim(packet, 'other', None, condition='UNKNOWN')
        packet = self.record(packet)
        # Explicit model reference order must survive in exact hypothesis coverage.
        leaves = [self.leaf('other'), self.leaf('beacon', ['beacon-two', 'beacon'])]
        report = self.analyze(packet, self.model(packet, leaves))
        cases = report['sensitivity']['cases']
        self.assertEqual([(case['selected_operand_id'], case['assumed_value']) for case in cases],
                         [('other', True), ('other', False), ('beacon', True), ('beacon', False)])
        self.assertEqual([case['sequence'] for case in cases], [1, 2, 3, 4])
        for case in cases:
            selected = case['selected_operand_id']
            other = 'beacon' if selected == 'other' else 'other'
            self.assertEqual(case['unknown_claim_ids'], leaves[0 if selected == 'other' else 1]['claim_refs'])
            self.assertEqual(case['hypothetical_result'], INDET)
            self.assertEqual(case['remaining_unresolved_operands'], [other])
            self.assertTrue(all(not row['hypothesized'] and row['effective_value'] is None
                                for row in self.operand(case, other)['assertion_evaluations']))
            self.assertEqual({row['effective_value'] for row in self.operand(case, selected)['assertion_evaluations']},
                             {case['assumed_value']})
        self.assertEqual(report['baseline']['computed_result'], 'INDETERMINATE')

    def test_known_mismatch_and_mixed_known_unknown_group_keep_existing_assertions(self):
        packet = self.successor(self.packet())
        beacon = next(row for row in packet['claims'] if row['claim_id'] == 'beacon')
        self.add_claim(packet, 'known-lit', True, subject=beacon['subject_id'], predicate=beacon['predicate'])
        packet = self.record(packet)
        leaves = [self.leaf('beacon', ['known-lit', 'beacon'])]
        cases = self.analyze(packet, self.model(packet, leaves))['sensitivity']['cases']
        self.assertEqual([case['hypothetical_result'] for case in cases], [SAT, INDET])
        self.assertEqual([self.operand(case, 'beacon')['status'] for case in cases], ['MATCH', 'UNRESOLVED'])
        self.assertIn('OPPOSING_BOOLEAN_ASSERTIONS', json.dumps(cases[1]['operands']))
        for case in cases:
            known = self.operand(case, 'beacon')['assertion_evaluations'][0]
            self.assertEqual((known['claim_id'], known['effective_value'], known['hypothesized']),
                             ('known-lit', True, False))
        # A different known requirement is unmet under both independent hypotheses.
        leaves.insert(0, self.leaf('known-unmet', ['premise'], expected=False))
        report = self.analyze(packet, self.model(packet, leaves))
        for case in report['sensitivity']['cases']:
            self.assertNotEqual(case['hypothetical_result'], SAT)
            self.assertEqual(case['known_mismatches'], [{'operand_id': 'known-unmet', 'claim_refs': ['premise']}])
            self.assertIn('known-unmet', case['aggregate_explanation'])
            self.assertEqual(self.operand(case, 'known-unmet')['status'], 'MISMATCH')

    def test_declared_conflict_unsupported_and_nonboolean_cannot_be_resolved(self):
        packet = self.successor(self.packet('packet-d-conflict.json'))
        self.add_claim(packet, 'missing', None, condition='UNKNOWN')
        self.add_claim(packet, 'uncomputed', None, condition='UNSUPPORTED')
        self.add_claim(packet, 'string-input', 'true')
        self.add_claim(packet, 'known-negative', False)
        packet = self.record(packet)
        leaves = [self.leaf('dispute', ['lit', 'unlit'])] + [self.leaf(key) for key in
                  ('missing', 'uncomputed', 'string-input', 'known-negative')]
        report = self.analyze(packet, self.model(packet, leaves))
        self.assertEqual(report['sensitivity']['case_count'], 2)
        for case in report['sensitivity']['cases']:
            self.assertEqual(case['unknown_claim_ids'], ['missing'])
            self.assertEqual(case['hypothetical_result'], INDET)
            self.assertEqual(case['remaining_unresolved_operands'], ['dispute', 'uncomputed', 'string-input'])
            kinds = {finding['kind'] for row in case['operands'] for finding in row['findings']}
            self.assertEqual(kinds, {'DECLARED_CONFLICT', 'OPPOSING_BOOLEAN_ASSERTIONS',
                                     'UNSUPPORTED_ASSERTION', 'UNSUPPORTED_BOOLEAN_INPUT'})
            dispute = self.operand(case, 'dispute')['assertion_evaluations']
            self.assertEqual([row['effective_value'] for row in dispute], [True, False])
            self.assertTrue(all(not row['hypothesized'] for row in dispute))
            self.assertEqual(case['known_mismatches'],
                             [{'operand_id': 'known-negative', 'claim_refs': ['known-negative']}])
        self.assertIn('fictional:d:observer-one', json.dumps(report['baseline']))
        self.assertIn('fictional:d:observer-two', json.dumps(report['baseline']))
        self.assertEqual(report['baseline']['packet_context']['authored_conclusion'], packet['conclusion'])

    def test_general_matching_alternative_and_foreign_exclusion_are_complete(self):
        packet = self.successor(self.packet('packet-e-compatibility.json'))
        common = self.add_claim(packet, 'common', None, condition='UNKNOWN', predicate='Exact opaque key')
        self.add_claim(packet, 'matching', None, condition='UNKNOWN', alternative='soften', predicate=common['predicate'])
        self.add_claim(packet, 'foreign', None, condition='UNKNOWN', alternative='brighten', predicate=common['predicate'])
        packet = self.record(packet)
        for alternative, refs in ((None, ['common']), ('soften', ['matching', 'common'])):
            with self.subTest(alternative=alternative):
                report = self.analyze(packet, self.model(packet, [self.leaf('fact', refs)], alternative))
                self.assertEqual([case['unknown_claim_ids'] for case in report['sensitivity']['cases']], [refs, refs])
                self.assertEqual([case['hypothetical_result'] for case in report['sensitivity']['cases']], [SAT, NOT])
                self.assertEqual(report['scope']['alternative_id'], alternative)
        for refs, alternative in ((['common'], 'soften'), (['matching'], 'soften'),
                                  (['common', 'matching', 'foreign'], 'soften'), (['foreign'], None)):
            with self.subTest(refs=refs), self.assertRaises(GameplayContractError):
                self.analyze(packet, self.model(packet, [self.leaf('fact', refs)], alternative))

    def test_zero_selected_unknown_cases_does_not_imply_complete_knowledge(self):
        packet = self.packet()
        for refs, expected_result in ((['premise'], 'SATISFIED_UNDER_ASSERTIONS'), (['flash'], 'INDETERMINATE')):
            with self.subTest(refs=refs):
                report = self.analyze(packet, self.model(packet, [self.leaf('selected', refs)]))
                self.assertEqual(report['sensitivity'], {'status': 'NOT_APPLICABLE_NO_SELECTED_UNKNOWN_CLAIMS',
                                                       'case_count': 0, 'cases': []})
                self.assertEqual(report['baseline']['computed_result'], expected_result)
                self.assertIn('missing-beacon', json.dumps(report['baseline']['packet_context']))
                self.assertIn('BLOCKED', s.render(s.analyze(self.workspace, packet['packet_id'],
                                                          self.model(packet, [self.leaf('selected', refs)]))))

    def test_invalid_models_bindings_and_tampered_actual_inputs_fail_closed(self):
        packet = self.packet()
        original = self.model(packet)
        mutations = []
        for field, value in (('packet_id', 'sha256:' + '0' * 64), ('revision', 2),
                             ('contract_id', 'sha256:' + '0' * 64)):
            changed = deepcopy(original); changed['packet'][field] = value; mutations.append(changed)
        for field, value in (('context_version', 2), ('context_id', 'other'), ('alternative_id', 'foreign')):
            changed = deepcopy(original); changed['scope'][field] = value; mutations.append(changed)
        changed = deepcopy(original); changed['operands'][1]['claim_refs'] = ['dangling']; mutations.append(changed)
        for changed in mutations:
            with self.subTest(binding=changed), self.assertRaises(GameplayContractError):
                self.analyze(packet, c.seal_model({key: value for key, value in changed.items() if key != 'model_id'}))
        for expected in (0, 1, 0.0, 1.0, 'true', None):
            changed = deepcopy(original); changed['operands'][0]['expected'] = expected
            with self.subTest(expected=expected), self.assertRaises(GameplayContractError):
                s.analyze(self.workspace, packet['packet_id'], changed)
        stale = deepcopy(original); stale['operands'][0]['expected'] = False
        with self.assertRaises(GameplayContractError):
            self.analyze(packet, stale)
        for identity in ('latest', 1, True, None, {'packet_id': packet['packet_id']}):
            with self.subTest(identity=identity), self.assertRaises(GameplayContractError):
                s.analyze(self.workspace, identity, original)
        path = self.path(packet['packet_id'])
        raw = path.read_bytes()
        path.write_bytes(raw + b' ')
        with self.assertRaises(GameplayContractError):
            self.analyze(packet)
        path.write_bytes(raw)
        child = self.record(self.successor(packet))
        path.write_bytes(raw.replace(b'"UNKNOWN"', b'"PRESENT"', 1))
        with self.assertRaises(GameplayContractError):
            self.analyze(child)
        path.write_bytes(raw)
        edited_root = self.packet(); edited_root['conclusion']['text'] += ' Unparented edit.'
        v.seal_packet(edited_root); self.path(edited_root['packet_id']).write_bytes(v._canonical_candidate(edited_root))
        with self.assertRaises(GameplayContractError):
            self.analyze(edited_root)
        # Actual source/contract bindings remain fresh, never hypothetical gaps.
        retained = self.root / 'retained'; shutil.copytree(v.PACKAGE_ROOT, retained)
        loader = v.load_package
        with patch.object(v, 'load_package', side_effect=lambda: loader(retained)):
            contract = retained / 'contract.json'; contract.write_bytes(contract.read_bytes() + b' ')
            with self.assertRaises(GameplayContractError):
                self.analyze(child)

    def test_private_ownership_one_fresh_read_determinism_relocation_and_read_only(self):
        packet = self.packet()
        model = self.model(packet)
        owned = c.ConditionModel.from_dict(model)
        path = self.root / 'model.json'; path.write_bytes(owned.canonical_bytes)
        file_owned = c.read_model(path)
        before = self.files()
        retained_before = {p.relative_to(v.REVIEW_ROOT).as_posix(): p.read_bytes()
                           for p in v.REVIEW_ROOT.rglob('*') if p.is_file()}
        captured = []
        actual_read = self.workspace.read
        def read(identity):
            result = actual_read(identity)
            captured.append(result)
            return result
        with patch.object(self.workspace, 'read', side_effect=read) as boundary:
            report = s.analyze(self.workspace, packet['packet_id'], owned)
            self.assertEqual(boundary.call_count, 1)
            boundary.assert_called_once_with(packet['packet_id'])
        raw = report.canonical_bytes
        model['operands'][0]['expected'] = False
        packet['claims'][0]['value'] = 'changed caller'
        captured[0][0]['claims'][0]['value'] = 'changed validated view'
        captured[0][1].clear()
        path.write_text('{}')
        decoded = report.to_dict(); decoded['sensitivity']['cases'].clear(); decoded['baseline'].clear()
        self.assertEqual(report.canonical_bytes, raw)
        self.assertNotIn('changed validated view', json.dumps(report.to_dict()))
        self.assertNotIn('changed caller', json.dumps(report.to_dict()))
        self.assertEqual(s.analyze(self.workspace, self.packet()['packet_id'], file_owned).canonical_bytes, raw)
        relocated = self.root / 'relocated'; shutil.copytree(self.directory, relocated)
        self.assertEqual(s.analyze(Workspace(relocated), self.packet()['packet_id'], owned).canonical_bytes, raw)
        with self.assertRaises(GameplayContractError):
            s.analyze(self.workspace, self.packet()['packet_id'], report.to_dict())
        with self.assertRaises((GameplayContractError, TypeError)):
            s.SensitivityReport(raw)
        with self.assertRaises((AttributeError, TypeError)):
            report.canonical_bytes = b'changed'
        self.assertEqual(self.files(), before)
        self.assertEqual({p.relative_to(v.REVIEW_ROOT).as_posix(): p.read_bytes()
                          for p in v.REVIEW_ROOT.rglob('*') if p.is_file()}, retained_before)

    def test_finite_maximum_32_operands_produces_exactly_64_independent_cases(self):
        packet = self.successor(self.packet())
        leaves = []
        for index in range(32):
            claim_id = 'unknown-' + str(index)
            self.add_claim(packet, claim_id, None, condition='UNKNOWN')
            leaves.append(self.leaf(claim_id))
        packet = self.record(packet)
        with patch.object(self.workspace, 'read', wraps=self.workspace.read) as boundary:
            report = self.analyze(packet, self.model(packet, leaves))
            self.assertEqual(boundary.call_count, 1)
        cases = report['sensitivity']['cases']
        self.assertEqual(len(cases), 64)
        self.assertEqual([(case['selected_operand_id'], case['assumed_value']) for case in cases],
                         [(leaf['operand_id'], value) for leaf in leaves for value in (True, False)])
        for case in cases:
            self.assertEqual(len(case['remaining_unresolved_operands']), 31)
            self.assertEqual(len(case['assumptions']), 1)
            self.assertEqual(case['hypothetical_result'], INDET)
        with self.assertRaises(GameplayContractError):
            self.model(packet, leaves + [self.leaf('overflow', ['beacon'])])

    def test_original_pr_212_demonstration_baseline_bytes_and_identities_are_exact(self):
        directory = self.root / 'original-demo'; directory.mkdir()
        process = subprocess.run([sys.executable, 'tools/proposed_spell_conditions_demo.py',
            '--workspace', str(directory)], cwd=ROOT, env=dict(os.environ, PYTHONPATH=str(ROOT / 'src')),
            capture_output=True, text=True)
        self.assertEqual(process.returncode, 0, process.stdout + process.stderr)
        summary = json.loads(process.stdout.splitlines()[-1])
        expected = {
            'missing': ('sha256:23e25cdaf82b0afdf3e69a8f98474fd149128d91b77efde1d19397f922c2369b',
                        'sha256:4809a76b53441a81183cb6d7d7e44681cbba4ef05fc28fe45b9971d91e0cd689',
                        'sha256:9c775f4945a4ed58fcd620d8231e96c6570ccc695dca4d5d1c951a37f915ad11'),
            'true': ('sha256:9aeeb8b24f1c7d88a832acb9c0e85232541ec7cb8286ee2c5c0ac0f47eef4a4b',
                     'sha256:1acaf7616e6ddeada41d2104cbe9ecad1d139f335f72b9d36aa816868223b6ae',
                     'sha256:05932b1f8bebd7ab2b8363815374dd8ff4f3e779c6ac9132196e81199128d99b'),
            'false': ('sha256:a030fba396262eb47d307654219fe64de030be498b2f2c0b8ab2c00f029b4cd2',
                      'sha256:cbd903a0974f5163022e98db8d307249e1e42e6f8cf310ecddfa146b8b8b834f',
                      'sha256:8dc041459c0715995d3cd98bf810a733b2843f8e92bf7552a07edc0e6b65233c')}
        workspace = Workspace(directory)
        for label, identities in expected.items():
            with self.subTest(label=label):
                row = summary['results'][label]
                self.assertEqual(tuple(row[field] for field in ('packet_id', 'model_id', 'result_id')), identities)
                model = c.read_model(directory / 'models' / (label + '.json'))
                ordinary = c.evaluate(workspace, identities[0], model)
                sensitivity = s.analyze(workspace, identities[0], model).to_dict()
                self.assertEqual(ordinary.result_id, identities[2])
                self.assertEqual(v._canonical_candidate(sensitivity['baseline']), ordinary.canonical_bytes)
                self.assertEqual(sensitivity['sensitivity']['case_count'], 2 if label == 'missing' else 0)
        self.assertTrue(summary['all_input_and_history_bytes_unchanged'])


if __name__ == '__main__':
    unittest.main()
