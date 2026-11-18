"""Real owning APIs over isolated fictional inventory; no production collections."""
import copy
from fractions import Fraction
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from collection.audit import CollectionAudit
from collection.intelligence import CanonicalCollectionResolver,build_snapshot,read_import,digest,compare_deck
from collection.deck_analysis import (analyze_collection_decks,validate_collection_decks,parse_collection_decks,
    render_collection_decks,DeckAnalysisError,INPUT_VERSION,MAX_INPUT_BYTES)
from probability.supplied_deck import assess_supplied_decks
from probability.draw_access import canonical_json
from query import CanonicalQueryEngine

ROOT=Path(__file__).resolve().parents[1]
P1='pack_fixture.tst.1.en';P2='pack_fixture.tst.2.en';P3='pack_fixture.tst.3.en';P4='pack_fixture.tst.4.en';P5='pack_fixture.tst.5.en'
C1='pack_fixture.card1';C2='pack_fixture.card2';C3='pack_fixture.card3';C4='pack_fixture.private-unrelated-card'
CANARY='PRIVATE_PATH_NOTES_STORAGE_CANARY'


class CollectionDeckAnalysisTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(prefix='private-collection-');self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name);self.data=self.root/'catalog'
        shutil.copytree(ROOT/'tests/fixtures/pack_simulation_v02/data',self.data)
        self.game=self.data/'canonical/games/pack_fixture'
        card=json.loads((self.game/f'cards/{C2}/card.json').read_text());card['id']=C4;card['name']='Fictional unrelated card'
        path=self.game/f'cards/{C4}/card.json';path.parent.mkdir();path.write_text(json.dumps(card))
        for pid,cid,number in ((P4,C1,'4'),(P5,C4,'5')):
            raw=json.loads((self.game/f'printings/{P1}/printing.json').read_text())
            raw.update(id=pid,card_id=cid,collector_number=number)
            for i,a in enumerate(raw['assertions']):
                a['subject_id']=pid;a['id']='fictional-extra-'+number+'-'+str(i)
                if a['path'] in ('/id','/card_id','/collector_number'):a['asserted_value']=raw[a['path'][1:]]
            path=self.game/f'printings/{pid}/printing.json';path.parent.mkdir();path.write_text(json.dumps(raw))
        self.source=self.root/(CANARY+'.json');self.snapshot_path=self.root/'snapshot.json'
        self.rows=[dict(printing_id=p,quantity=q,notes=CANARY,storage_location=CANARY,
            provenance=dict(owned_lot_id='fictional-lot-'+str(i))) for i,(p,q) in enumerate(((P1,1),(P4,1),(P3,57),(P5,8)))]
        self.rebuild()

    def rebuild(self):
        self.resolver=CanonicalCollectionResolver('pack_fixture',self.data)
        self.source.write_text(canonical_json(dict(schema_version='collection-import-v1',collection_id='fictional-inventory',
            source=dict(type='synthetic_fixture',real_user_inventory=False,notice=CANARY),entries=self.rows)))
        imported=read_import(self.source)
        self.snapshot=build_snapshot(imported,self.resolver.resolve(imported),'fictional-snapshot')
        self.snapshot_path.write_text(canonical_json(self.snapshot))
        self.value=dict(schema_version=INPUT_VERSION,
            catalog=dict(game='pack_fixture',snapshot_id=self.resolver.canonical_snapshot_id),
            collection_binding={k:self.snapshot[k] for k in ('snapshot_id','snapshot_digest','source_import_digest')},
            deck_analysis=dict(schema_version='supplied-deck-consistency-input-v1',decks=[self.deck('original',3),self.deck('modified',4)]),
            requirements=[dict(deck_id='original',requirements=[self.req('target-exact',C1,2,'exact',P1),self.req('target-flex',C1,1),self.req('filler',C3,57)]),
                          dict(deck_id='modified',requirements=[self.req('target',C1,4),self.req('filler',C3,56)])])

    @staticmethod
    def req(identity,card,quantity,policy='any',printing=None):
        return dict(requirement_id=identity,card_id=card,section='main',quantity=quantity,policy=policy,printing_id=printing)

    @staticmethod
    def deck(identity,target):
        return dict(deck_id=identity,identity_authority='CALLER_DECLARED',complete=True,
            draw_population=dict(section='main',declared_size=60),
            entries=[dict(card_id=C1,quantity=target,section='main'),dict(card_id=C3,quantity=60-target,section='main'),
                     dict(card_id=C2,quantity=15,section='sideboard')],
            groups=[dict(group_id='target-access',members=[C1],minimum=1)],
            schedule=[dict(label='Opening assumption',cards_seen=7),dict(label='Later assumption',cards_seen=9)],
            assumptions=dict(sampling='uniform-without-replacement',group_disjointness='caller_declared'))

    def run_analysis(self,value=None,**options):
        return analyze_collection_decks(value or self.value,snapshot=options.pop('snapshot',self.snapshot),
            source_path=options.pop('source_path',self.source),source_root=options.pop('source_root',self.root),
            catalog_root=options.pop('catalog_root',self.data),**options)

    def test_actual_audit_allocator_consistency_and_combined_benchmark(self):
        with patch('collection.deck_analysis.compare_deck',wraps=compare_deck) as owner:
            r=self.run_analysis();self.assertEqual(owner.call_count,2)
            self.assertTrue(all(c.kwargs['include_allocations'] is True for c in owner.call_args_list))
        self.assertEqual([c['covered_quantity'] for c in r['coverage']],[59,58])
        self.assertEqual([c['uncovered_quantity'] for c in r['coverage']],[1,2])
        self.assertEqual(r['consistency'],assess_supplied_decks(self.value['deck_analysis']))
        self.assertEqual([c['results'][0]['probability']['decimal'] for c in r['consistency']['configurations']],['0.315429573349','0.399499625745'])

    def test_exact_first_trace_and_physical_printing_conservation(self):
        r=self.run_analysis();rows={x['requirement_id']:x for x in r['coverage'][0]['requirements']}
        self.assertEqual(rows['target-exact']['printings'],[dict(printing_id=P1,quantity=1)])
        self.assertEqual(rows['target-flex']['printings'],[dict(printing_id=P4,quantity=1)])
        self.assertEqual(rows['target-exact']['uncovered_quantity'],1)
        for coverage in r['coverage']:
            allocated={}
            for row in coverage['requirements']:
                self.assertEqual(sum(p['quantity'] for p in row['printings']),row['allocated_quantity'])
                self.assertEqual(row['allocated_quantity']+row['uncovered_quantity'],row['required_quantity'])
                for p in row['printings']:allocated[p['printing_id']]=allocated.get(p['printing_id'],0)+p['quantity']
            self.assertLessEqual(allocated.get(P1,0),1);self.assertLessEqual(allocated.get(P4,0),1)

    def test_optional_trace_preserves_entire_legacy_allocator_report(self):
        native=dict(schema_version='deck-requirement-v1',deck_id='legacy',requirements=[dict(card_id=C1,quantity=3)])
        old=compare_deck(self.snapshot,native,self.resolver)
        self.assertEqual(old,compare_deck(self.snapshot,native,self.resolver,include_allocations=False))
        detailed=compare_deck(self.snapshot,native,self.resolver,include_allocations=True)
        detailed.pop('allocation_trace');detailed['schema_version']='deck-comparison-v1';self.assertEqual(detailed,old)
        for invalid in (None,1,'true'):
            with self.assertRaises(ValueError):compare_deck(self.snapshot,native,self.resolver,include_allocations=invalid)

    def test_independent_alternatives_do_not_reserve_or_deplete_inventory(self):
        r=self.run_analysis();self.assertEqual(r['allocation_scope'],'INDEPENDENT_ALTERNATIVES_NO_RESERVATION')
        for index in (0,1):
            value=copy.deepcopy(self.value);value['deck_analysis']['decks']=[value['deck_analysis']['decks'][index]];value['requirements']=[value['requirements'][index]]
            self.assertEqual(self.run_analysis(value)['coverage'][0],r['coverage'][index])

    def test_inventory_changes_never_change_intended_consistency(self):
        before=self.run_analysis()['consistency'];self.rows[0]['quantity']=4;self.rebuild()
        r=self.run_analysis();self.assertEqual(r['consistency'],before)
        self.assertEqual(r['coverage'][0]['uncovered_quantity'],0)

    def test_empty_reported_inventory_preserves_intended_deck_sizes(self):
        self.rows=[];self.rebuild();r=self.run_analysis()
        self.assertEqual([c['covered_quantity'] for c in r['coverage']],[0,0])
        self.assertEqual([c['uncovered_quantity'] for c in r['coverage']],[60,60])
        self.assertEqual([c['deck_size'] for c in r['consistency']['configurations']],[60,60])

    def test_conflicting_lots_block_both_alternatives_before_allocation(self):
        self.rows[1]['provenance']=copy.deepcopy(self.rows[0]['provenance']);self.rebuild()
        with patch('collection.deck_analysis.compare_deck') as owner:r=self.run_analysis();owner.assert_not_called()
        self.assertTrue(all(c['reasons']==['CONFLICTING_OWNERSHIP_LOTS'] for c in r['coverage']))
        self.assertTrue(all(c['covered_quantity'] is None and not c['requirements'] for c in r['coverage']))
        self.assertEqual(r['uncertainty']['conflicting_lot_rows'],2)
        self.assertEqual(r['consistency']['status'],'ASSESSED')

    def test_duplicate_invalid_unresolved_rows_never_create_copies(self):
        self.rows += [copy.deepcopy(self.rows[0]),dict(printing_id='private-unrelated',quantity=9,notes=CANARY),dict(printing_id=P1,quantity=-1)]
        self.rebuild();r=self.run_analysis()
        self.assertEqual(r['coverage'][0]['covered_quantity'],59)
        self.assertEqual((r['uncertainty']['excluded_duplicate_rows'],r['uncertainty']['unresolved_rows'],r['uncertainty']['invalid_rows']),(1,1,1))
        self.assertIsNone(r['uncertainty']['scope_complete']);self.assertFalse(r['uncertainty']['physical_ownership_independently_verified'])
        self.assertNotIn('private-unrelated',canonical_json(r))

    def test_unknown_card_join_withholds_coverage_without_zero_owned_claim(self):
        value=copy.deepcopy(self.value)
        for d in value['deck_analysis']['decks']:
            d['entries'][0]['card_id']='caller:unresolved';d['groups'][0]['members']=['caller:unresolved']
        for s in value['requirements']:
            for row in s['requirements']:
                if row['card_id']==C1:row['card_id']='caller:unresolved'
        r=self.run_analysis(value)
        self.assertTrue(all(c['status']=='WITHHELD' and c['uncovered_quantity'] is None for c in r['coverage']))
        self.assertEqual(r['consistency'],assess_supplied_decks(value['deck_analysis']))

    def test_foreign_and_unknown_printings_do_not_become_shortages(self):
        for printing in (P3,'unknown'):
            value=copy.deepcopy(self.value);value['requirements'][0]['requirements'][0]['printing_id']=printing
            r=self.run_analysis(value);self.assertEqual(r['coverage'][0]['status'],'WITHHELD')
            self.assertIsNone(r['coverage'][0]['uncovered_quantity']);self.assertEqual(r['coverage'][1]['status'],'REPORTED_SNAPSHOT_COVERAGE')

    def test_requirement_totals_sections_policies_and_zero_rows_are_strict(self):
        for field,invalid in (('quantity',0),('quantity',True),('quantity',2.0),('quantity',-1),('quantity',3),('section','sideboard'),('policy','finish-specific')):
            value=copy.deepcopy(self.value);value['requirements'][0]['requirements'][0][field]=invalid
            with self.subTest(field=field,value=invalid),self.assertRaises(DeckAnalysisError):self.run_analysis(value)
        value=copy.deepcopy(self.value)
        for d in value['deck_analysis']['decks']:d['entries'].append(dict(card_id=C2,quantity=0,section='main'))
        self.assertEqual(self.run_analysis(value)['coverage'][0]['covered_quantity'],59)

    def test_missing_retained_source_and_path_escape_withhold_coverage(self):
        for path,root in ((self.root/'missing.json',self.root),(self.source,self.root/'elsewhere')):
            r=self.run_analysis(source_path=path,source_root=root)
            self.assertTrue(all(c['status']=='WITHHELD' for c in r['coverage']))
            self.assertIsNone(r['bindings']['verified_collection']);self.assertNotIn(str(self.root),canonical_json(r))

    def test_source_tampering_is_detected(self):
        self.source.write_bytes(self.source.read_bytes()+b' ')
        r=self.run_analysis();self.assertTrue(all(c['status']=='WITHHELD' for c in r['coverage']))

    def test_coherently_rehashed_snapshot_is_not_source_admission(self):
        changed=copy.deepcopy(self.snapshot);changed['resolved_holdings'][0]['row']['quantity']=40
        changed['snapshot_digest']=digest({k:v for k,v in changed.items() if k!='snapshot_digest'})
        value=copy.deepcopy(self.value);value['collection_binding']['snapshot_digest']=changed['snapshot_digest']
        r=self.run_analysis(value,snapshot=changed)
        self.assertTrue(all(c['status']=='WITHHELD' for c in r['coverage']))

    def test_wrong_snapshot_or_catalog_bindings_never_substitute_defaults(self):
        for field in ('snapshot_id','snapshot_digest','source_import_digest'):
            value=copy.deepcopy(self.value);value['collection_binding'][field]='wrong' if field=='snapshot_id' else '0'*64
            self.assertEqual(self.run_analysis(value)['coverage'][0]['status'],'WITHHELD')
        value=copy.deepcopy(self.value);value['catalog']['snapshot_id']='sha256:'+'0'*64
        r=self.run_analysis(value);self.assertIsNone(r['bindings']['verified_catalog_id'])
        self.assertEqual(r['coverage'][0]['status'],'WITHHELD')
        self.assertEqual(self.run_analysis(catalog_root=self.root/'absent')['coverage'][0]['status'],'WITHHELD')

    def test_catalog_drift_and_ambiguous_card_identities_fail_closed(self):
        p=self.game/f'cards/{C1}/card.json';raw=json.loads(p.read_text());raw['name']='Changed fictional name';p.write_text(json.dumps(raw))
        self.assertEqual(self.run_analysis()['coverage'][0]['status'],'WITHHELD')
        duplicate=self.game/'cards/duplicate/card.json';duplicate.parent.mkdir();duplicate.write_bytes(p.read_bytes())
        self.assertEqual(self.run_analysis()['coverage'][0]['status'],'WITHHELD')

    def test_unverified_join_is_not_approved_by_a_matching_string(self):
        real_entity=CanonicalQueryEngine.entity
        def unverified(query,identifier,**kw):
            result=real_entity(query,identifier,**kw)
            if identifier==C1:
                from dataclasses import replace
                result=replace(result,uncertainty='unknown')
            return result
        with patch.object(CanonicalQueryEngine,'entity',unverified):r=self.run_analysis()
        self.assertTrue(all(c['status']=='WITHHELD' for c in r['coverage']))

    def test_final_source_drift_discards_all_earlier_coverage(self):
        def changed(*args,**kwargs):raise ValueError(CANARY)
        with patch.object(CollectionAudit,'verify_source_snapshot',changed):r=self.run_analysis()
        self.assertTrue(all(c['reasons']==['INPUT_DRIFT_DURING_ANALYSIS'] for c in r['coverage']))
        self.assertIsNone(r['bindings']['verified_collection']);self.assertNotIn(CANARY,canonical_json(r))

    def test_no_notes_paths_unrelated_holdings_or_raw_audit_are_exported(self):
        r=self.run_analysis()
        for text in (canonical_json(r),render_collection_decks(r,readable=True)):
            for private in (CANARY,str(self.root),P5,C4):self.assertNotIn(private,text)
        self.assertFalse(r['ownership_write']);self.assertFalse(r['real_gameplay_authorized'])

    def test_immutable_inputs_repeatable_reports_and_content_identities(self):
        before=copy.deepcopy((self.value,self.snapshot));a=self.run_analysis();saved=copy.deepcopy(a)
        a['coverage'].clear();a['consistency']['input'].clear()
        self.assertEqual(self.run_analysis(),saved);self.assertEqual((self.value,self.snapshot),before)
        value=copy.deepcopy(self.value);value['requirements'][0]['requirements'].reverse()
        self.assertEqual(self.run_analysis(value),saved)

    def test_probability_abstention_and_impossible_events_remain_native(self):
        value=copy.deepcopy(self.value);value['deck_analysis']['decks'][1]['groups'][0]['minimum']=2
        self.assertEqual(self.run_analysis(value)['consistency']['comparison']['status'],'ABSTAINED')
        value['deck_analysis']['decks'][0]['groups'][0]['minimum']=4
        r=self.run_analysis(value);self.assertEqual(r['consistency']['configurations'][0]['status'],'IMPOSSIBLE_POPULATION_REQUIREMENT')
        self.assertEqual(r['coverage'][0]['status'],'REPORTED_SNAPSHOT_COVERAGE')

    def test_closed_contracts_duplicate_identities_bad_json_and_bounds(self):
        for field in ('verified','mapping','private_collection','finish'):
            value=copy.deepcopy(self.value);value[field]=True
            with self.subTest(field=field),self.assertRaises(DeckAnalysisError):self.run_analysis(value)
        value=copy.deepcopy(self.value);value['requirements'][0]['requirements'][1]['requirement_id']='target-exact'
        with self.assertRaises(DeckAnalysisError):self.run_analysis(value)
        for raw in (b'{',b'\xff','\ud800','NaN','{"x":1,"x":2}',b'x'*(MAX_INPUT_BYTES+1)):
            with self.assertRaises(DeckAnalysisError):parse_collection_decks(raw)

    def test_public_cli_api_json_text_and_structured_refusals(self):
        path=self.root/'request.json';path.write_text(canonical_json(self.value));expected=self.run_analysis()
        cmd=[sys.executable,'-B','-m','mtglab','deck','analyze','--input',str(path),'--snapshot',str(self.snapshot_path),
             '--source',str(self.source),'--source-root',str(self.root),'--catalog-root',str(self.data)]
        for mode in ('json','text'):
            run=subprocess.run(cmd+['--format',mode],capture_output=True,cwd=ROOT)
            self.assertEqual(run.returncode,0,run.stderr);self.assertEqual(run.stderr,b'')
            self.assertEqual(run.stdout,render_collection_decks(expected,readable=mode=='text').encode())
        path.write_text('{}');run=subprocess.run(cmd,capture_output=True,cwd=ROOT)
        self.assertEqual(run.returncode,2);self.assertEqual(json.loads(run.stdout)['status'],'REFUSED')
        self.assertNotIn(CANARY,run.stdout.decode())

    def test_name_only_inventory_resolution_is_not_exact_identity_admission(self):
        self.rows.append(dict(card_name='Fictional Card 3',quantity=1));self.rebuild()
        self.assertEqual(self.run_analysis()['coverage'][0]['reasons'],['REPORTED_INVENTORY_IDENTITY_NOT_ESTABLISHED'])

    def test_one_invalid_alternative_does_not_change_other_valid_coverage(self):
        value=copy.deepcopy(self.value)
        value['requirements'][0]['requirements'][0]['printing_id']=P3
        r=self.run_analysis(value);self.assertEqual(r['coverage'][0]['status'],'WITHHELD')
        self.assertEqual(r['coverage'][1]['covered_quantity'],58)

    def test_trace_order_is_invariant_under_valid_requirement_reordering(self):
        before=self.run_analysis();self.value['requirements'][0]['requirements'].reverse()
        self.assertEqual(self.run_analysis(),before)

    def test_supplying_wrong_identity_authority_or_finish_constraints_refuses(self):
        value=copy.deepcopy(self.value);value['deck_analysis']['decks'][0]['identity_authority']='CANONICAL'
        with self.assertRaises(DeckAnalysisError):self.run_analysis(value)
        value=copy.deepcopy(self.value);value['requirements'][0]['requirements'][0]['finish_id']='foil'
        with self.assertRaises(DeckAnalysisError):self.run_analysis(value)

    def test_input_output_schemas_are_closed_for_success_withheld_and_refusal(self):
        from jsonschema import Draft202012Validator,ValidationError
        validators={}
        for name in ('input','report'):
            schema=json.loads((ROOT/f'src/schemas/v1/collection-deck-analysis-{name}.schema.json').read_text())
            Draft202012Validator.check_schema(schema);validators[name]=Draft202012Validator(schema)
        validators['input'].validate(self.value)
        for r in (self.run_analysis(),self.run_analysis(source_path=self.root/'missing')):
            validators['report'].validate(r)
            r['bindings']['permission_granted']=True
            with self.assertRaises(ValidationError):validators['report'].validate(r)
        validators['report'].validate(DeckAnalysisError('bad request').as_dict())

    def test_source_reread_and_report_budgets_are_explicit(self):
        with patch('collection.deck_analysis.MAX_REPORT_BYTES',100),self.assertRaises(DeckAnalysisError):self.run_analysis()
        with patch('collection.deck_analysis.MAX_SNAPSHOT_BYTES',100),self.assertRaises(DeckAnalysisError):self.run_analysis()
        with self.assertRaises(DeckAnalysisError):self.run_analysis(catalog_root=None)

    def test_closed_requirement_sets_and_collection_binding_types_refuse(self):
        for mutate in (lambda v:v['requirements'].pop(),
                       lambda v:v['requirements'].append(v['requirements'][0]),
                       lambda v:v['requirements'][0].update(deck_id='unknown'),
                       lambda v:v['collection_binding'].update(source_import_digest='unknown'),
                       lambda v:v['catalog'].update(game='../outside'),
                       lambda v:v['requirements'][1]['requirements'][0].update(printing_id=P1)):
            value=copy.deepcopy(self.value);mutate(value)
            with self.assertRaises(DeckAnalysisError):self.run_analysis(value)

    def test_unchanged_consistency_including_native_report_identity(self):
        original=assess_supplied_decks(self.value['deck_analysis'])
        self.source.unlink();r=self.run_analysis()
        self.assertEqual(r['consistency'],original);self.assertEqual(r['consistency']['report_id'],original['report_id'])

    def test_source_and_snapshot_files_are_never_written_by_analysis(self):
        paths=[p for p in self.root.rglob('*') if p.is_file()]
        before={p:p.read_bytes() for p in paths};self.run_analysis()
        self.assertEqual({p:p.read_bytes() for p in paths},before)
        self.assertEqual(set(p for p in self.root.rglob('*') if p.is_file()),set(paths))

    def test_final_catalog_change_withholds_previous_allocations(self):
        original=compare_deck
        def changing(*args,**kw):
            result=original(*args,**kw)
            p=self.game/f'cards/{C1}/card.json';d=json.loads(p.read_text());d['name']='Drift';p.write_text(json.dumps(d))
            return result
        with patch('collection.deck_analysis.compare_deck',changing):r=self.run_analysis()
        self.assertTrue(all(c['reasons']==['INPUT_DRIFT_DURING_ANALYSIS'] for c in r['coverage']))

    def test_valid_zero_group_requirement_never_adds_ownership_rows(self):
        value=copy.deepcopy(self.value)
        for d in value['deck_analysis']['decks']:
            d['entries'].append(dict(card_id=C2,quantity=0,section='main'))
            d['groups'].append(dict(group_id='zero',members=[C2],minimum=0))
        r=self.run_analysis(value)
        self.assertEqual(r['coverage'][0]['intended_quantity'],60)
        self.assertTrue(all(row['card_id']!=C2 for row in r['coverage'][0]['requirements']))


if __name__=='__main__':unittest.main()
