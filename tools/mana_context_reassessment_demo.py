"""Reproduce the source-backed successor through actual read-only API and CLI."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time

from card_rules_pilot.contract import canonical
from card_rules_pilot.reassessment import load_reassessment, render_reassessment
from card_rules_pilot_demo import _snapshot
from gameplay_rules.projection.mana_context_package import PACKAGE_NAME

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
        for directory in (args.successor_root, args.review_root / PACKAGE_NAME):
            for path in directory.iterdir():
                if not path.is_file() or path.is_symlink():
                    raise ValueError('ordinary retained file required')
                raw = path.read_bytes()
                selected[str(path)] = {'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}
        return selected
    before = snapshot()
    context = load_reassessment(catalog_root=args.catalog_root,
        mechanical_root=args.mechanical_root, review_root=args.review_root,
        plan_path=args.plan, successor_root=args.successor_root,
        expected_profile_id=args.expected_profile_id,
        expected_query_snapshot_id=args.expected_query_snapshot_id, expected_plan_id=args.expected_plan_id)
    command = [sys.executable, '-m', 'card_rules_pilot.reassessment_cli',
               '--review-root', str(args.review_root)]
    common = []
    for name in ('catalog-root', 'mechanical-root', 'plan', 'successor-root',
                 'expected-profile-id', 'expected-query-snapshot-id', 'expected-plan-id'):
        common += ['--' + name, str(getattr(args, name.replace('-', '_')))]
    env = dict(os.environ, PYTHONPATH=str(ROOT / 'src'), PYTHONDONTWRITEBYTECODE='1')
    commands = []
    def cli(action, document, subject=None, readable=False):
        suffix = [action, *common, *([subject] if subject else []), *([] if readable else ['--json'])]
        invoked = time.monotonic()
        result = subprocess.run(command + suffix, cwd=ROOT, env=env, capture_output=True)
        if result.returncode:
            raise RuntimeError(result.stderr.decode())
        expected = render_reassessment(document).encode() if readable else document.to_json().encode()
        if result.stdout != expected:
            raise RuntimeError('actual API/CLI output differs')
        if snapshot() != before:
            raise RuntimeError('read command changed evidence')
        commands.append({'action': action, 'subject': subject, 'readable': readable,
                         'exit_status': result.returncode, 'stdout_bytes': len(result.stdout),
                         'elapsed_seconds': format(time.monotonic() - invoked, '.3f'),
                         'stdout_sha256': hashlib.sha256(result.stdout).hexdigest()})
    for subject in SUBJECTS:
        doc = context.subject(subject)
        cli('subject', doc, subject)
        context.validate_report(doc.to_dict())
    comparison = context.comparison()
    cli('compare', comparison)
    cli('compare', comparison, readable=True)
    cli('check', context.check())
    original = comparison.to_json()
    view = comparison.to_dict()
    view.clear()
    if comparison.to_json() != original or context.comparison().to_json() != original:
        raise RuntimeError('immutable deterministic ownership failed')
    context.validate_report(json.loads(original))
    sys.stdout.buffer.write(canonical({'demonstration': 'MANA_CONTEXT_PENDING_REASSESSMENT',
        'comparison': comparison.to_dict(), 'commands': commands,
        'api_admissions': 1, 'fresh_cli_invocations': len(commands),
        'elapsed_seconds': format(time.monotonic() - started, '.3f'),
        'selected_evidence_file_count': len(before), 'selected_bytes_unchanged': snapshot() == before,
        'actual_api_cli_parity': True, 'immutable_deterministic_views': True}))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
