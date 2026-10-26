"""Finite shared requirements, complete candidate scopes and immutable output."""
from copy import deepcopy
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from gameplay_rules.errors import GameplayContractError
from proposed_spell_packets import alternatives as a
from proposed_spell_packets import conditions as c
from proposed_spell_packets import sensitivity as s
from proposed_spell_packets import validation as v
from proposed_spell_packets.authoring import Workspace

ROOT = Path(__file__).resolve().parents[1]
_spec = importlib.util.spec_from_file_location('alternatives_demo', ROOT / 'tools/proposed_spell_alternatives_demo.py')
demo = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(demo)
SAT = 'SATISFIED_UNDER_ASSERTIONS'
NOT = 'NOT_SATISFIED_UNDER_ASSERTIONS'
INDET = 'INDETERMINATE'
WITNESS = 'LISTED_WITNESS_FOUND_UNDER_ASSERTIONS'
NEGATIVE = 'NO_LISTED_WITNESS_UNDER_ASSERTIONS'
UNRESOLVED = 'INDETERMINATE_NO_LISTED_WITNESS_ESTABLISHED'


class AlternativeRequirementsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.seed = tempfile.TemporaryDirectory()
        cls.addClassCleanup(cls.seed.cleanup)
        cls.seed_path = Path(cls.seed.name)
        workspace = Workspace(cls.seed_path)
        cls.original = json.loads((v.PACKAGE_ROOT / 'packet-e-compatibility.json').read_bytes())
        workspace.record(sealed=v.PACKAGE_ROOT / 'packet-e-compatibility.json')
        packet = deepcopy(cls.original)
        packet['revision'] = 2
        packet['history'] = {'supersedes_packet_ids': [packet['packet_id']], 'review_observations': []}
        demo.author_assertions(packet)
        v.seal_packet(packet)
        path = cls.seed_path / 'explicit.json'; path.write_bytes(v._canonical_candidate(packet))
        workspace.record(sealed=path)
        cls.packet = packet
        cls.snapshot = workspace.read(packet['packet_id'])

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.directory = self.root / 'pilot'; shutil.copytree(self.seed_path, self.directory)
        self.workspace = Workspace(self.directory)
        # Structural/semantic combination matrix uses one actually admitted snapshot.
        # Separate tests below exercise the real fresh filesystem admission boundary.
        self.prepared = SimpleNamespace(read=lambda identity: deepcopy(self.snapshot))

    def definition(self, names=('soften', 'brighten'), integrity=False):
        return demo.definition_for(self.packet, names, integrity=integrity)

    @staticmethod
    def reseal(value):
        value = deepcopy(value); value.pop('definition_id', None)
        return a.seal_definition(value)

    def evaluate(self, definition=None, *, workspace=None):
        report = a.evaluate(workspace or self.prepared, self.packet['packet_id'], definition or self.definition())
        value = report.to_dict()
        self.assertEqual(report.canonical_bytes, v._canonical_candidate(value))
        self.assertEqual(report.report_id, v.identity(a.REPORT_VERSION, value, 'report_id'))
        self.assertEqual(value['execution_authority'], 'BLOCKED')
        return value

    def files(self):
        return {p.relative_to(self.directory).as_posix(): p.read_bytes()
                for p in self.directory.rglob('*') if p.is_file()}

    def test_data_driven_aggregate_and_independent_candidate_matrix(self):
        cases = [
            (['soften', 'brighten'], False, NEGATIVE, [NOT, NOT], []),
            (['soften', 'brighten', 'steady'], False, WITNESS, [NOT, NOT, SAT], ['steady']),
            (['missing'], False, UNRESOLVED, [INDET], []),
            (['steady', 'missing'], False, WITNESS, [SAT, INDET], ['steady']),
            (['steady', 'disputed', 'unsupported', 'text-only', 'declared'], True,
             WITNESS, [SAT, INDET, INDET, INDET, INDET], ['steady']),
        ]
        for names, integrity, aggregate, statuses, witnesses in cases:
            with self.subTest(names=names):
                report = self.evaluate(self.definition(names, integrity))
                self.assertEqual(report['computed_result'], aggregate)
                self.assertEqual([row['computed_result'] for row in report['candidates']], statuses)
                self.assertEqual(report['satisfying_alternative_ids'], witnesses)
                self.assertEqual([row['alternative_id'] for row in report['candidates']], names)
        separate = self.evaluate()
        self.assertEqual([[row['status'] for row in candidate['requirement_outcomes']]
                          for candidate in separate['candidates']], [['MATCH', 'MISMATCH'], ['MISMATCH', 'MATCH']])
        missing = self.evaluate(self.definition(['steady', 'missing']))['candidates'][1]
        self.assertEqual(missing['known_mismatches'], [{'requirement_id': 'requirement-b', 'claim_refs': ['missing-b']}])
        findings = self.evaluate(self.definition(['steady', 'disputed', 'unsupported', 'text-only', 'declared'], True))
        kinds = {row['alternative_id']: {finding['kind'] for finding in row['selected_input_findings']}
                 for row in findings['candidates']}
        self.assertEqual(kinds['disputed'], {'OPPOSING_BOOLEAN_ASSERTIONS'})
        self.assertEqual(kinds['unsupported'], {'UNSUPPORTED_ASSERTION'})
        self.assertEqual(kinds['text-only'], {'UNSUPPORTED_BOOLEAN_INPUT'})
        self.assertEqual(kinds['declared'], {'DECLARED_CONFLICT', 'OPPOSING_BOOLEAN_ASSERTIONS'})
        self.assertIn('disputed-integrity', json.dumps(findings['candidates'][1]['known_mismatches']))
        rendered = a.render(a.evaluate(self.prepared, self.packet['packet_id'], self.definition(['steady', 'missing'])))
        for term in ('steady', 'missing', 'MISSING_ASSERTION', 'Authored packet conclusion (separate)', 'BLOCKED'):
            self.assertIn(term, rendered)

    def test_expected_false_compares_explicit_false_and_retains_unknown(self):
        definition = self.definition(['soften', 'missing'])
        definition['requirements'][1]['expected'] = False
        report = self.evaluate(self.reseal(definition))
        self.assertEqual([row['computed_result'] for row in report['candidates']], [SAT, INDET])
        definition['requirements'][0]['expected'] = False
        report = self.evaluate(self.reseal(definition))
        self.assertEqual([row['computed_result'] for row in report['candidates']], [NOT, INDET])
        self.assertIn('MISSING_ASSERTION', json.dumps(report['candidates'][1]['selected_input_findings']))

    def test_closed_definition_scalar_duplicates_versions_and_limits(self):
        original = self.definition()
        mutations = []
        def add(fn):
            value = deepcopy(original); value.pop('definition_id'); fn(value); mutations.append(value)
        add(lambda d: d.update(extra='untrusted'))
        add(lambda d: d.update(definition_version='future-v2'))
        add(lambda d: d.update(authority='ACTUAL_CASTING_PERMISSION'))
        add(lambda d: d.update(requirements=[]))
        add(lambda d: d.update(candidates=[]))
        add(lambda d: d['requirements'].append(deepcopy(d['requirements'][0])))
        add(lambda d: d['candidates'].append(deepcopy(d['candidates'][0])))
        add(lambda d: d['requirements'][1].update(subject_id=d['requirements'][0]['subject_id'], predicate=d['requirements'][0]['predicate']))
        add(lambda d: d['candidates'][0]['bindings'][0].update(claim_refs=[]))
        add(lambda d: d['candidates'][0]['bindings'][0].update(claim_refs=['soften-a'] * 2))
        add(lambda d: d['candidates'][0]['bindings'][1].update(requirement_id='requirement-a'))
        add(lambda d: d['candidates'][0]['bindings'].pop())
        add(lambda d: d['candidates'][0].update(expected=False))
        add(lambda d: d['requirements'][0].update(extra=False))
        add(lambda d: d['packet'].update(extra=False))
        add(lambda d: d['candidates'][0]['bindings'][0].update(extra=False))
        add(lambda d: d['scope'].update(alternative_id='soften'))
        for value in (0, 1, 0.0, 1.0, 'true', None, [], {}):
            add(lambda d, value=value: d['requirements'][0].update(expected=value))
        for value in (True, '1', 1.0, None):
            add(lambda d, value=value: d['scope'].update(context_version=value))
            add(lambda d, value=value: d['packet'].update(revision=value))
        add(lambda d: d['requirements'][0].update(predicate='x' * 4097))
        add(lambda d: d['candidates'][0]['bindings'][0].update(claim_refs=['ref-' + str(i) for i in range(65)]))
        add(lambda d: d['scope'].update(context_id=('ctx',)))
        for index, value in enumerate(mutations):
            with self.subTest(index=index), self.assertRaises(GameplayContractError):
                a.seal_definition(value)
        for value in ({1: 'integer key'}, {'custom': object()}, {'many': [None] * 65_537},
                      {'bytes': ['x' * 4096] * 251}, {'nested': [[[[[[[[[None]]]]]]]]]}):
            with self.subTest(ownership_guard=type(value)), self.assertRaises(GameplayContractError):
                a.AlternativesDefinition(value)
        path = self.root / 'malformed-definition.json'
        for raw in (b'{"definition_id":"first","definition_id":"second"}', b'{', b'{"x":NaN}'):
            path.write_bytes(raw)
            with self.subTest(raw=raw), self.assertRaises(GameplayContractError):
                a.read_definition(path)
        stale = deepcopy(original); stale['requirements'][0]['expected'] = False
        with self.assertRaises(GameplayContractError):
            a.AlternativesDefinition(stale)
        for value in (c.seal_model({'model_version': c.MODEL_VERSION, 'authority': c.MODEL_AUTHORITY,
                'condition_id': 'foreign', 'condition_name': 'Foreign precomputed model', 'packet': original['packet'],
                'scope': {**original['scope'], 'alternative_id': 'soften'}, 'operator': 'ALL_OF',
                'operands': [{'operand_id': 'requirement-a', 'claim_refs': ['soften-a'], 'expected': True}]}),
                self.evaluate(), {'computed_result': SAT}):
            with self.assertRaises(GameplayContractError):
                a.evaluate(self.prepared, self.packet['packet_id'], value)

    def test_same_ids_cannot_hide_altered_keys_mixed_scopes_or_omitted_dissent(self):
        original = self.definition(['steady', 'disputed'], True)
        mutations = []
        def add(fn):
            value = deepcopy(original); fn(value); mutations.append(self.reseal(value))
        add(lambda d: d['requirements'][0].update(predicate='Opaque requirement A'))
        add(lambda d: d['requirements'][0].update(subject_id='fictional:e:other'))
        add(lambda d: d['candidates'][1]['bindings'][0].update(claim_refs=['general-integrity']))
        add(lambda d: d['candidates'][1]['bindings'][0].update(claim_refs=['steady-integrity', 'general-integrity']))
        add(lambda d: d['candidates'][1]['bindings'][0].update(claim_refs=['general-integrity', 'disputed-integrity', 'steady-integrity']))
        add(lambda d: d['candidates'][1]['bindings'][1].update(claim_refs=['steady-b']))
        add(lambda d: d['candidates'][0].update(alternative_id='undeclared'))
        add(lambda d: d['scope'].update(context_id='foreign'))
        add(lambda d: d['scope'].update(context_version=2))
        add(lambda d: d['packet'].update(revision=3))
        add(lambda d: d['packet'].update(packet_id='sha256:' + '0' * 64))
        add(lambda d: d['packet'].update(contract_id='sha256:' + '0' * 64))
        add(lambda d: d['packet'].update(lineage_id='fictional:e:other'))
        add(lambda d: d['candidates'][0]['bindings'][0].update(claim_refs=['dangling']))
        for index, definition in enumerate(mutations):
            with self.subTest(index=index), self.assertRaises(GameplayContractError):
                self.evaluate(definition)
        # The same ID and an expectation changed after sealing cannot carry its old identity.
        stale = deepcopy(original); stale['requirements'][0]['expected'] = False
        with self.assertRaises(GameplayContractError):
            self.evaluate(stale)
        # Valid changed expectations produce a different explicit definition and actual mismatch.
        changed = deepcopy(original); changed['requirements'][0]['expected'] = False
        changed = self.reseal(changed)
        self.assertNotEqual(changed['definition_id'], original['definition_id'])
        self.assertNotEqual(self.evaluate(changed)['candidates'][0]['computed_result'], SAT)

    def test_missing_group_is_binding_error_and_actual_root_is_still_valid(self):
        definition = self.definition(['soften'])
        definition['packet'] = {key: self.original[key] for key in c.PACKET_FIELDS}
        definition = self.reseal(definition)
        prepared_root = SimpleNamespace(read=lambda identity: (deepcopy(self.original), {}))
        with self.assertRaisesRegex(GameplayContractError, 'INSUFFICIENT_BINDING_MISSING_REQUIRED_GROUP'):
            a.evaluate(prepared_root, self.original['packet_id'], definition)
        actual, _ = self.workspace.read(self.original['packet_id'])
        self.assertEqual(actual, self.original)
        self.assertEqual(len(actual['claims']), 5)

    def test_actual_cli_canonical_stdout_and_standalone_v1_parity(self):
        definition = self.definition(['soften', 'brighten', 'steady', 'missing'])
        path = self.root / 'requirements.json'; path.write_text(json.dumps(definition))
        command = [sys.executable, '-m', 'proposed_spell_packets', '--workspace', str(self.directory),
                   'evaluate-alternatives', self.packet['packet_id'], '--requirements', str(path)]
        before = self.files()
        outputs = []
        for suffix in ([], ['--json']):
            process = subprocess.run(command + suffix, cwd=ROOT,
                env=dict(os.environ, PYTHONPATH=str(ROOT / 'src')), capture_output=True)
            self.assertEqual(process.returncode, 0, process.stdout + process.stderr)
            outputs.append(process.stdout)
        value = json.loads(outputs[1])
        self.assertEqual(outputs[1], v._canonical_candidate(value))
        self.assertIn(b'BLOCKED', outputs[0])
        # Compare whole actual v1 canonical result, never just status or copied IDs.
        for candidate in value['candidates']:
            result = c.evaluate(self.prepared, self.packet['packet_id'], candidate['condition_model'])
            self.assertEqual(v._canonical_candidate(candidate['condition_result']), result.canonical_bytes)
            self.assertEqual(candidate['result_id'], result.result_id)
            self.assertEqual(candidate['model_id'], candidate['condition_model']['model_id'])
        self.assertEqual(self.files(), before)

    def test_private_ownership_single_fresh_admission_determinism_and_read_only(self):
        definition = self.definition(['steady', 'missing'])
        path = self.root / 'requirements.json'; path.write_bytes(v._canonical_candidate(definition))
        owned = a.read_definition(path)
        before = self.files()
        captured = []
        actual_read = self.workspace.read
        def read(identity):
            result = actual_read(identity); captured.append(result); return result
        with patch.object(self.workspace, 'read', side_effect=read) as boundary:
            report = a.evaluate(self.workspace, self.packet['packet_id'], owned)
            boundary.assert_called_once_with(self.packet['packet_id'])
        raw = report.canonical_bytes
        definition['requirements'][0]['expected'] = False
        captured[0][0]['claims'][0]['value'] = 'caller edit'
        captured[0][1].clear()
        path.write_text('{}')
        decoded = report.to_dict(); decoded['candidates'].clear(); decoded['definition'].clear()
        decoded_input = owned.to_dict(); decoded_input['requirements'].clear()
        self.assertEqual(report.canonical_bytes, raw)
        self.assertEqual(a.evaluate(self.prepared, self.packet['packet_id'], owned).canonical_bytes, raw)
        relocated = self.root / 'relocated'; shutil.copytree(self.directory, relocated)
        self.assertEqual(a.evaluate(Workspace(relocated), self.packet['packet_id'], owned).canonical_bytes, raw)
        self.assertNotIn('caller edit', json.dumps(report.to_dict()))
        with self.assertRaises((AttributeError, TypeError)):
            report.canonical_bytes = b'changed'
        with self.assertRaises(GameplayContractError):
            a.AlternativesReport(raw)
        self.assertEqual(self.files(), before)

    def test_actual_edited_root_history_and_retained_contract_are_rejected(self):
        root_path = self.directory / 'packets' / (self.original['packet_id'][7:] + '.json')
        raw = root_path.read_bytes()
        root_path.write_bytes(raw + b' ')
        with self.assertRaises(GameplayContractError):
            self.evaluate(workspace=self.workspace)
        root_path.write_bytes(raw)
        edited = deepcopy(self.original); edited['conclusion']['text'] += ' Unparented edit.'
        v.seal_packet(edited)
        path = self.directory / 'packets' / (edited['packet_id'][7:] + '.json')
        path.write_bytes(v._canonical_candidate(edited))
        definition = self.definition(); definition['packet'] = {key: edited[key] for key in c.PACKET_FIELDS}
        with self.assertRaises(GameplayContractError):
            a.evaluate(self.workspace, edited['packet_id'], self.reseal(definition))
        path.unlink()
        retained = self.root / 'retained'; shutil.copytree(v.PACKAGE_ROOT, retained)
        loader = v.load_package
        with patch.object(v, 'load_package', side_effect=lambda: loader(retained)):
            contract = retained / 'contract.json'; contract.write_bytes(contract.read_bytes() + b' ')
            with self.assertRaises(GameplayContractError):
                self.evaluate(workspace=self.workspace)
        self.assertEqual(root_path.read_bytes(), raw)

    def test_maximum_structural_bounds_and_focused_actual_computation(self):
        # Exercise all 16x32x64 input cardinalities in pure structural validation.
        definition = self.definition(['steady'])
        definition.pop('definition_id')
        definition['requirements'] = [{'requirement_id': 'r-' + str(i),
            'subject_id': 'fictional:e:object', 'predicate': 'Opaque bound ' + str(i), 'expected': True}
            for i in range(32)]
        definition['candidates'] = [{'alternative_id': 'candidate-' + str(j), 'bindings': [
            {'requirement_id': 'r-' + str(i), 'claim_refs': ['r-' + str(i) + '-c-' + str(k) for k in range(64)]}
            for i in range(32)]} for j in range(16)]
        sealed = a.seal_definition(definition)
        self.assertEqual(len(sealed['candidates']), 16)
        self.assertEqual(len(sealed['requirements']), 32)
        self.assertEqual(len(sealed['candidates'][15]['bindings'][31]['claim_refs']), 64)
        for field in ('candidates', 'requirements'):
            overflow = deepcopy(definition); overflow[field].append(deepcopy(overflow[field][-1]))
            with self.subTest(field=field), self.assertRaises(GameplayContractError):
                a.seal_definition(overflow)
        # Real packet bound: 32 groups, with one complete 64-claim general group,
        # shared across 16 named candidates; all assertions pass actual admission.
        packet = deepcopy(self.packet)
        packet['revision'] += 1
        packet['history'] = {'supersedes_packet_ids': [self.packet['packet_id']], 'review_observations': []}
        packet['choices'] += [{'alternative_id': 'candidate-' + str(j), 'choice_id': 'bound-choice-' + str(j),
            'claim_refs': ['r-0-c-0'], 'context_id': 'ctx', 'description': 'Explicit bounded fictional candidate.'}
            for j in range(16)]
        template = deepcopy(packet['claims'][0])
        for i in range(32):
            for k in range(64 if i == 0 else 1):
                row = deepcopy(template)
                row.update(claim_id='r-' + str(i) + '-c-' + str(k), alternative_id=None, role='STATE',
                    predicate='Opaque bound ' + str(i), value=True, condition='PRESENT',
                    limitation_refs=[], rule_context_refs=[],
                    attribution={'actor_id': 'fictional:e:bound-author', 'statement_id': 'bound-' + str(i) + '-' + str(k)})
                packet['claims'].append(row)
        v.seal_packet(packet)
        path = self.root / 'bound.json'; path.write_bytes(v._canonical_candidate(packet))
        self.workspace.record(sealed=path)
        definition['packet'] = {key: packet[key] for key in c.PACKET_FIELDS}
        for candidate in definition['candidates']:
            for i, binding in enumerate(candidate['bindings']):
                binding['claim_refs'] = ['r-' + str(i) + '-c-' + str(k) for k in range(64 if i == 0 else 1)]
        with patch.object(self.workspace, 'read', wraps=self.workspace.read) as boundary:
            report = a.evaluate(self.workspace, packet['packet_id'], a.seal_definition(definition)).to_dict()
            boundary.assert_called_once_with(packet['packet_id'])
        self.assertEqual(report['computed_result'], WITNESS)
        self.assertEqual(report['satisfying_alternative_ids'], ['candidate-' + str(i) for i in range(16)])
        self.assertEqual(len(report['candidates'][15]['requirement_outcomes']), 32)
        self.assertEqual(len(report['candidates'][15]['requirement_outcomes'][0]['claim_refs']), 64)

    def test_original_ordinary_and_pr_213_sensitivity_identities_unchanged(self):
        packet = json.loads((v.PACKAGE_ROOT / 'packet-b-missing.json').read_bytes())
        model = c.seal_model({'model_version': c.MODEL_VERSION, 'authority': c.MODEL_AUTHORITY,
            'condition_id': 'premise-and-lit-beacon', 'condition_name': 'Fictional premise and lit beacon',
            'packet': {key: packet[key] for key in c.PACKET_FIELDS},
            'scope': {'context_id': 'ctx', 'context_version': 1, 'alternative_id': None},
            'operator': 'ALL_OF', 'operands': [
                {'operand_id': 'explicit-premise', 'claim_refs': ['premise'], 'expected': True},
                {'operand_id': 'lit-beacon', 'claim_refs': ['beacon'], 'expected': True}]})
        # Test the exact original baseline and sensitivity against their original IDs.
        prepared = SimpleNamespace(read=lambda identity: (deepcopy(packet), {}))
        ordinary = c.evaluate(prepared, packet['packet_id'], model)
        sensitivity = s.analyze(prepared, packet['packet_id'], model)
        self.assertEqual(model['model_id'], 'sha256:4809a76b53441a81183cb6d7d7e44681cbba4ef05fc28fe45b9971d91e0cd689')
        self.assertEqual(ordinary.result_id, 'sha256:9c775f4945a4ed58fcd620d8231e96c6570ccc695dca4d5d1c951a37f915ad11')
        self.assertEqual(sensitivity.report_id, 'sha256:5c0810f82cb9724078d399e969c1b6c8d37dd9b01d16b3b311ddb61607331d9f')
        self.assertEqual(v._canonical_candidate(sensitivity.to_dict()['baseline']), ordinary.canonical_bytes)


if __name__ == '__main__':
    unittest.main()
