"""Synthetic vertical, authority, identity, containment and recovery contracts."""
from copy import deepcopy
from dataclasses import replace
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from canonical_import.mtgjson_factual import (prepare_cohort,FactualAdmissionError,identity,
    assess_factual_publication,engine_binding,stable,validate_cohort_manifest)
from repository.factual_snapshot import (admit_factual_cohort,attach_factual_snapshot,
    verify_factual_snapshot,reopen_factual_snapshot)
from production_evidence.automatic_updates import IsolatedAdmissionTestBoundary
from production_evidence.automatic_updates import AdmissionDecision
from query import CanonicalQueryEngine
from card_intelligence.mechanics import MechanicalCardIntelligence
from factual_admission_fixture import Fixture,document,row,card_key,print_key,alias_key,CANARY


class FactualAdmissionTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name);self.fixture=Fixture(self.root)
        self.boundary=IsolatedAdmissionTestBoundary(self.temp)

    def cohort(self,ids=('existing-receiver',)):
        assessment=self.fixture.assess()
        manifest=prepare_cohort(assessment,list(ids),expected_assessment_id=assessment.report['assessment_id'])
        return assessment,manifest

    def admit(self,assessment,manifest,**changes):
        args=dict(expected_manifest_id=manifest['manifest_id'],review_boundary=self.boundary);args.update(changes)
        return admit_factual_cohort(assessment,manifest,self.root,**args)

    def test_complete_existing_engine_vertical_reuse_new_identity_multiple_printings_and_inspection(self):
        assessment,manifest=self.cohort(('existing-receiver',card_key(2)))
        self.assertEqual(assessment.report['population'],7)
        self.assertEqual(len(manifest['documents']),5)
        published=self.admit(assessment,manifest)
        attached=attach_factual_snapshot(published,expected_snapshot_id=published.receipt['snapshot_id'])
        query=CanonicalQueryEngine.from_attachment(attached)
        self.assertEqual(len(query.entities(entity_type='card')),2)
        self.assertEqual(len(query.related('existing-receiver','card_printings')),2)
        self.assertEqual(query.entity(print_key(2)).canonical_values['card_id'],'existing-receiver')
        with patch.object(MechanicalCardIntelligence,'_initialize',side_effect=AssertionError('blocked reader')):
            result=MechanicalCardIntelligence.inspect_canonical_facts(query,
                expected_query_snapshot_id=query.snapshot().snapshot_id,card_id='existing-receiver')
        self.assertEqual(result['characteristics']['mana_value'],{'status':'known','value':1})
        self.assertEqual(result['characteristics']['power'],{'status':'unknown'})
        self.assertFalse(result['admitted_mechanical_dossier_populated'])
        self.assertEqual(result['real_card_execution'],'BLOCKED')

    def test_matching_oracle_aliases_preserve_existing_identities(self):
        def change(doc):
            for partition in doc['data'].values():
                for row in partition['cards']:
                    row['identifiers']['oracleId']=row['identifiers']['scryfallOracleId']
        fixture=self.changed_fixture(change);assessment=fixture.assess()
        manifest=self.selected(assessment,'existing-receiver')
        self.assertIn('existing-receiver-print',[item['record']['id'] for item in manifest['documents']])

    def test_native_contradictory_oracle_alias_refusal_remains_quarantined(self):
        def change(doc):
            for partition in doc['data'].values():
                for row in partition['cards']:
                    if row['identifiers']['scryfallOracleId']==card_key(1):
                        row['identifiers']['oracleId']=card_key(99)
        fixture=self.changed_fixture(change);assessment=fixture.assess()
        rows=[json.loads(line) for line in (assessment.root/'printing-eligibility.jsonl').read_text().splitlines()]
        affected=[row for row in rows if 'MISSING_PRINTING_IDENTITY_EVIDENCE' in row['reasons']]
        self.assertEqual(len(affected),2)
        self.assertTrue(all(row['disposition']=='QUARANTINED' for row in affected))
        self.assertEqual(len(self.selected(assessment,card_key(2))['documents']),2)

    def test_new_same_name_identity_claims_are_held_without_merging(self):
        fixture=self.changed_fixture(lambda doc:doc['data']['FJA']['cards'][4].update(name='Original Paper Beacon'))
        assessment=fixture.assess()
        rows=[json.loads(line) for line in (assessment.root/'card-eligibility.jsonl').read_text().splitlines()]
        for key in (card_key(2),card_key(5)):
            affected=next(row for row in rows if row['canonical_identity']==key)
            self.assertIn('AMBIGUOUS_NEW_CARD_NAME',affected['reasons'])
            with self.assertRaises(FactualAdmissionError):self.selected(assessment,key)
        self.assertEqual(len(self.selected(assessment,'existing-receiver')['documents']),3)

    def test_independently_established_existing_cards_can_share_a_name(self):
        fixture=self.changed_fixture(lambda doc:doc['data']['FJA']['cards'][4].update(name='Original Paper Beacon'))
        def change(state):
            for cid,key in (('known-beacon',2),('known-other-beacon',5)):
                state['card'][cid]=dict(entity_type='card',values=dict(name='Original Paper Beacon',
                    layout='normal',mana_cost='{1}',card_reference=card_key(key)),superseded_status=False)
        self.change_baseline(fixture,change);assessment=fixture.assess()
        for cid in ('known-beacon','known-other-beacon'):
            self.assertEqual(self.selected(assessment,cid)['selected_card_ids'],[cid])

    def test_operator_root_must_exist_and_publication_syncs_parent_directories(self):
        assessment,manifest=self.cohort()
        missing=self.root/'unprepared-operator'
        with self.assertRaises(FactualAdmissionError):
            admit_factual_cohort(assessment,manifest,missing,
                expected_manifest_id=manifest['manifest_id'],review_boundary=self.boundary)
        self.assertFalse(missing.exists())
        from repository import factual_snapshot as module
        with patch.object(module,'_sync_parent',wraps=module._sync_parent) as synced:
            self.admit(assessment,manifest)
        paths=[call.args[0] for call in synced.call_args_list]
        self.assertGreaterEqual(paths.count(self.root),2)
        self.assertIn(self.root/'snapshots',paths)

    def test_final_operator_root_sync_failure_preserves_verified_recovery_pin(self):
        assessment,manifest=self.cohort()
        from repository import factual_snapshot as module
        destination=self.root/'snapshots'/manifest['manifest_id'][7:]
        original=module._sync_parent
        def fail_final(path):
            if path==self.root and destination.exists():raise OSError('original operator durability failure')
            return original(path)
        with patch.object(module,'_sync_parent',fail_final):
            with self.assertRaises(FactualAdmissionError) as failed:self.admit(assessment,manifest)
        self.assertTrue(destination.exists())
        with patch.object(module.CanonicalPromotionEngine,'promote',side_effect=AssertionError('no re-promotion')):
            published=self.admit(assessment,manifest,expected_existing_snapshot_id=failed.exception.verified_snapshot_id)
        self.assertEqual(published.root,destination)

    def test_publication_tampering_refuses_before_assessment(self):
        path=self.fixture.publication/'output/assertions.jsonl'
        path.write_bytes(path.read_bytes()+b'{}\n')
        with self.assertRaises(FactualAdmissionError):self.fixture.assess()

    def test_differing_optional_card_field_coverage_never_selects_a_row_winner(self):
        fixture=self.changed_fixture(lambda doc:doc['data']['FJA']['cards'][0].update(power='2'))
        assessment=fixture.assess()
        rows=[json.loads(line) for line in (assessment.root/'card-eligibility.jsonl').read_text().splitlines()]
        affected=next(row for row in rows if row['canonical_identity']=='existing-receiver')
        self.assertIn('INCONSISTENT_CARD_FIELD_COVERAGE',affected['reasons'])
        with self.assertRaises(FactualAdmissionError):self.selected(assessment,'existing-receiver')
        self.assertEqual(len(self.selected(assessment,card_key(2))['documents']),2)

    def test_conflicting_and_exceptional_groups_are_held_unrelated_groups_proceed(self):
        assessment=self.fixture.assess()
        self.assertEqual(assessment.report['counts']['card'],{'ELIGIBLE':3,'QUARANTINED':2})
        for cid in (card_key(3),card_key(4)):
            with self.assertRaises(FactualAdmissionError):
                prepare_cohort(assessment,[cid],expected_assessment_id=assessment.report['assessment_id'])
        manifest=prepare_cohort(assessment,[card_key(2)],expected_assessment_id=assessment.report['assessment_id'])
        self.assertEqual(len(manifest['documents']),2)

    def test_no_serialized_approval_or_missing_live_boundary(self):
        assessment,manifest=self.cohort()
        for boundary in (None,{'approved':True},self.boundary.authorize({'repository_root':str(self.root)})):
            with self.assertRaises(FactualAdmissionError):self.admit(assessment,manifest,review_boundary=boundary)
        self.assertFalse((self.root/'.factual-admission-staging').exists())

    def test_idempotent_publication_and_explicit_reopen(self):
        assessment,manifest=self.cohort()
        first=self.admit(assessment,manifest)
        second=self.admit(assessment,manifest,expected_existing_snapshot_id=first.receipt['snapshot_id'])
        self.assertEqual(first.receipt,second.receipt)
        reopened=reopen_factual_snapshot(first.root,expected_snapshot_id=first.receipt['snapshot_id'],
            expected_manifest_id=manifest['manifest_id'],review_boundary=self.boundary)
        self.assertEqual(CanonicalQueryEngine.from_attachment(reopened).entity('existing-receiver').canonical_identity,'existing-receiver')

    def changed_fixture(self,change,name='changed',baseline=True):
        doc=document();change(doc)
        root=self.root/name;root.mkdir(mode=0o700)
        return Fixture(root,source_document=doc,baseline=baseline)

    def selected(self,assessment,cid):
        return prepare_cohort(assessment,[cid],expected_assessment_id=assessment.report['assessment_id'])

    def change_baseline(self,fixture,change):
        path=fixture.base/'canonical/state.json';state=json.loads(path.read_bytes())
        change(state);path.write_text(json.dumps(state))
        fixture.query=CanonicalQueryEngine('magic',games_root=fixture.base/'canonical/games',data_root=fixture.base)

    def test_promoted_assertion_path_prestate_preserves_existing_card_and_printing(self):
        def change(state):
            for entities in state.values():
                for record in entities.values():
                    record['values']={'/'+key:value for key,value in record['values'].items()}
        self.change_baseline(self.fixture,change);assessment=self.fixture.assess()
        manifest=self.selected(assessment,'existing-receiver')
        self.assertIn('existing-receiver-print',[item['record']['id'] for item in manifest['documents']])
        published=self.admit(assessment,manifest)
        query=CanonicalQueryEngine.from_attachment(attach_factual_snapshot(published,
            expected_snapshot_id=published.receipt['snapshot_id']))
        self.assertEqual(query.entity('existing-receiver-print').canonical_values['card_id'],'existing-receiver')

    def test_assertion_path_names_still_hold_name_only_matches(self):
        def change(state):
            state['card']['existing-receiver']['values']={'/name':'Original Paper Beacon','/layout':'normal'}
        self.change_baseline(self.fixture,change);assessment=self.fixture.assess()
        with self.assertRaises(FactualAdmissionError):self.selected(assessment,card_key(2))

    def test_conflicting_plain_and_assertion_path_prestate_refuses(self):
        self.change_baseline(self.fixture,lambda state:state['card']['existing-receiver']['values'].update(
            {'/name':'Original Contradictory Prestate Name'}))
        with self.assertRaises(FactualAdmissionError) as failed:self.fixture.assess()
        self.assertEqual(failed.exception.code,'INVALID_PRESTATE')

    def test_known_absence_is_a_conflict_while_unknown_can_be_filled(self):
        def source_change(doc):
            doc['data']['FJA']['cards'][0]['power']='2'
            doc['data']['FJB']['cards'][0]['power']='2'
        for status in ('known_absent','unknown'):
            fixture=self.changed_fixture(source_change,name=status)
            self.change_baseline(fixture,lambda state:state['card']['existing-receiver']['values'].update(
                power={'status':status}))
            assessment=fixture.assess()
            if status=='known_absent':
                with self.assertRaises(FactualAdmissionError):self.selected(assessment,'existing-receiver')
            else:
                card=next(item['record'] for item in self.selected(assessment,'existing-receiver')['documents']
                    if item['entity_type']=='card')
                self.assertEqual(card['power'],'2')

    def test_internal_knowledge_status_objects_are_not_literal_publisher_facts(self):
        from canonical_import.mtgjson_factual import _documents
        # Deliberately altered original-fixture data exercises the mapping's
        # defensive boundary; it is not represented as a verified publication.
        rows=[json.loads(line) for line in (self.fixture.publication/'output/assertions.jsonl').read_text().splitlines()]
        original=next(row for row in rows if row['card_id']==card_key(2))
        for value in ({'status':'known_absent'},{'status':'known','value':'2'}):
            row=deepcopy(original);row['assertions']['power']=value
            with self.assertRaises(FactualAdmissionError) as failed:_documents(row,card_key(2),print_key(3))
            self.assertEqual(failed.exception.code,'UNSUPPORTED_SOURCE_VALUE')

    def test_existing_printing_fact_disagreement_holds_parent_and_siblings(self):
        for index,change in enumerate(({'rarity':'rare'},{'finish_ids':['foil']},
                {'external_identifiers':{'scryfallId':alias_key(99)}})):
            fixture=self.changed_fixture(lambda doc:None,name='printing-conflict-'+str(index))
            self.change_baseline(fixture,lambda state:state['printing']['existing-receiver-print']['values'].update(change))
            assessment=fixture.assess()
            with self.assertRaises(FactualAdmissionError):self.selected(assessment,'existing-receiver')
            affected=[json.loads(line) for line in (assessment.root/'printing-eligibility.jsonl').read_text().splitlines()
                if json.loads(line)['parent_source_card']==card_key(1)]
            self.assertEqual(len(affected),2)
            self.assertTrue(all(row['disposition']=='QUARANTINED' for row in affected))
            self.assertEqual(len(self.selected(assessment,card_key(2))['documents']),2)

    def test_exact_report_publication_and_profile_pins(self):
        fixture=self.fixture
        cases=[dict(expected_report_id='sha256:'+'0'*64),dict(expected_publication_id='sha256:'+'0'*64),
            dict(profile=replace(fixture.profile,provenance_sha256='0'*64)),
            dict(profile=replace(fixture.profile,retention_mode='retained-source'))]
        for index,change in enumerate(cases):
            args=dict(profile=fixture.profile,expected_report_id=fixture.report['report_id'],
                expected_publication_id=fixture.receipt['publication_id'],canonical_query=fixture.query,
                workspace=self.root/('wrong-'+str(index)));args.update(change)
            with self.assertRaises((FactualAdmissionError,ValueError)):
                assess_factual_publication(fixture.publication,**args)

    def test_archive_is_not_read_and_excluded_fields_are_not_retained(self):
        original=Path.open
        def bounded(path,*args,**kwargs):
            if path==self.fixture.source:raise AssertionError('original archive must not be read')
            return original(path,*args,**kwargs)
        with patch.object(Path,'open',bounded):
            assessment,manifest=self.cohort()
            published=self.admit(assessment,manifest)
        for path in published.root.rglob('*'):
            if path.is_file():self.assertNotIn(CANARY.encode(),path.read_bytes())
        self.assertTrue(self.fixture.source.exists())

    def test_strict_alias_collision_holds_dependency_groups_not_unrelated_cards(self):
        fixture=self.changed_fixture(lambda d:d['data']['FJA']['cards'][1]['identifiers'].update(scryfallId=alias_key(7)))
        assessment=fixture.assess()
        self.assertEqual(assessment.report['counts']['card'],{'ELIGIBLE':1,'QUARANTINED':4})
        for cid in (card_key(2),card_key(5)):
            with self.assertRaises(FactualAdmissionError):self.selected(assessment,cid)
        self.assertEqual(len(self.selected(assessment,'existing-receiver')['documents']),3)

    def test_parent_exception_in_one_occurrence_holds_normal_sibling_printing(self):
        fixture=self.changed_fixture(lambda d:d['data']['FJB']['cards'][0].update(side='a'))
        assessment=fixture.assess()
        with self.assertRaises(FactualAdmissionError):self.selected(assessment,'existing-receiver')
        self.assertEqual(len(self.selected(assessment,card_key(2))['documents']),2)

    def test_collector_collision_is_not_evaded_with_new_namespace(self):
        fixture=self.changed_fixture(lambda d:d['data']['FJA']['cards'][1].update(number='1'))
        assessment=fixture.assess()
        for cid in ('existing-receiver',card_key(2)):
            with self.assertRaises(FactualAdmissionError):self.selected(assessment,cid)
        self.assertNotIn('collector_number_namespace',stable(assessment.report))

    def test_same_name_different_provider_id_is_not_merged_or_duplicated(self):
        fixture=self.changed_fixture(lambda d:d['data']['FJA']['cards'][1].update(name='Original Brass Receiver'))
        assessment=fixture.assess()
        with self.assertRaises(FactualAdmissionError):self.selected(assessment,card_key(2))
        text=(assessment.root/'card-eligibility.jsonl').read_text()
        self.assertIn('NAME_ONLY_MATCH_REQUIRES_REVIEW',text)

    def test_ambiguous_existing_alias_refuses(self):
        path=self.fixture.base/'canonical/state.json';state=json.loads(path.read_text())
        state['card']['ambiguous-receiver']=deepcopy(state['card']['existing-receiver'])
        path.write_text(json.dumps(state))
        assessment=self.fixture.assess()
        with self.assertRaises(FactualAdmissionError):self.selected(assessment,'existing-receiver')
        self.assertIn('AMBIGUOUS_CANONICAL_IDENTITY',(assessment.root/'card-eligibility.jsonl').read_text())

    def test_promoted_identifier_entities_participate_in_crosswalk(self):
        path=self.fixture.base/'canonical/state.json';state=json.loads(path.read_text())
        state['printing']['existing-receiver-print']['values']['uuid']=print_key(991)
        state['identifier']={'existing-alias':dict(entity_type='identifier',values=dict(namespace='scryfallId',
            value=alias_key(1),printing_uuid=print_key(991)))}
        path.write_text(json.dumps(state))
        assessment=self.fixture.assess()
        manifest=self.selected(assessment,'existing-receiver')
        self.assertIn('existing-receiver-print',[x['canonical_identity'] for x in manifest['crosswalk']])

    def test_missing_required_facts_and_unsupported_defense_hold(self):
        for index,change in enumerate((lambda r:r.pop('manaValue'),lambda r:r.update(defense='7'))):
            fixture=self.changed_fixture(lambda d:change(d['data']['FJA']['cards'][1]),name='missing-'+str(index))
            with self.assertRaises(FactualAdmissionError):self.selected(fixture.assess(),card_key(2))

    def test_empty_cost_remains_unknown_not_known_absent(self):
        fixture=self.changed_fixture(lambda d:d['data']['FJA']['cards'][1].update(manaCost=''))
        assessment=fixture.assess();manifest=self.selected(assessment,card_key(2))
        field=next(a for a in manifest['assertions'] if a['path']=='/mana_cost')
        self.assertEqual(field['asserted_value'],{'status':'unknown'})
        self.assertIn('empty-provider-cost-preserves-unknown',field['notes'])
        published=self.admit(assessment,manifest)
        query=CanonicalQueryEngine.from_attachment(attach_factual_snapshot(published,expected_snapshot_id=published.receipt['snapshot_id']))
        result=MechanicalCardIntelligence.inspect_canonical_facts(query,expected_query_snapshot_id=query.snapshot().snapshot_id,card_id=card_key(2))
        self.assertEqual(result['characteristics']['mana_cost'],{'status':'unknown'})

    def test_assertions_have_exact_derivative_field_and_transformation_references(self):
        assessment,manifest=self.cohort()
        for assertion in manifest['assertions']:
            self.assertEqual(assertion['status'],'candidate')
            binding=json.loads(assertion['notes'])['binding']
            self.assertTrue(binding['supports']);self.assertTrue(binding['transformation'])
            for support in binding['supports']:
                self.assertEqual(support['factual_artifact'],'assertions.jsonl')
                self.assertIn('source_record_sha256',support)
                self.assertTrue(support['source_record_pointer'].startswith('/data/'))
                if assertion['path']!='/game':self.assertTrue(support['factual_pointer'].startswith('/'))

    def test_deterministic_reassessment_manifest_and_no_mutation(self):
        first=self.fixture.assess('first');second=self.fixture.assess('second')
        self.assertEqual(first.report,second.report)
        ids=['existing-receiver',card_key(2)];owned=ids[:]
        one=prepare_cohort(first,ids,expected_assessment_id=first.report['assessment_id'])
        two=prepare_cohort(second,list(reversed(ids)),expected_assessment_id=second.report['assessment_id'])
        self.assertEqual(one,two);self.assertEqual(ids,owned)

    def test_index_tamper_and_changed_publication_after_assessment_refuse(self):
        assessment=self.fixture.assess()
        path=assessment.root/'index.sqlite3';raw=path.read_bytes();path.write_bytes(raw+b'altered')
        with self.assertRaises(FactualAdmissionError):self.selected(assessment,card_key(2))
        path.write_bytes(raw)
        output=self.fixture.publication/'output/cards.jsonl';output.write_bytes(output.read_bytes()+b'{}\n')
        with self.assertRaises(FactualAdmissionError):self.selected(assessment,card_key(2))

    def test_stale_prestate_refuses_before_admission(self):
        assessment,manifest=self.cohort()
        path=self.fixture.base/'canonical/state.json';state=json.loads(path.read_text())
        state['card']['existing-receiver']['values']['name']='Original changed evidence'
        path.write_text(json.dumps(state))
        with self.assertRaises(FactualAdmissionError):self.admit(assessment,manifest)
        self.assertFalse((self.root/'.factual-admission-staging').exists())

    def test_tampered_manifest_even_with_recalculated_hash_refuses(self):
        assessment,manifest=self.cohort()
        for field in ('source','crosswalk','assertions','capabilities'):
            value=deepcopy(manifest)
            if isinstance(value[field],dict):value[field]['forged']='unsupported'
            else:value[field].append({'forged':'unsupported'})
            value['manifest_id']=identity({k:v for k,v in value.items() if k!='manifest_id'})
            with self.assertRaises(FactualAdmissionError):self.admit(assessment,value)

    def test_authenticated_decision_fields_cannot_be_substituted(self):
        assessment,manifest=self.cohort()
        class Host:
            authenticated_reviewer='HOST_SESSION_REVIEWER'
            def __init__(self,change):self.change=change
            def authorize(self,bindings):
                return self.change(AdmissionDecision('approved',self.authenticated_reviewer,
                    '2026-11-26T00:00:00Z','canonical-admission',bindings,'host-reviewed-cohort','production'))
        changes=[lambda d:replace(d,decision='pending'),lambda d:replace(d,reviewer='caller'),
            lambda d:replace(d,operation='source-acquisition'),lambda d:replace(d,bindings={}),
            lambda d:replace(d,scope='isolated-test'),lambda d:replace(d,decided_at='2026-11-26'),
            lambda d:d.as_dict()]
        for change in changes:
            with self.assertRaises(FactualAdmissionError):self.admit(assessment,manifest,review_boundary=Host(change))

    def test_serialized_publication_cannot_attach(self):
        assessment,manifest=self.cohort();published=self.admit(assessment,manifest)
        with self.assertRaises(FactualAdmissionError):
            attach_factual_snapshot(published.receipt,expected_snapshot_id=published.receipt['snapshot_id'])
        with self.assertRaises(FactualAdmissionError):
            attach_factual_snapshot(published,expected_snapshot_id='sha256:'+'0'*64)

    def test_snapshot_and_profile_tampering_are_detected(self):
        assessment,manifest=self.cohort();published=self.admit(assessment,manifest)
        attached=attach_factual_snapshot(published,expected_snapshot_id=published.receipt['snapshot_id'])
        marker=published.root/'publication.json';original=marker.read_bytes()
        value=json.loads(original);value['profile']='canonical-snapshot-fictional-v1'
        marker.write_text(json.dumps(value))
        with self.assertRaises(FactualAdmissionError):attached.verify_unchanged()
        marker.write_bytes(original)
        card=next((published.root/'data/canonical/games/magic/cards').glob('*/card.json'))
        value=json.loads(card.read_bytes());value['power']='99';card.write_text(json.dumps(value))
        with self.assertRaises(FactualAdmissionError):attached.verify_unchanged()

    def test_test_snapshot_cannot_be_reopened_as_production(self):
        assessment,manifest=self.cohort();published=self.admit(assessment,manifest)
        class Host:
            authenticated_reviewer='production-host'
            def authorize(self,bindings):return AdmissionDecision('approved',self.authenticated_reviewer,
                '2026-11-26T00:00:00Z','canonical-admission',bindings,'production-review','production')
        with self.assertRaises(FactualAdmissionError):
            reopen_factual_snapshot(published.root,expected_snapshot_id=published.receipt['snapshot_id'],
                expected_manifest_id=manifest['manifest_id'],review_boundary=Host())
        with self.assertRaises(FactualAdmissionError):self.admit(assessment,manifest,
            expected_existing_snapshot_id=published.receipt['snapshot_id'],review_boundary=Host())

    def test_transaction_failure_preserves_generation_for_recovery_and_no_live_switch(self):
        assessment,manifest=self.cohort()
        with patch('repository.canonical.CanonicalRepository.apply_import',side_effect=OSError('original synthetic failure')):
            with self.assertRaises(FactualAdmissionError):self.admit(assessment,manifest)
        self.assertTrue((self.root/'.factual-admission-staging').exists())
        self.assertEqual(list((self.root/'snapshots').iterdir()),[])
        with self.assertRaises(FactualAdmissionError):self.admit(assessment,manifest)

    def test_failure_after_rename_can_be_verified_and_recovered_without_repromotion(self):
        assessment,manifest=self.cohort()
        from repository import factual_snapshot as module
        original=module._sync_parent
        def fail_parent(path):
            if path==self.root/'snapshots':raise OSError('original parent durability failure')
            return original(path)
        with patch.object(module,'_sync_parent',fail_parent):
            with self.assertRaises(FactualAdmissionError) as failed:self.admit(assessment,manifest)
        destination=self.root/'snapshots'/manifest['manifest_id'][7:]
        self.assertTrue(destination.exists())
        with patch.object(module.CanonicalPromotionEngine,'promote',side_effect=AssertionError('no re-promotion')):
            published=self.admit(assessment,manifest,expected_existing_snapshot_id=failed.exception.verified_snapshot_id)
        self.assertEqual(published.root,destination)

    def test_existing_generation_requires_independent_pin_not_its_own_claim(self):
        assessment,manifest=self.cohort();published=self.admit(assessment,manifest)
        for changes in ({},{'expected_existing_snapshot_id':'sha256:'+'0'*64}):
            with self.assertRaises(FactualAdmissionError):self.admit(assessment,manifest,**changes)
        self.assertEqual(self.admit(assessment,manifest,expected_existing_snapshot_id=
            published.receipt['snapshot_id']).receipt,published.receipt)

    def test_coherently_rehashed_assertion_provenance_cannot_replace_approved_evidence(self):
        assessment,manifest=self.cohort();published=self.admit(assessment,manifest)
        card=next((published.root/'data/canonical/games/magic/cards').glob('*/card.json'))
        value=json.loads(card.read_bytes());value['assertions'][0]['notes']='fabricated provenance'
        card.write_text(stable(value)+'\n')
        marker=published.root/'publication.json';receipt=json.loads(marker.read_bytes())
        import hashlib
        receipt['files'][card.relative_to(published.root).as_posix()]={
            'bytes':card.stat().st_size,'sha256':hashlib.sha256(card.read_bytes()).hexdigest()}
        receipt['snapshot_id']=identity({k:v for k,v in receipt.items() if k!='snapshot_id'})
        marker.write_text(stable(receipt)+'\n')
        with self.assertRaises(FactualAdmissionError):verify_factual_snapshot(published.root,
            expected_snapshot_id=receipt['snapshot_id'],expected_manifest_id=manifest['manifest_id'])

    def test_previous_snapshot_preserved_and_rollback_is_explicit_selection(self):
        assessment=self.fixture.assess()
        first_manifest=self.selected(assessment,'existing-receiver');first=self.admit(assessment,first_manifest)
        old={p.relative_to(first.root):p.read_bytes() for p in first.root.rglob('*') if p.is_file()}
        second_manifest=self.selected(assessment,card_key(2))
        self.boundary=IsolatedAdmissionTestBoundary(self.temp)
        second=self.admit(assessment,second_manifest)
        self.assertNotEqual(first.root,second.root)
        prior=CanonicalQueryEngine.from_attachment(attach_factual_snapshot(first,expected_snapshot_id=first.receipt['snapshot_id']))
        self.assertEqual(len(prior.entities(entity_type='card')),1)
        self.assertEqual(old,{p.relative_to(first.root):p.read_bytes() for p in first.root.rglob('*') if p.is_file()})

    def test_private_containment_and_capability_limits(self):
        assessment,manifest=self.cohort();published=self.admit(assessment,manifest)
        attached=attach_factual_snapshot(published,expected_snapshot_id=published.receipt['snapshot_id'])
        query=CanonicalQueryEngine.from_attachment(attached)
        for capability in ('rules_execution','mechanical_semantics','format_legality','external_ai_export'):
            with self.assertRaises(ValueError):query.require_capability(capability)
        for p in [published.root,*published.root.rglob('*')]:self.assertEqual(p.stat().st_mode&0o077,0)
        with self.assertRaises(ValueError):attached.read_bytes(self.fixture.source)
        for invalid in ('Original Brass Receiver',card_key(99)):
            with self.assertRaises(ValueError):MechanicalCardIntelligence.inspect_canonical_facts(query,
                expected_query_snapshot_id=query.snapshot().snapshot_id,card_id=invalid)

    def test_whole_publication_is_not_a_hardcoded_single_cohort(self):
        source=dict(meta=document()['meta'],data={})
        for set_index,code in enumerate(('FQA','FQB')):
            source['data'][code]=dict(code=code,name='Original population '+code,cards=[
                row(set_index*80+i,100+i,'Original Population Gear '+str(i),i) for i in range(1,81)])
        location=self.root/'population';location.mkdir(mode=0o700)
        fixture=Fixture(location,source_document=source,baseline=False);assessment=fixture.assess()
        self.assertEqual(assessment.report['population'],160)
        self.assertEqual(assessment.report['counts']['card'],{'ELIGIBLE':80})
        for cid in (card_key(101),card_key(143),card_key(180)):
            self.assertEqual(len(self.selected(assessment,cid)['documents']),3)

    def test_cohort_bound_refuses_without_silently_truncating(self):
        assessment=self.fixture.assess()
        with self.assertRaises(FactualAdmissionError):
            prepare_cohort(assessment,['not-an-identity']*26,expected_assessment_id=assessment.report['assessment_id'])

    def test_deterministic_row_and_record_budget_refusals(self):
        from canonical_import import mtgjson_factual as module
        for index,changes in enumerate(({'MAX_ROWS':3},{'MAX_ROW_BYTES':8})):
            with patch.multiple(module,**changes):
                with self.assertRaises(FactualAdmissionError) as caught:self.fixture.assess('budget-'+str(index))
            self.assertEqual(caught.exception.code,'RESOURCE_BUDGET')

    def test_malformed_or_oracle_assertion_cannot_enter_factual_index(self):
        from canonical_import.mtgjson_factual import _validate_row
        raw=json.loads((self.fixture.publication/'output/assertions.jsonl').read_text().splitlines()[0])
        for field in ('oracle_text','text','legalities','strategic_role'):
            changed=deepcopy(raw);changed['assertions'][field]='original authored unsupported value'
            with self.assertRaises(FactualAdmissionError):_validate_row(changed)
        changed=deepcopy(raw);changed['mapped_card']['unknown_fields']={'text':CANARY}
        with self.assertRaises(FactualAdmissionError):_validate_row(changed)

    def test_manifest_hard_boundary_rejects_oracle_and_expanded_capabilities(self):
        _,manifest=self.cohort()
        changed=deepcopy(manifest);changed['documents'][0]['record']['oracle_text']=CANARY
        changed['manifest_id']=identity({k:v for k,v in changed.items() if k!='manifest_id'})
        with self.assertRaises(FactualAdmissionError):validate_cohort_manifest(changed)
        changed=deepcopy(manifest);changed['capabilities']['rules_execution']=True
        changed['manifest_id']=identity({k:v for k,v in changed.items() if k!='manifest_id'})
        with self.assertRaises(FactualAdmissionError):validate_cohort_manifest(changed)

    def test_approval_callback_cannot_change_reviewed_prestate(self):
        assessment,manifest=self.cohort()
        original=self.boundary
        path=self.fixture.base/'canonical/state.json'
        class MutatingHost:
            authenticated_reviewer=original.authenticated_reviewer
            def authorize(self,bindings):
                decision=original.authorize(bindings)
                state=json.loads(path.read_text());state['card']['existing-receiver']['values']['name']='Original changed during approval'
                path.write_text(json.dumps(state))
                return decision
        with self.assertRaises(FactualAdmissionError):self.admit(assessment,manifest,review_boundary=MutatingHost())
        self.assertFalse((self.root/'.factual-admission-staging').exists())

    def test_source_profile_cannot_use_project_authorship_for_real_material(self):
        profile=replace(self.fixture.profile,material='MIXED_MTGJSON_RELEASE')
        with self.assertRaises(ValueError):
            assess_factual_publication(self.fixture.publication,profile=profile,
                expected_report_id=self.fixture.report['report_id'],expected_publication_id=self.fixture.receipt['publication_id'],
                canonical_query=self.fixture.query,workspace=self.root/'fake-real')

    def test_factual_aliases_survive_a_private_snapshot_as_selected_prestate(self):
        assessment,manifest=self.cohort();published=self.admit(assessment,manifest)
        query=CanonicalQueryEngine.from_attachment(attach_factual_snapshot(published,expected_snapshot_id=published.receipt['snapshot_id']))
        next_assessment=assess_factual_publication(self.fixture.publication,profile=self.fixture.profile,
            expected_report_id=self.fixture.report['report_id'],expected_publication_id=self.fixture.receipt['publication_id'],
            canonical_query=query,workspace=self.root/'next-assessment')
        next_manifest=self.selected(next_assessment,'existing-receiver')
        self.assertEqual(next_manifest['selected_card_ids'],['existing-receiver'])

    def test_tampered_assertion_value_or_subject_is_rejected(self):
        _,manifest=self.cohort()
        for field,value in [('subject_id',card_key(99)),('asserted_value','original forged factual claim')]:
            changed=deepcopy(manifest);changed['assertions'][0][field]=value
            changed['manifest_id']=identity({k:v for k,v in changed.items() if k!='manifest_id'})
            with self.assertRaises(FactualAdmissionError):validate_cohort_manifest(changed)


if __name__=='__main__':unittest.main()
