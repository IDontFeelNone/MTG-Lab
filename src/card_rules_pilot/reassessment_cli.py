"""Explicit read-only successor inspection; historical pilot commands are unchanged."""
import argparse
from pathlib import Path
import sys

from .contract import canonical


def parser():
    result = argparse.ArgumentParser(description=__doc__)
    result.add_argument('--review-root', type=Path, required=True)
    commands = result.add_subparsers(dest='command', required=True)
    for name in ('subject', 'compare', 'check'):
        command = commands.add_parser(name)
        for root in ('catalog-root', 'mechanical-root', 'plan'):
            command.add_argument('--' + root, type=Path, required=True)
        for identity in ('profile-id', 'query-snapshot-id', 'plan-id'):
            command.add_argument('--expected-' + identity, required=True)
        command.add_argument('--successor-root', type=Path)
        command.add_argument('--json', action='store_true')
        if name == 'subject':
            command.add_argument('subject_id')
    fresh = commands.add_parser('verify-source', help='fresh reproduction using the external owner TXT')
    fresh.add_argument('--artifact', type=Path, required=True)
    fresh.add_argument('--json', action='store_true')
    build = commands.add_parser('build-source', help='explicit validated construction into a new empty directory')
    build.add_argument('--artifact', type=Path, required=True)
    build.add_argument('--output', type=Path, required=True)
    return result


def main(argv=None):
    entry = parser()
    args = entry.parse_args(argv)
    try:
        if args.command in ('verify-source', 'build-source'):
            from gameplay_rules.projection import mana_context_package as source
            if args.command == 'build-source':
                records = source.build_package(args.artifact, review_root=args.review_root)
                value = source.write_package(args.output, records, review_root=args.review_root)
            else:
                records = source.load_package(args.review_root / source.PACKAGE_NAME,
                                              review_root=args.review_root)
                value = source.verify_source(records, args.artifact, review_root=args.review_root)
            if hasattr(value, 'to_dict'):
                value = value.to_dict()
            sys.stdout.buffer.write(canonical(value))
        else:
            from .reassessment import load_reassessment, render_reassessment
            context = load_reassessment(catalog_root=args.catalog_root,
                mechanical_root=args.mechanical_root, review_root=args.review_root,
                plan_path=args.plan, expected_profile_id=args.expected_profile_id,
                expected_query_snapshot_id=args.expected_query_snapshot_id,
                expected_plan_id=args.expected_plan_id, successor_root=args.successor_root)
            document = (context.subject(args.subject_id) if args.command == 'subject'
                        else context.comparison() if args.command == 'compare' else context.check())
            sys.stdout.write(document.to_json() if args.json else render_reassessment(document))
    except (ValueError, OSError, KeyError, TypeError) as error:
        entry.exit(2, 'mana context reassessment rejected: ' + str(error) + '\n')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
