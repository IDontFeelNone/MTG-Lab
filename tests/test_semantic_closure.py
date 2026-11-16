"""Actual admitted pilot plus explicitly synthetic pure-policy adversarial graphs."""
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

from card_intelligence import semantic_closure as s, semantic_closure_policy as p
from card_rules_pilot import contract as c, land_decision as d
from land_test_support import ROOT, current_catalog_intact
from test_land_decision import decision_arguments

FIX = ROOT/'tests/fixtures/semantic_closure_v1'


def synthetic():
    """Fictional input, neither a reviewed Card nor authenticated evidence."""
    row=dict(key='imaginary.output',dimension='semantics',question='Known imaginary output?',
        why='Synthetic reuse demonstration.',needed='Explicit hypothetical premise.',premise='sample',
        required_level='accepted_interpretation',dependencies=[])
    fact=dict(key='sample',state='ESTABLISHED',level='accepted_interpretation',evidence_refs=['synthetic'])
    evidence={'synthetic':dict(identity=c.identity('synthetic-closure-example',{'example':'not-a-real-card'},'id'),
        pointer='/assertion',scope='SYNTHETIC_ONLY_NOT_ADMITTED')}
    return [row],[fact],evidence


class GenericClosurePolicyTests(unittest.TestCase):
    def test_synthetic_alternative_subject_is_not_real_acceptance_or_execution(self):
        a,b,e=synthetic();out=p.evaluate(a,b,e)
        self.assertEqual(out['status'],'SATISFIED')
        self.assertEqual(out['execution_authority'],'BLOCKED')
        self.assertEqual(out['authority'],'PURE_REQUIREMENT_EVALUATION_NOT_EVIDENCE_ADMISSION')
        b[0]['state']='UNKNOWN';self.assertEqual(p.evaluate(a,b,e)['status'],'UNKNOWN')

    def test_policy_uses_evidence_levels_not_card_names_or_source_presence(self):
        a,b,e=synthetic();b[0]['level']='retained_source'
        out=p.evaluate(a,b,e);self.assertEqual(out['status'],'UNKNOWN')
        self.assertEqual(out['requirements'][0]['reason'],'INSUFFICIENT_AUTHORITY_LEVEL')
        a[0]['key']='another-label';self.assertEqual(p.evaluate(a,b,e)['status'],'UNKNOWN')
        with self.assertRaises(p.ClosureError):p.evaluate(a,[dict(b[0],card_name='Snow-Covered Wastes')],e)
        self.assertNotIn(s.CARD_ID,p.policy_document().to_json())
        self.assertNotIn('Snow-Covered Wastes',p.policy_document().to_json())

    def test_missing_unknown_unsupported_conflicting_and_blocked_are_distinct(self):
        a,b,e=synthetic();self.assertEqual(p.evaluate(a,[],e)['status'],'MISSING')
        for state,status in [('ABSENT','MISSING'),('UNKNOWN','UNKNOWN'),('UNSUPPORTED','UNSUPPORTED'),
                             ('PROHIBITED','BLOCKED'),('CONFLICTING','BLOCKED')]:
            with self.subTest(state=state):
                b[0]['state']=state;self.assertEqual(p.evaluate(a,b,e)['status'],status)

    def test_dependency_precedence_preserves_local_status_and_determinism(self):
        a,b,e=synthetic();a.append(dict(a[0],key='imaginary.use',dependencies=['imaginary.output']))
        b[0]['state']='ABSENT';a[1]['premise']='other';b.append(dict(b[0],key='other',state='ESTABLISHED'))
        out=p.evaluate(a,b,e);row=out['requirements'][1]
        self.assertEqual(row['local_status'],'SATISFIED');self.assertEqual(row['status'],'MISSING')
        self.assertEqual(out,p.evaluate(list(reversed(a)),list(reversed(b)),e))
        b[0]['state']='PROHIBITED';self.assertEqual(p.evaluate(a,b,e)['status'],'BLOCKED')

    def test_cycles_missing_dependencies_and_duplicate_requirements_reject(self):
        a,b,e=synthetic()
        for deps in (['imaginary.output'],['foreign']):
            with self.subTest(deps=deps),self.assertRaises(p.ClosureError):p.evaluate([dict(a[0],dependencies=deps)],b,e)
        with self.assertRaises(p.ClosureError):p.evaluate(a+a,b,e)
        with self.assertRaises(p.ClosureError):p.evaluate(a,b+b,e)

    def test_invented_citations_missing_evidence_and_wrong_identity_types_reject(self):
        a,b,e=synthetic()
        for refs in (['rule:invented'],[],None,'synthetic',[1]):
            with self.subTest(refs=refs),self.assertRaises(ValueError):p.evaluate(a,[dict(b[0],evidence_refs=refs)],e)
        for identity in ('sha256:bad',None,False,17):
            bad=deepcopy(e);bad['synthetic']['identity']=identity
            with self.subTest(identity=identity),self.assertRaises(ValueError):p.evaluate(a,b,bad)

    def test_closed_strict_types_and_finite_graph_bounds(self):
        a,b,e=synthetic()
        for bad in (None,False,{},'a',[False],a*65):
            with self.subTest(bad=str(bad)[:30]),self.assertRaises(ValueError):p.evaluate(bad,b,e)
        with self.assertRaises(ValueError):p.evaluate([dict(a[0],confidence=1)],b,e)
        with self.assertRaises(ValueError):p.evaluate(a,[dict(b[0],state=True)],e)
        with self.assertRaises(ValueError):p.evaluate(a,[dict(b[0],state=0.0)],e)

    def test_pure_calculation_detaches_inputs_and_policy_documents(self):
        a,b,e=synthetic();out=p.evaluate(a,b,e);original=deepcopy(out)
        a[0]['dependencies'].append('foreign');b[0]['evidence_refs'].clear();e.clear()
        self.assertEqual(out,original)
        doc=p.policy_document();doc.to_dict()['requirements'].clear()
        self.assertTrue(p.policy_document().to_dict()['requirements'])


class RealCardSemanticClosureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.intact=current_catalog_intact(cls())
        if cls.intact:cls.consumer=s.load_semantic_closure(**decision_arguments())

    def live(self):
        if self.intact:return True
        # The real 654-card nested writer changes the attached query. Require
        # actual rejection, never an old positive fixture or a new inherited skip.
        with self.assertRaises(s.ClosureError) as caught:s.load_semantic_closure(**decision_arguments())
        self.assertEqual(caught.exception.code,'EVIDENCE_ADMISSION_REJECTED')
        return False

    def report(self):return self.consumer.assess(s.overlay_api.CARD_NAMESPACE,s.CARD_ID,s.SUBJECT_ID).to_dict()

    def test_actual_subject_candidate_decision_and_exact_identity_joins(self):
        if not self.live():return
        v=self.report();self.assertEqual(v['input']['candidate_id'],s.CANDIDATE_ID)
        self.assertEqual(v['input']['decision_id'],d.DECISION_ID)
        self.assertEqual(v['identity']['card_id'],s.CARD_ID)
        joins=v['identity']['joins'];self.assertEqual(joins['historical_correspondence']['status'],'ESTABLISHED')
        self.assertEqual(joins['current_identifier_edge']['status'],'ESTABLISHED')
        self.assertEqual(joins['operator_production']['status'],'IDENTITY_NOT_ESTABLISHED')
        self.assertNotEqual(v['identity']['printing']['printing_id'],v['identity']['observation']['provider_record_id'])

    def test_historical_acceptance_is_not_oracle_freshness_or_observed_state(self):
        if not self.live():return
        v=self.report();rows={r['key']:r for r in v['requirements']}
        self.assertEqual(rows['text.accepted']['status'],'SATISFIED');self.assertEqual(rows['text.current']['status'],'UNKNOWN')
        self.assertEqual(v['text']['binding']['selected_passage'],'{T}: Add {C}.')
        self.assertEqual(v['text']['observation_timestamp'],'2026-08-02T09:09:45.851000Z')
        self.assertEqual(v['text']['retrieved_at'],'2026-08-02T15:34:06Z')
        self.assertEqual(v['accepted_semantics']['historical_status'],'PENDING_NOT_ESTABLISHED')
        self.assertEqual(v['accepted_semantics']['current_status'],'ACCEPTED_BOUNDED_RETAINED_TEXT')

    def test_retention_review_and_real_procedure_support_are_separate(self):
        if not self.live():return
        v=self.report();rows={r['key']:r for r in v['requirements']}
        for key in ('rules.retained','rules.reviewed'):self.assertEqual(rows[key]['status'],'SATISFIED')
        self.assertEqual(rows['rules.execution_review']['status'],'MISSING')
        self.assertTrue(v['rules']['dependency_reviews'])
        self.assertTrue(any(r['review_state']=='PROJECTED_FOR_REVIEW' for r in v['rules']['selected_support']))
        self.assertTrue(all(r['executable_review']=='NOT_ESTABLISHED' for r in v['rules']['selected_support']))

    def test_literal_missing_dependencies_and_required_procedures_are_exposed(self):
        if not self.live():return
        v=self.report();self.assertEqual({r['target'] for r in v['rules']['unresolved_frontiers']},{'733','701.20a'})
        self.assertTrue(all(r['retained_support']=='MISSING_IN_SELECTED_CONTEXT' and r['status']=='UNKNOWN'
                            for r in v['rules']['unresolved_frontiers']))
        rows={r['key']:r for r in v['requirements']}
        self.assertEqual(rows['rules.dependencies']['status'],'UNKNOWN')
        for key in ('procedure.activation','procedure.timing','procedure.cost',
                    'procedure.output','procedure.resolution','procedure.checkpoint','procedure.recovery'):
            self.assertEqual(rows[key]['status'],'MISSING')
        self.assertEqual(rows['procedure.external']['status'],'UNSUPPORTED')

    def test_permissions_semantic_closure_and_profile_authorization_remain_independent(self):
        if not self.live():return
        v=self.report();rows={r['key']:r for r in v['requirements']}
        self.assertEqual(rows['permissions.use']['status'],'UNKNOWN')
        self.assertEqual(rows['authorization.closure']['status'],'BLOCKED')
        self.assertEqual(rows['authorization.profile']['status'],'BLOCKED')
        self.assertEqual(set(v['authority']['permissions'].values()),{'NOT_ESTABLISHED'})
        self.assertFalse(v['authority']['canonical_admission']);self.assertIsNone(v['real_execution_profile_id'])
        self.assertEqual(v['authority']['semantic_closure'],'OPEN')
        self.assertEqual(v['disposition'],'BLOCKED_NON_EXECUTING_ASSESSMENT')

    def test_foreign_uuid_namespace_subject_and_name_only_requests_reject(self):
        if not self.live():return
        for namespace,card,subject in ((s.overlay_api.CARD_NAMESPACE,'Snow-Covered Wastes',s.SUBJECT_ID),
                (s.overlay_api.CARD_NAMESPACE,'foreign',s.SUBJECT_ID),('magic:mtgjson:printing',s.CARD_ID,s.SUBJECT_ID),
                (s.overlay_api.CARD_NAMESPACE,s.CARD_ID,'port-mana'),(None,s.CARD_ID,s.SUBJECT_ID)):
            with self.subTest(card=card,subject=subject),self.assertRaises(s.ClosureError):self.consumer.assess(namespace,card,subject)

    def test_coherently_rehashed_report_substitutions_and_authority_promotions_reject(self):
        if not self.live():return
        for key in ('card','candidate','decision','rule','citation','permission','profile','status','missing','extra','bool'):
            v=self.report()
            if key=='card':v['input']['card_id']='foreign'
            elif key=='candidate':v['input']['candidate_id']=dict(d.CANDIDATE_IDS)['port-mana']
            elif key=='decision':v['input']['decision_id']='sha256:'+'0'*64
            elif key=='rule':v['rules']['selected_support'][0]['rule_id']='sha256:'+'0'*64
            elif key=='citation':v['rules']['selected_support'][0]['reference']='invented'
            elif key=='permission':v['authority']['permissions']['private_retention']='ESTABLISHED'
            elif key=='profile':v['real_execution_profile_id']='fictional-two-player-stack-abilities-v1'
            elif key=='status':v['requirements'][0]['status']='SATISFIED'
            elif key=='missing':del v['rules']['unresolved_frontiers']
            elif key=='bool':v['authority']['canonical_admission']=0
            else:v['ready_for_execution']=True
            v=c.seal(s.VERSION,v,'report_id')
            with self.subTest(key=key),self.assertRaises(ValueError):self.consumer.validate_report(v)

    def test_canonical_duplicate_keys_wrong_types_and_bounds_reject(self):
        if not self.live():return
        raw=self.consumer.check().to_json().encode()
        self.assertEqual(self.consumer.parse_report(raw).to_dict(),self.report())
        for bad in (raw.replace(b'"scope":',b'"scope":null,"scope":',1),b' '*65537,raw+b' ',b'{"x":NaN}\n'):
            with self.subTest(size=len(bad)),self.assertRaises(ValueError):self.consumer.parse_report(bad)

    def test_owned_views_detach_and_repeated_assessment_is_deterministic(self):
        if not self.live():return
        doc=self.consumer.check();raw=doc.to_json();doc.to_dict()['requirements'].clear()
        self.assertEqual(self.consumer.check().to_json(),raw)
        self.assertEqual(self.consumer.validate_report(json.loads(raw)).to_json(),raw)
        with self.assertRaises(FrozenInstanceError):self.consumer._source=b'{}'

    def test_exact_evidence_pointers_resolve_in_their_admitted_documents(self):
        if not self.live():return
        v=self.report();docs=[self.consumer.detailed(v['detailed_references'][k]).to_dict() for k in ('overlay','historical')]
        by_id={doc['report_id']:doc for doc in docs}
        for ref in v['evidence'].values():
            value=by_id[ref['identity']]
            for key in ref['pointer'].split('/')[1:]:value=value[int(key)] if type(value) is list else value[key]
            self.assertIsNotNone(value)

    def test_detailed_routes_and_original_historical_report_remain_exact(self):
        if not self.live():return
        v=self.report();ref=v['detailed_references']['historical'];doc=self.consumer.detailed(ref)
        self.assertEqual(doc.to_dict()['report_id'],d.OVERVIEW_ID)
        self.assertEqual(len(doc.to_json().encode()),689253)
        self.assertEqual(hashlib.sha256(doc.to_json().encode()).hexdigest(),d.OVERVIEW_SHA256)
        for ref in v['detailed_references'].values():
            self.assertTrue(self.consumer.detailed(ref).to_dict())
            bad=deepcopy(ref);bad['sha256']='0'*64
            with self.assertRaises(ValueError):self.consumer.detailed(bad)

    def test_actual_no_real_execution_no_profile_promotion_and_no_mutation(self):
        if not self.live():return
        paths=[ROOT/'data/review/land-semantic-decisions/owner-acceptance-v1.json',
               ROOT/'data/review/land-mana-utility/interpretations.json',ROOT/'src/gameplay_rules/models.py']
        before=[x.read_bytes() for x in paths]
        with patch('gameplay_rules.engine.GameplayRulesEngine.apply_action',side_effect=AssertionError('No execution allowed')):
            self.consumer.validate_report(self.report())
        from gameplay_rules.models import STATE_SCHEMAS_BY_PROFILE
        self.assertTrue(all(k.startswith('fictional-') for k in STATE_SCHEMAS_BY_PROFILE))
        self.assertEqual(before,[x.read_bytes() for x in paths])

    def test_adapter_refuses_unsupported_behavior_and_inconsistent_admitted_premises(self):
        if not self.live():return
        v=self.report();source=self.consumer.detailed(v['detailed_references']['overlay']).to_dict()
        history=self.consumer.detailed(v['detailed_references']['historical']).to_dict()
        bad=deepcopy(source);bad['cards'][0]['subjects'][0]['explanation']['dimensions']['procedure']='invented'
        with self.assertRaisesRegex(s.ClosureError,'UNSUPPORTED_BEHAVIOR'):s._premises(bad,history)
        bad=deepcopy(source);bad['decision_id']='sha256:'+'0'*64
        with self.assertRaisesRegex(s.ClosureError,'EVIDENCE_BINDING'):s._premises(bad,history)

    def test_public_load_revalidates_actual_changed_owner_decision(self):
        if not self.live():return
        original=self.consumer.check().to_json()
        with tempfile.TemporaryDirectory() as directory:
            target=Path(directory)/'decision';shutil.copytree(ROOT/'data/review/land-semantic-decisions',target)
            file=target/'owner-acceptance-v1.json';value=c.read_json(file,limit=524288)
            value['authority']='FORGED_APPROVAL';value=c.seal(value['schema_version'],value,'decision_id');file.write_bytes(c.canonical(value))
            with self.assertRaises(s.ClosureError):s.load_semantic_closure(**decision_arguments(decision_root=target))
        self.assertEqual(self.consumer.check().to_json(),original)

    def test_coherently_rehashed_actual_rule_package_is_not_new_admission(self):
        if not self.live():return
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)/'reviews';shutil.copytree(ROOT/'reference-reviews',root)
            package=root/'gameplay-rules-bounded-mana-ability-projection'
            file=package/'projection.json';value=c.read_json(file,limit=524288)
            value['rules'][0]['source_anchor']['span_sha256']='sha256:'+'0'*64
            value=c.seal(value['schema_version'],value,'projection_id');raw=c.canonical(value);file.write_bytes(raw)
            file=package/'manifest.json';m=c.read_json(file,limit=524288)
            m['record_ids']['projection.json']=value['projection_id']
            m['files']['projection.json']=dict(bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest())
            file.write_bytes(c.canonical(c.seal(m['schema_version'],m,'package_id')))
            with self.assertRaises(s.ClosureError):s.load_semantic_closure(**decision_arguments(review_root=root))

    def test_missing_actual_evidence_fails_closed_and_public_batch_is_shared(self):
        if not self.live():return
        with patch.object(s.overlay_api,'load_land_overlay',side_effect=ValueError('missing source')) as load:
            with self.assertRaisesRegex(s.ClosureError,'EVIDENCE_ADMISSION_REJECTED'):s.load_semantic_closure(**decision_arguments())
            self.assertEqual(load.call_count,1)
        with patch.object(s.overlay_api,'load_land_overlay',side_effect=AssertionError('No reload per requirement')):
            self.assertTrue(self.consumer.check().to_dict()['requirements'])

    def test_missing_actual_owner_record_never_receives_partial_admission(self):
        if not self.live():return
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(s.ClosureError) as caught:
                s.load_semantic_closure(**decision_arguments(decision_root=Path(directory)))
            self.assertEqual(caught.exception.code,'EVIDENCE_ADMISSION_REJECTED')

    def test_canonical_readable_golden_and_compact_bounds(self):
        if not self.live():return
        doc=self.consumer.check();self.assertEqual(doc.to_dict(),c.read_json(FIX/'report.json',limit=s.REPORT_LIMIT))
        text=s.render_closure(doc);self.assertEqual(text,(FIX/'report.txt').read_text())
        self.assertLessEqual(len(doc.to_json().encode()),s.REPORT_LIMIT);self.assertLessEqual(len(text.encode()),s.READABLE_LIMIT)
        self.assertNotIn('"assessments":',text);self.assertNotIn('"context":',text)

    def test_actual_public_cli_serialization_and_read_only_behavior(self):
        if not self.live():return
        args=[]
        for k,v in decision_arguments().items():args+=['--'+k.replace('_','-'),str(v)]
        prefix=[sys.executable,'-B','-m','card_intelligence.semantic_closure',*args]
        canonical=subprocess.run(prefix+['--json','assess','--namespace',s.overlay_api.CARD_NAMESPACE,
            '--card-id',s.CARD_ID,'--subject-id',s.SUBJECT_ID],cwd=ROOT,capture_output=True,check=True)
        self.assertEqual(canonical.stdout,self.consumer.check().to_json().encode())
        readable=subprocess.run(prefix+['check'],cwd=ROOT,capture_output=True,check=True)
        self.assertEqual(readable.stdout,s.render_closure(self.consumer.check()).encode())
        bad=subprocess.run(prefix+['assess','--namespace',s.overlay_api.CARD_NAMESPACE,'--card-id','foreign',
            '--subject-id',s.SUBJECT_ID],cwd=ROOT,capture_output=True)
        self.assertEqual(bad.returncode,2);self.assertEqual(bad.stdout,b'')
        self.assertEqual(json.loads(bad.stderr)['code'],'UNSUPPORTED_SUBJECT')
