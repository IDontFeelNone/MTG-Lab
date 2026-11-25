"""Original authored sources only: explicit Standard envelope and exact recovery."""
from copy import deepcopy
from dataclasses import asdict, replace
import gzip
import hashlib
import io
import json
from pathlib import Path
import sqlite3
import sys
import tempfile
import types
import unittest
from unittest.mock import patch

from providers.mtgjson import reconciliation as implementation
from providers.mtgjson.private_activation import activate_private_release, plan_private_activation
from providers.mtgjson.private_import import import_private_release
from providers.mtgjson.private_policy import (PrivateResearchProfile, SourceUseBasis, SourcePolicyError,
    LIMITED_OPERATIONS, OPERATIONS, RETENTION, ORACLE_RETENTION, ORACLE_OPERATION, FACTUAL_FIELDS,
    canonical, digest)
from providers.mtgjson.reconciliation import StandardExportContract, ReconciliationError, ReconciliationLimits
from providers.mtgjson.factual_retention import verify_factual_publication

ROOT = Path(__file__).resolve().parents[1]
CANARY = 'ORIGINAL_EXCLUDED_ENVELOPE_FIXTURE_PROSE_4a71'
NOTICE = b'Original MTG Lab synthetic diagnostic records, not real Magic evidence.\n'
AUTHORSHIP = b'MTG Lab independently authored this synthetic envelope, its metadata and every record.\n'


def predecessor_worker(connection, source, root, binding, limits, stop_after):
    """Execute the exact reconstructed baseline worker/parser in the real child."""
    from standard_envelope_preservation import preceding_bytes
    name = 'src/providers/mtgjson/reconciliation.py'
    raw = preceding_bytes(name, (ROOT/name).read_bytes())
    module_name = 'providers.mtgjson._standard_envelope_predecessor'
    module = types.ModuleType(module_name)
    module.__package__ = 'providers.mtgjson'
    module.__file__ = str(ROOT/name)
    sys.modules[module_name] = module
    exec(compile(raw, module.__file__, 'exec'), module.__dict__)
    module._worker(connection, source, root, binding, limits, stop_after)


class StandardEnvelopeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(dir='/tmp')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.source = self.root/'authored.json'
        self.notice = self.root/'notice.txt'
        self.provenance = self.root/'provenance.json'
        self.evidence = self.root/'authorship.txt'
        self.workspace = self.root/'candidates'
        self.meta = dict(version='5.3.0+original', date='2026-11-25')
        self.document = dict(meta=self.meta, data={})
        for i in range(22):
            code = 'Z'+str(i).zfill(2)
            family = i % 4
            row = dict(uuid=f'00000000-0000-0000-0000-{i+1:012d}',
                name=f'Original fixture resource {family}', number='1', layout='normal',
                colors=[], colorIdentity=[], manaCost='{1}', manaValue=1, type='Artifact',
                types=['Artifact'], language='English', rarity='common', finishes=['nonfoil'],
                identifiers=dict(scryfallOracleId=f'10000000-0000-0000-0000-{family+1:012d}',
                                 scryfallId=f'20000000-0000-0000-0000-{i+1:012d}'),
                text=CANARY, flavorText=CANARY, foreignData=[dict(text=CANARY)],
                rulings=[dict(text=CANARY)], purchaseUrls=dict(example=CANARY), artwork=CANARY)
            self.document['data'][code] = dict(code=code, name=f'Original fixture set {i}',
                releaseDate='2026-11-25', cards=[row], originalProse=CANARY)
        self.document['format_name'] = 'standard'
        self.prepare()

    def prepare(self, raw=None, *, mode='limited-retention', compressed=False):
        # Publisher ordering is meta, data, then format_name, not sorted root keys.
        if raw is None:
            raw = json.dumps(self.document, separators=(',', ':'), ensure_ascii=False).encode()
        if compressed:
            raw = gzip.compress(raw, mtime=0)
        self.source.write_bytes(raw)
        self.release = dict(provider='MTGJSON', release_id='original-standard-envelope-fixture',
            version=self.meta['version'], date=self.meta['date'], artifact_sha256=digest(raw),
            provenance_reference='original-envelope-provenance', notice_reference='original-envelope-notice')
        self.notice.write_bytes(NOTICE); self.evidence.write_bytes(AUTHORSHIP)
        self.plan = plan_private_activation(self.release, source_url='urn:mtglab:original:standard-envelope',
            acquired_at='2026-11-25T00:00:00Z', notice_sha256=digest(NOTICE), retention_mode=mode)
        facts = {k:self.release[k] for k in ('provider','release_id','version','date','artifact_sha256')}
        facts.update(source_url=self.plan['source_url'], acquired_at=self.plan['acquired_at'],
                     acquisition_method='MANUALLY_SUPPLIED')
        self.provenance.write_text(canonical(facts)+'\n')
        operations = LIMITED_OPERATIONS if mode == 'limited-retention' else OPERATIONS
        self.bases = (SourceUseBasis('original-envelope-authorship', digest(AUTHORSHIP),
            'PROJECT_AUTHORSHIP', 'COMPLETE_ARTIFACT', operations, 'SUPPORTED'),)
        self.profile = PrivateResearchProfile.for_release(self.release,
            provenance_sha256=digest(self.provenance.read_bytes()), notice_sha256=digest(NOTICE),
            bases=self.bases, internal_decision_reference='original-envelope-research',
            material='ORIGINAL_PROJECT_FIXTURE', retention_mode=mode)
        self.contract = StandardExportContract.for_profile(self.profile)
        for path in (self.source,self.notice,self.provenance,self.evidence): path.chmod(0o600)

    def run_import(self, *, contract=True, **kwargs):
        options = dict(source_contract=self.contract) if contract else {}
        return import_private_release(self.source,self.workspace,profile=self.profile,
            provenance=self.provenance,notice=self.notice,**options,**kwargs)

    def refusal(self, call, code=None):
        with self.assertRaises(ReconciliationError) as context: call()
        if code: self.assertEqual(context.exception.code,code)
        return context.exception

    def checkpoint(self):
        with sqlite3.connect('file:'+str(self.workspace/'index.sqlite3')+'?mode=ro',uri=True) as db:
            self.assertEqual(db.execute('PRAGMA integrity_check').fetchone(),('ok',))
            return {table:db.execute('SELECT * FROM '+table+(' ORDER BY 1' if table=='binding' else ' ORDER BY 1,2')).fetchall()
                    for table in ('binding','partitions','records','assertions')}

    def test_explicit_exact_release_profile_contract_receipt(self):
        receipt=self.contract.receipt()
        self.assertEqual(receipt['expected_format'],'standard')
        self.assertEqual(receipt['release'],self.release)
        self.assertEqual(receipt['source_use_profile_id'],self.profile.receipt()['profile_id'])
        self.assertEqual(receipt['contract_id'],'sha256:'+digest({k:v for k,v in receipt.items() if k!='contract_id'}))
        owned=self.contract.receipt();owned['release']['release_id']='altered'
        self.assertEqual(self.contract.receipt(),receipt)
        self.assertNotIn('source_contract',self.profile.receipt())
        self.assertNotIn('source_contract',self.plan)

    def test_valid_standard_plain_and_gzip(self):
        for compressed in (False,True):
            with self.subTest(compressed=compressed):
                self.prepare(compressed=compressed);self.workspace=self.root/str(compressed)
                report=self.run_import()
                self.assertEqual((report['total_source_rows'],len(report['partition_inventory'])),(22,22))
                self.assertEqual((report['unique_supported_card_identities'],report['distinct_printing_identities']),(4,22))
                receipt=verify_factual_publication(self.workspace,profile=self.profile,expected_report_id=report['report_id'])
                self.assertTrue(receipt['cleanup_eligible']);self.assertFalse(receipt['cleanup_performed'])

    def test_unselected_contract_preserves_original_refusal(self):
        error=self.refusal(lambda:self.run_import(contract=False),'INVALID_INPUT')
        self.assertEqual(str(error),'closed unique MTGJSON meta/data envelope required')

    def test_existing_meta_data_envelopes_keep_historical_results_and_receipts(self):
        self.document.pop('format_name')
        for mode in ('retained-source','limited-retention'):
            with self.subTest(mode=mode):
                self.prepare(mode=mode);self.workspace=self.root/mode
                before=(self.profile.receipt(),deepcopy(self.plan))
                report=self.run_import(contract=False)
                artifacts={p.name:p.read_bytes() for p in (self.workspace/'output').iterdir()}
                self.assertEqual(self.run_import(contract=False),report)
                self.assertEqual({p.name:p.read_bytes() for p in (self.workspace/'output').iterdir()},artifacts)
                self.assertEqual((self.profile.receipt(),self.plan),before)

    def test_default_factual_outputs_equal_exact_predecessor_in_both_modes(self):
        self.document.pop('format_name')
        for mode in ('retained-source','limited-retention'):
            with self.subTest(mode=mode):
                self.prepare(mode=mode);self.workspace=self.root/('old-'+mode)
                with patch.object(implementation,'_worker',predecessor_worker):
                    original=self.run_import(contract=False)
                original_bytes={p.name:p.read_bytes() for p in (self.workspace/'output').iterdir()}
                self.workspace=self.root/('new-'+mode)
                self.assertEqual(self.run_import(contract=False),original)
                self.assertEqual({p.name:p.read_bytes() for p in (self.workspace/'output').iterdir()},original_bytes)

    def test_missing_required_format_metadata_refuses(self):
        self.document.pop('format_name');self.prepare()
        self.refusal(self.run_import,'INVALID_INPUT')
        self.assertFalse((self.workspace/'output/publication.json').exists())

    def test_unsupported_invalid_and_oversized_format_values_refuse(self):
        for i,value in enumerate(('modern','Standard','',False,True,None,1,[],{},'x'*65)):
            with self.subTest(value=value):
                self.document['format_name']=value;self.prepare();self.workspace=self.root/f'invalid{i}'
                self.refusal(self.run_import,'RESOURCE_BUDGET' if value=='x'*65 else 'INVALID_INPUT')
                self.assertFalse((self.workspace/'output/publication.json').exists())

    def test_duplicate_unknown_malformed_truncated_and_trailing_envelopes_refuse(self):
        valid=json.dumps(self.document,separators=(',',':')).encode()
        raw_cases=[valid[:-1]+b',"format_name":"standard"}',
            valid[:-1]+b',"meta":{}}',valid[:-1]+b',"data":{}}',
            valid[:-1]+b',"unknown":true}',valid+b' false',valid[:-1],
            valid.replace(b',"format_name"',b';"format_name"'),
            valid.replace(b'"standard"',b'"stand\\qard"'),
            b'{"meta":{"version":"5.3.0","date":"2026-11-25"},"format_name":"standard"}',
            b'{"data":{},"format_name":"standard"}',b'{}']
        for i,raw in enumerate(raw_cases):
            with self.subTest(case=i):
                self.prepare(raw);self.workspace=self.root/f'bad{i}'
                self.refusal(self.run_import)

    def test_only_documented_section_order_is_supported(self):
        for i,keys in enumerate((('format_name','meta','data'),('meta','format_name','data'),('data','meta','format_name'))):
            doc={k:self.document[k] for k in keys};self.prepare(json.dumps(doc).encode());self.workspace=self.root/f'order{i}'
            self.refusal(self.run_import)

    def test_contract_cannot_come_from_filename_or_source_assertion(self):
        self.source.rename(self.root/'Standard.json.gz');self.source=self.root/'Standard.json.gz'
        self.refusal(lambda:self.run_import(contract=False),'INVALID_INPUT')
        self.assertNotIn('format_name',FACTUAL_FIELDS)

    def test_contract_profile_or_release_mismatch_refuses_before_io(self):
        for contract in (replace(self.contract,source_use_profile_id='sha256:'+'0'*64),
                         replace(self.contract,release_json='{}')):
            self.contract=contract
            with patch.object(Path,'open',side_effect=AssertionError('no source reads')):
                self.refusal(self.run_import,'SOURCE_POLICY_REFUSAL')

    def test_missing_source_use_operation_is_not_bypassed_by_contract(self):
        for operation in LIMITED_OPERATIONS:
            basis=replace(self.bases[0],operations=tuple(x for x in LIMITED_OPERATIONS if x!=operation))
            profile=replace(self.profile,bases=(basis,))
            with patch.object(Path,'open',side_effect=AssertionError('no I/O')):
                with self.assertRaises(SourcePolicyError): StandardExportContract.for_profile(profile)

    def test_serialized_contract_is_not_trusted_host_code(self):
        self.contract=self.contract.receipt()
        with patch.object(Path,'open',side_effect=AssertionError('no I/O')):
            with self.assertRaises(SourcePolicyError):self.run_import()
        with patch.object(implementation,'_decoded',side_effect=AssertionError('no I/O')):
            self.refusal(lambda:list(implementation._partitions(None,ReconciliationLimits(),True)),
                         'UNSUPPORTED_PROFILE')

    def test_oracle_extension_is_not_implicitly_enabled(self):
        profile=replace(self.profile,retention_profile=ORACLE_RETENTION,bases=(
            replace(self.bases[0],operations=LIMITED_OPERATIONS+(ORACLE_OPERATION,)),))
        self.refusal(lambda:StandardExportContract.for_profile(profile),'UNSUPPORTED_PROFILE')

    def test_excluded_fields_and_format_metadata_never_enter_factual_rows(self):
        report=self.run_import()
        self.assertEqual(report['canonical_admission'],'NOT_PERFORMED')
        self.assertEqual(report['production_activation'],'NOT_PERFORMED')
        self.assertEqual(report['real_card_execution'],'BLOCKED')
        self.assertEqual(report['catalog_population_completeness'],'NOT_ESTABLISHED')
        for path in self.workspace.rglob('*'):
            if path.is_file():
                raw=path.read_bytes();self.assertNotIn(CANARY.encode(),raw,path.name)
                self.assertNotIn(b'format_name',raw,path.name)
        self.assertFalse(self.contract.receipt()['format_legality'])
        self.assertTrue(self.source.is_file())

    def test_predecessor_pause_refusal_repaired_resume_matches_clean_publication(self):
        with patch.object(implementation,'_worker',predecessor_worker):
            paused=self.run_import(contract=False,stop_after_partitions=1)
            self.assertEqual(paused['completed_partitions'],1)
            error=self.refusal(lambda:self.run_import(contract=False),'INVALID_INPUT')
        self.assertEqual(str(error),'closed unique MTGJSON meta/data envelope required')
        before=self.checkpoint()
        self.assertEqual((len(before['partitions']),len(before['records']),len(before['assertions'])),(22,22,154))
        self.assertFalse((self.workspace/'output').exists())
        resumed=self.run_import();after=self.checkpoint()
        self.assertEqual(before,after)  # Exact committed binding, partition, row and assertion tuples.
        resumed_bytes={p.name:p.read_bytes() for p in (self.workspace/'output').iterdir()}
        receipt=verify_factual_publication(self.workspace,profile=self.profile,expected_report_id=resumed['report_id'])
        self.assertEqual(receipt['status'],'FACTUAL_RESULTS_DURABLY_PUBLISHED')
        self.workspace=self.root/'clean'
        clean=self.run_import()
        self.assertEqual(clean,resumed)
        self.assertEqual({p.name:p.read_bytes() for p in (self.workspace/'output').iterdir()},resumed_bytes)
        self.assertEqual(verify_factual_publication(self.workspace,profile=self.profile,expected_report_id=clean['report_id']),receipt)

    def test_tampered_checkpoint_refuses_without_relaxing_comparisons(self):
        for i,sql in enumerate(("UPDATE partitions SET raw_hash='altered'", "UPDATE records SET card_id='altered'",
                               "UPDATE assertions SET value='null'", "UPDATE binding SET payload='{}'")):
            with self.subTest(case=i):
                self.workspace=self.root/f'tampered{i}';self.run_import(stop_after_partitions=1)
                with sqlite3.connect(self.workspace/'index.sqlite3') as db:db.execute(sql)
                self.refusal(self.run_import,'INTEGRITY_MISMATCH')

    def test_changed_source_refuses_at_original_hash_check(self):
        self.run_import(stop_after_partitions=1)
        self.source.write_bytes(self.source.read_bytes()+b' ')
        self.refusal(self.run_import,'INTEGRITY_MISMATCH')

    def test_resource_limits_remain_enforced(self):
        self.refusal(lambda:self.run_import(limits=replace(ReconciliationLimits(),rows=1)),'RESOURCE_BUDGET')
        self.workspace=self.root/'invalid-limits'
        self.refusal(lambda:self.run_import(limits=replace(ReconciliationLimits(),rows=1_000_001)),'INVALID_INPUT')
        self.assertEqual(asdict(ReconciliationLimits())['partition_bytes'],8*1024**2)

    def test_trusted_activation_passes_contract_without_changing_plan_identity(self):
        original_plan=deepcopy(self.plan)
        report=activate_private_release(self.plan,self.source,self.root/'activation',
            expected_plan_id=self.plan['plan_id'],reviewed_bases=self.bases,
            basis_files={'original-envelope-authorship':self.evidence},
            internal_decision_reference='original-envelope-research',material='ORIGINAL_PROJECT_FIXTURE',
            notice=self.notice,source_contract=self.contract)
        self.assertEqual(self.plan,original_plan)
        self.assertEqual(report['total_source_rows'],22)
        verify_factual_publication(self.root/'activation/candidates',profile=self.profile,expected_report_id=report['report_id'])

    def test_retained_source_standard_path(self):
        self.prepare(mode='retained-source')
        report=self.run_import()
        self.assertEqual(report['schema_version'],'private-mtgjson-import-report-v1')
        self.assertNotIn('retention_mode',report)
        self.assertFalse((self.workspace/'output/publication.json').exists())

    def test_metadata_string_escapes_and_streaming_boundaries(self):
        # Only original text is supplied to these native-reader checks.
        from contextlib import contextmanager
        for padding in (0,65500,65535,65536,65537,131000):
            doc=deepcopy(self.document);doc['meta']['original_padding']='x'*padding
            raw=json.dumps(doc,separators=(',',':')).replace('"standard"','"\\u0073tandard"').encode()
            for fragment in (7,65536) if padding==0 else (65536,):
                class Fragmented(io.BytesIO):
                    def read(self,size=-1):return super().read(min(size,fragment))
                @contextmanager
                def decoded(_):yield Fragmented(raw)
                with patch.object(implementation,'_decoded',decoded):
                    units=list(implementation._partitions(None,ReconciliationLimits(),self.contract))
                self.assertEqual(sum(key is not None for _,key,_ in units),22)


if __name__=='__main__':unittest.main()
