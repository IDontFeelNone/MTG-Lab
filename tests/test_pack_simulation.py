"""Actual synthetic pack execution; no real collation or gameplay claims."""
import copy
from contextlib import redirect_stdout
import hashlib
import io
import json
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch

from query import CanonicalQueryEngine
from query import QueryError
from simulation import ALGORITHM, MODEL, VERSION, PackSimulationError, load_pack_simulator, render_pack_report
from simulation.pack import _select, _ticket

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT/'tests/fixtures/pack_simulation_v0/data'
GAME = 'pack_fixture'
PRODUCT = 'fictional-pack'
PACK = 'fictional-definition'


def files(root):
    return {p.relative_to(root).as_posix(): p.read_bytes() for p in root.rglob('*') if p.is_file()}


class PackSimulationTests(unittest.TestCase):
    def test_exact_source_successors_additions_and_coherent_tampering_reject(self):
        import pack_simulation_preservation as guard
        import query_attachment_performance_preservation as previous
        for name,pin in guard.REPLACEMENTS.items():
            raw=(ROOT/name).read_bytes();old=guard.preceding_bytes(name,raw)
            self.assertEqual(hashlib.sha256(old).hexdigest(),pin['old_sha256'])
            self.assertEqual(guard.preceding_bytes(name,old),old)
            for bad in (raw+b'future',bytearray(raw)):
                with self.assertRaises(AssertionError):guard.preceding_bytes(name,bad)
            if name.startswith('src/'):
                row=dict(path=name,bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest())
                original=previous.historical_inventory_row(row)
                previous.assert_retained_row(original)
                with tempfile.TemporaryDirectory() as d:
                    path=Path(d)/name;path.parent.mkdir(parents=True);path.write_bytes(raw+b'future')
                    changed=dict(path=name,bytes=path.stat().st_size,sha256=hashlib.sha256(path.read_bytes()).hexdigest())
                    with self.assertRaises(AssertionError):previous.historical_inventory_row(changed,Path(d))
        for name in guard.ADDITIONS:
            self.assertTrue(guard.is_addition(ROOT/name,ROOT))
            with tempfile.TemporaryDirectory() as d:
                path=Path(d)/name;path.parent.mkdir(parents=True);path.write_bytes((ROOT/name).read_bytes()+b'future')
                with self.assertRaises(AssertionError):guard.is_addition(path,Path(d))
        self.assertFalse(guard.is_addition(ROOT/'src/simulation/future.py',ROOT))

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.data = Path(self.temp.name)/'data'; shutil.copytree(FIXTURE, self.data)
        self.game = self.data/'canonical/games'/GAME

    def generate(self, seed=42, **kwargs):
        return load_pack_simulator(GAME, data_root=self.data).generate(
            PRODUCT, pack_definition_id=PACK, seed=seed, **kwargs)

    def mutate(self, path, change):
        p = self.game/path; d = json.loads(p.read_text()); change(d); p.write_text(json.dumps(d))

    def refuse(self):
        with self.assertRaises(PackSimulationError) as caught: self.generate()
        value = caught.exception.as_dict()
        self.assertEqual(value['status'], 'NOT_READY_FOR_SIMULATION')
        self.assertNotIn('slots', value); self.assertFalse(value['production_authorized'])
        self.assertIn('NOT_READY_FOR_SIMULATION', render_pack_report(value, readable=True))

    def test_complete_pack_actual_golden_counts_and_slot_association(self):
        r = self.generate(); self.assertEqual(r['status'], 'GENERATED'); self.assertEqual(r['card_count'], 3)
        self.assertEqual(r['slots'], [dict(slot_id='base-slot', print_sheet_id='base-sheet',
            printing_ids=['pack_fixture.tst.2.en','pack_fixture.tst.2.en']),
            dict(slot_id='accent-slot',print_sheet_id='accent-sheet',printing_ids=['pack_fixture.tst.3.en'])])
        self.assertFalse(r['production_authorized']); self.assertIn('NON_PRODUCTION', r['scope'])

    def test_seed_reproduction_variation_and_independent_output_ownership(self):
        owner = load_pack_simulator(GAME, data_root=self.data)
        a = owner.generate(PRODUCT, pack_definition_id=PACK, seed=42)
        b = owner.generate(PRODUCT, pack_definition_id=PACK, seed=42)
        self.assertEqual(a,b)
        self.assertNotEqual(a['slots'],self.generate(1)['slots'])
        b['slots'][0]['printing_ids'].clear()
        self.assertEqual(a,owner.generate(PRODUCT, pack_definition_id=PACK, seed=42))

    def test_nonuniform_integer_intervals_and_rejection_sampling(self):
        entries = [('a',1),('b',3)]
        self.assertEqual([_select(entries,t) for t in range(4)],['a','b','b','b'])
        with self.assertRaises(PackSimulationError): _select(entries,4)
        # Force the single excluded 256-bit value for total3, then a valid block.
        first = type('Digest',(),{'digest':lambda self: b'\xff'*32})()
        second = type('Digest',(),{'digest':lambda self: b'\0'*32})()
        with patch('simulation.pack.hashlib.sha256',side_effect=[first,second]):
            self.assertEqual(_ticket(42,0,3),(0,2))
        digest=hashlib.sha256(ALGORITHM.encode()+b'\0' + b'42\0' + b'0').digest()
        self.assertEqual(_ticket(42,0,4),(int.from_bytes(digest,'big')%4,1))

    def test_exact_input_source_version_and_timestamp_metadata(self):
        r=self.generate(recorded_at='2026-11-09T00:00:00Z')
        self.assertEqual((r['schema_version'],r['simulator_version'],r['algorithm'],r['sampling_model']),
                         (VERSION,VERSION,ALGORITHM,MODEL))
        self.assertEqual((r['game'],r['product_id'],r['product_version_id'],r['pack_definition_id']),
                         (GAME,PRODUCT,'fictional-version',PACK))
        self.assertEqual(r['timestamp_authority'],'caller_supplied'); self.assertIsNone(r['database_version'])
        self.assertTrue(r['input_id'].startswith('sha256:')); self.assertTrue(r['query_snapshot_id'].startswith('sha256:'))
        self.assertEqual(r['input_id'],'sha256:4cbd3dd8c9d78ecf0a3503840507c0fbd711c96dbe8e07ca1712ef334fb5e8d2')
        self.assertEqual(len(r['source_references']),1)
        refs=[(e['kind'],e['id']) for e in r['evidence_references']]
        self.assertEqual(refs,sorted(set(refs)))
        self.assertEqual(r,self.generate(recorded_at='2026-11-09T00:00:00Z'))
        self.assertEqual(json.loads(render_pack_report(r)),r)
        self.assertIn('base-slot:',render_pack_report(r,readable=True))

    def test_source_content_binding_changes_without_inventing_authority(self):
        a=self.generate()
        self.mutate('sources/fictional-definition.json',lambda d:d['claims'].append('Additional fictional scope note.'))
        b=self.generate()
        self.assertNotEqual(a['source_references'],b['source_references']);self.assertNotEqual(a['input_id'],b['input_id'])
        self.assertEqual(a['slots'],b['slots']);self.assertFalse(b['production_authorized'])

    def test_input_files_and_retained_record_views_are_independent(self):
        before=files(self.data); self.generate();self.assertEqual(before,files(self.data))
        query=CanonicalQueryEngine(GAME,data_root=self.data,games_root=self.data/'canonical/games')
        raw=query.retained_record('base-sheet',entity_type='print_sheet');raw['entries'][0]['weight']=999
        self.assertEqual(query.retained_record('base-sheet',entity_type='print_sheet')['entries'][0]['weight'],1)
        with self.assertRaises(QueryError): query.retained_record('base-sheet',entity_type='slot')
        with self.assertRaises(QueryError): query.retained_record('absent',entity_type='print_sheet')
        self.assertEqual(before,files(self.data))

    def test_file_and_pool_order_determinism(self):
        a=self.generate()
        self.mutate('print_sheets/base-sheet/print-sheet.json',lambda d:d['entries'].reverse())
        b=self.generate()
        self.assertEqual(a['slots'],b['slots']);self.assertNotEqual(a['input_id'],b['input_id'])
        self.assertEqual([x['slot_id'] for x in b['slots']],['base-slot','accent-slot'])

    def test_invalid_weights_rejected_without_uniform_fallback(self):
        path='print_sheets/base-sheet/print-sheet.json'; original=(self.game/path).read_bytes()
        for value in (0,-1,True,1.5,'3',None,2**64):
            with self.subTest(weight=value):
                (self.game/path).write_bytes(original)
                self.mutate(path,lambda d:d['entries'][0].update(weight=value));self.refuse()
        (self.game/path).write_bytes(original)
        self.mutate(path,lambda d:d['entries'][0].pop('weight'));self.refuse()

    def test_legacy_coercion_or_unknown_versions_cannot_supply_missing_weights(self):
        # The compatibility reader could otherwise default a legacy missing weight to1.
        self.mutate('print_sheets/base-sheet/print-sheet.json',lambda d:(d.pop('schema_version'),d['entries'][0].pop('weight')))
        self.refuse()

    def test_empty_duplicate_and_unknown_printing_pools_rejected(self):
        path='print_sheets/base-sheet/print-sheet.json'; original=(self.game/path).read_bytes()
        for entries in ([],[dict(printing_id='foreign-printing',weight=1)],
                        [dict(printing_id='pack_fixture.tst.1.en',weight=1)]*2):
            with self.subTest(entries=entries):
                (self.game/path).write_bytes(original);self.mutate(path,lambda d:d.update(entries=entries));self.refuse()

    def test_unknown_slots_sheets_and_foreign_product_selection_rejected(self):
        self.mutate('packs/fictional-definition/pack-definition.json',lambda d:d.update(slot_ids=['unknown-slot']))
        self.refuse()
        owner_path=self.game/'packs/fictional-definition/pack-definition.json'
        shutil.copy2(FIXTURE/'canonical/games'/GAME/'packs/fictional-definition/pack-definition.json',owner_path)
        self.mutate('slots/base-slot/slot.json',lambda d:d.update(print_sheet_id='unknown-sheet'));self.refuse()
        with self.assertRaises(PackSimulationError):load_pack_simulator(GAME,data_root=FIXTURE).generate('foreign',seed=1)
        with self.assertRaises(PackSimulationError):load_pack_simulator(GAME,data_root=FIXTURE).generate(PRODUCT,pack_definition_id='foreign',seed=1)

    def test_missing_explicit_definition_selection_rejected(self):
        with self.assertRaisesRegex(PackSimulationError,'EXPLICIT_PACK_DEFINITION_SELECTION_REQUIRED'):
            load_pack_simulator(GAME,data_root=self.data).generate(PRODUCT,seed=1)

    def test_malformed_definitions_and_unsupported_collation_metadata_rejected(self):
        path='packs/fictional-definition/pack-definition.json';original=(self.game/path).read_bytes()
        for change in (lambda d:d.update(slot_ids=None),lambda d:d.update(slot_ids=[]),
                       lambda d:d['metadata'].update(simulation_model='physical-sequence'),
                       lambda d:d['metadata'].update(foil_frequency=0.5),lambda d:d.pop('metadata'),
                       lambda d:d.update(schema_version='v999'),lambda d:d.update(unrecognized=1)):
            (self.game/path).write_bytes(original);self.mutate(path,change);self.refuse()

    def test_unsupported_replacement_and_nonboolean_coercions_rejected(self):
        path='slots/base-slot/slot.json';original=(self.game/path).read_bytes()
        for replacement in (False,'false',1,None):
            with self.subTest(replacement=replacement):
                (self.game/path).write_bytes(original);self.mutate(path,lambda d:d.update(replacement=replacement));self.refuse()

    def test_seed_count_and_size_bounds(self):
        for seed in (-1,True,1.5,'42',2**64):
            with self.assertRaises(PackSimulationError):self.generate(seed)
        for count in (0,-1,True,1.5,1025):
            self.mutate('slots/base-slot/slot.json',lambda d:d.update(draw_count=count));self.refuse()
        for timestamp in (True,'yesterday','2026-11-09',[]):
            with self.assertRaises(PackSimulationError):load_pack_simulator(GAME,data_root=FIXTURE).generate(PRODUCT,pack_definition_id=PACK,seed=0,recorded_at=timestamp)
        self.assertEqual(load_pack_simulator(GAME,data_root=FIXTURE).generate(PRODUCT,
            pack_definition_id=PACK,seed=0)['seed'],0)

    def test_missing_or_unconfirmed_provenance_rejected(self):
        self.mutate('packs/fictional-definition/pack-definition.json',lambda d:d['provenance'][0].update(field_paths=['id']))
        self.refuse()
        shutil.copy2(FIXTURE/'canonical/games'/GAME/'packs/fictional-definition/pack-definition.json',self.game/'packs/fictional-definition/pack-definition.json')
        self.mutate('sources/fictional-definition.json',lambda d:d.update(verification_status='unverified'));self.refuse()

    def test_unavailable_or_invalid_catalog_never_falls_back(self):
        for root in (Path(self.temp.name)/'absent',self.data):
            if root==self.data:(self.game/'game.json').write_text('{broken')
            with self.assertRaises(PackSimulationError):load_pack_simulator(GAME,data_root=root)
        with self.assertRaises(PackSimulationError):load_pack_simulator(attachment=object(),data_root=FIXTURE)

    def test_valid_external_snapshot_has_no_simulation_capability_and_drift_rejects(self):
        from repository.snapshots import attach_snapshot
        from snapshot_fixture_builder import FIXTURES
        root=Path(self.temp.name)/'snapshot';shutil.copytree(FIXTURES/'lantern',root)
        expected=json.loads((root/'release-manifest.json').read_text())['snapshot_id']
        attachment=attach_snapshot(root,game='lantern',expected_snapshot_id=expected)
        with self.assertRaisesRegex(PackSimulationError,'CAPABILITY_UNAVAILABLE'):load_pack_simulator(attachment=attachment)
        (root/'data/canonical/games/lantern/game.json').write_text('{}')
        with self.assertRaises(PackSimulationError):load_pack_simulator(attachment=attachment)

    def test_public_cli_actual_generation_json_text_and_read_only(self):
        from mtglab.__main__ import main
        before=files(self.data)
        for fmt in ('json','text'):
            output=io.StringIO()
            with redirect_stdout(output):
                code=main(['--data-root',str(self.data),'pack','simulate','--game',GAME,'--product-id',PRODUCT,'--definition-id',PACK,'--seed','42','--format',fmt])
            self.assertEqual(code,0)
            if fmt=='json':self.assertEqual(json.loads(output.getvalue()),self.generate())
            else:self.assertIn('base-slot: pack_fixture.tst.2.en',output.getvalue())
        self.assertEqual(before,files(self.data))

    def test_current_mb2_public_refusal_machine_readable_human_readable_and_preserved(self):
        from mtglab.__main__ import main
        product_root=ROOT/'data/canonical/games/magic/products/mystery_booster_2'
        before=files(product_root)
        with self.assertRaises(PackSimulationError) as caught:load_pack_simulator().generate('mystery_booster_2',seed=42)
        reasons=set(caught.exception.requirements)
        self.assertTrue({'ADMITTED_PACK_DEFINITION_MISSING','ADMITTED_SLOT_DEFINITIONS_MISSING',
                         'VALIDATED_PRINTING_POOLS_AND_WEIGHTS_MISSING','EXPLICIT_COLLATION_MODEL_MISSING'}<=reasons)
        for fmt in ('json','text'):
            output=io.StringIO()
            with redirect_stdout(output):code=main(['--data-root',str(ROOT/'data'),'pack','simulate','--product-id','mystery_booster_2','--seed','42','--format',fmt])
            self.assertEqual(code,2);self.assertIn('NOT_READY_FOR_SIMULATION',output.getvalue())
            if fmt=='json':self.assertNotIn('slots',json.loads(output.getvalue()))
        self.assertEqual(before,files(product_root))
