"""Conditional behavior, evidence admission and bounded uncertainty regressions.

Synthetic criterion matrices exercise policy algebra only. Real-Card reports use
one current validated successor; a publication-expanded catalog must reject and
is never replaced with an earlier positive catalog.
"""
from copy import deepcopy
from dataclasses import FrozenInstanceError
import inspect
import hashlib
import json
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch

from card_rules_pilot import cards, pilot, contract as c, reasoning_policy as classification
from card_rules_pilot import behavior as b, behavior_policy as policy, behavior_context as context
from test_card_rules_pilot_cards import current_catalog_intact

ROOT = Path(__file__).resolve().parents[1]
SUBJECTS = tuple(row[0] for row in cards.SUBJECTS)


def arguments(**changes):
    value = dict(catalog_root=ROOT, mechanical_root=ROOT,
        review_root=ROOT / 'reference-reviews',
        plan_path=ROOT / 'data/review/card-rules-mana-pilot/plan.json',
        successor_root=ROOT / 'data/review/mana-context-reassessment',
        expected_profile_id=cards.PROFILE_ID,
        expected_query_snapshot_id=cards.QUERY_ID, expected_plan_id=pilot.PLAN_ID)
    value.update(changes)
    return value


def synthetic(kind='proposed_activated_ability', **states):
    """Fictional state matrix: no Card names, passages or proposal labels."""
    descriptor = classification.policy_document()
    active = (descriptor['activated_substantive'] + descriptor['activated_method_obligations']
        if kind == 'proposed_activated_ability' else descriptor['triggered_substantive']
        if kind == 'proposed_triggered_ability' else [])
    return dict(proposed_kind=kind,
        criteria=[{'criterion_id': row['criterion_id'],
            'state': states.get(row['criterion_id'], 'proposed_satisfied'
                if row['criterion_id'] in active else 'inapplicable'),
            'rule_refs': row['rule_refs']} for row in descriptor['criterion_definitions']],
        kind_evidence_refs=['type_line', 'rule:605.5b'] if kind == 'proposed_spell_instruction'
            else ['selected_passage', 'rule:605.1a' if kind == 'proposed_activated_ability' else 'rule:605.1b'])


def retained_policy_facts():
    """Retained structured fixtures, never a real-Card provenance admission."""
    names = ('gameplay-rules-bounded-mana-ability-projection',
        'gameplay-rules-bounded-mana-classification-projection',
        'gameplay-rules-bounded-mana-stack-exception-projection',
        'gameplay-rules-mana-classification-source-context',
        'gameplay-rules-bounded-activated-ability-procedure-projection',
        'gameplay-rules-casting-stage-family-completion')
    result = {}
    for name in names:
        root = ROOT / 'reference-reviews' / name
        manifest = json.loads((root / 'manifest.json').read_bytes())
        projection = json.loads((root / 'projection.json').read_bytes())
        for rule in projection['rules']:
            if rule['rule_reference'] in context.CONTEXT_REFERENCES:
                result[rule['rule_reference']] = {'package': name,
                    'package_id': manifest['package_id'],
                    'projection_id': projection['projection_id'],
                    'projection_schema_version': projection['schema_version'], 'rule': rule}
    if set(result) != set(context.CONTEXT_REFERENCES):
        raise AssertionError('complete 24-rule structured fixture required')
    return result


class SyntheticBehaviorPolicyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.facts = retained_policy_facts()

    def compute(self, kind='proposed_activated_ability', **states):
        return policy.compute(**synthetic(kind, **states), rule_facts=self.facts)


    def test_explicit_kind_and_completed_classification_select_distinct_branches(self):
        expected=(('proposed_activated_ability',{},'CONDITIONAL_ACTIVATED_MANA'),
            ('proposed_activated_ability',{'potential_mana':'proposed_not_satisfied'},'CONDITIONAL_ORDINARY_ACTIVATED'),
            ('proposed_triggered_ability',{},'CONDITIONAL_TRIGGERED_MANA'),
            ('proposed_triggered_ability',{'trigger_potential_mana':'proposed_not_satisfied'},'UNRESOLVED_ORDINARY_TRIGGERED_FRONTIER'),
            ('proposed_spell_instruction',{},'CONDITIONAL_SPELL_PROPOSAL'))
        for kind,states,branch in expected:
            with self.subTest(kind=kind,states=states):
                value=self.compute(kind,**states)
                self.assertEqual(value['branch'],branch)
                self.assertEqual(value['classification'],classification.compute(**synthetic(kind,**states)))
                self.assertEqual(value['calculation_id'],c.identity(policy.RESULT_VERSION,value,'calculation_id'))
                self.assertTrue(value['consequences'])

    def test_exclusion_or_failed_method_alone_never_supplies_ordinary_placement(self):
        for state in ('unknown','unsupported','conflicting','inapplicable','proposed_not_satisfied'):
            for negative in ({},{'potential_mana':'proposed_not_satisfied'}):
                with self.subTest(method=state,negative=negative):
                    value=self.compute(self_replacement_considered=state,**negative)
                    self.assertEqual(value['branch'],'UNRESOLVED_BEHAVIOR')
                    self.assertEqual(value['consequences'],[])
                    self.assertEqual(value['classification']['overall_assessment'],classification.INCOMPLETE)
        triggered=self.compute('proposed_triggered_ability',trigger_potential_mana='proposed_not_satisfied')
        self.assertEqual(triggered['branch'],'UNRESOLVED_ORDINARY_TRIGGERED_FRONTIER')
        self.assertEqual(triggered['consequences'][0]['conditional_consequence']['placement'],'UNSUPPORTED_603_FRONTIER')

    def test_unknown_unsupported_conflicting_inputs_preserve_uncertainty(self):
        for state in ('unknown','unsupported','conflicting','inapplicable'):
            for negative in ({},{'potential_mana':'proposed_not_satisfied'}):
                with self.subTest(state=state,negative=negative):
                    value=self.compute(no_target=state,**negative)
                    self.assertEqual(value['branch'],'UNRESOLVED_BEHAVIOR')
                    self.assertEqual(value['consequences'],[])
                    self.assertIn({'criterion_id':'no_target','state':state},value['classification']['unresolved_requirements'])
        missing=deepcopy(self.facts); missing.pop('602.2a')
        value=policy.compute(**synthetic(potential_mana='proposed_not_satisfied'),rule_facts=missing)
        self.assertEqual(value['branch'],'UNRESOLVED_BEHAVIOR')
        self.assertEqual(value['missing_rule_refs'],['602.2a'])
        self.assertEqual(value['consequences'],[])
        for missing_ref in ('605.3b','605.4a','601.2a'):
            kind={'605.3b':'proposed_activated_ability','605.4a':'proposed_triggered_ability',
                  '601.2a':'proposed_spell_instruction'}[missing_ref]
            missing=deepcopy(self.facts); missing.pop(missing_ref)
            value=policy.compute(**synthetic(kind),rule_facts=missing)
            self.assertEqual(value['branch'],'UNRESOLVED_BEHAVIOR')
            self.assertFalse(value['consequences'])

    def test_negative_kind_reading_conflicts_with_explicit_kind_without_behavior(self):
        for kind,criterion in (('proposed_activated_ability','activated_kind'),
                               ('proposed_triggered_ability','triggered_kind')):
            with self.subTest(kind=kind):
                value=policy.compute(**synthetic(kind,**{criterion:'proposed_not_satisfied'}),
                    rule_facts=self.facts,
                    hypothetical={'schema_version':policy.HYPOTHETICAL_VERSION,'prior_priority':'TRUE'})
                self.assertEqual(value['classification']['overall_assessment'],classification.EXCLUDED)
                self.assertIn(criterion,value['classification']['negative_witnesses'])
                self.assertEqual(value['branch'],'UNRESOLVED_BEHAVIOR')
                self.assertFalse(value['consequences'])
                self.assertEqual(value['hypothetical_applicability'],'NOT_APPLICABLE_TO_THIS_BRANCH')
                self.assertTrue(value['remaining_unresolved'])

    def test_priority_true_false_unknown_and_absent_have_no_converse(self):
        statuses={'TRUE':'CONDITIONAL_RETURN_IMPLICATION','FALSE':'ANTECEDENT_ABSENT_NO_RETURN_CONCLUSION',
                  'UNKNOWN':'APPLICABILITY_UNKNOWN'}
        for premise,status in statuses.items():
            value=policy.compute(**synthetic(),rule_facts=self.facts,
                hypothetical={'schema_version':policy.HYPOTHETICAL_VERSION,'prior_priority':premise})
            implication=next(row for row in value['consequences'] if row['consequence_id']=='activated_priority_implication')
            result=implication['conditional_consequence']
            self.assertEqual(result['status'],status)
            self.assertFalse(result['converse_inferred'])
            self.assertEqual(result['premise_origin'],'EXPLICIT_HYPOTHETICAL')
            self.assertIn('immediately before',implication['antecedents'][-1])
            self.assertEqual(implication['rule_refs'],['405.6c'])
            hyp=value['hypothetical_context']
            self.assertFalse(hyp['card_evidence'])
            self.assertFalse(hyp['interpretation_revision'])
            self.assertFalse(hyp['executable_state_transition'])
            self.assertTrue(hyp['other_assumptions'])
            if premise=='FALSE':
                self.assertIn('another rule',result['explanation'])
        ordinary=self.compute()
        implication=next(row for row in ordinary['consequences'] if row['consequence_id']=='activated_priority_implication')
        self.assertEqual(implication['conditional_consequence']['status'],'APPLICABILITY_UNKNOWN')
        self.assertEqual(implication['conditional_consequence']['premise_origin'],'NO_REAL_GAME_PRIORITY_EVIDENCE')

    def test_activated_priority_and_opportunities_never_transfer_to_other_branches(self):
        cases=(('proposed_triggered_ability',{}),('proposed_spell_instruction',{}),
            ('proposed_activated_ability',{'potential_mana':'proposed_not_satisfied'}),
            ('proposed_activated_ability',{'self_replacement_considered':'unknown'}),
            ('proposed_triggered_ability',{'qualifying_trigger_relationship':'unknown'}))
        for kind,states in cases:
            value=policy.compute(**synthetic(kind,**states),rule_facts=self.facts,
                hypothetical={'schema_version':policy.HYPOTHETICAL_VERSION,'prior_priority':'TRUE'})
            self.assertEqual(value['hypothetical_applicability'],'NOT_APPLICABLE_TO_THIS_BRANCH')
            ids={row['consequence_id'] for row in value['consequences']}
            self.assertNotIn('activated_priority_implication',ids)
            self.assertNotIn('activated_opportunity_categories',ids)
            refs={ref for row in value['consequences'] for ref in row['rule_refs']}
            self.assertNotIn('605.3a',refs)
            self.assertNotIn('405.6c',refs)

    def test_no_stack_uses_direct_kind_specific_evidence_and_precise_limits(self):
        activated=self.compute(); triggered=self.compute('proposed_triggered_ability')
        a=next(row for row in activated['consequences'] if row['consequence_id']=='activated_no_stack')
        t=next(row for row in triggered['consequences'] if row['consequence_id']=='triggered_no_stack')
        self.assertEqual(a['rule_refs'],['605.3b'])
        self.assertEqual(t['rule_refs'],['605.4a'])
        self.assertFalse(a['conditional_consequence']['stack_entry'])
        self.assertFalse(t['conditional_consequence']['stack_entry'])
        self.assertFalse(t['conditional_consequence']['waits_for_priority'])
        self.assertEqual(a['conditional_consequence']['resolution_context'],'IMMEDIATELY_AFTER_ACTIVATION')
        self.assertEqual(t['conditional_consequence']['resolution_context'],'IMMEDIATELY_AFTER_CAUSING_MANA_ABILITY')
        for result in (activated,triggered):
            separation=next(row for row in result['consequences']
                if row['consequence_id']=='classification_usability_output_separation')
            self.assertFalse(separation['conditional_consequence']['classification_implies_current_activation_eligibility'])
            self.assertFalse(separation['conditional_consequence']['classification_implies_current_output'])
        immediate=next(row for row in activated['consequences'] if row['consequence_id']=='immediate_resolution_context')
        self.assertEqual(immediate['conditional_consequence']['fine_grained_ordering'],'NOT_ESTABLISHED')
        self.assertIn('actually belong',immediate['antecedents'][-1])
        self.assertIn('no additional effect is asserted',immediate['conditional_consequence']['explanation'])

    def test_ordinary_placement_and_spell_start_supply_no_response_or_completion(self):
        activated=self.compute(potential_mana='proposed_not_satisfied')
        consequence=activated['consequences'][0]
        self.assertEqual(consequence['rule_refs'],['602.2','602.2a'])
        self.assertEqual(consequence['conditional_consequence']['object_kind'],'ABILITY_NOT_CARD')
        self.assertEqual(consequence['conditional_consequence']['relative_stack_position'],'TOPMOST')
        self.assertIn('counterspell applicability',' '.join(consequence['remaining_unknowns']))
        self.assertIn('successful completion',' '.join(consequence['remaining_unknowns']))
        self.assertNotIn('601.2a',consequence['rule_refs'])
        spell=self.compute('proposed_spell_instruction')['consequences'][0]
        self.assertEqual(spell['rule_refs'],['605.5b','601.2a'])
        self.assertFalse(spell['conditional_consequence']['casting_complete_at_start'])
        self.assertIn('outstanding payment request',' '.join(spell['remaining_unknowns']))
        self.assertNotIn('602.2',spell['rule_refs'])

    def test_every_consequence_resolves_exact_evidence_and_explicit_antecedents(self):
        for kind in ('proposed_activated_ability','proposed_triggered_ability','proposed_spell_instruction'):
            result=self.compute(kind)
            for row in result['consequences']:
                self.assertEqual(row['classification'],result['classification']['overall_assessment'])
                self.assertEqual(row['method_status'],result['classification']['method_status'])
                self.assertTrue(row['pending_interpretation'])
                self.assertTrue(row['antecedents'])
                self.assertTrue(row['remaining_unknowns'])
                self.assertTrue(row['conditional_consequence']['explanation'])
                self.assertEqual(row['semantic_review_status'],'PENDING_NOT_ESTABLISHED')
                self.assertEqual(row['review'],{'status':'requires_review','human_attestation':None,'canonical_admission':False})
                self.assertEqual(row['execution_authority'],'BLOCKED')
                for binding in row['rule_bindings']:
                    expected=self.facts[binding['rule_reference']]
                    self.assertEqual(binding['package_id'],expected['package_id'])
                    self.assertEqual(binding['projection_id'],expected['projection_id'])
                    self.assertEqual(binding['rule_id'],expected['rule']['rule_id'])
                    self.assertEqual(binding['source_anchor'],expected['rule']['source_anchor'])

    def test_malformed_types_unknown_fields_and_substituted_rule_content_reject(self):
        changes=[]
        value=synthetic(); value['criteria'][0]['state']=True; changes.append(value)
        value=synthetic(); value['criteria'][0]['extra']=False; changes.append(value)
        value=synthetic(); value['criteria'].pop(); changes.append(value)
        value=synthetic(); value['proposed_kind']=1; changes.append(value)
        value=synthetic(); value['kind_evidence_refs']=['rule:605.5b']; changes.append(value)
        for value in changes:
            with self.assertRaises(c.PilotError):
                policy.compute(**value,rule_facts=self.facts)
        for mutation in ('type','extra','content','foreign','stale-package','stale-projection','stale-schema'):
            facts=deepcopy(self.facts)
            if mutation=='type': facts['602.2']['rule']['execution_ready']=0
            elif mutation=='extra': facts['602.2']['unexpected']=True
            elif mutation=='content': facts['602.2']['rule']['findings']['ordinary_context']=[]
            elif mutation=='foreign': facts['603']=facts['602.2']
            elif mutation=='stale-package': facts['602.2']['package_id']='sha256:'+'0'*64
            elif mutation=='stale-projection': facts['602.2']['projection_id']='sha256:'+'0'*64
            else: facts['602.2']['projection_schema_version']='stale-version'
            with self.subTest(mutation=mutation),self.assertRaises(c.PilotError):
                policy.compute(**synthetic(),rule_facts=facts)
        for hypothetical in (True,{}, {'schema_version':policy.HYPOTHETICAL_VERSION,'prior_priority':True},
                {'schema_version':policy.HYPOTHETICAL_VERSION,'prior_priority':'TRUE','game_state':{}},
                {'schema_version':'unsupported','prior_priority':'TRUE'}):
            with self.assertRaises(c.PilotError):
                policy.compute(**synthetic(),rule_facts=self.facts,hypothetical=hypothetical)

    def test_generic_policy_has_no_card_name_prose_or_provider_decision_input(self):
        parameters=set(inspect.signature(policy.compute).parameters)
        self.assertEqual(parameters,{'proposed_kind','criteria','kind_evidence_refs','rule_facts','hypothetical'})
        for extra in ('card_name','subject_id','selected_passage','provider_mana','proposed_classification'):
            with self.subTest(extra=extra),self.assertRaises(TypeError):
                policy.compute(**synthetic(),rule_facts=self.facts,**{extra:'Sol Ring'})
        first=policy.compute(**synthetic(),rule_facts=self.facts)
        view=deepcopy(first); view['consequences'].clear()
        self.assertEqual(policy.compute(**synthetic(),rule_facts=self.facts),first)
        descriptor=policy.policy_document(); descriptor['review']['canonical_admission']=True
        self.assertFalse(policy.policy_document()['review']['canonical_admission'])


class ActualBehaviorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.intact = current_catalog_intact(unittest.TestCase())
        captured=[]
        original=b.admit_context
        def capture(**kwargs):
            captured.append(kwargs['successor'])
            return original(**kwargs)
        with patch.object(b,'admit_context',side_effect=capture):
            cls.consumer = b.load_behavior(**arguments()) if cls.intact else None
        cls.successor=captured[0] if captured else None
        cls.report = cls.consumer.comparison().to_dict() if cls.intact else None

    def current(self):
        return self.intact

    def rows(self):
        return {row['subject_id']: row for row in self.report['comparisons']}

    def test_actual_expanded_catalog_rejects_without_fixture_substitution(self):
        if not self.intact:
            self.assertFalse(current_catalog_intact(self))
            with self.assertRaises(ValueError):
                b.load_behavior(**arguments())

    def test_exact_seven_subjects_and_twenty_four_reused_rules(self):
        if not self.current():
            return
        self.assertEqual(tuple(self.rows()), SUBJECTS)
        retained = self.report['context']['retained_rules']
        self.assertEqual(tuple(retained['references']), context.CONTEXT_REFERENCES)
        self.assertEqual(len(set(retained['references'])), 24)
        self.assertEqual(retained['newly_reused_references'], ['602.2', '602.2a', '601.2a'])
        self.assertEqual((retained['original_interpretation_context_count'],
            retained['successor_interpretation_context_count'], retained['behavior_context_count']), (17,21,24))
        self.assertEqual((retained['global_source_units'], retained['global_projections']), (104,16))
        self.assertEqual((retained['new_source_units'], retained['new_projections']), (0,0))
        self.assertEqual(retained['source_inspection_allowlist'], [])
        self.assertEqual(retained['source_admission_allowlist'], [])
        self.assertFalse(retained['fresh_source_reproduction'])
        self.assertNotIn('602.2b', retained['references'])
        self.assertNotIn('601.2i', retained['references'])
        self.assertNotIn('603', retained['references'])
        self.assertFalse(retained['literal_602_2b_import_includes_601_2a'])
        self.assertEqual({(r['origin'],r['target']) for r in retained['unresolved_frontiers']},
            {('602.2','733'), ('602.2a','701.20a'), ('601.2a','611.2f'),
             ('601.2a','610.5'), ('605.4','603')})
        self.assertFalse(retained['historical_dependency_arrays_changed'])
        self.assertFalse(retained['historical_reviews_changed'])

    def test_all_seven_original_and_successor_results_keep_substantive_negatives(self):
        if not self.current():
            return
        unresolved='UNRESOLVED_BEHAVIOR'
        expected={
            'sol-ring-tap': (unresolved,'CONDITIONAL_ACTIVATED_MANA',[]),
            'basalt-monolith-tap': (unresolved,'CONDITIONAL_ACTIVATED_MANA',[]),
            'basalt-monolith-untap': (unresolved,'CONDITIONAL_ORDINARY_ACTIVATED',['potential_mana']),
            'deathrite-shaman-first': (unresolved,'CONDITIONAL_ORDINARY_ACTIVATED',['no_target']),
            'dark-ritual-spell': ('CONDITIONAL_SPELL_PROPOSAL','CONDITIONAL_SPELL_PROPOSAL',[]),
            'mana-flare-trigger': (unresolved,'CONDITIONAL_TRIGGERED_MANA',[]),
            'pitiless-plunderer-host-trigger': ('UNRESOLVED_ORDINARY_TRIGGERED_FRONTIER',
                'UNRESOLVED_ORDINARY_TRIGGERED_FRONTIER',['trigger_potential_mana','qualifying_trigger_relationship'])}
        records={r['subject_id']:r for r in self.report['context']['successor_input']['reassessments']}
        for sid,(before,after,negatives) in expected.items():
            with self.subTest(subject=sid):
                row=self.rows()[sid]
                self.assertEqual((row['original']['branch'],row['successor']['branch']),(before,after))
                for reading in ('original','successor'):
                    self.assertEqual(row[reading]['classification']['negative_witnesses'],negatives)
                    self.assertEqual(row[reading]['classification']['policy_id'],classification.POLICY_ID)
                self.assertEqual(row['original_interpretation_id'],row['original_candidate_id'])
                self.assertEqual(row['successor_interpretation_id'],records[sid]['reassessment_id']
                    if sid in records else row['original_candidate_id'])
                if sid in SUBJECTS[:4]:
                    self.assertEqual(row['original']['classification']['method_status'],'INCOMPLETE')
                    self.assertFalse(row['original']['consequences'])
                    self.assertEqual(row['successor']['classification']['method_status'],'PROPOSED_SATISFIED')
        context_value=self.report['context']
        candidates={r['subject']['subject_id']:r for r in context_value['original_comparison']['candidates']}
        self.assertEqual(candidates['deathrite-shaman-first']['subject']['selected_passage'],
            '{T}: Exile target land card from a graveyard. Add one mana of any color.')
        self.assertNotEqual(candidates['basalt-monolith-tap']['subject']['selected_passage'],
            candidates['basalt-monolith-untap']['subject']['selected_passage'])
        self.assertEqual(candidates['pitiless-plunderer-host-trigger']['subject']['owner'],'host_card')
        plunderer=self.rows()['pitiless-plunderer-host-trigger']['successor']['consequences'][0]
        self.assertEqual(plunderer['conditional_consequence']['placement'],'UNSUPPORTED_603_FRONTIER')

    def test_historical_own_contract_identities_reconstruct_without_new_admission(self):
        if not self.current():
            return
        from card_rules_pilot.reasoning import ManaEvidenceReasoning
        shared=self.report['context']['shared_original_rules_evidence']
        original=deepcopy(self.report['context']['original_comparison'])
        for candidate in original['candidates']:
            self.assertNotIn('rules_evidence',candidate)
            candidate['rules_evidence']=deepcopy(shared)
            self.assertEqual(candidate['candidate_id'],c.identity(c.CANDIDATE_VERSION,candidate,'candidate_id'))
        self.assertEqual(original['report_id'],c.identity(c.REPORT_VERSION,original,'report_id'))
        self.assertEqual(original['plan_id'],'sha256:acdfc01e0645dc788a5c04824cb40948377699fe9f047441500980578fb9aa83')
        self.assertEqual(original['report_id'],'sha256:a2b0dedc3ef68b779b5b3a36ec20f97afc348b1ce52ad79c9e4a3cd2a281da0c')
        historical=object.__new__(ManaEvidenceReasoning)
        object.__setattr__(historical,'_raw',c.owned(original))
        self.assertEqual(historical.comparison().to_dict()['report_id'],
            'sha256:40eeaca91627b97aaca9372d56dc7cef9ee8ef8ce60d9dff503aa1d10be941d4')
        self.assertEqual(historical.review_impact().to_dict()['report_id'],
            'sha256:69f04d914ae6653739f2c79f1849e9b54764e475035f71d30cef556f7e9b6014')
        self.assertEqual(classification.POLICY_ID,'sha256:5694ec96c5edcbe61895684c6885e556578b738f27a29154d95283542b1ed745')
        self.assertEqual(self.report['context']['successor_comparison_id'],
            'sha256:51ab182ea464d9374be53cd5d77a6cc76b6cc5210af168f4eb6b2afb2a2e2cb9')
        retained=self.report['context']['retained_rules']
        self.assertEqual(retained['historical_acquisition_identity'],
            'sha256:669d7db9ebcaf97853058fd62f408ce3c6596d5dae0ee72ff39d2ba9df56bb53')
        self.assertEqual(retained['successor_input_id'],context.SUCCESSOR_INPUT_ID)
        self.assertEqual(retained['successor_manifest_id'],context.SUCCESSOR_MANIFEST_ID)
        # A computed historical hypothetical remains a report, never evidence.
        with self.assertRaises(c.PilotError):
            context.admit_context(review_root=arguments()['review_root'],
                successor=historical.review_impact().to_dict())

    def test_complete_output_bound_and_single_admission_private_reuse(self):
        if not self.current():
            return
        with patch.object(b,'load_reassessment',wraps=b.load_reassessment) as successor_reader, \
             patch.object(b,'admit_context',wraps=b.admit_context) as context_reader:
            consumer=b.load_behavior(**arguments())
            self.assertEqual((successor_reader.call_count,context_reader.call_count),(1,1))
            self.assertLessEqual(len(consumer.comparison().to_json().encode()),b.REPORT_LIMIT)
            for sid in SUBJECTS:
                self.assertLessEqual(len(consumer.subject(sid).to_json().encode()),b.REPORT_LIMIT)
                for premise in ('true','false','unknown'):
                    self.assertLessEqual(len(consumer.priority(sid,premise).to_json().encode()),b.REPORT_LIMIT)
            self.assertEqual((successor_reader.call_count,context_reader.call_count),(1,1))
            b.load_behavior(**arguments())
            self.assertEqual((successor_reader.call_count,context_reader.call_count),(2,2))

    def test_additional_own_domains_schemas_anchors_and_complete_manifests(self):
        if not self.current():
            return
        from gameplay_rules.activated_ability_projection import package as activated
        from gameplay_rules.activated_ability_projection import contracts as activated_contracts
        from gameplay_rules.activated_ability_projection.source import anchor_identity as activated_anchor
        from gameplay_rules.casting_stage_family_completion import package as casting
        from gameplay_rules.casting_stage_family_completion import contracts as casting_contracts
        from gameplay_rules.casting_stage_family_completion.source import anchor_identity as casting_anchor
        retained=self.report['context']['retained_rules']
        wrappers={row['rule']['rule_reference']:row for row in retained['rules']}
        for module,contract,anchor,selected in (
                (activated,activated_contracts,activated_anchor,('602.2','602.2a')),
                (casting,casting_contracts,casting_anchor,('601.2a',))):
            directory=arguments()['review_root']/module.PACKAGE_NAME
            manifest=c.read_json(directory/'manifest.json')
            self.assertEqual(manifest['package_id'],c.identity(module.PACKAGE_SCHEMA,manifest,'package_id'))
            for name in module.RECORD_NAMES:
                record=c.read_json(directory/name)
                projected=name=='projection.json'
                field='projection_id' if projected else 'review_id'
                domain=record['schema_version'] if projected else module.RECORD_DOMAIN
                self.assertEqual(type(record['schema_version']),str if projected else int)
                self.assertEqual(record[field],c.identity(domain,record,field))
                self.assertEqual(manifest['record_ids'][name],record[field])
                raw=c.canonical(record)
                self.assertEqual(manifest['files'][name],{'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()})
            for ref in selected:
                row=wrappers[ref]
                self.assertEqual(row['package_id'],manifest['package_id'])
                self.assertEqual(row['rule']['rule_id'],contract.rule_identity(row['rule']))
                self.assertEqual(row['rule']['source_anchor']['anchor_id'],anchor(row['rule']['source_anchor']))
                self.assertEqual(row['rule']['source_anchor']['rule_reference'],ref)

    def test_additional_package_drift_duplicate_keys_and_coherent_substitution_reject(self):
        if not self.current():
            return
        from gameplay_rules.activated_ability_projection import package as activated
        from gameplay_rules.casting_stage_family_completion import package as casting
        with tempfile.TemporaryDirectory(prefix='mtglab-behavior-context-') as temp:
            root=Path(temp)
            for module in (activated,casting):
                shutil.copytree(arguments()['review_root']/module.PACKAGE_NAME,root/module.PACKAGE_NAME)
            admitted=context.admit_context(review_root=root,successor=self.successor)
            self.assertEqual(admitted.to_dict(),self.report['context']['retained_rules'])
            directory=root/activated.PACKAGE_NAME
            path=directory/'projection.json'; initial=path.read_bytes()
            for altered in (initial+b' ',b'{"schema_version":"duplicate",'+initial[1:]):
                path.write_bytes(altered)
                with self.assertRaises(ValueError):
                    context.admit_context(review_root=root,successor=self.successor)
            path.write_bytes(initial)
            from gameplay_rules.activated_ability_projection import contracts as activated_contracts
            from gameplay_rules.activated_ability_projection.source import anchor_identity
            changed=json.loads(initial)
            changed['rules'][0]['source_anchor']['byte_end']-=1
            changed['rules'][0]['source_anchor']['anchor_id']=anchor_identity(changed['rules'][0]['source_anchor'])
            changed['rules'][0]['rule_id']=activated_contracts.rule_identity(changed['rules'][0])
            changed=c.seal(changed['schema_version'],changed,'projection_id')
            path.write_bytes(c.canonical(changed))
            manifest=c.read_json(directory/'manifest.json')
            manifest['record_ids']['projection.json']=changed['projection_id']
            raw=path.read_bytes()
            manifest['files']['projection.json']={'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}
            manifest=c.seal(activated.PACKAGE_SCHEMA,manifest,'package_id')
            (directory/'manifest.json').write_bytes(c.canonical(manifest))
            self.assertEqual(manifest['package_id'],c.identity(activated.PACKAGE_SCHEMA,manifest,'package_id'))
            with self.assertRaises(ValueError):
                context.admit_context(review_root=root,successor=self.successor)
            self.assertEqual(admitted.to_dict(),self.report['context']['retained_rules'])

    def test_own_identities_pending_authority_and_independent_views(self):
        if not self.current():
            return
        documents = [self.consumer.comparison(), self.consumer.subject('deathrite-shaman-first'),
                     self.consumer.priority('sol-ring-tap','true'), self.consumer.check()]
        for document in documents:
            original = document.to_json()
            value = document.to_dict()
            self.assertEqual(value['report_id'], c.identity(value['schema_version'],value,'report_id'))
            self.assertEqual(value['semantic_review_status'],'PENDING_NOT_ESTABLISHED')
            self.assertEqual(value['review'], {'status':'requires_review','human_attestation':None,'canonical_admission':False})
            self.assertEqual(value['execution_authority'],'BLOCKED')
            value.clear()
            self.assertEqual(document.to_json(), original)
            with self.assertRaises((FrozenInstanceError, AttributeError)):
                document._raw = b'{}\n'
        original=self.consumer.comparison().to_json()
        with self.assertRaises((FrozenInstanceError, AttributeError)):
            self.consumer._raw = b'{}\n'
        self.assertEqual(self.consumer.comparison().to_json(), original)

    def test_closed_subject_priority_and_report_input_types(self):
        if not self.current():
            return
        for invalid in (None, True, 7, 7.0, '', 'treasure-tap', 'foreign-subject'):
            with self.subTest(subject=invalid), self.assertRaises(c.PilotError):
                self.consumer.subject(invalid)
        for invalid in (None, True, False, 0, 1, 1.0, '', 'TRUE', 'assume_yes'):
            with self.subTest(premise=invalid), self.assertRaises(c.PilotError):
                self.consumer.priority('sol-ring-tap',invalid)

    def test_forged_stale_rehashed_scope_and_authority_reject(self):
        if not self.current():
            return
        original=self.consumer.comparison().to_dict()
        changes=[]
        value=deepcopy(original); value['schema_version']='unsupported-v999'; changes.append(value)
        value=deepcopy(original); value['review']['canonical_admission']=0; changes.append(value)
        value=deepcopy(original); value['execution_authority']='READY'; changes.append(value)
        value=deepcopy(original); value['semantic_review_status']='APPROVED'; changes.append(value)
        value=deepcopy(original); value['official_ruling']=True; changes.append(value)
        value=deepcopy(original); value['comparisons'][0]['subject_id']='foreign'; changes.append(value)
        value=deepcopy(original); value['comparisons'][0]['original_candidate_id']='sha256:'+'0'*64; changes.append(value)
        value=deepcopy(original); value['context']['retained_rules']['rules'][0]['rule']['source_anchor']['effective_date']='2099-01-01'; changes.append(value)
        value=deepcopy(original); value['context']['retained_rules']['references'].append('603'); changes.append(value)
        value=deepcopy(original); value['context']['retained_rules']['rules'].pop(); changes.append(value)
        for value in changes:
            value=c.seal(value['schema_version'],value,'report_id')
            with self.assertRaises(c.PilotError):
                self.consumer.validate_report(value)
        self.assertEqual(self.consumer.validate_report(original).to_dict(), original)
        for imported in ({'classification':classification.ELIGIBLE}, {'report_id':original['report_id']},
                         {'comparisons':[]}, {'comparisons':True}, {'review':{'canonical_admission':1.0}}):
            with self.assertRaises((c.PilotError, ValueError)):
                self.consumer.validate_report(imported)

    def test_fresh_admission_checks_changed_successor_and_private_snapshot_survives(self):
        if not self.current():
            return
        with tempfile.TemporaryDirectory(prefix='mtglab-behavior-drift-') as temp:
            destination=Path(temp)/'successor'
            shutil.copytree(arguments()['successor_root'],destination)
            first=b.load_behavior(**arguments(successor_root=destination))
            original=first.comparison().to_json()
            path=destination/'reassessments.json'
            path.write_bytes(path.read_bytes()+b' ')
            self.assertEqual(first.comparison().to_json(),original)
            with self.assertRaises(ValueError):
                b.load_behavior(**arguments(successor_root=destination))
            path.write_bytes(b'{"schema_version":"x","schema_version":"duplicate"}\n')
            with self.assertRaises(ValueError):
                b.load_behavior(**arguments(successor_root=destination))


if __name__=='__main__':
    unittest.main()
