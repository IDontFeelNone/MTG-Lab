"""Closed read-only explicit hypothetical mana scenarios."""
import argparse
from pathlib import Path
import sys
from . import mana_scenario_policy as policy


def parser():
    entry = argparse.ArgumentParser(description=__doc__)
    entry.add_argument('--review-root', type=Path, required=True)
    commands = entry.add_subparsers(dest='command', required=True)
    for name in ('subject', 'compare', 'provenance', 'check'):
        command = commands.add_parser(name)
        for root in ('catalog-root', 'mechanical-root', 'cohort-root', 'decision-root'):
            command.add_argument('--' + root, type=Path, required=True)
        for identity in ('profile-id', 'query-snapshot-id', 'plan-id', 'decision-id'):
            command.add_argument('--expected-' + identity, required=True)
        command.add_argument('--json', action='store_true')
        if name != 'check': command.add_argument('selector')
        if name in ('subject', 'compare'):
            command.add_argument('--swamp-count', action='append', default=[])
            command.add_argument('--colors', action='append', default=[], help='Canonical WUBRG subsequence; explicit empty string allowed')
    return entry


def main(argv=None):
    entry = parser(); args = entry.parse_args(argv)
    try:
        from .mana_scenario import load_mana_scenarios, render_mana_scenario
        assumptions = []
        for count in getattr(args, 'swamp_count', []):
            # Canonical integers only; bool, decimals, signs and whitespace reject.
            if not count.isascii() or not count.isdigit() or str(int(count)) != count:
                raise policy.UnsupportedScenario('UNSUPPORTED: canonical nonnegative integer option required')
            assumptions.append({'dimension': 'controlled_swamp_count', 'value': int(count)})
        for colors in getattr(args, 'colors', []):
            assumptions.append({'dimension': 'commander_color_identity', 'value': list(colors)})
        scenario = policy.make_scenario(assumptions).to_dict()
        consumer = load_mana_scenarios(**{name: getattr(args, name) for name in (
            'catalog_root', 'mechanical_root', 'review_root', 'cohort_root', 'decision_root',
            'expected_profile_id', 'expected_query_snapshot_id', 'expected_plan_id', 'expected_decision_id')})
        if args.command == 'subject': doc = consumer.evaluate(args.selector, scenario)
        elif args.command == 'compare': doc = consumer.compare(args.selector, scenario)
        elif args.command == 'provenance': doc = consumer.provenance(args.selector)
        else: doc = consumer.check()
        sys.stdout.write(doc.to_json() if args.json else render_mana_scenario(doc))
        if doc.to_dict()['state'] == 'CONFLICTING': return 3
    except (ValueError, OSError, KeyError, TypeError) as error:
        entry.exit(2, 'hypothetical mana scenario rejected: ' + str(error) + '\n')
    return 0

if __name__ == '__main__': raise SystemExit(main())
