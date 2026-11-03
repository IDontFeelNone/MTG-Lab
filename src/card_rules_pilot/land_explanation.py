"""Compact read-only views admitted through the exact owner decision consumer."""
from dataclasses import dataclass
import hashlib
import json
from . import contract as c, land_decision as d, land_explanation_policy as policy
from .land import COMPARISONS

REPORT_VERSION = 'card-rules-accepted-land-explanation-report-v1'
REPORT_LIMIT = 65536
READABLE_LIMIT = 32768

@dataclass(frozen=True, init=False)
class LandExplanationConsumer:
    _snapshot: bytes

    @property
    def subject_ids(self): return d.SUBJECT_IDS
    @property
    def card_names(self):
        return tuple(dict.fromkeys(row['card'] for row in json.loads(self._snapshot)['rows']))
    @property
    def comparison_names(self): return tuple(COMPARISONS)

    def _report(self, kind, selector=None):
        snapshot = json.loads(self._snapshot)
        rows = snapshot['rows']
        if kind in ('subject', 'provenance'):
            selected = [r for r in rows if type(selector) is str and r['subject_id'] == selector]
        elif kind == 'card':
            selected = [r for r in rows if type(selector) is str and r['card'] == selector]
        elif kind == 'comparison' and type(selector) is str and selector in COMPARISONS:
            selected = [next(r for r in rows if r['subject_id'] == sid) for sid in COMPARISONS[selector]]
        elif kind == 'integrity' and selector is None:
            selected = []
        else:
            raise c.PilotError('unsupported explanation selector or inference')
        if not selected and kind != 'integrity':
            raise c.PilotError('unsupported explanation selector or inference')
        comparison = None
        if kind == 'comparison':
            dimensions = ('output_pattern', 'written_cost', 'dependencies', 'ownership', 'procedure')
            comparison = {'shared': [], 'differences': [],
                'limitation': 'Capability differences establish no strategic advantage, ranking, score, deck recommendation or acquisition advice. Actual and net output, payment feasibility and game impact require additional context.'}
            for dimension in dimensions:
                entries = [{'subject_id': r['subject_id'], 'value': r['dimensions'][dimension]} for r in selected]
                target = 'shared' if len({c.canonical(e['value']) for e in entries}) == 1 else 'differences'
                comparison[target].append({'dimension': dimension, 'premises': entries})
            capabilities = {}
            for r in selected:
                if any(f['template_id'] == 'potential_mana' for f in r['findings']):
                    capabilities.setdefault('potential_mana', []).append(r['subject_id'])
            comparison['shared_capabilities'] = [{'capability': key, 'subjects': ids, 'support': 'capability findings in each referenced subject'} for key, ids in capabilities.items() if len(ids) > 1]
        value = dict(schema_version=REPORT_VERSION, kind=kind, selector=selector,
            policy_id=policy.POLICY_ID, decision_id=d.DECISION_ID,
            approved_collection_id=d.COLLECTION_ID, decision_status='ACCEPTED_BOUNDED_RETAINED_TEXT',
            scope='Historical retained-text acceptance only; original pending records preserved. No current Oracle verification, current legal action, actual payment, output or damage is established.',
            canonical_admission=False, execution_authority='BLOCKED',
            subjects=selected, comparison=comparison, detailed=snapshot['detailed'])
        return c.ReviewDocument._verified(c.seal(REPORT_VERSION, value, 'report_id'), limit=REPORT_LIMIT)

    def explain_subject(self, sid): return self._report('subject', sid)
    def explain_card(self, name): return self._report('card', name)
    def compare(self, name): return self._report('comparison', name)
    def provenance(self, sid): return self._report('provenance', sid)
    def check(self): return self._report('integrity')
    def validate_report(self, value):
        value = json.loads(c.owned(value, limit=REPORT_LIMIT))
        if type(value) is not dict or type(value.get('kind')) is not str:
            raise c.PilotError('complete explanation report required')
        expected = self._report(value['kind'], value.get('selector'))
        c.exact(value, expected.to_dict(), limit=REPORT_LIMIT)
        return expected
    def parse_report(self, raw): return self.validate_report(c.parse_json(raw, limit=REPORT_LIMIT))
    def detailed(self, reference):
        snapshot = json.loads(self._snapshot)
        c.exact(reference, snapshot['detailed'])
        raw = c.canonical(snapshot['overview'])
        if hashlib.sha256(raw).hexdigest() != reference['sha256'] or len(raw) != reference['bytes']:
            raise c.PilotError('detailed evidence integrity rejected')
        return c.ReviewDocument._verified(snapshot['overview'], limit=1048576)


def load_land_explanations(**arguments):
    accepted = d.load_land_decision(**arguments)
    overview = accepted.historical_overview().to_dict()
    context = overview['context']
    rows = []
    assessments = {r['subject_id']: r for r in overview['assessments']}
    for candidate in context['interpretations']['candidates']:
        sid = candidate['subject']['subject_id']
        assessed = assessments[sid]
        readings = candidate['descriptive_readings']
        findings = policy.compute(readings=readings, classification=assessed['classification'],
            behavior=assessed['behavior'], composition=assessed['additional_effect_composition'],
            unknowns=candidate['unresolved'])
        rows.append(dict(card=context['evidence']['cards'][candidate['subject']['card_id']]['card_identity']['name'],
            subject_id=sid, selected_passage=candidate['subject']['selected_passage'], findings=findings,
            dimensions=dict(output_pattern=readings['output']['pattern'], written_cost=readings['cost']['written_cost'],
                dependencies=readings['output']['dependencies'], ownership=readings['effect_ownership']['state'],
                procedure=assessed['behavior']['branch']),
            provenance=dict(candidate_id=candidate['candidate_id'], source_binding=candidate['source_binding'],
                subject_binding=candidate['subject'], assessment_id=assessed['assessment_id'],
                behavior_calculation_id=assessed['behavior']['calculation_id'],
                composition_id=assessed['additional_effect_composition']['composition_id'],
                candidate_pointer='/context/interpretations/candidates/' + str(len(rows)),
                assessment_pointer='/assessments/' + str(len(rows)))))
    raw = c.canonical(overview)
    result = object.__new__(LandExplanationConsumer)
    object.__setattr__(result, '_snapshot', c.owned(dict(rows=rows, overview=overview,
        detailed=dict(report_id=overview['report_id'], bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest(),
            route='LandExplanationConsumer.detailed(reference)')), limit=1048576))
    result.check()
    return result


def render_land_explanation(document):
    value = document.to_dict()
    lines = ['MTG Lab — accepted land explanation', value['scope'],
        'Decision: ' + value['decision_id'], 'Collection: ' + value['approved_collection_id'],
        'Policy: ' + value['policy_id'], 'Report: ' + value['report_id'],
        'Canonical admission=false; execution=BLOCKED.']
    for row in value['subjects']:
        lines += ['', row['card'] + ' / ' + row['subject_id'], row['selected_passage']]
        for finding in row['findings']:
            lines += [finding['category'] + ': ' + finding['text'],
                '  Evidence: ' + ', '.join(finding['premise_paths']) + '; rules: ' + ', '.join(finding['rule_refs'])]
        lines += ['Provenance: ' + json.dumps(row['provenance'], sort_keys=True, ensure_ascii=False)]
    if value['comparison']:
        lines.append('Shared capabilities: ' + json.dumps(value['comparison']['shared_capabilities']))
        for kind in ('shared', 'differences'):
            for item in value['comparison'][kind]:
                lines.append(kind + ' ' + item['dimension'] + ': ' + json.dumps(item['premises'], ensure_ascii=False))
        lines.append(value['comparison']['limitation'])
    lines += ['Detailed evidence: ' + json.dumps(value['detailed'], sort_keys=True), '']
    output = '\n'.join(lines)
    if len(output.encode()) > READABLE_LIMIT: raise c.PilotError('readable byte limit')
    return output
