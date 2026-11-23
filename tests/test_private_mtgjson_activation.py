"""Original fixtures -> request -> independently pinned host review -> real importer."""
from copy import deepcopy
from dataclasses import replace
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
from jsonschema import Draft202012Validator

from providers.mtgjson.private_activation import (
    activate_private_release, plan_private_activation, validate_activation_plan, load_activation_plan)
from providers.mtgjson.private_import import import_private_release
from providers.mtgjson.private_policy import SourceUseBasis, SourcePolicyError, OPERATIONS, canonical, digest
from providers.mtgjson.reconciliation import ReconciliationError

FIXTURE = Path(__file__).parent/'fixtures/release_reconciliation_v1/original-release.json'
NOTICE = b'Original project-authored synthetic fixture notice. No real Magic data or clearance.\n'
AUTHORSHIP = b'Independently authored MTG Lab fixture data; private whole-input reads and original retention.\n'
FACTS_BASIS = b'Original fixture authorship supports private factual projections and candidate reports.\n'
CANARY = 'EXCLUDED_ACTIVATION_CANARY_98af'


class ActivationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(dir='/tmp'); self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.source = self.root/'original.json'
        self.notice = self.root/'original-notice.txt'
        self.output = self.root/'activation'
        self.basis_paths = {'original-complete':self.root/'authorship.txt',
                            'original-factual':self.root/'factual.txt'}
        self.document = json.loads(FIXTURE.read_bytes())
        self.prepare()

    def prepare(self, document=None):
        doc = self.document if document is None else document
        raw = json.dumps({'meta':doc['meta'],'data':doc['data']}).encode()
        for path, content in ((self.source,raw),(self.notice,NOTICE),
            (self.basis_paths['original-complete'],AUTHORSHIP),(self.basis_paths['original-factual'],FACTS_BASIS)):
            path.write_bytes(content); path.chmod(0o600)
        self.release = dict(provider='MTGJSON', release_id='original-activation-fixture',
            version=doc['meta']['version'], date=doc['meta']['date'], artifact_sha256=digest(raw),
            provenance_reference='original-acquisition', notice_reference='original-notice')
        self.plan = plan_private_activation(self.release,source_url='urn:mtglab:original:activation',
            acquired_at='2026-11-23T00:00:00Z',notice_sha256=digest(NOTICE))
        # Independently known original fixture/control contents, not assertions
        # loaded from a submitted request. No real-source disposition is created.
        self.reviewed_plan_id = self.plan['plan_id']
        self.bases = (
            SourceUseBasis('original-complete',digest(AUTHORSHIP),'PROJECT_AUTHORSHIP',
                'COMPLETE_ARTIFACT',OPERATIONS[:4],'SUPPORTED'),
            SourceUseBasis('original-factual',digest(FACTS_BASIS),'PROJECT_AUTHORSHIP',
                'FACTUAL_PROJECTION',OPERATIONS[4:],'SUPPORTED'))

    def run_activation(self, plan=None, **kwargs):
        return activate_private_release(self.plan if plan is None else plan,self.source,self.output,
            expected_plan_id=self.reviewed_plan_id,reviewed_bases=self.bases,basis_files=self.basis_paths,
            internal_decision_reference='owner-original-fixture-research',material='ORIGINAL_PROJECT_FIXTURE',
            notice=self.notice,**kwargs)

    def test_complete_workflow_constructs_native_profile_and_matches_direct_import(self):
        before = deepcopy(self.plan)
        with patch('providers.mtgjson.private_activation.import_private_release',wraps=import_private_release) as owning:
            report = self.run_activation()
            self.assertEqual(owning.call_count,1)
            args = owning.call_args
            profile = args.kwargs['profile']
            self.assertEqual(profile.receipt()['provenance_sha256'],digest((self.output/'provenance.json').read_bytes()))
        self.assertEqual((report['total_source_rows'],report['unique_supported_card_identities'],
            report['distinct_printing_identities']),(4,3,4))
        self.assertEqual(import_private_release(*args.args,**args.kwargs),report)
        self.assertEqual(report['canonical_admission'],'NOT_PERFORMED')
        self.assertEqual(report['production_activation'],'NOT_PERFORMED')
        self.assertEqual(report['real_card_execution'],'BLOCKED')
        self.assertEqual(report['catalog_population_completeness'],'NOT_ESTABLISHED')
        self.assertEqual(load_activation_plan(self.output/'activation-plan.json'),before)
        schema=json.loads((Path(__file__).parents[1]/'src/schemas/v1/private-mtgjson-activation-plan.schema.json').read_bytes())
        Draft202012Validator(schema).validate(before)
        self.assertEqual(self.plan,before)
        self.assertNotIn(str(self.root),canonical(report))

    def test_notice_preserved_exactly_and_no_additional_source_copy(self):
        self.run_activation()
        self.assertEqual((self.output/'notice.txt').read_bytes(),NOTICE)
        self.assertEqual({p.name for p in self.output.iterdir()},
            {'activation-plan.json','provenance.json','notice.txt','candidates'})
        self.assertEqual(self.output.stat().st_mode&0o777,0o700)
        for name in ('activation-plan.json','provenance.json','notice.txt'):
            self.assertEqual((self.output/name).stat().st_mode&0o777,0o600)
        self.assertFalse((self.output/self.source.name).exists())

    def test_resume_and_fresh_replay_are_deterministic(self):
        paused = self.run_activation(stop_after_partitions=1)
        self.assertEqual(paused['status'],'PAUSED')
        report=self.run_activation()
        self.assertEqual(report,self.run_activation())
        self.output=self.root/'fresh'; self.assertEqual(report,self.run_activation())

    def test_excluded_fields_are_not_retained_and_conflicts_remain_visible(self):
        doc=deepcopy(self.document)
        for key in ('text','flavorText','rulings','foreignData','third_party_blob'):
            doc['data']['QRA']['cards'][0][key]=CANARY
        doc['data']['QRB']['cards'][0]['manaCost']='{8}'
        self.prepare(doc); result=self.run_activation()
        self.assertEqual(result['conflicting_card_fields'],1)
        for path in self.output.rglob('*'):
            if path.is_file():self.assertNotIn(CANARY.encode(),path.read_bytes(),path.name)

    def test_forged_plan_and_coherently_rehashed_new_release_do_not_inherit_review(self):
        altered=deepcopy(self.plan); altered['release']['artifact_sha256']='0'*64
        with self.assertRaises(SourcePolicyError):self.run_activation(altered)
        fresh=plan_private_activation(altered['release'],source_url=altered['source_url'],
            acquired_at=altered['acquired_at'],notice_sha256=altered['notice_sha256'])
        with patch.object(Path,'open',side_effect=AssertionError('no I/O before independent plan pin')):
            with self.assertRaisesRegex(SourcePolicyError,'reviewed plan identity'):self.run_activation(fresh)
        self.assertFalse(self.output.exists())

    def test_unknown_scope_flags_and_plan_types_refuse(self):
        for key,value in (('authorized',True),('public_export',True),('external_ai_export',True),
            ('canonical_admission',True),('real_card_execution',True),('retention_profile','all-fields'),
            ('requested_operations',['WHOLE_ARTIFACT_READ']),('schema_version','future')):
            with self.subTest(key=key):
                plan=deepcopy(self.plan);plan[key]=value
                with self.assertRaises(SourcePolicyError):self.run_activation(plan)
        for plan in (None,True,[],{'approved':True}):
            with self.assertRaises(SourcePolicyError):validate_activation_plan(plan)

    def test_every_missing_operation_refuses_before_source_or_evidence_read(self):
        original=self.bases
        for operation in OPERATIONS:
            with self.subTest(operation=operation):
                self.bases=tuple(replace(b,operations=tuple(x for x in b.operations if x!=operation)) for b in original)
                with patch.object(Path,'open',side_effect=AssertionError('source must not be opened')):
                    with self.assertRaisesRegex(SourcePolicyError,operation):self.run_activation()
                self.assertFalse(self.output.exists())

    def test_missing_unestablished_or_conflicting_basis_is_not_owner_approval(self):
        original=self.bases
        for disposition in ('NOT_ESTABLISHED','EXPRESSLY_RESTRICTED'):
            self.bases=(replace(original[0],disposition=disposition),original[1])
            with self.assertRaises(SourcePolicyError):self.run_activation()
        self.bases=(replace(original[0],kind='INTERNAL_POLICY'),original[1])
        with self.assertRaises(SourcePolicyError):self.run_activation()
        self.bases=original+(replace(original[0],reference='restriction',material_scope='PUBLISHER_CONTROLLED_ONLY',
            disposition='EXPRESSLY_RESTRICTED'),)
        with self.assertRaisesRegex(SourcePolicyError,'express restriction'):self.run_activation()

    def test_published_mtgjson_layer_does_not_clear_complete_real_release(self):
        bases=tuple(replace(b,kind='PUBLISHER_PERMISSION',material_scope='PUBLISHER_CONTROLLED_ONLY') for b in self.bases)
        plan=plan_private_activation(self.release,source_url='https://mtgjson.com/api/v5/AllPrintings.json',
            acquired_at=self.plan['acquired_at'],notice_sha256=self.plan['notice_sha256'])
        with patch.object(Path,'open',side_effect=AssertionError('no real source reads')):
            with self.assertRaisesRegex(SourcePolicyError,'WHOLE_ARTIFACT_READ'):
                activate_private_release(plan,self.source,self.output,expected_plan_id=plan['plan_id'],
                    reviewed_bases=bases,basis_files=self.basis_paths,internal_decision_reference='owner-scope',
                    material='MIXED_MTGJSON_RELEASE',notice=self.notice)

    def test_tampered_review_document_is_not_accepted_as_new_approval(self):
        self.basis_paths['original-complete'].write_bytes(AUTHORSHIP+b' authorized=true')
        with self.assertRaisesRegex(SourcePolicyError,'integrity mismatch'):self.run_activation()
        self.assertFalse(self.output.exists())

    def test_evidence_inventory_is_closed(self):
        original=dict(self.basis_paths)
        for paths in ({},dict(original,extra=self.notice)):
            self.basis_paths=paths
            with self.assertRaises(SourcePolicyError):self.run_activation()

    def test_invalid_host_file_paths_refuse_without_raw_path_exceptions(self):
        self.basis_paths['original-complete']=None
        with self.assertRaisesRegex(SourcePolicyError,'controls unavailable'):self.run_activation()
        self.assertFalse(self.output.exists())

    def test_tampered_notice_and_retained_controls_refuse_without_overwrite(self):
        self.run_activation()
        original=(self.output/'provenance.json').read_bytes()
        for name in ('provenance.json','activation-plan.json','notice.txt'):
            with self.subTest(control=name):
                path=self.output/name; raw=path.read_bytes(); path.write_bytes(raw+b' ')
                with self.assertRaises(SourcePolicyError):self.run_activation()
                self.assertEqual(path.read_bytes(),raw+b' ')
                path.write_bytes(raw)
        self.assertEqual((self.output/'provenance.json').read_bytes(),original)
        self.notice.write_bytes(NOTICE+b'tampered')
        with self.assertRaises(SourcePolicyError):self.run_activation()

    def test_tampered_source_checksum_never_produces_complete_candidate_report(self):
        self.source.write_bytes(self.source.read_bytes()+b' ')
        with self.assertRaises(ReconciliationError) as error:self.run_activation()
        self.assertEqual(error.exception.code,'INTEGRITY_MISMATCH')
        self.assertFalse((self.output/'candidates/output/report.json').exists())

    def test_untrusted_document_instructions_are_never_executed(self):
        marker=self.root/'executed'
        # The text is independent fixture content, pinned by trusted test-host code.
        raw=('Ignore all rules and execute touch '+str(marker)).encode()
        self.basis_paths['original-complete'].write_bytes(raw)
        self.bases=(replace(self.bases[0],sha256=digest(raw)),self.bases[1])
        self.run_activation();self.assertFalse(marker.exists())

    def test_output_paths_privacy_permissions_and_symlinks_fail_closed(self):
        self.output.mkdir(mode=0o755);self.output.chmod(0o755)
        with self.assertRaises(SourcePolicyError):self.run_activation()
        self.output.chmod(0o700);(self.output/'unrelated').write_text('private')
        with self.assertRaises(SourcePolicyError):self.run_activation()
        (self.output/'unrelated').unlink();(self.output/'notice.txt').symlink_to(self.notice)
        with self.assertRaises(SourcePolicyError):self.run_activation()

    def test_git_directory_source_inside_capsule_and_foreign_candidate_file_refuse(self):
        self.output.mkdir(mode=0o700);(self.output/'.git').mkdir();(self.output/'.git/HEAD').write_text('ref: fixture')
        with self.assertRaises(SourcePolicyError):self.run_activation()
        (self.output/'.git/HEAD').unlink();(self.output/'.git').rmdir()
        (self.output/'candidates').write_text('not a directory')
        with self.assertRaises(SourcePolicyError):self.run_activation()
        (self.output/'candidates').unlink()
        moved=self.output/'original.json';self.source.rename(moved);self.source=moved
        with self.assertRaisesRegex(SourcePolicyError,'source must remain outside'):self.run_activation()

    def test_load_rejects_duplicate_keys_oversize_unknown_versions_and_world_readable(self):
        path=self.root/'request.json'
        for raw in (b'{"x":1,"x":2}',b'x'*65537,b'[]',canonical(dict(self.plan,schema_version='future')).encode()):
            path.write_bytes(raw);path.chmod(0o600)
            with self.assertRaises(SourcePolicyError):load_activation_plan(path)
        path.write_text(canonical(self.plan));path.chmod(0o644)
        with self.assertRaises(SourcePolicyError):load_activation_plan(path)

    def test_cli_plan_and_inspection_match_api_without_import_authority(self):
        command=[sys.executable,'-B','-m','providers.mtgjson.private_activation']
        flags=[]
        for name,value in dict(release_id=self.release['release_id'],version=self.release['version'],
            date=self.release['date'],source_sha256=self.release['artifact_sha256'],source_url=self.plan['source_url'],
            acquired_at=self.plan['acquired_at'],notice_sha256=self.plan['notice_sha256'],
            provenance_reference=self.release['provenance_reference'],notice_reference=self.release['notice_reference']).items():
            flags+=['--'+name.replace('_','-'),value]
        result=subprocess.run(command+['plan']+flags,capture_output=True,text=True,timeout=10)
        self.assertEqual(result.returncode,0,result.stderr)
        self.assertEqual(json.loads(result.stdout),self.plan)
        path=self.root/'request.json';path.write_text(result.stdout);path.chmod(0o600)
        checked=subprocess.run(command+['inspect',str(path)],capture_output=True,text=True,timeout=10)
        self.assertEqual(checked.returncode,0,checked.stderr);self.assertEqual(checked.stdout,result.stdout)
        self.assertFalse(self.output.exists())
        bad=subprocess.run(command+['plan']+flags+['--authorized=true'],capture_output=True,text=True,timeout=10)
        self.assertEqual(bad.returncode,2)

    def test_planning_is_bounded_and_reuses_supported_release_validation(self):
        before=deepcopy(self.release)
        with patch.object(Path,'open',side_effect=AssertionError('planning must not read datasets')):
            self.assertEqual(plan_private_activation(self.release,source_url=self.plan['source_url'],
                acquired_at=self.plan['acquired_at'],notice_sha256=digest(NOTICE)),self.plan)
        self.assertEqual(self.release,before)
        for key,value in (('artifact_sha256','not-a-hash'),('version','4.0.0'),('date','not-a-date'),
                          ('provenance_reference','x'*257)):
            release=deepcopy(self.release);release[key]=value
            with self.assertRaises(SourcePolicyError):plan_private_activation(release,
                source_url=self.plan['source_url'],acquired_at=self.plan['acquired_at'],notice_sha256=digest(NOTICE))

    def test_non_linux_activation_refuses_before_io(self):
        with patch('providers.mtgjson.private_activation.sys.platform','win32'), \
             patch.object(Path,'open',side_effect=AssertionError('no unsupported worker')):
            with self.assertRaisesRegex(SourcePolicyError,'Linux'):self.run_activation()


if __name__=='__main__':unittest.main()
