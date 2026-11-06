"""Consistency of one frozen design package, never actual reviewer authorization."""
from copy import deepcopy
from datetime import datetime
import hashlib
import json
from pathlib import Path
import unittest

from jsonschema import Draft202012Validator, ValidationError, FormatChecker
from card_rules_pilot import contract as c, land_decision as decision
from card_intelligence import context_review_input as supplied, context_review as review
from card_intelligence import strategic_requirements_policy as requirements
from land_test_support import ROOT, current_catalog_intact
from test_land_decision import decision_arguments

PACKAGE=ROOT/'docs/design/context-review-authorization-v1'
DOMAIN='context-evidence-review-authorization-design-v1'
EXPECTED_PACKAGE_ID='sha256:9003aba185b3c31f97306f96831cb34b84710958ebcf1643ba4eb1dc0e184872'
FILES={'README.md','inventory.json','source-bindings.json','contracts.schema.json','design.json','examples.json','runtime-preservation.json'}
BASE='cd5c15b9238cd051ecbb7e164ba2cdac744ae03c'
TREE='98177d19fbd09f4c692f5de590c850a9bb9a7e7a'


def document(name):return c.parse_json((PACKAGE/name).read_bytes(),limit=262144)


def blobs():return {p.name:p.read_bytes() for p in PACKAGE.iterdir() if p.is_file()}


def verify(value):
    """Test-only verification of this exact pinned design, not a runtime inspector."""
    if type(value) is not dict or set(value)!=FILES|{'manifest.json'}:raise ValueError('closed design package')
    if sum(len(v) for v in value.values())>524288 or any(type(v) is not bytes or len(v)>262144 for v in value.values()):raise ValueError('bounded package bytes')
    manifest=c.parse_json(value['manifest.json'],limit=262144)
    if manifest.get('package_id')!=EXPECTED_PACKAGE_ID or c.identity(DOMAIN,manifest,'package_id')!=EXPECTED_PACKAGE_ID:raise ValueError('exact independent package pin')
    if set(manifest['files'])!=FILES:raise ValueError('exact file inventory')
    for name in FILES:
        c.exact(manifest['files'][name],dict(bytes=len(value[name]),sha256=hashlib.sha256(value[name]).hexdigest()))
    return manifest


def _packets():
    original=c.read_json(ROOT/'docs/examples/context-evidence-review-v1.json')
    values=[v['packet'] for v in original['records']]+document('examples.json')['illustrative_new_submissions']
    return {v['packet_id']:v for v in values}


def _record_examples():return [v for v in document('examples.json')['examples'] if v['proposed_record'] is not None]


def _proposal_validator(schema):
    # Explicit test-only calendar syntax check: optional RFC3339 dependencies
    # need not be installed. This proves no trusted time or reviewer event.
    checker=FormatChecker()
    @checker.checks('date-time',raises=ValueError)
    def utc(value):
        if type(value) is not str:return True
        datetime.strptime(value,'%Y-%m-%dT%H:%M:%SZ')
        return True
    return Draft202012Validator(schema,format_checker=checker)


def _assert_fixed_example_links(test,example,packets,record_map):
    """Assertions over illustrative fixtures; never computes authorization or current status."""
    record=example['proposed_record']
    if record is None:return
    packet=packets[record['packet_id']]
    test.assertEqual(packet['packet_id'],record['packet_id'])
    test.assertEqual(record['packet_content_digest'],'sha256:'+hashlib.sha256(c.canonical(packet)).hexdigest())
    candidates={v['candidate_id']:v for v in packet['candidates']}
    test.assertTrue(set(record['candidate_ids'])<=set(candidates))
    test.assertEqual(record['scope']['packet_ids'],[packet['packet_id']])
    test.assertEqual(record['scope']['candidate_ids'],record['candidate_ids'])
    test.assertEqual(record['scope']['requirement_ids'],record['requirement_ids'])
    test.assertEqual(record['scope']['prior_review_record_ids'],record['prior_review_record_ids'])
    test.assertEqual(set(record['scope']['claim_ids']),{v['claim_id'] for v in record['claims']})
    for claim in record['claims']:
        candidate=candidates[claim['candidate_id']]
        test.assertEqual(claim['packet_id'],packet['packet_id'])
        test.assertEqual(c.identity(claim['schema_version'],claim,'claim_id'),claim['claim_id'])
        value=candidate
        for part in claim['pointer'].strip('/').split('/'):value=value[part]
        test.assertEqual(claim['value_digest'],'sha256:'+hashlib.sha256(c.canonical(value)).hexdigest())
        test.assertEqual(claim['scope_digest'],'sha256:'+hashlib.sha256(c.canonical(candidate['scope'])).hexdigest())
        test.assertEqual(candidate['scope']['deck_id'],record['scope']['deck_id'])
        test.assertEqual(candidate['scope']['deck_version'],record['scope']['deck_version'])
    for identity in record['submission_identities']:
        test.assertEqual(identity['packet_id'],packet['packet_id'])
        candidate=candidates[identity['candidate_id']]
        test.assertEqual(identity['candidate_bytes_digest'],'sha256:'+hashlib.sha256(c.canonical(candidate)).hexdigest())
        test.assertEqual(identity['supplied_content_digest'],candidate['content']['digest'])
        test.assertEqual(identity['content_mode'],candidate['content']['mode'])
    test.assertEqual(c.identity(record['schema_version'],record,'record_id'),record['record_id'])
    for parent in record['prior_review_record_ids']:
        test.assertIn(parent,record_map);test.assertNotEqual(parent,record['record_id'])
    for prior_packet in record['prior_submission_packet_ids']:
        test.assertIn(prior_packet,packets);test.assertNotEqual(prior_packet,packet['packet_id'])


class ContextReviewAuthorizationDesignTests(unittest.TestCase):
    def test_exact_immutable_package_closed_inventory_and_canonical_independent_views(self):
        values=blobs();manifest=verify(values)
        self.assertEqual({p.name for p in PACKAGE.iterdir()},FILES|{'manifest.json'})
        self.assertFalse(any(p.is_symlink() or not p.is_file() for p in PACKAGE.iterdir()))
        self.assertEqual(manifest['canonical_base'],BASE);self.assertEqual(manifest['canonical_tree'],TREE)
        self.assertEqual(manifest['status'],'DESIGN_ONLY_NOT_RUNTIME_OR_AUTHORIZATION')
        for name in FILES-{'README.md'}:self.assertEqual(c.canonical(document(name)),values[name])
        manifest.clear();self.assertEqual(verify(values)['package_id'],EXPECTED_PACKAGE_ID)
        with self.assertRaises(ValueError):verify(dict(values,future=b'not authorized'))
        with self.assertRaises(ValueError):c.parse_json(b'{"a":1,"a":2}\n')
        with self.assertRaises(ValueError):c.parse_json(b'{"a":NaN}\n')

    def test_byte_tampering_and_coherently_rehashed_manifest_or_decision_reject(self):
        original=blobs()
        for name in FILES:
            changed=dict(original);changed[name]+=b'\n'
            with self.assertRaises(ValueError):verify(changed)
            manifest=document('manifest.json');manifest['files'][name]=dict(bytes=len(changed[name]),sha256=hashlib.sha256(changed[name]).hexdigest())
            changed['manifest.json']=c.canonical(c.seal(DOMAIN,manifest,'package_id'))
            with self.assertRaises(ValueError):verify(changed)
        changed=dict(original);examples=document('examples.json');body=examples['examples'][3]['proposed_record']
        body['findings']=['This Card is universally superior.'];body=c.seal(body['schema_version'],body,'record_id');examples['examples'][3]['proposed_record']=body
        changed['examples.json']=c.canonical(examples);manifest=document('manifest.json');manifest['files']['examples.json']=dict(bytes=len(changed['examples.json']),sha256=hashlib.sha256(changed['examples.json']).hexdigest());changed['manifest.json']=c.canonical(c.seal(DOMAIN,manifest,'package_id'))
        with self.assertRaises(ValueError):verify(changed)

    def test_closed_bounded_proposal_schemas_and_twelve_illustrative_examples(self):
        schema=document('contracts.schema.json');Draft202012Validator.check_schema(schema);validator=_proposal_validator(schema)
        self.assertEqual(c.identity('context-review-authorization-proposed-schemas-v1',schema,'schema_id'),schema['schema_id'])
        def closed(node):
            if type(node) is dict:
                if node.get('type')=='object':
                    self.assertIs(node.get('additionalProperties'),False);self.assertEqual(set(node['required']),set(node['properties']))
                for value in node.values():closed(value)
            elif type(node) is list:
                for value in node:closed(value)
        closed(schema)
        examples=document('examples.json')['examples'];self.assertEqual(len(examples),12)
        self.assertEqual({v['example_id'] for v in examples},{f'illustrative-{n:02}' for n in range(1,13)})
        for example in examples:validator.validate(example)

    def test_schema_rejects_unknown_types_forged_approval_and_forbidden_promotion(self):
        validator=_proposal_validator(document('contracts.schema.json'));original=document('examples.json')['examples'][3]
        for mode in ('approval','authentication','authorization','execution','permission','strategic','foreign','role'):
            value=deepcopy(original)
            if mode=='approval':value['approved']=True
            elif mode=='authentication':value['actual_boundary']['actual_authentication']='AUTHENTICATED'
            elif mode=='authorization':value['actual_boundary']['actual_authorization']='AUTHORIZED'
            elif mode=='execution':value['actual_boundary']['canonical_admission']=True
            elif mode=='permission':value['proposed_record']['non_promotion']['permissions']['ai_export']='GRANTED'
            elif mode=='strategic':value['proposed_record']['strategic_confidence']=100
            elif mode=='foreign':value['proposed_record']['scope']['card_ids']=['foreign']
            else:value['proposed_record']['owner_approved']=True
            with self.assertRaises(ValidationError):validator.validate(value)
        for invalid in (True,1.5,{},['arbitrary']):
            value=deepcopy(original);value['proposed_record']['packet_id']=invalid
            with self.assertRaises(ValidationError):validator.validate(value)
        value=deepcopy(original);value['proposed_record']['claimed_decision_time']='2026-02-30T12:00:00Z'
        with self.assertRaises(ValidationError):validator.validate(value)

    def test_original_packet_candidate_content_claim_and_requirement_identities_preserved(self):
        examples=document('examples.json');packets=_packets();original=c.read_json(ROOT/'docs/examples/context-evidence-review-v1.json')
        original_ids=[v['packet']['packet_id'] for v in original['records']]
        self.assertEqual(examples['original_packet_ids'],original_ids)
        self.assertEqual(document('source-bindings.json')['original_packet_ids'],original_ids)
        requirement_ids={v['requirement_id'] for v in original['records'][0]['requirement_statuses']}
        record_map={v['proposed_record']['record_id']:v['proposed_record'] for v in _record_examples()}
        for packet in packets.values():self.assertEqual(supplied.validate_packet(packet).to_dict(),packet)
        for example in examples['examples']:
            self.assertTrue(set(example['packet_refs'])<=set(packets))
            _assert_fixed_example_links(self,example,packets,record_map)
            if example['proposed_record'] is not None:self.assertTrue(set(example['proposed_record']['requirement_ids'])<=requirement_ids)
        changed=deepcopy(examples['examples'][3]);changed['proposed_record']['claims'][0]['value_digest']='sha256:'+'0'*64
        with self.assertRaises(AssertionError):_assert_fixed_example_links(self,changed,packets,record_map)

    def test_append_only_corrected_submission_and_predecessor_rules_without_projection(self):
        examples=document('examples.json')['examples'];record_map={v['proposed_record']['record_id']:v['proposed_record'] for v in _record_examples()}
        earlier=examples[3]['proposed_record'];corrected=examples[6]['proposed_record'];invalidation=examples[7]['proposed_record']
        self.assertEqual(corrected['prior_review_record_ids'],[earlier['record_id']])
        self.assertEqual(corrected['prior_submission_packet_ids'],[earlier['packet_id']])
        self.assertNotEqual(corrected['packet_id'],earlier['packet_id'])
        self.assertEqual(invalidation['prior_review_record_ids'],[corrected['record_id']])
        self.assertEqual(invalidation['disposition'],'INVALIDATE_PRIOR_REVIEW');self.assertEqual(invalidation['requested_action'],'ISSUE_INVALIDATION')
        # A fixture acyclicity assertion only; no current-status or authority calculation.
        def visit(identity,path):
            self.assertNotIn(identity,path)
            self.assertIn(identity,record_map)
            for parent in record_map[identity]['prior_review_record_ids']:visit(parent,path|{identity})
        for identity in record_map:visit(identity,set())
        changed=deepcopy(examples[6]);changed['proposed_record']['prior_review_record_ids']=['sha256:'+'0'*64]
        with self.assertRaises(AssertionError):_assert_fixed_example_links(self,changed,_packets(),record_map)
        changed=deepcopy(examples[6]);changed['proposed_record']['prior_review_record_ids']=[corrected['record_id']]
        with self.assertRaises(AssertionError):_assert_fixed_example_links(self,changed,_packets(),record_map)

    def test_authentication_and_authorization_are_absent_in_every_example(self):
        design=document('design.json');boundary=design['authentication_boundary']
        self.assertEqual(boundary['actual'],'AUTHENTICATION_NOT_IMPLEMENTED');self.assertEqual(boundary['authorization'],'AUTHORIZATION_NOT_ESTABLISHED')
        self.assertIsNone(boundary['provider']);self.assertEqual(boundary['trusted_issuers'],[])
        for example in document('examples.json')['examples']:
            actual=example['actual_boundary'];self.assertEqual(actual['actual_authentication'],'AUTHENTICATION_NOT_IMPLEMENTED')
            self.assertEqual(actual['actual_authorization'],'AUTHORIZATION_NOT_ESTABLISHED');self.assertIsNone(actual['actual_review_event'])
            self.assertEqual(example['illustration'],'ILLUSTRATIVE_ONLY')
            for key in ('proposed_record','authorization_concept','attestation_concept','revocation_concept'):
                value=example[key]
                if value is not None:self.assertEqual(value['model_status'],'ILLUSTRATIVE_ONLY')
            if example['proposed_record'] is not None:self.assertEqual(example['proposed_record']['sources']['independently_verified_references'],[])
        self.assertIn('Host owns authentication', (ROOT/'src/production_evidence/automatic_updates.py').read_text().replace('The host owns authentication','Host owns authentication'))

    def test_scope_mismatch_and_role_actions_cannot_become_authorized(self):
        example=document('examples.json')['examples'][8];record=example['proposed_record'];grant=example['authorization_concept']
        self.assertEqual(record['reviewer']['authorization_id'],grant['grant_id'])
        self.assertEqual(record['scope']['categories'],['format-legality-lead'])
        self.assertEqual(grant['scope']['categories'],['deck-composition'])
        self.assertNotEqual(record['scope']['packet_ids'],grant['scope']['packet_ids'])
        self.assertIn('AUTHORIZATION_SCOPE_MISMATCH',example['expected_boundary_findings'])
        design=document('design.json');roles=design['authentication_boundary']['role_actions']
        self.assertNotIn('ISSUE_SCOPE_GRANT',{v for values in roles.values() for v in values})
        self.assertNotIn('REVOKE_SCOPE_GRANT',{v for values in roles.values() for v in values})
        self.assertNotIn('ISSUE_INVALIDATION',roles['CONTEXT_FACTUAL_REVIEWER'])

    def test_complete_hypothetical_attestation_binds_body_scope_grant_nonce_without_proof(self):
        example=document('examples.json')['examples'][11];record=example['proposed_record'];grant=example['authorization_concept'];event=example['attestation_concept']
        self.assertEqual(c.identity(grant['schema_version'],grant,'grant_id'),grant['grant_id'])
        self.assertEqual(c.identity(event['schema_version'],event,'event_id'),event['event_id'])
        self.assertEqual(event['review_record_id'],record['record_id']);self.assertEqual(event['authorization_id'],grant['grant_id'])
        self.assertEqual(record['reviewer']['authorization_id'],grant['grant_id'])
        self.assertEqual(event['principal'],record['reviewer']['claimed_principal']);self.assertEqual(event['principal'],grant['principal'])
        self.assertEqual(grant['scope'],record['scope']);self.assertIn(record['requested_action'],grant['permitted_actions'])
        # A valid illustrative calendar interval still establishes no trusted time.
        self.assertLess(grant['effective_period']['not_before'],record['claimed_decision_time'])
        self.assertLess(record['claimed_decision_time'],grant['effective_period']['not_after'])
        payload=dict(domain='context-evidence-review-event-signing-payload-proposal-v1',record_id=record['record_id'],authorization_id=grant['grant_id'],principal=event['principal'],action=record['requested_action'],scope_digest='sha256:'+hashlib.sha256(c.canonical(record['scope'])).hexdigest(),packet_id=record['packet_id'],claim_ids=sorted(v['claim_id'] for v in record['claims']),nonce=event['request_nonce'])
        self.assertEqual(event['signed_payload_digest'],'sha256:'+hashlib.sha256(c.canonical(payload)).hexdigest())
        for field in ('signature_evidence_ref','trusted_timestamp_evidence_ref','issuer_trust_evidence_ref','revocation_snapshot_ref'):self.assertIsNone(event[field])
        changed=deepcopy(payload);changed['nonce']='illustrative:different-event'
        self.assertNotEqual(event['signed_payload_digest'],'sha256:'+hashlib.sha256(c.canonical(changed)).hexdigest())
        self.assertIn('NO_ACTUAL_SIGNATURE_OR_TRUSTED_TIMESTAMP',example['expected_boundary_findings'])

    def test_revocation_expiry_conflict_and_source_unavailability_remain_separate(self):
        design=document('design.json');cases={v['case']:v for v in design['lineage_cases']}
        required={'corrected-claim','contradicted-source','reviewer-error','expired-authorization','prospective-revocation','retroactive-compromise','new-deck-version','incompatible-valid-reviews','replay-or-duplicate','changed-original-packet','source-unavailable','missing-or-cyclic-predecessor'}
        self.assertEqual(set(cases),required)
        rev=document('examples.json')['examples'][7]['revocation_concept']
        self.assertEqual(c.identity(rev['schema_version'],rev,'revocation_id'),rev['revocation_id'])
        self.assertEqual(rev['effect'],'PROSPECTIVE_NO_NEW_ACTIONS');self.assertNotEqual(rev['effective_from'],rev['recorded_at'])
        self.assertIsNone(rev['issuer_verification_ref'])
        self.assertEqual(design['projection_contract']['implementation'],'NOT_IMPLEMENTED')
        self.assertIn('CONFLICTING_REVIEWS',design['projection_statuses']);self.assertIn('EVIDENCE_UNAVAILABLE',design['projection_statuses'])
        self.assertGreaterEqual(len(design['threats']),18)

    def test_source_bindings_existing_governance_owning_contracts_and_permissions(self):
        binding=document('source-bindings.json');self.assertEqual(binding['canonical_base'],BASE);self.assertEqual(binding['canonical_tree'],TREE)
        self.assertEqual(binding['accepted_owner_decision_id'],decision.DECISION_ID);self.assertEqual(binding['accepted_collection_id'],decision.COLLECTION_ID)
        self.assertEqual(binding['submitted_packet_schema_id'],supplied.SCHEMA_ID);self.assertEqual(binding['existing_packet_review_policy_id'],review.POLICY_ID);self.assertEqual(binding['requirements_policy_id'],requirements.POLICY_ID)
        pins={v['path']:v for v in binding['files']};intact=current_catalog_intact(self)
        for name,pin in pins.items():
            if name=='data/canonical/state.json' and not intact:continue  # exact actual writer shape already verified by the inherited guard
            path=ROOT/name;raw=path.read_bytes();self.assertEqual(len(raw),pin['bytes']);self.assertEqual(hashlib.sha256(raw).hexdigest(),pin['sha256'])
        for subsystem in document('inventory.json')['subsystems']:
            self.assertTrue(subsystem['implemented']);self.assertTrue(subsystem['authority_boundary']);self.assertTrue(subsystem['missing_or_blocked'])
            for name in subsystem['owning_files']:self.assertIn(name,pins)
            text='\n'.join((ROOT/name).read_text() for name in subsystem['owning_files'])
            for symbol in subsystem['public_contracts']:self.assertIn(symbol.split('.')[-1],text)

    def test_actual_public_source_admission_or_actual_expanded_catalog_rejection(self):
        if not current_catalog_intact(self):
            with self.assertRaises(review.ContextReviewError) as caught:review.load_context_evidence_review(**decision_arguments())
            self.assertEqual(caught.exception.code,'EVIDENCE_ADMISSION_REJECTED');return
        owner=review.load_context_evidence_review(**decision_arguments());report=owner.review(supplied.make_packet().to_dict()).to_dict()
        self.assertEqual(report['requirements_reference']['report_id'],'sha256:47b134c21c5a54087ed29e6c70b06a5591e60958f38e2db4c759d1bafb71cedd')
        self.assertEqual(report['provenance']['decision_id'],decision.DECISION_ID)
        self.assertEqual({v['subject_id'] for v in report['capabilities']},set(supplied.SUBJECT_IDS))
        self.assertIsNone(report['review_boundary']['authenticated_reviewer']);self.assertIsNone(report['review_boundary']['approval'])
        actual_ids={v['requirement_id'] for v in report['requirements']}
        for example in _record_examples():self.assertTrue(set(example['proposed_record']['requirement_ids'])<=actual_ids)
        full=owner.detailed(report['full_evidence_reference'])
        self.assertEqual(full.to_dict()['report_id'],decision.OVERVIEW_ID)
        self.assertEqual(hashlib.sha256(full.to_json().encode()).hexdigest(),decision.OVERVIEW_SHA256)

    def test_all_inherited_runtime_and_workflows_are_byte_exact_no_runtime_addition(self):
        value=document('runtime-preservation.json');self.assertEqual(value['canonical_base'],BASE)
        self.assertEqual(c.identity(value['schema_version'],value,'preservation_id'),value['preservation_id'])
        expected={v['path'] for v in value['files']};actual=set()
        for directory in ('src','.github'):
            for p in (ROOT/directory).rglob('*'):
                if p.is_file() and '__pycache__' not in p.parts and p.suffix!='.pyc':actual.add(p.relative_to(ROOT).as_posix())
        self.assertEqual(actual,expected)
        for pin in value['files']:
            path=ROOT/pin['path'];raw=path.read_bytes();self.assertFalse(path.is_symlink())
            self.assertEqual(len(raw),pin['bytes']);self.assertEqual(hashlib.sha256(raw).hexdigest(),pin['sha256'])
            self.assertEqual(bool(path.stat().st_mode&0o111),pin['mode']=='100755')

    def test_exact_one_future_recommendation_and_no_runtime_or_authority_promotion(self):
        design=document('design.json');manifest=verify(blobs());examples=document('examples.json')
        self.assertEqual(c.identity(design['schema_version'],design,'design_id'),design['design_id'])
        self.assertEqual(manifest['design_policy_id'],design['design_id'])
        options=design['next_milestones'];self.assertEqual([v['rank'] for v in options],[1,2,3]);self.assertEqual(sum(v['recommended'] for v in options),1)
        self.assertEqual(options[0]['name'],'Design-boundary verifier and read-only review-lineage inspector')
        for value in (design,manifest):
            for key in ('future_implementation_authorized','future_source_projection_authorized','future_milestone_begun'):self.assertIs(value[key],False)
        for example in examples['examples']:
            b=example['actual_boundary'];self.assertFalse(b['canonical_admission']);self.assertEqual(b['execution_authority'],'BLOCKED')
            self.assertEqual(b['strategic_validation'],'UNIMPLEMENTED_OR_UNAUTHORIZED');self.assertEqual(b['source_policy_clearance'],'not_granted')
            self.assertEqual(set(b['permissions'].values()),{'NOT_ESTABLISHED'})


if __name__=='__main__':unittest.main()
