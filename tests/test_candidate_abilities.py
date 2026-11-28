"""Original synthetic vertical through native import, inspection and reasoning."""
from copy import deepcopy
from dataclasses import replace
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from card_intelligence import candidate_abilities as api
from card_intelligence import candidate_mana as v1
from card_intelligence.mechanics import MechanicalCardIntelligence
from card_intelligence.rules_reasoning import load_rules_reasoner, CONTEXT_ID
from card_rules_pilot import contract as c
import test_mtgjson_evidence_handoff as handoff
import test_candidate_mana as predecessor

ROOT = Path(__file__).parents[1]
P = '{T}: Add {G}.'
Q = '{T}: Add {C}{C}.'


def request(card='cloth-unit', printing='cloth-edition', reasoning=None):
    return dict(card_id=card, printing_id=printing, evidence_id=None, reasoning=reasoning)


def hypothesis(report, index=0):
    sid = report['segments'][index]['segment_id']
    scope = None
    if report['dependencies']['scope_hypothesis_required']:
        scope = dict(field_id=report['field']['field_id'], segment_id=sid,
            dependency_id=report['dependencies']['dependency_id'], assumption=api.SCOPE_HYPOTHESIS)
    return dict(segment_id=sid, interpretation_premise=v1.HYPOTHESIS,
        characteristics=dict(chosen_targets=0, self_replacement='ABSENT'),
        state=dict(mana_payment_request='SPELL_CASTING_MANA_PAYMENT', priority='NO',
            same_ability_unresolved='NO', current_mana_output='ZERO'), scope_assumption=scope)


class CandidateAbilityTests(unittest.TestCase):
    def setUp(self):
        self.h = handoff.EvidenceHandoffTests('runTest')
        self.h.setUp(); self.addCleanup(self.h.doCleanups)

    def build(self, text=P+'\n'+Q, **options):
        for part in self.h.document['data'].values():
            for row in part['cards']:
                row['text'] = text if row['identifiers']['scryfallOracleId']=='cloth-unit' else Q
        self.h.prepare(**options)
        self.imported = self.h.run_import()
        self.fixture = handoff.build_intelligence_fixture(self.h.root/'catalog-fixture')
        self.query = handoff.CanonicalQueryEngine.from_attachment(handoff.attach_fixture(self.fixture))
        self.consumer = api.load_candidate_ability_interpreter(self.query,
            expected_query_snapshot_id=self.query.snapshot().snapshot_id,
            evidence_directory=self.h.workspace/'output', profile=self.h.profile,
            expected_report_id=self.imported['report_id'], review_root=ROOT/'reference-reviews')
        return self.consumer

    def assert_accounted(self, report, text):
        raw = text.encode(); regions = report['regions']; offset=0
        for region in regions:
            self.assertEqual(region['span']['start'],offset)
            offset=region['span']['end']
            self.assertEqual(raw[region['span']['start']:offset],region['value'].encode())
        self.assertEqual(offset,len(raw))
        self.assertEqual(''.join(r['value'] for r in regions),text)
        self.assertEqual(report['coverage']['byte_accounting']['accounted_bytes'],len(raw))
        self.assertEqual(report['coverage']['byte_accounting']['reconstructed_sha256'],hashlib.sha256(raw).hexdigest())
        self.assertEqual(report['field']['value'],text)

    def test_actual_multi_ability_vertical_and_native_conditional_result(self):
        self.build(); before={p:p.read_bytes() for p in self.fixture['catalog'].rglob('*') if p.is_file()}
        with patch.object(MechanicalCardIntelligence,'_load_source',side_effect=AssertionError('blocked historical reader')):
            report=self.consumer.assess(request()).to_dict()
            answered=self.consumer.assess(request(reasoning=hypothesis(report,1))).to_dict()
        self.assertEqual(len(report['segments']),2)
        self.assertEqual([s['ordinal'] for s in report['segments']],[0,1])
        self.assertNotEqual(*[s['segment_id'] for s in report['segments']])
        for segment in report['segments']:
            self.assertEqual(segment['proposal']['review']['status'],'requires_review')
            self.assertEqual(segment['review_criteria']['native_result']['method_status'],'INCOMPLETE')
        native=answered['native_conditional_reasoning']
        self.assertEqual(native['input']['scenario_id'],report['segments'][1]['segment_id'])
        self.assertEqual(native['decision'],'PAYMENT_TIMING_EXCEPTION_APPLIES')
        self.assertEqual(native,load_rules_reasoner(review_root=ROOT/'reference-reviews',
            expected_context_id=CONTEXT_ID).assess(native['input']).to_dict())
        self.assertEqual(native['input']['state']['current_mana_output'],'ZERO')
        self.assertEqual(before,{p:p.read_bytes() for p in self.fixture['catalog'].rglob('*') if p.is_file()})
        for r in (report,answered):
            self.assertEqual(r['authority']['actual_mana_output'],'UNKNOWN')
            self.assertEqual(r['authority']['legal_activation'],'NOT_ESTABLISHED')
            self.assertFalse(r['authority']['canonical_admission'])
            self.assertFalse(r['authority']['admitted_dossier_populated'])
            self.assertEqual(r['authority']['execution_authority'],'BLOCKED')
            self.assertFalse(r['authority']['game_actions_performed'])

    def test_one_ability_has_whole_field_scope_without_sibling_hypothesis(self):
        self.build(P); r=self.consumer.assess(request()).to_dict()
        self.assertEqual(r['coverage']['total_ability_count'],1)
        self.assertFalse(r['dependencies']['scope_hypothesis_required'])
        self.assertEqual(self.consumer.assess(request(reasoning=hypothesis(r))).to_dict()[
            'native_conditional_reasoning']['decision'],'PAYMENT_TIMING_EXCEPTION_APPLIES')
        self.assert_accounted(r,P)

    def test_multiple_repeated_and_mixed_symbols_distinct_local_subjects(self):
        text=P+'\n'+P+'\n{T}: Add {W}{U}{B}{R}{G}{C}.'
        self.build(text);r=self.consumer.assess(request()).to_dict()
        self.assertEqual(len(r['segments']),3)
        self.assertEqual(len({s['segment_id'] for s in r['segments']}),3)
        self.assertEqual([x['symbol'] for x in r['segments'][2]['proposal']['written_characteristics']['effect']['symbols']],list('WUBRGC'))
        self.assert_accounted(r,text)

    def test_exact_original_spans_and_full_field_vs_selected_evidence(self):
        text='{T}  :   Add {G}.\n'+Q
        self.build(text);r=self.consumer.assess(request()).to_dict();s=r['segments'][1]
        first_end=len(text.split('\n')[0].encode())
        self.assertEqual(s['proposal']['spans']['cost']['start'],first_end+1)
        for name,relative in s['transformation']['relative_spans'].items():
            span=s['proposal']['spans'][name]
            self.assertEqual(span['start'],relative['start']+first_end+1)
            self.assertEqual(text.encode()[span['start']:span['end']],Q.encode()[relative['start']:relative['end']])
        refs=s['review_criteria']['evidence_refs']
        self.assertNotEqual(refs['selected_passage'],refs['full_oracle_field'])
        self.assertEqual(refs['full_oracle_field']['span']['end'],len(text.encode()))
        self.assertEqual(r['evidence']['selected_occurrence']['text']['source_pointer'],'/data/EQA/cards/0/text')
        self.assertEqual(r['evidence']['source_use_profile_id'],self.h.profile.receipt()['profile_id'])
        self.assertEqual(r['field']['sha256'],hashlib.sha256(text.encode()).hexdigest())
        self.assert_accounted(r,text)

    def test_supported_prefix_and_utf8_opaque_remainder_never_resume(self):
        tail='{T}: Observe αβ.\n'+Q
        text=P+'\n'+tail
        self.build(text);r=self.consumer.assess(request()).to_dict()
        self.assertEqual(r['status'],'PARTIAL_SEGMENTATION')
        self.assertEqual(len(r['segments']),1)
        self.assertEqual(r['regions'][-1]['value'],tail)
        self.assertEqual(r['regions'][-1]['kind'],'UNRESOLVED')
        self.assertIsNone(r['coverage']['total_ability_count'])
        self.assertEqual(r['coverage']['unresolved_bytes'],len(tail.encode()))
        self.assertEqual(r['coverage']['card_mechanical_completeness'],'NOT_ESTABLISHED')
        self.assertEqual(r['dependencies']['surrounding_effects'],'UNKNOWN')
        self.assert_accounted(r,text)
        h=hypothesis(r); h['segment_id']='sha256:'+'f'*64
        with self.assertRaises(api.CandidateSegmentationError):self.consumer.assess(request(reasoning=h))

    def test_uncertain_fields_account_all_bytes_without_a_proposal(self):
        examples=json.loads((ROOT/'tests/fixtures/candidate_abilities_v1/passages.json').read_bytes())
        for text in examples['unresolved']:
            with self.subTest(text=text):
                r=api._materialize(text,{'original_fixture_only':True},'synthetic-internal-no-authority')
                self.assertEqual(r['segments'],[])
                self.assertIsNone(r['coverage']['total_ability_count'])
                self.assert_accounted(r,text)

    def test_only_existing_grammar_and_supported_lf_boundaries(self):
        fixtures=json.loads((ROOT/'tests/fixtures/candidate_abilities_v1/passages.json').read_bytes())
        for text in fixtures['supported']:
            with self.subTest(text=text):
                r=api._materialize(text,{'original_fixture_only':True},'synthetic-internal-no-authority')
                self.assertEqual(r['status'],'SUPPORTED_SEGMENTATION');self.assert_accounted(r,text)
                for s in r['segments']:
                    span=s['proposal']['spans']['whole_passage'];literal=text.encode()[span['start']:span['end']].decode()
                    self.assertEqual(s['proposal']['proposed_rules_characteristics'],v1._recognize(literal)['proposal']['proposed_rules_characteristics'])

    def test_native_uncertain_boundary_cannot_be_bypassed_with_hypothesis(self):
        self.build(P+'\nActivate only during your turn.')
        r=self.consumer.assess(request()).to_dict();self.assertEqual(r['segments'],[])
        h=dict(segment_id='sha256:'+'a'*64,interpretation_premise=v1.HYPOTHESIS,
            characteristics={},state={},scope_assumption=dict(field_id='fake',segment_id='fake',
                dependency_id='fake',assumption=api.SCOPE_HYPOTHESIS))
        with self.assertRaises(api.CandidateSegmentationError):self.consumer.assess(request(reasoning=h))

    def test_surrounding_scope_required_exact_and_still_hypothetical(self):
        self.build(P+'\n{T}: Draw a card.');r=self.consumer.assess(request()).to_dict();h=hypothesis(r)
        for key in ('field_id','segment_id','dependency_id','assumption'):
            bad=deepcopy(h);bad['scope_assumption'][key]='substitute'
            with self.subTest(key=key),self.assertRaises(api.CandidateSegmentationError):
                self.consumer.assess(request(reasoning=bad))
        bad=deepcopy(h);bad['scope_assumption']=None
        with self.assertRaises(api.CandidateSegmentationError):self.consumer.assess(request(reasoning=bad))
        good=self.consumer.assess(request(reasoning=h)).to_dict()
        self.assertEqual(good['dependencies']['surrounding_effects'],'UNKNOWN')
        self.assertEqual(good['authority']['semantic_authority'],'NOT_ESTABLISHED')

    def test_native_unknowns_and_same_ability_restriction_preserved(self):
        self.build();r=self.consumer.assess(request()).to_dict();h=hypothesis(r)
        h['state']['same_ability_unresolved']='YES'
        self.assertEqual(self.consumer.assess(request(reasoning=h)).to_dict()['native_conditional_reasoning']['decision'],
                         'SAME_ABILITY_REACTIVATION_PROHIBITED')
        h['state']={};h['characteristics']={}
        result=self.consumer.assess(request(reasoning=h)).to_dict()
        self.assertEqual(result['native_conditional_reasoning']['decision'],'NEEDS_FACTS')
        self.assertEqual(result['authority']['actual_mana_output'],'UNKNOWN')

    def test_sibling_characteristics_and_serialized_authority_refused(self):
        self.build();r=self.consumer.assess(request()).to_dict()
        for extra in ({'ability_kind':'TRIGGERED'},{'potential_mana':'NO'},{'source_segment_id':r['segments'][1]['segment_id']},
                      {'review_status':'accepted'}):
            h=hypothesis(r);h['characteristics'].update(extra)
            with self.assertRaises(api.CandidateSegmentationError):self.consumer.assess(request(reasoning=h))
        for extra in ({'text':P},{'inspection':r['evidence']},{'approved':True}):
            with self.assertRaises(api.CandidateSegmentationError):self.consumer.assess(request()|extra)

    def test_native_contradictory_and_unsupported_rules_premises_refuse(self):
        self.build();r=self.consumer.assess(request()).to_dict();h=hypothesis(r)
        h['characteristics']['chosen_targets']=1
        with self.assertRaises(api.CandidateSegmentationError):self.consumer.assess(request(reasoning=h))
        h=hypothesis(r);h['characteristics']['self_replacement']='PRESENT'
        with self.assertRaises(api.CandidateSegmentationError):self.consumer.assess(request(reasoning=h))

    def test_wrong_identities_occurrence_and_snapshot_refuse(self):
        self.build()
        for raw in (request('unknown'),request('cloth-unit','copper-edition'),request()|dict(evidence_id='sha256:'+'0'*64)):
            with self.assertRaises(api.CandidateSegmentationError):self.consumer.assess(raw)
        r=self.consumer.assess(request()).to_dict()
        selected=request()|dict(evidence_id=r['evidence']['selected_occurrence']['evidence_id'])
        self.assertEqual(len(self.consumer.assess(selected).to_dict()['segments']),2)
        self.consumer._controls['expected_query_snapshot_id']='sha256:'+'0'*64
        with self.assertRaises(api.CandidateSegmentationError):self.consumer.assess(request())

    def test_conflicting_evidence_is_withheld_instead_of_segmented(self):
        self.h.document['data']['EQB']['cards'][0]['colors']=['R']
        self.build();r=self.consumer.assess(request()).to_dict()
        self.assertEqual(r['status'],'WITHHELD');self.assertEqual(r['segments'],[])
        self.assertIn('CONFLICTING_CARD_ASSERTIONS',r['diagnostics'])
        self.assertEqual(r['coverage']['byte_accounting']['status'],'NOT_AVAILABLE')

    def test_face_ownership_and_missing_text_are_not_borrowed(self):
        self.h.document['data']['EQA']['cards'][0].update(layout='transform',side='a',faceName='Original Face',otherFaceIds=['cloth-alternative'])
        self.h.document['data']['EQB']['cards'][0].update(layout='transform',side='b',faceName='Original Reverse',otherFaceIds=['cloth-edition'])
        self.build();r=self.consumer.assess(request()).to_dict()
        self.assertEqual(r['segments'],[]);self.assertIn(r['status'],('WITHHELD','EVIDENCE_UNRESOLVED'))

    def test_ambiguous_native_evidence_branch_never_produces_proposals(self):
        self.build();inspected=MechanicalCardIntelligence.inspect_mtgjson_candidate(self.query,
            **self.consumer._controls,card_id='cloth-unit',printing_id='cloth-edition')
        # Negative branch only; no mocked positive evidence-to-reasoning vertical.
        inspected['evidence']['occurrences']*=2
        with patch.object(MechanicalCardIntelligence,'inspect_mtgjson_candidate',return_value=inspected) as reader:
            r=self.consumer.assess(request()).to_dict()
        reader.assert_called_once();self.assertEqual(r['status'],'AMBIGUOUS');self.assertEqual(r['segments'],[])

    def test_source_profile_and_artifact_tampering_fail_closed(self):
        self.build();self.consumer._controls['profile']=replace(self.h.profile,notice_sha256='0'*64)
        with self.assertRaises(api.CandidateSegmentationError):self.consumer.assess(request())
        self.consumer._controls['profile']=self.h.profile
        p=self.h.workspace/'output/oracle-evidence.jsonl';p.write_bytes(p.read_bytes()+b' ')
        with self.assertRaises(api.CandidateSegmentationError):self.consumer.assess(request())

    def test_factual_profile_cannot_substitute_for_oracle_authorization(self):
        self.build(factual=True)
        with self.assertRaises(api.CandidateSegmentationError):self.consumer.assess(request())

    def test_native_empty_and_truncated_text_preserve_original_field(self):
        self.build('{T}: Add {G}')
        r=self.consumer.assess(request()).to_dict()
        self.assertEqual(r['segments'],[]);self.assert_accounted(r,'{T}: Add {G}')

    def test_empty_supplied_field_is_not_known_absent(self):
        self.build('');r=self.consumer.assess(request()).to_dict()
        self.assertEqual(r['status'],'UNRESOLVED');self.assertEqual(r['segments'],[])
        self.assertIsNone(r['coverage']['total_ability_count']);self.assert_accounted(r,'')

    def test_null_provider_text_cannot_supply_an_ability(self):
        self.build(None);r=self.consumer.assess(request()).to_dict()
        self.assertIn(r['status'],('WITHHELD','EVIDENCE_UNRESOLVED'))
        self.assertEqual(r['segments'],[]);self.assertIsNone(r['field'])

    def test_oversized_verified_field_refuses_without_prefix_truncation(self):
        self.build(P+'x'*8192)
        with self.assertRaises(api.CandidateSegmentationError):self.consumer.assess(request())

    def test_deterministic_report_coverage_and_fresh_recomputation(self):
        self.build();r=self.consumer.assess(request()).to_dict()
        doc=self.consumer.assess(request(reasoning=hypothesis(r)))
        self.assertEqual(doc.to_json(),self.consumer.assess(request(reasoning=hypothesis(r))).to_json())
        with patch.object(MechanicalCardIntelligence,'inspect_mtgjson_candidate',wraps=MechanicalCardIntelligence.inspect_mtgjson_candidate) as fresh:
            self.assertEqual(doc.to_json(),self.consumer.replay(doc.to_json().encode(),expected_report_id=doc.to_dict()['report_id']).to_json())
        fresh.assert_called_once()
        coverage=self.consumer.assess_many([request(),request('copper-unit','copper-edition'),request('unknown')])
        self.assertEqual(coverage.to_dict()['counts'],dict(SUPPORTED_SEGMENTATION=2,REFUSED=1))
        self.assertEqual(coverage.to_json(),self.consumer.replay_coverage(coverage.to_json().encode(),expected_report_id=coverage.to_dict()['report_id']).to_json())

    def test_coherently_rehashed_boundaries_separators_proposals_and_results_refuse(self):
        self.build();r=self.consumer.assess(request()).to_dict()
        r=self.consumer.assess(request(reasoning=hypothesis(r))).to_dict()
        def boundary(x):x['segments'][0]['boundary']['status']='ACCEPTED'
        def separator(x):x['regions'][1]['value']=' '
        def span(x):x['segments'][1]['proposal']['spans']['cost']['start']=0
        def quantity(x):x['segments'][0]['proposal']['written_characteristics']['effect']['symbols'][0]['quantity']=8
        def source(x):x['evidence']['selected_occurrence']['evidence_id']='sha256:'+'0'*64
        def face(x):x['evidence']['selected_occurrence']['text']['face_boundary']['kind']='EXPLICIT_FACE'
        def version(x):x['evidence']['selected_occurrence']['source_release']['version']='wrong'
        def assumed(x):x['request']['reasoning']['scope_assumption']['dependency_id']='wrong'
        def native(x):x['native_conditional_reasoning']['decision']='LEGAL_ACTIVATION'
        def count(x):x['coverage']['total_ability_count']=8
        def field(x):x['field']['value']='substituted'
        def authority(x):x['authority']['semantic_authority']='ACCEPTED'
        for alter in (boundary,separator,span,quantity,source,face,version,assumed,native,count,field,authority):
            with self.subTest(alter=alter.__name__):
                changed=deepcopy(r);alter(changed);changed=c.seal(api.VERSION,changed,'report_id')
                with self.assertRaises(api.CandidateSegmentationError):
                    self.consumer.replay(c.canonical(changed),expected_report_id=changed['report_id'])
        with self.assertRaises(api.CandidateSegmentationError):self.consumer.replay(c.canonical(r),expected_report_id='sha256:'+'0'*64)

    def test_changed_live_source_bindings_and_code_refuse_replay(self):
        self.build();r=self.consumer.assess(request())
        self.consumer._controls['expected_report_id']='sha256:'+'0'*64
        with self.assertRaises(api.CandidateSegmentationError):self.consumer.replay(r.to_json().encode(),expected_report_id=r.to_dict()['report_id'])
        with patch.object(api,'_implementation',return_value='changed'):
            with self.assertRaises(api.CandidateSegmentationError):self.consumer.assess(request())

    def test_coverage_rehash_and_duplicate_json_keys_refuse(self):
        self.build();doc=self.consumer.assess_many([request()]);r=doc.to_dict()
        r['reports'][0]['coverage']['total_ability_count']=99
        r=c.seal('candidate-ability-coverage-v1',r,'report_id')
        with self.assertRaises(api.CandidateSegmentationError):
            self.consumer.replay_coverage(c.canonical(r),expected_report_id=r['report_id'])
        with self.assertRaises(api.CandidateSegmentationError):
            self.consumer.replay(b'{"request":null,"request":null}\n',expected_report_id='sha256:'+'0'*64)

    def test_closed_request_population_and_report_limits(self):
        self.build()
        for bad in (request()|dict(extra=True),request()|dict(card_id=[]),request()|dict(reasoning={'approved':True}),None):
            with self.assertRaises(api.CandidateSegmentationError):self.consumer.assess(bad)
        for rows in ([],[request()]*2,[request()]*17):
            with self.assertRaises(api.CandidateSegmentationError):self.consumer.assess_many(rows)
        with patch.object(api,'REPORT_BYTES',100):
            with self.assertRaises(api.CandidateSegmentationError):self.consumer.assess(request())
        with self.assertRaises(api.CandidateSegmentationError):api._partition('\n'.join([P]*17))
        material=api._materialize('\n'.join([P]*16),{'original_fixture_only':True},'no-authority')
        self.assertEqual(len(material['segments']),16)
        with self.assertRaises(api.CandidateSegmentationError):api._partition('é'*8192)
        with self.assertRaises(api.CandidateSegmentationError):api._partition('\ud800')

    def test_proposals_cannot_become_executable_or_accepted_semantics(self):
        from gameplay_rules.models import CardGameplaySemantics
        from gameplay_rules.errors import GameplayContractError
        from card_rules_pilot.land_decision import _verify_original
        self.build();r=self.consumer.assess(request()).to_dict()
        for segment in r['segments']:
            with self.assertRaises(GameplayContractError):CardGameplaySemantics.create(segment['proposal'])
        with self.assertRaises(c.PilotError):_verify_original(r)
        intelligence=MechanicalCardIntelligence.from_attachment(handoff.attach_fixture(self.fixture),
            data_root=self.fixture['mechanical_data'],expected_query_snapshot_id=self.query.snapshot().snapshot_id,
            source_directory=self.fixture['source_directory'])
        before=intelligence.dossier('cloth-unit').to_json();self.consumer.assess(request())
        self.assertEqual(before,intelligence.dossier('cloth-unit').to_json())

    def test_predecessor_golden_report_and_native_replay_are_unchanged(self):
        old=predecessor.CandidateManaTests('runTest');old.setUp();self.addCleanup(old.doCleanups)
        consumer=old.build()
        r=consumer.assess(predecessor.request())
        self.assertEqual(r.to_dict()['report_id'],'sha256:969e53da9c3b4f55ad6c2639a42cb00d42812d93d93ab550fc44c0bcb4cb01c0')
        answered=consumer.assess(predecessor.request(reasoning=predecessor.hypothesis()))
        self.assertEqual(answered.to_dict()['report_id'],'sha256:66056c920928acd6a501e9394e441625e5ab0984be1983f9fe247137e8da6272')
        self.assertEqual(answered.to_json(),consumer.replay(answered.to_json().encode(),expected_report_id=answered.to_dict()['report_id']).to_json())


if __name__=='__main__':unittest.main()
