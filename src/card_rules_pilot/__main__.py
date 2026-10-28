"""Read-only commands for the exact pending Card–rules pilot."""
import argparse
from pathlib import Path
import sys

from .contract import canonical, exact, read_json, PLAN_LIMIT
from .pilot import load_pilot, render


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('catalog-root', 'mechanical-root', 'review-root', 'plan'):
        parser.add_argument('--' + name, type=Path, required=True)
    for name in ('profile-id', 'query-snapshot-id', 'plan-id'):
        parser.add_argument('--expected-' + name, required=True)
    commands = parser.add_subparsers(dest='command', required=True)
    subject = commands.add_parser('subject', help='one exact local review subject')
    subject.add_argument('subject_id')
    subject.add_argument('--json', action='store_true')
    compare = commands.add_parser('compare', help='all seven pending proposals')
    compare.add_argument('--json', action='store_true')
    analyze = commands.add_parser('analyze', help='computed conditional evidence analysis for one subject')
    analyze.add_argument('subject_id')
    analyze.add_argument('--json', action='store_true')
    for name in ('analyze-all', 'review-impact'):
        derived = commands.add_parser(name, help='bounded computed pending-review reasoning')
        derived.add_argument('--json', action='store_true')
    commands.add_parser('check', help='explicit read-only byte reproduction check of retained candidates/report')
    args = parser.parse_args(argv)
    try:
        pilot = load_pilot(catalog_root=args.catalog_root,
            mechanical_root=args.mechanical_root, review_root=args.review_root,
            plan_path=args.plan, expected_profile_id=args.expected_profile_id,
            expected_query_snapshot_id=args.expected_query_snapshot_id,
            expected_plan_id=args.expected_plan_id)
        if args.command in ('analyze', 'analyze-all', 'review-impact'):
            from .reasoning import _from_pilot, render_reasoning
            reasoning = _from_pilot(pilot)
            document = (reasoning.subject(args.subject_id) if args.command == 'analyze'
                else reasoning.comparison() if args.command == 'analyze-all'
                else reasoning.review_impact())
            sys.stdout.write(document.to_json() if args.json else render_reasoning(document))
        elif args.command == 'check':
            report = pilot.comparison()
            directory = args.plan.parent
            manifest = pilot.reproduction_manifest()
            exact(read_json(directory / 'manifest.json', limit=PLAN_LIMIT), manifest, limit=PLAN_LIMIT)
            sys.stdout.buffer.write(canonical({'check': 'EXACT_REPRODUCTION',
                'plan_id': pilot.plan_id, 'report_id': report.to_dict()['report_id'],
                'manifest_id': manifest['manifest_id'],
                'subjects': 7, 'review_status': 'requires_review', 'execution_authority': 'BLOCKED'}))
        else:
            document = pilot.subject(args.subject_id) if args.command == 'subject' else pilot.comparison()
            sys.stdout.write(document.to_json() if args.json else render(document))
    except (ValueError, OSError, KeyError, TypeError) as error:
        parser.exit(2, 'card-rules pilot rejected: ' + str(error) + '\n')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
