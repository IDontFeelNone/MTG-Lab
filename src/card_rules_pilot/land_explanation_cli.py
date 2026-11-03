"""Closed read-only accepted land explanations; no natural-language inference."""
import argparse
from pathlib import Path
import sys


def parser():
    entry = argparse.ArgumentParser(description=__doc__)
    entry.add_argument('--review-root', type=Path, required=True)
    commands = entry.add_subparsers(dest='command', required=True)
    for name in ('subject', 'card', 'compare', 'provenance', 'check'):
        command = commands.add_parser(name)
        for root in ('catalog-root', 'mechanical-root', 'cohort-root', 'decision-root'):
            command.add_argument('--' + root, type=Path, required=True)
        for identity in ('profile-id', 'query-snapshot-id', 'plan-id', 'decision-id'):
            command.add_argument('--expected-' + identity, required=True)
        command.add_argument('--json', action='store_true')
        if name != 'check':
            command.add_argument('selector')
    return entry


def main(argv=None):
    entry = parser()
    args = entry.parse_args(argv)
    try:
        from .land_explanation import load_land_explanations, render_land_explanation
        consumer = load_land_explanations(catalog_root=args.catalog_root,
            mechanical_root=args.mechanical_root, review_root=args.review_root,
            cohort_root=args.cohort_root, decision_root=args.decision_root,
            expected_profile_id=args.expected_profile_id,
            expected_query_snapshot_id=args.expected_query_snapshot_id,
            expected_plan_id=args.expected_plan_id,
            expected_decision_id=args.expected_decision_id)
        if args.command == 'subject':
            document = consumer.explain_subject(args.selector)
        elif args.command == 'card':
            document = consumer.explain_card(args.selector)
        elif args.command == 'compare':
            document = consumer.compare(args.selector)
        elif args.command == 'provenance':
            document = consumer.provenance(args.selector)
        else:
            document = consumer.check()
        output = document.to_json() if args.json else render_land_explanation(document)
        sys.stdout.write(output)
    except (ValueError, OSError, KeyError, TypeError) as error:
        entry.exit(2, 'accepted land explanation rejected: ' + str(error) + '\n')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
