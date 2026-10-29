"""Finite read-only land intelligence over privately admitted pending evidence.

No historical pilot loader is used. Each public load checks the actual catalog,
mechanical collection, retained packages and authored files once. Questions reuse
that owned snapshot; reports are recomputed, never accepted by their hash alone.
"""
from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path

from . import contract as c
from . import land_cards, land_authored, land_context, land_effects
from . import reasoning_policy, behavior_policy

REPORT_VERSION = 'card-rules-land-mana-report-v1'
CHECK_VERSION = 'card-rules-land-mana-integrity-v1'
ASSESSMENT_VERSION = 'card-rules-land-mana-assessment-v1'
COMPARISON_VERSION = 'card-rules-land-mana-comparison-v1'
MANIFEST_VERSION = 'card-rules-land-mana-manifest-v1'
REPORT_LIMIT = 1_048_576
INPUT_LIMIT = 524_288
COMPARISONS = {
    'mana-and-utility': ('snow-wastes-mana', 'port-mana', 'port-utility'),
    'damage-ownership': ('city-mana', 'city-damage-trigger', 'citadel-colorless', 'citadel-color-choice'),
    'variable-output': ('snow-wastes-mana', 'coffers-mana'),
    'color-context': ('tower-mana', 'city-mana'),
}


def authority():
    return {'authority': 'CONDITIONAL_LAND_INTELLIGENCE_FROM_PENDING_READINGS_ONLY',
        'semantic_review_status': 'PENDING_NOT_ESTABLISHED',
        'review': {'status': 'requires_review', 'human_attestation': None, 'canonical_admission': False},
        'execution_authority': 'BLOCKED'}


def _inputs(candidate):
    return {'proposed_kind': candidate['proposed_kind'],
        'criteria': [{key: row[key] for key in ('criterion_id', 'state', 'rule_refs')}
                     for row in candidate['criteria']],
        'kind_evidence_refs': candidate['kind_evidence_refs']}


def _assessment(candidate, facts):
    inputs = _inputs(candidate)
    classified = reasoning_policy.compute(**inputs)
    behavior = behavior_policy.compute(**inputs, rule_facts=facts)
    c.exact(classified, behavior['classification'])
    effect = land_effects.compute(subject=candidate['subject'],
        candidate=candidate, candidate_id=candidate['candidate_id'], classification=classified,
        behavior=behavior, reading=candidate['descriptive_readings']['effect_ownership'],
        rule_facts=facts)
    return c.seal(ASSESSMENT_VERSION, {'schema_version': ASSESSMENT_VERSION,
        'subject_id': candidate['subject']['subject_id'], 'candidate_id': candidate['candidate_id'],
        'card_id': candidate['subject']['card_id'], 'classification': classified,
        'behavior': behavior, 'additional_effect_composition': effect,
        'baseline_additional_effect_scope': 'BASELINE_DID_NOT_RECEIVE_EFFECT_OWNERSHIP_INPUT; ITS_NONASSERTION_IS_NOT_EVIDENCE_OF_ABSENCE',
        'descriptive_readings': candidate['descriptive_readings'],
        'remaining_unknowns': candidate['unresolved'], **authority()}, 'assessment_id')


def _compare(candidates, assessments):
    """Compare explicit structured options; labels never select conclusions."""
    options = []
    for candidate, assessed in zip(candidates, assessments):
        options.append({'subject_id': assessed['subject_id'], 'card_id': assessed['card_id'],
            'candidate_id': candidate['candidate_id'], 'assessment_id': assessed['assessment_id'],
            'complete_owned_passage': candidate['subject']['selected_passage'],
            'classification': assessed['classification']['overall_assessment'],
            'negative_witnesses': assessed['classification']['negative_witnesses'],
            'behavior_branch': assessed['behavior']['branch'],
            'written_readings': candidate['descriptive_readings'],
            'effect_relationship': assessed['additional_effect_composition'],
            'missing_inputs': candidate['unresolved']})
    # Differences are projections of the actual pending structures and computed
    # results. The finite adapter chooses the cohort, never a preferred outcome.
    dimensions = {
        'classification': lambda option: option['classification'],
        'negative_witnesses': lambda option: option['negative_witnesses'],
        'behavior_branch': lambda option: option['behavior_branch'],
        'written_cost': lambda option: option['written_readings']['cost']['written_cost'],
        'output_pattern': lambda option: option['written_readings']['output']['pattern'],
        'written_output': lambda option: option['written_readings']['output']['written_instruction'],
        'dependencies': lambda option: option['written_readings']['output']['dependencies'],
        'effect_ownership': lambda option: option['written_readings']['effect_ownership']['state'],
        'effect_composition': lambda option: option['effect_relationship']['status'],
    }
    differences = []
    for key, project in dimensions.items():
        values = [project(option) for option in options]
        if len({c.canonical(value) for value in values}) > 1:
            differences.append({'dimension': key, 'values': values})
    groups = {}
    for option in options:
        groups.setdefault(option['card_id'], []).append(option['subject_id'])
    return c.seal(COMPARISON_VERSION, {'schema_version': COMPARISON_VERSION,
        'options': options, 'differences': differences,
        'ownership_groups': [{'card_id': key, 'separate_subjects': value} for key, value in groups.items()],
        'constraints': [
            'Only each complete selected subject supplies its costs, targeting and effects. Sibling abilities supply neither borrowed mana nor borrowed damage.',
            'Printed cost, potential production, actual output, payment feasibility and strategic value are separate questions.',
            'Unknown external inputs remain unknown; they are neither zero nor an empty palette nor a classification failure.',
            'Becomes tapped and tapping for mana are distinct authored relationships; no actual event, trigger sequence or payment disruption follows.',
            'Ordinary triggered placement, ordering and response timing remain unresolved at broad 603. Exclusion alone supplies no stack placement.',
            'No snow-payment semantics, intrinsic land ability, land-play rule, subtype recognition, net benefit, break-even threshold or commander palette is inferred.',
            'No ranking, score, deck recommendation, acquisition recommendation or executable sequence is produced.',
        ], **authority()}, 'comparison_id')


@dataclass(frozen=True, init=False)
class LandConsumer:
    _snapshot: bytes

    @property
    def subject_ids(self):
        return tuple(row['subject_id'] for row in json.loads(self._snapshot)['plan']['subjects'])

    def _report(self, kind, selector=None):
        snapshot = json.loads(self._snapshot)
        candidates = snapshot['interpretations']['candidates']
        by_id = {candidate['subject']['subject_id']: candidate for candidate in candidates}
        if kind == 'subject':
            if type(selector) is not str or selector not in by_id:
                raise c.PilotError('foreign land subject')
            selected = [selector]
        elif kind == 'comparison':
            if type(selector) is not str or selector not in COMPARISONS:
                raise c.PilotError('undeclared land comparison')
            selected = list(COMPARISONS[selector])
        elif kind in ('overview', 'integrity') and selector is None:
            selected = list(by_id)
        else:
            raise c.PilotError('closed land report selection required')
        facts = {row['rule']['rule_reference']: row for row in snapshot['retained_rules']['rules']}
        results = [_assessment(by_id[sid], facts) for sid in selected]
        comparisons = []
        if kind == 'overview':
            mapped = {row['subject_id']: row for row in results}
            comparisons = [{'name': name, 'comparison': _compare([by_id[sid] for sid in members],
                [mapped[sid] for sid in members])} for name, members in COMPARISONS.items()]
        elif kind == 'comparison':
            comparisons = [{'name': selector, 'comparison': _compare([by_id[sid] for sid in selected], results)}]
        version = CHECK_VERSION if kind == 'integrity' else REPORT_VERSION
        value = {'schema_version': version, 'kind': kind, 'selector': selector,
            'plan_id': snapshot['plan']['plan_id'],
            'interpretations_id': snapshot['interpretations']['interpretations_id'],
            'context_id': snapshot['retained_rules']['context_id'],
            'context': snapshot, 'assessments': results, 'comparisons': comparisons,
            'subject_count': len(selected), 'cohort_subject_count': 9, 'cohort_card_count': 6,
            'integrity_supplies_semantic_attestation': False, **authority()}
        return c.ReviewDocument._verified(c.seal(version, value, 'report_id'), limit=REPORT_LIMIT)

    def subject(self, subject_id):
        return self._report('subject', subject_id)

    def overview(self):
        return self._report('overview')

    def comparison(self, name):
        return self._report('comparison', name)

    def check(self):
        return self._report('integrity')

    def validate_report(self, value):
        view = json.loads(c.owned(value, limit=REPORT_LIMIT))
        if type(view) is not dict or type(view.get('kind')) is not str:
            raise c.PilotError('complete land report required')
        expected = self._report(view['kind'], view.get('selector'))
        c.exact(view, expected.to_dict(), limit=REPORT_LIMIT)
        return expected


def load_lands(*, catalog_root, mechanical_root, review_root, cohort_root,
               expected_profile_id, expected_query_snapshot_id, expected_plan_id):
    """Fresh fail-closed public admission; no report store or fallback fixture."""
    evidence = land_cards.read_cards(catalog_root=catalog_root, mechanical_root=mechanical_root,
        expected_profile_id=expected_profile_id, expected_query_snapshot_id=expected_query_snapshot_id)
    context = land_context.read_context(review_root)
    plan = land_authored.build_plan(evidence)
    interpretations = land_authored.build_interpretations(evidence, context)
    if type(expected_plan_id) is not str or expected_plan_id != plan['plan_id']:
        raise c.PilotError('independent exact land plan identity required')
    root = Path(cohort_root)
    if (root.is_symlink() or not root.is_dir()
            or {path.name for path in root.iterdir()} != {'plan.json', 'interpretations.json', 'manifest.json'}):
        raise c.PilotError('exact finite land cohort file set required')
    files = {'plan.json': plan, 'interpretations.json': interpretations}
    for name, expected in files.items():
        c.exact(c.read_json(root / name, limit=INPUT_LIMIT), expected, limit=INPUT_LIMIT)
    manifest = land_authored.build_manifest(plan, interpretations)
    c.exact(c.read_json(root / 'manifest.json', limit=32_768), manifest)
    snapshot = {'evidence': evidence, 'plan': plan, 'interpretations': interpretations,
        'manifest': manifest, 'retained_rules': context['retained_rules'],
        'classification_policy': reasoning_policy.policy_document(),
        'behavior_policy': behavior_policy.policy_document(),
        'effect_ownership_policy': land_effects.policy_document()}
    consumer = object.__new__(LandConsumer)
    object.__setattr__(consumer, '_snapshot', c.owned(snapshot, limit=INPUT_LIMIT))
    # Complete bounded output checked before any consumer escapes admission.
    consumer.overview()
    return consumer


def render_lands(document):
    """Readable complete content; no evidence or counterevidence truncation."""
    value = document.to_dict()
    names = {key: card['card_identity']['name'] for key, card in value['context']['evidence']['cards'].items()}
    lines = ['MTG Lab — pending land mana and utility intelligence',
        'Review required; no human attestation; canonical admission false; execution BLOCKED.',
        'Plan: ' + value['plan_id'], 'Report: ' + value['report_id'], '']
    for assessed in value['assessments']:
        description = assessed['descriptive_readings']
        lines += [names[assessed['card_id']] + ' / ' + assessed['subject_id'],
            '  Classification: ' + assessed['classification']['overall_assessment'],
            '  Behavior: ' + assessed['behavior']['branch'],
            '  Complete written cost: ' + str(description['cost']['written_cost']),
            '  Written output: ' + description['output']['written_instruction'],
            '  Dependencies: ' + ', '.join(description['output']['dependencies']),
            '  Effect ownership: ' + description['effect_ownership']['state'],
            '  Composition: ' + assessed['additional_effect_composition']['status'],
            '  Unknowns: ' + ' '.join(assessed['remaining_unknowns']), '']
    for comparison in value['comparisons']:
        lines += ['Comparison: ' + comparison['name']]
        for difference in comparison['comparison']['differences']:
            lines.append('  ' + difference['dimension'] + ': ' + json.dumps(difference['values'], ensure_ascii=False))
        lines += ['  ' + constraint for constraint in comparison['comparison']['constraints']]
        lines.append('')
    lines += ['Complete evidence, pending readings, counterevidence and computed traces:',
        json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False), '']
    return '\n'.join(lines)
