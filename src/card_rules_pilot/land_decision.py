"""One append-only owner-supplied land decision over actual retained evidence.

This finite successor never rewrites the pending interpretations or their reports.
Its closed decision is explicit source material, not an approval service, signed
attestation, arbitrary approval flag, or executable gameplay admission.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from pathlib import Path

from . import contract as c
from .land import load_lands

DECISION_VERSION = 'card-rules-land-semantic-decision-v1'
REPORT_VERSION = 'card-rules-land-semantic-decision-report-v1'
OWNER_RECORD = 'owner-acceptance-v1.json'
DECISION_LIMIT = 524_288
REPORT_LIMIT = 524_288
DECISION_ID = 'sha256:648ebea0994f5d400664b35db6fcd5bcbc7feadeb0d28e039ecd55ed0c243075'
PLAN_ID = 'sha256:0f72e8aeed7b2d57a5ae4a562183233079c48170e69d5df5831a96b951e4fdd5'
COLLECTION_ID = 'sha256:73bbedd05ae01f4869cbf7aeed2c4f5f95d624a7c19a2f31d0bd4a106ac9fc7e'
MANIFEST_ID = 'sha256:243fd17c5ccedd3c0ad6bdeeb5f2769a45b55fe7a17e2003fe9b265c1cc5eed1'
CONTEXT_ID = 'sha256:59eb902055e8f597f9b0761ac176ad37406365c53a87098e3dcf621a1c5df478'
OVERVIEW_ID = 'sha256:b8cf0f67c6d1e22bf6d918d234213846af4f966ab86f0831082c0a23e1f362dd'
OVERVIEW_SHA256 = '0025ed0082783a9287ecb0dbd222fb5636ee3a07a862735c35b6c561c8ece515'
CANDIDATE_IDS = (
    ('snow-wastes-mana', 'sha256:7ce81b50485c09cb3ed789db287142253b55541c067d275f6750f1c9a2bc02e5'),
    ('port-mana', 'sha256:142af8b66263bb182396c134e4c9efb7b6f686be5097d875743d9e67c076748a'),
    ('port-utility', 'sha256:8dc9ba9f08113d9ee170efeadf7e4f21022e60f3e2a5694cfd088ad3657a66da'),
    ('city-mana', 'sha256:75a3a8dd76a16138dfbd8528d2680109e3f9ca542538df6b0fe6298a63e84148'),
    ('city-damage-trigger', 'sha256:0a66c251fedc138c584b64ba80b36dcf1c59ba5ae34010a45c7909dfdce658e4'),
    ('citadel-colorless', 'sha256:9df44dd22515ca823e3b65d3e56160b2bb6b1e756e5c691daa234cba744db013'),
    ('citadel-color-choice', 'sha256:83aa0a956dd278b5362466b29664874ece949dbf6f32cf74b9777bcf47d954c1'),
    ('coffers-mana', 'sha256:408822dc3b1df68991360cc87046c00d6c17851a491db95194208cac1eb6af48'),
    ('tower-mana', 'sha256:2073df2b692f1deccc77f14a9fd85665fa805b8cff62ca92b40424f0aa78adbc'),
)
SUBJECT_IDS = tuple(sid for sid, _ in CANDIDATE_IDS)
OWNER_STATEMENT = (
    'The project owner explicitly approved all nine land interpretation candidates in collection:\n\n'
    + COLLECTION_ID + '\n\n'
    'The approval applies strictly to their bounded historical retained-text interpretations '
    'and documented limitations. The Senior PM separately recommended acceptance of all nine.')
ACCEPTED_SCOPE = (
    'Complete owned ability passages.',
    'Proposed activated/triggered classifications within the documented retained-text scope.',
    'Applicable criterion readings and method assessments.',
    'Separate ability and additional-effect ownership.',
    'Written costs, conditions, and output dependencies.',
    'Conditional behavior conclusions supported by the existing evidence.',
)
EXCLUDED_SCOPE = (
    'Current Oracle verification.', 'Arbitrary game-state legality.',
    'Current activation eligibility.', 'Actual mana production.', 'Payment feasibility.',
    'Trigger occurrence or resolution.', 'Complete stack or priority execution.',
    'Canonical executable CardGameplaySemantics.', 'A general Card parser or automatic classifier.',
    'Permission for source retention, redistribution, services, or AI export.',
    'Approval of the earlier seven-subject pilot or any unrelated interpretation.',
    'Resolution of changed text, gained abilities, copies, external effects, or arbitrary game states.',
)


def _boundaries():
    return {'canonical_admission': False, 'execution_authority': 'BLOCKED',
        'canonical_executable_card_gameplay_semantics': False,
        'semantic_closure': 'OPEN',
        'all_ten_activation_responsibilities': 'OPEN / EXECUTION_BLOCKED',
        'source_policy_clearance': 'not_granted',
        'permissions': {name: 'NOT_ESTABLISHED' for name in (
            'private_retention', 'redistribution', 'free_service', 'commercial_service', 'ai_export')},
        'tier_a_restrictions': 'UNCHANGED_NON_PRODUCTION',
        'new_source_units': 0, 'new_projections': 0,
        'global_source_units': 104, 'global_projections': 16, 'land_context_units': 24,
        'fresh_source_inspection_allowlist': [], 'new_source_projection_allowlist': [],
        'fresh_oracle_verification': False, 'fresh_cr_txt_verification': False}


def _verify_original(overview):
    """Reproduce owning identities and the pinned complete historical result.

    Only load_land_decision passes actual publicly admitted evidence here. A
    dictionary and matching digest are not a public evidence-admission route.
    """
    raw = c.owned(overview)
    if (len(raw) != 689_253 or hashlib.sha256(raw).hexdigest() != OVERVIEW_SHA256
            or overview.get('report_id') != OVERVIEW_ID
            or c.identity(overview['schema_version'], overview, 'report_id') != OVERVIEW_ID):
        raise c.PilotError('exact original admitted land overview required')
    context = overview['context']
    for name, own, expected in (
            ('plan', 'plan_id', PLAN_ID), ('interpretations', 'interpretations_id', COLLECTION_ID),
            ('manifest', 'manifest_id', MANIFEST_ID), ('retained_rules', 'context_id', CONTEXT_ID)):
        value = context[name]
        if value[own] != expected or c.identity(value['schema_version'], value, own) != expected:
            raise c.PilotError('original land owning identity mismatch')
    candidates = context['interpretations']['candidates']
    if tuple((row['subject']['subject_id'], row['candidate_id']) for row in candidates) != CANDIDATE_IDS:
        raise c.PilotError('exact approved nine-candidate membership required')
    for candidate in candidates:
        if c.identity(candidate['schema_version'], candidate, 'candidate_id') != candidate['candidate_id']:
            raise c.PilotError('original candidate identity mismatch')
        c.exact(candidate['review'], {'status': 'requires_review',
            'human_attestation': None, 'canonical_admission': False})
        if (candidate['semantic_review_status'] != 'PENDING_NOT_ESTABLISHED'
                or candidate['execution_authority'] != 'BLOCKED'):
            raise c.PilotError('historical pending candidate was changed')
    return context


def _original_result(assessed):
    return {'assessment_id': assessed['assessment_id'],
        'classification_canonical_sha256': hashlib.sha256(c.canonical(assessed['classification'])).hexdigest(),
        'behavior_calculation_id': assessed['behavior']['calculation_id'],
        'composition_id': assessed['additional_effect_composition']['composition_id'],
        'classification': assessed['classification']['overall_assessment'],
        'negative_witnesses': assessed['classification']['negative_witnesses'],
        'behavior_branch': assessed['behavior']['branch'],
        'additional_effect_status': assessed['additional_effect_composition']['status']}


def _record(overview):
    """Closed reproduction of this one supplied decision; no approval arguments."""
    context = _verify_original(overview)
    return c.seal(DECISION_VERSION, {'schema_version': DECISION_VERSION,
        'record_kind': 'APPEND_ONLY_OWNER_SUPPLIED_LAND_SEMANTIC_DECISION',
        'record_policy': 'IMMUTABLE_FIRST_RECORD_NO_OVERWRITE_OR_AMENDMENT_API',
        'sequence': 1, 'previous_decision_id': None,
        'replaces_historical_candidates': False,
        'decision': {'status': 'ACCEPTED_BOUNDED_RETAINED_TEXT',
            'source': 'EXPLICIT_OWNER_SUPPLIED_INSTRUCTION',
            'owner_supplied_statement': OWNER_STATEMENT,
            'authenticated_account_identity': None, 'authenticated_signature': None,
            'decision_timestamp': None, 'separate_human_attestation_event': None},
        'preceding_pm_recommendation': {
            'recommendation': 'ACCEPT_ALL_NINE_WITHIN_BOUNDED_HISTORICAL_RETAINED_TEXT_SCOPE',
            'source': 'OWNER_REPORTED_PRECEDING_INDEPENDENT_SENIOR_PM_RECOMMENDATION',
            'independently_authenticated_evidence': None,
            'authenticated_account_identity': None, 'recommendation_timestamp': None},
        'approved_collection_id': COLLECTION_ID, 'plan_id': PLAN_ID,
        'manifest_id': MANIFEST_ID, 'context_id': CONTEXT_ID,
        'scope': {'historical_retained_text_only': True,
            'accepted': list(ACCEPTED_SCOPE), 'not_established': list(EXCLUDED_SCOPE),
            'external_context_questions_remain_unresolved': True},
        # Complete copies bind every original criterion, absence scope,
        # counterevidence, provenance, limitation and unresolved question. Their
        # own pending identities and statuses remain historically accurate.
        'candidates': context['interpretations']['candidates'],
        'retained_card_evidence': context['evidence'],
        'retained_cr_context': context['retained_rules'],
        'original_reports': {'overview': {'report_id': OVERVIEW_ID,
            'bytes': 689_253, 'sha256': OVERVIEW_SHA256},
            'assessments': [{ 'subject_id': row['subject_id'], **_original_result(row)}
                for row in overview['assessments']],
            'comparisons': [{'name': row['name'],
                'comparison_id': row['comparison']['comparison_id']}
                for row in overview['comparisons']]},
        'historical_records_preserved': {'semantic_review_status': 'PENDING_NOT_ESTABLISHED',
            'review': {'status': 'requires_review', 'human_attestation': None,
                'canonical_admission': False}, 'execution_authority': 'BLOCKED',
            'original_json_bytes_and_identities_unchanged': True,
            'computed_results_unchanged': True},
        'boundaries': _boundaries()}, 'decision_id')


@dataclass(frozen=True, init=False)
class LandDecisionConsumer:
    _overview: bytes
    _decision: bytes

    @property
    def subject_ids(self):
        return SUBJECT_IDS

    def validate_record(self, value):
        """Exact decision/evidence reproduction; rehashing a change cannot pass."""
        value = json.loads(c.owned(value, limit=DECISION_LIMIT))
        if (type(value) is not dict or value.get('schema_version') != DECISION_VERSION
                or value.get('decision_id') != DECISION_ID
                or c.identity(DECISION_VERSION, value, 'decision_id') != DECISION_ID):
            raise c.PilotError('exact immutable owner decision identity required')
        expected = _record(json.loads(self._overview))
        c.exact(value, expected, limit=DECISION_LIMIT)
        return c.ReviewDocument._verified(expected, limit=DECISION_LIMIT)

    def historical_overview(self):
        """The original report retains its original pending authority and bytes."""
        return c.ReviewDocument._verified(json.loads(self._overview), limit=1_048_576)

    def _report(self, kind, selector=None):
        if kind == 'subject':
            if type(selector) is not str or selector not in SUBJECT_IDS:
                raise c.PilotError('foreign land decision subject')
            selected = (selector,)
        elif kind in ('summary', 'integrity') and selector is None:
            selected = SUBJECT_IDS
        else:
            raise c.PilotError('closed land decision report selection required')
        overview, decision = json.loads(self._overview), json.loads(self._decision)
        context = overview['context']
        assessed = {row['subject_id']: row for row in overview['assessments']}
        rows = []
        for candidate in decision['candidates']:
            sid = candidate['subject']['subject_id']
            if sid not in selected:
                continue
            result = assessed[sid]
            rows.append({'subject_id': sid, 'candidate_id': candidate['candidate_id'],
                'card': context['evidence']['cards'][candidate['subject']['card_id']]['card_identity'],
                'source_binding': candidate['source_binding'], 'subject': candidate['subject'],
                'proposed_kind': candidate['proposed_kind'], 'criteria': candidate['criteria'],
                'written_readings': candidate['descriptive_readings'],
                'counterevidence': candidate['counterevidence'],
                'historical_semantic_review_status': candidate['semantic_review_status'],
                'historical_review': candidate['review'],
                'current_decision_status': decision['decision']['status'],
                'resolved_through_decision_id': decision['decision_id'],
                'original_result': _original_result(result),
                'conditional_conclusions': [{key: consequence[key] for key in (
                    'consequence_id', 'antecedents', 'conditional_consequence',
                    'remaining_unknowns', 'rule_refs')}
                    for consequence in result['behavior']['consequences']],
                'additional_effect_relationship': result['additional_effect_composition']['conditional_relationship'],
                'remaining_unknowns': candidate['unresolved'],
                'limitations': candidate['limitations'],
                'canonical_admission': False, 'execution_authority': 'BLOCKED'})
        return c.ReviewDocument._verified(c.seal(REPORT_VERSION, {
            'schema_version': REPORT_VERSION, 'kind': kind, 'selector': selector,
            'decision_id': decision['decision_id'],
            'decision_status': decision['decision']['status'],
            'decision_provenance': decision['decision'],
            'preceding_pm_recommendation': decision['preceding_pm_recommendation'],
            'scope': decision['scope'], 'approved_collection_id': COLLECTION_ID,
            'plan_id': PLAN_ID, 'manifest_id': MANIFEST_ID, 'context_id': CONTEXT_ID,
            'subject_count': len(rows), 'approved_candidate_count': 9,
            'subjects': rows, 'original_reports': decision['original_reports'],
            'historical_semantic_review_status': 'PENDING_NOT_ESTABLISHED',
            'historical_records_preserved': decision['historical_records_preserved'],
            'boundaries': decision['boundaries'],
            'integrity_is_not_the_source_of_owner_acceptance': True}, 'report_id'), limit=REPORT_LIMIT)

    def summary(self):
        return self._report('summary')

    def subject(self, subject_id):
        return self._report('subject', subject_id)

    def candidate(self, candidate_id):
        if type(candidate_id) is not str:
            raise c.PilotError('exact accepted candidate identity required')
        for subject_id, expected in CANDIDATE_IDS:
            if candidate_id == expected:
                return self.subject(subject_id)
        raise c.PilotError('foreign land decision candidate')

    def check(self):
        return self._report('integrity')

    def validate_report(self, value):
        value = json.loads(c.owned(value, limit=REPORT_LIMIT))
        if type(value) is not dict or type(value.get('kind')) is not str:
            raise c.PilotError('complete land decision report required')
        expected = self._report(value['kind'], value.get('selector'))
        c.exact(value, expected.to_dict(), limit=REPORT_LIMIT)
        return expected


def load_land_decision(*, catalog_root, mechanical_root, review_root, cohort_root,
        decision_root, expected_profile_id, expected_query_snapshot_id,
        expected_plan_id, expected_decision_id):
    """One actual public land admission, then this fixed immutable decision.

    Incompatible current catalogs reject. Neither a historical fixture nor an
    imported report can replace current retained evidence admission.
    """
    if type(expected_decision_id) is not str or expected_decision_id != DECISION_ID:
        raise c.PilotError('independent exact owner decision identity required')
    lands = load_lands(catalog_root=catalog_root, mechanical_root=mechanical_root,
        review_root=review_root, cohort_root=cohort_root,
        expected_profile_id=expected_profile_id,
        expected_query_snapshot_id=expected_query_snapshot_id,
        expected_plan_id=expected_plan_id)
    overview = lands.overview()
    _verify_original(overview.to_dict())
    root = Path(decision_root)
    if (root.is_symlink() or not root.is_dir()
            or {path.name for path in root.iterdir()} != {OWNER_RECORD}):
        raise c.PilotError('exact finite append-only owner decision file set required')
    decision = c.read_json(root / OWNER_RECORD, limit=DECISION_LIMIT)
    consumer = object.__new__(LandDecisionConsumer)
    object.__setattr__(consumer, '_overview', overview.to_json().encode('utf-8'))
    object.__setattr__(consumer, '_decision', c.owned(decision, limit=DECISION_LIMIT))
    consumer.validate_record(decision)
    consumer.summary()
    return consumer


def render_land_decision(document):
    """Readable decision summary keeps accepted scope and limitations together."""
    value = document.to_dict()
    lines = ['MTG Lab — owner-supplied land semantic decision',
        'Current decision: ' + value['decision_status'],
        'Decision: ' + value['decision_id'], 'Report: ' + value['report_id'],
        'Historical interpretations remain PENDING_NOT_ESTABLISHED / requires_review; historical human_attestation=null.',
        'Owner-supplied decision; no authenticated account, signature, decision timestamp or separate attestation event.',
        'Preceding PM recommendation: owner-reported independent acceptance of all nine.',
        'Original pending lifecycle statements below describe preserved historical records; current bounded acceptance is separate.',
        'All retained evidence limits and unresolved external-context limitations continue to apply.',
        'Canonical admission=false; real gameplay execution=BLOCKED.', '',
        'Exact supplied owner statement:', value['decision_provenance']['owner_supplied_statement'], '',
        'Accepted scope:', *['  ' + item for item in value['scope']['accepted']],
        'Not established:', *['  ' + item for item in value['scope']['not_established']], '']
    for row in value['subjects']:
        lines += [row['card']['name'] + ' / ' + row['subject_id'],
            '  Candidate: ' + row['candidate_id'],
            '  Complete owned passage: ' + row['subject']['selected_passage'],
            '  Decision: ' + row['current_decision_status'],
            '  Original conditional classification: ' + row['original_result']['classification'],
            '  Original behavior: ' + row['original_result']['behavior_branch'],
            '  Effect composition: ' + row['original_result']['additional_effect_status'],
            '  Remaining unknowns: ' + ' '.join(row['remaining_unknowns'])]
        lines += ['  Original retained limitation: ' + item for item in row['limitations']]
        lines.append('')
    lines += ['Source policy clearance=not_granted; private retention, redistribution, free service, commercial service and AI export=NOT_ESTABLISHED.',
        'Tier A non-production restrictions unchanged. Coverage=104 units / 16 projections; land context=24 existing units; new units/projections=0.',
        'Semantic closure OPEN; all ten activation responsibilities OPEN / EXECUTION_BLOCKED.',
        'Canonical JSON exposes all retained criterion readings, source bindings, counterevidence and conditional antecedents.', '']
    return '\n'.join(lines)
