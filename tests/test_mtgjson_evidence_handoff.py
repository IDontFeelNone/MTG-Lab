"""Original authored evidence exercises the actual importer and existing consumer."""
from copy import deepcopy
from dataclasses import replace
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from jsonschema import Draft202012Validator
from card_intelligence.mechanics import MechanicalCardIntelligence, MechanicalEvidenceError
from providers.mtgjson.private_import import import_private_release
from providers.mtgjson.private_policy import (PrivateResearchProfile, SourceUseBasis, SourcePolicyError,
    OPERATIONS, ORACLE_RETENTION, ORACLE_OPERATION, ORACLE_INSPECTION, RETENTION, canonical, digest)
from providers.mtgjson.reconciliation import ReconciliationError, ReconciliationLimits
from card_intelligence_attachment_fixture import build_intelligence_fixture, attach_fixture
from query import CanonicalQueryEngine

ROOT = Path(__file__).parents[1]
TEXT = 'Original test mechanism: rotate a paper dial, then place a blue pebble in a tray.'
CANARY = 'UNAUTHORIZED_FLAVOR_OR_RULINGS_CANARY'


def original_document():
    def row(card, printing, name, number):
        return dict(uuid=printing, name=name, number=number, layout='normal', colors=[],
            manaCost='{2}', finishes=['nonfoil'], text=TEXT,
            identifiers={'scryfallOracleId':card})
    return dict(meta=dict(version='5.2.1',date='2026-11-23'), data={
        'EQA':dict(code='EQA',name='Original Evidence: Quiet Apparatus', cards=[
            row('cloth-unit','cloth-edition','Original Cloth Apparatus','1'),
            row('copper-unit','copper-edition','Original Copper Apparatus','2')]),
        'EQB':dict(code='EQB',name='Original Evidence: Quiet Branch', cards=[
            row('cloth-unit','cloth-alternative','Original Cloth Apparatus','7')])})


class EvidenceHandoffTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(dir='/tmp');self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name); self.workspace=self.root/'import'
        self.source=self.root/'source.json';self.provenance=self.root/'provenance.json';self.notice=self.root/'notice.txt'
        self.document=original_document()

    def prepare(self, *, mode='retained-source', factual=False):
        self.source.write_text(json.dumps(self.document));self.source.chmod(0o600)
        release=dict(provider='MTGJSON',release_id='original-evidence-fixture',
            version=self.document['meta'].get('version','5.2.1'),date='2026-11-23',artifact_sha256=digest(self.source.read_bytes()),
            provenance_reference='original-authored-acquisition',notice_reference='original-notice')
        self.provenance.write_text(canonical({k:v for k,v in release.items() if k not in
            ('provenance_reference','notice_reference')} | dict(source_url='urn:mtglab:original:evidence',
            acquired_at='2026-11-23T08:00:00Z',acquisition_method='MANUALLY_SUPPLIED')))
        self.notice.write_text('Original project-authored test fixture only; no real Card source content.\n')
        self.notice.chmod(0o600); self.provenance.chmod(0o600)
        operations=OPERATIONS if factual else (*OPERATIONS,ORACLE_OPERATION,ORACLE_INSPECTION)
        self.profile=PrivateResearchProfile.for_release(release,
            provenance_sha256=digest(self.provenance.read_bytes()),notice_sha256=digest(self.notice.read_bytes()),
            bases=(SourceUseBasis('original-fixture-authorship',digest(b'Original authorship'),
                'PROJECT_AUTHORSHIP','COMPLETE_ARTIFACT',operations,'SUPPORTED'),),
            material='ORIGINAL_PROJECT_FIXTURE',internal_decision_reference='original-test-scope',
            retention_profile=RETENTION if factual else ORACLE_RETENTION,retention_mode=mode)

    def run_import(self, **kwargs):
        return import_private_release(self.source,self.workspace,profile=self.profile,
            provenance=self.provenance,notice=self.notice,**kwargs)

    def inspect(self, report, **kwargs):
        if not hasattr(self,'query'):
            self.fixture=build_intelligence_fixture(self.root/'catalog-fixture')
            self.query=CanonicalQueryEngine.from_attachment(attach_fixture(self.fixture))
        args=dict(expected_query_snapshot_id=self.query.snapshot().snapshot_id,
            card_id='cloth-unit',printing_id='cloth-edition',evidence_directory=self.workspace/'output',
            profile=self.profile,expected_report_id=report['report_id'])
        args.update(kwargs)
        return MechanicalCardIntelligence.inspect_mtgjson_candidate(self.query,**args)

    def test_end_to_end_actual_imported_text_existing_consumer_and_no_authority_change(self):
        self.prepare(); report=self.run_import()
        with patch.object(MechanicalCardIntelligence,'_load_source',side_effect=AssertionError('no acquisition read')):
            result=self.inspect(report)
        before={p:p.read_bytes() for p in self.fixture['catalog'].rglob('*') if p.is_file()}
        row=result['evidence']['occurrences'][0]
        self.assertEqual(row['text']['value'],TEXT)
        self.assertEqual(row['text']['source_pointer'],'/data/EQA/cards/0/text')
        self.assertEqual(row['source_record_sha256'],digest(self.document['data']['EQA']['cards'][0]))
        self.assertEqual(row['source_release']['artifact_sha256'],digest(self.source.read_bytes()))
        self.assertEqual(row['source_use_profile_id'],self.profile.receipt()['profile_id'])
        self.assertEqual(row['source_release']['version'],'5.2.1')
        self.assertEqual(result['authority'],'UNADMITTED_SOURCE_EVIDENCE_ONLY')
        self.assertFalse(result['admitted_dossier_populated']);self.assertFalse(result['current_oracle_verified'])
        self.assertEqual(result['semantic_authority'],'NOT_ESTABLISHED')
        self.assertEqual(result['real_card_execution'],'BLOCKED')
        self.assertEqual(self.inspect(report),result)
        self.assertEqual(before,{p:p.read_bytes() for p in self.fixture['catalog'].rglob('*') if p.is_file()})
        native=MechanicalCardIntelligence.from_attachment(attach_fixture(self.fixture),
            data_root=self.fixture['mechanical_data'],expected_query_snapshot_id=self.query.snapshot().snapshot_id,
            source_directory=self.fixture['source_directory'])
        before_dossier=native.dossier('cloth-unit').to_json()
        self.inspect(report)
        self.assertEqual(native.dossier('cloth-unit').to_json(),before_dossier)
        self.assertNotIn(TEXT,before_dossier)
        schema=json.loads((ROOT/'src/schemas/v1/private-mtgjson-oracle-import-report.schema.json').read_bytes())
        Draft202012Validator(schema).validate(report)
        self.assertEqual(report,self.run_import())

    def test_factual_path_still_excludes_text_and_receipt_shape_unchanged(self):
        self.prepare(factual=True);report=self.run_import()
        self.assertEqual(report['schema_version'],'private-mtgjson-import-report-v1')
        self.assertNotIn('retention_mode',self.profile.receipt())
        self.assertNotIn('oracle-evidence.jsonl',report['artifacts'])
        self.assertNotIn(TEXT,(self.workspace/'output/assertions.jsonl').read_text())
        with self.assertRaises(SourcePolicyError):self.inspect(report)

    def test_limited_retention_no_original_after_completion_and_honest_replay(self):
        self.prepare(mode='limited-retention')
        self.profile=replace(self.profile,bases=(replace(self.profile.bases[0],operations=tuple(
            x for x in self.profile.bases[0].operations if x!='PRIVATE_SOURCE_RETENTION')),))
        report=self.run_import();original=self.source.read_bytes()
        self.assertEqual(self.source.read_bytes(),original)  # No automatic deletion.
        self.source.unlink()  # Explicit test custodian action only.
        result=self.inspect(report)
        self.assertEqual(result['evidence']['occurrences'][0]['text']['value'],TEXT)
        self.assertFalse(result['evidence']['replay']['complete_source_replay_available_without_original'])
        with self.assertRaises((SourcePolicyError,ReconciliationError)):self.run_import()

    def test_retained_mode_requires_original_retention_basis(self):
        self.prepare();self.profile=replace(self.profile,bases=(replace(self.profile.bases[0],operations=tuple(
            x for x in self.profile.bases[0].operations if x!='PRIVATE_SOURCE_RETENTION')),))
        with patch.object(Path,'open',side_effect=AssertionError('no read')):
            with self.assertRaises(SourcePolicyError):self.run_import()

    def test_missing_or_wrong_text_retention_scope_refuses_before_reads(self):
        self.prepare()
        for change in (dict(operations=OPERATIONS),dict(material_scope='FACTUAL_PROJECTION'),
                       dict(disposition='NOT_ESTABLISHED'),dict(disposition='EXPRESSLY_RESTRICTED'),dict(kind='INTERNAL_POLICY')):
            with self.subTest(change=change):
                profile=replace(self.profile,bases=(replace(self.profile.bases[0],**change),))
                with patch.object(Path,'open',side_effect=AssertionError('no IO')):
                    with self.assertRaises(SourcePolicyError):profile.require_supported()

    def test_inspection_requires_its_own_operation_scope(self):
        self.prepare();self.profile=replace(self.profile,bases=(replace(self.profile.bases[0],operations=tuple(
            x for x in self.profile.bases[0].operations if x!=ORACLE_INSPECTION)),))
        report=self.run_import()
        with self.assertRaisesRegex(SourcePolicyError,ORACLE_INSPECTION):self.inspect(report)

    def test_conflicting_card_text_is_retained_as_withheld_not_a_winner(self):
        self.document['data']['EQB']['cards'][0]['text']='Original contradictory dial instruction.'
        self.prepare();report=self.run_import();result=self.inspect(report)
        self.assertEqual(report['conflicting_card_fields'],1)
        self.assertEqual(result['evidence']['status'],'WITHHELD')
        self.assertIn('CONFLICTING_CARD_ASSERTIONS',result['evidence']['occurrences'][0]['conditions'])

    def test_conflicting_printing_and_foreign_identity_are_not_confident_evidence(self):
        other=deepcopy(self.document['data']['EQA']['cards'][0]);other['text']='Original other text.'
        other['identifiers']['scryfallOracleId']='copper-unit'
        self.document['data']['EQA']['cards'].append(other)
        self.prepare();report=self.run_import();result=self.inspect(report)
        self.assertEqual(result['evidence']['status'],'WITHHELD')
        self.assertIn('DUPLICATE_OR_CONFLICTING_PRINTING',result['evidence']['occurrences'][0]['conditions'])
        with self.assertRaises(MechanicalEvidenceError):self.inspect(report,card_id='copper-unit')
        with self.assertRaises(MechanicalEvidenceError):self.inspect(report,card_id='not-a-card')
        with self.assertRaises(MechanicalEvidenceError):self.inspect(report,printing_id='cloth-alternative')

    def test_missing_identity_is_not_zero_or_verified_text(self):
        self.document['data']['EQA']['cards'][0]['identifiers']={}
        self.prepare();report=self.run_import()
        self.assertEqual(self.inspect(report)['evidence']['status'],'IDENTITY_UNRESOLVED')

    def test_missing_null_unsupported_text_and_face_boundaries(self):
        for changes, state in (({'text':None},'MISSING'),({'text':3},'UNSUPPORTED'),
            ({'layout':'transform'},'UNSUPPORTED'),({'oracle_text':TEXT},'MISSING')):
            with self.subTest(changes=changes):
                self.document=original_document();row=self.document['data']['EQA']['cards'][0]
                row.pop('text');row.update(changes);self.prepare();self.workspace=self.root/('run-'+str(len(list(self.root.iterdir()))))
                report=self.run_import();obs=self.inspect(report)['evidence']['occurrences'][0]
                self.assertEqual(obs['text']['status'],state);self.assertNotIn('value',obs['text'])

    def test_explicit_face_text_never_inherits_other_face(self):
        row=self.document['data']['EQA']['cards'][0]
        row.update(layout='transform',side='a',faceName='Original Front',otherFaceIds=['cloth-alternative'])
        back=self.document['data']['EQB']['cards'][0]
        back.update(layout='transform',side='b',faceName='Original Back',otherFaceIds=['cloth-edition'],text='Original back instruction.')
        self.prepare();report=self.run_import();occ=self.inspect(report)['evidence']['occurrences'][0]
        self.assertEqual(occ['text']['face_boundary']['kind'],'EXPLICIT_FACE')
        self.assertEqual(occ['text']['value'],TEXT)
        self.assertEqual(occ['candidate_status'],'WITHHELD')

    def test_unsupported_fields_never_retained(self):
        for row in self.document['data']['EQA']['cards']:
            row.update(flavorText=CANARY,rulings=[CANARY],oracle_text=CANARY,foreignData=[CANARY])
        self.prepare();self.run_import()
        for path in self.workspace.rglob('*'):
            if path.is_file():self.assertNotIn(CANARY.encode(),path.read_bytes())

    def test_source_corruption_and_version_mismatch_refuse(self):
        self.prepare();self.source.write_text(self.source.read_text()+' ')
        with self.assertRaisesRegex(ReconciliationError,'checksum'):self.run_import()
        self.document['meta'].pop('version');self.prepare();self.workspace=self.root/'missing-version'
        with self.assertRaises(ReconciliationError):self.run_import()

    def test_changed_evidence_or_rehashed_report_does_not_inherit_host_pin(self):
        self.prepare();report=self.run_import();self.inspect(report)
        path=self.workspace/'output/oracle-evidence.jsonl';raw=path.read_bytes()
        path.write_bytes(raw.replace(b'paper dial',b'other dial'))
        with self.assertRaises(SourcePolicyError):self.inspect(report)
        path.write_bytes(raw)
        rp=self.workspace/'output/report.json';new=deepcopy(report)
        new['canonical_admission']='ADMITTED';new['report_id']='sha256:'+digest({k:v for k,v in new.items() if k!='report_id'})
        rp.write_text(canonical(new))
        with self.assertRaises(SourcePolicyError):self.inspect(report)

    def test_stale_profile_catalog_and_unattached_query_refuse(self):
        self.prepare();report=self.run_import();self.inspect(report)
        with self.assertRaises(MechanicalEvidenceError):self.inspect(report,expected_query_snapshot_id='sha256:'+'0'*64)
        with self.assertRaises(SourcePolicyError):self.inspect(report,profile=replace(self.profile,notice_sha256='0'*64))
        query=CanonicalQueryEngine(data_root=self.fixture['catalog']/'data')
        with self.assertRaises(MechanicalEvidenceError):MechanicalCardIntelligence.inspect_mtgjson_candidate(query,
            expected_query_snapshot_id=query.snapshot().snapshot_id,card_id='cloth-unit',printing_id='cloth-edition',
            evidence_directory=self.workspace/'output',profile=self.profile,expected_report_id=report['report_id'])

    def test_paused_checkpoint_resume_and_fresh_replay(self):
        self.prepare();self.assertEqual(self.run_import(stop_after_partitions=1)['status'],'PAUSED')
        with self.assertRaises(SourcePolicyError):self.inspect({'report_id':'sha256:'+'0'*64})
        report=self.run_import();self.assertEqual(report,self.run_import())
        self.workspace=self.root/'fresh';self.assertEqual(report,self.run_import())

    def test_resource_bound_no_silent_ceiling_increase(self):
        self.prepare()
        with self.assertRaises(ReconciliationError):self.run_import(limits=replace(ReconciliationLimits(),row_bytes=100))
        with self.assertRaises(ReconciliationError):self.run_import(limits=replace(ReconciliationLimits(),row_bytes=128*1024))

    def test_host_umask_does_not_expose_or_block_oracle_evidence(self):
        self.prepare()
        previous=os.umask(0o022)
        try:
            report=self.run_import()
            self.assertEqual((self.workspace/'output').stat().st_mode & 0o777,0o700)
            for path in self.workspace.rglob('*'):
                if path.is_file() and path.name not in ('.lock','last-run.json'):
                    self.assertEqual(path.stat().st_mode & 0o077,0,path.name)
            self.assertEqual(self.inspect(report)['evidence']['occurrences'][0]['text']['value'],TEXT)
            (self.workspace/'output').chmod(0o755)  # Earlier host-default output mode.
            self.assertEqual(self.run_import(),report)
            self.assertEqual((self.workspace/'output').stat().st_mode & 0o777,0o700)
            self.assertEqual(self.inspect(report)['evidence']['occurrences'][0]['text']['value'],TEXT)
        finally:
            os.umask(previous)

    def test_split_grants_and_unsupported_field_retention_cannot_inherit_scope(self):
        self.prepare()
        original=self.profile.bases[0]
        # Complete reads and factual retention do not cover expressive retention.
        factual=replace(original,operations=OPERATIONS)
        text=replace(original,reference='original-text-scope',material_scope='ORACLE_PROJECTION',
            operations=(ORACLE_OPERATION,ORACLE_INSPECTION,'PRIVATE_REPORTS'))
        self.profile=replace(self.profile,bases=(factual,text))
        report=self.run_import();self.assertEqual(self.inspect(report)['evidence']['occurrences'][0]['text']['value'],TEXT)
        self.profile=replace(self.profile,retention_profile='retain-all-source-fields')
        with self.assertRaises(SourcePolicyError):self.profile.require_supported()

    def test_exact_empty_unicode_instruction_data_and_immutable_inputs(self):
        self.document['data']['EQA']['cards'][0]['text']='$(never_execute) <script>data</script>\nOriginal Ω instruction.'
        self.document['data']['EQB']['cards'][0]['text']=self.document['data']['EQA']['cards'][0]['text']
        self.document['data']['EQA']['cards'][1]['text']=''
        self.prepare();original=self.source.read_bytes();profile=self.profile.receipt()
        report=self.run_import();result=self.inspect(report)
        self.assertEqual(result['evidence']['occurrences'][0]['text']['value'],self.document['data']['EQA']['cards'][0]['text'])
        empty=self.inspect(report,card_id='copper-unit',printing_id='copper-edition')['evidence']['occurrences'][0]['text']
        self.assertEqual((empty['status'],empty['value']),('SUPPLIED',''))
        self.assertEqual(original,self.source.read_bytes());self.assertEqual(profile,self.profile.receipt())

    def test_unsafe_evidence_paths_and_wrong_report_version_refuse(self):
        self.prepare();report=self.run_import();self.inspect(report)
        link=self.root/'linked-output';link.symlink_to(self.workspace/'output',target_is_directory=True)
        with self.assertRaises(SourcePolicyError):self.inspect(report,evidence_directory=link)
        row=self.workspace/'output/oracle-evidence.jsonl';saved=row.read_bytes();row.unlink()
        elsewhere=self.root/'elsewhere';elsewhere.write_bytes(saved);row.symlink_to(elsewhere)
        with self.assertRaises(SourcePolicyError):self.inspect(report)
        row.unlink();row.write_bytes(saved)
        changed=deepcopy(report);changed['schema_version']='unsupported-import-v99'
        changed['report_id']='sha256:'+digest({k:v for k,v in changed.items() if k!='report_id'})
        (self.workspace/'output/report.json').write_text(canonical(changed))
        with self.assertRaises(SourcePolicyError):self.inspect(changed)


if __name__=='__main__':unittest.main()
