"""Read-only bounded behavior explanations over retained pending interpretations."""
import argparse
from pathlib import Path
import sys


def parser():
    result = argparse.ArgumentParser(description=__doc__)
    result.add_argument('--review-root', type=Path, required=True)
    commands = result.add_subparsers(dest='command', required=True)
    for name in ('compare', 'subject', 'priority', 'check'):
        command = commands.add_parser(name)
        for root in ('catalog-root', 'mechanical-root', 'plan'):
            command.add_argument('--' + root, type=Path, required=True)
        command.add_argument('--successor-root', type=Path)
        for identity in ('profile-id', 'query-snapshot-id', 'plan-id'):
            command.add_argument('--expected-' + identity, required=True)
        command.add_argument('--json', action='store_true')
        if name in ('subject', 'priority'):
            command.add_argument('subject_id')
        if name == 'priority':
            command.add_argument('--prior-priority', choices=('true', 'false', 'unknown'), required=True,
                help='explicitly assumed hypothetical premise, never a real game observation')
    return result


def main(argv=None):
    entry = parser()
    args = entry.parse_args(argv)
    try:
        from .behavior import load_behavior, render_behavior
        context = load_behavior(catalog_root=args.catalog_root,
            mechanical_root=args.mechanical_root, review_root=args.review_root,
            plan_path=args.plan, successor_root=args.successor_root,
            expected_profile_id=args.expected_profile_id,
            expected_query_snapshot_id=args.expected_query_snapshot_id,
            expected_plan_id=args.expected_plan_id)
        if args.command == 'subject':
            document = context.subject(args.subject_id)
        elif args.command == 'priority':
            document = context.priority(args.subject_id, args.prior_priority)
        elif args.command == 'compare':
            document = context.comparison()
        else:
            document = context.check()
        sys.stdout.write(document.to_json() if args.json else render_behavior(document))
    except (ValueError, OSError, KeyError, TypeError) as error:
        entry.exit(2, 'bounded mana behavior rejected: ' + str(error) + '\n')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
