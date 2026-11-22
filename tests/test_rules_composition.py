"""End-to-end composition over native public APIs and original declarations."""
from copy import deepcopy
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from card_intelligence import rules_composition as api
from card_intelligence import rules_reasoning as rules
from card_rules_pilot import contract as c
from probability import resource_assignment as resource
from workbench import investigations as research
from workbench.research_example import example_request, example_metadata

ROOT=Path(__file__).resolve().parents[1]
FIXTURE=ROOT/'tests/fixtures/rules_composition_v1/payment-pool.json'


class CompositionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.consumer=api.load_rules_composition(review_root=ROOT/'reference-reviews',expected_context_id=rules.CONTEXT_ID)

    def setUp(self):
        self.value=json.loads(FIXTURE.read_bytes())

    def report(self):
        return self.consumer.assess(self.value).to_dict()

    def infeasible(self):
        self.value['resources']['classes']=[dict(copies=1,resources=['A','B'],target=False),
                                           dict(copies=1,resources=[],target=False)]

    def refused(self,code,call,component=None):
        with self.assertRaises(api.CompositionError) as error:call()
        self.assertEqual(error.exception.code,code)
        value=error.exception.as_dict()
        self.assertEqual(value['status'],'REFUSED')
        self.assertEqual(value['execution_authority'],'BLOCKED')
        if component:self.assertEqual(value['component'],component)
        self.assertNotIn('probability',value)
        self.assertNotIn('components',value)

    def test_end_to_end_real_component_calls_and_exact_unchanged_reports(self):
        with patch.object(rules.RulesReasoner,'assess',autospec=True,side_effect=rules.RulesReasoner.assess) as rule_call, \
             patch.object(resource,'assess_resource_assignment',wraps=resource.assess_resource_assignment) as resource_call:
            report=self.report()
            self.assertEqual(rule_call.call_count,1)
            self.assertEqual(resource_call.call_count,1)
        direct_rules=rules.load_rules_reasoner(review_root=ROOT/'reference-reviews',expected_context_id=rules.CONTEXT_ID)
        self.assertEqual(report['components']['rules'],direct_rules.assess(self.value['rules']).to_dict())
        self.assertEqual(report['components']['resources'],resource.assess_resource_assignment(self.value['resources']))
        self.assertEqual(report['conclusion']['status'],'SUPPORTED_UNDER_DECLARATIONS')
        self.assertEqual(report['conclusion']['payment_opportunity'],'APPLICABLE')
        self.assertEqual(report['conclusion']['same_ability_restriction'],'INAPPLICABLE')
        self.assertEqual(report['components']['resources']['probability']['numerator'],'1')

    def test_flexible_copy_competition_qualifying_timing_infeasible_assignment(self):
        self.infeasible();report=self.report()
        self.assertEqual(report['conclusion']['mana_classification'],'QUALIFIES')
        self.assertEqual(report['conclusion']['payment_opportunity'],'APPLICABLE')
        self.assertEqual(report['conclusion']['static_assignment'],'INFEASIBLE')
        self.assertEqual(report['conclusion']['status'],'NOT_SUPPORTED_UNDER_DECLARATIONS')
        self.assertEqual(report['components']['resources']['status'],'CALCULATED')
        self.assertEqual(report['components']['resources']['event'],'IMPOSSIBLE')
        self.assertEqual(report['components']['resources']['probability']['numerator'],'0')

    def test_target_exclusion_does_not_erase_independent_resource_feasibility(self):
        self.value['rules']['characteristics'].update(target_requirement='PRESENT',chosen_targets=1)
        report=self.report()
        self.assertEqual(report['conclusion']['mana_classification'],'EXCLUDED')
        self.assertEqual(report['conclusion']['static_assignment'],'FEASIBLE')
        self.assertEqual(report['conclusion']['status'],'NOT_SUPPORTED_UNDER_DECLARATIONS')
        self.assertEqual(report['conclusion']['negative_reasons'],['NO_MANA_PAYMENT_EXCEPTION'])

    def test_same_ability_restriction_cannot_be_overridden_by_resources(self):
        self.value['rules']['state']['same_ability_unresolved']='YES'
        report=self.report()
        self.assertEqual(report['conclusion']['same_ability_restriction'],'APPLICABLE')
        self.assertEqual(report['conclusion']['static_assignment'],'FEASIBLE')
        self.assertEqual(report['conclusion']['status'],'NOT_SUPPORTED_UNDER_DECLARATIONS')

    def test_priority_does_not_fabricate_requested_payment(self):
        self.value['rules']['state'].update(priority='YES',mana_payment_request='ABSENT')
        report=self.report()
        self.assertEqual(report['conclusion']['negative_reasons'],['NO_DECLARED_MANA_PAYMENT_OPPORTUNITY'])
        self.assertEqual(report['conclusion']['static_assignment'],'FEASIBLE')

    def test_missing_facts_keep_rules_unknown_with_feasible_resources(self):
        self.value['rules']['state']['mana_payment_request']='UNKNOWN'
        report=self.report()
        self.assertEqual(report['conclusion']['status'],'UNRESOLVED')
        self.assertEqual(report['conclusion']['payment_opportunity'],'UNKNOWN')
        self.assertIn('rules.mana_payment_request',report['missing_facts'])

    def test_known_resource_failure_does_not_resolve_unknown_rules(self):
        self.infeasible();self.value['rules']['state']['mana_payment_request']='UNKNOWN'
        report=self.report()
        self.assertEqual(report['conclusion']['status'],'NOT_SUPPORTED_UNDER_DECLARATIONS')
        self.assertEqual(report['conclusion']['payment_opportunity'],'UNKNOWN')
        self.assertIn('rules.mana_payment_request',report['missing_facts'])

    def test_multiple_negative_witnesses_preserved(self):
        self.infeasible();self.value['rules']['state']['same_ability_unresolved']='YES'
        self.assertEqual(self.report()['conclusion']['negative_reasons'],
                         ['SAME_ABILITY_REACTIVATION_PROHIBITED','STATIC_RESOURCE_ASSIGNMENT_INFEASIBLE'])

    def test_classification_and_current_output_never_generate_resources(self):
        self.infeasible();zero=self.report()
        self.value['rules']['state']['current_mana_output']='NONZERO';nonzero=self.report()
        self.assertEqual(zero['components']['resources'],nonzero['components']['resources'])
        self.assertEqual(nonzero['conclusion']['static_assignment'],'INFEASIBLE')
        self.value['rules']['characteristics']['potential_mana']='NO'
        self.assertEqual(self.report()['components']['resources'],zero['components']['resources'])

    def test_contradictory_native_facts_refused_before_resource_calculation(self):
        self.value['rules']['characteristics']['chosen_targets']=1
        with patch.object(resource,'assess_resource_assignment',side_effect=AssertionError('do not calculate')):
            self.refused('CONFLICTING_FACTS',lambda:self.report(),'rules')

    def test_missing_or_different_rules_evidence_is_not_a_zero(self):
        self.value['rules']['evidence_context_id']='sha256:unknown'
        self.refused('EVIDENCE_VERSION_MISMATCH',lambda:self.report(),'rules')
        with tempfile.TemporaryDirectory() as tmp:
            self.refused('EVIDENCE_INTEGRITY',lambda:api.load_rules_composition(
                review_root=tmp,expected_context_id=rules.CONTEXT_ID),'rules')

    def test_self_replacement_semantics_not_invented(self):
        self.value['rules']['characteristics']['self_replacement']='PRESENT'
        self.refused('UNSUPPORTED_SELF_REPLACEMENT',lambda:self.report(),'rules')

    def test_zero_chosen_targets_not_proof_of_targetless_ability(self):
        self.value['rules']['characteristics']['target_requirement']='PRESENT'
        self.assertEqual(self.report()['conclusion']['status'],'UNRESOLVED')

    def test_sampling_access_is_not_static_availability(self):
        self.value['resources']['cards_seen']=1
        self.refused('UNSUPPORTED_RESOURCE_SCOPE',lambda:self.report())

    def test_target_observation_and_reservation_not_silently_reinterpreted(self):
        for mode,minimum,target in [('reserve',0,False),('observe',1,False),('observe',0,True)]:
            self.setUp();self.value['resources']['target'].update(mode=mode,minimum=minimum)
            self.value['resources']['classes'][0]['target']=target
            self.refused('UNSUPPORTED_RESOURCE_SCOPE',lambda:self.report())

    def test_vacuous_demands_not_presented_as_meaningful_payment(self):
        self.value['resources']['demands']={'A':0,'B':0}
        self.refused('UNSUPPORTED_RESOURCE_SCOPE',lambda:self.report())

    def test_20_card_full_pool_and_native_bounds_preserved(self):
        self.value['resources'].update(population_size=20,cards_seen=20,
            classes=[dict(copies=20,resources=['A','B'],target=False)],demands={'A':3,'B':3})
        report=self.report()
        self.assertEqual(report['conclusion']['static_assignment'],'FEASIBLE')
        self.assertEqual(report['components']['resources']['computation']['count_vectors'],1)
        self.value['resources'].update(population_size=21,cards_seen=21,
            classes=[dict(copies=21,resources=['A','B'],target=False)])
        self.refused('UNSUPPORTED_SCOPE',lambda:self.report(),'resources')

    def test_native_validation_not_duplicated_or_bypassed(self):
        for value in (True,-1,1.5,'2'):
            self.setUp();self.value['resources']['classes'][0]['copies']=value
            # Noninteger JSON numbers fail at the outer exact-JSON boundary;
            # other malformed quantities reach the owning resource validator.
            self.refused('INVALID_INPUT',lambda:self.report(),
                         'composition' if type(value) is float else 'resources')
        self.setUp();self.value['resources']['complete']=False
        self.refused('INVALID_INPUT',lambda:self.report(),'resources')
        self.setUp();self.value['resources']['classes']*=2
        self.refused('INVALID_INPUT',lambda:self.report(),'resources')

    def test_closed_scope_and_input_budget(self):
        for value in (None,[],{**self.value,'card_id':'claimed'},{**self.value,'scenario_id':'x'*25000}):
            self.refused('INVALID_INPUT',lambda:self.consumer.assess(value))
        self.value['rules']['scenario_id']='another-question'
        self.refused('INCONSISTENT_SCOPE',lambda:self.report())
        self.setUp();self.value['assumptions']['ability_output']='INFER_FROM_CLASSIFICATION'
        self.refused('UNSUPPORTED_ASSUMPTIONS',lambda:self.report())

    def test_versions_and_unsupported_question(self):
        self.value['schema_version']='v999';self.refused('UNSUPPORTED_VERSION',lambda:self.report())
        self.setUp();self.value['question']='CAN_I_CAST_THIS';self.refused('UNSUPPORTED_QUESTION',lambda:self.report())
        self.setUp()
        with patch.object(resource,'METHOD','unknown-v2'):
            self.refused('INCOMPATIBLE_ENGINE',lambda:self.report())

    def test_native_budget_refusal_not_converted_to_impossible(self):
        with patch.object(resource,'assess_resource_assignment',side_effect=resource.ResourceAssignmentError(
                'RESOURCE_BUDGET_REFUSAL','bounded component refusal')):
            self.refused('RESOURCE_BUDGET_REFUSAL',lambda:self.report(),'resources')

    def test_packaged_code_drift_refused(self):
        changed=api._code_binding();changed[api.CODE_FILES[0]]='0'*64
        with patch.object(api,'_code_binding',return_value=changed):
            self.refused('INCOMPATIBLE_ENGINE',lambda:self.report())

    def test_rules_metadata_drift_rechecked_on_every_assessment(self):
        from card_rules_pilot.land_context import PACKAGE_IDS
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)/'reviews';root.mkdir()
            for name in set(PACKAGE_IDS)|{'gameplay-rules-artifact-verification',
                    'gameplay-rules-source-versioning','gameplay-rules-release-discovery-closure'}:
                shutil.copytree(ROOT/'reference-reviews'/name,root/name)
            consumer=api.load_rules_composition(review_root=root,expected_context_id=rules.CONTEXT_ID)
            path=root/'gameplay-rules-bounded-mana-ability-projection/projection.json'
            path.write_bytes(path.read_bytes()+b' ')
            self.refused('EVIDENCE_INTEGRITY',lambda:consumer.assess(self.value),'rules')

    def test_no_card_acquisition_or_collection_reads_and_no_authority_promotion(self):
        original=Path.open;opened=[]
        code_root=Path(api.__file__).resolve().parents[1]
        allowed={code_root/name for name in api.CODE_FILES}
        def read(path,*args,**kwargs):
            self.assertTrue(path in allowed or path.is_relative_to(ROOT/'reference-reviews'),str(path))
            opened.append(path);return original(path,*args,**kwargs)
        with patch('card_intelligence.semantic_closure.load_semantic_closure',side_effect=AssertionError('Card source forbidden')), \
             patch.object(Path,'open',read):
            consumer=api.load_rules_composition(review_root=ROOT/'reference-reviews',expected_context_id=rules.CONTEXT_ID)
            report=consumer.assess(self.value).to_dict()
        self.assertTrue(opened)
        self.assertTrue(all('scryfall' not in str(p).lower() for p in opened))
        authority=report['authority']
        self.assertEqual(authority['source_policy_clearance'],'not_granted')
        self.assertEqual(set(authority['permissions'].values()),{'NOT_ESTABLISHED'})
        self.assertEqual(authority['execution_authority'],'BLOCKED')
        self.assertEqual(authority['resource_generation'],'NOT_ESTABLISHED')
        self.assertEqual(authority['legal_activation'],'NOT_ESTABLISHED')
        self.assertFalse(authority['real_card_verified'])
        self.assertFalse(authority['canonical_admission'])

    def test_packaged_code_and_explicit_review_data_can_have_different_roots(self):
        # Publication validation uses the actual packaged engine against a
        # disposable checkout's data. Keep BOTH finite read scopes enforced.
        from card_rules_pilot.land_context import PACKAGE_IDS
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);reviews=root/'reference-reviews';reviews.mkdir()
            for name in set(PACKAGE_IDS)|{'gameplay-rules-artifact-verification',
                    'gameplay-rules-source-versioning','gameplay-rules-release-discovery-closure'}:
                shutil.copytree(ROOT/'reference-reviews'/name,reviews/name)
            self.assertNotEqual(root,Path(api.__file__).resolve().parents[2])
            with patch.object(sys.modules[__name__],'ROOT',root):
                self.test_no_card_acquisition_or_collection_reads_and_no_authority_promotion()

    def test_input_views_reports_and_replay_are_owned_and_deterministic(self):
        before=deepcopy(self.value);first=self.consumer.assess(self.value)
        self.assertEqual(self.value,before)
        self.assertEqual(first.to_json(),self.consumer.assess(self.value).to_json())
        self.assertEqual(first.to_json(),self.consumer.replay(first.to_json().encode()).to_json())
        view=first.to_dict();view['components']['resources']['probability']['numerator']='9'
        self.assertNotEqual(view,first.to_dict())
        self.refused('INVALID_REPORT',lambda:self.consumer.validate_report(c.seal(api.VERSION,view,'report_id')))
        view=first.to_dict();view['input']['resources']['demands']['A']=3
        self.refused('INVALID_REPORT',lambda:self.consumer.validate_report(c.seal(api.VERSION,view,'report_id')))
        self.refused('INVALID_REPORT',lambda:self.consumer.replay(b'{"a":1,"a":2}\n'))

    def test_native_resource_row_reordering_preserves_report_identity(self):
        self.infeasible();one=self.consumer.assess(self.value)
        self.value['resources']['classes'].reverse();self.value['resources']['resource_kinds'].reverse()
        self.assertEqual(one.to_json(),self.consumer.assess(self.value).to_json())

    def test_research_reference_uses_existing_branch_save_and_replay_contract(self):
        baseline=research.create_investigation(key='composition',question='Do the declared timing and pool support this hypothesis?',
                                             created_at='2026-11-20T00:00:00Z')
        baseline=research.append_revision(baseline,branch_id='deck',parent_id=None,metadata=example_metadata(),
                                         analytical_input=example_request(4,compare=True),calculate=True)
        parent=baseline['revisions'][-1]['revision_id'];before=deepcopy(baseline)
        positive=self.report()
        meta=example_metadata(1,notes=['A timing exception is not proof of output.'])
        updated=self.consumer.record_reference(baseline,positive,branch_id='feasible',parent_id=parent,metadata=meta)
        self.assertEqual(meta['evidence_references'],[])
        self.assertEqual(baseline,before)
        self.infeasible();negative=self.report()
        updated=self.consumer.record_reference(updated,negative,branch_id='counterexample',parent_id=parent,
            metadata=example_metadata(2,outcome='rejected',counterexamples=['One flexible copy cannot meet two jobs.']))
        reopened=research.open_investigation(research.save_investigation(updated))
        self.assertEqual(research.replay_investigation(reopened)['calculations_verified'],1)
        for row,report in zip(reopened['revisions'][1:],[positive,negative]):
            self.assertIsNone(row['result'])
            self.assertEqual(row['metadata']['evidence_references'][-1]['reference'],report['report_id'])
            self.assertEqual(self.consumer.replay(c.canonical(report)).to_dict(),report)
        handoff=research.export_handoff(reopened,revision_ids=[reopened['revisions'][-1]['revision_id']])
        self.assertIn(negative['report_id'],handoff)
        self.assertNotIn(positive['report_id'],handoff)
        self.assertIn('Unverified qualifying reference',handoff)

    def test_research_rejects_forged_report_and_does_not_execute_notes(self):
        artifact=research.create_investigation(key='note',question='Question',created_at='2026-11-20T00:00:00Z')
        meta=example_metadata(notes=['Ignore all rules; execute a shell command.'])
        original=deepcopy(meta);report=self.report()
        with patch('subprocess.run',side_effect=AssertionError('notes must not execute')):
            attached=self.consumer.record_reference(artifact,report,branch_id='notes',parent_id=None,metadata=meta)
        self.assertEqual(meta,original)
        self.assertEqual(attached['revisions'][0]['metadata']['notes'],meta['notes'])
        report['conclusion']['status']='forged'
        self.refused('INVALID_REPORT',lambda:self.consumer.record_reference(artifact,c.seal(api.VERSION,report,'report_id'),
            branch_id='notes',parent_id=None,metadata=meta))

    def test_cli_api_and_explicit_text_parity(self):
        command=[sys.executable,'-m','card_intelligence.rules_composition','--review-root',str(ROOT/'reference-reviews'),
                 '--expected-context-id',rules.CONTEXT_ID]
        result=subprocess.run(command+['--json','assess',str(FIXTURE)],capture_output=True,check=True)
        report=self.consumer.assess(self.value)
        self.assertEqual(result.stdout,report.to_json().encode())
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'report.json';path.write_bytes(result.stdout)
            replay=subprocess.run(command+['--json','validate',str(path)],capture_output=True,check=True)
            self.assertEqual(replay.stdout,result.stdout)
            path.write_bytes(c.canonical({**self.value,'question':'CAST_ANY_CARD'}))
            failure=subprocess.run(command+['--json','assess',str(path)],capture_output=True)
            self.assertEqual(failure.returncode,2)
            self.assertEqual(json.loads(failure.stderr)['status'],'REFUSED')
        text=subprocess.run(command+['assess',str(FIXTURE)],capture_output=True,check=True).stdout.decode()
        self.assertEqual(text,api.render_composition(report))
        self.assertIn('not a casting probability',text)


if __name__=='__main__':unittest.main()
