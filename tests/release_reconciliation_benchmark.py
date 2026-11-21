"""Bounded original-data scale demonstration, never a provider acquisition.

PYTHONPATH=src python tests/release_reconciliation_benchmark.py --directory /tmp/reconciliation-benchmark
"""
import argparse
import hashlib
import json
from pathlib import Path

from providers.mtgjson.reconciliation import reconcile_release, ReconciliationError


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--directory',type=Path,required=True)
    parser.add_argument('--sets',type=int,default=40)
    parser.add_argument('--rows-per-set',type=int,default=500)
    args=parser.parse_args()
    if not (1<=args.sets<=1000 and 1<=args.rows_per_set<=1000 and args.sets*args.rows_per_set<=100000):
        parser.error('bounded original fixture sizes required')
    args.directory.mkdir(parents=True,exist_ok=False)
    source=args.directory/'original-source.json'
    with source.open('w') as stream:
        stream.write('{"meta":{"version":"5.2.1","date":"2026-11-20"},"data":{')
        for partition in range(args.sets):
            code='BENCH'+str(partition)
            cards=[dict(uuid='original-print-'+str(partition)+'-'+str(row),
                name='Original Benchmark Identity '+str(row),number=str(row),layout='normal',
                manaCost='{2}',colors=[],finishes=['nonfoil'],
                identifiers={'scryfallOracleId':'original-card-'+str(row)})
                for row in range(args.rows_per_set)]
            if partition:stream.write(',')
            stream.write(json.dumps(code)+':'+json.dumps(dict(code=code,name='Original Benchmark '+str(partition),cards=cards)))
        stream.write('}}')
    with source.open('rb') as stream:
        digest=hashlib.file_digest(stream,'sha256').hexdigest()
    release=dict(provider='MTGJSON',release_id='original-benchmark-v1',version='5.2.1',
        date='2026-11-20',artifact_sha256=digest,provenance_reference='original-benchmark-authorship',
        notice_reference='project-authored-no-external-data')
    def original_only(binding):
        return binding['release']==release and binding['whole_artifact_read'] and not binding['public_export']
    try:
        report=reconcile_release(source,args.directory/'private',release,authorize_source=original_only)
        measurement=json.loads((args.directory/'private/last-run.json').read_text())
        result=dict(status=report['status'],report_id=report['report_id'],source_sha256=digest,
            sets=args.sets,total_rows=report['total_source_rows'],cards=report['unique_supported_card_identities'],
            printings=report['distinct_printing_identities'],measurement=measurement,
            disk_bytes=sum(x.stat().st_size for x in args.directory.rglob('*') if x.is_file()),
            source_kind='ORIGINAL_PROJECT_AUTHORED_FIXTURE',real_catalog_demonstration='BLOCKED')
    except ReconciliationError as error:
        result=error.as_dict()
    (args.directory/'receipt.json').write_text(json.dumps(result,sort_keys=True,indent=2)+'\n')
    print(json.dumps(result,sort_keys=True))
    return 0 if result['status']=='CANDIDATES_PREPARED' else 2


if __name__=='__main__':raise SystemExit(main())
