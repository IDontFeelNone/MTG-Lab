"""Immutable design verification only; no integration runtime or source promotion."""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import unittest

from jsonschema import Draft202012Validator, ValidationError
from card_rules_pilot import contract as c, land_decision as d, mana_scenario as h, mana_scenario_policy as hp
from land_test_support import ROOT, current_catalog_intact
from test_land_decision import decision_arguments

PACKAGE = ROOT / 'docs/design/rules-card-intelligence-v1'
DOMAIN = 'rules-card-intelligence-integration-design-v1'
EXPECTED_PACKAGE_ID = 'sha256:fdd5e2362a36b906f3158977ced62aeb7f2f41e8a5acb111fbf1c01bbe6849a5'
FILES = {'README.md','inventory.json','identity-joins.json','source-bindings.json','contract.schema.json','examples.json'}


def verify(blobs):
    """Verify this one frozen design package, not arbitrary consumer evidence."""
    if set(blobs) != FILES | {'manifest.json'}: raise ValueError('closed design file set')
    manifest = c.parse_json(blobs['manifest.json'])
    if manifest.get('package_id') != EXPECTED_PACKAGE_ID or c.identity(DOMAIN, manifest, 'package_id') != EXPECTED_PACKAGE_ID:
        raise ValueError('exact immutable design identity')
    if set(manifest['files']) != FILES: raise ValueError('closed design inventory')
    for name in FILES:
        expected = dict(bytes=len(blobs[name]), sha256=hashlib.sha256(blobs[name]).hexdigest())
        c.exact(manifest['files'][name], expected)
    return manifest


def blobs(): return {p.name:p.read_bytes() for p in PACKAGE.iterdir() if p.is_file()}

def document(name): return c.parse_json((PACKAGE / name).read_bytes())


class RulesCardIntegrationDesignTests(unittest.TestCase):
    def test_immutable_package_and_independent_canonical_views(self):
        original = blobs(); manifest = verify(original)
        self.assertEqual(manifest['status'], 'DESIGN_ONLY_NOT_RUNTIME_OR_APPROVAL')
        self.assertFalse(manifest['canonical_admission']); self.assertFalse(manifest['future_implementation_authorized'])
        self.assertFalse(manifest['future_source_projection_authorized']); self.assertFalse(manifest['future_milestone_begun'])
        self.assertEqual(manifest['execution_authority'], 'BLOCKED')
        for name in FILES - {'README.md'}: self.assertEqual(c.canonical(document(name)), original[name])
        manifest.clear(); self.assertEqual(verify(original)['package_id'], EXPECTED_PACKAGE_ID)
        with self.assertRaises(ValueError): c.parse_json(b'{"a":1,"a":2}\n')
        with self.assertRaises(ValueError): verify(dict(original, future=b'not authorized'))

    def test_rehashed_manifest_and_coherent_example_tampering_reject(self):
        original = blobs()
        for name in FILES:
            changed = dict(original); changed[name] += b'\n'
            with self.assertRaises(ValueError): verify(changed)
            m = json.loads(changed['manifest.json']); m['files'][name] = dict(bytes=len(changed[name]),sha256=hashlib.sha256(changed[name]).hexdigest())
            changed['manifest.json'] = c.canonical(c.seal(DOMAIN,m,'package_id'))
            with self.assertRaises(ValueError): verify(changed)
        changed = dict(original); ex = document('examples.json')
        ex['records'][0]['layers']['strategic_hypotheses']['claims'][0]['statement'] = 'Universally superior'
        ex['records'][0] = c.seal('rules-card-evidence-design-example-v1',ex['records'][0],'design_record_id')
        changed['examples.json'] = c.canonical(ex)
        m = document('manifest.json'); m['files']['examples.json'] = dict(bytes=len(changed['examples.json']),sha256=hashlib.sha256(changed['examples.json']).hexdigest()); changed['manifest.json'] = c.canonical(c.seal(DOMAIN,m,'package_id'))
        with self.assertRaises(ValueError): verify(changed)

    def test_proposed_schema_examples_graph_and_no_semantic_or_execution_promotion(self):
        schema = document('contract.schema.json'); Draft202012Validator.check_schema(schema); validator = Draft202012Validator(schema)
        examples = document('examples.json')['records']; matrix = document('identity-joins.json')
        subjects = {r['subject_id']:r for r in matrix['subjects']}; cards = {r['card_id']:r for r in matrix['cards']}
        self.assertEqual({r['question_kind'] for r in examples},{'port-utility','coffers-value','tower-city','citadel-damage'})
        for record in examples:
            validator.validate(record)
            self.assertEqual(c.identity('rules-card-evidence-design-example-v1',record,'design_record_id'),record['design_record_id'])
            self.assertEqual(record['bindings']['decision_id'],d.DECISION_ID)
            self.assertEqual(record['bindings']['collection_id'],d.COLLECTION_ID)
            for subject in record['bindings']['subjects']: self.assertEqual(subject,subjects[subject['subject_id']])
            self.assertEqual({s['card_id'] for s in record['bindings']['subjects']},{s['card_id'] for s in record['bindings']['cards']})
            for card in record['bindings']['cards']:
                self.assertEqual(card['printing_id'],cards[card['card_id']]['printing_id'])
                self.assertEqual(card['operator_join_status'],'IDENTITY_NOT_ESTABLISHED')
            seen=set()
            for name in ('source_facts','reviewed_semantics','derived_capabilities','contextual_assumptions','strategic_hypotheses','validation'):
                layer=record['layers'][name]
                for claim in layer['claims']:
                    self.assertTrue(set(claim['depends_on']) <= seen)
                    self.assertNotIn(claim['claim_id'],seen); seen.add(claim['claim_id'])
            self.assertEqual(record['layers']['strategic_hypotheses']['status'],'HYPOTHESIS')
            self.assertEqual(record['layers']['validation']['status'],'OPEN')
            self.assertEqual(record['layers']['validation']['review_records'],[])
            ctx=record['layers']['contextual_assumptions']
            if ctx['scenario_record'] is not None:
                hp.validate_scenario(ctx['scenario_record'])
                self.assertIn(ctx['scenario_record']['scenario_id'],ctx['evidence_refs'])
            self.assertTrue(record['boundaries']['design_only'])
            self.assertEqual(record['boundaries']['execution_authority'],'BLOCKED')
            self.assertFalse(record['boundaries']['canonical_admission'])
            self.assertEqual(set(record['boundaries']['permissions'].values()),{'NOT_ESTABLISHED'})

    def test_schema_refuses_unfounded_elevation_foreign_cohort_and_unknown_fields(self):
        validator=Draft202012Validator(document('contract.schema.json')); original=document('examples.json')['records'][0]
        for change in ('score','execution','strategic','foreign','extra_layer'):
            record=deepcopy(original)
            if change=='score': record['power_score']=100
            elif change=='execution':record['boundaries']['canonical_admission']=True
            elif change=='strategic':record['layers']['strategic_hypotheses']['status']='ESTABLISHED_WITHIN_EXPLICIT_CONTEXT'
            elif change=='foreign':record['bindings']['cards'][0]['card_id']='unrelated-card'
            else: record['layers']['gameplay_execution']={}
            with self.assertRaises(ValidationError):validator.validate(record)

    def test_inventory_owning_contract_paths_and_nonproduction_readiness_are_pinned(self):
        inv=document('inventory.json')['subsystems']; self.assertEqual(len(inv),12)
        pins={x['path']:x for x in document('source-bindings.json')['files']}
        for subsystem in inv:
            self.assertTrue(subsystem['inputs']); self.assertTrue(subsystem['authority_boundary']); self.assertTrue(subsystem['missing_or_blocked'])
            self.assertTrue(subsystem['public_contracts']); self.assertTrue(subsystem['schema_versions'])
            for name in subsystem['owning_files']:self.assertIn(name,pins)
        intact=current_catalog_intact(self)
        for name,pin in pins.items():
            if name.startswith('data/') and not intact: continue
            raw=(ROOT/name).read_bytes()
            from overlay_preservation_support import verify_source_pin
            verify_source_pin(name, raw, pin)
        if not intact:
            with self.assertRaises(ValueError):h.load_mana_scenarios(**decision_arguments())

    def test_actual_owning_identity_joins_and_accepted_subject_references(self):
        if not current_catalog_intact(self):
            with self.assertRaises(ValueError):h.load_mana_scenarios(**decision_arguments())
            return
        from projection.engine import _historical_admission_records
        from repository.legacy_profile import attach_legacy_compatibility
        from repository.cards import load_card_repository
        from query import CanonicalQueryEngine
        from card_rules_pilot.cards import PROFILE_ID, QUERY_ID
        matrix=document('identity-joins.json'); state=json.loads((ROOT/'data/canonical/state.json').read_bytes()); audit=json.loads((ROOT/matrix['historical_audit_path']).read_bytes());payload=json.loads((ROOT/matrix['historical_payload_path']).read_bytes())
        historical=_historical_admission_records(ROOT/'data',audit)
        attachment=attach_legacy_compatibility(ROOT,game='magic',control_path='config/catalog_profiles/legacy-public-tier-a.json',expected_profile_id=PROFILE_ID)
        query=CanonicalQueryEngine.from_attachment(attachment)
        self.assertEqual(query.snapshot().snapshot_id,QUERY_ID)
        cards={x.canonical_identity:x for x in query.entities(entity_type='card')}; printings={x.canonical_identity:x for x in query.entities(entity_type='printing')}
        self.assertEqual((len(cards),len(printings)),(399,928))
        seed_cards,seed_printings=load_card_repository('magic',games_root=ROOT/'data/canonical/games');self.assertEqual((len(seed_cards),len(seed_printings)),(15,15))
        consumer=h.load_mana_scenarios(**decision_arguments());overview=consumer.detailed(consumer.check().to_dict()['full_evidence_reference']).to_dict()
        for row in matrix['cards']:
            cid,pid,provider=row['card_id'],row['printing_id'],row['provider_record_id']
            self.assertEqual(cards[cid].canonical_values['card_reference'],cid)
            self.assertEqual(printings[pid].canonical_values['card_id'],cid)
            self.assertNotEqual(pid,provider)
            self.assertEqual(overview['context']['evidence']['cards'][cid]['mechanical_dossier_id'],row['dossier_id'])
            self.assertEqual(overview['context']['evidence']['cards'][cid]['source']['provider_record_id'],provider)
            proof=historical['printing'][pid]; self.assertEqual(proof['values']['identifiers']['scryfallId'],provider)
            self.assertEqual(proof['values']['identifiers']['scryfallOracleId'],cid)
            self.assertEqual(proof['evidence_references'],state['printing'][pid]['evidence_references'])
            self.assertTrue(set(proof['evidence_references']) <= set(audit['promoted_entities']))
            candidate=payload['candidate_payloads'][int(row['payload_pointer'].split('/')[-1])]
            self.assertEqual(candidate['candidate_identifier'],row['payload_evidence'][0])
            self.assertEqual(candidate['mapped_fields']['uuid'],pid)
            for seed in seed_cards:self.assertNotEqual(seed['id'],cid)
        self.assertEqual(len(matrix['subjects']),9)
        for row in matrix['subjects']:
            sid=row['subject_id']; candidate=next(x for x in overview['context']['interpretations']['candidates'] if x['subject']['subject_id']==sid)
            self.assertEqual(candidate['candidate_id'],row['candidate_id']);self.assertEqual(candidate['subject']['source_field_identity'],row['source_field_identity'])
            self.assertEqual(consumer.evaluate(sid).to_dict()['subjects'][0]['accepted_explanation_id'],row['accepted_explanation_id'])
            self.assertTrue(row['rule_refs'])

    def test_identity_abstentions_coverage_and_ambiguous_membership(self):
        matrix=document('identity-joins.json');self.assertEqual(len(matrix['cards']),6)
        for row in matrix['cards']:
            self.assertEqual(row['typed_seed_join_status'],'IDENTITY_NOT_ESTABLISHED')
            self.assertEqual(row['operator_production_join_status'],'IDENTITY_NOT_ESTABLISHED')
            self.assertFalse(row['functional_role_coverage']);self.assertFalse(row['contextual_pilot_coverage'])
        self.assertEqual(sum(len(r['promoted_identifier_ids']) for r in matrix['cards']),1)
        self.assertEqual(sum(r['current_identifier_edge_status']=='IDENTITY_NOT_ESTABLISHED' for r in matrix['cards']),5)
        if not current_catalog_intact(self):
            with self.assertRaises(ValueError):h.load_mana_scenarios(**decision_arguments())
            return
        state=json.loads((ROOT/'data/canonical/state.json').read_bytes())
        for row in matrix['cards']:
            ids=[key for key,x in state['identifier'].items() if x['values'].get('namespace')=='scryfallId' and x['values'].get('value')==row['provider_record_id'] and x['values'].get('printing_uuid')==row['printing_id']]
            self.assertEqual(ids,row['promoted_identifier_ids'])
            self.assertEqual(sum(x['values'].get('card_id')==row['card_id'] for x in state['printing'].values()),row['printing_membership_count'])
        profile=json.loads((ROOT/'config/catalog_profiles/legacy-public-tier-a.json').read_bytes());self.assertFalse(profile['production_eligible'])
        roles=json.loads((ROOT/'config/card_intelligence/functional-role-pilot-v1.json').read_bytes());comparison=json.loads((ROOT/'config/card_intelligence/contextual-comparison-pilot-v1.json').read_bytes())
        landids={x['card_id'] for x in matrix['cards']}
        self.assertFalse(landids & {x['card_id'] for x in roles['cards']});self.assertFalse(landids & {x['card_id'] for x in comparison['cards']})

    def test_real_execution_and_simulation_remain_unavailable(self):
        from gameplay_rules.capabilities import ENGINE_CONTRACT_VERSION,EXECUTION_PROFILE
        self.assertEqual(ENGINE_CONTRACT_VERSION,'gameplay-kernel-v1');self.assertEqual(EXECUTION_PROFILE,'fictional-two-player-v1')
        readiness=json.loads((ROOT/'reference-reviews/gameplay-rules-execution-profile-design/readiness.json').read_bytes())
        self.assertEqual(readiness['overall_execution_readiness'],'BLOCKED');self.assertFalse(readiness['real_rules_executable']);self.assertFalse(readiness['execution_authorized'])
        self.assertEqual([p.name for p in (ROOT/'src/simulation').iterdir()],['.gitkeep'])
        self.assertEqual([p.name for p in (ROOT/'src/probability').glob('*.py')],['__init__.py'])
        self.assertEqual(document('examples.json')['status'],'ILLUSTRATIVE_NOT_STRATEGIC_VALIDATION')

if __name__=='__main__':unittest.main()
