"""Reproduce the fixed seven-subject review through its public API and real CLI.

Read commands write no artifacts. Optional transcripts require an explicitly
selected existing empty directory outside every evidence root. Bounded snapshots
cover only the selected evidence, controls and pilot artifacts, never a new
repository-wide preservation inventory.
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

from card_rules_pilot import PLAN_ID, load_pilot, render
from card_rules_pilot.cards import ACQUISITION, CARD_BINDINGS, PROFILE_ID, QUERY_ID
from card_rules_pilot.contract import canonical
from card_rules_pilot.rules import PACKAGE_IDS, activated

ROOT = Path(__file__).resolve().parents[1]


def digest(raw):
    return {'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}


def _snapshot(catalog_root, mechanical_root, review_root, plan):
    files = [catalog_root / 'config/catalog_profiles/legacy-public-tier-a.json',
        mechanical_root / 'data/review/mechanical-card-cohort/dossiers.jsonl',
        mechanical_root / 'data/review/mechanical-card-cohort/manifest.json']
    # The approved attachment validates the actual catalog representation. Do
    # not guess name-derived canonical directories or access excluded audit
    # capabilities merely to take the demonstration's bounded byte snapshot.
    directories = [mechanical_root / 'data/market/acquisitions' / ACQUISITION,
        plan.parent, *[review_root / name for name in PACKAGE_IDS],
        review_root / activated.PACKAGE_NAME,
        review_root / 'gameplay-rules-artifact-verification']
    for directory in directories:
        if not directory.is_dir() or any(p.is_symlink() for p in (directory, *directory.parents)):
            raise ValueError('ordinary selected evidence directory required')
        entries = list(directory.iterdir())
        if len(entries) > 20 or any(not p.is_file() for p in entries):
            raise ValueError('bounded selected evidence directory required')
        files.extend(entries)
    if len(files) > 100:
        raise ValueError('bounded demonstration evidence selection exceeded')
    result = {}
    for path in sorted(set(files)):
        if any(p.is_symlink() for p in (path, *path.parents)) or path.stat().st_nlink != 1:
            raise ValueError('ordinary selected evidence file required')
        with path.open('rb') as stream:
            raw = stream.read(3_000_001)
        if len(raw) > 3_000_000:
            raise ValueError('bounded demonstration evidence file exceeded')
        result[str(path)] = digest(raw)
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('catalog-root', 'mechanical-root', 'review-root', 'plan'):
        parser.add_argument('--' + name, required=True, type=Path)
    parser.add_argument('--expected-profile-id', required=True)
    parser.add_argument('--expected-query-snapshot-id', required=True)
    parser.add_argument('--expected-plan-id', required=True)
    parser.add_argument('--output-directory', type=Path,
        help='explicit existing empty external directory for demonstration transcripts only')
    args = parser.parse_args(argv)
    if (args.expected_profile_id, args.expected_query_snapshot_id, args.expected_plan_id) != (PROFILE_ID, QUERY_ID, PLAN_ID):
        parser.error('the three independently selected exact pilot identities are required')
    catalog, mechanical, reviews, plan = (getattr(args, key).absolute()
        for key in ('catalog_root', 'mechanical_root', 'review_root', 'plan'))
    destination = args.output_directory.absolute() if args.output_directory else None
    if destination is not None:
        forbidden = (ROOT, catalog, mechanical, reviews, plan.parent)
        if (not destination.is_dir() or any(destination.iterdir())
                or any(p.is_symlink() for p in (destination, *destination.parents))
                or any(destination == root or root in destination.parents for root in forbidden)):
            parser.error('output-directory must be existing, empty and outside all repository/evidence roots')
    original = _snapshot(catalog, mechanical, reviews, plan)
    def unchanged():
        if _snapshot(catalog, mechanical, reviews, plan) != original:
            raise RuntimeError('a read command changed selected retained evidence')
    pilot = load_pilot(catalog_root=catalog, mechanical_root=mechanical, review_root=reviews,
        plan_path=plan, expected_profile_id=args.expected_profile_id,
        expected_query_snapshot_id=args.expected_query_snapshot_id,
        expected_plan_id=args.expected_plan_id)
    unchanged()
    base = [sys.executable, '-m', 'card_rules_pilot', '--catalog-root', str(catalog),
        '--mechanical-root', str(mechanical), '--review-root', str(reviews), '--plan', str(plan),
        '--expected-profile-id', args.expected_profile_id,
        '--expected-query-snapshot-id', args.expected_query_snapshot_id,
        '--expected-plan-id', args.expected_plan_id]
    env = dict(os.environ, PYTHONPATH=str(ROOT / 'src'), PYTHONDONTWRITEBYTECODE='1')
    commands = []
    def cli(*arguments):
        command = base + list(arguments)
        print('$ ' + shlex.join(command), file=sys.stderr, flush=True)
        process = subprocess.run(command, cwd=ROOT, env=env, capture_output=True)
        unchanged()
        if process.returncode:
            raise RuntimeError(process.stderr.decode(errors='replace'))
        index = len(commands) + 1
        entry = {'arguments': list(arguments), 'command': shlex.join(command),
                 'exit_status': process.returncode, 'stdout': digest(process.stdout)}
        commands.append(entry)
        if destination is not None:
            (destination / f'{index:02d}-stdout.txt').write_bytes(process.stdout)
            (destination / f'{index:02d}-stderr.txt').write_bytes(process.stderr)
        return process.stdout
    summaries = []
    for subject_id in pilot.subject_ids:
        document = pilot.subject(subject_id)
        api = document.to_dict()
        stdout = cli('subject', subject_id, '--json')
        if stdout != document.to_json().encode():
            raise RuntimeError('individual public API/CLI canonical output differs')
        candidate = json.loads(stdout)
        subject, card, authored = candidate['subject'], candidate['card_evidence'], candidate['authored_interpretation']
        # Mutating an independent decoded view must not change the validated owner.
        api['subject']['card_id'] = 'fictional:caller-mutation'
        if document.to_json().encode() != stdout:
            raise RuntimeError('candidate lost immutable ownership')
        if pilot.validate_candidate(candidate).to_json().encode() != stdout:
            raise RuntimeError('validated candidate changed canonical output')
        summaries.append({'subject_id': subject_id, 'candidate_id': candidate['candidate_id'],
            'card_id': subject['card_id'], 'card_name': card['card_identity']['name'],
            'mechanical_dossier_id': subject['mechanical_dossier_id'],
            'provider_record_id': card['source']['provider_record_id'],
            'source_row_index': card['source']['source_record_index'],
            'provider_record_content_identity': card['source']['record_content_identity'],
            'source_record_pointer': subject['source_record_pointer'],
            'source_field_identity': subject['source_field_identity'],
            'complete_oracle_field': subject['complete_field_value'],
            'selected_complete_passage': subject['selected_passage'],
            'retained_type_line': subject['type_line'], 'owner': subject['owner'],
            'ownership_and_context_limitations': subject['ownership_and_context_limitations'],
            'proposed_kind': authored['proposed_kind'],
            'proposed_classification': authored['proposed_classification'],
            'classification_evidence_refs': authored['classification_evidence_refs'],
            'criterion_matrix': [{'criterion_id': row['criterion_id'], 'state': row['state'],
                'evidence_refs': row['evidence_refs']} for row in authored['criteria']],
            'material_unresolved_criteria': candidate['material_unresolved_criteria'],
            'counterevidence': authored['counterevidence'],
            'missing_requirements': authored['missing_requirements'],
            'review': candidate['review'], 'execution_authority': candidate['execution_authority']})
    readable = cli('subject', 'basalt-monolith-untap')
    if readable.decode() != render(pilot.subject('basalt-monolith-untap')):
        raise RuntimeError('individual readable public API/CLI output differs')
    report = pilot.comparison()
    comparison = cli('compare', '--json')
    if comparison != report.to_json().encode() or cli('compare', '--json') != comparison:
        raise RuntimeError('canonical comparison API/CLI or deterministic replay differs')
    decoded = report.to_dict()
    decoded['candidates'][0]['review']['canonical_admission'] = True
    if report.to_json().encode() != comparison:
        raise RuntimeError('report lost immutable ownership')
    if cli('compare').decode() != render(report):
        raise RuntimeError('readable comparison API/CLI differs')
    checked = json.loads(cli('check'))
    if checked['check'] != 'EXACT_REPRODUCTION':
        raise RuntimeError('retained output manifest reproduction did not pass')
    unchanged()
    sample = pilot.subject(pilot.subject_ids[0]).to_dict()
    summary = {'plan_id': pilot.plan_id, 'report_id': report.to_dict()['report_id'],
        'six_exact_card_ids': [row[0] for row in CARD_BINDINGS],
        'subject_count': len(summaries), 'subjects': summaries,
        'source_observation_timestamp': sample['acquisition_binding']['source_timestamp'],
        'source_retrieval_timestamp': sample['acquisition_binding']['retrieved_at'],
        'retained_card_source_sha256': sample['acquisition_binding']['retained_source_sha256'],
        'cr_source_binding': sample['rules_evidence']['source_binding'],
        'rule_bindings': [{key: row[key] for key in ('package', 'package_id', 'projection_id')}
            | {'rule_reference': row['rule']['rule_reference'], 'rule_id': row['rule']['rule_id'],
               'source_anchor': row['rule']['source_anchor']} for row in sample['rules_evidence']['rules']],
        'separately_bound_current_dependency_reviews': [
            {key: row[key] for key in ('package', 'package_id', 'record', 'review_id', 'schema_version', 'identity_domain')}
            for row in sample['rules_evidence']['current_dependency_reviews']],
        'bounded_selected_evidence_file_count': len(original),
        'bounded_selected_evidence_bytes_unchanged': True,
        'candidate_and_report_independent_views': True, 'deterministic_comparison_replay': True,
        'individual_api_cli_canonical_parity': True, 'comparison_api_cli_canonical_parity': True,
        'readable_api_cli_parity': True, 'explicit_retained_reproduction_check': checked,
        'commands': commands, 'execution_authority': 'BLOCKED',
        'semantic_review_status': 'PENDING_NOT_ESTABLISHED'}
    raw = canonical(summary)
    if destination is not None:
        (destination / 'summary.json').write_bytes(raw)
    sys.stdout.buffer.write(raw)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
