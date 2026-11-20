"""Original synthetic complete-set census, quarantine and authority regressions."""
import copy
from hashlib import sha256
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from ingestion.set_preparation import (INPUT_VERSION, MAX_BYTES, MAX_ROWS, SetPreparationError,
    canonical_json, prepare_set_candidates)

FIXTURES = Path(__file__).parent / 'fixtures/set_preparation_v1'


def provenance(record, source='fixture-source'):
    record['provenance']=[dict(source_id=source,field_paths=sorted(set(record)-{'schema_version','provenance'}),claim='Original synthetic fixture facts')]
    return record


def card(identifier='shared-fixture-card', name='Workshop Compass Cairn'):
    return provenance(dict(schema_version='v1',id=identifier,game='fixture-game',name=name,layout='normal',oracle_id='synthetic-oracle-'+identifier))


def row(record, kind):
    return dict(id='row-'+record['id'],entity_type=kind,normalized=record,
                identifiers=dict(canonical_identifier=record['id'],provider_identifier='original:'+record['id']))


def sample(code='FJA'):
    new_id='new-'+code.lower()
    cards=[card(),card(new_id,'Independent Ribbon Relay '+code)]
    rows=[row(c,'card') for c in cards]
    for n,c in enumerate(cards):
        p=provenance(dict(schema_version='v1',id='print-'+code.lower()+'-'+str(n),card_id=c['id'],set_code=code,collector_number=str(n+1),rarity='fictional'))
        rows.append(row(p,'printing'))
    request=dict(schema_version=INPUT_VERSION,set_code=code,inventory_reference='original-authored-population-'+code,
                 expected_inventory=[dict(entity_type=r['entity_type'],id=r['normalized']['id']) for r in rows])
    return dict(records=rows),request


def manifest(payload):
    return dict(manifest_schema='external-dataset-manifest-v1',dataset_name='Original synthetic set',logical_identity='fixture-source',
        version='1',provider='Original MTG Lab fixture author',publication_date='2026-11-20',
        source_attribution='Independently authored fictional records; not Magic data',license='Original project-authored synthetic test material',
        expected_entity_types=['card','printing'],schema_version='supplied-canonical-records-v1',checksum=sha256(payload).hexdigest(),data_file='records.json')


class SetPreparationTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name); game=self.root/'fixture-game'
        p=game/'cards/shared-fixture-card/card.json';p.parent.mkdir(parents=True);p.write_text(canonical_json(card()))
        p=game/'sources/fixture-source.json';p.parent.mkdir(parents=True)
        p.write_text(canonical_json(dict(schema_version='v1',id='fixture-source',title='Original fixture source',source_classification='internal',
            provider='MTG Lab test author',source_location='internal-original-synthetic',access_date='2026-11-20',verification_status='confirmed',
            claims=['Original fictional test records only'],record_version='1')))

    def run_case(self, doc=None, request=None, *, authorize=True, supplied_manifest=None):
        original, default=sample();doc=original if doc is None else doc;request=default if request is None else request
        payload=(canonical_json(doc)+'\n').encode();m=manifest(payload) if supplied_manifest is None else supplied_manifest
        # Test-host disposition authorizes only these exact independently authored
        # bytes and their manifest. No caller-supplied license is promoted.
        binding_hash=sha256(payload).hexdigest()
        def host(bindings):
            return authorize is True and bindings['operation']=='private-set-candidate-preparation-v1' and bindings['artifact_sha256']==binding_hash
        return prepare_set_candidates(payload,m,request,game='fixture-game',games_root=self.root,authorize_source=host)

    def test_two_original_sets_same_consumer_new_card_and_reprint(self):
        for code in ('FJA','FJB'):
            doc,request=sample(code);r=self.run_case(doc,request)
            self.assertEqual(r['declared_completeness']['status'],'COMPLETE_DECLARED_INVENTORY')
            self.assertEqual(r['file_coverage']['accounted_rows'],4)
            self.assertEqual(len(r['candidates']),4)
            self.assertEqual([x['catalog_relation'] for x in r['rows'][:2]],['EXISTING_IDENTICAL_CONTENT','NEW_DECLARED_IDENTITY'])
            self.assertEqual(r['canonical_admission'],dict(status='NOT_PERFORMED',approved_count=0))
            self.assertEqual(r['real_world_set_completeness'],'NOT_ESTABLISHED')

    def test_incomplete_population_still_has_complete_file_coverage(self):
        doc,request=sample();doc['records'].pop()
        r=self.run_case(doc,request)
        self.assertEqual(r['file_coverage']['status'],'ALL_SOURCE_ROWS_ACCOUNTED')
        self.assertEqual(len(r['declared_completeness']['missing']),1)
        self.assertEqual(r['declared_completeness']['status'],'INCOMPLETE_OR_CONTRADICTORY')

    def test_unexpected_record_is_not_dropped(self):
        doc,request=sample();doc['records'].append(row(card('unexpected','Original Unexpected Spindle'),'card'))
        r=self.run_case(doc,request)
        self.assertEqual(r['declared_completeness']['unexpected'],[dict(entity_type='card',id='unexpected')])
        self.assertEqual(r['file_coverage']['accounted_rows'],5)

    def test_unknown_inventory_is_not_an_empty_or_complete_inventory(self):
        doc,request=sample();request['expected_inventory']=None
        r=self.run_case(doc,request)
        self.assertEqual(r['declared_completeness']['status'],'UNKNOWN')
        self.assertIsNone(r['declared_completeness']['expected'])

    def test_duplicate_printing_quarantines_every_copy(self):
        doc,request=sample();doc['records'].append(copy.deepcopy(doc['records'][-1]))
        r=self.run_case(doc,request)
        self.assertEqual(r['duplicates'][0]['source_rows'],2)
        self.assertTrue(all(r['rows'][i]['disposition']=='QUARANTINED' for i in (3,4)))
        self.assertNotIn(3,r['accepted_candidate_rows'])

    def test_conflicting_printing_and_row_ids_fail_closed(self):
        doc,request=sample();duplicate=copy.deepcopy(doc['records'][-1]);duplicate['normalized']['card_id']='shared-fixture-card'
        doc['records'].append(duplicate);r=self.run_case(doc,request)
        self.assertEqual(r['rows'][3]['disposition'],'QUARANTINED');self.assertEqual(r['rows'][4]['disposition'],'QUARANTINED')

    def test_alias_collision_is_owned_by_existing_resolver(self):
        doc,request=sample()
        for entry in doc['records'][:2]:entry['identifiers']['external_identifiers']=['original:collision']
        r=self.run_case(doc,request)
        self.assertTrue(r['identity_conflicts']['aliases'])
        self.assertEqual(r['candidates'],[])

    def test_catalog_oracle_conflict_does_not_become_a_new_card(self):
        doc,request=sample();doc['records'][1]['normalized']['oracle_id']=card()['oracle_id']
        r=self.run_case(doc,request)
        self.assertTrue(r['identity_conflicts']['aliases'])
        self.assertEqual(r['rows'][1]['disposition'],'QUARANTINED')

    def test_altered_existing_card_content_is_catalog_conflict(self):
        doc,request=sample();doc['records'][0]['normalized']['name']='Conflicting original label'
        r=self.run_case(doc,request)
        self.assertEqual(r['identity_conflicts']['catalog_rows'],[0]);self.assertEqual(r['candidates'],[])

    def test_missing_identity_is_unknown_and_withholds_batch(self):
        doc,request=sample();del doc['records'][0]['normalized']['id']
        r=self.run_case(doc,request)
        self.assertEqual(r['declared_completeness']['status'],'UNKNOWN')
        self.assertEqual(r['unresolved_identity_rows'],[0]);self.assertEqual(r['candidates'],[])

    def test_multiface_is_unresolved_not_silently_flattened(self):
        doc,request=sample();doc['records'][1]['normalized']['layout']='transform'
        r=self.run_case(doc,request)
        self.assertEqual(r['unresolved_multiface_rows'],[1]);self.assertEqual(r['candidates'],[])

    def test_foreign_printing_and_missing_card_dependency(self):
        for mode in ('foreign','missing'):
            doc,request=sample();p=doc['records'][-1]['normalized']
            if mode=='foreign':p['set_code']='OTHER'
            else:p['card_id']='not-declared'
            r=self.run_case(doc,request)
            self.assertEqual(r['rows'][-1]['disposition'],'QUARANTINED')

    def test_invalid_schema_is_accounted_without_source_text_diagnostics(self):
        doc,request=sample();doc['records'][1]['normalized']['unreviewed']='PRIVATE_SOURCE_CANARY'
        r=self.run_case(doc,request)
        self.assertEqual(r['file_coverage']['source_rows'],4);self.assertEqual(r['candidates'],[])
        self.assertNotIn('PRIVATE_SOURCE_CANARY',canonical_json(r))

    def test_source_policy_refusal_and_no_default_clearance(self):
        with self.assertRaises(SetPreparationError) as c:self.run_case(authorize=False)
        self.assertEqual(c.exception.code,'SOURCE_POLICY_REFUSAL')
        doc,request=sample();payload=canonical_json(doc).encode()
        with self.assertRaises(SetPreparationError) as c:
            prepare_set_candidates(payload,manifest(payload),request,game='fixture-game',games_root=self.root)
        self.assertEqual(c.exception.code,'SOURCE_POLICY_REFUSAL')

    def test_license_and_user_supplied_flags_cannot_authorize(self):
        doc,request=sample();payload=(canonical_json(doc)+'\n').encode();m=manifest(payload);m['permission_granted']=True
        with self.assertRaises(SetPreparationError):self.run_case(doc,request,supplied_manifest=m)
        m=manifest(payload);m['license']='GRANTED'
        with self.assertRaises(SetPreparationError) as c:self.run_case(doc,request,authorize=False,supplied_manifest=m)
        self.assertEqual(c.exception.code,'SOURCE_POLICY_REFUSAL')

    def test_altered_hash_and_invalid_manifest(self):
        for field,value in (('checksum','0'*64),('data_file','../source.json'),('publication_date','bad'),('provider','')):
            doc,request=sample();m=manifest(canonical_json(doc).encode());m[field]=value
            with self.subTest(field=field),self.assertRaises(SetPreparationError):self.run_case(doc,request,supplied_manifest=m)

    def test_forged_completeness_and_duplicate_inventory_reject(self):
        for mode in ('flag','duplicate','unknown-type'):
            doc,request=sample()
            if mode=='flag':request['complete']=True
            elif mode=='duplicate':request['expected_inventory'].append(request['expected_inventory'][0])
            else:request['expected_inventory'][0]['entity_type']='set'
            with self.assertRaises(SetPreparationError):self.run_case(doc,request)

    def test_deterministic_replay_immutable_inputs_and_no_repository_writes(self):
        doc,request=sample();before=copy.deepcopy((doc,request));files={p.relative_to(self.root):p.read_bytes() for p in self.root.rglob('*') if p.is_file()}
        a=self.run_case(doc,request);b=self.run_case(doc,request)
        self.assertEqual(a,b);self.assertEqual((doc,request),before)
        self.assertEqual(files,{p.relative_to(self.root):p.read_bytes() for p in self.root.rglob('*') if p.is_file()})
        self.assertEqual(a['source_use']['publication'],'NOT_AUTHORIZED');self.assertFalse(a['real_card_execution_authorized'])

    def test_catalog_drift_refuses_report(self):
        from repository.cards import canonical_repository_bytes
        original=canonical_repository_bytes('fixture-game',games_root=self.root)
        changed=json.loads(original);changed['cards'][0]['name']='Changed catalog fixture'
        successor=(canonical_json(changed)+'\n').encode()
        with patch('ingestion.set_preparation.canonical_repository_bytes',side_effect=[original,successor]):
            with self.assertRaises(SetPreparationError) as c:self.run_case()
        self.assertEqual(c.exception.code,'CATALOG_DRIFT')

    def test_json_duplicate_keys_and_nonfinite_reject(self):
        _,request=sample()
        for payload in (b'{"records":[],"records":[]}',b'{"records":[NaN]}',b'\xff'):
            with self.assertRaises(SetPreparationError):
                prepare_set_candidates(payload,manifest(payload),request,game='fixture-game',games_root=self.root,authorize_source=lambda _:True)

    def test_resource_bounds_before_processing(self):
        _,request=sample()
        with self.assertRaises(SetPreparationError):prepare_set_candidates(b'x'*(MAX_BYTES+1),{},request,game='fixture-game',games_root=self.root)
        doc,request=sample();doc['records']*=501
        with self.assertRaises(SetPreparationError):self.run_case(doc,request)

    def test_coherently_rehashed_source_and_changed_inventory_require_new_host_disposition(self):
        doc,request=sample();payload=(canonical_json(doc)+'\n').encode();m=manifest(payload)
        observed=[]
        def original_host(bindings): observed.append(copy.deepcopy(bindings)); return True
        prepare_set_candidates(payload,m,request,game='fixture-game',games_root=self.root,authorize_source=original_host)
        expected=observed[0]
        for change in ('source','inventory','manifest'):
            d=copy.deepcopy(doc);r=copy.deepcopy(request);new_m=copy.deepcopy(m)
            if change=='source':d['records'][1]['normalized']['name']='Changed original label'
            if change=='inventory':r['expected_inventory'].pop()
            if change=='manifest':new_m['source_attribution']='Different provenance assertion'
            raw=(canonical_json(d)+'\n').encode();new_m['checksum']=sha256(raw).hexdigest()
            with self.subTest(change=change),self.assertRaises(SetPreparationError) as c:
                prepare_set_candidates(raw,new_m,r,game='fixture-game',games_root=self.root,authorize_source=lambda b:b==expected)
            self.assertEqual(c.exception.code,'SOURCE_POLICY_REFUSAL')

    def test_host_exceptions_nonboolean_and_mutation_cannot_grant_or_change_bindings(self):
        doc,request=sample();payload=canonical_json(doc).encode();m=manifest(payload)
        def broken(_):raise RuntimeError('private path canary')
        for host in (broken,lambda _:1,lambda _:'GRANTED'):
            with self.assertRaises(SetPreparationError) as c:
                prepare_set_candidates(payload,m,request,game='fixture-game',games_root=self.root,authorize_source=host)
            self.assertEqual(c.exception.code,'SOURCE_POLICY_REFUSAL');self.assertNotIn('canary',str(c.exception))
        def mutating(b):b.clear();return True
        r=prepare_set_candidates(payload,m,request,game='fixture-game',games_root=self.root,authorize_source=mutating)
        self.assertEqual(r['bindings']['artifact_sha256'],sha256(payload).hexdigest())

    def test_invalid_manifest_types_profile_and_empty_expected_inventory(self):
        doc,request=sample();payload=(canonical_json(doc)+'\n').encode()
        for key,value in (('notes',{}),('schema_version','unsupported'),('expected_entity_types',True),('checksum',True)):
            m=manifest(payload);m[key]=value
            with self.assertRaises(SetPreparationError):self.run_case(doc,request,supplied_manifest=m)
        request['expected_inventory']=[]
        with self.assertRaises(SetPreparationError):self.run_case(doc,request)

    def test_conflicting_existing_printing_not_silently_replaced(self):
        doc,request=sample();record=copy.deepcopy(doc['records'][-1]['normalized'])
        # Existing Printing legitimately points to the already-present Card.
        record['card_id']='shared-fixture-card'
        p=self.root/'fixture-game/printings'/record['id']/'printing.json';p.parent.mkdir(parents=True);p.write_text(canonical_json(record))
        result=self.run_case(doc,request)
        self.assertIn(3,result['identity_conflicts']['catalog_rows']);self.assertEqual(result['candidates'],[])

    def test_missing_layout_is_unresolved_not_assumed_normal(self):
        doc,request=sample();del doc['records'][1]['normalized']['layout']
        r=self.run_case(doc,request)
        self.assertEqual(r['unresolved_multiface_rows'],[1]);self.assertEqual(r['candidates'],[])

    def test_unsupported_manifest_data_is_structured_refusal(self):
        doc,request=sample();m=manifest((canonical_json(doc)+'\n').encode());m['notes']={1,2}
        with self.assertRaises(SetPreparationError) as c:self.run_case(doc,request,supplied_manifest=m)
        self.assertEqual(c.exception.code,'INVALID_MANIFEST')

    def test_unknown_identity_rows_do_not_expose_unbounded_labels(self):
        doc,request=sample();doc['records'][1]['normalized']['id']='x'*129
        r=self.run_case(doc,request)
        self.assertEqual(r['unresolved_identity_rows'],[1]);self.assertEqual(r['candidates'],[])

    def test_catalog_comparisons_use_the_exact_bound_snapshot_bytes(self):
        doc,request=sample()
        doc['records'][0]['normalized']['name']='Bound snapshot original label'
        bound_card=copy.deepcopy(doc['records'][0]['normalized'])
        bound=(canonical_json(dict(schema_version='v1',game='fixture-game',cards=[bound_card],printings=[]))+'\n').encode()
        # The independent reader still exposes the earlier valid catalog.
        # A report bound to the later bytes must not compare against that reader.
        with patch('ingestion.set_preparation.canonical_repository_bytes',return_value=bound):
            r=self.run_case(doc,request)
        self.assertEqual(r['rows'][0]['catalog_relation'],'EXISTING_IDENTICAL_CONTENT')
        self.assertEqual(r['bindings']['catalog_sha256'],sha256(bound).hexdigest())
        self.assertEqual(len(r['candidates']),4)

    def test_retained_original_fixtures_replay(self):
        for code in ('FJA','FJB'):
            packet=json.loads((FIXTURES/(code+'.json')).read_bytes())
            self.assertEqual(self.run_case(packet['source'],packet['request']),self.run_case(*sample(code)))


if __name__=='__main__':unittest.main()
