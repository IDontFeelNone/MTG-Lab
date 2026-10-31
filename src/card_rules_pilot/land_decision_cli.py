"""Read-only reports for the one recorded owner-supplied land decision."""
import argparse
from pathlib import Path
import sys


def parser():
    entry = argparse.ArgumentParser(description=__doc__)
    entry.add_argument('--review-root', type=Path, required=True)
    commands = entry.add_subparsers(dest='command', required=True)
    for name in ('summary', 'subject', 'check'):
        command = commands.add_parser(name)
        for root in ('catalog-root', 'mechanical-root', 'cohort-root', 'decision-root'):
            command.add_argument('--' + root, type=Path, required=True)
        for identity in ('profile-id', 'query-snapshot-id', 'plan-id', 'decision-id'):
            command.add_argument('--expected-' + identity, required=True)
        command.add_argument('--json', action='store_true')
        if name == 'subject':
            command.add_argument('subject_id')
    return entry


def main(argv=None):
    entry = parser()
    args = entry.parse_args(argv)
    try:
        from .land_decision import load_land_decision, render_land_decision
        consumer = load_land_decision(catalog_root=args.catalog_root,
            mechanical_root=args.mechanical_root, review_root=args.review_root,
            cohort_root=args.cohort_root, decision_root=args.decision_root,
            expected_profile_id=args.expected_profile_id,
            expected_query_snapshot_id=args.expected_query_snapshot_id,
            expected_plan_id=args.expected_plan_id,
            expected_decision_id=args.expected_decision_id)
        if args.command == 'subject':
            document = consumer.subject(args.subject_id)
        elif args.command == 'check':
            document = consumer.check()
        else:
            document = consumer.summary()
        output = document.to_json() if args.json else render_land_decision(document)
        # Complete validation/rendering precede output; no implicit file writer.
        sys.stdout.write(output)
    except (ValueError, OSError, KeyError, TypeError) as error:
        entry.exit(2, 'bounded land semantic decision rejected: ' + str(error) + '\n')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
