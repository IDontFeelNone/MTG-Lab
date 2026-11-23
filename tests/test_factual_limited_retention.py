"""Original authored inputs exercise the existing importer, activation and custody boundary."""
from copy import deepcopy
from dataclasses import replace
import json
import os
from pathlib import Path
import subprocess
import sys
import fcntl
import unittest
from unittest.mock import patch

from jsonschema import Draft202012Validator
import test_private_mtgjson_import as original
import test_private_mtgjson_activation as activation
from providers.mtgjson.private_policy import (SourcePolicyError, LIMITED_OPERATIONS,
    RETENTION, canonical, digest)
from providers.mtgjson.private_activation import plan_private_activation, validate_activation_plan
from providers.mtgjson.factual_retention import verify_factual_publication, publish_factual_results
from providers.mtgjson.reconciliation import ReconciliationError, ReconciliationLimits


class FactualLimitedTests(unittest.TestCase):
    def setUp(self):
        self.h = original.PrivateImportTests(); self.h.setUp(); self.addCleanup(self.h.doCleanups)
        self.h.prepare()
        self.h.profile = replace(self.h.profile, retention_mode='limited-retention', bases=(
            replace(self.h.profile.bases[0], operations=LIMITED_OPERATIONS),))

    def verify(self, report):
        return verify_factual_publication(self.h.workspace, profile=self.h.profile,
                                         expected_report_id=report['report_id'])

    def test_explicit_selection_and_mode_receipt_bind_actual_operations(self):
        receipt = self.h.profile.receipt()
        self.assertEqual(receipt['schema_version'], 'private-mtgjson-source-profile-v2')
        self.assertEqual(receipt['retention_mode'], 'limited-retention')
        self.assertEqual(receipt['requested_operations'], list(LIMITED_OPERATIONS))
        self.assertNotIn('PRIVATE_SOURCE_RETENTION', receipt['requested_operations'])
        report = self.h.run_import(); publication = self.verify(report)
        self.assertEqual(report['schema_version'], 'private-mtgjson-factual-limited-report-v1')
        self.assertEqual((report['total_source_rows'], report['distinct_printing_identities']), (4,4))
        self.assertTrue(publication['cleanup_eligible']); self.assertFalse(publication['cleanup_performed'])
        self.assertTrue(self.h.source.is_file())
        self.assertEqual((self.h.workspace/'output/notice.txt').read_bytes(),self.h.notice.read_bytes())
        self.assertEqual((self.h.workspace/'output/provenance.json').read_bytes(),self.h.provenance.read_bytes())

    def test_retained_source_default_receipt_and_report_remain_v1(self):
        self.h.prepare(); report=self.h.run_import()
        self.assertNotIn('retention_mode',self.h.profile.receipt())
        self.assertNotIn('requested_operations',self.h.profile.receipt())
        self.assertNotIn('retention_mode', report)
        self.assertEqual(report['schema_version'],'private-mtgjson-import-report-v1')
        self.assertFalse((self.h.workspace/'output/publication.json').exists())
        missing=replace(self.h.profile,bases=(replace(self.h.profile.bases[0],operations=LIMITED_OPERATIONS),))
        with self.assertRaisesRegex(SourcePolicyError,'PRIVATE_SOURCE_RETENTION'):missing.require_supported()

    def test_each_actual_operation_remains_required_before_io(self):
        for operation in LIMITED_OPERATIONS:
            profile=replace(self.h.profile,bases=(replace(self.h.profile.bases[0],
                operations=tuple(x for x in LIMITED_OPERATIONS if x!=operation)),))
            with self.subTest(operation=operation),patch.object(Path,'open',side_effect=AssertionError('no read')):
                with self.assertRaisesRegex(SourcePolicyError,operation):
                    original.import_private_release(self.h.source,self.h.workspace,profile=profile,
                        provenance=self.h.provenance,notice=self.h.notice)

    def test_supported_broad_grant_cannot_erase_express_restriction(self):
        for operation in LIMITED_OPERATIONS:
            restriction=replace(self.h.profile.bases[0],reference='restricted',operations=(operation,),
                                disposition='EXPRESSLY_RESTRICTED')
            with self.subTest(operation=operation),self.assertRaisesRegex(SourcePolicyError,'express restriction'):
                replace(self.h.profile,bases=(*self.h.profile.bases,restriction)).require_supported()

    def test_unperformed_source_retention_is_not_requested(self):
        restriction=replace(self.h.profile.bases[0],reference='no-ongoing-source',
            operations=('PRIVATE_SOURCE_RETENTION',),disposition='EXPRESSLY_RESTRICTED')
        self.h.profile=replace(self.h.profile,bases=(*self.h.profile.bases,restriction))
        self.verify(self.h.run_import())

    def test_limited_mode_is_not_authority_or_whole_input_scope(self):
        for basis in (replace(self.h.profile.bases[0],kind='INTERNAL_POLICY'),
                      replace(self.h.profile.bases[0],material_scope='FACTUAL_PROJECTION'),
                      replace(self.h.profile.bases[0],disposition='NOT_ESTABLISHED')):
            with self.assertRaises(SourcePolicyError):replace(self.h.profile,bases=(basis,)).require_supported()

    def test_source_checksum_failure_never_publishes_cleanup_receipt(self):
        self.h.source.write_bytes(self.h.source.read_bytes()+b' ')
        with self.assertRaisesRegex(ReconciliationError,'checksum'):self.h.run_import()
        self.assertFalse((self.h.workspace/'output/publication.json').exists())
        self.assertTrue(self.h.source.exists())

    def test_coherently_rehashed_source_metadata_mismatch_refuses(self):
        doc=deepcopy(self.h.document);doc['meta']['version']='5.9.9'
        raw=json.dumps({'meta':doc['meta'],'data':doc['data']}).encode();self.h.source.write_bytes(raw)
        release=json.loads(self.h.profile.release_json);release['artifact_sha256']=digest(raw)
        provenance=json.loads(self.h.provenance.read_bytes());provenance['artifact_sha256']=digest(raw)
        self.h.provenance.write_text(canonical(provenance))
        self.h.profile=replace(self.h.profile,release_json=canonical(release),
                               provenance_sha256=digest(self.h.provenance.read_bytes()))
        with self.assertRaisesRegex(ReconciliationError,'metadata mismatch'):self.h.run_import()
        self.assertFalse((self.h.workspace/'output/publication.json').exists())

    def test_excluded_fields_never_reach_sqlite_outputs_controls_or_errors(self):
        doc=deepcopy(self.h.document);canary='LIMITED_EXPRESSIVE_CANARY_54391'
        row=doc['data']['QRA']['cards'][0]
        for key in ('text','rulings','flavorText','artwork','purchaseUrls','marketplace','unsupported'):
            row[key]=canary
        self.h.prepare(doc);self.h.profile=replace(self.h.profile,retention_mode='limited-retention',
            bases=(replace(self.h.profile.bases[0],operations=LIMITED_OPERATIONS),))
        self.h.run_import()
        for path in self.h.workspace.rglob('*'):
            if path.is_file():self.assertNotIn(canary.encode(),path.read_bytes(),path.name)

    def test_pause_requires_original_recovery_then_matches_fresh_replay(self):
        paused=self.h.run_import(stop_after_partitions=1)
        self.assertEqual(paused['status'],'PAUSED')
        self.assertFalse((self.h.workspace/'output/publication.json').exists())
        source=self.h.source.read_bytes();self.h.source.unlink()
        with self.assertRaises(SourcePolicyError):self.h.run_import()
        self.h.source.write_bytes(source);self.h.source.chmod(0o600)
        report=self.h.run_import();receipt=self.verify(report)
        self.h.workspace=self.h.root/'fresh'
        self.assertEqual(self.h.run_import(),report);self.assertEqual(self.verify(report),receipt)

    def test_mode_change_cannot_resume_old_checkpoint(self):
        self.h.run_import(stop_after_partitions=1)
        self.h.profile=replace(self.h.profile,retention_mode='retained-source',bases=(
            replace(self.h.profile.bases[0],operations=original.OPERATIONS),))
        with self.assertRaisesRegex(ReconciliationError,'workspace binding mismatch'):self.h.run_import()

    def test_failed_publication_is_not_cleanup_eligible_and_retry_recovers(self):
        with patch('providers.mtgjson.factual_retention._write_control',side_effect=OSError('private canary')):
            with self.assertRaisesRegex(SourcePolicyError,'publication unavailable'):self.h.run_import()
        report=json.loads((self.h.workspace/'output/report.json').read_bytes())
        with self.assertRaises(SourcePolicyError):self.verify(report)
        self.assertTrue(self.h.source.exists())
        self.assertEqual(self.h.run_import(),report);self.verify(report)

    def test_failed_directory_durability_before_marker_withholds_cleanup(self):
        with patch('providers.mtgjson.factual_retention._sync_directory',side_effect=OSError('fsync failed')):
            with self.assertRaises(SourcePolicyError):self.h.run_import()
        self.assertFalse((self.h.workspace/'output/publication.json').exists())
        self.verify(self.h.run_import())

    def test_interrupted_control_publication_has_no_marker_and_retries(self):
        import providers.mtgjson.factual_retention as lifecycle
        write=lifecycle._write_control
        def interrupted(path,raw):
            if path.name=='notice.txt':raise OSError('interrupted after provenance')
            return write(path,raw)
        with patch.object(lifecycle,'_write_control',side_effect=interrupted):
            with self.assertRaises(SourcePolicyError):self.h.run_import()
        self.assertTrue((self.h.workspace/'output/provenance.json').exists())
        self.assertFalse((self.h.workspace/'output/publication.json').exists())
        self.verify(self.h.run_import())

    def test_publication_cannot_accept_corrupted_import_output(self):
        report=self.h.run_import();path=self.h.workspace/'output/cards.jsonl'
        path.write_bytes(path.read_bytes()+b'changed')
        with self.assertRaisesRegex(SourcePolicyError,'artifact'):
            publish_factual_results(self.h.workspace,profile=self.h.profile,
                expected_report_id=report['report_id'],provenance=self.h.provenance,notice=self.h.notice)

    def test_import_lock_prevents_concurrent_publication_inspection(self):
        report=self.h.run_import()
        with (self.h.workspace/'.lock').open('rb') as lock:
            fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
            with self.assertRaisesRegex(SourcePolicyError,'workspace busy'):self.verify(report)

    def test_cleanup_verification_refuses_missing_current_permission_before_io(self):
        report=self.h.run_import();self.h.source.unlink()
        self.h.profile=replace(self.h.profile,bases=(replace(self.h.profile.bases[0],operations=()),))
        with patch.object(Path,'open',side_effect=AssertionError('no I/O')):
            with self.assertRaises(SourcePolicyError):self.verify(report)

    def test_bounded_original_fixture_measurement(self):
        report=self.h.run_import();measurement=json.loads((self.h.workspace/'last-run.json').read_bytes())
        self.assertLessEqual(measurement['peak_memory_kib']*1024,report['limits']['memory_bytes'])
        self.assertLessEqual(measurement['seconds'],report['limits']['wall_seconds'])

    def test_output_budget_refusal_preserves_source_and_no_receipt(self):
        with self.assertRaises((SourcePolicyError,ReconciliationError)):
            self.h.run_import(limits=replace(ReconciliationLimits(),output_bytes=1024))
        self.assertTrue(self.h.source.exists())
        self.assertFalse((self.h.workspace/'output/publication.json').exists())

    def test_successful_publication_syncs_before_cleanup_marker(self):
        import providers.mtgjson.factual_retention as lifecycle
        events=[];write=lifecycle._write_control;sync=lifecycle._sync_directory
        def record_write(path,raw):events.append(path.name);return write(path,raw)
        def record_sync(path):events.append('sync-directory');return sync(path)
        with patch.object(lifecycle,'_write_control',side_effect=record_write),patch.object(lifecycle,'_sync_directory',side_effect=record_sync):
            report=self.h.run_import()
        self.assertLess(events.index('sync-directory'),events.index('publication.json'))
        self.verify(report)

    def test_new_nested_workspace_ancestry_is_synced_before_marker(self):
        import providers.mtgjson.factual_retention as lifecycle
        self.h.workspace=self.h.root/'new-parent'/'new-child'/'candidates'
        events=[];sync=lifecycle._sync_directory;write=lifecycle._write_control
        def record_sync(path):events.append(path);return sync(path)
        def record_write(path,raw):events.append(path.name);return write(path,raw)
        with patch.object(lifecycle,'_sync_directory',side_effect=record_sync),patch.object(lifecycle,'_write_control',side_effect=record_write):
            report=self.h.run_import()
        for path in (self.h.workspace,*self.h.workspace.parents):
            self.assertLess(events.index(path),events.index('publication.json'))
        self.verify(report)

    def test_custodian_cleanup_failure_does_not_invalidate_published_results(self):
        report=self.h.run_import();receipt=self.verify(report)
        with patch.object(Path,'unlink',side_effect=OSError('custodian deletion failed')):
            with self.assertRaises(OSError):self.h.source.unlink()
        self.assertTrue(self.h.source.exists());self.assertEqual(self.verify(report),receipt)

    def test_after_custodian_cleanup_only_derived_verification_remains(self):
        report=self.h.run_import();receipt=self.verify(report)
        self.h.source.unlink();self.h.provenance.unlink();self.h.notice.unlink()
        self.assertEqual(self.verify(report),receipt)
        self.assertFalse(receipt['replay']['complete_source_replay_available_without_original'])
        self.assertTrue(receipt['replay']['checkpoint_recovery_requires_original'])
        with self.assertRaises(SourcePolicyError):self.h.run_import()

    def test_each_tampered_artifact_or_control_is_refused_after_cleanup(self):
        report=self.h.run_import();self.h.source.unlink()
        for name in (*report['artifacts'],'report.json','notice.txt','provenance.json','publication.json'):
            path=self.h.workspace/'output'/name;raw=path.read_bytes();path.write_bytes(raw+b'x')
            with self.subTest(name=name),self.assertRaises(SourcePolicyError):self.verify(report)
            path.write_bytes(raw)
        self.verify(report)

    def test_missing_publication_or_artifact_refuses(self):
        report=self.h.run_import()
        for name in ('publication.json','cards.jsonl'):
            path=self.h.workspace/'output'/name;raw=path.read_bytes();path.unlink()
            with self.assertRaises(SourcePolicyError):self.verify(report)
            path.write_bytes(raw);path.chmod(0o600)

    def test_independent_report_and_profile_pins_required(self):
        report=self.h.run_import()
        with self.assertRaises(SourcePolicyError):self.verify(dict(report,report_id='sha256:'+'0'*64))
        self.h.profile=replace(self.h.profile,internal_decision_reference='unreviewed-different-profile')
        with self.assertRaisesRegex(SourcePolicyError,'profile or release'):self.verify(report)

    def test_original_controls_inside_rebuildable_workspace_are_preserved_and_refused(self):
        report=self.h.run_import();output=self.h.workspace/'output'
        before={p.name:p.read_bytes() for p in output.iterdir()}
        self.h.provenance=output/'provenance.json';self.h.notice=output/'notice.txt'
        with self.assertRaisesRegex(SourcePolicyError,'controls must remain outside'):self.h.run_import()
        self.assertEqual({p.name:p.read_bytes() for p in output.iterdir()},before)
        self.verify(report)

    def test_cyclic_workspace_symlink_refuses_without_private_path_diagnostics(self):
        loop=self.h.root/'PRIVATE_PATH_CANARY';loop.symlink_to(loop)
        self.h.workspace=loop
        with self.assertRaises(SourcePolicyError) as error:self.h.run_import()
        self.assertNotIn('PRIVATE_PATH_CANARY',str(error.exception))
        self.assertTrue(self.h.source.exists())

    def test_symlinks_and_nonprivate_outputs_refuse(self):
        report=self.h.run_import();path=self.h.workspace/'output/cards.jsonl';raw=path.read_bytes()
        path.unlink();path.symlink_to(self.h.source)
        with self.assertRaises(SourcePolicyError):self.verify(report)
        path.unlink();path.write_bytes(raw);path.chmod(0o644)
        with self.assertRaises(SourcePolicyError):self.verify(report)

    def test_temporary_publication_symlink_is_not_followed(self):
        report=self.h.run_import()
        (self.h.workspace/'output/notice.txt.tmp').symlink_to(self.h.source)
        with self.assertRaisesRegex(SourcePolicyError,'symlink'):self.verify(report)

    def test_authority_and_export_remain_withheld(self):
        report=self.h.run_import();receipt=self.verify(report)
        for key in ('canonical_admission','production_activation'):self.assertEqual(receipt[key],'NOT_PERFORMED')
        self.assertEqual(receipt['real_card_execution'],'BLOCKED')
        self.assertEqual(receipt['semantic_authority'],'NOT_ESTABLISHED')
        self.assertFalse(receipt['external_ai_export'])
        self.assertEqual(report['catalog_population_completeness'],'NOT_ESTABLISHED')


class LimitedActivationTests(unittest.TestCase):
    def setUp(self):
        self.h=activation.ActivationTests();self.h.setUp();self.addCleanup(self.h.doCleanups)
        self.h.plan=plan_private_activation(self.h.release,source_url=self.h.plan['source_url'],
            acquired_at=self.h.plan['acquired_at'],notice_sha256=self.h.plan['notice_sha256'],
            retention_mode='limited-retention')
        self.h.reviewed_plan_id=self.h.plan['plan_id']
        self.h.bases=tuple(replace(b,operations=tuple(x for x in b.operations if x!='PRIVATE_SOURCE_RETENTION')) for b in self.h.bases)

    def test_existing_activation_runs_explicit_limited_plan(self):
        report=self.h.run_activation()
        self.assertEqual(report['retention_mode'],'limited-retention')
        self.assertTrue((self.h.output/'candidates/output/publication.json').is_file())
        self.assertEqual(validate_activation_plan(self.h.plan),self.h.plan)
        self.assertEqual(report,self.h.run_activation())
        schema=json.loads((Path(__file__).parents[1]/'src/schemas/v1/private-mtgjson-activation-plan-v2.schema.json').read_bytes())
        Draft202012Validator(schema).validate(self.h.plan)

    def test_v1_plan_cannot_silently_inherit_limited_mode(self):
        changed=deepcopy(self.h.plan);changed['schema_version']='private-mtgjson-activation-plan-v1'
        with self.assertRaises(SourcePolicyError):validate_activation_plan(changed)
        changed=deepcopy(self.h.plan);changed['retention_mode']='retained-source'
        with self.assertRaises(SourcePolicyError):validate_activation_plan(changed)

    def test_plan_cli_is_explicit_without_source_reads(self):
        args=[sys.executable,'-m','providers.mtgjson.private_activation','plan']
        for key,value in {'release-id':self.h.release['release_id'],'version':self.h.release['version'],
            'date':self.h.release['date'],'source-sha256':self.h.release['artifact_sha256'],
            'source-url':self.h.plan['source_url'],'acquired-at':self.h.plan['acquired_at'],
            'notice-sha256':self.h.plan['notice_sha256'],'provenance-reference':self.h.release['provenance_reference'],
            'notice-reference':self.h.release['notice_reference'],'retention-mode':'limited-retention'}.items():
            args.extend(['--'+key,value])
        result=subprocess.run(args,env=dict(os.environ,PYTHONPATH='src'),text=True,capture_output=True,check=True)
        self.assertEqual(json.loads(result.stdout),self.h.plan)


if __name__=='__main__':unittest.main()
