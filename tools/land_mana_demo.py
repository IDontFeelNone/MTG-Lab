"""Exercise the actual bounded land API/CLI; emit the demonstration to stdout."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shlex
import subprocess
import sys
import time

from card_rules_pilot.land import load_lands, render_lands
from card_rules_pilot.land_cli import COMPARISONS
from card_rules_pilot.contract import canonical
from card_rules_pilot_demo import _snapshot
from repository.legacy_profile import MAX_BYTES as CATALOG_FILE_LIMIT

ROOT = Path(__file__).resolve().parents[1]
SUBJECTS = ('snow-wastes-mana', 'port-mana', 'port-utility', 'city-mana',
    'city-damage-trigger', 'citadel-colorless', 'citadel-color-choice',
    'coffers-mana', 'tower-mana')


def main(argv=None):
    started = time.monotonic()
    entry = argparse.ArgumentParser(description=__doc__)
    for name in ('catalog-root', 'mechanical-root', 'review-root', 'cohort-root'):
        entry.add_argument('--' + name, type=Path, required=True)
    for name in ('profile-id', 'query-snapshot-id', 'plan-id'):
        entry.add_argument('--expected-' + name, required=True)
    args = entry.parse_args(argv)

    def snapshot():
        selected = _snapshot(args.catalog_root, args.mechanical_root,
            args.review_root, args.cohort_root / 'plan.json')
        profile_path = args.catalog_root / 'config/catalog_profiles/legacy-public-tier-a.json'
        with profile_path.open('rb') as stream:
            profile_raw = stream.read(1_048_577)
        if len(profile_raw) > 1_048_576:
            raise ValueError('bounded catalog profile required')
        profile = json.loads(profile_raw)
        if type(profile.get('files')) is not list or len(profile['files']) > 2_000:
            raise ValueError('bounded catalog file selection required')
        paths = []
        catalog_bindings = {}
        for row in profile['files']:
            path = args.catalog_root / row['path']
            length = row['byte_length']
            if type(length) is not int or not 0 <= length <= CATALOG_FILE_LIMIT:
                raise ValueError('owning catalog file byte bound required')
            catalog_bindings[path] = {'bytes': length, 'sha256': row['sha256']}
            paths.append(path)
        for name in ('gameplay-rules-mana-classification-source-context',
                     'gameplay-rules-casting-stage-family-completion'):
            directory = args.review_root / name
            entries = list(directory.iterdir())
            if len(entries) > 20 or any(not path.is_file() for path in entries):
                raise ValueError('bounded selected evidence directory required')
            paths.extend(entries)
        for path in paths:
            if (any(parent.is_symlink() for parent in (path, *path.parents))
                    or path.stat().st_nlink != 1):
                raise ValueError('ordinary selected evidence file required')
            # Catalog attachment owns its file bounds. Stream opaque bytes
            # against that retained binding without imposing a report/input
            # bound on the catalog's complete canonical state file.
            expected = catalog_bindings.get(path)
            limit = expected['bytes'] if expected is not None else 3_000_000
            digest, length = hashlib.sha256(), 0
            with path.open('rb') as stream:
                while True:
                    chunk = stream.read(min(65_536, limit + 1 - length))
                    if not chunk:
                        break
                    length += len(chunk)
                    if length > limit:
                        raise ValueError('owning selected evidence byte bound exceeded')
                    digest.update(chunk)
            actual = {'bytes': length, 'sha256': digest.hexdigest()}
            if expected is not None and actual != expected:
                raise ValueError('current catalog file differs from declared profile binding')
            selected[str(path)] = actual
        return selected

    before = snapshot()
    admission_started = time.monotonic()
    context = load_lands(catalog_root=args.catalog_root,
        mechanical_root=args.mechanical_root, review_root=args.review_root,
        cohort_root=args.cohort_root,
        expected_profile_id=args.expected_profile_id,
        expected_query_snapshot_id=args.expected_query_snapshot_id,
        expected_plan_id=args.expected_plan_id)
    admission_seconds = time.monotonic() - admission_started
    if tuple(context.subject_ids) != SUBJECTS:
        raise RuntimeError('exact nine-subject cohort required')
    questions_started = time.monotonic()
    subjects = [context.subject(subject) for subject in SUBJECTS]
    comparisons = [context.comparison(name) for name in COMPARISONS]
    overview = context.overview()
    integrity = context.check()
    question_seconds = time.monotonic() - questions_started
    repeated_started = time.monotonic()
    for original, subject in zip(subjects, SUBJECTS):
        if original.to_json() != context.subject(subject).to_json():
            raise RuntimeError('repeated subject result differs')
    for original, name in zip(comparisons, COMPARISONS):
        if original.to_json() != context.comparison(name).to_json():
            raise RuntimeError('repeated comparison result differs')
    repeated_seconds = time.monotonic() - repeated_started
    for document in [overview, integrity, *subjects, *comparisons]:
        raw = document.to_json()
        view = document.to_dict()
        context.validate_report(view)
        view.clear()
        if document.to_json() != raw:
            raise RuntimeError('returned dictionary aliases private content')

    base = [sys.executable, '-m', 'card_rules_pilot.land_cli',
        '--review-root', str(args.review_root)]
    common = []
    for name in ('catalog-root', 'mechanical-root', 'cohort-root',
                 'expected-profile-id', 'expected-query-snapshot-id', 'expected-plan-id'):
        common.extend(['--' + name, str(getattr(args, name.replace('-', '_')))])
    env = dict(os.environ, PYTHONPATH=str(ROOT / 'src'), PYTHONDONTWRITEBYTECODE='1')
    commands = []

    def cli(action, document, selection=None, readable=False):
        command = [*base, action, *common]
        if selection is not None:
            command.append(selection)
        if not readable:
            command.append('--json')
        invoked = time.monotonic()
        print('$ ' + shlex.join(command), file=sys.stderr, flush=True)
        actual = subprocess.run(command, cwd=ROOT, env=env, capture_output=True)
        if actual.returncode:
            raise RuntimeError(actual.stderr.decode(errors='replace'))
        expected = render_lands(document).encode() if readable else document.to_json().encode()
        if actual.stdout != expected:
            raise RuntimeError('actual canonical/readable API/CLI output differs')
        if snapshot() != before:
            raise RuntimeError('read command changed retained evidence')
        commands.append({'command': shlex.join(command), 'action': action,
            'selection': selection, 'readable': readable,
            'exit_status': actual.returncode, 'stdout_bytes': len(actual.stdout),
            'stdout_sha256': hashlib.sha256(actual.stdout).hexdigest(),
            'elapsed_seconds': format(time.monotonic() - invoked, '.3f')})

    cli('overview', overview)
    cli('check', integrity)
    cli('subject', subjects[2], SUBJECTS[2], readable=True)
    for name, document in zip(COMPARISONS, comparisons):
        cli('compare', document, name)
        cli('compare', document, name, readable=True)
    if snapshot() != before:
        raise RuntimeError('demonstration changed retained evidence')
    transcript = {
        'demonstration': 'BOUNDED_LAND_MANA_AND_UTILITY_INTELLIGENCE',
        'overview': overview.to_dict(),
        # The aggregate carries complete candidates, all nine assessments,
        # four comparisons and shared evidence once. Individual public views
        # were validated above and have independently reproducible identities.
        'individual_reports': [{'subject_id': sid,
            'report_id': document.to_dict()['report_id'],
            'bytes': len(document.to_json().encode()),
            'sha256': hashlib.sha256(document.to_json().encode()).hexdigest()}
            for sid, document in zip(SUBJECTS, subjects)],
        'comparison_reports': [{'comparison': name,
            'report_id': document.to_dict()['report_id'],
            'bytes': len(document.to_json().encode()),
            'sha256': hashlib.sha256(document.to_json().encode()).hexdigest()}
            for name, document in zip(COMPARISONS, comparisons)],
        'integrity_report_id': integrity.to_dict()['report_id'], 'commands': commands,
        'api_admissions': 1, 'fresh_cli_invocations': len(commands),
        'cold_admission_seconds': format(admission_seconds, '.3f'),
        'all_questions_seconds': format(question_seconds, '.3f'),
        'repeated_nine_subjects_four_comparisons_seconds': format(repeated_seconds, '.3f'),
        'complete_overview_bytes': len(overview.to_json().encode()),
        'selected_evidence_file_count': len(before), 'selected_bytes_unchanged': True,
        'actual_canonical_readable_api_cli_parity': True,
        'immutable_independent_views': True,
        'elapsed_seconds': format(time.monotonic() - started, '.3f')}
    sys.stdout.buffer.write(canonical(transcript))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
