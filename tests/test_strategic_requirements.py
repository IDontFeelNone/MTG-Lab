"""Actual admitted requirements behavior and explicit authority/gap boundaries."""
from copy import deepcopy
from dataclasses import FrozenInstanceError
import contextlib
import hashlib
import io
import json
from pathlib import Path
import shutil
import tempfile
import time
import unittest
from unittest.mock import patch

from card_rules_pilot import contract as c, land_decision as decision, mana_scenario_policy as hp
from card_intelligence import strategic_context as inputs, strategic_requirements_policy as policy
from card_intelligence import strategic_requirements as api
from land_test_support import ROOT, current_catalog_intact
from test_land_decision import decision_arguments


def context(declarations=None, assumptions=None, leads=None):
    return inputs.make_context(declarations,hypothetical=hp.make_scenario(assumptions or []).to_dict(),leads=leads).to_dict()


def flat(report):return [r for rows in report['requirements'].values() for r in rows]
def by_template(report):return {r['template_id']:r for r in flat(report)}


class StrategicContextContractTests(unittest.TestCase):
    def test_strict_input_types_fields_canonical_and_duplicate_keys(self):
        original=context();self.assertEqual(inputs.parse_context(c.canonical(original)).to_dict(),original)
        for value in ({},True,dict(original,verified_format=True),dict(original,authority='OBSERVED_GAME_STATE')):
            with self.assertRaises(ValueError):inputs.validate_context(value)
        for raw in (b'{"a":1,"a":1}\n',b'{}',b'{"number":NaN}\n',b' '*8193):
            with self.assertRaises(ValueError):inputs.parse_context(raw)
        for dim,value in (('format_label',True),('format_label',''),('format_label','a\nb'),('deck_objective','combo-archetype'),('deck_color_requirements',['B','W']),('deck_color_requirements',['W','W']),('deck_color_requirements',['C']),('observed_swamps',5),('format_legality',True),('role','mana-rock')):
            with self.assertRaises(ValueError):context([dict(dimension=dim,value=value)])

    def test_closed_alternative_identities_and_reference_leads(self):
        valid=[dict(namespace=inputs.NAMESPACE,card_id=cid) for cid in inputs.CARD_IDS]
        self.assertEqual(context([dict(dimension='alternatives',value=valid)])['declarations'][0]['value'],valid)
        for invalid in ([dict(namespace=inputs.NAMESPACE,card_id='foreign')],[dict(namespace='printing',card_id=inputs.CARD_IDS[0])],valid[::-1],valid+valid[:1]):
            with self.assertRaises(ValueError):context([dict(dimension='alternatives',value=invalid)])
        for lead in (dict(category='verified',reference='x'),dict(category='deck-context',reference='x',authenticated=True),dict(category='deck-context',reference='x'*161)):
            with self.assertRaises(ValueError):context(leads=[lead])
        value=context(leads=[dict(category='format-legality',reference='sha256:'+'0'*64)])
        self.assertIn('NOT_OBSERVATIONS',value['authority'])

    def test_duplicate_conflicting_values_and_hypothetical_contract(self):
        row=dict(dimension='deck_objective',value=inputs.OBJECTIVES[0])
        with self.assertRaises(ValueError):context([row,row])
        value=context([row,dict(dimension='deck_objective',value=inputs.OBJECTIVES[1])]);self.assertEqual(len(value['declarations']),2)
        for count in (True,-1,1.0,'5',1000001):
            with self.assertRaises(ValueError):context(assumptions=[dict(dimension='controlled_swamp_count',value=count)])
        for colors in (['W','W'],['B','W'],['C'],None):
            with self.assertRaises(ValueError):context(assumptions=[dict(dimension='commander_color_identity',value=colors)])
        for value in (0,1,5,1000000):
            original=context(assumptions=[dict(dimension='controlled_swamp_count',value=value)])
            self.assertEqual(inputs.validate_context(original).to_dict(),original)

    def test_owned_input_contract_and_policy_documents(self):
        value=context([dict(dimension='deck_color_requirements',value=[])]);doc=inputs.validate_context(value)
        value['declarations'].clear();self.assertTrue(doc.to_dict()['declarations'])
        policy.policy_document().to_dict()['templates'].clear();self.assertTrue(policy.policy_document().to_dict()['templates'])
        policy.family_registry().clear();self.assertEqual(len(policy.family_registry()),4)
        inputs.contract_document().to_dict()['card_ids'].clear();self.assertEqual(len(inputs.contract_document().to_dict()['card_ids']),6)
        self.assertEqual(c.identity(inputs.CONTRACT_VERSION,inputs.contract_document().to_dict(),'contract_id'),inputs.CONTRACT_ID)


class ActualStrategicRequirementsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.intact=current_catalog_intact(unittest.TestCase())
        if cls.intact:
            start=time.perf_counter();cls.consumer=api.load_strategic_requirements(**decision_arguments());cls.load_seconds=time.perf_counter()-start

    def live(self):
        if self.intact:return True
        # Actual writer-expanded catalog rejection, not a historical positive
        # fixture or an extra skip. Every live test exercises this path nested.
        with self.assertRaises(api.RequirementsError) as caught:api.load_strategic_requirements(**decision_arguments())
        self.assertEqual(caught.exception.code,'EVIDENCE_ADMISSION_REJECTED')
        return False

    def report(self,family,supplied=None):return self.consumer.requirements(family,supplied).to_dict()

    def test_exact_four_families_all_six_cards_and_nine_subjects(self):
        if not self.live():return
        cards=set();subjects=set()
        self.assertEqual(set(self.consumer.question_families),{'mana-and-utility','variable-output','color-context','damage-ownership'})
        for family in self.consumer.question_families:
            report=self.report(family);self.assertEqual(report['request_state'],'ANSWERABLE_REQUIREMENTS_ONLY')
            self.assertEqual(report['answerability']['strategic_evaluation'],'UNSUPPORTED')
            self.assertEqual(by_template(report)['source-currency']['status']['satisfaction'],'UNRESOLVED')
            self.assertEqual(report['provenance']['decision_id'],decision.DECISION_ID)
            self.assertEqual(report['provenance']['accepted_collection_id'],decision.COLLECTION_ID)
            self.assertEqual({r['identity']['card_id'] for r in report['cards']},set(policy.family_registry()[family]['cards']))
            cards.update(r['identity']['card_id'] for r in report['cards']);subjects.update(r['subject_id'] for r in report['capabilities'])
            for cap in report['capabilities']:
                self.assertEqual(cap['historical_status'],'PENDING_NOT_ESTABLISHED');self.assertEqual(cap['current_status'],'ACCEPTED_BOUNDED_RETAINED_TEXT')
                self.assertEqual(dict(decision.CANDIDATE_IDS)[cap['subject_id']],cap['candidate_id'])
        self.assertEqual(cards,set(inputs.CARD_IDS));self.assertEqual(subjects,set(decision.SUBJECT_IDS))

    def test_missing_and_declared_objective_are_not_strategy(self):
        if not self.live():return
        missing=self.report('mana-and-utility');supplied=self.report('mana-and-utility',context([dict(dimension='deck_objective',value='interaction-utility')]))
        self.assertEqual(by_template(missing)['deck-objective']['status']['information'],'ABSENT')
        self.assertEqual(by_template(supplied)['deck-objective']['status']['information'],'DECLARED_UNVERIFIED')
        self.assertEqual(supplied['request_state'],'PARTIALLY_INFORMED')
        self.assertEqual(by_template(supplied)['alternative-use-cost']['status']['satisfaction'],'UNRESOLVED')
        self.assertEqual(by_template(supplied)['strategic-performance']['status']['validation'],'UNIMPLEMENTED_OR_UNAUTHORIZED')
        self.assertEqual(missing['capabilities'],supplied['capabilities'])

    def test_coffers_missing_zero_five_and_conflicting_counts(self):
        if not self.live():return
        missing=self.report('variable-output');self.assertEqual(by_template(missing)['hypothetical-swamps']['status']['information'],'ABSENT')
        for n in (0,1,5,23,1000000):
            value=self.report('variable-output',context(assumptions=[dict(dimension='controlled_swamp_count',value=n)]))
            cap=next(v for v in value['capabilities'] if v['output_pattern']=='swamp_count_dependent')
            self.assertEqual(cap['hypothetical']['conditional_written_output']['quantity'],n)
            self.assertEqual(cap['written_cost'],'{2}, {T}')
            self.assertEqual(by_template(value)['hypothetical-swamps']['status']['information'],'HYPOTHETICAL_SUPPLIED')
            self.assertEqual(by_template(value)['swamp-composition']['status']['satisfaction'],'UNRESOLVED')
        conflict=self.report('variable-output',context(assumptions=[dict(dimension='controlled_swamp_count',value=n) for n in (0,5)]))
        self.assertEqual(conflict['request_state'],'CONFLICTING')
        self.assertTrue(conflict['conflicting_requirements'])
        cap=next(v for v in conflict['capabilities'] if v['output_pattern']=='swamp_count_dependent');self.assertIsNone(cap['hypothetical']['conditional_written_output'])

    def test_commander_identity_and_deck_colors_remain_independent(self):
        if not self.live():return
        self.assertEqual(by_template(self.report('color-context'))['hypothetical-commander-colors']['status']['information'],'ABSENT')
        for colors in ([],['W'],['W','B'],list(hp.COLORS)):
            value=self.report('color-context',context([dict(dimension='deck_color_requirements',value=['R','G'])],assumptions=[dict(dimension='commander_color_identity',value=colors)]))
            self.assertEqual(value['request_state'],'PARTIALLY_INFORMED')
            cap=next(v for v in value['capabilities'] if v['output_pattern']=='commander_color_context_dependent')
            self.assertEqual(cap['hypothetical']['conditional_written_output']['colors'],colors)
            self.assertEqual(by_template(value)['commander-evidence']['status']['satisfaction'],'UNRESOLVED')
            self.assertEqual(by_template(value)['deck-colors']['status']['information'],'DECLARED_UNVERIFIED')
        conflict=self.report('color-context',context(assumptions=[dict(dimension='commander_color_identity',value=v) for v in (['W'],['B'])]))
        self.assertEqual(conflict['request_state'],'CONFLICTING')
        cap=next(v for v in conflict['capabilities'] if v['output_pattern']=='commander_color_context_dependent')
        self.assertIsNone(cap['hypothetical']['conditional_written_output'])


    def test_declared_format_and_all_fields_never_close_validation(self):
        if not self.live():return
        supplied=context([dict(dimension='format_label',value='owner-declared format'),dict(dimension='deck_objective',value='mana-flexibility'),dict(dimension='deck_color_requirements',value=['W','B']),dict(dimension='alternatives',value=[])],assumptions=[dict(dimension='commander_color_identity',value=['W','B'])],leads=[dict(category=k,reference='declared:'+k) for k in inputs.LEAD_CATEGORIES])
        value=self.report('color-context',supplied);rows=by_template(value)
        self.assertEqual(rows['format-label']['status']['information'],'DECLARED_UNVERIFIED')
        for template in ('format-legality','strategic-performance','evidence-authentication','commander-evidence','production-permission'):
            self.assertEqual(rows[template]['status']['satisfaction'],'UNRESOLVED')
            self.assertEqual(rows[template]['status']['validation'],'UNIMPLEMENTED_OR_UNAUTHORIZED')
        self.assertEqual(value['answerability']['strategic_evaluation'],'UNSUPPORTED')
        self.assertNotIn('confidence',value);self.assertNotIn('ready_for_recommendation',value)

    def test_declaration_conflicts_and_no_cross_question_context_leakage(self):
        if not self.live():return
        supplied=context([dict(dimension='format_label',value=v) for v in ('scope-one','scope-two')],assumptions=[dict(dimension='controlled_swamp_count',value=5)])
        value=self.report('variable-output',supplied);self.assertEqual(value['request_state'],'CONFLICTING')
        cap=next(v for v in value['capabilities'] if v['output_pattern']=='swamp_count_dependent')
        self.assertEqual(cap['hypothetical']['conditional_written_output']['quantity'],5)
        for family in ('mana-and-utility','damage-ownership','color-context'):
            with self.assertRaises(ValueError):self.report(family,context(assumptions=[dict(dimension='controlled_swamp_count',value=5)]))
        self.assertEqual(self.report('variable-output')['request_state'],'ANSWERABLE_REQUIREMENTS_ONLY')
        value=self.report('variable-output',context(assumptions=[dict(dimension='controlled_swamp_count',value=5)]))
        for cap in value['capabilities']:
            if cap['output_pattern']=='fixed_colorless':self.assertEqual(cap['hypothetical']['state'],'UNSPECIFIED')

    def test_cost_output_utility_and_damage_ownership_and_procedure(self):
        if not self.live():return
        utility=self.report('mana-and-utility');caps={v['subject_id']:v for v in utility['capabilities']}
        self.assertEqual(caps['port-utility']['written_cost'],'{1}, {T}');self.assertEqual(caps['port-mana']['written_cost'],'{T}')
        self.assertIsNone(caps['port-utility']['hypothetical']['conditional_written_output'])
        self.assertIn('target-relevance',by_template(utility));self.assertIn('alternative-use-cost',by_template(utility))
        damage=self.report('damage-ownership');caps={v['subject_id']:v for v in damage['capabilities']}
        self.assertEqual(caps['city-damage-trigger']['ownership']['state'],'separate_triggered_ability')
        self.assertIsNotNone(caps['citadel-color-choice']['ownership']['damage_clause'])
        self.assertIsNone(caps['citadel-colorless']['ownership']['damage_clause'])
        self.assertEqual(by_template(damage)['trigger-procedure']['status']['satisfaction'],'UNRESOLVED')
        self.assertIn('effect-context',by_template(damage))

    def test_generic_policy_independent_of_card_and_subject_labels(self):
        if not self.live():return
        for family in self.consumer.question_families:
            value=self.report(family);caps=deepcopy(value['capabilities']);cards=deepcopy(value['cards'])
            aliases={r['identity']['card_id']:'synthetic-card-'+str(i) for i,r in enumerate(cards)}
            for cap in caps:
                cap['subject_id']='renamed:'+cap['subject_id'];cap['display_name']='unrelated label'
                cap['evidence_key']='synthetic-evidence:'+cap['subject_id'];cap['card_id']=aliases[cap['card_id']]
            for card in cards:card['identity']['display_name']='another label'
            computed=policy.compute(family=family,capabilities=caps,cards=cards,supplied=value['context'])
            project=lambda rows:[{k:r[k] for k in ('template_id','information_needed','rationale','status','future_consumer')} for r in rows]
            self.assertCountEqual(project(computed),project(flat(value)))

    def test_identity_pilot_permission_and_production_abstentions(self):
        if not self.live():return
        for family in self.consumer.question_families:
            value=self.report(family);self.assertFalse(value['authority']['canonical_admission']);self.assertEqual(value['authority']['execution_authority'],'BLOCKED')
            self.assertEqual(set(value['authority']['permissions'].values()),{'NOT_ESTABLISHED'})
            for card in value['cards']:
                self.assertEqual(card['joins']['historical_correspondence']['status'],'ESTABLISHED')
                self.assertEqual(card['joins']['operator_production']['status'],'IDENTITY_NOT_ESTABLISHED')
                self.assertEqual(card['joins']['functional_role_pilot']['status'],'NOT_IN_SUPPORTED_COHORT')
                self.assertEqual(card['joins']['contextual_comparison_pilot']['status'],'NOT_IN_SUPPORTED_COHORT')
                expected='ESTABLISHED' if card['identity']['card_id']==inputs.CARD_IDS[1] else 'IDENTITY_NOT_ESTABLISHED'
                self.assertEqual(card['joins']['current_identifier_edge']['status'],expected)

    def test_unsupported_question_card_namespace_role_and_format_assertions(self):
        if not self.live():return
        for family in ('Nykthos','strategic-rank','universal-winner',None,True,[]):
            with self.assertRaises(api.RequirementsError):self.report(family)
        pair=sorted(policy.family_registry()['mana-and-utility']['cards'])
        self.assertEqual(self.consumer.for_cards(inputs.NAMESPACE,pair,'mana-and-utility').to_dict(),self.report('mana-and-utility'))
        for namespace,ids in (('Card',pair),(inputs.NAMESPACE,['foreign']),(inputs.NAMESPACE,pair[::-1])):
            with self.assertRaises(api.RequirementsError):self.consumer.for_cards(namespace,ids,'mana-and-utility')
        for key in ('role','format_verified','format_legality','game_state','observed_swamp_count'):
            with self.assertRaises(ValueError):self.report('mana-and-utility',dict(context(),**{key:True}))

    def test_reports_recompute_and_reject_coherently_rehashed_tampering(self):
        if not self.live():return
        original=self.report('color-context')
        for mutation in ('policy','candidate','requirement','validation','authority','input','extra','missing','selector'):
            value=deepcopy(original)
            if mutation=='policy':value['policy_id']='sha256:'+'0'*64
            elif mutation=='candidate':value['capabilities'][0]['candidate_id']=dict(decision.CANDIDATE_IDS)['coffers-mana']
            elif mutation=='requirement':flat(value)[0]['rationale']='universally stronger'
            elif mutation=='validation':flat(value)[0]['status']['validation']='ESTABLISHED'
            elif mutation=='authority':value['authority']['canonical_admission']=0
            elif mutation=='input':value['context']['authority']='OBSERVED_FACTS'
            elif mutation=='extra':value['power_score']=100
            elif mutation=='selector':value['requirement_id']=False
            else:del value['cards'][0]['joins']['operator_production']
            value=c.seal(api.VERSION,value,'report_id')
            with self.assertRaises(api.RequirementsError):self.consumer.validate_report(value)
        raw=c.canonical(original)
        with self.assertRaises(ValueError):self.consumer.parse_report(raw.replace(b'"kind":"requirements"',b'"kind":"requirements","kind":"requirements"'))
        with self.assertRaises(ValueError):self.consumer.parse_report(b' '*65537)

    def test_integrity_detailed_routes_and_historical_output_preservation(self):
        if not self.live():return
        for family in self.consumer.question_families:
            value=self.report(family);old=self.consumer.detailed(value['overlay_reference'])
            self.assertEqual(old.to_dict()['selector'],family)
            full=self.consumer.detailed(value['full_evidence_reference'])
            self.assertEqual(full.to_dict()['report_id'],decision.OVERVIEW_ID)
            self.assertEqual(hashlib.sha256(full.to_json().encode()).hexdigest(),decision.OVERVIEW_SHA256)
            for cap in value['capabilities']:
                original=self.consumer.detailed(cap['explanation_reference']).to_dict()['subjects'][0]
                self.assertEqual(original['provenance'],cap['provenance'])
            changed=deepcopy(value['overlay_reference']);changed['sha256']='0'*64
            with self.assertRaises(ValueError):self.consumer.detailed(changed)
        self.consumer.validate_report(self.consumer.check().to_dict())

    def test_private_ownership_and_unverified_leads_are_not_dereferenced(self):
        if not self.live():return
        supplied=context([dict(dimension='deck_objective',value='effect-tradeoffs')],leads=[dict(category='deck-context',reference='/not/an/authenticated/source')])
        with patch('builtins.open',side_effect=AssertionError('no lead IO')):
            doc=self.consumer.requirements('damage-ownership',supplied)
        original=doc.to_json();supplied['declarations'].clear();doc.to_dict()['requirements'].clear();self.assertEqual(doc.to_json(),original)
        with self.assertRaises(FrozenInstanceError):self.consumer._overlay=None
        self.assertEqual(by_template(doc.to_dict())['effect-context']['status']['information'],'DECLARED_UNVERIFIED')

    def test_actual_public_load_once_and_fresh_admission_tampering_rejection(self):
        if not self.live():return
        from card_intelligence.mechanics import MechanicalCardIntelligence as M
        from query import CanonicalQueryEngine as Q
        from card_rules_pilot import land_context
        with patch.object(M,'from_attachment',wraps=M.from_attachment) as m,patch.object(Q,'from_attachment',wraps=Q.from_attachment) as q,patch.object(land_context,'read_context',wraps=land_context.read_context) as rules:
            consumer=api.load_strategic_requirements(**decision_arguments())
            for family in consumer.question_families:consumer.requirements(family)
            self.assertEqual((m.call_count,q.call_count,rules.call_count),(1,1,1))
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)/'decision';shutil.copytree(decision_arguments()['decision_root'],root);path=root/decision.OWNER_RECORD
            value=c.read_json(path);value['scope']['not_established']=[];path.write_bytes(c.canonical(c.seal(decision.DECISION_VERSION,value,'decision_id')))
            with self.assertRaises(api.RequirementsError):api.load_strategic_requirements(**decision_arguments(decision_root=root))
        from card_intelligence import land_overlay as o
        real=o.LandEvidenceOverlay.compare
        def changed(reader,family,scenario=None):
            value=real(reader,family,scenario).to_dict();value['cards'][0]['mechanical']['dossier_id']='sha256:'+'0'*64
            return c.ReviewDocument._verified(c.seal(o.VERSION,value,'report_id'),limit=o.REPORT_LIMIT)
        with patch.object(o.LandEvidenceOverlay,'compare',changed):
            with self.assertRaises(api.RequirementsError):api.load_strategic_requirements(**decision_arguments())

    def test_inspection_views_compact_size_performance_and_render_parity(self):
        if not self.live():return
        self.assertLess(self.load_seconds,30)
        for family in self.consumer.question_families:
            start=time.perf_counter();doc=self.consumer.requirements(family);text=api.render_requirements(doc);value=doc.to_dict()
            self.assertLess(time.perf_counter()-start,5);self.assertLessEqual(len(doc.to_json().encode()),65536);self.assertLessEqual(len(text.encode()),32768)
            self.assertEqual(self.consumer.parse_report(doc.to_json().encode()).to_json(),doc.to_json())
            declarations=[dict(dimension='format_label',value='x'*80),dict(dimension='format_label',value='y'*80),dict(dimension='deck_objective',value='mana-flexibility'),dict(dimension='deck_objective',value='effect-tradeoffs'),dict(dimension='deck_color_requirements',value=[]),dict(dimension='deck_color_requirements',value=list(hp.COLORS)),dict(dimension='alternatives',value=[]),dict(dimension='alternatives',value=[dict(namespace=inputs.NAMESPACE,card_id=cid) for cid in inputs.CARD_IDS])]
            assumptions=[]
            if family=='variable-output':assumptions=[dict(dimension='controlled_swamp_count',value=n) for n in (0,hp.COUNT_LIMIT)]
            if family=='color-context':assumptions=[dict(dimension='commander_color_identity',value=v) for v in ([],list(hp.COLORS))]
            worst=self.consumer.requirements(family,context(declarations,assumptions,[dict(category=k,reference='x'*160) for k in inputs.LEAD_CATEGORIES]))
            self.assertLessEqual(len(worst.to_json().encode()),65536);self.assertLessEqual(len(api.render_requirements(worst).encode()),32768)
            self.assertEqual(worst.to_dict()['request_state'],'CONFLICTING')

            self.assertIn(value['report_id'],text)
            for row in flat(value):self.assertIn(row['information_needed'],text);self.assertIn(row['rationale'],text)
            requirement=flat(value)[0]
            self.assertEqual(sum(map(len,self.consumer.requirement(family,requirement['requirement_id']).to_dict()['requirements'].values())),1)
            self.assertTrue(flat(self.consumer.missing(family).to_dict()))
            self.assertFalse(flat(self.consumer.provenance(family).to_dict()))
            with self.assertRaises(api.RequirementsError):self.consumer.requirement(family,'foreign')

    def test_actual_retained_demonstrations_reproduce_reports_and_statuses(self):
        if not self.live():return
        receipt=c.read_json(ROOT/'docs/examples/strategic-context-requirements-v1.json')
        self.assertEqual(receipt['policy_id'],policy.POLICY_ID);self.assertEqual(receipt['input_contract_id'],inputs.CONTRACT_ID)
        self.assertEqual(len(receipt['records']),12)
        for item in receipt['records']:
            doc=self.consumer.requirements(item['family'],item['context']);value=doc.to_dict()
            self.assertEqual(value['report_id'],item['report_id'])
            self.assertEqual(len(doc.to_json().encode()),item['canonical_bytes']);self.assertEqual(len(api.render_requirements(doc).encode()),item['readable_bytes'])
            for requirement in item['requirements']:
                original=next(r for r in flat(value) if r['requirement_id']==requirement['requirement_id'])
                self.assertEqual(original['status'],requirement['status'])
        self.assertEqual(self.consumer.detailed(receipt['full_evidence_reference']).to_dict()['report_id'],decision.OVERVIEW_ID)

    def test_actual_read_only_cli_and_explicit_conflict_exit(self):
        if not self.live():return
        from card_intelligence.strategic_requirements_cli import main
        args=[]
        for k,v in decision_arguments().items():args += ['--'+k.replace('_','-'),str(v)]
        paths=[ROOT/'data/canonical/state.json',ROOT/'data/review/land-semantic-decisions/owner-acceptance-v1.json',ROOT/'src/card_intelligence/land_overlay.py']
        before={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
        output=io.StringIO()
        with contextlib.redirect_stdout(output):self.assertEqual(main(args+['--json','requirements','variable-output','--swamp-count','5']),0)
        self.consumer.validate_report(json.loads(output.getvalue()))
        self.assertEqual(before,{str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths})
        output=io.StringIO()
        with patch('card_intelligence.strategic_requirements_cli.load_strategic_requirements',return_value=self.consumer),contextlib.redirect_stdout(output):
            self.assertEqual(main(args+['--json','requirements','mana-and-utility','--objective','mana-flexibility','--objective','interaction-utility']),3)
        self.assertEqual(json.loads(output.getvalue())['request_state'],'CONFLICTING')


class StrategicRequirementsPreservationTests(unittest.TestCase):
    def test_exact_predecessor_helper_reversal_and_finite_source_pins(self):
        import requirements_preservation_support as support
        import overlay_preservation_support as older
        import proposed_spell_packet_analysis_preservation as guard
        for name,pins in support.PINS.items():
            raw=(ROOT/name).read_bytes();old=support.preceding_bytes(name,raw)
            self.assertEqual(hashlib.sha256(old).hexdigest(),pins['old']['sha256'])
            for changed in (raw+b'future',b'X'+raw[1:],bytearray(raw)):
                with self.assertRaises(AssertionError):support.preceding_bytes(name,changed)
        self.assertEqual(set(support.ADDITIONS),set(guard.STRATEGIC_REQUIREMENTS_SOURCE_PATHS))
        self.assertEqual(len(support.ADDITIONS),4)
        for name in support.ADDITIONS:
            self.assertTrue(guard.is_packet_analysis_addition(ROOT/name))
            self.assertTrue(older.is_overlay_addition(ROOT/name,ROOT));older.assert_overlay_addition(ROOT/name,ROOT)
            self.assertFalse(older.is_overlay_addition(ROOT/(name+'.future'),ROOT))
        for name in older.OVERLAY_ADDITIONS:older.assert_overlay_addition(ROOT/name,ROOT)


if __name__=='__main__':unittest.main()
