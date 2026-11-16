"""Actual retained admission and explicitly synthetic hypothetical applicability."""
from copy import deepcopy
from dataclasses import FrozenInstanceError
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from card_intelligence import mana_window as m, semantic_closure as closure
from card_rules_pilot import contract as c
from land_test_support import ROOT, current_catalog_intact
from test_land_decision import decision_arguments

FIX = ROOT/'tests/fixtures/mana_window_v1'


def context(**kwargs):
    return m.hypothetical_context(**kwargs)


def statuses(doc):
    return {r['key']:r['status'] for r in doc.to_dict()['findings']}


class WindowPolicyTests(unittest.TestCase):
    def test_strict_closed_context_types_versions_and_bounds(self):
        for key in m.FIELDS:
            for value in (None,True,0,[],{},'foreign'):
                with self.subTest(key=key,value=value),self.assertRaises(ValueError):context(**{key:value})
        for changes in ({'schema_version':'foreign'},{'card_name':'Snow-Covered Wastes'},
                        {'permission':'APPROVED'},{'priority_opportunity':'x'*5000}):
            with self.assertRaises(ValueError):context(**changes)
        with self.assertRaises(ValueError):m._context({})

    def test_unknown_defaults_never_manufacture_payment_or_priority(self):
        v=context();self.assertEqual(v['payment_opportunity'],'UNKNOWN')
        self.assertEqual(v['priority_opportunity'],'UNKNOWN')
        self.assertNotEqual(v,context(payment_opportunity='ABSENT'))

    def test_generic_synthetic_proposition_uses_terms_not_card_or_rule_labels(self):
        prop=dict(key='imaginary',rule_reference='SYNTHETIC_NOT_CR',rule_id='SYNTHETIC_ONLY',
            conditions=[dict(field='priority_opportunity',allowed=['YES'])],conditional_consequence='Synthetic condition only.')
        out=m.evaluate_propositions([prop],context(priority_opportunity='YES'))
        self.assertEqual(out['findings'][0]['status'],'APPLICABLE')
        self.assertEqual(out['execution_authority'],'BLOCKED')
        self.assertEqual(out['legal_activation'],'NOT_ESTABLISHED')
        prop['key']='renamed';prop['rule_reference']='OTHER_SYNTHETIC_LABEL'
        self.assertEqual(m.evaluate_propositions([prop],context(priority_opportunity='YES'))['findings'][0]['status'],'APPLICABLE')

    def test_generic_conjunction_false_unknown_unsupported_and_conflict(self):
        prop=dict(key='imaginary',rule_reference='SYNTHETIC',rule_id='SYNTHETIC',
            conditions=[dict(field='classification',allowed=['ACTIVATED_MANA']),dict(field='priority_opportunity',allowed=['YES'])],
            conditional_consequence='No real-rule claim.')
        for changes,expected in (({},'UNKNOWN'),({'classification':'ACTIVATED_NONMANA'},'INAPPLICABLE'),
                ({'classification':'UNSUPPORTED'},'UNSUPPORTED'),({'classification':'ACTIVATED_MANA','priority_opportunity':'YES'},'APPLICABLE'),
                ({'classification':'ACTIVATED_MANA','stack_use':'YES'},'CONFLICTING')):
            with self.subTest(changes=changes):
                self.assertEqual(m.evaluate_propositions([prop],context(**changes))['findings'][0]['status'],expected)

    def test_malformed_duplicate_and_unbounded_propositions_reject(self):
        prop=dict(key='x',rule_reference='SYNTHETIC',rule_id='SYNTHETIC',conditions=[dict(field='priority_opportunity',allowed=['YES'])],conditional_consequence='Synthetic.')
        for props in (None,[],[False],[prop,prop],[prop]*17,[dict(prop,extra=True)],
                      [dict(prop,conditions=[dict(field='unknown',allowed=['YES'])])],
                      [dict(prop,conditions=[dict(field='priority_opportunity',allowed=['UNKNOWN'])])],
                      [dict(prop,conditions=prop['conditions']*2)]):
            with self.subTest(props=str(props)[:50]),self.assertRaises(ValueError):m.evaluate_propositions(props,context())

    def test_policy_inputs_and_outputs_are_independent(self):
        prop=dict(key='x',rule_reference='SYNTHETIC',rule_id='SYNTHETIC',conditions=[dict(field='priority_opportunity',allowed=['YES'])],conditional_consequence='Synthetic.')
        ctx=context(priority_opportunity='YES');out=m.evaluate_propositions([prop],ctx);before=deepcopy(out)
        ctx['priority_opportunity']='NO';prop['conditions'].clear();self.assertEqual(out,before)


class RetainedManaWindowTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.intact=current_catalog_intact(cls())
        if cls.intact:cls.consumer=m.load_mana_window(**decision_arguments())

    def live(self):
        if self.intact:return True
        with self.assertRaises(m.WindowError) as error:m.load_mana_window(**decision_arguments())
        self.assertEqual(error.exception.code,'EVIDENCE_ADMISSION_REJECTED')
        return False

    def assess(self,**kwargs):return self.consumer.assess(context(**kwargs))

    def test_exact_four_rule_identities_source_anchors_projection_and_reviews(self):
        if not self.live():return
        report=self.consumer.check().to_dict();evidence=self.consumer.detailed(report['detailed_reference']).to_dict()
        self.assertEqual({r['reference']:r['rule_id'] for r in report['references']},dict(m.RULE_IDS))
        self.assertEqual(evidence['context_id'],closure.CONTEXT_ID)
        self.assertEqual(len(evidence['rules']),4);self.assertEqual(len(evidence['dependency_reviews']),4)
        for row in evidence['rules']:
            self.assertTrue(row['projection_id'].startswith('sha256:'));self.assertTrue(row['package_id'].startswith('sha256:'))
            a=row['rule']['source_anchor'];self.assertEqual(a['effective_date'],'2026-09-25')
            self.assertLess(a['byte_start'],a['byte_end']);self.assertTrue(a['span_sha256'].startswith('sha256:'))
        self.assertIn('NOT_EXECUTABLE_APPROVAL',evidence['review_scope'])

    def test_priority_opportunity_does_not_invent_payment(self):
        if not self.live():return
        states=statuses(self.assess(classification='ACTIVATED_MANA',priority_opportunity='YES'))
        self.assertEqual(states['ordinary-priority-opportunity'],'APPLICABLE')
        self.assertEqual(states['mana-payment-opportunity'],'UNKNOWN')

    def test_each_explicit_payment_category_without_ordinary_priority(self):
        if not self.live():return
        for payment in m.FIELDS['payment_opportunity'][1:5]:
            with self.subTest(payment=payment):
                states=statuses(self.assess(classification='ACTIVATED_MANA',priority_opportunity='NO',payment_opportunity=payment))
                self.assertEqual(states['ordinary-priority-opportunity'],'INAPPLICABLE')
                self.assertEqual(states['mana-payment-opportunity'],'APPLICABLE')

    def test_known_false_conditions_do_not_grant_opposite_permission(self):
        if not self.live():return
        doc=self.assess(classification='ACTIVATED_NONMANA',priority_opportunity='YES');self.assertEqual(set(statuses(doc).values()),{'INAPPLICABLE'})
        self.assertEqual(doc.to_dict()['legal_activation'],'NOT_ESTABLISHED')
        self.assertIn('no opposite permission',' '.join(doc.to_dict()['limitations']))

    def test_unknown_classification_and_payment_remain_unknown(self):
        if not self.live():return
        self.assertEqual(set(statuses(self.consumer.check()).values()),{'UNKNOWN'})
        self.assertEqual(statuses(self.assess(classification='ACTIVATED_MANA'))['mana-payment-opportunity'],'UNKNOWN')
        self.assertEqual(statuses(self.assess(classification='ACTIVATED_MANA',payment_opportunity='ABSENT'))['mana-payment-opportunity'],'INAPPLICABLE')

    def test_unsupported_triggered_and_unknown_mechanics_fail_closed(self):
        if not self.live():return
        for classification in ('TRIGGERED_MANA','UNSUPPORTED'):
            self.assertEqual(set(statuses(self.assess(classification=classification)).values()),{'UNSUPPORTED'})
        self.assertEqual(statuses(self.assess(classification='ACTIVATED_MANA',payment_opportunity='UNSUPPORTED'))['mana-payment-opportunity'],'UNSUPPORTED')

    def test_stack_conflict_preserves_both_assertions(self):
        if not self.live():return
        doc=self.assess(classification='ACTIVATED_MANA',stack_use='YES');v=doc.to_dict()
        self.assertEqual(set(statuses(doc).values()),{'CONFLICTING'})
        self.assertEqual(v['context']['stack_use'],'YES');self.assertEqual(v['context']['classification'],'ACTIVATED_MANA')
        self.assertTrue(all(not r['consequence_established'] for r in v['findings']))

    def test_progress_conflict_is_not_silently_repaired(self):
        if not self.live():return
        doc=self.assess(classification='ACTIVATED_MANA',same_ability_unresolved='YES',activation_resolved='YES')
        self.assertEqual(set(statuses(doc).values()),{'CONFLICTING'})

    def test_no_stack_exception_is_conditional_not_an_executed_transition(self):
        if not self.live():return
        doc=self.assess(classification='ACTIVATED_MANA');v=doc.to_dict()
        self.assertEqual(statuses(doc)['no-stack-immediate-resolution'],'APPLICABLE')
        self.assertEqual(v['legal_activation'],'NOT_ESTABLISHED');self.assertNotIn('next_state',v)
        self.assertNotIn('game_state',v);self.assertEqual(v['assumptions_authority'],'CALLER_SUPPLIED_HYPOTHETICAL_NOT_OBSERVED_OR_VERIFIED')

    def test_repeat_restriction_changes_only_with_explicit_same_ability_progress(self):
        if not self.live():return
        for progress,status in (('YES','APPLICABLE'),('NO','INAPPLICABLE'),('UNKNOWN','UNKNOWN')):
            self.assertEqual(statuses(self.assess(classification='ACTIVATED_MANA',same_ability_unresolved=progress))['same-ability-repeat-restriction'],status)

    def test_priority_return_needs_both_pre_activation_holder_and_resolution(self):
        if not self.live():return
        for held,resolved,status in (('YES','YES','APPLICABLE'),('NO','YES','INAPPLICABLE'),('YES','NO','INAPPLICABLE'),('UNKNOWN','YES','UNKNOWN')):
            doc=self.assess(classification='ACTIVATED_MANA',held_priority_before_activation=held,activation_resolved=resolved)
            self.assertEqual(statuses(doc)['post-resolution-priority-return'],status)

    def test_general_priority_payment_and_permission_absence_is_explicit(self):
        if not self.live():return
        v=self.assess(classification='ACTIVATED_MANA',priority_opportunity='YES').to_dict()
        self.assertIn('General priority',v['missing_dependencies'][0]);self.assertFalse(v['canonical_admission'])
        self.assertEqual(set(v['permissions'].values()),{'NOT_ESTABLISHED'})
        self.assertEqual(v['source_policy_clearance'],'not_granted');self.assertEqual(v['execution_authority'],'BLOCKED')

    def test_determinism_private_ownership_and_detached_views(self):
        if not self.live():return
        ctx=context(classification='ACTIVATED_MANA');a=self.consumer.assess(ctx);raw=a.to_json()
        a.to_dict()['findings'].clear();ctx['classification']='UNSUPPORTED'
        self.assertEqual(self.assess(classification='ACTIVATED_MANA').to_json(),raw)
        with self.assertRaises(FrozenInstanceError):self.consumer._evidence=b'{}'

    def test_coherent_report_rule_anchor_citation_and_permission_tampering_rejects(self):
        if not self.live():return
        for kind in ('rule','anchor','citation','status','legal','permission','extra'):
            v=self.consumer.check().to_dict()
            if kind=='rule':v['references'][0]['rule_id']='sha256:'+'0'*64
            elif kind=='anchor':v['references'][0]['source_anchor']['byte_start']+=1
            elif kind=='citation':v['findings'][0]['rule_reference']='invented'
            elif kind=='status':v['findings'][0]['status']='APPLICABLE'
            elif kind=='legal':v['legal_activation']='APPROVED'
            elif kind=='permission':v['permissions']['private_retention']='ESTABLISHED'
            else:v['ready']=True
            v=c.seal(m.VERSION,v,'report_id')
            with self.subTest(kind=kind),self.assertRaises(ValueError):self.consumer.validate_report(v)

    def test_expected_context_binding_rejects_a_different_valid_hypothesis(self):
        if not self.live():return
        a=context(classification='ACTIVATED_MANA');b=context(classification='ACTIVATED_NONMANA')
        with self.assertRaises(ValueError):self.consumer.validate_report(self.consumer.assess(b).to_dict(),expected_context=a)
        self.assertEqual(self.consumer.validate_report(self.consumer.assess(a).to_dict(),expected_context=a).to_json(),self.consumer.assess(a).to_json())

    def test_duplicate_json_keys_types_and_report_bounds_reject(self):
        if not self.live():return
        raw=self.consumer.check().to_json().encode();self.assertEqual(self.consumer.parse_report(raw).to_json().encode(),raw)
        for bad in (raw.replace(b'"policy_id":',b'"policy_id":null,"policy_id":',1),raw+b' ',b'x'*32769,b'{"x":NaN}\n'):
            with self.assertRaises(ValueError):self.consumer.parse_report(bad)

    def test_detailed_evidence_route_checks_full_exact_reference(self):
        if not self.live():return
        ref=self.consumer.check().to_dict()['detailed_reference'];doc=self.consumer.detailed(ref)
        self.assertEqual(hashlib.sha256(doc.to_json().encode()).hexdigest(),ref['sha256'])
        bad=dict(ref,sha256='0'*64)
        with self.assertRaises(ValueError):self.consumer.detailed(bad)
        history=self.consumer.detailed(doc.to_dict()['historical_reference']);self.assertEqual(len(history.to_json().encode()),689253)

    def test_actual_rehashed_source_evidence_is_not_authorized(self):
        if not self.live():return
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)/'reviews';shutil.copytree(ROOT/'reference-reviews',root)
            p=root/'gameplay-rules-bounded-mana-ability-projection';f=p/'projection.json';v=c.read_json(f,limit=524288)
            v['rules'][0]['source_anchor']['span_sha256']='sha256:'+'0'*64
            v=c.seal(v['schema_version'],v,'projection_id');raw=c.canonical(v);f.write_bytes(raw)
            f=p/'manifest.json';mfest=c.read_json(f,limit=524288);mfest['record_ids']['projection.json']=v['projection_id']
            mfest['files']['projection.json']=dict(bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest());f.write_bytes(c.canonical(c.seal(mfest['schema_version'],mfest,'package_id')))
            with self.assertRaises(m.WindowError):m.load_mana_window(**decision_arguments(review_root=root))

    def test_fresh_public_load_rejects_changed_or_missing_owner_evidence(self):
        if not self.live():return
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(m.WindowError):m.load_mana_window(**decision_arguments(decision_root=Path(d)))
        with patch.object(m.closure,'load_semantic_closure',side_effect=ValueError('missing evidence')) as load:
            with self.assertRaises(m.WindowError):m.load_mana_window(**decision_arguments())
            self.assertEqual(load.call_count,1)

    def test_existing_closure_report_and_no_execution_remain_exact(self):
        if not self.live():return
        original=(ROOT/'tests/fixtures/semantic_closure_v1/report.json').read_bytes()
        paths=[ROOT/'src/gameplay_rules/models.py',ROOT/'src/gameplay_rules/engine.py',ROOT/'data/review/land-semantic-decisions/owner-acceptance-v1.json']
        before=[p.read_bytes() for p in paths]
        with patch('gameplay_rules.engine.GameplayRulesEngine.apply_action',side_effect=AssertionError('No execution')):
            self.consumer.check();self.assertEqual(self.consumer._closure.check().to_json().encode(),original)
        self.assertEqual(before,[p.read_bytes() for p in paths]);v=json.loads(original)
        self.assertEqual(len(v['requirements']),23);self.assertEqual(v['report_id'],'sha256:bf3c12d0f87975d9cee608c4c3ac05ecd38a9b236ceeec0df2eb6d18ab46ada9')

    def test_readable_canonical_sizes_and_golden_parity(self):
        if not self.live():return
        doc=self.consumer.check();self.assertEqual(doc.to_json().encode(),(FIX/'report.json').read_bytes())
        text=m.render_window(doc);self.assertEqual(text,(FIX/'report.txt').read_text())
        self.assertLessEqual(len(doc.to_json().encode()),m.LIMIT);self.assertLessEqual(len(text.encode()),m.READABLE_LIMIT)
        self.assertNotIn('"assessments":',text)

    def test_actual_public_cli_read_only_serialization(self):
        if not self.live():return
        args=[]
        for k,v in decision_arguments().items():args+=['--'+k.replace('_','-'),str(v)]
        prefix=[sys.executable,'-B','-m','card_intelligence.mana_window',*args]
        result=subprocess.run(prefix+['--json','check'],cwd=ROOT,capture_output=True,check=True)
        self.assertEqual(result.stdout,self.consumer.check().to_json().encode())
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'context.json';p.write_bytes(c.canonical(context(classification='ACTIVATED_MANA',priority_opportunity='YES')))
            result=subprocess.run(prefix+['assess',str(p)],cwd=ROOT,capture_output=True,check=True)
            self.assertEqual(result.stdout,m.render_window(self.assess(classification='ACTIVATED_MANA',priority_opportunity='YES')).encode())
            p.write_bytes(c.canonical(dict(context(),approved=True)))
            bad=subprocess.run(prefix+['--json','assess',str(p)],cwd=ROOT,capture_output=True)
            self.assertEqual(bad.returncode,2);self.assertEqual(bad.stdout,b'')


class WindowPreservationTests(unittest.TestCase):
    def test_addition_tampering_and_executable_mode_fail_closed(self):
        import mana_window_preservation as guard
        name=next(iter(guard.ADDITIONS))
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);p=root/name;p.parent.mkdir(parents=True);raw=(ROOT/name).read_bytes();p.write_bytes(raw)
            self.assertTrue(guard.is_addition(p,root));p.write_bytes(raw+b'\n# altered')
            with self.assertRaises(AssertionError):guard.is_addition(p,root)
            p.write_bytes(raw);p.chmod(0o744)
            with self.assertRaises(AssertionError):guard.is_addition(p,root)

    def test_exact_addition_and_historical_helper_pins(self):
        import mana_window_preservation as guard
        self.assertEqual(len(guard.ADDITIONS),1)
        for name in guard.ADDITIONS:self.assertTrue(guard.is_addition(ROOT/name,ROOT))
        self.assertFalse(guard.is_addition(ROOT/'src/card_intelligence/future.py',ROOT))
        for name in guard.REPLACEMENTS:
            pin=guard.ledger()['replacements'][name];raw=(ROOT/name).read_bytes()
            self.assertEqual(hashlib.sha256(guard.preceding_bytes(name,raw)).hexdigest(),pin['old_sha256'])
            with self.assertRaises(AssertionError):guard.preceding_bytes(name,raw+b'# tampered')
