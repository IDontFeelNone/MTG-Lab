"""Read-only bounded land mana and utility reports over pending readings."""
import argparse
from pathlib import Path
import sys


COMPARISONS = ('mana-and-utility', 'damage-ownership', 'variable-output', 'color-context')


def parser():
    entry = argparse.ArgumentParser(description=__doc__)
    entry.add_argument('--review-root', type=Path, required=True)
    commands = entry.add_subparsers(dest='command', required=True)
    for name in ('overview', 'subject', 'compare', 'check'):
        command = commands.add_parser(name)
        for root in ('catalog-root', 'mechanical-root', 'cohort-root'):
            command.add_argument('--' + root, type=Path, required=True)
        for identity in ('profile-id', 'query-snapshot-id', 'plan-id'):
            command.add_argument('--expected-' + identity, required=True)
        command.add_argument('--json', action='store_true')
        if name == 'subject':
            command.add_argument('subject_id')
        elif name == 'compare':
            command.add_argument('comparison', choices=COMPARISONS)
    return entry


def main(argv=None):
    entry = parser()
    args = entry.parse_args(argv)
    try:
        from .land import load_lands, render_lands
        context = load_lands(catalog_root=args.catalog_root,
            mechanical_root=args.mechanical_root, review_root=args.review_root,
            cohort_root=args.cohort_root,
            expected_profile_id=args.expected_profile_id,
            expected_query_snapshot_id=args.expected_query_snapshot_id,
            expected_plan_id=args.expected_plan_id)
        if args.command == 'subject':
            document = context.subject(args.subject_id)
        elif args.command == 'compare':
            document = context.comparison(args.comparison)
        elif args.command == 'overview':
            document = context.overview()
        else:
            document = context.check()
        # Admission, bounded calculation and rendering complete before stdout.
        output = document.to_json() if args.json else render_lands(document)
        sys.stdout.write(output)
    except (ValueError, OSError, KeyError, TypeError) as error:
        entry.exit(2, 'bounded land mana intelligence rejected: ' + str(error) + '\n')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
