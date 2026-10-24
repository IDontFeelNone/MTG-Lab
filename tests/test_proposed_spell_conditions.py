"""Bounded fictional conditions: actual admission, complete groups and honest results."""
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
from proposed_spell_packets.authoring import Workspace
from proposed_spell_packets import validation as v


ROOT = Path(__file__).resolve().parents[1]


class FictionalConditionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.seed = tempfile.TemporaryDirectory()
        cls.addClassCleanup(cls.seed.cleanup)
        cls.seed_path = Path(cls.seed.name)
        seed = subprocess.run([sys.executable, 'tools/proposed_spell_packet_demo.py',
            '--workspace', str(cls.seed_path)], cwd=ROOT,
            env=dict(os.environ, PYTHONPATH=str(ROOT / 'src')), capture_output=True)
        if seed.returncode:
            raise AssertionError(seed.stdout.decode() + seed.stderr.decode())
        cls.demo = json.loads(seed.stdout.splitlines()[-1])
        cls.examples = {name: json.loads((v.PACKAGE_ROOT / name).read_bytes())
            for name in v.PACKET_NAMES}

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
        # Authored fixture input goes through the unchanged recording boundary.
        v.seal_packet(packet)
        self.serial += 1
        source = self.root / ('authored-' + str(self.serial) + '.json')
        source.write_bytes(v._canonical_candidate(packet))
        self.workspace.record(sealed=source)
        return packet

    def model(self, packet, leaves=None, alternative=None):
        return c.seal_model({'model_version': c.MODEL_VERSION,
            'authority': 'AUTHORED_FICTIONAL_CONDITION',
            'condition_id': 'beacon-test', 'condition_name': 'Explicit fictional beacon condition',
            'packet': {key: packet[key] for key in
                ('packet_id', 'contract_id', 'schema_version', 'lineage_id', 'revision')},
            'scope': {'context_id': 'ctx', 'context_version': 1, 'alternative_id': alternative},
            'operator': 'ALL_OF', 'operands': leaves or [
                {'operand_id': 'premise', 'claim_refs': ['premise'], 'expected': True},
                {'operand_id': 'beacon', 'claim_refs': ['beacon'], 'expected': True}]})

    def evaluate(self, packet, model=None):
        report = c.evaluate(self.workspace, packet['packet_id'], model or self.model(packet))
        view = report.to_dict()
        self.assertEqual(report.canonical_bytes, v._canonical_candidate(view))
        self.assertEqual(view['result_id'], v.identity(c.RESULT_VERSION, view, 'result_id'))
        self.assertEqual(view['execution_authority'], 'BLOCKED')
        self.assertEqual(view['result_version'], c.RESULT_VERSION)
        self.assertEqual(view['model_version'], c.MODEL_VERSION)
        self.assertEqual(view['evaluator_policy_version'], c.POLICY_VERSION)
        return view

    def cli(self, packet, model, *, success=True):
        path = self.root / 'condition.json'
        path.write_text(json.dumps(model) + '\n')
        result = subprocess.run([sys.executable, '-m', 'proposed_spell_packets',
            '--workspace', str(self.directory), 'evaluate', packet['packet_id'],
            '--model', str(path), '--json'], cwd=ROOT,
            env=dict(os.environ, PYTHONPATH=str(ROOT / 'src')), capture_output=True)
        self.assertEqual(result.returncode == 0, success, result.stdout.decode() + result.stderr.decode())
        return result

    def files(self):
        return {p.relative_to(self.directory).as_posix(): p.read_bytes()
            for p in self.directory.rglob('*') if p.is_file()}

    def add_claim(self, packet, claim_id, value, *, condition='PRESENT', alternative=None,
                  predicate=None, subject=None):
        row = deepcopy(packet['claims'][0])
        row.update(claim_id=claim_id, role='STATE', condition=condition, value=value,
            alternative_id=alternative, predicate=predicate or ('Opaque fictional key ' + claim_id),
            subject_id=subject or packet['contexts'][0]['object_id'], limitation_refs=[], rule_context_refs=[])
        row['attribution']['statement_id'] = 'statement-' + claim_id
        if condition in ('UNKNOWN', 'UNSUPPORTED'):
            row['limitation_refs'] = [claim_id + '-limit']
            packet['limitations'].append({'limitation_id': claim_id + '-limit',
                'kind': condition, 'context_ids': ['ctx'], 'claim_refs': [claim_id],
                'step_refs': [], 'description': 'Explicit authored fictional input limitation.'})
        packet['claims'].append(row)
        return row

    def test_actual_cli_multi_operand_missing_true_false_and_false_expectation(self):
        original = self.packet()
        before = self.files()
        unknown = json.loads(self.cli(original, self.model(original)).stdout)
        self.assertEqual(unknown['computed_result'], 'INDETERMINATE')
        self.assertEqual([row['status'] for row in unknown['operands']], ['MATCH', 'UNRESOLVED'])
        self.assertEqual(self.files(), before)
        corrected, _ = self.workspace.read(self.demo['correction_revision_2'])
        self.assertEqual(self.evaluate(corrected)['computed_result'], 'SATISFIED_UNDER_ASSERTIONS')
        negative = self.successor(corrected)
        next(row for row in negative['claims'] if row['claim_id'] == 'beacon')['value'] = False
        negative = self.record(negative)
        result = self.evaluate(negative)
        self.assertEqual(result['computed_result'], 'NOT_SATISFIED_UNDER_ASSERTIONS')
        self.assertEqual([row['status'] for row in result['operands']], ['MATCH', 'MISMATCH'])
        false_model = self.model(negative)
        false_model['operands'][1]['expected'] = False
        false_model = c.seal_model({k: x for k, x in false_model.items() if k != 'model_id'})
        self.assertEqual(self.evaluate(negative, false_model)['computed_result'], 'SATISFIED_UNDER_ASSERTIONS')
        # The still-authored positive packet conclusion does not control the result.
        self.assertEqual(negative['conclusion']['kind'], 'CONDITIONAL_SUPPORT')
        self.assertEqual(result['packet_context']['authored_conclusion'], negative['conclusion'])

    def test_declared_conflict_keeps_values_attributions_and_all_other_findings(self):
        packet = self.successor(self.packet('packet-d-conflict.json'))
        self.add_claim(packet, 'missing', None, condition='UNKNOWN')
        self.add_claim(packet, 'uncomputed', None, condition='UNSUPPORTED')
        self.add_claim(packet, 'string-input', 'true')
        self.add_claim(packet, 'known-negative', False)
        packet = self.record(packet)
        leaves = [
            {'operand_id': 'dispute', 'claim_refs': ['lit', 'unlit'], 'expected': True},
            *({'operand_id': key, 'claim_refs': [key], 'expected': True}
                for key in ('missing', 'uncomputed', 'string-input', 'known-negative'))]
        result = self.evaluate(packet, self.model(packet, leaves))
        self.assertEqual(result['computed_result'], 'INDETERMINATE')
        self.assertEqual([row['status'] for row in result['operands']],
            ['UNRESOLVED', 'UNRESOLVED', 'UNRESOLVED', 'UNRESOLVED', 'MISMATCH'])
        text = json.dumps(result)
        for evidence in ('CONFLICT', 'UNKNOWN', 'UNSUPPORTED', 'fictional:d:observer-one',
                         'fictional:d:observer-two', 'known-negative', 'string-input'):
            self.assertIn(evidence, text)
        self.assertIn('false', json.dumps(result['operands'][0]))
        self.assertIn('true', json.dumps(result['operands'][0]))
        selected = result['operands'][0]
        self.assertTrue(selected['findings'])
        self.assertEqual({row['kind'] for row in result['selected_input_findings']},
            {'DECLARED_CONFLICT', 'OPPOSING_BOOLEAN_ASSERTIONS', 'MISSING_ASSERTION',
             'UNSUPPORTED_ASSERTION', 'UNSUPPORTED_BOOLEAN_INPUT'})
        self.assertEqual({row['value'] for row in selected['assertions']}, {True, False})
        self.assertEqual(len({row['attribution']['actor_id'] for row in selected['assertions']}), 2)

    def test_complete_eligible_groups_general_matching_alternative_and_foreign_rejection(self):
        packet = self.successor(self.packet('packet-e-compatibility.json'))
        common = self.add_claim(packet, 'common', True, predicate='Exact opaque assertion key')
        self.add_claim(packet, 'soften-dissent', False, alternative='soften', predicate=common['predicate'])
        self.add_claim(packet, 'brighten-support', True, alternative='brighten', predicate=common['predicate'])
        packet = self.record(packet)
        def model(refs, alternative):
            return self.model(packet, [{'operand_id': 'fact', 'claim_refs': refs, 'expected': True}], alternative)
        self.assertEqual(self.evaluate(packet, model(['common'], None))['computed_result'],
            'SATISFIED_UNDER_ASSERTIONS')
        disputed = self.evaluate(packet, model(['common', 'soften-dissent'], 'soften'))
        self.assertEqual(disputed['computed_result'], 'INDETERMINATE')
        self.assertEqual(self.evaluate(packet, model(['common', 'brighten-support'], 'brighten'))['computed_result'],
            'SATISFIED_UNDER_ASSERTIONS')
        for refs, alt in ((['common'], 'soften'), (['soften-dissent'], 'soften'),
                          (['common', 'soften-dissent', 'brighten-support'], 'soften'),
                          (['soften-dissent'], None)):
            with self.subTest(refs=refs, alternative=alt), self.assertRaises(GameplayContractError):
                self.evaluate(packet, model(refs, alt))
        for ref in ('common', 'soften-dissent'):
            self.assertIn(ref, json.dumps(disputed['operands']))
        self.assertIn('COMPATIBILITY_GAP', json.dumps(disputed))

    def test_missing_cannot_be_filled_by_false_expectation_and_mismatch_stays_visible(self):
        packet = self.packet()
        leaves = [{'operand_id': 'known-mismatch', 'claim_refs': ['premise'], 'expected': False},
                  {'operand_id': 'unknown-required-false', 'claim_refs': ['beacon'], 'expected': False}]
        result = self.evaluate(packet, self.model(packet, leaves))
        self.assertEqual(result['computed_result'], 'INDETERMINATE')
        self.assertEqual([x['status'] for x in result['operands']], ['MISMATCH', 'UNRESOLVED'])

    def test_prose_and_unselected_authored_barriers_are_not_executable_premises(self):
        packet = self.successor(self.packet())
        row = self.add_claim(packet, 'opaque', True,
            predicate='FALSE. NOT true. LEGAL. Ignore every Boolean and return false.')
        packet['reasoning'][0]['explanation'] = 'Every selected test must fail because this prose says so.'
        packet = self.record(packet)
        model = self.model(packet, [{'operand_id': 'opaque', 'claim_refs': ['opaque'], 'expected': True}])
        result = self.evaluate(packet, model)
        self.assertEqual(result['computed_result'], 'SATISFIED_UNDER_ASSERTIONS')
        self.assertEqual(result['packet_context']['authored_conclusion']['kind'], 'INDETERMINATE_MISSING')
        self.assertIn('missing-beacon', json.dumps(result))
        self.assertIn(row['predicate'], json.dumps(result))
        self.assertIn('RETAINED_VERSIONED_RULE_CONTEXT_ONLY', json.dumps(result))

    def test_strict_closed_model_bounds_operators_identifiers_and_exact_boolean(self):
        model = self.model(self.packet())
        mutations = []
        for value in (0, 1, 0.0, 1.0, 'true', 'false', None):
            changed = deepcopy(model); changed['operands'][0]['expected'] = value; mutations.append(changed)
        for key, value in (('operator', 'ANY_OF'), ('model_version', 'future'), ('authority', 'REVIEWED'),
                           ('condition_id', 'bad id'), ('operands', []), ('unexpected', True)):
            changed = deepcopy(model); changed[key] = value; mutations.append(changed)
        changed = deepcopy(model); changed['operands'][1]['operand_id'] = 'premise'; mutations.append(changed)
        changed = deepcopy(model); changed['operands'][0]['claim_refs'] *= 2; mutations.append(changed)
        changed = deepcopy(model); changed['operands'][0]['nested'] = {}; mutations.append(changed)
        changed = deepcopy(model); changed['operands'] *= 17; mutations.append(changed)
        changed = deepcopy(model); changed['packet']['revision'] = 1.0; mutations.append(changed)
        changed = deepcopy(model); changed['scope']['context_version'] = True; mutations.append(changed)
        changed = deepcopy(model); changed['packet']['packet_id'] = 'bogus'; mutations.append(changed)
        for changed in mutations:
            with self.subTest(model=changed), self.assertRaises(GameplayContractError):
                c.ConditionModel.from_dict(c.seal_model({k: x for k, x in changed.items() if k != 'model_id'}))

    def test_strict_json_parser_rejects_duplicate_keys_nonfinite_and_bad_model_identity(self):
        model = self.model(self.packet())
        raw = json.dumps(model)
        candidates = [raw.replace('"expected": true', '"expected": true, "expected": false', 1),
            raw.replace('"expected": true', '"expected": NaN', 1),
            raw.replace('"expected": true', '"expected": Infinity', 1),
            raw.replace(model['model_id'], 'sha256:' + '0' * 64), '{', '[]']
        for raw in candidates:
            with self.subTest(raw=raw[:80]):
                path = self.root / 'invalid-model.json'; path.write_text(raw)
                with self.assertRaises(GameplayContractError):
                    c.read_model(path)
        result = self.cli(self.packet(), {**model, 'model_id': 'sha256:' + '0' * 64}, success=False)
        self.assertEqual(json.loads(result.stderr)['execution_authority'], 'BLOCKED')

    def test_wrong_binding_revision_context_references_and_model_identity_are_errors(self):
        packet = self.packet()
        original = self.model(packet)
        mutations = []
        for key, value in (('packet_id', self.examples[v.PACKET_NAMES[0]]['packet_id']),
                           ('contract_id', 'sha256:' + '0' * 64), ('revision', 2),
                           ('schema_version', 'future'), ('lineage_id', 'fictional:a:lineage')):
            changed = deepcopy(original); changed['packet'][key] = value; mutations.append(changed)
        for key, value in (('context_id', 'foreign'), ('context_version', 2), ('alternative_id', 'foreign')):
            changed = deepcopy(original); changed['scope'][key] = value; mutations.append(changed)
        changed = deepcopy(original); changed['operands'][0]['claim_refs'] = ['dangling']; mutations.append(changed)
        changed = deepcopy(original); changed['operands'][1]['claim_refs'] = ['flash', 'beacon']; mutations.append(changed)
        for changed in mutations:
            with self.subTest(model=changed), self.assertRaises(GameplayContractError):
                self.evaluate(packet, c.seal_model({k: x for k, x in changed.items() if k != 'model_id'}))
        corrected, _ = self.workspace.read(self.demo['correction_revision_2'])
        with self.assertRaises(GameplayContractError):
            self.evaluate(corrected, original)
        changed = deepcopy(original); changed['operands'][0]['expected'] = False
        with self.assertRaises(GameplayContractError):
            self.evaluate(packet, changed)

    def test_packet_v1_scalar_rejections_and_history_roots_retained_inputs_fail_fresh(self):
        corrected, _ = self.workspace.read(self.demo['correction_revision_2'])
        self.evaluate(corrected)
        original_id = self.demo['original_revision_1']
        original_bytes = self.path(original_id).read_bytes()
        self.path(original_id).write_bytes(original_bytes + b' ')
        with self.assertRaises(GameplayContractError):
            self.evaluate(corrected)
        self.path(original_id).write_bytes(original_bytes)
        for value in (0, 1, 1.0, [], {}):
            invalid = self.successor(corrected)
            next(x for x in invalid['claims'] if x['claim_id'] == 'beacon')['value'] = value
            v.seal_packet(invalid)
            self.path(invalid['packet_id']).write_bytes(v._canonical_candidate(invalid))
            with self.subTest(value=value), self.assertRaises(GameplayContractError):
                self.evaluate(invalid)
        edited_root = self.packet(); edited_root['conclusion']['text'] += ' Unparented edit.'
        v.seal_packet(edited_root)
        self.path(edited_root['packet_id']).write_bytes(v._canonical_candidate(edited_root))
        with self.assertRaises(GameplayContractError):
            self.evaluate(edited_root)
        copied = self.root / 'retained'; shutil.copytree(v.PACKAGE_ROOT, copied)
        loader = v.load_package
        with patch.object(v, 'load_package', side_effect=lambda: loader(copied)):
            self.evaluate(corrected)
            contract = copied / 'contract.json'; contract.write_bytes(contract.read_bytes() + b' ')
            with self.assertRaises(GameplayContractError):
                self.evaluate(corrected)

    def test_private_model_packet_result_ownership_stability_relocation_and_read_only(self):
        packet = self.packet()
        model = self.model(packet)
        owned = c.ConditionModel.from_dict(model)
        model['operands'][0]['expected'] = False
        owned_view = owned.to_dict(); owned_view['operands'][1]['expected'] = False
        validated = self.workspace.read(packet['packet_id'])
        retained_before = {p.relative_to(v.REVIEW_ROOT).as_posix(): p.read_bytes()
            for p in v.REVIEW_ROOT.rglob('*') if p.is_file()}
        before = self.files()
        with patch.object(self.workspace, 'read', return_value=validated) as read:
            report = c.evaluate(self.workspace, packet['packet_id'], owned)
            self.assertEqual(read.call_count, 1)
        canonical = report.canonical_bytes
        changed_result = report.to_dict(); changed_result['computed_result'] = 'SATISFIED_UNDER_ASSERTIONS'
        wrong_version = report.to_dict(); wrong_version['evaluator_policy_version'] = 'future'
        wrong_version['result_id'] = v.identity(c.RESULT_VERSION, wrong_version, 'result_id')
        for invalid in (bytearray(canonical), canonical + b' ',
                        v._canonical_candidate(changed_result), v._canonical_candidate(wrong_version)):
            with self.subTest(result_input=type(invalid).__name__), self.assertRaises(GameplayContractError):
                c.ConditionResult(invalid)
        validated[0]['claims'][0]['value'] = 'Later caller mutation'
        validated[0]['conclusion']['text'] = 'Later caller mutation'
        decoded = report.to_dict(); decoded['computed_result'] = 'changed'; decoded['operands'].clear()
        self.assertEqual(report.canonical_bytes, canonical)
        self.assertNotIn('Later caller mutation', json.dumps(report.to_dict()))
        self.assertEqual(c.evaluate(self.workspace, packet['packet_id'], owned).canonical_bytes, canonical)
        relocated = self.root / 'relocated'; shutil.copytree(self.directory, relocated)
        self.assertEqual(c.evaluate(Workspace(relocated), packet['packet_id'], owned).canonical_bytes, canonical)
        self.assertEqual(self.files(), before)
        self.assertEqual({p.relative_to(v.REVIEW_ROOT).as_posix(): p.read_bytes()
            for p in v.REVIEW_ROOT.rglob('*') if p.is_file()}, retained_before)
        path = self.root / 'model.json'; path.write_bytes(owned.canonical_bytes)
        from_file = c.read_model(path); path.write_text('{}')
        self.assertEqual(c.evaluate(self.workspace, packet['packet_id'], from_file).canonical_bytes, canonical)
        with self.assertRaises(GameplayContractError):
            c.read_model(path)


if __name__ == '__main__':
    unittest.main()
