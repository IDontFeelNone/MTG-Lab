"""Demonstrate bounded conditional evidence reasoning via actual public API/CLI.

This command writes no files. A caller may explicitly redirect stdout to retain
its canonical transcript. Each CLI invocation freshly verifies current evidence;
one API admission supplies the seven analyses and ten cases from one snapshot.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import shlex
import subprocess
import sys

from card_rules_pilot import PLAN_ID
from card_rules_pilot.cards import PROFILE_ID, QUERY_ID
from card_rules_pilot.contract import canonical
from card_rules_pilot.reasoning import load_reasoning, render_reasoning
from card_rules_pilot_demo import _snapshot

ROOT = Path(__file__).resolve().parents[1]


def digest(raw):
    return {'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('catalog-root', 'mechanical-root', 'review-root', 'plan'):
        parser.add_argument('--' + name, required=True, type=Path)
    for name in ('profile-id', 'query-snapshot-id', 'plan-id'):
        parser.add_argument('--expected-' + name, required=True)
    args = parser.parse_args(argv)
    if (args.expected_profile_id, args.expected_query_snapshot_id, args.expected_plan_id) != (PROFILE_ID, QUERY_ID, PLAN_ID):
        parser.error('the three independently selected exact pilot identities are required')
    catalog, mechanical, reviews, plan = (getattr(args, key).absolute()
        for key in ('catalog_root', 'mechanical_root', 'review_root', 'plan'))
    before = _snapshot(catalog, mechanical, reviews, plan)
    def unchanged():
        if _snapshot(catalog, mechanical, reviews, plan) != before:
            raise RuntimeError('read-only demonstration changed selected retained evidence')
    reasoning = load_reasoning(catalog_root=catalog, mechanical_root=mechanical,
        review_root=reviews, plan_path=plan, expected_profile_id=args.expected_profile_id,
        expected_query_snapshot_id=args.expected_query_snapshot_id, expected_plan_id=args.expected_plan_id)
    unchanged()
    command = [sys.executable, '-m', 'card_rules_pilot', '--catalog-root', str(catalog),
        '--mechanical-root', str(mechanical), '--review-root', str(reviews), '--plan', str(plan),
        '--expected-profile-id', args.expected_profile_id,
        '--expected-query-snapshot-id', args.expected_query_snapshot_id,
        '--expected-plan-id', args.expected_plan_id]
    env = dict(os.environ, PYTHONPATH=str(ROOT / 'src'), PYTHONDONTWRITEBYTECODE='1')
    commands = []
    def cli(*suffix):
        current = command + list(suffix)
        print('$ ' + shlex.join(current), file=sys.stderr, flush=True)
        process = subprocess.run(current, cwd=ROOT, env=env, capture_output=True)
        unchanged()
        if process.returncode:
            raise RuntimeError(process.stderr.decode(errors='replace'))
        commands.append({'arguments': list(suffix), 'command': shlex.join(current),
            'exit_status': process.returncode, 'stdout': digest(process.stdout)})
        return process.stdout
    comparison = reasoning.comparison()
    baseline = comparison.to_dict()
    subjects = [row['subject_id'] for row in baseline['analyses']]
    if len(subjects) != 7:
        raise RuntimeError('exact seven computed baseline analyses required')
    for subject in subjects:
        document = reasoning.subject(subject)
        stdout = cli('analyze', subject, '--json')
        if stdout != document.to_json().encode():
            raise RuntimeError('individual computed API/CLI canonical output differs')
        if reasoning.validate_report(json.loads(stdout)).to_json().encode() != stdout:
            raise RuntimeError('individual computed report validation changed output')
        view = document.to_dict()
        view.clear()
        if document.to_json().encode() != stdout:
            raise RuntimeError('individual computed document lost immutable ownership')
    if cli('analyze-all', '--json') != comparison.to_json().encode():
        raise RuntimeError('comparison computed API/CLI canonical output differs')
    impact = reasoning.review_impact()
    hypothetical = impact.to_dict()
    if len(hypothetical['cases']) != 10:
        raise RuntimeError('exact ten bounded hypothetical cases required')
    if cli('review-impact', '--json') != impact.to_json().encode():
        raise RuntimeError('hypothetical computed API/CLI canonical output differs')
    for suffix, document in ((('analyze', 'basalt-monolith-untap'), reasoning.subject('basalt-monolith-untap')),
                             (('analyze-all',), comparison), (('review-impact',), impact)):
        if cli(*suffix).decode() != render_reasoning(document):
            raise RuntimeError('readable computed API/CLI output differs')
    original_comparison = baseline['context']['original_comparison']
    if cli('compare', '--json') != canonical(original_comparison):
        raise RuntimeError('original PR #216 comparison bytes changed')
    checked = json.loads(cli('check'))
    if checked['check'] != 'EXACT_REPRODUCTION':
        raise RuntimeError('original PR #216 retained reproduction failed')
    for document in (comparison, impact):
        original = document.to_json()
        view = document.to_dict()
        view['review']['canonical_admission'] = True
        if document.to_json() != original:
            raise RuntimeError('aggregate computed document lost immutable ownership')
        if reasoning.validate_report(json.loads(original)).to_json() != original:
            raise RuntimeError('aggregate recomputation changed output')
    if reasoning.comparison().to_json() != comparison.to_json() or reasoning.review_impact().to_json() != impact.to_json():
        raise RuntimeError('computed outputs are not deterministic')
    unchanged()
    summary = {
        'demonstration': 'BOUNDED_MANA_CLASSIFICATION_EVIDENCE_REASONING',
        'plan_id': PLAN_ID, 'policy': baseline['policy'],
        'original_comparison_id': original_comparison['report_id'],
        'original_reproduction_check': checked,
        'analysis_report_id': baseline['report_id'], 'review_impact_report_id': hypothetical['report_id'],
        'baseline_analyses': baseline['analyses'], 'hypothetical_cases': hypothetical['cases'],
        'selected_evidence_file_count': len(before), 'selected_evidence_bytes_unchanged': True,
        'api_snapshot_admissions': 1, 'fresh_cli_invocations': len(commands),
        'individual_api_cli_canonical_parity': True, 'comparison_api_cli_canonical_parity': True,
        'review_impact_api_cli_canonical_parity': True, 'readable_api_cli_parity': True,
        'immutable_independent_views': True, 'deterministic_replay': True,
        'original_output_parity': True, 'commands': commands,
        'semantic_review_status': 'PENDING_NOT_ESTABLISHED',
        'review': {'status': 'requires_review', 'human_attestation': None, 'canonical_admission': False},
        'execution_authority': 'BLOCKED'}
    sys.stdout.buffer.write(canonical(summary))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
