"""Original fixture vertical through the real importer, inspector and reasoner."""
from copy import deepcopy
from dataclasses import replace
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from card_intelligence import candidate_mana as api
from card_intelligence.mechanics import MechanicalCardIntelligence
from card_intelligence.rules_reasoning import load_rules_reasoner, CONTEXT_ID
from card_rules_pilot import contract as c
from providers.mtgjson.private_policy import canonical
import test_mtgjson_evidence_handoff as handoff

ROOT = Path(__file__).parents[1]
FIXTURE = ROOT/'tests/fixtures/candidate_mana_v1/passages.json'


def request(card='cloth-unit', printing='cloth-edition', reasoning=None):
    return dict(card_id=card, printing_id=printing, evidence_id=None, reasoning=reasoning)


def hypothesis(**state):
    return dict(interpretation_premise=api.HYPOTHESIS,
        characteristics=dict(chosen_targets=0, self_replacement='ABSENT'),
        state=dict(mana_payment_request='SPELL_CASTING_MANA_PAYMENT', priority='NO',
                   same_ability_unresolved='NO', current_mana_output='ZERO', **state))


class CandidateManaTests(unittest.TestCase):
    def setUp(self):
        self.h = handoff.EvidenceHandoffTests('runTest')
        self.h.setUp(); self.addCleanup(self.h.doCleanups)
        self.rows = self.h.document['data']
        for partition in self.rows.values():
            for row in partition['cards']:
                row['text'] = '{T}: Add {G}.' if row['identifiers']['scryfallOracleId']=='cloth-unit' else '{T}: Add {C}{C}.'

    def build(self, **prepare):
        self.h.prepare(**prepare)
        self.report = self.h.run_import()
        self.h.fixture=handoff.build_intelligence_fixture(self.h.root/'catalog-fixture')
        self.h.query=handoff.CanonicalQueryEngine.from_attachment(handoff.attach_fixture(self.h.fixture))
        self.consumer = api.load_candidate_mana_interpreter(self.h.query,
            expected_query_snapshot_id=self.h.query.snapshot().snapshot_id,
            evidence_directory=self.h.workspace/'output', profile=self.h.profile,
            expected_report_id=self.report['report_id'], review_root=ROOT/'reference-reviews')
        return self.consumer

    def test_actual_import_inspection_proposal_review_and_native_reasoning_vertical(self):
        self.build()
        original={p:p.read_bytes() for p in self.h.fixture['catalog'].rglob('*') if p.is_file()}
        with patch.object(MechanicalCardIntelligence, '_load_source', side_effect=AssertionError('blocked reader')):
            first=self.consumer.assess(request(reasoning=hypothesis())).to_dict()
            second=self.consumer.assess(request('copper-unit','copper-edition')).to_dict()
        self.assertEqual(first['status'],'SUPPORTED_COMPLETE')
        self.assertEqual([(x['symbol'],x['quantity']) for x in first['proposal']['written_characteristics']['effect']['symbols']],[('G',1)])
        self.assertEqual([(x['symbol'],x['quantity']) for x in second['proposal']['written_characteristics']['effect']['symbols']],[('C',2)])
        self.assertEqual(first['proposal']['review']['status'],'requires_review')
        self.assertEqual(first['proposal']['written_characteristics']['cost']['literal'],'{T}')
        self.assertEqual(first['review_criteria']['native_result']['policy_id'],first['review_criteria']['policy_id'])
        native=first['native_conditional_reasoning']
        self.assertEqual(native['decision'],'PAYMENT_TIMING_EXCEPTION_APPLIES')
        reasoner=load_rules_reasoner(review_root=ROOT/'reference-reviews',expected_context_id=CONTEXT_ID)
        self.assertEqual(native,reasoner.assess(native['input']).to_dict())
        self.assertEqual(native['input']['state']['current_mana_output'],'ZERO')
        for result in (first,second):
            self.assertEqual(result['authority']['semantic_authority'],'NOT_ESTABLISHED')
            self.assertEqual(result['authority']['execution_authority'],'BLOCKED')
            self.assertFalse(result['authority']['canonical_admission'])
            self.assertFalse(result['authority']['admitted_dossier_populated'])
            self.assertEqual(result['authority']['actual_mana_output'],'UNKNOWN')
        self.assertEqual(original,{p:p.read_bytes() for p in self.h.fixture['catalog'].rglob('*') if p.is_file()})
        native_mechanics=MechanicalCardIntelligence.from_attachment(handoff.attach_fixture(self.h.fixture),
            data_root=self.h.fixture['mechanical_data'],expected_query_snapshot_id=self.h.query.snapshot().snapshot_id,
            source_directory=self.h.fixture['source_directory'])
        dossier=native_mechanics.dossier('cloth-unit').to_json()
        self.consumer.assess(request())
        self.assertEqual(dossier,native_mechanics.dossier('cloth-unit').to_json())
        self.assertNotIn('{T}: Add {G}.',dossier)

    def test_exact_provenance_spans_and_normalization(self):
        for p in self.rows.values():
            for row in p['cards']:
                if row['identifiers']['scryfallOracleId']=='cloth-unit':row['text']='{T}  :   Add {G}.'
        self.build();r=self.consumer.assess(request()).to_dict()
        evidence=r['evidence']['selected_occurrence'];text=self.rows['EQA']['cards'][0]['text']
        self.assertEqual(evidence['text']['sha256'],hashlib.sha256(text.encode()).hexdigest())
        self.assertEqual(evidence['text']['source_pointer'],'/data/EQA/cards/0/text')
        self.assertEqual(evidence['source_use_profile_id'] if 'source_use_profile_id' in evidence else
                         r['evidence']['source_use_profile_id'],self.h.profile.receipt()['profile_id'])
        self.assertEqual(evidence['source_row'],0)
        self.assertEqual(evidence['text']['face_boundary']['kind'],'WHOLE_CARD')
        for field in ('cost','effect','mana','whole_passage'):
            s=r['proposal']['spans'][field]
            self.assertEqual(s['encoding'],'UTF-8')
            self.assertTrue(text.encode()[s['start']:s['end']])
        self.assertEqual(r['proposal']['normalization']['canonical_spelling'],'{T}: Add {G}.')
        for trait in r['proposal']['proposed_rules_characteristics'].values():
            self.assertTrue(trait['derivation']['span_refs'])
            self.assertEqual(trait['review_status'],'requires_review')

    def test_grammar_is_closed_complete_and_not_color_or_card_specific(self):
        fixture=json.loads(FIXTURE.read_bytes())
        for text in fixture['supported']:
            with self.subTest(text=text):self.assertEqual(api._recognize(text)['status'],'SUPPORTED_COMPLETE')
        for text in fixture['unsupported']:
            with self.subTest(text=text):
                r=api._recognize(text)
                self.assertNotEqual(r['status'],'SUPPORTED_COMPLETE');self.assertIsNone(r['proposal'])
        self.assertIsNone(api._recognize('x'*8193)['proposal'])
        self.assertIsNone(api._recognize('{T}'+(' '*9)+': Add {G}.')['proposal'])
        self.assertIsNone(api._recognize('{T}: Add {G}.\x00')['proposal'])

    def test_supported_substring_cannot_enable_reasoning(self):
        for p in self.rows.values():
            for row in p['cards']:row['text']='A token has "{T}: Add {G}."'
        self.build();r=self.consumer.assess(request()).to_dict()
        self.assertIsNone(r['proposal']);self.assertIsNone(r['review_criteria'])
        self.assertIn('QUOTED_OR_GRANTED_ABILITY',r['diagnostics'])
        with self.assertRaisesRegex(api.CandidateInterpretationError,'complete supported'):
            self.consumer.assess(request(reasoning=hypothesis()))

    def test_unparsed_suffix_never_proves_absent_targets(self):
        for p in self.rows.values():
            for row in p['cards']:row['text']='{T}: Add {G}. Do something not represented here.'
        self.build();r=self.consumer.assess(request()).to_dict()
        self.assertEqual(r['status'],'PARTIAL_RECOGNITION')
        self.assertIn('UNPARSED_SUFFIX',r['diagnostics'])
        self.assertIsNone(r['proposal']);self.assertIsNone(r['native_conditional_reasoning'])
        with self.assertRaises(api.CandidateInterpretationError):self.consumer.assess(request(reasoning=hypothesis()))

    def test_actual_mixed_population_coverage_does_not_overstate_support(self):
        self.rows['EQA']['cards'][1]['text']='{T}: Add {C} if a hypothetical condition holds.'
        self.build()
        coverage=self.consumer.assess_many([request(),request('copper-unit','copper-edition'),request('foreign')]).to_dict()
        self.assertEqual(coverage['evaluated_requests'],3)
        self.assertEqual(coverage['counts'],dict(PARTIAL_RECOGNITION=1,REFUSED=1,SUPPORTED_COMPLETE=1))
        self.assertEqual(coverage['overlapping_diagnostics']['CONDITIONAL_OR_CHOICE_OUTPUT'],1)
        self.assertEqual(coverage['coverage_scope'],'ONLY_EXPLICIT_EVALUATED_REQUESTS_NOT_ORACLE_CORPUS')

    def test_missing_external_context_stays_unknown(self):
        self.build()
        assumptions=dict(interpretation_premise=api.HYPOTHESIS,characteristics={},state={})
        r=self.consumer.assess(request(reasoning=assumptions)).to_dict()
        self.assertEqual(r['native_conditional_reasoning']['decision'],'NEEDS_FACTS')
        self.assertEqual(r['native_conditional_reasoning']['input']['characteristics']['self_replacement'],'UNKNOWN')
        self.assertEqual(r['native_conditional_reasoning']['input']['characteristics']['chosen_targets'],'UNKNOWN')
        for gap in ('source_control','source_zone','source_tapped_status','resource_availability','actual_mana_produced'):
            self.assertIn(gap,r['unresolved_characteristics'])
        self.assertEqual(r['authority']['legal_activation'],'NOT_ESTABLISHED')

    def test_same_ability_and_native_self_replacement_restrictions(self):
        self.build();h=hypothesis();h['state']['same_ability_unresolved']='YES'
        r=self.consumer.assess(request(reasoning=h)).to_dict()
        self.assertEqual(r['native_conditional_reasoning']['decision'],'SAME_ABILITY_REACTIVATION_PROHIBITED')
        h['characteristics']['self_replacement']='PRESENT'
        with self.assertRaises(api.CandidateInterpretationError):self.consumer.assess(request(reasoning=h))

    def test_cannot_override_written_traits_or_claim_acceptance(self):
        self.build()
        for extra in (dict(potential_mana='NO'),dict(target_requirement='PRESENT'),dict(semantic_authority='ACCEPTED')):
            h=hypothesis();h['characteristics'].update(extra)
            with self.assertRaises(api.CandidateInterpretationError):self.consumer.assess(request(reasoning=h))
        h=hypothesis();h['interpretation_premise']='ACCEPTED_SEMANTICS'
        with self.assertRaises(api.CandidateInterpretationError):self.consumer.assess(request(reasoning=h))
        r=request();r['text']='{T}: Add {G}.'
        with self.assertRaises(api.CandidateInterpretationError):self.consumer.assess(r)

    def test_pending_proposal_cannot_substitute_for_native_executable_semantics(self):
        from gameplay_rules.models import CardGameplaySemantics
        from gameplay_rules.errors import GameplayContractError
        self.build();r=self.consumer.assess(request()).to_dict()
        with self.assertRaises(GameplayContractError):CardGameplaySemantics.create(r['proposal'])
        # Historical accepted interpretations retain their exact original gate.
        from card_rules_pilot.land_decision import _verify_original
        with self.assertRaises(c.PilotError):_verify_original(r)

    def test_contradictory_chosen_target_assumption_is_native_refusal(self):
        self.build();h=hypothesis();h['characteristics']['chosen_targets']=1
        with self.assertRaises(api.CandidateInterpretationError):self.consumer.assess(request(reasoning=h))

    def test_incorrect_card_printing_occurrence_and_snapshot_refuse(self):
        self.build()
        for r in (request('not-a-card'),request('cloth-unit','copper-edition'),
                  request()|dict(evidence_id='sha256:'+'0'*64)):
            with self.assertRaises(api.CandidateInterpretationError):self.consumer.assess(r)
        current=self.consumer.assess(request()).to_dict()
        selected=request()|dict(evidence_id=current['evidence']['selected_occurrence']['evidence_id'])
        self.assertEqual(self.consumer.assess(selected).to_dict()['status'],'SUPPORTED_COMPLETE')
        self.consumer._controls['expected_query_snapshot_id']='sha256:'+'0'*64
        with self.assertRaises(api.CandidateInterpretationError):self.consumer.assess(request())

    def test_conflicting_occurrences_are_withheld_without_choosing_winner(self):
        self.rows['EQB']['cards'][0]['text']='{T}: Add {R}.'
        self.build();r=self.consumer.assess(request()).to_dict()
        self.assertEqual(r['status'],'WITHHELD');self.assertIsNone(r['proposal'])
        self.assertIn('CONFLICTING_CARD_ASSERTIONS',r['diagnostics'])
        with self.assertRaises(api.CandidateInterpretationError):self.consumer.assess(request(reasoning=hypothesis()))

    def test_missing_text_and_unresolved_face_are_not_interpreted(self):
        self.rows['EQA']['cards'][0]['text']=None
        self.build();r=self.consumer.assess(request()).to_dict()
        self.assertIn(r['status'],('WITHHELD','EVIDENCE_UNRESOLVED'));self.assertIsNone(r['proposal'])

    def test_face_and_exceptional_evidence_cannot_borrow_text(self):
        self.rows['EQA']['cards'][0].update(layout='transform',side='a',faceName='Original Face',otherFaceIds=['cloth-alternative'])
        self.rows['EQB']['cards'][0].update(layout='transform',side='b',faceName='Original Reverse',otherFaceIds=['cloth-edition'])
        self.build();r=self.consumer.assess(request()).to_dict()
        self.assertIsNone(r['proposal']);self.assertIn(r['status'],('WITHHELD','EVIDENCE_UNRESOLVED'))

    def test_authorization_and_integrity_fail_closed(self):
        self.build();self.consumer.assess(request())
        self.consumer._controls['profile']=replace(self.h.profile,notice_sha256='0'*64)
        with self.assertRaises(api.CandidateInterpretationError):self.consumer.assess(request())
        self.consumer._controls['profile']=self.h.profile
        p=self.h.workspace/'output/oracle-evidence.jsonl';p.write_bytes(p.read_bytes()+b' ')
        with self.assertRaises(api.CandidateInterpretationError):self.consumer.assess(request())

    def test_factual_only_profile_cannot_supply_oracle_proposals(self):
        self.build(factual=True)
        with self.assertRaises(api.CandidateInterpretationError):self.consumer.assess(request())

    def test_report_and_coverage_determinism_and_recomputation(self):
        self.build();r=self.consumer.assess(request(reasoning=hypothesis()))
        self.assertEqual(r.to_json(),self.consumer.assess(request(reasoning=hypothesis())).to_json())
        self.assertEqual(r.to_json(),self.consumer.replay(r.to_json().encode(),expected_report_id=r.to_dict()['report_id']).to_json())
        requests=[request(),request('copper-unit','copper-edition'),request('not-a-card')]
        coverage=self.consumer.assess_many(requests)
        self.assertEqual(coverage.to_dict()['counts'],dict(REFUSED=1,SUPPORTED_COMPLETE=2))
        self.assertEqual(coverage.to_json(),self.consumer.replay_coverage(coverage.to_json().encode(),
            expected_report_id=coverage.to_dict()['report_id']).to_json())
        with self.assertRaises(api.CandidateInterpretationError):self.consumer.assess_many([request()]*2)
        with self.assertRaises(api.CandidateInterpretationError):self.consumer.assess_many([request()]*17)

    def test_coherently_rehashed_report_substitutions_do_not_replay(self):
        self.build();r=self.consumer.assess(request(reasoning=hypothesis())).to_dict()
        def span(x):x['proposal']['spans']['cost']['end']=1
        def quantity(x):x['proposal']['written_characteristics']['effect']['symbols'][0]['quantity']=9
        def premise(x):x['request']['reasoning']['state']['same_ability_unresolved']='YES'
        def native(x):x['native_conditional_reasoning']['decision']='LEGAL_ACTIVATION'
        def authority(x):x['authority']['semantic_authority']='ACCEPTED'
        def identity(x):x['evidence']['selected_occurrence']['printing_id']='foreign'
        for change in (span,quantity,premise,native,authority,identity):
            altered=deepcopy(r);change(altered);altered=c.seal(api.VERSION,altered,'report_id')
            # Even accepting the substitute's checksum cannot replace recomputation.
            with self.assertRaises(api.CandidateInterpretationError):
                self.consumer.replay(c.canonical(altered),expected_report_id=altered['report_id'])
        with self.assertRaises(api.CandidateInterpretationError):self.consumer.replay(c.canonical(r),expected_report_id='sha256:'+'0'*64)

    def test_changed_source_bindings_and_implementation_refuse(self):
        self.build();r=self.consumer.assess(request())
        original=self.report['report_id'];self.consumer._controls['expected_report_id']='sha256:'+'0'*64
        with self.assertRaises(api.CandidateInterpretationError):
            self.consumer.replay(r.to_json().encode(),expected_report_id=r.to_dict()['report_id'])
        self.consumer._controls['expected_report_id']=original
        with patch.object(api,'_code_identity',return_value='sha256:'+'0'*64):
            with self.assertRaises(api.CandidateInterpretationError):self.consumer.assess(request())

    def test_modified_face_text_and_source_version_report_bindings_refuse(self):
        self.build();r=self.consumer.assess(request()).to_dict()
        for change in ('face','version','text_hash'):
            altered=deepcopy(r);e=altered['evidence']['selected_occurrence']
            if change=='face':e['text']['face_boundary']['kind']='EXPLICIT_FACE'
            if change=='version':e['source_release']['version']='foreign'
            if change=='text_hash':e['text']['sha256']='0'*64
            altered=c.seal(api.VERSION,altered,'report_id')
            with self.assertRaises(api.CandidateInterpretationError):
                self.consumer.replay(c.canonical(altered),expected_report_id=altered['report_id'])

    def test_duplicate_request_keys_and_report_output_budget_refuse(self):
        self.build();r=self.consumer.assess(request())
        with self.assertRaises(api.CandidateInterpretationError):
            self.consumer.replay(b'{"request":null,"request":null}\n',expected_report_id=r.to_dict()['report_id'])
        with patch.object(api,'REPORT_BYTES',100):
            with self.assertRaises(api.CandidateInterpretationError):self.consumer.assess(request())

    def test_missing_rules_or_incompatible_version_refuse(self):
        self.build()
        with tempfile.TemporaryDirectory() as tmp:
            object.__setattr__(self.consumer,'_review_root',Path(tmp))
            with self.assertRaises(api.CandidateInterpretationError):self.consumer.assess(request())


if __name__=='__main__':unittest.main()
