"""Read-only supplied-evidence packet inspection; no approval action."""
import argparse
import json
from pathlib import Path
import sys

from card_rules_pilot import contract as c
from . import context_review_input as inputs
from .context_review import load_context_evidence_review, render_review


def parser():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('catalog-root','mechanical-root','review-root','cohort-root','decision-root'):
        p.add_argument('--'+name,type=Path,required=True)
    for name in ('profile-id','query-snapshot-id','plan-id','decision-id'):
        p.add_argument('--expected-'+name,required=True)
    p.add_argument('--json',action='store_true')
    commands=p.add_subparsers(dest='command',required=True)
    for name in ('create','validate-packet','review','candidates','candidate','provenance','conflicts','missing','check','validate','detail'):
        q=commands.add_parser(name)
        q.add_argument('file',type=Path,help='canonical candidate input list, packet, or detailed reference')
        if name=='candidate': q.add_argument('candidate_id')
        if name=='validate': q.add_argument('report',type=Path)
    return p


def main(argv=None):
    args=parser().parse_args(argv)
    try:
        owner=load_context_evidence_review(**{name:getattr(args,name) for name in (
            'catalog_root','mechanical_root','review_root','cohort_root','decision_root',
            'expected_profile_id','expected_query_snapshot_id','expected_plan_id','expected_decision_id')})
        if args.command=='detail':
            doc=owner.detailed(c.read_json(args.file,limit=8192))
            # Detailed evidence is intentionally explicit JSON, separate from concise review rendering.
            sys.stdout.write(doc.to_json());return 0
        raw=c.read_json(args.file,limit=inputs.PACKET_LIMIT)
        if args.command=='create':
            if type(raw) is not list or len(raw)>inputs.MAX_CANDIDATES: raise inputs.ReviewInputError('bounded list of explicit candidate inputs required')
            doc=inputs.make_packet([inputs.make_candidate(**v).to_dict() for v in raw])
        elif args.command=='validate-packet': doc=inputs.validate_packet(raw)
        else:
            bound=owner.submit(raw)
            if args.command=='validate': doc=bound.validate_report(c.read_json(args.report,limit=65536))
            elif args.command=='candidate': doc=bound.candidate(args.candidate_id)
            else: doc=getattr(bound,dict(review='report').get(args.command,args.command))()
        if args.command in ('create','validate-packet'):
            if args.json: sys.stdout.write(doc.to_json())
            else:
                value=doc.to_dict()
                sys.stdout.write('Unverified review packet: '+value['packet_id']+'\nCandidates: '+str(len(value['candidates']))+'\nNo authentication, permission grant or approval.\n')
            return 0
        sys.stdout.write(doc.to_json() if args.json else render_review(doc))
        return 3 if any(s in doc.to_dict()['review_states'] for s in ('CONFLICTING','OUT_OF_SCOPE')) else 0
    except (ValueError,OSError,KeyError,TypeError) as error:
        sys.stderr.write(json.dumps(dict(status='REJECTED',code=getattr(error,'code','INVALID_SUPPLIED_EVIDENCE'),message=str(error)),sort_keys=True)+'\n')
        return 2


if __name__=='__main__': raise SystemExit(main())
