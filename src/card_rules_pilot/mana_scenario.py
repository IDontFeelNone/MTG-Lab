"""Read-only scenario views over one actual accepted-explanation admission."""
from dataclasses import dataclass
import hashlib
import json
from . import contract as c, land_explanation as e, land_decision as d
from . import mana_scenario_policy as policy
from .land import COMPARISONS

REPORT_VERSION = 'card-rules-hypothetical-mana-report-v1'
REPORT_LIMIT = 65536
READABLE_LIMIT = 32768

@dataclass(frozen=True, init=False)
class ManaScenarioConsumer:
    _snapshot: bytes

    @property
    def subject_ids(self): return d.SUBJECT_IDS
    @property
    def comparison_names(self): return tuple(COMPARISONS)

    def _report(self, kind, selector, scenario):
        snapshot = json.loads(self._snapshot)
        by_id = snapshot['subjects']
        scenario = policy.make_scenario([]).to_dict() if scenario is None else policy.validate_scenario(scenario).to_dict()
        if kind in ('subject', 'provenance') and type(selector) is str and selector in by_id:
            selected = [selector]
        elif kind == 'comparison' and type(selector) is str and selector in COMPARISONS:
            selected = list(COMPARISONS[selector])
        elif kind == 'integrity' and selector is None and not scenario['assumptions']:
            selected = list(by_id)
        else:
            raise policy.UnsupportedScenario('UNSUPPORTED: closed subject or comparison selector required')
        allowed = {policy.PATTERNS[by_id[sid]['descriptor']['pattern']] for sid in selected} - {None}
        if any(row['dimension'] not in allowed for row in scenario['assumptions']):
            raise policy.UnsupportedScenario('UNSUPPORTED: input outside selected dependencies')
        rows = []
        for sid in selected:
            admitted = by_id[sid]
            dimension = policy.PATTERNS[admitted['descriptor']['pattern']]
            filtered = [r for r in scenario['assumptions'] if r['dimension'] == dimension]
            local = policy.make_scenario(filtered).to_dict()
            calculated = policy.compute(descriptor=admitted['descriptor'], scenario=local)
            rows.append({'card': admitted['card'], 'subject_id': sid, 'calculation': calculated,
                'accepted_explanation_id': admitted['explanation_id'],
                'accepted_explanation_sha256': admitted['explanation_sha256'],
                'provenance': admitted['provenance'],
                'retained_unknowns': admitted['retained_unknowns'],
                'evidence_premises': admitted['premise_pointers']})
        states = [r['calculation']['state'] for r in rows]
        state = 'CONFLICTING' if 'CONFLICTING' in states else 'SUPPLIED' if 'SUPPLIED' in states else 'UNSPECIFIED'
        comparison = None
        if kind == 'comparison':
            comparison = {'original_comparison_id': snapshot['comparisons'][selector],
                'dimensions': ['conditional_written_output', 'written_cost', 'ownership', 'missing_inputs'],
                'finding': 'Compare the displayed written outputs, separate costs and ownership under the explicit assumptions. No actual usability, payment feasibility, net mana or strategic advantage follows.'}
        return c.ReviewDocument._verified(c.seal(REPORT_VERSION, {
            'schema_version': REPORT_VERSION, 'kind': kind, 'selector': selector,
            'policy_id': policy.POLICY_ID, 'scenario': scenario, 'state': state,
            'decision_id': d.DECISION_ID, 'approved_collection_id': d.COLLECTION_ID,
            'plan_id': d.PLAN_ID, 'context_id': d.CONTEXT_ID,
            'decision_status': 'ACCEPTED_BOUNDED_RETAINED_TEXT',
            'scope': 'Explicit hypothetical assumptions over accepted historical retained text; no observations or gameplay execution.',
            'subjects': rows, 'comparison': comparison,
            'full_evidence_reference': snapshot['detailed'],
            'canonical_admission': False, 'execution_authority': 'BLOCKED',
            'semantic_closure': 'OPEN', 'all_ten_activation_responsibilities': 'OPEN / EXECUTION_BLOCKED',
            'source_policy_clearance': 'not_granted',
            'permissions': {key: 'NOT_ESTABLISHED' for key in ('private_retention', 'redistribution', 'free_service', 'commercial_service', 'ai_export')},
            'tier_a_restrictions': 'UNCHANGED_NON_PRODUCTION'}, 'report_id'), limit=REPORT_LIMIT)

    def evaluate(self, subject_id, scenario=None): return self._report('subject', subject_id, scenario)
    def compare(self, name, scenario=None): return self._report('comparison', name, scenario)
    def provenance(self, subject_id): return self._report('provenance', subject_id, None)
    def check(self): return self._report('integrity', None, None)
    def validate_report(self, value):
        value = json.loads(c.owned(value, limit=REPORT_LIMIT))
        if type(value) is not dict or type(value.get('kind')) is not str or 'scenario' not in value:
            raise c.PilotError('complete hypothetical report required')
        expected = self._report(value['kind'], value.get('selector'), value['scenario'])
        c.exact(value, expected.to_dict(), limit=REPORT_LIMIT)
        return expected
    def parse_report(self, raw): return self.validate_report(c.parse_json(raw, limit=REPORT_LIMIT))
    def detailed(self, reference):
        snapshot = json.loads(self._snapshot)
        c.exact(reference, snapshot['detailed'])
        raw = c.canonical(snapshot['overview'])
        if len(raw) != reference['bytes'] or hashlib.sha256(raw).hexdigest() != reference['sha256']:
            raise c.PilotError('full evidence integrity rejection')
        return c.ReviewDocument._verified(snapshot['overview'], limit=1048576)


def load_mana_scenarios(**arguments):
    # Actual explanation consumer invokes actual decision and original evidence
    # admission once. Neither pending dictionaries nor hypothetical inputs admit.
    explanations = e.load_land_explanations(**arguments)
    detail = explanations.check().to_dict()['detailed']
    overview = explanations.detailed(detail).to_dict()
    subjects = {}
    candidates = overview['context']['interpretations']['candidates']
    for index, candidate in enumerate(candidates):
        sid = candidate['subject']['subject_id']
        doc = explanations.explain_subject(sid)
        row = doc.to_dict()['subjects'][0]
        readings = candidate['descriptive_readings']
        subjects[sid] = {'card': row['card'], 'explanation_id': doc.to_dict()['report_id'],
            'explanation_sha256': hashlib.sha256(doc.to_json().encode()).hexdigest(),
            'provenance': {key: row['provenance'][key] for key in (
                'candidate_id', 'source_binding', 'assessment_id', 'behavior_calculation_id', 'composition_id')},
            'premise_pointers': {'candidate': '/context/interpretations/candidates/' + str(index),
                'assessment': '/assessments/' + str(index),
                'descriptor': '/context/interpretations/candidates/' + str(index) + '/descriptive_readings'},
            'retained_unknowns': candidate['unresolved'],
            'descriptor': {'pattern': readings['output']['pattern'],
                'dependencies': readings['output']['dependencies'],
                'written_instruction': readings['output']['written_instruction'],
                'written_cost': readings['cost']['written_cost'],
                'ownership': readings['effect_ownership']['state'],
                'damage_clause': readings['effect_ownership']['damage_clause']}}
    comparisons = {row['name']: row['comparison']['comparison_id'] for row in overview['comparisons']}
    consumer = object.__new__(ManaScenarioConsumer)
    object.__setattr__(consumer, '_snapshot', c.owned(dict(subjects=subjects,
        comparisons=comparisons, detailed=detail, overview=overview), limit=1048576))
    consumer.check()
    return consumer


def render_mana_scenario(document):
    value = document.to_dict()
    lines = ['MTG Lab — hypothetical mana context', value['scope'],
        'State: ' + value['state'], 'Explicit assumptions (not observations): ' + json.dumps(value['scenario']['assumptions']),
        'Scenario: ' + value['scenario']['scenario_id'], 'Decision: ' + value['decision_id'],
        'Collection: ' + value['approved_collection_id'], 'Plan: ' + value['plan_id'], 'Context: ' + value['context_id'],
        'Policy: ' + value['policy_id'], 'Report: ' + value['report_id']]
    for row in value['subjects']:
        calc = row['calculation']
        lines += ['', row['card'] + ' / ' + row['subject_id'] + ' — ' + calc['state'],
            'Accepted written capability: ' + calc['accepted_written_capability'],
            'Local assumptions: ' + json.dumps(calc['supplied_assumptions']),
            'Conditional written output: ' + json.dumps(calc['conditional_written_output']),
            'Written cost (separate): ' + str(calc['written_cost']),
            'Ownership: ' + calc['ownership'] + '; conditional damage clause, not executed: ' + str(calc['conditional_damage_clause_not_executed']),
            'Mode: ' + calc['mode'], 'Required hypothetical inputs: ' + ', '.join(calc['required_hypothetical_inputs']),
            'Missing inputs: ' + ', '.join(calc['missing_inputs']), 'Conflict: ' + str(calc['conflict']),
            'Unknowns: ' + ' '.join(calc['unknown_game_inputs']), 'Retained unknowns: ' + ' '.join(row['retained_unknowns']),
            'Unsupported conclusions: ' + ', '.join(calc['unsupported_conclusions']),
            'Calculation: ' + calc['calculation_id'], 'Local scenario: ' + calc['scenario_id'],
            'Accepted explanation: ' + row['accepted_explanation_id'] + '; SHA-256 ' + row['accepted_explanation_sha256'],
            'Evidence: ' + json.dumps(row['provenance'], sort_keys=True), 'Pointers: ' + json.dumps(row['evidence_premises'], sort_keys=True)]
    if value['comparison']: lines += ['Comparison: ' + json.dumps(value['comparison'], sort_keys=True)]
    lines += ['Full evidence: ' + json.dumps(value['full_evidence_reference'], sort_keys=True),
        'Canonical admission=false; execution=BLOCKED; semantic closure OPEN; all ten responsibilities OPEN / EXECUTION_BLOCKED.',
        'Source clearance=not_granted; permissions=' + json.dumps(value['permissions'], sort_keys=True) + '; Tier A non-production.', '']
    output = '\n'.join(lines)
    if len(output.encode()) > READABLE_LIMIT: raise c.PilotError('readable scenario bound')
    return output
