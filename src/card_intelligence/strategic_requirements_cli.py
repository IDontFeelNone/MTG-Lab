"""Structured read-only requirements inspection; no strategic evaluation."""
import argparse
import json
from pathlib import Path
import sys

from card_rules_pilot import contract as c, mana_scenario_policy as hp
from . import strategic_context as inputs
from .strategic_requirements import load_strategic_requirements, render_requirements


def parser():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('catalog-root','mechanical-root','review-root','cohort-root','decision-root'):
        p.add_argument('--'+name,type=Path,required=True)
    for name in ('profile-id','query-snapshot-id','plan-id','decision-id'):
        p.add_argument('--expected-'+name,required=True)
    p.add_argument('--json',action='store_true')
    commands=p.add_subparsers(dest='command',required=True)
    for name in ('requirements','missing','provenance','requirement','check','validate','detail'):
        q=commands.add_parser(name)
        if name in ('validate','detail'): q.add_argument('file',type=Path)
        if name in ('check','validate','detail'): continue
        q.add_argument('family')
        if name=='requirement':q.add_argument('requirement_id')
        q.add_argument('--context',type=Path)
        q.add_argument('--format-label',action='append',default=[])
        q.add_argument('--objective',action='append',default=[])
        q.add_argument('--deck-colors',action='append',default=[])
        q.add_argument('--alternative',nargs=2,action='append',default=[],metavar=('NAMESPACE','CARD_UUID'))
        q.add_argument('--lead',nargs=2,action='append',default=[],metavar=('CATEGORY','OPAQUE_REFERENCE'))
        q.add_argument('--swamp-count',action='append',default=[])
        q.add_argument('--commander-colors',action='append',default=[])
        q.add_argument('--namespace')
        q.add_argument('--card-id',action='append',default=[])
    return p


def _context(args):
    names=('format_label','objective','deck_colors','alternative','lead','swamp_count','commander_colors')
    if args.context is not None:
        if any(getattr(args,n) for n in names):raise inputs.ContextError('context file and context options cannot be combined')
        return inputs.validate_context(c.read_json(args.context,limit=inputs.LIMIT)).to_dict()
    declarations=[]
    for value in args.format_label:declarations.append(dict(dimension='format_label',value=value))
    for value in args.objective:declarations.append(dict(dimension='deck_objective',value=value))
    for value in args.deck_colors:declarations.append(dict(dimension='deck_color_requirements',value=list(value)))
    if args.alternative:
        declarations.append(dict(dimension='alternatives',value=[dict(namespace=n,card_id=i) for n,i in args.alternative]))
    hypothetical=[]
    for text in args.swamp_count:
        if len(text)>7 or not text.isascii() or not text.isdigit() or str(int(text))!=text:
            raise inputs.ContextError('canonical bounded nonnegative integer option required')
        hypothetical.append(dict(dimension='controlled_swamp_count',value=int(text)))
    for text in args.commander_colors:hypothetical.append(dict(dimension='commander_color_identity',value=list(text)))
    return inputs.make_context(declarations,hypothetical=hp.make_scenario(hypothetical).to_dict(),
        leads=[dict(category=k,reference=v) for k,v in args.lead]).to_dict()


def main(argv=None):
    args=parser().parse_args(argv)
    try:
        context=None if args.command in ('check','validate','detail') else _context(args)
        consumer=load_strategic_requirements(**{name:getattr(args,name) for name in (
            'catalog_root','mechanical_root','review_root','cohort_root','decision_root',
            'expected_profile_id','expected_query_snapshot_id','expected_plan_id','expected_decision_id')})
        if getattr(args,'namespace',None) is not None or getattr(args,'card_id',[]):
            consumer.for_cards(args.namespace,args.card_id,args.family,context)
        if args.command=='check':doc=consumer.check()
        elif args.command=='validate':
            with args.file.open('rb') as stream:doc=consumer.parse_report(stream.read(65537))
        elif args.command=='detail':doc=consumer.detailed(c.read_json(args.file,limit=8192))
        elif args.command=='requirement':doc=consumer.requirement(args.family,args.requirement_id,context)
        else:doc=getattr(consumer,args.command)(args.family,context)
        sys.stdout.write(doc.to_json() if args.json or args.command=='detail' else render_requirements(doc))
        return 3 if doc.to_dict().get('request_state')=='CONFLICTING' else 0
    except (ValueError, OSError, KeyError, TypeError) as error:
        sys.stderr.write(json.dumps(dict(code=getattr(error,'code','INPUT_OR_EVIDENCE_REJECTED'),message=str(error)),sort_keys=True)+'\n')
        return 2


if __name__=='__main__':raise SystemExit(main())
