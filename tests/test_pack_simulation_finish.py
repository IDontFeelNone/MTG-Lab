"""Executable fictional finish outcomes; no physical MB2 distribution claims."""
from contextlib import redirect_stdout
import hashlib
import io
import json
from pathlib import Path
import shutil
import tempfile
import unittest

from simulation import FINISH_MODEL, FINISH_VERSION, PackSimulationError, load_pack_simulator, render_pack_report
from simulation.pack import _select
from validation import validate_document
from test_pack_simulation import files

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT/'tests/fixtures/pack_simulation_v01/data'
GAME='pack_fixture'
P1='pack_fixture.tst.1.en'
P2='pack_fixture.tst.2.en'


class FinishSimulationTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.data=Path(self.temp.name)/'data';shutil.copytree(FIXTURE,self.data)
        self.game=self.data/'canonical/games'/GAME

    def generate(self,seed=1):
        return load_pack_simulator(GAME,data_root=self.data).generate('fictional-pack',
            pack_definition_id='fictional-definition',seed=seed)

    def mutate(self,path,change):
        p=self.game/path;d=json.loads(p.read_text());change(d);p.write_text(json.dumps(d))

    def refuse(self):
        with self.assertRaises(PackSimulationError) as caught:self.generate()
        self.assertEqual(caught.exception.as_dict()['status'],'NOT_READY_FOR_SIMULATION')
        self.assertNotIn('slots',caught.exception.as_dict())

    def test_seeded_same_printing_distinct_finishes_and_explicit_version(self):
        a=self.generate(1);b=self.generate(2)
        self.assertEqual(a['schema_version'],FINISH_VERSION)
        self.assertEqual(a['sampling_model'],FINISH_MODEL)
        self.assertEqual(a['slots'][0]['outcomes'],[dict(printing_id=P1,finish_id='foil'),dict(printing_id=P2,finish_id='nonfoil')])
        self.assertEqual(b['slots'][0]['outcomes'][1],dict(printing_id=P1,finish_id='nonfoil'))
        self.assertEqual(a,self.generate(1));self.assertNotEqual(a['slots'],b['slots'])
        self.assertTrue(all('printing_ids' not in s for s in a['slots']))
        self.assertEqual(a['card_count'],sum(len(s['outcomes']) for s in a['slots']))
        self.assertFalse(a['production_authorized'])

    def test_exact_finish_weight_intervals_without_floating_point(self):
        entries=[((P1,'foil'),3),((P1,'nonfoil'),1),((P2,'nonfoil'),2)]
        self.assertEqual([_select(entries,t) for t in range(6)],[(P1,'foil')]*3+[(P1,'nonfoil')]+[(P2,'nonfoil')]*2)

    def test_missing_null_wrong_or_unknown_finish_rejected(self):
        path='print_sheets/base-sheet/print-sheet.json';original=(self.game/path).read_bytes()
        for value in (None,True,1,[],{},'', 'unknown'):
            with self.subTest(finish=value):
                (self.game/path).write_bytes(original)
                self.mutate(path,lambda d:d['entries'][0].update(finish_id=value));self.refuse()
        (self.game/path).write_bytes(original)
        self.mutate(path,lambda d:d['entries'][0].pop('finish_id'));self.refuse()

    def test_known_finish_not_supported_by_printing_rejected(self):
        self.mutate('print_sheets/base-sheet/print-sheet.json',lambda d:d['entries'][2].update(finish_id='foil'));self.refuse()

    def test_duplicate_pair_refused_but_multiple_finishes_allowed(self):
        self.generate()
        self.mutate('print_sheets/base-sheet/print-sheet.json',lambda d:d['entries'].append(dict(d['entries'][0],weight=7)));self.refuse()

    def test_new_sheet_closed_schema_and_explicit_weights(self):
        path='print_sheets/base-sheet/print-sheet.json';original=(self.game/path).read_bytes()
        for change in (lambda d:d['entries'][0].update(extra=True),lambda d:d['entries'][0].pop('weight'),
                       lambda d:d.update(schema_version='v999'),lambda d:d.update(entries=None),
                       lambda d:d.update(provenance=[])):
            (self.game/path).write_bytes(original);self.mutate(path,change);self.refuse()
        for w in (True,0,-1,1.5,'3',None,2**64):
            (self.game/path).write_bytes(original);self.mutate(path,lambda d:d['entries'][0].update(weight=w));self.refuse()

    def test_schema_and_typed_sheet_preserve_explicit_pair(self):
        from repository.canonical import CanonicalRepository
        owner=CanonicalRepository(GAME,games_root=self.data/'canonical/games')
        sheet=next(s for s in owner.sheets if s.id=='base-sheet')
        self.assertEqual(sheet.schema_version,'v3')
        self.assertEqual([(e.printing_id,e.finish_id,e.weight) for e in sheet.entries],[(P1,'nonfoil',1),(P1,'foil',3),(P2,'nonfoil',2)])
        raw=json.loads((self.game/'print_sheets/base-sheet/print-sheet.json').read_text())
        validate_document(raw,'print-sheet','v3')
        with self.assertRaises(ValueError):validate_document(raw,'print-sheet','v2')

    def test_model_version_mismatch_never_silently_reinterprets(self):
        self.mutate('packs/fictional-definition/pack-definition.json',lambda d:d['metadata'].update(simulation_model='independent-weighted-with-replacement-v1'));self.refuse()

    def test_printing_finish_assertions_must_be_explicit_consistent_and_source_bound(self):
        path=f'printings/{P1}/printing.json';original=(self.game/path).read_bytes()
        changes=[lambda d:d.update(finishes={'status':'unknown'}),lambda d:d.pop('finishes'),
                 lambda d:d['assertions'][-1].update(asserted_value=['nonfoil']),
                 lambda d:d['assertions'][-1].update(status='candidate'),
                 lambda d:d['assertions'][-1].update(verification_status='unverified'),
                 lambda d:d['assertions'][-1].update(subject_id=P2),
                 lambda d:d['assertions'][-1].update(evidence_class='unknown')]
        for change in changes:
            (self.game/path).write_bytes(original);self.mutate(path,change);self.refuse()

    def test_finish_identity_must_exist_in_admitted_namespace(self):
        (self.game/'finishes/foil.json').unlink();self.refuse()

    def test_provenance_and_finish_eligibility_are_in_input_identity(self):
        a=self.generate();refs={(r['kind'],r['id']) for r in a['evidence_references']}
        self.assertIn(('finish','foil'),refs);self.assertIn(('finish','nonfoil'),refs)
        self.assertIn(('printing',P1),refs)
        self.assertEqual(a['input_id'],'sha256:43177ed777da2d687eeee56a872e3a35d73076777fabb88428a2c157a7a2f0e1')
        self.mutate('sources/fictional-definition.json',lambda d:d['claims'].append('Additional supplied fictional note.'))
        b=self.generate();self.assertNotEqual(a['input_id'],b['input_id']);self.assertNotEqual(a['source_references'],b['source_references'])
        self.assertEqual(a['slots'],b['slots'])

    def test_input_snapshot_and_result_ownership_and_stable_pool_order(self):
        before=files(self.data);owner=load_pack_simulator(GAME,data_root=self.data)
        a=owner.generate('fictional-pack',pack_definition_id='fictional-definition',seed=1)
        b=owner.generate('fictional-pack',pack_definition_id='fictional-definition',seed=1)
        b['slots'][0]['outcomes'][0]['finish_id']='forged'
        self.assertEqual(a,owner.generate('fictional-pack',pack_definition_id='fictional-definition',seed=1))
        self.assertEqual(before,files(self.data))
        self.mutate('print_sheets/base-sheet/print-sheet.json',lambda d:d['entries'].reverse())
        c=self.generate();self.assertEqual(a['slots'],c['slots']);self.assertNotEqual(a['input_id'],c['input_id'])

    def test_public_cli_json_readable_and_api_parity(self):
        from mtglab.__main__ import main
        before=files(self.data)
        for fmt in ('json','text'):
            out=io.StringIO()
            with redirect_stdout(out):code=main(['--data-root',str(self.data),'pack','simulate','--game',GAME,'--product-id','fictional-pack','--definition-id','fictional-definition','--seed','1','--format',fmt])
            self.assertEqual(code,0)
            if fmt=='json':self.assertEqual(json.loads(out.getvalue()),self.generate())
            else:
                self.assertIn('pack-simulation-v0.1',out.getvalue());self.assertIn(P1+' [foil]',out.getvalue())
            self.assertEqual(out.getvalue(),render_pack_report(self.generate(),readable=fmt=='text'))
        self.assertEqual(before,files(self.data))

    def test_all_seeded_results_remain_in_declared_finish_pools(self):
        owner=load_pack_simulator(GAME,data_root=self.data)
        allowed={(P1,'foil'),(P1,'nonfoil'),(P2,'nonfoil')}
        for seed in range(16):
            r=owner.generate('fictional-pack',pack_definition_id='fictional-definition',seed=seed)
            self.assertEqual(len(r['slots'][0]['outcomes']),2)
            self.assertTrue(all((o['printing_id'],o['finish_id']) in allowed for o in r['slots'][0]['outcomes']))

    def test_retained_examples_are_actual_public_outputs_including_v0(self):
        examples=ROOT/'tests/fixtures/pack_simulation_v01/examples'
        for version,seeds in (('v0',(1,)),('v01',(1,2))):
            owner=load_pack_simulator(GAME,data_root=ROOT/f'tests/fixtures/pack_simulation_{version}/data')
            for seed in seeds:
                report=owner.generate('fictional-pack',pack_definition_id='fictional-definition',seed=seed)
                for readable,ext in ((False,'json'),(True,'txt')):
                    self.assertEqual((examples/f'{version}-seed{seed}.{ext}').read_text(),
                                     render_pack_report(report,readable=readable))

    def test_exact_successor_preservation_and_coherently_rehashed_tamper(self):
        import finish_simulation_preservation as guard
        for name,pin in guard.ledger()['replacements'].items():
            raw=(ROOT/name).read_bytes();old=guard.preceding_bytes(name,raw)
            self.assertEqual(hashlib.sha256(old).hexdigest(),pin['old_sha256'])
            for bad in (raw+b'future',bytearray(raw)):
                with self.assertRaises(AssertionError):guard.preceding_bytes(name,bad)
        for name in guard.ledger()['additions']:
            self.assertTrue(guard.is_addition(ROOT/name,ROOT))
        with tempfile.TemporaryDirectory() as d:
            name=next(iter(guard.ledger()['replacements']));p=Path(d)/name;p.parent.mkdir(parents=True);p.write_bytes((ROOT/name).read_bytes()+b'future')
            import query_attachment_performance_preservation as previous
            row=dict(path=name,bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest())
            with self.assertRaises(AssertionError):previous.historical_inventory_row(row,Path(d))
