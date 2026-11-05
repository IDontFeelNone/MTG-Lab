"""Actual six-land integration, public composition and fail-closed boundaries."""
from copy import deepcopy
from dataclasses import FrozenInstanceError
import hashlib
import io
import json
from pathlib import Path
import shutil
import tempfile
import time
import unittest
from contextlib import redirect_stdout, redirect_stderr
from unittest.mock import patch

from card_intelligence import land_overlay as o
from card_rules_pilot import contract as c, land_decision as d, mana_scenario_policy as hp
from land_test_support import ROOT, current_catalog_intact
from test_land_decision import decision_arguments

MATRIX = c.read_json(ROOT / 'docs/design/rules-card-intelligence-v1/identity-joins.json')
IDS = {r['name']:r['card_id'] for r in MATRIX['cards']}


def scenario(dimension, value):
    return hp.make_scenario([dict(dimension=dimension,value=value)]).to_dict()


class LandEvidenceOverlayTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.intact = current_catalog_intact(cls())
        if cls.intact:
            start = time.perf_counter()
            cls.overlay = o.load_land_overlay(**decision_arguments())
            cls.load_seconds = time.perf_counter() - start

    def live(self):
        if self.intact: return True
        # The actual nested 654-card writer changes current evidence. Require
        # rejection, with no historical fixture, fallback or inherited skip.
        with self.assertRaises(o.OverlayError) as caught: o.load_land_overlay(**decision_arguments())
        self.assertEqual(caught.exception.code,'EVIDENCE_ADMISSION_REJECTED')
        return False

    def card(self, name, context=None): return self.overlay.card(o.CARD_NAMESPACE,IDS[name],context).to_dict()

    def test_all_six_exact_cards_nine_accepted_subjects_and_owning_dossiers(self):
        if not self.live(): return
        seen=[]
        for expected in MATRIX['cards']:
            value=self.overlay.card(o.CARD_NAMESPACE,expected['card_id']).to_dict(); row=value['cards'][0]
            self.assertEqual(row['identity']['card_id'],expected['card_id'])
            self.assertEqual(row['identity']['display_name'],expected['name'])
            self.assertEqual(row['mechanical']['dossier_id'],expected['dossier_id'])
            self.assertEqual(value['decision_id'],d.DECISION_ID)
            self.assertEqual(value['accepted_collection_id'],d.COLLECTION_ID)
            self.assertFalse(value['authority']['canonical_admission']);self.assertFalse(value['authority']['production_eligible'])
            self.assertEqual(value['authority']['execution_authority'],'BLOCKED')
            self.assertEqual(set(value['authority']['permissions'].values()),{'NOT_ESTABLISHED'})
            for subject in row['subjects']:
                seen.append(subject['subject_id']); sem=subject['accepted_semantics']
                self.assertEqual(sem['historical_status'],'PENDING_NOT_ESTABLISHED')
                self.assertEqual(sem['current_status'],'ACCEPTED_BOUNDED_RETAINED_TEXT')
                self.assertEqual(dict(d.CANDIDATE_IDS)[subject['subject_id']],sem['candidate_id'])
                self.assertTrue(sem['rule_refs'])
                dossier=self.overlay.detailed(row['mechanical']['detailed_reference']).to_dict()
                self.assertEqual(dossier['card_identity']['card_id'],expected['card_id'])
                self.assertEqual(dossier['fields']['oracle_text'],row['mechanical']['facts']['oracle_text'])
        self.assertCountEqual(seen,d.SUBJECT_IDS)

    def test_separate_historical_current_production_and_pilot_statuses(self):
        if not self.live(): return
        for expected in MATRIX['cards']:
            row=self.overlay.card(o.CARD_NAMESPACE,expected['card_id']).to_dict()['cards'][0]; identity=row['identity']; joins=identity['joins']
            self.assertEqual(joins['historical_correspondence']['status'],'ESTABLISHED')
            self.assertEqual(joins['current_identifier_edge']['status'],expected['current_identifier_edge_status'])
            self.assertEqual(joins['current_identifier_edge']['identifier_ids'],expected['promoted_identifier_ids'])
            self.assertEqual(joins['operator_production']['status'],'IDENTITY_NOT_ESTABLISHED')
            self.assertEqual(joins['typed_seed']['status'],'IDENTITY_NOT_ESTABLISHED')
            self.assertEqual(joins['functional_role_pilot']['status'],'NOT_IN_SUPPORTED_COHORT')
            self.assertEqual(joins['contextual_comparison_pilot']['status'],'NOT_IN_SUPPORTED_COHORT')
            self.assertNotEqual(identity['printing']['printing_id'],identity['observation']['provider_record_id'])
            self.assertEqual(identity['printing']['historical_membership_count'],expected['printing_membership_count'])
        self.assertEqual(self.card('Command Tower')['cards'][0]['identity']['printing']['historical_membership_count'],111)
        absent=self.overlay.identity(o.CARD_NAMESPACE,IDS['Rishadan Port'],'current_identifier_edge').to_dict()
        self.assertEqual(absent['identity_status'],'IDENTITY_NOT_ESTABLISHED')
        prod=self.overlay.identity(o.CARD_NAMESPACE,IDS['Snow-Covered Wastes'],'operator_production').to_dict()
        self.assertEqual(prod['identity_status'],'IDENTITY_NOT_ESTABLISHED')

    def test_all_four_comparisons_original_calculations_and_references(self):
        if not self.live(): return
        for group in self.overlay.comparison_names:
            value=self.overlay.compare(group).to_dict(); comparison=value['comparison']
            explained=self.overlay.detailed(comparison['explanation_reference']).to_dict()
            hypothetical=self.overlay.detailed(comparison['scenario_reference']).to_dict()
            self.assertEqual(comparison['findings'],explained['comparison'])
            self.assertEqual(comparison['hypothetical_findings'],hypothetical['comparison'])
            self.assertEqual(len(value['cards']),2)
            self.assertTrue(comparison['missing_strategic_inputs'])
            self.assertEqual(self.overlay.validate_report(value).to_dict(),value)

    def test_cost_output_and_damage_ownership_separation(self):
        if not self.live(): return
        port={s['subject_id']:s for s in self.card('Rishadan Port')['cards'][0]['subjects']}
        self.assertEqual(port['port-mana']['hypothetical']['calculation']['written_cost'],'{T}')
        self.assertEqual(port['port-utility']['hypothetical']['calculation']['written_cost'],'{1}, {T}')
        self.assertIsNone(port['port-utility']['hypothetical']['calculation']['conditional_written_output'])
        city={s['subject_id']:s for s in self.card('City of Brass')['cards'][0]['subjects']}
        self.assertEqual(city['city-damage-trigger']['accepted_semantics']['proposed_kind'],'proposed_triggered_ability')
        self.assertIsNone(city['city-damage-trigger']['hypothetical']['calculation']['conditional_written_output'])
        citadel={s['subject_id']:s for s in self.card('Tarnished Citadel')['cards'][0]['subjects']}
        self.assertIsNone(citadel['citadel-colorless']['hypothetical']['calculation']['conditional_damage_clause_not_executed'])
        self.assertIsNotNone(citadel['citadel-color-choice']['hypothetical']['calculation']['conditional_damage_clause_not_executed'])

    def test_coffers_missing_zero_five_and_conflicting_counts(self):
        if not self.live(): return
        missing=self.card('Cabal Coffers');self.assertEqual(missing['state'],'UNSPECIFIED')
        for n in (0,1,5,37,hp.COUNT_LIMIT):
            v=self.card('Cabal Coffers',scenario('controlled_swamp_count',n));calc=v['cards'][0]['subjects'][0]['hypothetical']['calculation']
            self.assertEqual(v['state'],'SUPPLIED');self.assertEqual(calc['conditional_written_output']['quantity'],n)
            self.assertEqual(calc['written_cost'],'{2}, {T}')
            self.assertIn('No actual activation', ' '.join(calc['unknown_game_inputs']))
        context=hp.make_scenario([dict(dimension='controlled_swamp_count',value=n) for n in (0,5)]).to_dict()
        v=self.card('Cabal Coffers',context);self.assertEqual(v['state'],'CONFLICTING')
        self.assertIsNone(v['cards'][0]['subjects'][0]['hypothetical']['calculation']['conditional_written_output'])

    def test_tower_missing_empty_and_color_sets(self):
        if not self.live(): return
        self.assertEqual(self.card('Command Tower')['state'],'UNSPECIFIED')
        for colors in ([],['W'],['W','B'],list(hp.COLORS)):
            v=self.card('Command Tower',scenario('commander_color_identity',colors));calc=v['cards'][0]['subjects'][0]['hypothetical']['calculation']
            self.assertEqual(v['state'],'SUPPLIED');self.assertEqual(calc['conditional_written_output']['colors'],colors)
            self.assertTrue(calc['conditional_written_output']['empty_set_does_not_establish_actual_unusability'])

    def test_comparison_context_does_not_leak(self):
        if not self.live(): return
        for group,dim,value,affected in (('variable-output','controlled_swamp_count',5,'coffers-mana'),('color-context','commander_color_identity',['W','B'],'tower-mana')):
            report=self.overlay.compare(group,scenario(dim,value)).to_dict()
            for row in report['cards']:
                for subject in row['subjects']:
                    calc=subject['hypothetical']['calculation']
                    self.assertEqual(bool(calc['supplied_assumptions']),subject['subject_id']==affected)
        with self.assertRaises(ValueError):self.card('Snow-Covered Wastes',scenario('controlled_swamp_count',5))
        with self.assertRaises(ValueError):self.overlay.compare('damage-ownership',scenario('commander_color_identity',['W']))

    def test_invalid_context_contract_and_foreign_requests(self):
        if not self.live(): return
        for namespace,card in (('Card',IDS['Cabal Coffers']),(o.PRINTING_NAMESPACE,IDS['Cabal Coffers']),('',IDS['Cabal Coffers']),(o.CARD_NAMESPACE,'Cabal Coffers'),(o.CARD_NAMESPACE,'foreign')):
            with self.assertRaises(o.OverlayError):self.overlay.card(namespace,card)
        for group in ('foreign','Nykthos',None,[]):
            with self.assertRaises(o.OverlayError):self.overlay.compare(group)
        for n in (-1,True,1.0,1000001,'5',None):
            with self.assertRaises(ValueError):self.card('Cabal Coffers',scenario('controlled_swamp_count',n))
        for colors in (['B','W'],['W','W'],['C'],['foreign'],True):
            with self.assertRaises(ValueError):self.card('Command Tower',scenario('commander_color_identity',colors))
        with self.assertRaises(ValueError):self.card('Cabal Coffers',{'game_state':{}})
        with self.assertRaises(o.OverlayError):self.overlay.identity(o.CARD_NAMESPACE,IDS['Cabal Coffers'],'production_approved')

    def test_strict_expected_reports_and_coherently_rehashed_tampering(self):
        if not self.live(): return
        original=self.card('Rishadan Port')
        for alteration in ('extra','production','candidate','mechanical','join','cost','missing','bool'):
            value=deepcopy(original);row=value['cards'][0]
            if alteration=='extra':value['score']=100
            elif alteration=='production':value['authority']['production_eligible']=True
            elif alteration=='candidate':row['subjects'][0]['accepted_semantics']['candidate_id']=dict(d.CANDIDATE_IDS)['tower-mana']
            elif alteration=='mechanical':row['mechanical']['dossier_id']=MATRIX['cards'][0]['dossier_id']
            elif alteration=='join':row['identity']['joins']['current_identifier_edge']['status']='ESTABLISHED'
            elif alteration=='cost':row['subjects'][0]['hypothetical']['calculation']['written_cost']='{0}'
            elif alteration=='missing':del row['identity']['joins']['operator_production']
            else:value['authority']['canonical_admission']=0
            value=c.seal(o.VERSION,value,'report_id')
            with self.assertRaises(ValueError):self.overlay.validate_report(value)
        raw=c.canonical(original)
        with self.assertRaises(ValueError):self.overlay.parse_report(raw.replace(b'"kind":"card"',b'"kind":"card","kind":"card"'))
        with self.assertRaises(ValueError):self.overlay.parse_report(b' '*65537)

    def test_immutable_ownership_and_independent_decoded_views(self):
        if not self.live(): return
        context=scenario('controlled_swamp_count',5);doc=self.overlay.card(o.CARD_NAMESPACE,IDS['Cabal Coffers'],context)
        original=doc.to_json();context['assumptions'][0]['value']=99
        doc.to_dict()['cards'].clear();self.assertEqual(doc.to_json(),original)
        with self.assertRaises(FrozenInstanceError):self.overlay._cards=b'{}'
        ref=doc.to_dict()['cards'][0]['mechanical']['detailed_reference']
        detail=self.overlay.detailed(ref);expected=detail.to_json();detail.to_dict()['fields'].clear()
        self.assertEqual(self.overlay.detailed(ref).to_json(),expected)
        o.policy_document().to_dict()['rules'].clear();self.assertTrue(o.policy_document().to_dict()['rules'])

    def test_integrity_checked_detailed_route_and_historical_parity(self):
        if not self.live(): return
        doc=self.card('City of Brass');ref=doc['full_evidence_reference'];detail=self.overlay.detailed(ref)
        self.assertEqual(len(detail.to_json().encode()),689253)
        self.assertEqual(hashlib.sha256(detail.to_json().encode()).hexdigest(),d.OVERVIEW_SHA256)
        self.assertEqual(detail.to_dict()['report_id'],d.OVERVIEW_ID)
        for subject in doc['cards'][0]['subjects']:
            explained=self.overlay.detailed(subject['explanation_reference']).to_dict()
            hypothetical=self.overlay.detailed(subject['scenario_reference']).to_dict()
            self.assertEqual(explained['subjects'][0],subject['explanation'])
            self.assertEqual(hypothetical['subjects'][0],subject['hypothetical'])
        for field in ('sha256','bytes','identity','route'):
            changed=deepcopy(ref);changed[field]='altered'
            with self.assertRaises(ValueError):self.overlay.detailed(changed)

    def test_public_batch_composition_one_mci_and_fresh_readmission(self):
        if not self.live(): return
        from card_intelligence.mechanics import MechanicalCardIntelligence as M
        from query import CanonicalQueryEngine as Q
        from card_rules_pilot import land_context
        with patch.object(M,'from_attachment',wraps=M.from_attachment) as m, patch.object(Q,'from_attachment',wraps=Q.from_attachment) as q, patch.object(land_context,'read_context',wraps=land_context.read_context) as rules:
            overlay=o.load_land_overlay(**decision_arguments())
            for cid in overlay.card_ids:overlay.card(o.CARD_NAMESPACE,cid)
            for group in overlay.comparison_names:overlay.compare(group)
            self.assertEqual(m.call_count,1);self.assertEqual(q.call_count,1);self.assertEqual(rules.call_count,1)
        with self.assertRaises(ValueError):o.e.from_decision({})
        with self.assertRaises(ValueError):o.h.from_explanations({})
        # Deliberately corrupt a copy of an admitted immutable object to exercise
        # the public composition seam against coherent private-state tampering.
        # This adversarial fixture is never a production composition technique.
        forged=deepcopy(self.overlay._explanations)
        snapshot=json.loads(forged._snapshot)
        snapshot['rows'][0]['findings'][0]['text']='fabricated capability'
        object.__setattr__(forged,'_snapshot',c.owned(snapshot))
        with self.assertRaises(ValueError):o.h.from_explanations(forged)


    def test_altered_decision_mechanical_and_historical_evidence_reject(self):
        if not self.live(): return
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            decision=root/'decision';shutil.copytree(ROOT/'data/review/land-semantic-decisions',decision)
            path=decision/d.OWNER_RECORD;value=c.read_json(path);value['decision']['status']='APPROVED_ALL_CARDS'
            path.write_bytes(c.canonical(c.seal(d.DECISION_VERSION,value,'decision_id')))
            with self.assertRaises(o.OverlayError):o.load_land_overlay(**decision_arguments(decision_root=decision))
        from card_rules_pilot import land_cards
        from test_card_rules_pilot_cards import evidence_copy
        with tempfile.TemporaryDirectory() as tmp:
            root=evidence_copy(tmp)
            (root/land_cards.DOSSIER_REFERENCE).unlink()
            with self.assertRaises(o.OverlayError):o.load_land_overlay(**decision_arguments(mechanical_root=root))
        from card_intelligence.mechanics import MechanicalCardIntelligence as M, MechanicalDossier, content_identity
        real=M.dossier
        def tampered(reader,cid):
            value=real(reader,cid).to_dict();value['fields']['oracle_text']['value']='fabricated output'
            value['dossier_id']=content_identity({k:v for k,v in value.items() if k!='dossier_id'})
            return MechanicalDossier(value)
        with patch.object(M,'dossier',tampered):
            with self.assertRaises(o.OverlayError):o.load_land_overlay(**decision_arguments())
        from projection.historical_evidence import load_historical_admission
        with self.assertRaises(RuntimeError):load_historical_admission(data_root=ROOT/'data',audit_reference=MATRIX['historical_audit_path'].removeprefix('data/'),expected_audit_sha256='0'*64,expected_payload_sha256='0'*64)

    def test_compact_size_determinism_readable_parity_and_bounded_performance(self):
        if not self.live(): return
        self.assertLess(self.load_seconds,30)
        for kind,selector in [('card',cid) for cid in self.overlay.card_ids]+[('comparison',g) for g in self.overlay.comparison_names]:
            start=time.perf_counter();doc=self.overlay.card(o.CARD_NAMESPACE,selector) if kind=='card' else self.overlay.compare(selector)
            raw=doc.to_json().encode();text=o.render_overlay(doc);self.assertLess(time.perf_counter()-start,5)
            self.assertLessEqual(len(raw),o.REPORT_LIMIT);self.assertLessEqual(len(text.encode()),o.READABLE_LIMIT)
            self.assertEqual(self.overlay.parse_report(raw).to_json(),doc.to_json())
            self.assertIn(doc.to_dict()['report_id'],text)
            for row in doc.to_dict()['cards']:
                self.assertIn(row['identity']['card_id'],text)
                for subject in row['subjects']:
                    self.assertIn(subject['accepted_semantics']['candidate_id'],text)
                    self.assertIn(subject['hypothetical']['calculation']['calculation_id'],text)
                    for finding in subject['explanation']['findings']:self.assertIn(finding['text'],text)
            self.assertNotIn('"context":{"',text)

    def test_retained_demonstrations_reproduce_actual_reports(self):
        if not self.live(): return
        receipt=c.read_json(ROOT/'docs/examples/six-land-overlay-v1.json')
        self.assertEqual(receipt['policy_id'],o.POLICY_ID)
        self.assertEqual(len(receipt['reports']),10)
        for row in receipt['reports']:
            doc=self.overlay.card(o.CARD_NAMESPACE,row['selector'],row['scenario']) if row['kind']=='card' else self.overlay.compare(row['selector'],row['scenario'])
            self.assertEqual(doc.to_dict()['report_id'],row['report_id'])
            self.assertEqual(len(doc.to_json().encode()),row['canonical_bytes'])
            self.assertEqual(len(o.render_overlay(doc).encode()),row['readable_bytes'])
        for row in receipt['missing_zero_empty_conflicting']:
            doc=self.overlay.card(o.CARD_NAMESPACE,row['card_id'],row['scenario'])
            self.assertEqual(doc.to_dict()['report_id'],row['report_id'])
            self.assertEqual(doc.to_dict()['state'],row['state'])
        self.assertEqual(self.overlay.detailed(receipt['verified_historical_reference']).to_dict()['report_id'],d.OVERVIEW_ID)

    def test_actual_cli_read_only_and_finite_preservation_adapters(self):
        if not self.live(): return
        from card_intelligence.land_overlay_cli import main
        from overlay_preservation_support import historical_source_bytes, COMPOSITION_SOURCE_PINS
        import proposed_spell_packet_analysis_preservation as guard
        expected_sources={'src/card_intelligence/land_overlay.py','src/card_intelligence/land_overlay_cli.py','src/projection/historical_evidence.py'}
        self.assertEqual(guard.LAND_OVERLAY_SOURCE_PATHS,expected_sources)
        for name in expected_sources:
            self.assertTrue(guard.is_packet_analysis_addition(ROOT/name))
            self.assertFalse(guard.is_packet_analysis_addition(ROOT/(name+'.future')))
        for name,pair in COMPOSITION_SOURCE_PINS.items():
            raw=(ROOT/name).read_bytes();old=historical_source_bytes(name,raw)
            self.assertEqual(hashlib.sha256(old).hexdigest(),pair['historical']['sha256'])
            for changed in (raw+b'future',b'X'+raw[1:],bytearray(raw)):
                with self.assertRaises(AssertionError):historical_source_bytes(name,changed)
        names=['data/canonical/state.json','data/review/mechanical-card-cohort/dossiers.jsonl','data/review/land-semantic-decisions/owner-acceptance-v1.json','.github/workflows/python-validation.yml']
        before={n:hashlib.sha256((ROOT/n).read_bytes()).hexdigest() for n in names}
        args=[]
        for key,value in decision_arguments().items():args += ['--'+key.replace('_','-'),str(value)]
        output=io.StringIO()
        with redirect_stdout(output):
            self.assertEqual(main(args+['--json','card','--namespace',o.CARD_NAMESPACE,'--card-id',IDS['Snow-Covered Wastes']]),0)
        self.overlay.validate_report(json.loads(output.getvalue()))
        self.assertEqual(before,{n:hashlib.sha256((ROOT/n).read_bytes()).hexdigest() for n in names})

    def test_cli_read_only_actual_entry_points_and_conflict_exit(self):
        if not self.live(): return
        from card_intelligence.land_overlay_cli import main
        args=[]
        for key,value in decision_arguments().items():args += ['--'+key.replace('_','-'),str(value)]
        for command,expected in ((['card','--namespace',o.CARD_NAMESPACE,'--card-id',IDS['Cabal Coffers'],'--swamp-count','5'],0),(['compare','variable-output','--swamp-count','0'],0),(['identity','--namespace',o.CARD_NAMESPACE,'--card-id',IDS['Rishadan Port'],'--join','current_identifier_edge'],4),(['card','--namespace','foreign','--card-id',IDS['Cabal Coffers']],2),(['card','--namespace',o.CARD_NAMESPACE,'--card-id',IDS['Cabal Coffers'],'--swamp-count','0','--swamp-count','5'],3)):
            output,error=io.StringIO(),io.StringIO()
            # Reuse only the already admitted private batch for formatting/CLI
            # tests; separate test above proves the real factory admission.
            with patch('card_intelligence.land_overlay_cli.load_land_overlay',return_value=self.overlay),redirect_stdout(output),redirect_stderr(error):
                status=main(args+['--json']+command)
            self.assertEqual(status,expected,error.getvalue())
            if expected!=2:self.overlay.validate_report(json.loads(output.getvalue()))
            else:self.assertEqual(json.loads(error.getvalue())['code'],'UNSUPPORTED_NAMESPACE')


if __name__=='__main__': unittest.main()
