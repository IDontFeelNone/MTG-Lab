"""Demonstrate actual bounded behavior API/CLI parity without retaining records."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shlex
import subprocess
import sys
import time

from card_rules_pilot.behavior import load_behavior, render_behavior
from card_rules_pilot.contract import canonical
from card_rules_pilot_demo import _snapshot

ROOT = Path(__file__).resolve().parents[1]
SUBJECTS = ('sol-ring-tap', 'basalt-monolith-tap', 'basalt-monolith-untap',
            'deathrite-shaman-first', 'dark-ritual-spell', 'mana-flare-trigger',
            'pitiless-plunderer-host-trigger')


def main(argv=None):
    started = time.monotonic()
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('catalog-root', 'mechanical-root', 'review-root', 'plan', 'successor-root'):
        parser.add_argument('--' + name, type=Path, required=True)
    for name in ('profile-id', 'query-snapshot-id', 'plan-id'):
        parser.add_argument('--expected-' + name, required=True)
    args = parser.parse_args(argv)

    def snapshot():
        selected = _snapshot(args.catalog_root, args.mechanical_root, args.review_root, args.plan)
        directories = (args.successor_root,
            args.review_root / 'gameplay-rules-mana-classification-source-context',
            args.review_root / 'gameplay-rules-casting-stage-family-completion')
        paths = []
        for directory in directories:
            entries = list(directory.iterdir())
            if len(entries) > 20 or any(not p.is_file() or p.is_symlink() for p in entries):
                raise ValueError('bounded ordinary retained evidence files required')
            paths.extend(entries)
        profile_path = args.catalog_root / 'config/catalog_profiles/legacy-public-tier-a.json'
        profile = json.loads(profile_path.read_bytes())
        paths.extend(args.catalog_root / row['path'] for row in profile['files'])
        for path in paths:
            if any(p.is_symlink() for p in (path, *path.parents)) or path.stat().st_nlink != 1:
                raise ValueError('ordinary selected evidence file required')
            raw = path.read_bytes()
            selected[str(path)] = {'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}
        return selected

    before = snapshot()
    context = load_behavior(catalog_root=args.catalog_root,
        mechanical_root=args.mechanical_root, review_root=args.review_root,
        plan_path=args.plan, successor_root=args.successor_root,
        expected_profile_id=args.expected_profile_id,
        expected_query_snapshot_id=args.expected_query_snapshot_id,
        expected_plan_id=args.expected_plan_id)
    if tuple(context.subject_ids) != SUBJECTS:
        raise RuntimeError('exact seven-subject cohort required')
    command = [sys.executable, '-m', 'card_rules_pilot.behavior_cli',
               '--review-root', str(args.review_root)]
    common = []
    for name in ('catalog-root', 'mechanical-root', 'plan', 'successor-root',
                 'expected-profile-id', 'expected-query-snapshot-id', 'expected-plan-id'):
        common += ['--' + name, str(getattr(args, name.replace('-', '_')))]
    env = dict(os.environ, PYTHONPATH=str(ROOT / 'src'), PYTHONDONTWRITEBYTECODE='1')
    commands = []

    def cli(action, document, subject=None, premise=None, readable=False):
        suffix = [action, *common, *([subject] if subject else [])]
        if premise is not None:
            suffix += ['--prior-priority', premise]
        if not readable:
            suffix.append('--json')
        invoked = time.monotonic()
        actual_command = command + suffix
        result = subprocess.run(actual_command, cwd=ROOT, env=env, capture_output=True)
        if result.returncode:
            raise RuntimeError(result.stderr.decode())
        expected = render_behavior(document).encode() if readable else document.to_json().encode()
        if result.stdout != expected:
            raise RuntimeError('actual API/CLI output differs')
        if snapshot() != before:
            raise RuntimeError('read command changed selected evidence')
        commands.append({'command': shlex.join(actual_command), 'action': action,
            'subject': subject, 'prior_priority': premise, 'readable': readable,
            'exit_status': result.returncode, 'stdout_bytes': len(result.stdout),
            'elapsed_seconds': format(time.monotonic() - invoked, '.3f'),
            'stdout_sha256': hashlib.sha256(result.stdout).hexdigest()})

    comparison = context.comparison()
    cli('compare', comparison)
    individual = context.subject('basalt-monolith-untap')
    cli('subject', individual, 'basalt-monolith-untap', readable=True)
    triggered = context.subject('mana-flare-trigger')
    cli('subject', triggered, 'mana-flare-trigger')
    priority = []
    for premise in ('true', 'false', 'unknown'):
        document = context.priority('sol-ring-tap', premise)
        cli('priority', document, 'sol-ring-tap', premise)
        priority.append(document.to_dict())
    original = comparison.to_json()
    view = comparison.to_dict()
    view.clear()
    if comparison.to_json() != original or context.comparison().to_json() != original:
        raise RuntimeError('immutable independent deterministic views failed')
    context.validate_report(json.loads(original))
    sys.stdout.buffer.write(canonical({
        'demonstration': 'BOUNDED_MANA_BEHAVIOR_AND_PROCEDURE_REASONING',
        'comparison': comparison.to_dict(),
        'representative_readable': render_behavior(individual),
        'representative_triggered': triggered.to_dict(),
        'priority_hypotheticals': priority,
        'commands': commands, 'api_admissions': 1,
        'fresh_cli_invocations': len(commands),
        'elapsed_seconds': format(time.monotonic() - started, '.3f'),
        'selected_evidence_file_count': len(before),
        'selected_bytes_unchanged': snapshot() == before,
        'actual_api_cli_parity': True, 'immutable_independent_views': True}))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
