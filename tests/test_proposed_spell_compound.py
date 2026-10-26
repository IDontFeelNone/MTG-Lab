"""Compound contract, policy and actual offline workflow regressions."""
from copy import deepcopy
from dataclasses import FrozenInstanceError
import importlib.util
import itertools
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
from types import SimpleNamespace
import unittest

from gameplay_rules.errors import GameplayContractError
from proposed_spell_packets import alternatives as a1
from proposed_spell_packets import alternatives_v2 as a
from proposed_spell_packets import conditions as c1
from proposed_spell_packets import sensitivity as s1
from proposed_spell_packets import conditions_v2 as c
from proposed_spell_packets import sensitivity_v2 as s
from proposed_spell_packets import validation as v
from proposed_spell_packets.authoring import Workspace

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location('compound_demo', ROOT / 'tools/proposed_spell_compound_demo.py')
DEMO = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(DEMO)


class CompoundConditionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.seed = tempfile.TemporaryDirectory()
        cls.addClassCleanup(cls.seed.cleanup)
        cls.directory = Path(cls.seed.name)
        process = subprocess.run([sys.executable, 'tools/proposed_spell_compound_demo.py',
            '--workspace', str(cls.directory)], cwd=ROOT,
            env=dict(os.environ, PYTHONPATH=str(ROOT / 'src')), capture_output=True, text=True)
        if process.returncode:
            raise AssertionError(process.stdout + process.stderr)
        cls.summary = json.loads(process.stdout.splitlines()[-1])
        cls.packet, cls.history = Workspace(cls.directory).read(cls.summary['packet_id'])

    def prepared(self):
        # Policy tests use an actual admitted, privately copied fixture snapshot;
        # the complete authoring/admission/CLI boundary is exercised by the demo.
        return SimpleNamespace(read=lambda identity: (deepcopy(self.packet), deepcopy(self.history)))

    def seal(self, value):
        return c.seal_model({key: child for key, child in value.items() if key != 'model_id'})

    def model(self, leaves, expression):
        value = DEMO.model_for(self.packet, 'satisfied')
        value.update(leaves=leaves, expression=expression)
        value['scope']['alternative_id'] = None
        return self.seal(value)

    def evaluate(self, model):
        result = c.evaluate(self.prepared(), self.packet['packet_id'], model)
        value = result.to_dict()
        self.assertEqual(v._canonical_candidate(value), result.canonical_bytes)
        self.assertEqual(value['result_id'], v.identity(c.RESULT_VERSION, value, 'result_id'))
        self.assertEqual(value['evaluator_policy'], c.policy())
        self.assertEqual(value['evaluator_policy_id'], c.POLICY_ID)
        self.assertEqual(c.POLICY_ID, v.identity(c.POLICY_VERSION, c.policy(), 'policy_id'))
        policy_view = c.policy(); policy_view['authority'] = 'changed'
        self.assertNotEqual(policy_view, c.policy())
        return value

    def test_actual_authoring_cli_scenarios_parity_and_preservation(self):
        for scenario, expected in DEMO.EXPECTED.items():
            with self.subTest(scenario=scenario):
                result = self.summary['results'][scenario]
                self.assertEqual(result['computed_result'], expected)
                if 'unknown' in scenario or 'unresolved' in scenario:
                    self.assertIn('UNRESOLVED', result['leaf_statuses'])
                    self.assertTrue(result['selected_input_findings'])
        for scenario, kind in (('unsupported-alongside-match', 'UNSUPPORTED_ASSERTION'),
                               ('conflict-alongside-match', 'DECLARED_CONFLICT')):
            self.assertIn(kind, {row['kind'] for row in self.summary['results'][scenario]['selected_input_findings']})
        self.assertTrue(self.summary['all_evaluation_invocations_read_only'])
        self.assertTrue(self.summary['retained_root_bytes_and_reachable_history_preserved'])
        self.assertTrue(self.summary['hidden_invalid_branches_rejected'])
        self.assertEqual(self.packet['history']['supersedes_packet_ids'], [self.summary['root_packet_id']])
        self.assertEqual(self.summary['comparisons']['separate']['witnesses'], [])
        self.assertEqual(self.summary['comparisons']['whole-witness']['witnesses'], ['satisfied'])
        self.assertEqual(len(self.summary['comparisons']['whole-witness']['exact_candidate_parity']), 3)

    def test_data_driven_operator_truth_tables_through_real_groups_and_trace(self):
        statuses = ('MATCH', 'MISMATCH', 'UNRESOLVED')
        for operator, pair in itertools.product(('ALL_OF', 'ANY_OF'), itertools.product(statuses, repeat=2)):
            expected = ('MISMATCH' if 'MISMATCH' in pair else 'UNRESOLVED' if 'UNRESOLVED' in pair else 'MATCH') \
                if operator == 'ALL_OF' else ('MATCH' if 'MATCH' in pair else 'UNRESOLVED' if 'UNRESOLVED' in pair else 'MISMATCH')
            leaves = [{'leaf_id': side, 'claim_refs': ['table-' + side + '-' + status.lower()], 'expected': True}
                      for side, status in zip(('left', 'right'), pair)]
            model = self.model(leaves, {'operator': operator, 'children': [{'leaf_id': 'left'}, {'leaf_id': 'right'}]})
            with self.subTest(operator=operator, outcomes=pair):
                value = self.evaluate(model)
                nodes = value['expression_nodes']
                self.assertEqual(nodes[0]['status'], expected)
                self.assertEqual([row['status'] for row in nodes[0]['child_outcomes']], list(pair))
                self.assertEqual([row['parent_path'] for row in nodes[1:]], ['root', 'root'])
                self.assertEqual(nodes[0]['policy_version'], c.POLICY_VERSION)
                self.assertTrue(nodes[0]['determining_child_paths'])
                self.assertEqual(value['computed_result'], {'MATCH': 'SATISFIED_UNDER_ASSERTIONS',
                    'MISMATCH': 'NOT_SATISFIED_UNDER_ASSERTIONS', 'UNRESOLVED': 'INDETERMINATE'}[expected])

    def test_group_with_known_mismatch_stays_unresolved_but_separate_mismatch_is_decisive(self):
        together = self.model([{'leaf_id': 'mixed', 'claim_refs': ['same-mismatch', 'same-unknown'], 'expected': True}],
                              {'leaf_id': 'mixed'})
        result = self.evaluate(together)
        self.assertEqual(result['computed_result'], 'INDETERMINATE')
        self.assertEqual(result['leaves'][0]['status'], 'UNRESOLVED')
        self.assertEqual(result['leaves'][0]['known_mismatch_claim_refs'], ['same-mismatch'])
        leaves = [{'leaf_id': 'negative', 'claim_refs': ['independent-mismatch'], 'expected': True},
                  {'leaf_id': 'missing', 'claim_refs': ['independent-unknown'], 'expected': True}]
        apart = self.model(leaves, {'operator': 'ALL_OF', 'children': [{'leaf_id': 'negative'}, {'leaf_id': 'missing'}]})
        v2 = self.evaluate(apart)
        self.assertEqual(v2['computed_result'], 'NOT_SATISFIED_UNDER_ASSERTIONS')
        self.assertEqual([row['status'] for row in v2['leaves']], ['MISMATCH', 'UNRESOLVED'])
        v1 = {key: value for key, value in apart.items() if key not in ('model_id', 'leaves', 'expression')}
        v1.update(model_version=c1.MODEL_VERSION, operator='ALL_OF', operands=[
            {'operand_id': row['leaf_id'], 'claim_refs': row['claim_refs'], 'expected': row['expected']} for row in leaves])
        v1_result = c1.evaluate(self.prepared(), self.packet['packet_id'], c1.seal_model(v1)).to_dict()
        self.assertEqual(v1_result['computed_result'], 'INDETERMINATE')
        self.assertNotEqual(v1_result['result_id'], v2['result_id'])
        self.assertNotEqual(v1_result['evaluator_policy_version'], v2['evaluator_policy_version'])
        self.assertIn('MISSING_ASSERTION', json.dumps(v2['selected_input_findings']))

    def test_nested_repeated_leaf_hypotheses_are_correlated_and_baseline_exact(self):
        model = DEMO.model_for(self.packet, 'unknown-alongside-mismatch', repeated=True)
        baseline = c.evaluate(self.prepared(), self.packet['packet_id'], model)
        report = s.analyze(self.prepared(), self.packet['packet_id'], model).to_dict()
        self.assertEqual(v._canonical_candidate(report['baseline']), baseline.canonical_bytes)
        self.assertEqual(report['sensitivity']['case_count'], 2)
        self.assertEqual(self.summary['sensitivity']['case_count'], 2)
        for case, expected in zip(report['sensitivity']['cases'], ('MATCH', 'MISMATCH')):
            occurrences = [row for row in case['expression_nodes'] if row.get('leaf_id') == 'route-b']
            self.assertEqual(len(occurrences), 2)
            self.assertEqual({row['status'] for row in occurrences}, {expected})
            self.assertEqual(case['selected_leaf_id'], 'route-b')
            self.assertEqual(len(case['assumptions']), 1)
            self.assertTrue(any(row['changed'] for row in case['expression_node_changes']))
        self.assertEqual([case['hypothetical_result'] for case in report['sensitivity']['cases']],
                         ['SATISFIED_UNDER_HYPOTHESIS', 'NOT_SATISFIED_UNDER_HYPOTHESIS'])

    def test_exact_false_expectation_leaf_root_and_opaque_predicates(self):
        model = self.model([{'leaf_id': 'false', 'claim_refs': ['independent-mismatch'], 'expected': False}],
                           {'leaf_id': 'false'})
        value = self.evaluate(model)
        self.assertEqual(value['computed_result'], 'SATISFIED_UNDER_ASSERTIONS')
        self.assertEqual(len(value['expression_nodes']), 1)
        self.assertEqual(value['leaves'][0]['assertions'][0]['predicate'], 'Opaque independent mismatch')
        self.assertEqual(value['retained_rule_context_authority'], 'RETAINED_VERSIONED_RULE_CONTEXT_ONLY')
        self.assertEqual(value['execution_authority'], 'BLOCKED')

    def test_every_branch_reference_and_complete_group_validated_before_decision(self):
        original = DEMO.model_for(self.packet, 'conflict-alongside-match')
        variants = []
        changed = deepcopy(original); changed['leaves'][-1]['claim_refs'].pop(); variants.append(changed)
        changed = deepcopy(original); changed['leaves'][-1]['claim_refs'] = ['absent']; variants.append(changed)
        changed = deepcopy(original); changed['leaves'][-1]['claim_refs'] = ['satisfied-route-b']; variants.append(changed)
        for changed in variants:
            with self.subTest(refs=changed['leaves'][-1]['claim_refs']), self.assertRaises(GameplayContractError):
                self.evaluate(self.seal(changed))
        for refs in ([], ['same-mismatch'], ['same-unknown']):
            with self.subTest(refs=refs), self.assertRaises(GameplayContractError):
                self.evaluate(self.model([{'leaf_id': 'mixed', 'claim_refs': refs, 'expected': True}], {'leaf_id': 'mixed'}))

    def test_closed_versions_types_references_and_no_implicit_migration(self):
        original = DEMO.model_for(self.packet, 'satisfied')
        variants = []
        def mutate(change):
            changed = deepcopy(original); change(changed); variants.append(changed)
        for scalar in (0, 1, 1.0, 'true', None, [], {}):
            mutate(lambda model, scalar=scalar: model['leaves'][0].update(expected=scalar))
        for version in ('fictional-condition-model-v1', 'fictional-condition-model-v3', 2, None):
            mutate(lambda model, version=version: model.update(model_version=version))
        mutate(lambda model: model['scope'].update(context_version=True))
        mutate(lambda model: model['packet'].update(revision=1.0))
        mutate(lambda model: model.update(leaves=tuple(model['leaves'])))
        mutate(lambda model: model['leaves'][0].update(extra=True))
        mutate(lambda model: model['leaves'][1].update(leaf_id='gate'))
        mutate(lambda model: model['leaves'][1].update(claim_refs=model['leaves'][0]['claim_refs']))
        mutate(lambda model: model['expression']['children'].append({'leaf_id': 'missing'}))
        mutate(lambda model: model.update(expression={'leaf_id': 'gate'}))
        mutate(lambda model: model['expression'].update(operator='NOT'))
        mutate(lambda model: model['expression'].update(children=[]))
        mutate(lambda model: model['expression'].update(children=32 * [{'leaf_id': 'gate'}] + [{'leaf_id': 'route-a'}, {'leaf_id': 'route-b'}]))
        mutate(lambda model: model['expression']['children'][1].update(alternative_id='foreign'))
        mutate(lambda model: model.update(extra=True))
        for changed in variants:
            with self.subTest(model=changed), self.assertRaises(GameplayContractError):
                self.seal(changed)
        with self.assertRaises(GameplayContractError):
            c1.ConditionModel(original)
        wrong = deepcopy(original); wrong['model_id'] = 'sha256:' + '0' * 64
        with self.assertRaises(GameplayContractError):
            c.ConditionModel(wrong)

    def test_expression_depth_eight_nodes_128_and_cumulative_resource_limits(self):
        single = self.model([{'leaf_id': 'leaf', 'claim_refs': ['independent-mismatch'], 'expected': True}], {'leaf_id': 'leaf'})
        deep = deepcopy(single)
        for _ in range(7):
            deep['expression'] = {'operator': 'ANY_OF', 'children': [deep['expression']]}
        deep = self.seal(deep)
        self.assertEqual(len(self.evaluate(deep)['expression_nodes']), 8)
        deep['expression'] = {'operator': 'ANY_OF', 'children': [deep['expression']]}
        with self.assertRaises(GameplayContractError):
            self.seal(deep)
        wide = deepcopy(single)
        wide['expression'] = {'operator': 'ALL_OF', 'children': [
            {'operator': 'ANY_OF', 'children': [{'leaf_id': 'leaf'}] * count} for count in (32, 32, 32, 27)]}
        self.assertEqual(len(self.evaluate(self.seal(wide))['expression_nodes']), 128)
        wide['expression']['children'][-1]['children'].append({'leaf_id': 'leaf'})
        with self.assertRaises(GameplayContractError):
            self.seal(wide)
        maximum = deepcopy(single)
        maximum['leaves'] = [{'leaf_id': 'l-' + str(i), 'expected': True,
            'claim_refs': ['r-' + str(i) + '-' + str(j) for j in range(64)]} for i in range(32)]
        maximum['expression'] = {'operator': 'ALL_OF', 'children': [{'leaf_id': row['leaf_id']} for row in maximum['leaves']]}
        self.assertEqual(len(self.seal(maximum)['leaves']), 32)
        overflow = deepcopy(maximum); overflow['leaves'].append(deepcopy(overflow['leaves'][-1]))
        with self.assertRaises(GameplayContractError):
            self.seal(overflow)
        overflow = deepcopy(maximum); overflow['leaves'][0]['claim_refs'].append('overflow')
        with self.assertRaises(GameplayContractError):
            self.seal(overflow)
        overflow = deepcopy(maximum)
        for leaf in overflow['leaves']:
            leaf['claim_refs'] = [ref + 'x' * 52 for ref in leaf['claim_refs']]
        with self.assertRaises(GameplayContractError):
            self.seal(overflow)
        # Raw structure has its own bounded allowance, independent of expression depth.
        raw = deepcopy(single); raw['unknown'] = []
        cursor = raw['unknown']
        for _ in range(c.RAW_DEPTH_LIMIT + 1):
            child = []; cursor.append(child); cursor = child
        with self.assertRaises(GameplayContractError):
            self.seal(raw)
        for change in (lambda value: value.update(unknown=[None] * c.RAW_NODE_LIMIT),
                       lambda value: value.update(condition_name='x' * 4097),
                       lambda value: value.update({('x' * 129): True})):
            raw = deepcopy(single); change(raw)
            with self.assertRaises(GameplayContractError):
                self.seal(raw)

    def test_duplicate_json_nonfinite_parser_and_unknown_dispatch_version_reject(self):
        model = DEMO.model_for(self.packet, 'satisfied')
        raw = json.dumps(model)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'model.json'
            for invalid in (raw.replace('"expected": true', '"expected": true, "expected": false', 1),
                            raw.replace('"expected": true', '"expected": NaN', 1),
                            raw.replace('"expected": true', '"expected": Infinity', 1), '{', '[]'):
                with self.subTest(raw=invalid[:80]), self.assertRaises(GameplayContractError):
                    path.write_text(invalid)
                    c.read_model(path)
            unknown = deepcopy(model); unknown['model_version'] = 'fictional-condition-model-v99'
            path.write_text(json.dumps(unknown))
            process = subprocess.run([sys.executable, '-m', 'proposed_spell_packets', '--workspace',
                str(self.directory), 'evaluate', self.packet['packet_id'], '--model', str(path), '--json'],
                cwd=ROOT, env=dict(os.environ, PYTHONPATH=str(ROOT / 'src')), capture_output=True, text=True)
            self.assertNotEqual(process.returncode, 0)
            self.assertEqual(json.loads(process.stderr)['status'], 'REJECTED')

    def test_private_immutable_ownership_result_only_and_deterministic_replay(self):
        original = DEMO.model_for(self.packet, 'unknown-alongside-match')
        owned = c.ConditionModel(original)
        expected_model = owned.canonical_bytes
        report = c.evaluate(self.prepared(), self.packet['packet_id'], owned)
        expected_result = report.canonical_bytes
        original['leaves'][0]['expected'] = False
        view = owned.to_dict(); view['expression']['children'].clear()
        decoded = report.to_dict(); decoded['leaves'].clear()
        self.assertEqual(owned.canonical_bytes, expected_model)
        self.assertEqual(report.canonical_bytes, expected_result)
        self.assertEqual(c.evaluate(self.prepared(), self.packet['packet_id'], owned).canonical_bytes, expected_result)
        with self.assertRaises(FrozenInstanceError):
            owned.canonical_bytes = b'changed'
        with self.assertRaises(FrozenInstanceError):
            report.canonical_bytes = b'changed'
        for raw in (expected_result, bytearray(expected_result), report.to_dict()):
            with self.assertRaises(GameplayContractError):
                c.ConditionResult(raw)
        with self.assertRaises(GameplayContractError):
            c.evaluate(self.prepared(), self.packet['packet_id'], report.to_dict())

    def test_existing_public_apis_explicitly_dispatch_v2_and_unknown_versions_reject(self):
        model = DEMO.model_for(self.packet, 'unknown-alongside-mismatch')
        direct = c.evaluate(self.prepared(), self.packet['packet_id'], model)
        routed = c1.evaluate(self.prepared(), self.packet['packet_id'], model)
        self.assertEqual(routed.canonical_bytes, direct.canonical_bytes)
        self.assertEqual(c1.render(routed), c.render(direct))
        sensitivity = s1.analyze(self.prepared(), self.packet['packet_id'], c.ConditionModel(model))
        self.assertEqual(sensitivity.canonical_bytes,
                         s.analyze(self.prepared(), self.packet['packet_id'], model).canonical_bytes)
        self.assertEqual(s1.render(sensitivity), s.render(sensitivity))
        definition = DEMO.definition_for(self.packet, ['failed-routes', 'satisfied'])
        alternatives = a1.evaluate(self.prepared(), self.packet['packet_id'], a.AlternativesDefinition(definition))
        self.assertEqual(alternatives.canonical_bytes,
                         a.evaluate(self.prepared(), self.packet['packet_id'], definition).canonical_bytes)
        self.assertEqual(a1.render(alternatives), a.render(alternatives))
        with self.assertRaises(GameplayContractError):
            a1.AlternativesDefinition(definition)
        for invalid in ('fictional-condition-model-v99', 2, None):
            changed = deepcopy(model); changed['model_version'] = invalid
            for consumer in (c1.evaluate, s1.analyze):
                with self.subTest(version=invalid, consumer=consumer.__name__), self.assertRaises(GameplayContractError):
                    consumer(self.prepared(), self.packet['packet_id'], changed)
        changed = deepcopy(definition); changed['definition_version'] = 'fictional-alternative-requirements-v99'
        with self.assertRaises(GameplayContractError):
            a1.evaluate(self.prepared(), self.packet['packet_id'], changed)

    def test_unchanged_v1_ordinary_sensitivity_and_comparison_golden_identities(self):
        controls = self.summary['v1_controls']
        self.assertEqual(controls['model_id'], 'sha256:4809a76b53441a81183cb6d7d7e44681cbba4ef05fc28fe45b9971d91e0cd689')
        self.assertEqual(controls['result_id'], 'sha256:9c775f4945a4ed58fcd620d8231e96c6570ccc695dca4d5d1c951a37f915ad11')
        self.assertEqual(controls['sensitivity_report_id'], 'sha256:5c0810f82cb9724078d399e969c1b6c8d37dd9b01d16b3b311ddb61607331d9f')
        self.assertEqual(controls['definition_id'], 'sha256:14c615f005cdfa05e2d747faee42dda83c8ff4ba1ffee555c96a351e214edc8c')
        self.assertEqual(controls['comparison_report_id'], 'sha256:eb1a00252765691ccb0e1ef149d84edc82e28e41d80771724a72c2267721bb9e')


if __name__ == '__main__':
    unittest.main()
