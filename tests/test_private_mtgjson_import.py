"""Original fixtures exercise the real parser/validator/mapper/reconciler, not rights clearance."""
from copy import deepcopy
from dataclasses import FrozenInstanceError, replace
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from jsonschema import Draft202012Validator

from providers.mtgjson.private_import import import_private_release
from providers.mtgjson.private_policy import (
    PrivateResearchProfile, SourceUseBasis, SourcePolicyError, OPERATIONS, RETENTION, canonical, digest)
from providers.mtgjson.reconciliation import reconcile_release, ReconciliationError

FIXTURE = Path(__file__).parent/'fixtures/release_reconciliation_v1/original-release.json'
CANARY = 'PRIVATE_EXPRESSIVE_CANARY_861d9'


class PrivateImportTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(dir='/tmp'); self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.source, self.provenance, self.notice = [self.root/x for x in ('source.json','provenance.json','notice.txt')]
        self.workspace = self.root/'private'
        self.document = json.loads(FIXTURE.read_bytes())

    def prepare(self, document=None, bases=None):
        doc = self.document if document is None else document
        self.source.write_text(json.dumps({'meta':doc['meta'],'data':doc['data']})); self.source.chmod(0o600)
        self.release = dict(provider='MTGJSON', release_id='original-private-import-fixture',
            version=doc['meta']['version'], date=doc['meta']['date'], artifact_sha256=digest(self.source.read_bytes()),
            provenance_reference='original-fixture-acquisition', notice_reference='original-fixture-notice')
        self.provenance.write_text(canonical({k:v for k,v in self.release.items() if k not in
            ('provenance_reference','notice_reference')} | dict(source_url='urn:mtglab:original:private-import',
                acquired_at='2026-11-22T12:00:00Z', acquisition_method='MANUALLY_SUPPLIED')))
        self.notice.write_text('Original project-authored fictional test data. Not licensed real Magic evidence.\n')
        for path in (self.provenance,self.notice): path.chmod(0o600)
        basis = SourceUseBasis('original-fixture-authorship', digest(b'Original project test authorship'),
            'PROJECT_AUTHORSHIP', 'COMPLETE_ARTIFACT', OPERATIONS, 'SUPPORTED')
        self.profile = PrivateResearchProfile.for_release(self.release,
            provenance_sha256=digest(self.provenance.read_bytes()), notice_sha256=digest(self.notice.read_bytes()),
            bases=(basis,) if bases is None else bases, internal_decision_reference='owner-private-research-v1',
            material='ORIGINAL_PROJECT_FIXTURE')

    def run_import(self, **kwargs):
        return import_private_release(self.source,self.workspace,profile=self.profile,
            provenance=self.provenance,notice=self.notice, **kwargs)

    def test_complete_private_import_reuses_owning_components_and_replays(self):
        self.prepare(); before = deepcopy(self.release); original = self.source.read_bytes()
        report = self.run_import()
        self.assertEqual(report['schema_version'],'private-mtgjson-import-report-v1')
        self.assertEqual((report['total_source_rows'],report['unique_supported_card_identities'],
                          report['distinct_printing_identities']),(4,3,4))
        self.assertEqual(report['retention_profile'],RETENTION)
        self.assertEqual(report['canonical_admission'],'NOT_PERFORMED')
        self.assertEqual(report['production_activation'],'NOT_PERFORMED')
        self.assertEqual(report['real_card_execution'],'BLOCKED')
        self.assertEqual(report['catalog_population_completeness'],'NOT_ESTABLISHED')
        self.assertEqual(report['source_use_status'],'HOST_SCOPED_DISPOSITION_NOT_EXTERNAL_LICENSE')
        schema=json.loads((Path(__file__).parents[1]/'src/schemas/v1/private-mtgjson-import-report.schema.json').read_bytes())
        Draft202012Validator(schema).validate(report)
        self.assertEqual(self.run_import(),report)
        self.assertEqual(json.loads((self.workspace/'output/report.json').read_bytes()),report)
        self.assertEqual(self.release,before); self.assertEqual(self.source.read_bytes(),original)
        self.assertNotIn(str(self.root),canonical(report))
        self.assertFalse(any(p.name=='source.json' for p in self.workspace.rglob('*')))

    def test_no_expressive_unknown_or_third_party_fields_in_any_private_artifact(self):
        self.document['meta']['extra']=CANARY
        self.document['data']['QRA']['set_prose']=CANARY
        raw=self.document['data']['QRA']['cards'][0]
        for key in ('text','flavorText','rulings','foreignData','purchaseUrls','edhrecRank','unknown_blob'):
            raw[key]=CANARY
        raw['identifiers']['unsupported-provider']=CANARY
        self.prepare(); self.run_import()
        for path in self.workspace.rglob('*'):
            if path.is_file(): self.assertNotIn(CANARY.encode(),path.read_bytes(),path.name)
        rows=[json.loads(x) for x in (self.workspace/'output/assertions.jsonl').read_text().splitlines()]
        self.assertEqual(rows[0]['omitted_field_count'],8)
        for row in rows:
            for key in ('mapped_card','mapped_printing'):
                if row[key]: self.assertEqual(row[key]['unknown_fields'],{})

    def test_factual_conflicts_withhold_candidates(self):
        self.document['data']['QRB']['cards'][0]['manaCost']='{8}'
        self.prepare(); report=self.run_import()
        self.assertEqual(report['conflicting_card_fields'],1)
        candidates=[json.loads(x) for x in (self.workspace/'output/printings.jsonl').read_text().splitlines()]
        self.assertEqual(sum(x['candidate_status']=='WITHHELD' for x in candidates),2)

    def test_duplicate_differing_only_in_excluded_text_still_withheld(self):
        row=deepcopy(self.document['data']['QRA']['cards'][0]); row['text']=CANARY
        self.document['data']['QRA']['cards'].append(row)
        self.prepare(); report=self.run_import()
        self.assertEqual(report['duplicate_printing_identities'],1)
        self.assertEqual(report['conflicting_printing_identities'],1)
        self.assertNotIn(CANARY,(self.workspace/'output/assertions.jsonl').read_text())

    def test_missing_or_ambiguous_identities_remain_unresolved(self):
        self.document['data']['QRA']['cards'][0]['identifiers']={}
        self.document['data']['QRB']['cards'][0]['identifiers']['oracleId']='different-card'
        self.prepare(); report=self.run_import()
        self.assertEqual(report['unresolved_identity_records'],2)

    def test_paused_resume_and_fresh_run_have_identical_reports(self):
        self.prepare(); pause=self.run_import(stop_after_partitions=1)
        self.assertEqual(pause['status'],'PAUSED')
        resumed=self.run_import(); self.workspace=self.root/'fresh'
        self.assertEqual(self.run_import(),resumed)

    def test_missing_whole_read_grant_refuses_before_any_open(self):
        self.prepare(); basis=replace(self.profile.bases[0],operations=tuple(x for x in OPERATIONS if x!='WHOLE_ARTIFACT_READ'))
        self.profile=replace(self.profile,bases=(basis,))
        with patch.object(Path,'open',side_effect=AssertionError('must refuse before I/O')):
            with self.assertRaisesRegex(SourcePolicyError,'WHOLE_ARTIFACT_READ'): self.run_import()
        self.assertFalse(self.workspace.exists())

    def test_each_operation_is_independently_required(self):
        self.prepare()
        for operation in OPERATIONS:
            with self.subTest(operation=operation):
                profile=replace(self.profile,bases=(replace(self.profile.bases[0],
                    operations=tuple(x for x in OPERATIONS if x!=operation)),))
                with self.assertRaisesRegex(SourcePolicyError,operation): profile.require_supported()

    def test_factual_retention_does_not_authorize_whole_mixed_read(self):
        self.prepare(); profile=replace(self.profile,bases=(replace(self.profile.bases[0],material_scope='FACTUAL_PROJECTION'),))
        with self.assertRaisesRegex(SourcePolicyError,'WHOLE_ARTIFACT_READ'): profile.require_supported()

    def test_internal_risk_policy_cannot_manufacture_external_rights(self):
        self.prepare(); self.profile=replace(self.profile,bases=(replace(self.profile.bases[0],kind='INTERNAL_POLICY'),))
        with self.assertRaises(SourcePolicyError): self.run_import()

    def test_publisher_controlled_grant_does_not_inherit_to_mixed_artifact(self):
        self.prepare(); self.profile=replace(self.profile,material='MIXED_MTGJSON_RELEASE',bases=(
            replace(self.profile.bases[0],kind='PUBLISHER_PERMISSION',material_scope='PUBLISHER_CONTROLLED_ONLY'),))
        with self.assertRaises(SourcePolicyError): self.run_import()

    def test_fixture_authorship_cannot_be_relabelled_as_real_source_authority(self):
        self.prepare(); self.profile=replace(self.profile,material='MIXED_MTGJSON_RELEASE')
        with self.assertRaises(SourcePolicyError): self.run_import()

    def test_unestablished_and_express_restrictions_refuse(self):
        self.prepare()
        for state in ('NOT_ESTABLISHED','EXPRESSLY_RESTRICTED'):
            self.profile=replace(self.profile,bases=(replace(self.profile.bases[0],disposition=state),))
            with self.assertRaises(SourcePolicyError): self.run_import()

    def test_restriction_is_not_overridden_by_another_supported_basis(self):
        self.prepare(); self.profile=replace(self.profile,bases=(self.profile.bases[0],replace(
            self.profile.bases[0],reference='restricted-evidence',disposition='EXPRESSLY_RESTRICTED')))
        with self.assertRaises(SourcePolicyError): self.run_import()

    def test_missing_profile_and_data_supplied_approval_cannot_authorize(self):
        self.prepare()
        for profile in (None,True,{'approved':True,'private_use':True}):
            with self.assertRaises(SourcePolicyError): import_private_release(self.source,self.workspace,
                profile=profile,provenance=self.provenance,notice=self.notice)

    def test_tampered_source_provenance_and_notice_refuse(self):
        for name in ('source','provenance','notice'):
            with self.subTest(name=name):
                self.prepare(); path=getattr(self,name); path.write_bytes(path.read_bytes()+b' ')
                with self.assertRaises((SourcePolicyError,ReconciliationError)): self.run_import()

    def test_coherently_rehashed_but_inconsistent_provenance_refuses(self):
        self.prepare(); facts=json.loads(self.provenance.read_bytes()); facts['version']='5.9.9'
        self.provenance.write_text(canonical(facts))
        self.profile=replace(self.profile,provenance_sha256=digest(self.provenance.read_bytes()))
        with self.assertRaisesRegex(SourcePolicyError,'release mismatch'): self.run_import()

    def test_nonmanual_acquisition_and_malformed_controls_refuse(self):
        self.prepare()
        facts=json.loads(self.provenance.read_bytes());facts['acquisition_method']='AUTOMATIC'
        self.provenance.write_text(canonical(facts))
        self.profile=replace(self.profile,provenance_sha256=digest(self.provenance.read_bytes()))
        with self.assertRaisesRegex(SourcePolicyError,'manual source'): self.run_import()
        for raw in (b'{}',b'{"x":1,"x":2}',b'[]',b'x'*65537):
            self.provenance.write_bytes(raw)
            self.profile=replace(self.profile,provenance_sha256=digest(raw))
            with self.assertRaises(SourcePolicyError): self.run_import()

    def test_private_inputs_symlinks_git_and_permissions(self):
        self.prepare(); self.source.chmod(0o644)
        with self.assertRaises(SourcePolicyError): self.run_import()
        self.source.chmod(0o600); link=self.root/'link'; link.symlink_to(self.source)
        with self.assertRaises(SourcePolicyError): import_private_release(link,self.workspace,
            profile=self.profile,provenance=self.provenance,notice=self.notice)
        (self.root/'.git').mkdir(); (self.root/'.git/HEAD').write_text('ref: refs/heads/fixture\n')
        with self.assertRaises(SourcePolicyError): self.run_import()

    def test_profile_is_immutable_and_receipts_are_independent(self):
        self.prepare()
        with self.assertRaises(FrozenInstanceError): self.profile.material='anything'
        receipt=self.profile.receipt(); receipt['bases'][0]['operations'].clear()
        self.assertEqual(len(self.profile.receipt()['bases'][0]['operations']),len(OPERATIONS))

    def test_profile_cannot_authorize_legacy_full_retention_or_set_preparation(self):
        self.prepare()
        with self.assertRaises(ReconciliationError): reconcile_release(self.source,self.workspace,self.release,
            authorize_source=self.profile)
        self.assertFalse(self.profile(dict(operation='private-set-candidate-preparation-v1',
            artifact_sha256=self.release['artifact_sha256'],manifest_sha256='0'*64,request_sha256='0'*64)))

    def test_export_canonical_and_wrong_release_bindings_refuse(self):
        from dataclasses import asdict
        from providers.mtgjson.reconciliation import OPERATION,ReconciliationLimits
        self.prepare()
        binding=dict(operation=OPERATION,release=self.release,limits=asdict(ReconciliationLimits()),
            whole_artifact_read=True,private_source_and_derived_retention=True,public_export=False,
            canonical_admission=False,retention_profile=RETENTION,source_use_receipt=self.profile.receipt())
        self.assertTrue(self.profile(binding))
        for key,value in (('public_export',True),('canonical_admission',True),('external_ai_export',True),
                          ('retention_profile','all-fields'),('whole_artifact_read',False)):
            altered=deepcopy(binding); altered[key]=value; self.assertFalse(self.profile(altered))
        altered=deepcopy(binding); altered['release']['artifact_sha256']='0'*64
        self.assertFalse(self.profile(altered))

    def test_changed_profile_cannot_resume_old_checkpoint(self):
        self.prepare(); self.run_import(stop_after_partitions=1)
        self.profile=replace(self.profile,internal_decision_reference='different-owner-decision')
        with self.assertRaisesRegex(ReconciliationError,'workspace binding mismatch'): self.run_import()

    def test_invalid_supported_field_types_are_not_retained_as_fact_payloads(self):
        for key,value in (('type',{'prose':CANARY}),('manaValue',True),('colors',[{'prose':CANARY}])):
            with self.subTest(field=key):
                doc=deepcopy(self.document);doc['data']['QRA']['cards'][0][key]=value
                self.prepare(doc)
                with self.assertRaises(ReconciliationError): self.run_import()
                for path in self.workspace.rglob('*'):
                    if path.is_file(): self.assertNotIn(CANARY.encode(),path.read_bytes())

    def test_native_set_preparation_cannot_inherit_this_narrower_profile(self):
        from test_set_preparation import sample,manifest
        from ingestion.set_preparation import prepare_set_candidates,SetPreparationError,canonical_json
        self.prepare(); doc,request=sample();payload=canonical_json(doc).encode()
        with self.assertRaises(SetPreparationError) as refusal:
            prepare_set_candidates(payload,manifest(payload),request,game='fixture-game',
                                   games_root=self.root/'no-catalog',authorize_source=self.profile)
        self.assertEqual(refusal.exception.code,'SOURCE_POLICY_REFUSAL')

    def test_private_source_permissions_and_notice_are_rechecked_on_replay(self):
        self.prepare(); self.run_import()
        self.notice.write_text('altered source notice')
        with self.assertRaises(SourcePolicyError): self.run_import()

    def test_incomplete_basis_and_scope_values_are_refused(self):
        self.prepare()
        for basis in (replace(self.profile.bases[0],sha256='not-a-hash'),
                      replace(self.profile.bases[0],operations=('EXPORT_AI',)),
                      replace(self.profile.bases[0],material_scope='all-content')):
            with self.assertRaises(SourcePolicyError): replace(self.profile,bases=(basis,)).require_supported()


if __name__=='__main__': unittest.main()
