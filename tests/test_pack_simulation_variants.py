"""Actual fictional variant execution, not physical manufacturing inference."""
from contextlib import redirect_stdout
import io
import json
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch

from simulation import (VARIANT_MODEL, VARIANT_VERSION, PackSimulationError,
                        load_pack_simulator, render_pack_report)
from simulation.pack import _select, _ticket
from test_pack_simulation import files

ROOT=Path(__file__).resolve().parents[1]
FIXTURE=ROOT/'tests/fixtures/pack_simulation_v02/data'
GAME='pack_fixture';PARENT='fictional-variants'
A='variant-a-nonfoil';B='variant-b-foil';C='variant-c-mixed'
P1='pack_fixture.tst.1.en'
PARENT_PATH=f'packs/{PARENT}/pack-definition.json'


class WeightedPackVariantTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.data=Path(self.temp.name)/'data';shutil.copytree(FIXTURE,self.data)
        self.game=self.data/'canonical/games'/GAME

    def generate(self,seed=1):
        return load_pack_simulator(GAME,data_root=self.data).generate('fictional-pack',pack_definition_id=PARENT,seed=seed)

    def mutate(self,path,change):
        p=self.game/path;d=json.loads(p.read_text());change(d);p.write_text(json.dumps(d))

    def refuse(self):
        with self.assertRaises(PackSimulationError) as caught:self.generate()
        r=caught.exception.as_dict();self.assertEqual(r['status'],'NOT_READY_FOR_SIMULATION');self.assertNotIn('slots',r)
        self.assertFalse(r['production_authorized'])

    def test_actual_fifteen_card_variants_counts_slots_and_finishes(self):
        expected={0:(B,[10,4,1],'foil-slot'),1:(A,[10,4,1],'nonfoil-slot'),97:(C,[9,4,2],'mixed-slot')}
        for seed,(variant,counts,last) in expected.items():
            r=self.generate(seed);self.assertEqual(r['selected_variant_id'],variant)
            self.assertEqual(r['card_count'],15);self.assertEqual([len(s['outcomes']) for s in r['slots']],counts)
            self.assertEqual(sum(counts),15);self.assertEqual(r['slots'][-1]['slot_id'],last)
            self.assertTrue(all('printing_ids' not in s for s in r['slots']))
            if seed==0:self.assertEqual(r['slots'][-1]['outcomes'],[dict(printing_id=P1,finish_id='foil')])
            if seed==1:self.assertTrue(all(o['finish_id']=='nonfoil' for s in r['slots'] for o in s['outcomes']))
            if seed==97:self.assertEqual(r['slots'][-1]['print_sheet_id'],'mixed-sheet')
            self.assertFalse(r['production_authorized'])

    def test_exact_all_one_hundred_tickets_and_actual_routing(self):
        entries=[(A,90),(B,8),(C,2)]
        self.assertEqual([_select(entries,t) for t in range(100)],[A]*90+[B]*8+[C]*2)
        owner=load_pack_simulator(GAME,data_root=self.data)
        for ticket in range(100):
            def first(seed,counter,total):return (ticket,1) if counter==0 else _ticket(seed,counter,total)
            with patch('simulation.pack._ticket',side_effect=first):
                report=owner.generate('fictional-pack',pack_definition_id=PARENT,seed=1)
            self.assertEqual(report['selected_variant_id'],entries[0 if ticket<90 else 1 if ticket<98 else 2][0])
        with self.assertRaises(PackSimulationError):_select(entries,100)

    def test_selection_consumes_counter_zero_then_slots_preserve_stream(self):
        with patch('simulation.pack._ticket',wraps=_ticket) as draw:r=self.generate(0)
        self.assertEqual(draw.call_args_list[0].args,(0,0,100))
        self.assertEqual(len(draw.call_args_list),16)
        self.assertEqual([c.args[1] for c in draw.call_args_list],list(range(16)))
        first,_=_ticket(0,1,3)
        self.assertEqual(r['slots'][0]['outcomes'][0]['printing_id'],_select([(P1,1),('pack_fixture.tst.2.en',2)],first))

    def test_rejected_random_blocks_advance_before_any_card_draw(self):
        # 2^256-1 is outside the unbiased acceptance region for total100.
        real=_ticket
        with patch('simulation.pack.hashlib.sha256') as h:
            h.return_value.digest.side_effect=[b'\xff'*32,b'\0'*32]
            self.assertEqual(real(1,0,100),(0,2))
        def forced(seed,counter,total):return (0,2) if counter==0 else real(seed,counter,total)
        with patch('simulation.pack._ticket',side_effect=forced) as draw:r=self.generate(1)
        self.assertEqual(draw.call_args_list[1].args[1],2);self.assertEqual(r['selected_variant_id'],A)

    def test_seed_reproducibility_detached_results_and_read_only_inputs(self):
        before=files(self.data);owner=load_pack_simulator(GAME,data_root=self.data)
        a=owner.generate('fictional-pack',pack_definition_id=PARENT,seed=0)
        b=owner.generate('fictional-pack',pack_definition_id=PARENT,seed=0);self.assertEqual(a,b)
        b['slots'][0]['outcomes'][0]['finish_id']='forged';b['evidence_references'].clear()
        self.assertEqual(a,owner.generate('fictional-pack',pack_definition_id=PARENT,seed=0))
        self.assertEqual(before,files(self.data));self.assertNotEqual(a['selected_variant_id'],self.generate(1)['selected_variant_id'])

    def test_missing_and_malformed_variant_weights_never_default(self):
        p=self.game/PARENT_PATH;original=p.read_bytes()
        for value in (None,True,False,0,-1,1.5,'90',[],{},2**64):
            p.write_bytes(original);self.mutate(PARENT_PATH,lambda d:d['variants'][0].update(weight=value));self.refuse()
        p.write_bytes(original);self.mutate(PARENT_PATH,lambda d:d['variants'][0].pop('weight'));self.refuse()
        p.write_bytes(original);self.mutate(PARENT_PATH,lambda d:d['variants'][0].update(weight=2**64-1));self.refuse()

    def test_empty_duplicate_invalid_and_missing_variant_references(self):
        p=self.game/PARENT_PATH;original=p.read_bytes()
        for variants in ([],None,{},'a',[None],[1],[{}],
                         [dict(pack_definition_id=A,weight=1)]*2,
                         [dict(pack_definition_id='absent',weight=1)],
                         [dict(pack_definition_id=1,weight=1)],
                         [dict(pack_definition_id='',weight=1)]):
            p.write_bytes(original);self.mutate(PARENT_PATH,lambda d:d.update(variants=variants));self.refuse()

    def test_cross_version_and_unknown_fields_reject(self):
        p=self.game/PARENT_PATH;original=p.read_bytes()
        for change in (lambda d:d.update(schema_version='v2'),lambda d:d.update(slot_ids=['base-slot']),
                       lambda d:d['variants'][0].update(approval=True),lambda d:d.update(extra=1),
                       lambda d:d.update(metadata={'simulation_model':'independent-finish-weighted-with-replacement-v1'})):
            p.write_bytes(original);self.mutate(PARENT_PATH,change);self.refuse()
        p.write_bytes(original)
        self.mutate(f'packs/{C}/pack-definition.json',lambda d:d.update(metadata={'simulation_model':'independent-weighted-with-replacement-v1'}));self.refuse()

    def test_unselected_invalid_composition_rejected_before_random_selection(self):
        self.mutate(f'packs/{C}/pack-definition.json',lambda d:d.update(metadata={'simulation_model':'unknown'}))
        with patch('simulation.pack._ticket') as random:
            self.refuse();random.assert_not_called()

    def test_unknown_slot_sheet_printing_and_finish_references(self):
        for path,change in [
            (f'packs/{C}/pack-definition.json',lambda d:d.update(slot_ids=['absent'])),
            ('slots/mixed-slot/slot.json',lambda d:d.update(print_sheet_id='absent')),
            ('print_sheets/mixed-sheet/print-sheet.json',lambda d:d['entries'][0].update(printing_id='absent')),
            ('print_sheets/mixed-sheet/print-sheet.json',lambda d:d['entries'][0].update(finish_id='absent')),
            ('print_sheets/mixed-sheet/print-sheet.json',lambda d:d['entries'][0].pop('finish_id'))]:
            p=self.game/path;old=p.read_bytes();self.mutate(path,change);self.refuse();p.write_bytes(old)

    def test_unsupported_printing_finish_and_unresolved_assertions(self):
        path='print_sheets/mixed-sheet/print-sheet.json';p=self.game/path;old=p.read_bytes()
        self.mutate(path,lambda d:d['entries'][0].update(printing_id='pack_fixture.tst.2.en'));self.refuse();p.write_bytes(old)
        (self.game/'finishes/foil.json').unlink();self.refuse()

    def test_missing_unverified_forged_source_and_provenance_reject(self):
        source='sources/fictional-definition.json';p=self.game/source;original=p.read_bytes()
        for change in (lambda d:d.update(verification_status='unverified'),lambda d:d.update(authenticated=True),
                       lambda d:d.update(permission_granted=True),lambda d:d.pop('source_location')):
            p.write_bytes(original);self.mutate(source,change);self.refuse()
        p.write_bytes(original);self.mutate(PARENT_PATH,lambda d:d['provenance'][0].update(field_paths=['id']));self.refuse()

    def test_all_candidate_evidence_and_weights_bind_input_identity(self):
        a=self.generate();refs={(x['kind'],x['id']) for x in a['evidence_references']}
        self.assertTrue({('pack_definition',n) for n in (PARENT,A,B,C)}<=refs)
        self.assertIn(('print_sheet','mixed-sheet'),refs)
        self.mutate(PARENT_PATH,lambda d:d['variants'][2].update(weight=3));b=self.generate()
        self.assertNotEqual(a['input_id'],b['input_id']);self.assertEqual(b['variant_total_weight'],101)
        self.mutate(f'packs/{C}/pack-definition.json',lambda d:d.update(name='Unselected fictional display label'))
        c=self.generate();self.assertNotEqual(b['input_id'],c['input_id']);self.assertEqual(b['slots'],c['slots'])

    def test_source_content_changes_identity_without_authentication_or_permission(self):
        a=self.generate();self.mutate('sources/fictional-definition.json',lambda d:d['claims'].append('Fictional extra note.'))
        b=self.generate();self.assertNotEqual(a['input_id'],b['input_id']);self.assertNotEqual(a['source_references'],b['source_references'])
        self.assertEqual(a['slots'],b['slots']);self.assertFalse(b['production_authorized'])

    def test_variant_declaration_order_and_pool_order_preserve_draws(self):
        a=self.generate(0);self.mutate(PARENT_PATH,lambda d:d['variants'].reverse())
        self.mutate('print_sheets/base-sheet/print-sheet.json',lambda d:d['entries'].reverse())
        b=self.generate(0);self.assertEqual(a['selected_variant_id'],b['selected_variant_id']);self.assertEqual(a['slots'],b['slots'])
        self.assertNotEqual(a['input_id'],b['input_id'])

    def test_nested_foreign_variants_and_unknown_product_or_pack_reject(self):
        self.mutate(PARENT_PATH,lambda d:d['variants'][0].update(pack_definition_id=PARENT));self.refuse()
        for product,pack in (('unknown',PARENT),('fictional-pack','unknown')):
            with self.assertRaises(PackSimulationError):load_pack_simulator(GAME,data_root=FIXTURE).generate(product,pack_definition_id=pack,seed=0)
        with self.assertRaisesRegex(PackSimulationError,'PACK_NOT_IN_PRODUCT_VERSION'):
            load_pack_simulator(GAME,data_root=FIXTURE).generate('fictional-pack',pack_definition_id=A,seed=0)

    def test_foreign_product_version_is_not_an_eligible_variant(self):
        path=self.game/'product_versions/fictional-version/product-version.json'
        version=json.loads(path.read_text());version.update(id='foreign-version',components=[])
        other=self.game/'product_versions/foreign-version/product-version.json'
        other.parent.mkdir();other.write_text(json.dumps(version))
        self.mutate('products/fictional-pack/product.json',lambda d:d['version_ids'].append('foreign-version'))
        self.mutate(f'packs/{C}/pack-definition.json',lambda d:d.update(product_version_id='foreign-version'))
        self.refuse()

    def test_parent_variant_count_and_total_weight_bounds(self):
        self.mutate(PARENT_PATH,lambda d:d.update(variants=[dict(pack_definition_id=f'child-{i}',weight=1) for i in range(33)]))
        self.refuse()

    def test_existing_bounds_also_limit_total_candidate_work(self):
        self.mutate('slots/base-slot/slot.json',lambda d:d.update(draw_count=600));self.refuse()
        # Each individual composition is <1024, while the candidate sum exceeds it.
        p=self.game/'slots/base-slot/slot.json';d=json.loads(p.read_text());d['draw_count']=10;p.write_text(json.dumps(d))
        self.mutate('slots/mixed-slot/slot.json',lambda d:d.update(replacement=False));self.refuse()

    def test_public_api_cli_json_text_and_versioned_provenance(self):
        from mtglab.__main__ import main
        before=files(self.data);r=self.generate(0)
        self.assertEqual((r['schema_version'],r['simulator_version'],r['sampling_model']),(VARIANT_VERSION,VARIANT_VERSION,VARIANT_MODEL))
        self.assertEqual((r['selected_variant_weight'],r['variant_total_weight']),(8,100))
        self.assertEqual((r['product_id'],r['product_version_id'],r['pack_definition_id']),('fictional-pack','fictional-version',PARENT))
        for fmt in ('json','text'):
            out=io.StringIO()
            with redirect_stdout(out):code=main(['--data-root',str(self.data),'pack','simulate','--game',GAME,'--product-id','fictional-pack','--definition-id',PARENT,'--seed','0','--format',fmt])
            self.assertEqual(code,0);self.assertEqual(out.getvalue(),render_pack_report(r,readable=fmt=='text'))
        self.assertEqual(before,files(self.data))

    def test_typed_native_contract_and_detached_reference(self):
        from query import CanonicalQueryEngine
        q=CanonicalQueryEngine(GAME,data_root=self.data,games_root=self.data/'canonical/games')
        raw=q.retained_record(PARENT,entity_type='pack_definition');raw['variants'][0]['weight']=0
        self.assertEqual(q.retained_record(PARENT,entity_type='pack_definition')['variants'][0]['weight'],90)
        version=q.retained_record('fictional-version',entity_type='product_version')
        self.assertEqual(version['components'],[dict(component_type='pack_definition',component_id=PARENT,quantity=1)])
        view=q.entities(canonical_id=PARENT)[0].as_dict()['canonical_values']
        self.assertEqual(view['schema_version'],'v3')
        self.assertEqual(view['variants'],[dict(pack_definition_id=A,weight=90),dict(pack_definition_id=B,weight=8),dict(pack_definition_id=C,weight=2)])
        # Variants are alternatives, never three extra simultaneous physical packs.

    def test_existing_v0_and_v01_exact_full_report_compatibility(self):
        examples=ROOT/'tests/fixtures/pack_simulation_v01/examples'
        for version,seeds in (('v0',(1,)),('v01',(1,2))):
            owner=load_pack_simulator(GAME,data_root=ROOT/f'tests/fixtures/pack_simulation_{version}/data')
            for seed in seeds:
                r=owner.generate('fictional-pack',pack_definition_id='fictional-definition',seed=seed)
                self.assertNotIn('selected_variant_id',r)
                for readable,ext in ((False,'json'),(True,'txt')):
                    self.assertEqual((examples/f'{version}-seed{seed}.{ext}').read_text(),render_pack_report(r,readable=readable))

    def test_actual_examples_and_finite_successor_integrity(self):
        import variant_simulation_preservation as guard
        import hashlib
        for name,pin in guard.ledger()['replacements'].items():
            raw=(ROOT/name).read_bytes();old=guard.preceding_bytes(name,raw)
            self.assertEqual(hashlib.sha256(old).hexdigest(),pin['old_sha256'])
            with self.assertRaises(AssertionError):guard.preceding_bytes(name,raw+b'coherently-rehashed')
        name='src/canonical/__init__.py'
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/name;p.parent.mkdir(parents=True);raw=(ROOT/name).read_bytes()+b'future';p.write_bytes(raw)
            row=dict(path=name,bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest())
            import query_attachment_performance_preservation as prior
            with self.assertRaises(AssertionError):prior.historical_inventory_row(row,Path(d))
        for seed in (0,1,97):
            r=self.generate(seed)
            for readable,ext in ((False,'json'),(True,'txt')):
                self.assertEqual((ROOT/f'tests/fixtures/pack_simulation_v02/examples/seed{seed}.{ext}').read_text(),render_pack_report(r,readable=readable))
