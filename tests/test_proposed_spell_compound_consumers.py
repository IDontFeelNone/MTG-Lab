"""Compound consumers retain complete evidence, private ownership and one admission."""
from copy import deepcopy
import importlib.util
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from gameplay_rules.errors import GameplayContractError
from proposed_spell_packets import alternatives as a1
from proposed_spell_packets import alternatives_v2 as a
from proposed_spell_packets import conditions_v2 as c
from proposed_spell_packets import sensitivity_v2 as s
from proposed_spell_packets import validation as v
from proposed_spell_packets.authoring import Workspace

ROOT = Path(__file__).resolve().parents[1]
_spec = importlib.util.spec_from_file_location('compound_consumer_seed', ROOT / 'tools/proposed_spell_alternatives_demo.py')
seed = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(seed)


def leaf(name):
    return {'leaf_id': name}


def node(op, *children):
    return {'operator': op, 'children': list(children)}


class CompoundConsumerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory()
        cls.addClassCleanup(cls.temp.cleanup)
        cls.path = Path(cls.temp.name)
        cls.workspace = Workspace(cls.path)
        cls.b = json.loads((v.PACKAGE_ROOT / 'packet-b-missing.json').read_bytes())
        cls.workspace.record(sealed=v.PACKAGE_ROOT / 'packet-b-missing.json')
        root = json.loads((v.PACKAGE_ROOT / 'packet-e-compatibility.json').read_bytes())
        cls.workspace.record(sealed=v.PACKAGE_ROOT / 'packet-e-compatibility.json')
        packet = deepcopy(root)
        packet['revision'] = 2
        packet['history'] = {'supersedes_packet_ids': [root['packet_id']], 'review_observations': []}
        seed.author_assertions(packet)
        row = deepcopy(packet['claims'][0])
        row.update(claim_id='route-c', alternative_id=None, role='STATE',
            predicate='Explicit route C', condition='PRESENT', value=False,
            rule_context_refs=[], limitation_refs=[],
            attribution={'actor_id': 'fictional:e:compound-consumer-author', 'statement_id': 'route-c'})
        packet['claims'].append(row)
        v.seal_packet(packet)
        source = cls.path / 'explicit.json'; source.write_bytes(v._canonical_candidate(packet))
        cls.workspace.record(sealed=source)
        cls.packet = packet
        cls.snapshot = cls.workspace.read(packet['packet_id'])
        cls.b_snapshot = cls.workspace.read(cls.b['packet_id'])

    def prepared(self, b=False):
        return SimpleNamespace(read=lambda identity: deepcopy(self.b_snapshot if b else self.snapshot))

    def definition(self, names=('soften', 'brighten', 'steady'), integrity=False):
        value = seed.definition_for(self.packet, names, integrity=integrity)
        value.pop('definition_id')
        value['definition_version'] = a.DEFINITION_VERSION
        value['requirements'].append({'requirement_id': 'route-c', 'subject_id': 'fictional:e:object',
                                     'predicate': 'Explicit route C', 'expected': True})
        value['expression'] = node('ALL_OF', leaf('requirement-a'),
                                   node('ANY_OF', leaf('requirement-b'), leaf('route-c')))
        for candidate in value['candidates']:
            candidate['bindings'].append({'requirement_id': 'route-c', 'claim_refs': ['route-c']})
        return a.seal_definition(value)

    def b_model(self):
        return c.seal_model({'model_version': c.MODEL_VERSION, 'authority': c.MODEL_AUTHORITY,
            'condition_id': 'repeated-beacon', 'condition_name': 'Repeated unknown with fixed premise',
            'packet': c._binding(self.b), 'scope': {'context_id': 'ctx', 'context_version': 1, 'alternative_id': None},
            'leaves': [{'leaf_id': 'gate', 'claim_refs': ['premise'], 'expected': True},
                       {'leaf_id': 'route', 'claim_refs': ['beacon'], 'expected': True}],
            'expression': node('ALL_OF', leaf('gate'), node('ANY_OF', leaf('route'), leaf('route')))})

    def test_alternatives_complete_models_standalone_parity_and_no_shared_witness(self):
        for names, witnesses in [(('soften', 'brighten'), []), (('soften', 'brighten', 'steady'), ['steady'])]:
            with self.subTest(names=names):
                report = a.evaluate(self.prepared(), self.packet['packet_id'], self.definition(names))
                value = report.to_dict()
                self.assertEqual(value['satisfying_alternative_ids'], witnesses)
                self.assertEqual(value['computed_result'], 'LISTED_WITNESS_FOUND_UNDER_ASSERTIONS' if witnesses else 'NO_LISTED_WITNESS_UNDER_ASSERTIONS')
                self.assertEqual(report.report_id, v.identity(a.REPORT_VERSION, value, 'report_id'))
                for candidate in value['candidates']:
                    model = c.ConditionModel(candidate['condition_model'])
                    standalone = c.evaluate(self.prepared(), self.packet['packet_id'], model)
                    self.assertEqual(standalone.canonical_bytes, v._canonical_candidate(candidate['condition_result']))
                    self.assertEqual(standalone.result_id, candidate['result_id'])
                    sensitivity = s.analyze(self.prepared(), self.packet['packet_id'], model).to_dict()
                    self.assertEqual(v._canonical_candidate(sensitivity['baseline']), standalone.canonical_bytes)

    def test_sensitivity_baseline_correlated_occurrences_and_once_read(self):
        prepared = self.prepared(b=True)
        with patch.object(prepared, 'read', wraps=prepared.read) as reader:
            report = s.analyze(prepared, self.b['packet_id'], self.b_model())
            self.assertEqual(reader.call_count, 1)
        value = report.to_dict()
        baseline = c.evaluate(self.prepared(b=True), self.b['packet_id'], self.b_model())
        self.assertEqual(v._canonical_candidate(value['baseline']), baseline.canonical_bytes)
        self.assertEqual(value['sensitivity']['case_count'], 2)
        for case, expected in zip(value['sensitivity']['cases'], ('SATISFIED_UNDER_HYPOTHESIS', 'NOT_SATISFIED_UNDER_HYPOTHESIS')):
            self.assertEqual(case['hypothetical_result'], expected)
            self.assertEqual(case['selected_leaf_id'], 'route')
            refs = [row for row in case['expression_nodes'] if row.get('leaf_id') == 'route']
            self.assertEqual(len(refs), 2)
            self.assertEqual(len({row['status'] for row in refs}), 1)
            self.assertEqual(case['assumptions'], [{'claim_id': 'beacon', 'value': case['assumed_value']}])
            self.assertTrue(case['root_change']['changed'])
            self.assertEqual(len(case['expression_node_changes']), len(case['expression_nodes']))
        self.assertEqual(value['authority'], s.AUTHORITY)
        self.assertEqual(value['baseline']['computed_result'], 'INDETERMINATE')

    def test_unknown_hypotheses_preserve_unsupported_conflicting_and_non_boolean_inputs(self):
        for name, kind in [('unsupported', 'UNSUPPORTED_ASSERTION'), ('text-only', 'UNSUPPORTED_BOOLEAN_INPUT'), ('declared', 'DECLARED_CONFLICT')]:
            with self.subTest(name=name):
                # A third selected leaf uses the general fixed route-c fact. The
                # actual unknown claim is explicitly bound from the same general scope.
                packet = deepcopy(self.packet)
                unknown = deepcopy(next(row for row in packet['claims'] if row['claim_id'] == 'missing-a'))
                unknown.update(claim_id='extra-unknown', alternative_id=None, predicate='Explicit additional unknown')
                packet['claims'].append(unknown)
                v.seal_packet(packet)
                definition = self.definition([name], integrity=True)
                definition.pop('definition_id')
                definition['packet'] = c._binding(packet)
                definition['requirements'][2]['predicate'] = 'Explicit additional unknown'
                definition['candidates'][0]['bindings'][2]['claim_refs'] = ['extra-unknown']
                definition = a.seal_definition(definition)
                prepared = SimpleNamespace(read=lambda identity: (deepcopy(packet), {}))
                candidate = a.evaluate(prepared, packet['packet_id'], definition).to_dict()['candidates'][0]
                sensitivity = s.analyze(prepared, packet['packet_id'], candidate['condition_model']).to_dict()
                self.assertEqual(sensitivity['sensitivity']['case_count'], 2)
                before = candidate['condition_result']['leaves'][0]
                for case in sensitivity['sensitivity']['cases']:
                    affected_integrity = case['leaves'][0]
                    self.assertEqual(affected_integrity['status'], 'UNRESOLVED')
                    self.assertIn(kind, {row['kind'] for row in affected_integrity['findings']})
                    self.assertEqual(affected_integrity['findings'], before['findings'])
                    evaluations = affected_integrity['assertion_evaluations']
                    self.assertFalse(any(row['hypothesized'] for row in evaluations))

    def test_alternatives_once_read_private_ownership_and_read_only(self):
        before = {p.relative_to(self.path).as_posix(): p.read_bytes() for p in self.path.rglob('*') if p.is_file()}
        source = self.definition()
        owned = a.AlternativesDefinition(source)
        source['requirements'][0]['expected'] = False
        with patch.object(self.workspace, 'read', wraps=self.workspace.read) as reader:
            report = a.evaluate(self.workspace, self.packet['packet_id'], owned)
            self.assertEqual(reader.call_count, 1)
        raw = report.canonical_bytes
        view = report.to_dict(); view['candidates'][0]['condition_model']['leaves'].clear()
        self.assertEqual(report.canonical_bytes, raw)
        self.assertEqual(report.to_dict()['definition'], owned.to_dict())
        self.assertTrue(owned.to_dict()['requirements'][0]['expected'])
        self.assertEqual(before, {p.relative_to(self.path).as_posix(): p.read_bytes() for p in self.path.rglob('*') if p.is_file()})
        for constructor in (a.AlternativesReport, s.SensitivityReport):
            with self.assertRaises(GameplayContractError):
                constructor(raw)
        with self.assertRaises(AttributeError):
            report.canonical_bytes = b'changed'

    def test_closed_definition_types_versions_expression_and_complete_bindings(self):
        original = self.definition()
        mutations = [lambda d: d.update(definition_version=a1.DEFINITION_VERSION),
                     lambda d: d.update(definition_version='unknown-v3'),
                     lambda d: d.update(extra=True),
                     lambda d: d['scope'].update(alternative_id='soften'),
                     lambda d: d['expression']['children'].append({'leaf_id': 'missing'}),
                     lambda d: d['requirements'][0].update(expected=1),
                     lambda d: d['requirements'][0].update(expected=1.0),
                     lambda d: d['requirements'][0].update(extra=None),
                     lambda d: d['candidates'][0]['bindings'][0].update(extra=True),
                     lambda d: d['candidates'][0]['bindings'][0].update(claim_refs=[]),
                     lambda d: d['candidates'][0]['bindings'].pop(),
                     lambda d: d['candidates'].extend([d['candidates'][0]] * 16)]
        for mutate in mutations:
            with self.subTest(mutate=mutate):
                value = deepcopy(original); value.pop('definition_id'); mutate(value)
                with self.assertRaises(GameplayContractError):
                    a.seal_definition(value)
        with self.assertRaises(GameplayContractError):
            a.AlternativesDefinition({**original, 'definition_id': 'sha256:' + '0' * 64})
        with self.assertRaises(GameplayContractError):
            a1.AlternativesDefinition(original)
        with self.assertRaises(GameplayContractError):
            a.AlternativesDefinition(seed.definition_for(self.packet, ['steady']))
        # Another candidate is fully satisfied, but a foreign fact binding in
        # the second candidate remains a request-wide error.
        value = self.definition(['steady', 'soften']); value.pop('definition_id')
        value['candidates'][1]['bindings'][0]['claim_refs'] = ['soften-b']
        with self.assertRaises(GameplayContractError):
            a.evaluate(self.prepared(), self.packet['packet_id'], a.seal_definition(value))

    def test_duplicate_json_nonfinite_byte_structure_and_cumulative_model_limits(self):
        original = self.definition()
        for raw in (b'{"definition_version":"x","definition_version":"y"}', b'{"value":NaN}', b'{"value":Infinity}'):
            path = self.path / 'rejected-definition.json'; path.write_bytes(raw)
            with self.assertRaises(GameplayContractError):
                a.read_definition(path)
        for value in ([None] * 65537, 'X' * 4097, [tuple()], {1: 'key'}, [True] * 65536):
            with self.assertRaises(GameplayContractError):
                a._owned(value)
        deep = None
        for _ in range(21):
            deep = [deep]
        with self.assertRaises(GameplayContractError):
            a._owned(deep)
        # Common requirements can be structurally small while one composed model
        # exhausts its independent 64,000-byte bound. No global-only bypass.
        value = deepcopy(original); value.pop('definition_id')
        value['candidates'] = [value['candidates'][0]]
        value['requirements'] = []
        value['candidates'][0]['bindings'] = []
        for index in range(32):
            rid = 'r-' + str(index)
            value['requirements'].append({'requirement_id': rid, 'subject_id': 'fictional:e:object',
                                          'predicate': rid, 'expected': True})
            value['candidates'][0]['bindings'].append({'requirement_id': rid,
                'claim_refs': ['claim-' + str(index) + '-' + str(j) + '-' + 'x' * 40 for j in range(64)]})
        value['expression'] = node('ALL_OF', *(leaf(row['requirement_id']) for row in value['requirements']))
        self.assertLess(len(v._canonical_candidate(value)), a.DEFINITION_BYTE_LIMIT)
        with self.assertRaises(GameplayContractError):
            a.seal_definition(value)

    def test_finite_policy_identities_ownership_and_embedded_authority(self):
        for module in (a, s):
            with self.subTest(module=module.__name__):
                content = module.policy()
                self.assertEqual(content['policy_version'], module.POLICY_VERSION)
                self.assertEqual(content['authority'], module.POLICY_AUTHORITY)
                self.assertEqual(content['policy_id'], module.POLICY_ID)
                self.assertEqual(module.POLICY_ID, v.identity(module.POLICY_VERSION, content, 'policy_id'))
                content['authority'] = 'UNTRUSTED_IMPORTED_POLICY'
                self.assertEqual(module.policy()['authority'], module.POLICY_AUTHORITY)
        sensitivity = s.analyze(self.prepared(b=True), self.b['packet_id'], self.b_model()).to_dict()
        self.assertEqual(sensitivity['sensitivity_policy'], s.policy())
        self.assertEqual(sensitivity['sensitivity_policy_id'], s.POLICY_ID)
        self.assertEqual(sensitivity['evaluator_policy_id'], c.POLICY_ID)
        alternatives = a.evaluate(self.prepared(), self.packet['packet_id'], self.definition()).to_dict()
        self.assertEqual(alternatives['comparison_policy'], a.policy())
        self.assertEqual(alternatives['comparison_policy_id'], a.POLICY_ID)
        self.assertEqual(alternatives['evaluator_policy_id'], c.POLICY_ID)

    def test_maximum_64_cases_and_leaf_order_without_cross_group_carryover(self):
        # This pure-calculation fixture starts from the original admitted B
        # snapshot, supplies explicit UNKNOWN claims, and preserves all values.
        packet = deepcopy(self.b)
        template = deepcopy(next(row for row in packet['claims'] if row['claim_id'] == 'beacon'))
        packet['claims'] = []
        leaves = []
        for index in range(32):
            row = deepcopy(template); row.update(claim_id='u-' + str(index), predicate='Opaque unknown ' + str(index))
            packet['claims'].append(row)
            leaves.append({'leaf_id': 'l-' + str(index), 'claim_refs': [row['claim_id']], 'expected': True})
        v.seal_packet(packet)
        model = c.seal_model({'model_version': c.MODEL_VERSION, 'authority': c.MODEL_AUTHORITY,
            'condition_id': 'bounded-cases', 'condition_name': 'Explicit 32 independent unknown groups',
            'packet': c._binding(packet), 'scope': {'context_id': 'ctx', 'context_version': 1, 'alternative_id': None},
            'leaves': leaves, 'expression': node('ALL_OF', *(leaf(row['leaf_id']) for row in leaves))})
        prepared = SimpleNamespace(read=lambda identity: (deepcopy(packet), {}))
        value = s.analyze(prepared, packet['packet_id'], model).to_dict()
        self.assertEqual(value['sensitivity']['case_count'], 64)
        for index, case in enumerate(value['sensitivity']['cases']):
            self.assertEqual(case['selected_leaf_id'], 'l-' + str(index // 2))
            self.assertEqual(case['assumed_value'], index % 2 == 0)
            self.assertEqual(len(case['remaining_unresolved_leaves']), 31)
            self.assertEqual(len(case['assumptions']), 1)
            self.assertEqual(sum(e['hypothesized'] for row in case['leaves'] for e in row['assertion_evaluations']), 1)


if __name__ == '__main__':
    unittest.main()
