"""Four complete source units: offline checks and separately named fresh proof.

All fixture prose below is fictional structural data, without source authority.
"""
from dataclasses import FrozenInstanceError
import copy
import hashlib
import json
import os
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch

from gameplay_rules.errors import GameplayContractError
from gameplay_rules.projection import mana_context_package as p
from gameplay_rules.projection import mana_context_source as s
from gameplay_rules.projection import mana_context_contracts as c
from gameplay_rules.projection.contracts import _json

ROOT=Path(__file__).resolve().parents[1]
REVIEWS=ROOT/'reference-reviews'
PACKAGE=REVIEWS/p.PACKAGE_NAME
FIXTURE=(b'106.11. Fictional neighboring marker.\n\xc2\xa0\n'
    b'106.12. Fictional selected body cites 605.\n\xc2\xa0\n'
    b'106.12a Fictional selected child.\n\xc2\xa0\n'
    b'106.12b Fictional selected child.\n\xc2\xa0\n'
    b'106.13. Fictional neighboring marker.\n\xc2\xa0\n'
    b'614.14. Fictional neighboring marker.\n\xc2\xa0\n'
    b'614.15. Fictional selected body.\n\xc2\xa0\n'
    b'614.16. Fictional neighboring marker.\n')


class ManaContextSourceTests(unittest.TestCase):
    def test_allowlist_complete_owned_spans_and_marker_only_neighbors(self):
        anchors=s.locate_anchors(FIXTURE)
        self.assertEqual(tuple(a['rule_reference'] for a in anchors),s.SELECTED_REFERENCES)
        self.assertEqual(s.literal_citations(FIXTURE,anchors),
            {'106.12':['605'],'106.12a':[],'106.12b':[],'614.15':[]})
        self.assertEqual(s.SELECTED_REFERENCES,('106.12','106.12a','106.12b','614.15'))
        for a in anchors:
            block=FIXTURE[a['byte_start']:a['byte_end']]
            self.assertEqual(a['span_sha256'],'sha256:'+hashlib.sha256(block).hexdigest())
            self.assertEqual(a['line_count'],1)
            self.assertFalse(block.endswith((b'\r',b'\n')))
            self.assertEqual(a['span_length'],len(block))
            self.assertIs(a['preceding_marker']['body_inspected'],False)
            self.assertIs(a['following_marker']['body_inspected'],False)
        # Neighbor bodies do not enter source spans or citations.
        changed=FIXTURE.replace(b'Fictional neighboring marker.',b'Different adjacent text 999.9.')
        after=s.locate_anchors(changed)
        self.assertEqual([a['span_sha256'] for a in anchors],[a['span_sha256'] for a in after])
        self.assertEqual(s.literal_citations(changed,after),s.literal_citations(FIXTURE,anchors))

    def test_owned_continuations_examples_preserve_internal_raw_terminators(self):
        data=FIXTURE.replace(b'Fictional selected body.\n',
            b'Fictional selected body.\r\n  Fictional continuation.\r\nExample: Fictional owned example.\r\n  Fictional example continuation.\n')
        a=s.locate_anchors(data)[-1]
        self.assertEqual(a['line_count'],4)
        self.assertEqual(a['owned_example_line_count'],1)
        raw=data[a['byte_start']:a['byte_end']]
        self.assertIn(b'\r\n  Fictional continuation.\r\nExample:',raw)
        self.assertFalse(raw.endswith((b'\r',b'\n')))
        self.assertEqual(a['span_sha256'],'sha256:'+hashlib.sha256(raw).hexdigest())
        self.assertEqual(a['span_policy'],'EXACT_RULE_BLOCK_RAW_BYTES_EXCLUDING_FINAL_LINE_TERMINATOR')

    def test_missing_duplicate_extra_numbering_and_ambiguous_blocks_reject(self):
        variations=[
            FIXTURE.replace(b'106.12a ',b'106.99 '),
            FIXTURE+b'106.12a Fictional duplicate.\n',
            FIXTURE.replace(b'614.16. ',b'614.17. '),
            FIXTURE.replace(b'614.14. ',b'614.13. '),
            FIXTURE.replace(b'106.12b ',b'106.12b. '),
            FIXTURE.replace(b'614.16. ',b'614.15a Fictional excluded child.\n614.16. '),
            FIXTURE.replace(b'614.16. ',b'Unowned continuation.\n614.16. '),
            FIXTURE.replace(b'614.16. ',b'  Late continuation.\n614.16. '),
            FIXTURE.replace(b'614.16. ',b'\n614.16. '),
            FIXTURE.replace(b'614.16. Fictional neighboring marker.\n',b''),
        ]
        for data in variations:
            with self.subTest(sha=hashlib.sha256(data).hexdigest()),self.assertRaises(GameplayContractError):
                s.locate_anchors(data)
        for invalid in (None,b'',bytearray(FIXTURE),FIXTURE+b'X'*(s.ARTIFACT_BYTE_LENGTH+1)):
            with self.assertRaises(GameplayContractError):
                s.locate_anchors(invalid)

    def test_fictional_missing_wrong_release_truncated_altered_cannot_verify(self):
        with self.assertRaises(GameplayContractError):
            s.verified_anchors(None,review_root=REVIEWS)
        for data in (FIXTURE,FIXTURE[:60],b'2099-01-01\n'+FIXTURE,
                b'X'*s.ARTIFACT_BYTE_LENGTH):
            with self.assertRaises(GameplayContractError):
                s.verify_bytes(data)
        with tempfile.TemporaryDirectory() as temp:
            artifact=Path(temp)/'fictional.txt'
            artifact.write_bytes(FIXTURE)
            with self.assertRaises(GameplayContractError):
                s.verified_anchors(artifact,review_root=REVIEWS)
        # The actual lineage verifier must complete before the locator is called.
        with patch.object(s,'_verified_bytes',side_effect=GameplayContractError('fixture','rejected')) as lineage,\
                patch.object(s,'locate_anchors') as locate:
            with self.assertRaises(GameplayContractError):
                s.verified_anchors(__file__,review_root=REVIEWS)
            self.assertEqual(lineage.call_count,1)
            locate.assert_not_called()

    def test_pinned_real_metadata_exact_spans_and_new_own_anchor_identities(self):
        expected=[('106.12',441,30359,30539),('106.12a',443,30543,30759),
            ('106.12b',445,30763,31030),('614.15',3128,407923,408473)]
        rows=c.projection()['rules']
        for row,(ref,line,start,end),pin in zip(rows,expected,_json(s.VERIFIED_ANCHORS),strict=True):
            a=row['source_anchor']
            self.assertEqual((a['rule_reference'],a['starting_physical_line'],a['byte_start'],a['byte_end']),
                (ref,line,start,end))
            self.assertEqual(a['ending_physical_line'],line)
            self.assertEqual(a['line_count'],1)
            self.assertEqual(a['owned_example_line_count'],0)
            self.assertEqual(c.seal(c.ANCHOR_DOMAIN,pin,'anchor_id'),a)
            self.assertEqual(c.seal(c.RULE_DOMAIN,row,'rule_id'),row)
            self.assertEqual(a['artifact_hash'],s.ARTIFACT_HASH)


class ManaContextPackageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.loaded=p.load_package(PACKAGE,review_root=REVIEWS)

    def test_offline_exact_four_admission_composite_and_no_semantic_closure(self):
        view=self.loaded.to_dict()
        self.assertEqual(set(view),set(p.RECORD_NAMES)|{'manifest.json'})
        self.assertEqual(p.rebuild_package(review_root=REVIEWS).to_json(),self.loaded.to_json())
        m=view['manifest.json']; projection=view['projection.json']
        self.assertEqual(m['selected_references'],list(s.SELECTED_REFERENCES))
        self.assertEqual((m['projected_rule_count_before'],m['new_source_units_projected'],m['projected_rule_count_after']),
            (100,4,104))
        self.assertEqual((m['existing_projection_count_before'],m['existing_projection_count_after']),(15,16))
        composite=p.composite_view(self.loaded,review_root=REVIEWS).to_dict()
        self.assertEqual(len(composite['projected_references']),104)
        self.assertEqual(len(set(composite['projected_references'])),104)
        self.assertEqual(len(composite['projection_components']),16)
        self.assertEqual(composite['projection_components'][-1]['package_id'],m['package_id'])
        self.assertEqual(composite['historical_interpretation_context_unit_count'],17)
        self.assertEqual(composite['separately_enriched_context_unit_count'],21)
        self.assertEqual(m['historical_acquisition_identity'],p.HISTORICAL_ACQUISITION_ID)
        for record in view.values():
            self.assertEqual(record['semantic_review_status'],'PENDING_NOT_ESTABLISHED')
            self.assertEqual(record['review'],{'status':'requires_review','human_attestation':None,'canonical_admission':False})
            self.assertEqual(record['execution_authority'],'BLOCKED')
            self.assertEqual(record['semantic_closure'],'OPEN')
        self.assertEqual(projection['projection_kind'],'NON_EXECUTABLE')
        self.assertEqual(projection['subsystem_completion'],{'mana':False,'triggers':False,'replacements':False})
        for name,record in view.items():
            if name!='manifest.json':
                self.assertEqual(m['files'][name],{'bytes':len(c.canonical(record)),
                    'sha256':hashlib.sha256(c.canonical(record)).hexdigest()})

    def test_complete_structured_content_keeps_trigger_replacement_and_order_distinct(self):
        rows={r['rule_reference']:r for r in self.loaded['projection.json']['rules']}
        self.assertEqual(rows['106.12']['activation_cost_requirement'],'CONTAINS_TAP_SYMBOL')
        trigger=rows['106.12a']; replace=rows['106.12b']; own=rows['614.15']
        self.assertEqual(trigger['relationship'],'RESOLUTION_OF_REFERENT_ABILITY_AND_MANA_PRODUCTION')
        self.assertIn('TYPE',trigger['specified_type_condition'])
        self.assertIn('AND_OR_AMOUNT',replace['specified_constraints'])
        self.assertFalse(replace['replacement_recognition_implemented'])
        self.assertIn('OWN_EFFECTS',own['replacement_scope'])
        self.assertIn('CONTINUOUS_EFFECTS',own['effect_category'])
        self.assertTrue(own['creation_text_context']['separate_ability_possible'])
        self.assertEqual(own['creation_text_context']['separate_ability_emphasis'],'ESPECIALLY_WITH_PRECEDING_ABILITY_WORD')
        self.assertTrue(own['ordering_knowledge']['self_replacements_precede_other_replacements'])
        self.assertFalse(own['ordering_knowledge']['ordering_execution_implemented'])

    def test_literal_structural_semantic_relationships_and_unresolved_are_separate(self):
        d=self.loaded['dependency-review.json']
        self.assertEqual(d['literal_numbered_citations'],{'106.12':['605'],'106.12a':[],'106.12b':[],'614.15':[]})
        resolution=d['literal_citation_resolution'][0]
        self.assertEqual(resolution['target_reference'],'605')
        self.assertEqual(len(resolution['target_rule_bindings']),13)
        self.assertEqual([r['rule_reference'] for r in resolution['target_rule_bindings']],list(p.MANA_REFERENCES))
        self.assertFalse(resolution['semantic_closure_established'])
        self.assertFalse(resolution['execution_readiness_established'])
        self.assertEqual({r['child'] for r in d['structural_relationships']},{'106.12a','106.12b'})
        self.assertEqual({(r['criterion_rule'],r['support_rule']) for r in d['semantic_support']},
            {('605.1a','614.15'),('605.1b','106.12'),('605.1b','106.12a')})
        self.assertTrue(all(r['relationship_kind']=='AUTHORED_SEMANTIC_CONTEXT_NOT_LITERAL_CITATION' for r in d['semantic_support']))
        self.assertTrue(d['genuine_unresolved_outgoing_references'])
        self.assertTrue(any(r['target_reference']=='603' for r in d['genuine_unresolved_outgoing_references']))
        self.assertTrue(all(not r['historical_dependency_array_rewritten'] for r in d['historical_outgoing_reference_accounting']))

    def test_private_immutable_ownership_strict_types_rehash_and_conflicts_reject(self):
        baseline=self.loaded.to_json()
        decoded=self.loaded.to_dict(); decoded['projection.json']['rules'].clear()
        separate=self.loaded['projection.json']; separate['rules'].clear()
        self.assertEqual(self.loaded.to_json(),baseline)
        with self.assertRaises((FrozenInstanceError,AttributeError)):
            self.loaded._raw=b'{}\n'
        changes=[]
        for key,value in [('selected_rule_count',True),('selected_rule_count',4.0),
                ('selected_rule_count','4'),('official_ruling',True),('execution_authority','READY')]:
            changed=self.loaded.to_dict(); changed['projection.json'][key]=value
            changes.append(changed)
        changed=self.loaded.to_dict(); changed['projection.json']['rules'].append(copy.deepcopy(changed['projection.json']['rules'][0])); changes.append(changed)
        changed=self.loaded.to_dict(); changed['projection.json']['rules'][0]['source_anchor']['byte_end']-=1
        changed['projection.json']=c.seal(c.PROJECTION_SCHEMA,changed['projection.json'],'projection_id'); changes.append(changed)
        changed=self.loaded.to_dict(); changed['manifest.json']['prior_package_id']='sha256:'+'0'*64
        changed['manifest.json']=c.seal(c.PACKAGE_SCHEMA,changed['manifest.json'],'package_id'); changes.append(changed)
        changed=self.loaded.to_dict(); changed['projection.json']['review']['human_attestation']={'reviewer':'fictional'}; changes.append(changed)
        with tempfile.TemporaryDirectory() as temp:
            destination=Path(temp)/'never-created'
            for value in changes:
                with self.assertRaises(GameplayContractError):
                    p.write_package(destination,value,review_root=REVIEWS)
                self.assertFalse(destination.exists())
            output=Path(temp)/'valid'
            p.write_package(output,self.loaded,review_root=REVIEWS)
            self.assertEqual(p.load_package(output,review_root=REVIEWS).to_json(),baseline)
            with self.assertRaises(GameplayContractError):
                p.write_package(output,self.loaded,review_root=REVIEWS)
            self.assertEqual(p.load_package(output,review_root=REVIEWS).to_json(),baseline)

    def test_exact_disk_bytes_duplicates_missing_extra_and_drift_reject(self):
        with tempfile.TemporaryDirectory() as temp:
            destination=Path(temp)/'package'; shutil.copytree(PACKAGE,destination)
            path=destination/'projection.json'; raw=path.read_bytes()
            for altered in (raw+b' ',b'{"schema_version":"duplicate",'+raw[1:],raw[:-2]+b',"unlisted":true}\n'):
                path.write_bytes(altered)
                with self.assertRaises(GameplayContractError):
                    p.load_package(destination,review_root=REVIEWS)
            path.write_bytes(raw)
            extra=destination/'extra.json'; extra.write_bytes(b'{}\n')
            with self.assertRaises(GameplayContractError):
                p.load_package(destination,review_root=REVIEWS)
            extra.unlink(); path.unlink()
            with self.assertRaises(GameplayContractError):
                p.load_package(destination,review_root=REVIEWS)
            self.assertTrue(self.loaded['projection.json']['rules'])

    def test_private_snapshot_taken_before_historical_validation_and_no_success_cache(self):
        candidate=self.loaded.to_dict()
        original=p.validate_historical
        with tempfile.TemporaryDirectory() as temp:
            output=Path(temp)/'owned'
            def race(*,review_root):
                candidate['projection.json']['rules'].clear()
                return original(review_root=review_root)
            with patch.object(p,'validate_historical',side_effect=race):
                written=p.write_package(output,candidate,review_root=REVIEWS)
            self.assertEqual(written.to_json(),self.loaded.to_json())
        with patch.object(p,'validate_historical',wraps=original) as validate:
            p.load_package(PACKAGE,review_root=REVIEWS)
            p.load_package(PACKAGE,review_root=REVIEWS)
            self.assertEqual(validate.call_count,2)
        # A previously admitted immutable snapshot remains usable. A new disk
        # admission still verifies current historical files instead of caching success.
        with patch.object(p,'validate_historical',side_effect=GameplayContractError('fixture','current drift')):
            self.assertTrue(self.loaded['projection.json']['rules'])
            with self.assertRaises(GameplayContractError):
                p.load_package(PACKAGE,review_root=REVIEWS)

    def test_outgoing_reference_reads_revalidate_private_bytes_after_lineage(self):
        original=p._read
        def changed(path):
            raw=original(path)
            value=json.loads(raw)
            value['rules'][0]['direct_dependency_references']=['999.9']
            # Even a coherent own-identity rehash cannot substitute history.
            field='projection_id'
            value=c.seal(value['schema_version'],value,field)
            return c.canonical(value)
        with patch.object(p,'_read',side_effect=changed):
            with self.assertRaisesRegex(GameplayContractError,'HISTORICAL_PROJECTION_PRIVATE_BYTES_CHANGED'):
                p.rebuild_package(review_root=REVIEWS)

    @unittest.skipUnless(os.environ.get('MTGLAB_MANA_CONTEXT_SOURCE'),
        'fresh owner TXT unavailable: set MTGLAB_MANA_CONTEXT_SOURCE; offline/fictional checks are not source verification')
    def test_fresh_owner_artifact_lineage_and_four_complete_raw_spans(self):
        artifact=Path(os.environ['MTGLAB_MANA_CONTEXT_SOURCE'])
        result=p.verify_source(self.loaded,artifact,review_root=REVIEWS).to_dict()
        self.assertTrue(result['fresh_source_verification'])
        self.assertEqual(result['selected_rule_count'],4)
        self.assertEqual(result['package_id'],self.loaded['manifest.json']['package_id'])
        self.assertEqual(p.build_package(artifact,review_root=REVIEWS).to_json(),self.loaded.to_json())
        raw=artifact.read_bytes()
        self.assertEqual(len(raw),977752)
        self.assertEqual('sha256:'+hashlib.sha256(raw).hexdigest(),s.ARTIFACT_HASH)
        for anchor in result['source_anchors']:
            block=raw[anchor['byte_start']:anchor['byte_end']]
            self.assertEqual('sha256:'+hashlib.sha256(block).hexdigest(),anchor['span_sha256'])
        for altered in (raw[:-1],raw[:30370]+b'X'+raw[30371:]):
            with self.assertRaises(GameplayContractError):
                s.verify_bytes(altered)


if __name__=='__main__':
    unittest.main()
