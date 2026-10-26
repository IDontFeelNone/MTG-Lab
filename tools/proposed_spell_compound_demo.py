"""Actual offline authoring/admission/CLI demonstration of bounded compound conditions."""
from __future__ import annotations

import argparse
from copy import deepcopy
import json
import os
from pathlib import Path
import shlex
import subprocess
import sys

from proposed_spell_packets import alternatives as a1
from proposed_spell_packets import alternatives_v2 as a
from proposed_spell_packets import conditions as c1
from proposed_spell_packets import conditions_v2 as c
from proposed_spell_packets import validation as v

ROOT = Path(__file__).resolve().parents[1]
FACTS = ('gate', 'route-a', 'route-b')
SCENARIOS = {
    'satisfied': (True, True, False),
    'unknown-alongside-match': (True, True, None),
    'unknown-alongside-mismatch': (True, False, None),
    'failed-gate-unresolved-routes': (False, False, None),
    'failed-routes': (True, False, False),
    'unsupported-alongside-match': (True, True, 'UNSUPPORTED'),
    'conflict-alongside-match': (True, True, 'CONFLICTING'),
    'route-without-gate': (False, True, False),
}
EXPECTED = {
    'satisfied': 'SATISFIED_UNDER_ASSERTIONS',
    'unknown-alongside-match': 'SATISFIED_UNDER_ASSERTIONS',
    'unknown-alongside-mismatch': 'INDETERMINATE',
    'failed-gate-unresolved-routes': 'NOT_SATISFIED_UNDER_ASSERTIONS',
    'failed-routes': 'NOT_SATISFIED_UNDER_ASSERTIONS',
    'unsupported-alongside-match': 'SATISFIED_UNDER_ASSERTIONS',
    'conflict-alongside-match': 'SATISFIED_UNDER_ASSERTIONS',
    'route-without-gate': 'NOT_SATISFIED_UNDER_ASSERTIONS',
}


def expression(*, repeated=False):
    routes = {'operator': 'ANY_OF', 'children': [{'leaf_id': 'route-a'}, {'leaf_id': 'route-b'}]}
    return {'operator': 'ALL_OF', 'children': [{'leaf_id': 'gate'}, routes] +
            ([deepcopy(routes)] if repeated else [])}


def author_assertions(packet):
    """Supply explicit fictional assertions with attribution; no retained prose is interpreted."""
    template = deepcopy(packet['claims'][0])
    def claim(claim_id, alternative, predicate, value, condition='PRESENT'):
        row = deepcopy(template)
        row.update(claim_id=claim_id, alternative_id=alternative, role='STATE',
                   predicate=predicate, condition=condition, value=value,
                   rule_context_refs=[], limitation_refs=[],
                   attribution={'actor_id': 'fictional:e:compound-demo-author',
                                'statement_id': 'statement-' + claim_id})
        packet['claims'].append(row)
        if condition in ('UNKNOWN', 'UNSUPPORTED', 'CONFLICTING'):
            limit = claim_id + '-limit'
            row['limitation_refs'] = [limit]
            packet['limitations'].append({'limitation_id': limit,
                'kind': 'CONFLICT' if condition == 'CONFLICTING' else condition,
                'context_ids': ['ctx'], 'claim_refs': [claim_id], 'step_refs': [],
                'description': 'Explicit fictional ' + condition + ' assertion for the compound demonstration.'})
        return row
    for alternative, facts in SCENARIOS.items():
        packet['choices'].append({'alternative_id': alternative, 'choice_id': 'choice-' + alternative,
            'claim_refs': [alternative + '-gate'], 'context_id': 'ctx',
            'description': 'Explicit fictional candidate; feasibility and co-selection unestablished.'})
        for fact, value in zip(FACTS, facts):
            special = value if type(value) is str else 'UNKNOWN' if value is None else 'PRESENT'
            actual = None if special in ('UNKNOWN', 'UNSUPPORTED') else True if special == 'CONFLICTING' else value
            row = claim(alternative + '-' + fact, alternative, 'Opaque compound ' + fact, actual, special)
            if special == 'CONFLICTING':
                opposing = claim(alternative + '-' + fact + '-opposing', alternative,
                                 row['predicate'], False)
                opposing['condition'] = 'CONFLICTING'
                opposing['limitation_refs'] = row['limitation_refs'][:]
                packet['limitations'][-1]['claim_refs'].append(opposing['claim_id'])
    for side in ('left', 'right'):
        for status, value in (('match', True), ('mismatch', False), ('unresolved', None)):
            claim('table-' + side + '-' + status, None, 'Opaque table ' + side + ' ' + status,
                  value, 'UNKNOWN' if value is None else 'PRESENT')
    claim('same-mismatch', None, 'Opaque mixed group', False)
    claim('same-unknown', None, 'Opaque mixed group', None, 'UNKNOWN')
    claim('independent-mismatch', None, 'Opaque independent mismatch', False)
    claim('independent-unknown', None, 'Opaque independent unknown', None, 'UNKNOWN')


def model_for(packet, alternative, *, repeated=False):
    return c.seal_model({'model_version': c.MODEL_VERSION, 'authority': c.MODEL_AUTHORITY,
        'condition_id': 'gate-and-routes', 'condition_name': 'Gate and an explicitly authored route',
        'packet': {key: packet[key] for key in c1.PACKET_FIELDS},
        'scope': {'context_id': 'ctx', 'context_version': 1, 'alternative_id': alternative},
        'leaves': [{'leaf_id': fact, 'claim_refs': [alternative + '-' + fact] +
                   ([alternative + '-' + fact + '-opposing']
                    if alternative == 'conflict-alongside-match' and fact == 'route-b' else []),
                    'expected': True} for fact in FACTS],
        'expression': expression(repeated=repeated)})


def definition_for(packet, alternatives):
    return a.seal_definition({'definition_version': a.DEFINITION_VERSION,
        'authority': a.DEFINITION_AUTHORITY, 'packet': {key: packet[key] for key in c1.PACKET_FIELDS},
        'scope': {'context_id': 'ctx', 'context_version': 1},
        'requirements': [{'requirement_id': fact, 'subject_id': 'fictional:e:object',
                          'predicate': 'Opaque compound ' + fact, 'expected': True} for fact in FACTS],
        'expression': expression(), 'candidates': [
            {'alternative_id': alternative, 'bindings': [
                {'requirement_id': leaf['leaf_id'], 'claim_refs': leaf['claim_refs']}
                for leaf in model_for(packet, alternative)['leaves']]}
            for alternative in alternatives]})


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--workspace', required=True, type=Path)
    args = parser.parse_args()
    workspace = args.workspace.absolute()
    if (not workspace.is_dir() or any(p.is_symlink() for p in (workspace, *workspace.parents))
            or any(workspace.iterdir()) or workspace == ROOT or ROOT in workspace.parents):
        parser.error('workspace must be an existing empty directory outside the repository without symlinks')
    for name in ('drafts', 'models', 'requirements'):
        (workspace / name).mkdir()
    env = dict(os.environ, PYTHONPATH=str(ROOT / 'src'))
    def files():
        return {p.relative_to(workspace).as_posix(): p.read_bytes()
                for p in workspace.rglob('*') if p.is_file()}
    def save(path, value):
        path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    def cli(*arguments, reject=False):
        command = [sys.executable, '-m', 'proposed_spell_packets', '--workspace', str(workspace), *map(str, arguments)]
        print('$ ' + shlex.join(command), flush=True)
        before = files()
        process = subprocess.run(command, cwd=ROOT, env=env, capture_output=True, text=True)
        if arguments[0] in ('evaluate', 'sensitivity', 'evaluate-alternatives') and files() != before:
            raise RuntimeError('evaluation wrote workspace files')
        if reject:
            if not process.returncode:
                raise RuntimeError('invalid hidden branch was accepted')
            print(process.stderr, end='', flush=True)
        elif process.returncode:
            raise RuntimeError(process.stdout + process.stderr)
        return process.stdout
    root_draft = workspace / 'drafts' / 'retained-e.json'
    cli('draft', '--example', 'packet-e-compatibility.json', '--output', root_draft)
    root_id = json.loads(cli('record', '--draft', root_draft))['packet_id']
    root_path = workspace / 'packets' / (root_id[7:] + '.json')
    root_bytes = root_path.read_bytes()
    if root_bytes != (v.PACKAGE_ROOT / 'packet-e-compatibility.json').read_bytes():
        raise RuntimeError('retained E root bytes changed')
    child_draft = workspace / 'drafts' / 'compound-assertions.json'
    cli('draft', '--base', root_id, '--output', child_draft)
    draft = json.loads(child_draft.read_bytes())
    draft['packet']['history']['review_observations'] = []
    author_assertions(draft['packet'])
    save(child_draft, draft)
    packet_id = json.loads(cli('record', '--draft', child_draft))['packet_id']
    packet_path = workspace / 'packets' / (packet_id[7:] + '.json')
    packet_bytes = packet_path.read_bytes()
    packet = json.loads(packet_bytes)
    results = {}
    for alternative, expected in EXPECTED.items():
        path = workspace / 'models' / (alternative + '.json')
        save(path, model_for(packet, alternative))
        readable = cli('evaluate', packet_id, '--model', path)
        raw = cli('evaluate', packet_id, '--model', path, '--json')
        report = json.loads(raw)
        if report['computed_result'] != expected or not readable.strip():
            raise RuntimeError('unexpected result for ' + alternative)
        if alternative == 'unknown-alongside-match' and cli('evaluate', packet_id, '--model', path, '--json') != raw:
            raise RuntimeError('ordinary replay differed')
        results[alternative] = {'model_id': report['model_id'], 'result_id': report['result_id'],
            'computed_result': report['computed_result'],
            'leaf_statuses': [row['status'] for row in report['leaves']],
            'selected_input_findings': report['selected_input_findings']}
        print('Scenario ' + alternative + ': ' + json.dumps(results[alternative], sort_keys=True), flush=True)
    invalid = model_for(packet, 'conflict-alongside-match')
    invalid.pop('model_id'); invalid['leaves'][-1]['claim_refs'].pop()
    invalid_path = workspace / 'models' / 'incomplete-hidden-branch.json'
    save(invalid_path, c.seal_model(invalid))
    cli('evaluate', packet_id, '--model', invalid_path, '--json', reject=True)
    invalid['leaves'][-1]['claim_refs'] = ['nonexistent']
    malformed_path = workspace / 'models' / 'dangling-hidden-branch.json'
    save(malformed_path, c.seal_model(invalid))
    cli('evaluate', packet_id, '--model', malformed_path, '--json', reject=True)
    repeated_path = workspace / 'models' / 'repeated.json'
    save(repeated_path, model_for(packet, 'unknown-alongside-mismatch', repeated=True))
    repeated_baseline = json.loads(cli('evaluate', packet_id, '--model', repeated_path, '--json'))
    sensitivity_raw = cli('sensitivity', packet_id, '--model', repeated_path, '--json')
    sensitivity = json.loads(sensitivity_raw)
    if cli('sensitivity', packet_id, '--model', repeated_path, '--json') != sensitivity_raw:
        raise RuntimeError('sensitivity replay differed')
    cli('sensitivity', packet_id, '--model', repeated_path)
    if v._canonical_candidate(sensitivity['baseline']) != v._canonical_candidate(repeated_baseline):
        raise RuntimeError('sensitivity ordinary baseline changed')
    cases = sensitivity['sensitivity']['cases']
    if len(cases) != 2 or [case['assumed_value'] for case in cases] != [True, False]:
        raise RuntimeError('repeated leaf created independent cases')
    for case, expected in zip(cases, ('MATCH', 'MISMATCH')):
        occurrences = [row for row in case['expression_nodes'] if row.get('leaf_id') == 'route-b']
        if len(occurrences) != 2 or any(row['status'] != expected for row in occurrences):
            raise RuntimeError('repeated leaf hypotheses were not correlated')
    comparisons = {}
    for name, alternatives, witnesses in (
            ('separate', ['failed-routes', 'route-without-gate'], []),
            ('whole-witness', ['failed-routes', 'route-without-gate', 'satisfied'], ['satisfied'])):
        path = workspace / 'requirements' / (name + '.json')
        save(path, definition_for(packet, alternatives))
        raw = cli('evaluate-alternatives', packet_id, '--requirements', path, '--json')
        report = json.loads(raw)
        cli('evaluate-alternatives', packet_id, '--requirements', path)
        if name == 'whole-witness' and cli('evaluate-alternatives', packet_id, '--requirements', path, '--json') != raw:
            raise RuntimeError('comparison replay differed')
        if report['satisfying_alternative_ids'] != witnesses:
            raise RuntimeError('different candidates created a shared witness')
        parity = []
        for candidate in report['candidates']:
            candidate_path = workspace / 'models' / ('candidate-' + candidate['alternative_id'] + '.json')
            save(candidate_path, candidate['condition_model'])
            standalone = cli('evaluate', packet_id, '--model', candidate_path, '--json').encode()
            if standalone != v._canonical_candidate(candidate['condition_result']):
                raise RuntimeError('embedded/standalone candidate canonical bytes differ')
            # Every emitted model is also usable directly by the sensitivity workflow.
            cli('sensitivity', packet_id, '--model', candidate_path, '--json')
            parity.append({'alternative_id': candidate['alternative_id'],
                           'model_id': candidate['model_id'], 'result_id': candidate['result_id']})
        comparisons[name] = {'definition_id': report['definition_id'], 'report_id': report['report_id'],
            'computed_result': report['computed_result'], 'witnesses': witnesses, 'exact_candidate_parity': parity}
        print('Comparison ' + name + ': ' + json.dumps(comparisons[name], sort_keys=True), flush=True)
    # Actual retained B supplies the unchanged v1 ordinary and sensitivity identity controls.
    b_draft = workspace / 'drafts' / 'retained-b.json'
    cli('draft', '--example', 'packet-b-missing.json', '--output', b_draft)
    b_id = json.loads(cli('record', '--draft', b_draft))['packet_id']
    b = json.loads((workspace / 'packets' / (b_id[7:] + '.json')).read_bytes())
    v1_model = c1.seal_model({'model_version': c1.MODEL_VERSION, 'authority': c1.MODEL_AUTHORITY,
        'condition_id': 'premise-and-lit-beacon', 'condition_name': 'Fictional premise and lit beacon',
        'packet': {key: b[key] for key in c1.PACKET_FIELDS},
        'scope': {'context_id': 'ctx', 'context_version': 1, 'alternative_id': None},
        'operator': 'ALL_OF', 'operands': [
            {'operand_id': 'explicit-premise', 'claim_refs': ['premise'], 'expected': True},
            {'operand_id': 'lit-beacon', 'claim_refs': ['beacon'], 'expected': True}]})
    v1_path = workspace / 'models' / 'v1-control.json'; save(v1_path, v1_model)
    v1_result = json.loads(cli('evaluate', b_id, '--model', v1_path, '--json'))
    v1_sensitivity = json.loads(cli('sensitivity', b_id, '--model', v1_path, '--json'))
    retained_e = json.loads(root_bytes)
    v1_definition = a1.seal_definition({'definition_version': a1.DEFINITION_VERSION,
        'authority': a1.DEFINITION_AUTHORITY, 'packet': {key: retained_e[key] for key in c1.PACKET_FIELDS},
        'scope': {'context_id': 'ctx', 'context_version': 1},
        'requirements': [{'requirement_id': 'retained-ban', 'subject_id': 'fictional:e:object',
                          'predicate': retained_e['claims'][0]['predicate'], 'expected': True}],
        'candidates': [{'alternative_id': alt, 'bindings': [
            {'requirement_id': 'retained-ban', 'claim_refs': ['ban']}]} for alt in ('soften', 'brighten')]})
    v1_definition_path = workspace / 'requirements' / 'v1-control.json'; save(v1_definition_path, v1_definition)
    v1_comparison = json.loads(cli('evaluate-alternatives', root_id, '--requirements', v1_definition_path, '--json'))
    if root_path.read_bytes() != root_bytes or packet_path.read_bytes() != packet_bytes:
        raise RuntimeError('retained root or descendant bytes changed')
    summary = {'root_packet_id': root_id, 'packet_id': packet_id, 'results': results,
        'comparisons': comparisons, 'sensitivity': {'report_id': sensitivity['report_id'],
            'baseline_result_id': sensitivity['baseline_result_id'], 'case_count': len(cases),
            'hypothetical_results': [case['hypothetical_result'] for case in cases],
            'repeated_leaf_occurrences': 2, 'all_occurrences_correlated': True},
        'v1_controls': {'model_id': v1_model['model_id'], 'result_id': v1_result['result_id'],
            'sensitivity_report_id': v1_sensitivity['report_id'],
            'definition_id': v1_definition['definition_id'], 'comparison_report_id': v1_comparison['report_id']},
        'retained_root_bytes_and_reachable_history_preserved': True,
        'all_evaluation_invocations_read_only': True, 'hidden_invalid_branches_rejected': True,
        'explicit_assertions_author': 'fictional:e:compound-demo-author', 'execution_authority': 'BLOCKED'}
    print(json.dumps(summary, sort_keys=True), flush=True)


if __name__ == '__main__':
    main()
