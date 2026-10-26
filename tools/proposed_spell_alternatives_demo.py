"""Actual CLI demonstration of explicit fictional requirements over retained E descendants."""
from __future__ import annotations

import argparse
from copy import deepcopy
import json
import os
from pathlib import Path
import shlex
import subprocess
import sys

from proposed_spell_packets import alternatives as a
from proposed_spell_packets import conditions as c
from proposed_spell_packets import validation as v

ROOT = Path(__file__).resolve().parents[1]
SCENARIOS = {
    'A-separate': ['soften', 'brighten'],
    'B-witness': ['soften', 'brighten', 'steady'],
    'C-unknown': ['steady', 'missing'],
    'D-findings': ['steady', 'disputed', 'unsupported', 'text-only', 'declared'],
    'E-negative': ['soften', 'brighten'],
}


def author_assertions(packet):
    """Explicit supplied Boolean facts; no retained prose is interpreted."""
    template = deepcopy(packet['claims'][0])
    def claim(claim_id, alternative, predicate, value, condition='PRESENT'):
        row = deepcopy(template)
        row.update(claim_id=claim_id, alternative_id=alternative, role='STATE',
                   predicate=predicate, condition=condition, value=value,
                   rule_context_refs=[], limitation_refs=[],
                   attribution={'actor_id': 'fictional:e:requirements-demo-author',
                                'statement_id': 'statement-' + claim_id})
        packet['claims'].append(row)
        if condition in ('UNKNOWN', 'UNSUPPORTED', 'CONFLICTING'):
            limit = claim_id + '-limit'
            row['limitation_refs'] = [limit]
            packet['limitations'].append({'limitation_id': limit,
                'kind': 'CONFLICT' if condition == 'CONFLICTING' else condition,
                'context_ids': ['ctx'], 'claim_refs': [claim_id], 'step_refs': [],
                'description': 'Explicit fictional ' + condition + ' assertion supplied for this demonstration.'})
        return row
    for alternative in ('steady', 'missing', 'disputed', 'unsupported', 'text-only', 'declared'):
        packet['choices'].append({'alternative_id': alternative, 'choice_id': 'choice-' + alternative,
            'claim_refs': [alternative + '-a'], 'context_id': 'ctx',
            'description': 'Separately declared fictional option; feasibility and co-selection unestablished.'})
    facts = {'soften': (True, False), 'brighten': (False, True), 'steady': (True, True),
             'missing': (None, False), 'disputed': (True, True),
             'unsupported': (True, True), 'text-only': (True, True), 'declared': (True, True)}
    for alternative, (first, second) in facts.items():
        claim(alternative + '-a', alternative, 'Opaque requirement A', first,
              'UNKNOWN' if alternative == 'missing' else 'PRESENT')
        claim(alternative + '-b', alternative, 'Opaque requirement B', second)
    claim('general-integrity', None, 'Opaque integrity requirement', True)
    claim('steady-integrity', 'steady', 'Opaque integrity requirement', True)
    claim('disputed-integrity', 'disputed', 'Opaque integrity requirement', False)
    claim('unsupported-integrity', 'unsupported', 'Opaque integrity requirement', None, 'UNSUPPORTED')
    claim('text-only-integrity', 'text-only', 'Opaque integrity requirement', 'true')
    first = claim('declared-integrity', 'declared', 'Opaque integrity requirement', True, 'CONFLICTING')
    second = claim('declared-integrity-opposing', 'declared', 'Opaque integrity requirement', False)
    second['condition'] = 'CONFLICTING'
    second['limitation_refs'] = first['limitation_refs'][:]
    packet['limitations'][-1]['claim_refs'].append(second['claim_id'])


def definition_for(packet, alternatives, *, integrity=False):
    requirements = [
        {'requirement_id': 'requirement-a', 'subject_id': 'fictional:e:object',
         'predicate': 'Opaque integrity requirement' if integrity else 'Opaque requirement A', 'expected': True},
        {'requirement_id': 'requirement-b', 'subject_id': 'fictional:e:object',
         'predicate': 'Opaque requirement B', 'expected': True}]
    candidates = []
    for alternative in alternatives:
        candidates.append({'alternative_id': alternative, 'bindings': [
            {'requirement_id': 'requirement-a',
             'claim_refs': (['general-integrity', alternative + '-integrity'] +
                            (['declared-integrity-opposing'] if alternative == 'declared' else [])) if integrity else [alternative + '-a']},
            {'requirement_id': 'requirement-b', 'claim_refs': [alternative + '-b']}]})
    return a.seal_definition({'definition_version': a.DEFINITION_VERSION,
        'authority': 'AUTHORED_FICTIONAL_REQUIREMENTS',
        'packet': {key: packet[key] for key in c.PACKET_FIELDS},
        'scope': {'context_id': 'ctx', 'context_version': 1},
        'requirements': requirements, 'candidates': candidates})


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--workspace', required=True, type=Path)
    args = parser.parse_args()
    workspace = args.workspace.absolute()
    if (not workspace.is_dir() or any(p.is_symlink() for p in (workspace, *workspace.parents))
            or any(workspace.iterdir()) or workspace == ROOT or ROOT in workspace.parents):
        parser.error('workspace must be an existing empty directory outside the repository without symlinks')
    drafts = workspace / 'drafts'; drafts.mkdir()
    definitions = workspace / 'requirements'; definitions.mkdir()
    env = dict(os.environ, PYTHONPATH=str(ROOT / 'src'))
    def cli(*arguments, reject=False):
        command = [sys.executable, '-m', 'proposed_spell_packets', '--workspace', str(workspace), *map(str, arguments)]
        print('$ ' + shlex.join(command), flush=True)
        process = subprocess.run(command, cwd=ROOT, env=env, capture_output=True, text=True)
        if reject:
            if process.returncode == 0:
                raise RuntimeError('missing group was accepted')
            print(process.stdout + process.stderr, end='', flush=True)
        elif process.returncode:
            raise RuntimeError(process.stdout + process.stderr)
        return process.stdout
    def save(path, value):
        path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    root_draft = drafts / 'retained-e.json'
    cli('draft', '--example', 'packet-e-compatibility.json', '--output', root_draft)
    root_id = json.loads(cli('record', '--draft', root_draft))['packet_id']
    root_path = workspace / 'packets' / (root_id[7:] + '.json')
    if root_path.read_bytes() != (v.PACKAGE_ROOT / 'packet-e-compatibility.json').read_bytes():
        raise RuntimeError('retained E bytes changed')
    child_draft = drafts / 'explicit-assertions.json'
    cli('draft', '--base', root_id, '--output', child_draft)
    draft = json.loads(child_draft.read_bytes())
    draft['packet']['history']['review_observations'] = []
    author_assertions(draft['packet'])
    save(child_draft, draft)
    packet_id = json.loads(cli('record', '--draft', child_draft))['packet_id']
    packet = json.loads((workspace / 'packets' / (packet_id[7:] + '.json')).read_bytes())
    for label, candidates in SCENARIOS.items():
        save(definitions / (label + '.json'), definition_for(packet, candidates, integrity=label == 'D-findings'))
    # This exact requirement has no group in retained E. Its absence is a binding error.
    missing = definition_for(packet, ['soften'])
    missing.pop('definition_id')
    missing['packet'] = {key: json.loads(root_path.read_bytes())[key] for key in c.PACKET_FIELDS}
    missing = a.seal_definition(missing)
    save(definitions / 'missing-group.json', missing)
    before = {p.relative_to(workspace).as_posix(): p.read_bytes() for p in workspace.rglob('*') if p.is_file()}
    outputs = {}
    for label in SCENARIOS:
        path = definitions / (label + '.json')
        readable = cli('evaluate-alternatives', packet_id, '--requirements', path)
        report = json.loads(cli('evaluate-alternatives', packet_id, '--requirements', path, '--json'))
        print('Scenario ' + label + ': ' + report['computed_result'], flush=True)
        for candidate in report['candidates']:
            print('Candidate ' + candidate['alternative_id'] + ': ' + candidate['condition_result']['computed_result'] +
                  ' outcomes=' + json.dumps([row['status'] for row in candidate['condition_result']['operands']]) +
                  ' findings=' + json.dumps(candidate['condition_result']['selected_input_findings']) +
                  ' mismatches=' + json.dumps(candidate['known_mismatches']), flush=True)
        if not readable.strip():
            raise RuntimeError('empty readable output')
        outputs[label] = {'packet_id': packet_id, 'definition_id': report['definition_id'],
            'report_id': report['report_id'], 'computed_result': report['computed_result'],
            'satisfying_alternative_ids': report['satisfying_alternative_ids'],
            'candidates': [{'alternative_id': row['alternative_id'], 'model_id': row['condition_result']['model_id'],
                            'result_id': row['condition_result']['result_id'], 'computed_result': row['condition_result']['computed_result']}
                           for row in report['candidates']]}
    cli('evaluate-alternatives', root_id, '--requirements', definitions / 'missing-group.json', reject=True)
    after = {p.relative_to(workspace).as_posix(): p.read_bytes() for p in workspace.rglob('*') if p.is_file()}
    if before != after:
        raise RuntimeError('evaluation wrote workspace files')
    if outputs['A-separate']['satisfying_alternative_ids'] or outputs['E-negative']['satisfying_alternative_ids']:
        raise RuntimeError('separate successes fabricated a shared witness')
    for label in ('B-witness', 'C-unknown', 'D-findings'):
        if outputs[label]['satisfying_alternative_ids'] != ['steady']:
            raise RuntimeError('unexpected witnesses')
    print(json.dumps({'root_packet_id': root_id, 'results': outputs,
        'all_input_and_history_bytes_unchanged': True, 'retained_e_prose_preserved': True,
        'explicit_assertions_author': 'fictional:e:requirements-demo-author',
        'missing_group_rejected_without_synthetic_evidence': True,
        'execution_authority': 'BLOCKED'}, sort_keys=True), flush=True)


if __name__ == '__main__':
    main()
