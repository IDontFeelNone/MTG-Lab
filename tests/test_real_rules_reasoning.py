"""Declared real-rules inference; never authenticate Card mechanics or actions."""
from copy import deepcopy
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from card_intelligence import rules_reasoning as r
from card_rules_pilot import contract as c

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT/'tests/fixtures/rules_reasoning_v1/payment.json'


class RulesReasoningTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.consumer = r.load_rules_reasoner(review_root=ROOT/'reference-reviews', expected_context_id=r.CONTEXT_ID)

    def setUp(self):
        self.value = json.loads(FIXTURE.read_bytes())

    def assess(self, *, traits=None, state=None):
        self.value['characteristics'].update(traits or {})
        self.value['state'].update(state or {})
        return self.consumer.assess(self.value).to_dict()

    def refused(self, code, call):
        with self.assertRaises(r.RulesReasoningError) as context:
            call()
        self.assertEqual(context.exception.code, code)
        result = context.exception.as_dict()
        self.assertEqual(result['status'], 'REFUSED')
        self.assertEqual(result['execution_authority'], 'BLOCKED')

    def test_payment_exception_without_priority_positive(self):
        report = self.assess()
        self.assertEqual(report['decision'], 'PAYMENT_TIMING_EXCEPTION_APPLIES')
        self.assertEqual(report['classification']['status'], 'QUALIFIES')
        self.assertEqual(report['missing_facts'], [])
        self.assertFalse(report['authority']['game_actions_performed'])
        self.assertEqual(report['authority']['legal_activation'], 'NOT_ESTABLISHED')

    def test_each_retained_payment_category(self):
        for category in r.PAYMENT_REQUESTS:
            with self.subTest(category=category):
                self.assertEqual(self.assess(state={'mana_payment_request':category})['decision'],
                                 'PAYMENT_TIMING_EXCEPTION_APPLIES')

    def test_ordinary_priority_does_not_invent_payment_request(self):
        report = self.assess(state={'priority':'YES','mana_payment_request':'ABSENT'})
        self.assertEqual(report['decision'], 'NO_DECLARED_MANA_PAYMENT_OPPORTUNITY')
        self.assertIn('ordinary-priority', report['explanation'])

    def test_targeted_ability_is_negative_not_universally_illegal(self):
        report = self.assess(traits={'target_requirement':'PRESENT','chosen_targets':1})
        self.assertEqual(report['decision'], 'NO_MANA_PAYMENT_EXCEPTION')
        self.assertEqual(report['authority']['legal_activation'], 'NOT_ESTABLISHED')

    def test_zero_chosen_does_not_erase_target_requirement(self):
        for requirement in ('PRESENT','UNKNOWN'):
            with self.subTest(requirement=requirement):
                report = self.assess(traits={'target_requirement':requirement,'chosen_targets':0})
                self.assertEqual(report['decision'], 'NEEDS_FACTS')
                self.assertIn('no_target', report['missing_facts'])

    def test_loyalty_is_about_cost_not_source_type(self):
        report = self.assess(traits={'loyalty_symbol_in_cost':'YES','source_is_planeswalker':'NO'})
        self.assertEqual(report['decision'], 'NO_MANA_PAYMENT_EXCEPTION')
        report = self.assess(traits={'loyalty_symbol_in_cost':'NO','source_is_planeswalker':'YES'})
        self.assertEqual(report['decision'], 'PAYMENT_TIMING_EXCEPTION_APPLIES')

    def test_each_explicit_exclusion(self):
        for key,value in (('potential_mana','NO'),('cost_library_movement','YES'),('effect_library_movement','YES')):
            with self.subTest(key=key):
                self.setUp()
                self.assertEqual(self.assess(traits={key:value})['decision'], 'NO_MANA_PAYMENT_EXCEPTION')

    def test_current_zero_output_does_not_remove_classification(self):
        zero = self.assess(state={'current_mana_output':'ZERO'})
        nonzero = self.assess(state={'current_mana_output':'NONZERO'})
        self.assertEqual(zero['classification'], nonzero['classification'])
        self.assertEqual(zero['decision'], nonzero['decision'])
        self.assertEqual(self.assess(traits={'potential_mana':'NO'})['decision'], 'NO_MANA_PAYMENT_EXCEPTION')

    def test_other_replacements_are_ignored_for_classification_only(self):
        for kind in ('PRESENT','UNKNOWN'):
            self.assertEqual(self.assess(traits={'other_replacement':kind})['decision'],
                             'PAYMENT_TIMING_EXCEPTION_APPLIES')

    def test_self_replacement_requires_unsupported_application(self):
        self.value['characteristics']['self_replacement'] = 'PRESENT'
        self.refused('UNSUPPORTED_SELF_REPLACEMENT', lambda:self.consumer.assess(self.value))

    def test_unknown_self_replacement_prevents_affirmative_classification(self):
        report = self.assess(traits={'self_replacement':'UNKNOWN','potential_mana':'NO'})
        self.assertEqual(report['decision'], 'NEEDS_FACTS')
        self.assertIn('self_replacement_assessment', report['missing_facts'])

    def test_same_ability_restriction_negative_even_with_payment_opportunity(self):
        report = self.assess(state={'same_ability_unresolved':'YES'})
        self.assertEqual(report['decision'], 'SAME_ABILITY_REACTIVATION_PROHIBITED')
        finding = next(x for x in report['opportunity_findings'] if x['key']=='repeat')
        self.assertTrue(finding['consequence_established'])

    def test_missing_facts_preserved(self):
        report = self.assess(state={'same_ability_unresolved':'UNKNOWN','mana_payment_request':'UNKNOWN'})
        self.assertEqual(report['decision'], 'NEEDS_FACTS')
        self.assertEqual(report['missing_facts'], ['mana_payment_request','same_ability_unresolved'])
        report = self.assess(traits={'ability_kind':'UNKNOWN'})
        self.assertIn('activated_kind', report['missing_facts'])

    def test_known_absent_request_can_answer_despite_unknown_repeat(self):
        report = self.assess(state={'mana_payment_request':'ABSENT','same_ability_unresolved':'UNKNOWN'})
        self.assertEqual(report['decision'], 'NO_DECLARED_MANA_PAYMENT_OPPORTUNITY')

    def test_conflicting_target_declarations_refused(self):
        self.value['characteristics']['chosen_targets'] = 1
        self.refused('CONFLICTING_FACTS', lambda:self.consumer.assess(self.value))

    def test_triggered_and_spell_questions_not_promoted(self):
        for kind in ('TRIGGERED','SPELL'):
            self.value['characteristics']['ability_kind'] = kind
            self.refused('UNSUPPORTED_SCOPE', lambda:self.consumer.assess(self.value))

    def test_closed_input_rejects_permission_and_identity_assertions(self):
        for key in ('card_id','verified','owner_approval','source_policy_clearance'):
            value = deepcopy(self.value); value[key] = 'claimed'
            self.refused('INVALID_INPUT', lambda:self.consumer.assess(value))

    def test_invalid_types_bounds_and_missing_fields(self):
        for field, invalid in (('chosen_targets',True),('chosen_targets',-1),('chosen_targets',17),
                ('potential_mana',True),('ability_kind',None)):
            value=deepcopy(self.value); value['characteristics'][field]=invalid
            self.refused('INVALID_INPUT', lambda:self.consumer.assess(value))
        for value in ([], None, {'bad':1}, {**self.value,'scenario_id':'x'*9000}):
            self.refused('INVALID_INPUT', lambda:self.consumer.assess(value))
        value=deepcopy(self.value); del value['state']['priority']
        self.refused('INVALID_INPUT', lambda:self.consumer.assess(value))

    def test_versions_and_question_are_closed(self):
        self.value['schema_version']='v999'
        self.refused('UNSUPPORTED_VERSION',lambda:self.consumer.assess(self.value))
        self.setUp(); self.value['question']='CAST_THIS_CARD'
        self.refused('UNSUPPORTED_QUESTION',lambda:self.consumer.assess(self.value))

    def test_evidence_version_mismatch_at_factory_and_input(self):
        self.refused('EVIDENCE_VERSION_MISMATCH', lambda:r.load_rules_reasoner(
            review_root=ROOT/'reference-reviews',expected_context_id='sha256:wrong'))
        self.value['evidence_context_id']='sha256:wrong'
        self.refused('EVIDENCE_VERSION_MISMATCH',lambda:self.consumer.assess(self.value))

    def test_no_card_or_acquisition_reads(self):
        opened=[]; original=Path.open
        def metadata_only(path,*args,**kwargs):
            self.assertTrue(path.is_relative_to(ROOT/'reference-reviews'), str(path))
            opened.append(path)
            return original(path,*args,**kwargs)
        # A forbidden factory would fail even if it attempted no file reads.
        with patch('card_intelligence.semantic_closure.load_semantic_closure',side_effect=AssertionError('Card admission forbidden')), \
             patch('card_intelligence.mana_window.load_mana_window',side_effect=AssertionError('Card admission forbidden')), \
             patch.object(Path,'open',metadata_only):
            consumer=r.load_rules_reasoner(review_root=ROOT/'reference-reviews',expected_context_id=r.CONTEXT_ID)
            report=consumer.assess(self.value).to_dict()
        self.assertTrue(opened)
        self.assertTrue(all('scryfall' not in str(p).lower() for p in opened))
        self.assertEqual(report['authority']['source_policy_clearance'],'not_granted')
        self.assertEqual(set(report['authority']['permissions'].values()),{'NOT_ESTABLISHED'})

    def test_each_assessment_revalidates_metadata_tampering(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)/'reviews'; root.mkdir()
            from card_rules_pilot.land_context import PACKAGE_IDS
            names=set(PACKAGE_IDS)|{'gameplay-rules-artifact-verification',
                'gameplay-rules-source-versioning','gameplay-rules-release-discovery-closure'}
            for name in names:
                shutil.copytree(ROOT/'reference-reviews'/name,root/name)
            consumer=r.load_rules_reasoner(review_root=root,expected_context_id=r.CONTEXT_ID)
            path=root/'gameplay-rules-bounded-mana-ability-projection/projection.json'
            path.write_bytes(path.read_bytes()+b' ')
            self.refused('EVIDENCE_INTEGRITY',lambda:consumer.assess(self.value))

    def test_hashes_are_not_semantic_acceptance_or_execution_approval(self):
        report=self.assess()
        refs=report['evidence']['references']
        self.assertEqual({x['reference'] for x in refs},set(r.REFERENCES))
        self.assertTrue(all(x['rule_id'].startswith('sha256:') and x['package_id'].startswith('sha256:') for x in refs))
        self.assertEqual(refs[0]['historical_review_state'],'PROJECTED_FOR_REVIEW')
        self.assertFalse(report['evidence']['fresh_source_verification'])
        self.assertFalse(report['evidence']['historical_review_states_changed'])
        self.assertFalse(report['authority']['real_card_verified'])
        self.assertFalse(report['authority']['canonical_admission'])

    def test_replay_immutable_deterministic_and_tamper_detection(self):
        before=deepcopy(self.value)
        first=self.consumer.assess(self.value)
        self.assertEqual(self.value,before)
        self.assertEqual(first.to_json(),self.consumer.assess(self.value).to_json())
        self.assertEqual(first.to_json(),self.consumer.replay(first.to_json().encode()).to_json())
        decoded=first.to_dict();decoded['decision']='forged'
        self.assertNotEqual(decoded,first.to_dict())
        forged=c.seal(r.VERSION,decoded,'report_id')
        self.refused('INVALID_REPORT',lambda:self.consumer.validate_report(forged))
        changed=first.to_dict(); changed['input']['state']['mana_payment_request']='ABSENT'
        self.refused('INVALID_REPORT',lambda:self.consumer.validate_report(c.seal(r.VERSION,changed,'report_id')))
        self.refused('INVALID_REPORT',lambda:self.consumer.replay(b'{"duplicate":1,"duplicate":2}\n'))

    def test_cli_api_and_readable_parity(self):
        command=[sys.executable,'-m','card_intelligence.rules_reasoning','--review-root',str(ROOT/'reference-reviews'),
                 '--expected-context-id',r.CONTEXT_ID]
        result=subprocess.run(command+['--json','assess',str(FIXTURE)],capture_output=True,check=True)
        self.assertEqual(result.stdout,self.consumer.assess(self.value).to_json().encode())
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'report.json';path.write_bytes(result.stdout)
            replay=subprocess.run(command+['--json','validate',str(path)],capture_output=True,check=True)
            self.assertEqual(result.stdout,replay.stdout)
        text=subprocess.run(command+['assess',str(FIXTURE)],capture_output=True,check=True).stdout.decode()
        self.assertEqual(text,r.render_reasoning(self.consumer.assess(self.value)))
        self.assertIn('NOT_ESTABLISHED',text)
        self.assertIn('NOT_ASSESSED',text)

    def test_cli_structured_refusal(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'input.json';self.value['characteristics']['chosen_targets']=2
            path.write_bytes(c.canonical(self.value))
            result=subprocess.run([sys.executable,'-m','card_intelligence.rules_reasoning','--review-root',
                str(ROOT/'reference-reviews'),'--expected-context-id',r.CONTEXT_ID,'assess',str(path)],capture_output=True)
            self.assertEqual(result.returncode,2)
            self.assertEqual(result.stdout,b'')
            self.assertEqual(json.loads(result.stderr)['code'],'CONFLICTING_FACTS')

    def test_schema_and_document_links(self):
        import re
        import jsonschema
        schema=json.loads((ROOT/'src/schemas/v1/real-card-rules-reasoning-input.schema.json').read_bytes())
        jsonschema.Draft202012Validator.check_schema(schema)
        jsonschema.validate(self.value,schema)
        with self.assertRaises(jsonschema.ValidationError):
            jsonschema.validate({**self.value,'approval':True},schema)
        doc=ROOT/'docs/REAL_CARD_RULES_REASONING_V1.md'
        for target in re.findall(r'\[[^\]]+\]\(([^\s)]+)\)',doc.read_text()):
            self.assertTrue((doc.parent/target).is_file(),target)


if __name__=='__main__':unittest.main()
