"""Actual public admission plus explicitly synthetic owner-supplied review examples."""
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

from card_rules_pilot import contract as c, land_decision as decision
from card_intelligence import context_review_input as inputs, context_review as api
from card_intelligence import strategic_requirements as requirements
from land_test_support import ROOT, current_catalog_intact
from test_land_decision import decision_arguments


def candidate(category='deck-composition', *, payload=None, version='v1', origin='Owner declaration',
              reference=None, content=None, refs=None, assertion='Explicit hypothetical review example.', **changes):
    data=dict(category=category,
        source=dict(type='owner-declaration',claimed_origin=origin,reference=reference,source_date=None,observation_date=None),
        scope=dict(deck_id='hypothetical-example',deck_version=version,kind='declared-hypothetical-deck'),
        assertion=assertion,payload=payload or dict(total_lands=36,claimed_swamps=20),content=content,requirement_refs=refs)
    data.update(changes)
    return inputs.make_candidate(**data).to_dict()


def packet(*rows): return inputs.make_packet(list(rows)).to_dict()


class SuppliedEvidenceInputTests(unittest.TestCase):
    def test_canonical_strict_fields_types_duplicate_keys_and_bounds(self):
        original=packet(candidate());self.assertEqual(inputs.parse_packet(c.canonical(original)).to_dict(),original)
        for value in ({},False,dict(original,verified=True),dict(original,namespace='printing'),dict(original,family='color-context')):
            with self.assertRaises(ValueError):inputs.validate_packet(value)
        for raw in (b'{}',b'{"x":1,"x":1}\n',b'{"x":NaN}\n',b' '*32769):
            with self.assertRaises(ValueError):inputs.parse_packet(raw)
        for count in (True,-1,1001,1.0,'5'):
            with self.assertRaises(ValueError):candidate(payload=dict(total_lands=36,claimed_swamps=count))
        for n in (0,1,5,1000):inputs.validate_candidate(candidate(payload=dict(total_lands=n,claimed_swamps=n)))
        with self.assertRaises(ValueError):candidate(payload=dict(total_lands=None,claimed_swamps=None))
        with self.assertRaises(ValueError):candidate(payload=dict(total_lands=36,claimed_swamps=20,observed_swamps=5))
        with self.assertRaises(ValueError):inputs.make_packet([candidate()]*2)
        with self.assertRaises(ValueError):inputs.make_packet([candidate(version=str(n)) for n in range(5)])

    def test_content_exact_utf8_digest_and_reference_only_separation(self):
        text='Owner-supplied fictional review note.\r\nSwamps: 20.\nπ'
        row=candidate(content=dict(mode='supplied-utf8',text=text,digest=None))
        self.assertEqual(row['content']['digest'],'sha256:'+hashlib.sha256(text.encode()).hexdigest())
        self.assertEqual(row['content']['text'],text)
        for body in (dict(mode='reference-only',text='absent?',digest=None),dict(mode='supplied-utf8',text='x'*1025,digest=None),
                     dict(mode='supplied-utf8',text='π'*513,digest=None),dict(mode='supplied-utf8',text='x',digest='sha256:'+'0'*64)):
            with self.assertRaises(ValueError):candidate(content=body)
        absent=candidate(reference='owner:lead',content=dict(mode='reference-only',text=None,digest='sha256:'+'a'*64))
        self.assertIsNone(absent['content']['text']);inputs.validate_candidate(absent)
        rows=[candidate(version=str(n),content=dict(mode='supplied-utf8',text='x'*1024,digest=None)) for n in range(5)]
        with self.assertRaises(ValueError):inputs.make_packet(rows)

    def test_source_dates_scope_permission_and_authentication_are_claims(self):
        row=candidate();row['source']['source_date']='2026-02-30'
        kwargs={k:row[k] for k in ('category','source','scope','assertion','payload')}
        with self.assertRaises(ValueError):inputs.make_candidate(**kwargs)
        kwargs['source']['source_date']='2024-02-29';doc=inputs.make_candidate(**kwargs);self.assertEqual(doc.to_dict()['source_authentication'],'NOT_ESTABLISHED')
        for change in ('source','permissions','scope','authority'):
            value=candidate()
            if change=='source':value['source']['authenticated']=True
            elif change=='scope':value['scope']['kind']='observed-battlefield'
            else:value[change]='GRANTED'
            value=c.seal(inputs.CANDIDATE_VERSION,value,'candidate_id')
            with self.assertRaises(ValueError):inputs.validate_candidate(value)
        row=candidate(claimed_use_restrictions='Owner claims private-review use only.')
        self.assertEqual(row['permissions'],'NOT_ESTABLISHED')

    def test_owned_schema_input_and_content_changes_have_distinct_identities(self):
        row=candidate();doc=inputs.make_packet([row]);old=doc.to_json();row['source']['claimed_origin']='changed'
        doc.to_dict()['candidates'].clear();self.assertEqual(doc.to_json(),old)
        self.assertNotEqual(candidate(assertion='A')['candidate_id'],candidate(assertion='B')['candidate_id'])
        self.assertEqual(inputs.schema_document().to_dict()['schema_id'],inputs.SCHEMA_ID)
        inputs.schema_document().to_dict()['rules'].clear();self.assertTrue(inputs.schema_document().to_dict()['rules'])
        with self.assertRaises(FrozenInstanceError):doc._raw=b'{}'


class ActualContextReviewTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.intact=current_catalog_intact(unittest.TestCase())
        if cls.intact:
            start=time.perf_counter();cls.owner=api.load_context_evidence_review(**decision_arguments());cls.load_seconds=time.perf_counter()-start

    def live(self):
        if self.intact:return True
        # The actual publication writer expanded this catalog; reject current
        # incompatible evidence rather than installing a positive fixture/skip.
        with self.assertRaises(api.ContextReviewError) as caught:api.load_context_evidence_review(**decision_arguments())
        self.assertEqual(caught.exception.code,'EVIDENCE_ADMISSION_REJECTED');return False

    def report(self,*rows):return self.owner.review(packet(*rows)).to_dict()

    def test_exact_two_cards_subjects_and_original_requirements(self):
        if not self.live():return
        value=self.report();self.assertEqual(value['family'],'variable-output')
        self.assertEqual(value['card_ids'],list(inputs.CARD_IDS));self.assertEqual(value['subject_ids'],list(inputs.SUBJECT_IDS))
        self.assertEqual({r['subject_id'] for r in value['capabilities']},set(inputs.SUBJECT_IDS))
        original=self.owner.detailed(value['requirements_reference']).to_dict()
        originals={r['requirement_id']:r for group in original['requirements'].values() for r in group}
        for r in value['requirements']:
            self.assertEqual(r['original_status'],originals[r['requirement_id']]['status'])
            self.assertEqual(r['support_refs'],originals[r['requirement_id']]['support_refs'])
        self.assertEqual(original['report_id'],'sha256:47b134c21c5a54087ed29e6c70b06a5591e60958f38e2db4c759d1bafb71cedd')
        self.assertFalse(value['review_boundary']['canonical_admission']);self.assertEqual(value['authority']['execution_authority'],'BLOCKED')

    def test_consistent_declared_deck_composition_is_not_controlled_swamps(self):
        if not self.live():return
        value=self.report(candidate());row=value['candidates'][0]
        self.assertEqual(row['review_states'],['SUBMITTED_UNVERIFIED','REQUIRES_REVIEW'])
        self.assertEqual(row['mappings'][0]['template_id'],'swamp-composition')
        self.assertFalse(any(m['requirement_promoted'] for m in row['mappings']))
        cap=next(v for v in value['capabilities'] if v['subject_id']=='coffers-mana')
        self.assertEqual(cap['hypothetical']['state'],'UNSPECIFIED');self.assertIsNone(cap['hypothetical']['conditional_written_output'])
        self.assertEqual(cap['written_cost'],'{2}, {T}')

    def test_cross_record_conflicts_preserve_each_assertion_without_preference(self):
        if not self.live():return
        a=candidate();b=candidate(payload=dict(total_lands=40,claimed_swamps=25))
        value=self.report(a,b);self.assertEqual(len(value['conflicts']),2)
        self.assertEqual({r['candidate']['candidate_id'] for r in value['candidates']},{a['candidate_id'],b['candidate_id']})
        self.assertTrue(all('CONFLICTING' in v['review_states'] for v in value['candidates']))
        self.assertTrue(all(v['resolution']=='UNRESOLVED_NO_PREFERRED_SOURCE' for v in value['conflicts']))
        self.assertEqual({v['field'] for v in value['conflicts']},{'total_lands','claimed_swamps'})

    def test_internal_inconsistency_quarantine_and_missing_count_not_zero(self):
        if not self.live():return
        bad=candidate(payload=dict(total_lands=20,claimed_swamps=30));item=self.report(bad)['candidates'][0]
        self.assertEqual(item['disposition'],'QUARANTINED');self.assertIn('INTERNALLY_INCONSISTENT_COUNTS',{v['code'] for v in item['findings']})
        partial=self.report(candidate(payload=dict(total_lands=36,claimed_swamps=None)))['candidates'][0]
        self.assertIn('MISSING_COMPOSITION_QUANTITY',{v['code'] for v in partial['findings']})
        zero=self.report(candidate(payload=dict(total_lands=0,claimed_swamps=0)))['candidates'][0]
        self.assertNotIn('CONFLICTING',zero['review_states']);self.assertNotIn('INSUFFICIENT_SOURCE',zero['review_states'])

    def test_scope_and_category_isolation_no_cross_deck_conflict_or_leak(self):
        if not self.live():return
        value=self.report(candidate(),candidate(version='v2',payload=dict(total_lands=40,claimed_swamps=25)))
        self.assertFalse(value['conflicts'])
        objective=candidate('objective-and-mana',payload=dict(objective='resource-output',mana_requirements='Claimed larger resource needs later in the hypothetical plan.'))
        value=self.report(objective);mapped={m['template_id'] for m in value['candidates'][0]['mappings']}
        self.assertEqual(mapped,{'deck-objective','resources-and-timing','evidence-authentication'})
        self.assertFalse(self.report()['candidates'])

    def test_labels_do_not_select_relevance_and_foreign_scope_rejects(self):
        if not self.live():return
        a=self.report(candidate(assertion='Cabal Coffers is allegedly amazing.'))['candidates'][0]
        b=self.report(candidate(assertion='Unrelated owner wording; no strategic truth asserted.'))['candidates'][0]
        self.assertEqual(a['mappings'],b['mappings'])
        for change in (dict(card_ids=['foreign']),dict(namespace='printing'),dict(family='mana-and-utility'),dict(subject_ids=['port-mana'])):
            value=packet(candidate());value.update(change);value=c.seal(inputs.PACKET_VERSION,value,'packet_id')
            with self.assertRaises(ValueError):self.owner.review(value)

    def test_reference_only_format_and_performance_metadata_are_unverified(self):
        if not self.live():return
        fmt=candidate('format-legality-lead',payload=dict(format_label='Owner declared format'),reference='owner:format-note',content=dict(mode='reference-only',text=None,digest=None))
        perf=candidate('performance-lead',payload=dict(method=None,sample_scope=None,limitations=None),reference='owner:test-note',content=dict(mode='reference-only',text=None,digest=None))
        value=self.report(fmt,perf)
        self.assertTrue(all('INSUFFICIENT_SOURCE' in v['review_states'] for v in value['candidates']))
        findings={f['code'] for v in value['candidates'] for f in v['findings']}
        self.assertTrue({'CONTENT_ABSENT','MISSING_DECLARED_DATE','MISSING_PERFORMANCE_METADATA'}<=findings)
        self.assertEqual(value['review_boundary']['source_authentication'],'NOT_ESTABLISHED')

    def test_content_presence_claimed_source_and_missing_source_are_separate(self):
        if not self.live():return
        row=candidate(origin=None,content=dict(mode='supplied-utf8',text='Supplied test note.\n',digest=None))
        value=self.report(row);item=value['candidates'][0]
        self.assertEqual(item['candidate']['content']['text'],'Supplied test note.\n')
        self.assertIn('MISSING_CLAIMED_ORIGIN',{f['code'] for f in item['findings']})
        self.assertIsNone(item['authenticated_review_event'])

    def test_exact_existing_requirement_refs_and_foreign_or_irrelevant_abstention(self):
        if not self.live():return
        rows=self.report()['requirements'];ref=next(r['requirement_id'] for r in rows if r['template_id']=='swamp-composition')
        good=self.report(candidate(refs=[ref]))['candidates'][0]
        self.assertIn(ref,{m['requirement_id'] for m in good['mappings']})
        irrelevant=next(r['requirement_id'] for r in rows if r['template_id']=='format-legality')
        for ref in ('sha256:'+'0'*64,irrelevant):
            bad=self.report(candidate(refs=[ref]))['candidates'][0]
            self.assertIn('OUT_OF_SCOPE',bad['review_states']);self.assertEqual(bad['disposition'],'QUARANTINED')
            self.assertFalse(any(m['requirement_id']==ref for m in bad['mappings']))

    def test_all_categories_never_satisfy_strategy_authentication_or_permissions(self):
        if not self.live():return
        rows=[candidate(),candidate('objective-and-mana',payload=dict(objective='resource-output',mana_requirements='Declared need only.')),
            candidate('format-legality-lead',payload=dict(format_label='Unverified format'),reference='owner:format'),
            candidate('performance-lead',payload=dict(method='Claimed comparison',sample_scope='Claimed small example',limitations='Not independently reviewed'),reference='owner:performance')]
        empty=self.report();filled=self.report(*rows)
        self.assertEqual(empty['requirements'],filled['requirements'])
        self.assertEqual(filled['review_boundary']['requirement_status_changes'],[])
        self.assertEqual(filled['review_boundary']['strategic_validation'],'UNIMPLEMENTED_OR_UNAUTHORIZED')
        self.assertTrue(all(v['candidate']['permissions']=='NOT_ESTABLISHED' for v in filled['candidates']))
        self.assertFalse(any(k in filled for k in ('score','confidence','winner','recommendation','ready_for_recommendation')))

    def test_private_ownership_complete_packet_binding_and_coherent_tamper_rejection(self):
        if not self.live():return
        submitted=packet(candidate());bound=self.owner.submit(submitted);doc=bound.report();original=doc.to_json()
        submitted['candidates'].clear();bound.packet().to_dict()['candidates'].clear();doc.to_dict()['requirements'].clear()
        self.assertEqual(bound.report().to_json(),original)
        with self.assertRaises(FrozenInstanceError):bound._packet_raw=b'{}'
        for field in ('review_boundary','requirements','candidate','extra','packet_id','selector'):
            value=doc.to_dict()
            if field=='review_boundary':value[field]['source_authentication']='ESTABLISHED'
            elif field=='requirements':value[field][0]['original_status']['satisfaction']='SATISFIED'
            elif field=='candidate':value['candidates'][0]['candidate']['assertion']='Changed claim'
            elif field=='packet_id':value[field]='sha256:'+'0'*64
            elif field=='selector':value['candidate_id']=False
            else:value['approval']=True
            value=c.seal(api.REPORT_VERSION,value,'report_id')
            with self.assertRaises(ValueError):bound.validate_report(value)
        changed=packet(candidate(assertion='Different explicit submission.'))
        with self.assertRaises(ValueError):self.owner.validate_report(doc.to_dict(),changed)
        altered=bound.packet().to_dict();altered['candidates'][0]['assertion']='Rehashed but changed'
        altered=c.seal(inputs.PACKET_VERSION,altered,'packet_id')
        with self.assertRaises(ValueError):inputs.validate_packet(altered)
        # Rehashing every level creates a new unverified submission, never an
        # authorized revision of the original immutable binding or report.
        altered['candidates'][0]=c.seal(inputs.CANDIDATE_VERSION,altered['candidates'][0],'candidate_id')
        altered=inputs.make_packet(altered['candidates']).to_dict()
        with self.assertRaises(ValueError):self.owner.validate_report(doc.to_dict(),altered)

    def test_admission_uses_one_public_batch_rechecks_owner_and_catalog(self):
        if not self.live():return
        from card_intelligence.mechanics import MechanicalCardIntelligence as M
        from query import CanonicalQueryEngine as Q
        from card_rules_pilot import land_context
        with patch.object(requirements,'load_strategic_requirements',wraps=requirements.load_strategic_requirements) as public,patch.object(M,'from_attachment',wraps=M.from_attachment) as m,patch.object(Q,'from_attachment',wraps=Q.from_attachment) as q,patch.object(land_context,'read_context',wraps=land_context.read_context) as rule:
            owner=api.load_context_evidence_review(**decision_arguments());owner.review(packet(candidate()))
            self.assertEqual((public.call_count,m.call_count,q.call_count,rule.call_count),(1,1,1,1))
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)/'decision';shutil.copytree(decision_arguments()['decision_root'],root);path=root/decision.OWNER_RECORD
            value=c.read_json(path);value['scope']['not_established']=[];path.write_bytes(c.canonical(c.seal(decision.DECISION_VERSION,value,'decision_id')))
            with self.assertRaises(api.ContextReviewError):api.load_context_evidence_review(**decision_arguments(decision_root=root))
        self.assertEqual(self.owner.review(packet()).to_dict()['provenance']['decision_id'],decision.DECISION_ID)

    def test_detail_integrity_and_original_historical_output_and_identity_abstentions(self):
        if not self.live():return
        bound=self.owner.submit(packet());value=bound.report().to_dict()
        self.assertEqual(bound.detailed(value['requirements_reference']).to_dict()['family'],'variable-output')
        full=bound.detailed(value['full_evidence_reference'])
        self.assertEqual(full.to_dict()['report_id'],decision.OVERVIEW_ID)
        self.assertEqual(hashlib.sha256(full.to_json().encode()).hexdigest(),decision.OVERVIEW_SHA256)
        reference=deepcopy(value['requirements_reference']);reference['bytes']+=1
        with self.assertRaises(ValueError):bound.detailed(reference)
        by_id={v['identity']['card_id']:v for v in value['cards']}
        self.assertEqual(by_id[inputs.CARD_IDS[0]]['joins']['current_identifier_edge']['status'],'ESTABLISHED')
        self.assertEqual(by_id[inputs.CARD_IDS[1]]['joins']['current_identifier_edge']['status'],'IDENTITY_NOT_ESTABLISHED')
        self.assertTrue(all(v['joins']['operator_production']['status']=='IDENTITY_NOT_ESTABLISHED' for v in value['cards']))

    def test_all_inspections_rendering_determinism_strict_parse_and_no_lead_io(self):
        if not self.live():return
        bound=self.owner.submit(packet(candidate(reference='/not/read/or/fetched')))
        with patch('builtins.open',side_effect=AssertionError('no lead IO')):
            docs=[bound.report(),bound.candidates(),bound.candidate(bound.packet().to_dict()['candidates'][0]['candidate_id']),bound.provenance(),bound.conflicts(),bound.missing(),bound.check()]
        self.assertTrue(bound.provenance().to_dict()['candidates'])
        for doc in docs:
            value=doc.to_dict();self.assertEqual(bound.parse_report(doc.to_json().encode()).to_json(),doc.to_json())
            text=api.render_review(doc);self.assertIn(value['report_id'],text);self.assertIn('BLOCKED',text)
        with self.assertRaises(ValueError):bound.parse_report(docs[0].to_json().encode().replace(b'"kind":"review"',b'"kind":"review","kind":"review"'))
        with self.assertRaises(ValueError):bound.candidate('foreign')

    def test_compact_maximal_context_bounds_and_performance(self):
        if not self.live():return
        self.assertLess(self.load_seconds,30)
        rows=[]
        for n in range(inputs.MAX_CANDIDATES):
            rows.append(candidate('performance-lead',version=str(n),origin='x'*120,reference='x'*160,assertion='x'*240,
                payload=dict(method='x'*160,sample_scope='x'*160,limitations='x'*160),
                claimed_use_restrictions='x'*160,notes=['x'*120,'y'*120,'z'*120],
                content=dict(mode='supplied-utf8',text='x'*1024,digest=None)))
        start=time.perf_counter();doc=self.owner.review(packet(*rows));text=api.render_review(doc)
        self.assertLess(time.perf_counter()-start,5);self.assertLessEqual(len(doc.to_json().encode()),65536);self.assertLessEqual(len(text.encode()),32768)
        self.assertNotIn('x'*512,text)  # Full content available by packet/candidate inspection, not a raw JSON appendix.
        # Maximum provenance plus every pair contradicting both defined counts.
        rows=[candidate(origin='x'*120,reference='x'*160,assertion='x'*240,
            payload=dict(total_lands=50+n,claimed_swamps=20+n),claimed_use_restrictions='x'*160,
            notes=['x'*120,'y'*120,'z'*120],content=dict(mode='supplied-utf8',text='x'*1024,digest=None)) for n in range(4)]
        doc=self.owner.review(packet(*rows));self.assertEqual(len(doc.to_dict()['conflicts']),12)
        self.assertLessEqual(len(doc.to_json().encode()),65536);self.assertLessEqual(len(api.render_review(doc).encode()),32768)

    def test_actual_cli_read_only_create_review_conflict_and_no_approval_action(self):
        if not self.live():return
        from card_intelligence.context_review_cli import main,parser
        args=[]
        for k,v in decision_arguments().items():args += ['--'+k.replace('_','-'),str(v)]
        paths=[ROOT/'data/canonical/state.json',ROOT/'data/review/land-semantic-decisions/owner-acceptance-v1.json',ROOT/'src/card_intelligence/strategic_requirements.py']
        before=[p.read_bytes() for p in paths]
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'packet.json';path.write_bytes(c.canonical(packet(candidate())))
            out=io.StringIO()
            with contextlib.redirect_stdout(out):self.assertEqual(main(args+['--json','review',str(path)]),0)
            self.owner.validate_report(json.loads(out.getvalue()),c.read_json(path))
            with patch('card_intelligence.context_review_cli.load_context_evidence_review',return_value=self.owner):
                path.write_bytes(c.canonical(packet(candidate(),candidate(payload=dict(total_lands=40,claimed_swamps=25)))))
                with contextlib.redirect_stdout(io.StringIO()):self.assertEqual(main(args+['conflicts',str(path)]),3)
                row=candidate();raw={k:row[k] for k in ('category','source','scope','assertion','payload','content','claimed_use_restrictions','requirement_refs','notes')}
                path.write_bytes(c.canonical([raw]));out=io.StringIO()
                with contextlib.redirect_stdout(out):self.assertEqual(main(args+['--json','create',str(path)]),0)
                inputs.parse_packet(out.getvalue().encode())
        self.assertEqual(before,[p.read_bytes() for p in paths])
        self.assertNotIn('approve',parser().format_help())

    def test_actual_demonstration_receipts_recompute_from_complete_submissions(self):
        if not self.live():return
        receipt=c.read_json(ROOT/'docs/examples/context-evidence-review-v1.json')
        self.assertEqual(receipt['schema_id'],inputs.SCHEMA_ID);self.assertEqual(receipt['policy_id'],api.POLICY_ID)
        self.assertEqual(len(receipt['demonstration_coverage']),12);self.assertEqual(len(receipt['records']),10)
        for record in receipt['records']:
            doc=self.owner.review(record['packet']);value=doc.to_dict()
            self.assertEqual(record['report_id'],value['report_id'])
            self.assertEqual(record['canonical_bytes'],len(doc.to_json().encode()))
            self.assertEqual(record['readable_bytes'],len(api.render_review(doc).encode()))
            self.assertEqual(record['conflicts'],value['conflicts']);self.assertEqual(record['review_boundary'],value['review_boundary'])
            self.assertEqual(record['review_states'],value['review_states'])
            for item in record['candidate_findings']:
                actual=next(v for v in value['candidates'] if v['candidate']['candidate_id']==item['candidate_id'])
                for key in ('review_states','disposition','findings','mappings'):self.assertEqual(item[key],actual[key])


class ContextReviewPreservationTests(unittest.TestCase):
    def test_exact_helper_predecessors_and_finite_runtime_additions(self):
        import context_review_preservation_support as support
        import overlay_preservation_support as older
        import proposed_spell_packet_analysis_preservation as guard
        for name,pins in support.PINS.items():
            raw=(ROOT/name).read_bytes();old=support.preceding_bytes(name,raw)
            self.assertEqual(hashlib.sha256(old).hexdigest(),pins['old']['sha256'])
            for changed in (raw+b'future',b'X'+raw[1:],bytearray(raw)):
                with self.assertRaises(AssertionError):support.preceding_bytes(name,changed)
        self.assertEqual(set(support.ADDITIONS),set(guard.CONTEXT_REVIEW_SOURCE_PATHS))
        self.assertEqual(len(support.ADDITIONS),3)
        for name in support.ADDITIONS:
            self.assertTrue(guard.is_packet_analysis_addition(ROOT/name))
            self.assertTrue(older.is_overlay_addition(ROOT/name,ROOT));older.assert_overlay_addition(ROOT/name,ROOT)
            self.assertFalse(older.is_overlay_addition(ROOT/(name+'.future'),ROOT))


if __name__=='__main__':unittest.main()
