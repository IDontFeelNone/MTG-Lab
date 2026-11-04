"""Read-only exact-ID land evidence overlay; no name or natural-language routing."""
import argparse
import json
from pathlib import Path
import sys

from card_rules_pilot import mana_scenario_policy as hp
from .land_overlay import load_land_overlay, render_overlay, OverlayError, JOIN_NAMES


def parser():
    entry = argparse.ArgumentParser(description=__doc__)
    for root in ('catalog-root','mechanical-root','review-root','cohort-root','decision-root'):
        entry.add_argument('--' + root, type=Path, required=True)
    for identity in ('profile-id','query-snapshot-id','plan-id','decision-id'):
        entry.add_argument('--expected-' + identity, required=True)
    entry.add_argument('--json', action='store_true')
    commands = entry.add_subparsers(dest='command', required=True)
    for name in ('card','compare','provenance','identity','check','detail','validate'):
        command = commands.add_parser(name)
        if name in ('card','provenance','identity'):
            command.add_argument('--namespace', required=True)
            command.add_argument('--card-id', required=True)
        if name == 'identity': command.add_argument('--join', choices=JOIN_NAMES, required=True)
        if name == 'compare': command.add_argument('group')
        if name in ('card','compare'):
            command.add_argument('--swamp-count', action='append', default=[])
            command.add_argument('--colors', action='append', default=[], help='Canonical WUBRG subset; explicit empty string allowed')
        if name in ('detail','validate'): command.add_argument('file', type=Path)
    return entry


def main(argv=None):
    entry = parser(); args = entry.parse_args(argv)
    try:
        assumptions = []
        for text in getattr(args,'swamp_count',[]):
            if len(text) > 7 or not text.isascii() or not text.isdigit() or str(int(text)) != text:
                raise OverlayError('UNSUPPORTED_CONTEXT','canonical nonnegative bounded integer required')
            assumptions.append(dict(dimension='controlled_swamp_count',value=int(text)))
        for text in getattr(args,'colors',[]):
            assumptions.append(dict(dimension='commander_color_identity',value=list(text)))
        scenario = hp.make_scenario(assumptions).to_dict()
        overlay = load_land_overlay(**{name:getattr(args,name) for name in (
            'catalog_root','mechanical_root','review_root','cohort_root','decision_root',
            'expected_profile_id','expected_query_snapshot_id','expected_plan_id','expected_decision_id')})
        if args.command == 'card': doc = overlay.card(args.namespace,args.card_id,scenario)
        elif args.command == 'compare': doc = overlay.compare(args.group,scenario)
        elif args.command == 'provenance': doc = overlay.provenance(args.namespace,args.card_id)
        elif args.command == 'identity': doc = overlay.identity(args.namespace,args.card_id,args.join)
        elif args.command == 'check': doc = overlay.check()
        elif args.command == 'validate':
            with args.file.open('rb') as stream: doc = overlay.parse_report(stream.read(65537))
        else:
            from card_rules_pilot import contract as c
            doc = overlay.detailed(c.read_json(args.file,limit=8192))
        if args.command == 'detail':
            # Detailed mode is explicitly selected, never appended to readable.
            sys.stdout.write(doc.to_json())
        else:
            sys.stdout.write(doc.to_json() if args.json else render_overlay(doc))
        value = doc.to_dict()
        if value.get('state') == 'CONFLICTING': return 3
        if value.get('identity_status') in ('IDENTITY_NOT_ESTABLISHED','NOT_IN_SUPPORTED_COHORT'): return 4
        return 0
    except (ValueError, OSError, KeyError, TypeError) as error:
        code = getattr(error,'code','EVIDENCE_OR_INPUT_REJECTED')
        sys.stderr.write(json.dumps(dict(code=code,message=str(error)),sort_keys=True) + '\n')
        return 2


if __name__ == '__main__': raise SystemExit(main())
