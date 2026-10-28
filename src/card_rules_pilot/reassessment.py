"""Five fixed source-backed pending reassessments; append-only, read-only consumer.

This contract owns a separately versioned input. The original pilot and closed
reasoning policy never accept successor content. The adapter supplies the same
original twelve criterion IDs and bindings, with only the explicitly reviewed
primary state changed. No text recognition or arbitrary override API exists.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from pathlib import Path

from .contract import PilotError, ReviewDocument, canonical, owned, exact, seal, read_json
from .pilot import load_pilot, InterpretationReviewPilot
from . import reasoning_policy as policy
from .reasoning import _inputs

INPUT_VERSION = 'card-rules-mana-context-reassessment-input-v1'
REASSESSMENT_VERSION = 'card-rules-mana-context-pending-reassessment-v1'
MANIFEST_VERSION = 'card-rules-mana-context-reassessment-manifest-v1'
REPORT_VERSION = 'card-rules-mana-context-before-after-v1'
ANALYSIS_VERSION = 'card-rules-mana-context-consequence-v1'
CHECK_VERSION = 'card-rules-mana-context-integrity-v1'
INPUT_LIMIT = 131_072
REPORT_LIMIT = 1_048_576
PREPARED_AT = '2026-10-28T00:00:00Z'
PACKAGE_NAME = 'gameplay-rules-mana-classification-source-context'
SUBJECTS = ('sol-ring-tap', 'basalt-monolith-tap', 'basalt-monolith-untap',
            'deathrite-shaman-first', 'mana-flare-trigger')
_AUTHORITY = canonical({
    'authority': 'SOURCE_BACKED_ENGINEER_AUTHORED_PENDING_REASSESSMENT_ONLY',
    'semantic_review_status': 'PENDING_NOT_ESTABLISHED',
    'review': {'status': 'requires_review', 'human_attestation': None, 'canonical_admission': False},
    'execution_authority': 'BLOCKED',
})
LIMITATIONS = (
    'Authored interpretation is supported by structured source context; it is not verbatim CR content or an official Card ruling.',
    'The four method proposals narrow assessment to complete retained Card text. Universal formal self-replacement semantics remain unknown.',
    'Gained abilities, text changes, copy effects, external modifiers and every possible game state are outside this bounded reading.',
    'No event detection, actual trigger occurrence, actual output, ordering application, activation, cost payment or resolution executes.',
    'Source verification, code review, successful tests and merge do not establish semantic approval or canonical admission.',
)


def _authority():
    return json.loads(_AUTHORITY)


# Authored arguments concern exact retained passages, not substring heuristics.
_ARGUMENTS = {
    'sol-ring-tap': {
        'question': 'Can the self-replacement assessment be completed for the complete retained Sol Ring tap ability and its whole retained Card text?',
        'context_argument': 'The whole retained field consists of one activation: tapping the host pays its cost and the effect adds two colorless mana. Its cost and its output are distinct. There is no separate retained instruction that changes part or all of this resolving ability\'s own effect. This is an authored reading of that entire cost/effect structure, not a test for a missing word or annotation.',
        'counterevidence': 'Even this simple retained text does not describe gained abilities, text-changing effects or all external states. Its apparent simplicity cannot establish universal absence of self-replacement.',
        'rechecks': {
            'activated_kind': 'The whole selected cost/effect remains one tap-cost activation; completing the bounded method introduces no other ability.',
            'no_target': 'The whole selected effect instructs mana addition for the activating player; it does not designate any target. This authored whole-passage reading retains the no-target proposal.',
            'potential_mana': 'The selected effect adds two colorless mana; no retained text revises that effect into a different own effect under 614.15. Potential production remains proposed satisfied, without actual output.',
            'not_loyalty': 'The entire cost is tapping the host, not a loyalty-symbol cost; retained 606.1 and 606.2 remain the classification context.',
            'no_library_cost_movement': 'The full cost is tapping the host; it performs no library transfer under this authored reading.',
            'no_library_effect_movement': 'The full effect adds mana; the retained whole-Card review identifies no own-effect revision into a library transfer.',
        },
    },
    'basalt-monolith-tap': {
        'question': 'Can the self-replacement assessment be completed for Basalt Monolith\'s selected tap activation while accounting for both other retained instructions?',
        'context_argument': 'The selected activation taps the artifact and adds three colorless mana. The surrounding static restriction concerns untapping during the untap step. The separate paid activation pays three mana to untap this artifact. On this authored reading neither surrounding instruction replaces any part of the selected tap activation\'s resolving mana-addition effect. The static restriction is considered because 614.15 permits separate-ability text; it is not ignored merely for being outside the selected line.',
        'counterevidence': 'The untap restriction is meaningful surrounding text and must not be treated as blank context. This assessment does not decide every interaction involving untapping, a gained ability or external modifiers.',
        'rechecks': {
            'activated_kind': 'The selected tap-cost activation remains separate from the paid untap activation and the static untap-step restriction.',
            'no_target': 'The whole selected tap/add instruction does not designate a target; reviewing the two other instructions does not add a target to it.',
            'potential_mana': 'The selected activation potentially adds three colorless mana. The paid untap ability and untap-step restriction do not replace this own effect in the retained-text assessment.',
            'not_loyalty': 'The selected cost taps the artifact; its complete cost is not a loyalty-symbol cost.',
            'no_library_cost_movement': 'The selected whole cost taps the artifact, without a library transfer.',
            'no_library_effect_movement': 'The selected whole effect adds mana; neither separately retained instruction revises that own effect into a library transfer.',
        },
    },
    'basalt-monolith-untap': {
        'question': 'Can the self-replacement assessment be completed for Basalt Monolith\'s paid untap activation without borrowing its separate mana-producing activation?',
        'context_argument': 'The selected activation pays three mana and untaps this artifact. The other activation taps it to add three colorless mana and remains a separate ability. The static restriction concerns the untap step, whereas the selected effect is an instruction to untap during its own resolution. Neither surrounding instruction is read as replacing part or all of the selected resolving untap effect. This accounts for the separate-ability possibility in 614.15 rather than discarding the static restriction by position.',
        'counterevidence': 'The same Card also has mana production, and the static untap restriction cannot be silently discarded. Neither fact supplies potential mana production to this selected untap effect; no repeatable sequence or legality conclusion is assessed.',
        'rechecks': {
            'activated_kind': 'The full selected mana-payment/untap passage remains its own activation, distinct from tapping for mana.',
            'no_target': 'The entire selected effect identifies this artifact for untapping, not a target requirement; the retained-text reading remains proposed satisfied.',
            'potential_mana': 'Paying three mana is its cost, and its own resolving effect untaps. The full-Card self-replacement review does not transform that effect into mana production or borrow the other activation. The negative reading remains.',
            'not_loyalty': 'The full selected cost pays three mana rather than loyalty symbols.',
            'no_library_cost_movement': 'The complete selected cost pays mana, without a library transfer.',
            'no_library_effect_movement': 'The complete selected effect untaps this artifact, with no retained own-effect revision into a library transfer.',
        },
    },
    'deathrite-shaman-first': {
        'question': 'Can the self-replacement assessment be completed for Deathrite Shaman\'s complete first activation, including exile and mana addition, while considering both other abilities?',
        'context_argument': 'The complete first activation taps the host, exiles a target land card from a graveyard, and adds one mana of any color. Both later abilities have their own costs and targeted graveyard-exile instructions: one causes each opponent to lose life, the other gains life for its controller. In this whole-field authored reading they neither condition nor replace part of the first activation\'s own resolving exile/mana effects. They are inspected as possible separate-ability context under 614.15, without classifying either as a new subject.',
        'counterevidence': 'The first ability has both a targeted exile instruction and mana addition. The target requirement cannot be erased by the mana clause or by method completion; the other abilities cannot be used as effects of this selected subject.',
        'rechecks': {
            'activated_kind': 'The complete first cost/effect remains a single tap-cost activation containing both targeted exile and mana addition.',
            'no_target': 'The first ability requires a target land card from a graveyard. Whole-field self-replacement review removes no such requirement; the negative reading remains independently of chosen-target count.',
            'potential_mana': 'The complete first ability retains its mana-addition instruction after exile. No retained separate text replaces its own output. Potential production remains proposed satisfied without target legality or actual output.',
            'not_loyalty': 'The whole selected cost taps the host rather than paying loyalty symbols.',
            'no_library_cost_movement': 'The entire cost is tapping; targeted exile belongs to the effect, not the cost.',
            'no_library_effect_movement': 'Both the targeted graveyard-to-exile instruction and the mana addition are retained. The graveyard source is not a library, and no retained own-effect revision creates a library transfer.',
        },
    },
    'mana-flare-trigger': {
        'question': 'Does the exact retained taps-a-land-for-mana trigger wording support one of 605.1b\'s qualifying relationships under newly verified 106.12 and 106.12a?',
        'context_argument': 'The complete retained trigger begins whenever a player taps a land for mana and then instructs that player to add one mana of a type the land produced. Under 106.12, tapping that land for mana denotes activation of a mana ability of it with a tap-symbol cost. Under 106.12a, this trigger wording relates to that mana ability resolving and producing mana. Together these support the resolution-of-an-activated-mana-ability alternative retained in 605.1b. This is a semantic interpretation supported by context, not a literal citation from 605.1b to 106.12. It needs no invented concrete land instance or event to express that conditional relationship.',
        'counterevidence': 'The selected words alone originally left activation versus resolution unresolved. New 106.12a supports the resolution-and-production relationship, not a trigger for every activation regardless of production. 106.12b instead concerns replacement effects and must not be substituted for the triggered context. Mana mentioned in an effect alone would not establish this relationship.',
        'rechecks': {
            'triggered_kind': 'The whole whenever/event/effect passage remains a proposed host-owned triggered ability.',
            'trigger_no_target': 'The full event and output identify the player and land by their relationship; this authored whole-passage reading identifies no target designation.',
            'trigger_potential_mana': 'The selected effect adds one mana of a type the land produced. 106.12a supplies a production-qualified relationship; no output amount, concrete type or actual resolution is computed.',
        },
    },
}


def _record(candidate, package):
    sid = candidate['subject']['subject_id']
    argument = _ARGUMENTS[sid]
    primary = 'qualifying_trigger_relationship' if sid == 'mana-flare-trigger' else 'self_replacement_considered'
    original = next(r for r in candidate['authored_interpretation']['criteria'] if r['criterion_id'] == primary)
    references = ['106.12', '106.12a', '106.12b'] if sid == 'mana-flare-trigger' else ['614.15']
    projection = package['projection.json']
    source_refs = [{key: rule[key] for key in ('rule_reference', 'rule_id', 'source_anchor')}
                   for rule in projection['rules'] if rule['rule_reference'] in references]
    if len(source_refs) != len(references):
        raise PilotError('complete fixed source support required')
    rechecks = []
    for row in candidate['authored_interpretation']['criteria']:
        identifier = row['criterion_id']
        state = 'proposed_satisfied' if identifier == primary else row['state']
        rationale = ('The inactive criterion family remains inapplicable to the unchanged proposed kind; it supplies no successful substantive premise or activated assessment method.' if row['state'] == 'inapplicable' else
                     argument['context_argument'] if identifier == primary else
                     argument['rechecks'].get(identifier) or
                     ('Other replacement effects are disregarded for this classification assessment as 605.1a requires. The own-effect review under 614.15 does not admit external replacements or implement their ordering.'
                      if identifier == 'other_replacements_disregarded' else
                      'The inactive criterion family remains inapplicable to the unchanged proposed kind; it supplies no successful substantive premise.'))
        rechecks.append({'criterion_id': identifier, 'original_state': row['state'],
            'proposed_state': state, 'rationale': rationale,
            'original_evidence_refs': row['evidence_refs'],
            'source_support_refs': references if identifier == primary else [],
            'state_changed': state != row['state']})
    is_method = primary == 'self_replacement_considered'
    body = {
        'schema_version': REASSESSMENT_VERSION, 'prepared_at': PREPARED_AT,
        'record_kind': 'NEW_SOURCE_BACKED_PENDING_REASSESSMENT',
        'original_plan_id': candidate['plan_id'], 'original_candidate_id': candidate['candidate_id'],
        'subject_id': sid, 'original_subject': candidate['subject'],
        'original_criterion': original,
        'card_evidence_binding': candidate['card_evidence'],
        'original_counterevidence': candidate['authored_interpretation']['counterevidence'],
        'source_package_id': package['manifest.json']['package_id'],
        'source_projection_id': projection['projection_id'], 'source_binding': projection['source_binding'],
        'new_source_support': source_refs,
        'historical_context_count': 17, 'enriched_context_count': 21,
        'assessment_question': argument['question'],
        'scope_change': ('NARROWED_TO_COMPLETE_RETAINED_CARD_TEXT' if is_method else 'CLARIFIED_RETAINED_TRIGGER_WORDING_RELATIONSHIP_ONLY'),
        'scope_explanation': ('The original unknown concerns complete formal semantics and external state. This successor proposes only completion of an authored whole-retained-Card-text assessment. It does not resolve the original universal question.' if is_method else 'The proposed reading relates the retained trigger wording to a qualifying category of event. Whether any event occurs and any concrete ability qualifies in a game remains unassessed.'),
        'universal_question_remaining_unknown': True,
        'added_context_contribution': ('614.15 distinguishes replacement of the resolving ability\'s own effects, including text in separate abilities, from continuous effects and places self-replacement before other replacements. It supplies the assessment question, not an automatic absence finding or an implemented recognizer.' if is_method else '106.12 defines the tap-for-mana relationship to an activated mana ability; 106.12a supplies resolution plus production for the trigger wording, while 106.12b keeps the replacement context distinct.'),
        'proposed_state': 'proposed_satisfied',
        'candidate_specific_rationale': argument['context_argument'],
        'counterevidence': argument['counterevidence'],
        'rechecked_criteria': rechecks,
        'associated_state_changes': [],
        'associated_revision_explanation': 'All applicable substantive readings and the other-replacement method were rechecked against the complete retained passage and surrounding Card text. No additional state change is justified within this retained-text scope.' if is_method else 'The other three triggered substantive readings were rechecked. No associated state change is justified; activated criteria remain inapplicable.',
        'hypothetical_cases_used_as_evidence': False,
        'assumptions_and_limitations': list(LIMITATIONS),
        'successor_acceptance': 'PROPOSED_ONLY_NOT_AUTOMATICALLY_ACCEPTED',
        **_authority(),
    }
    return seal(REASSESSMENT_VERSION, body, 'reassessment_id')


def _input(original, package):
    candidates = {c['subject']['subject_id']: c for c in original['candidates']}
    body = {'schema_version': INPUT_VERSION, 'prepared_at': PREPARED_AT,
        'original_plan_id': original['plan_id'], 'original_comparison_id': original['report_id'],
        'policy_id': policy.POLICY_ID, 'source_package_id': package['manifest.json']['package_id'],
        'source_projection_id': package['projection.json']['projection_id'],
        'historical_input_mutated': False, 'automatic_successor_acceptance': False,
        'reassessments': [_record(candidates[sid], package) for sid in SUBJECTS],
        'unchanged_controls': [{'subject_id': sid, 'original_candidate_id': c['candidate_id'],
            'input_relationship': 'UNCHANGED_ORIGINAL_IDENTITY_NO_REISSUED_INTERPRETATION'}
            for sid, c in candidates.items() if sid not in SUBJECTS],
        **_authority()}
    return seal(INPUT_VERSION, body, 'input_id')


def _manifest(value):
    raw = owned(value, limit=INPUT_LIMIT)
    return seal(MANIFEST_VERSION, {'schema_version': MANIFEST_VERSION,
        'input_id': value['input_id'], 'source_package_id': value['source_package_id'],
        'original_plan_id': value['original_plan_id'],
        'reassessment_ids': [r['reassessment_id'] for r in value['reassessments']],
        'files': {'reassessments.json': {'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}},
        **_authority()}, 'manifest_id')


class ReassessmentDocument(ReviewDocument):
    """Immutable canonical view; decoded values are independent."""


def _document(value, limit=REPORT_LIMIT):
    return ReassessmentDocument._verified(value, limit=limit)


def _adapt(candidate, record):
    """Finite adapter into the unchanged PR #217 policy, never into its loader."""
    inputs = _inputs(candidate)
    if record is not None:
        # The caller only obtains this record from the privately verified input.
        if (record['original_candidate_id'] != candidate['candidate_id'] or
                record['subject_id'] != candidate['subject']['subject_id']):
            raise PilotError('foreign successor parent binding')
        primary = record['original_criterion']['criterion_id']
        for row in inputs['criteria']:
            if row['criterion_id'] == primary:
                row['state'] = record['proposed_state']
    return policy.compute(**inputs)


def _row(candidate, record):
    before = _adapt(candidate, None)
    after = _adapt(candidate, record)
    return seal(ANALYSIS_VERSION, {'schema_version': ANALYSIS_VERSION,
        'subject_id': candidate['subject']['subject_id'],
        'original_candidate_id': candidate['candidate_id'],
        'interpretation_input_id': record['reassessment_id'] if record else candidate['candidate_id'],
        'input_kind': 'SOURCE_BACKED_PENDING_REASSESSMENT' if record else 'UNCHANGED_ORIGINAL_PENDING_INTERPRETATION',
        'original_readings': candidate['authored_interpretation']['criteria'],
        'proposed_changes': ([{'criterion_id': record['original_criterion']['criterion_id'],
            'original_state': record['original_criterion']['state'], 'proposed_state': record['proposed_state']}]
            if record else []),
        'source_support': record['new_source_support'] if record else [],
        'reassessment_id': record['reassessment_id'] if record else None,
        'scope_change': record['scope_change'] if record else 'UNCHANGED_ORIGINAL_SCOPE',
        'universal_question_remaining_unknown': True,
        'before': before, 'after': after,
        'interpretation_accepted': False, 'limitations': list(LIMITATIONS), **_authority()}, 'analysis_id')


@dataclass(frozen=True, init=False)
class ManaContextReassessment:
    """Privately owned admitted historical pilot, source package and successor."""
    _raw: bytes

    def _material(self):
        return json.loads(self._raw)

    @property
    def subject_ids(self):
        return tuple(c['subject']['subject_id'] for c in self._material()['original']['candidates'])

    def input_document(self):
        return _document(self._material()['input'], INPUT_LIMIT)

    def subject(self, subject_id):
        if type(subject_id) is not str or subject_id not in self.subject_ids:
            raise PilotError('exact original seven-subject identity required')
        material = self._material()
        candidate = next(c for c in material['original']['candidates'] if c['subject']['subject_id'] == subject_id)
        record = next((r for r in material['input']['reassessments'] if r['subject_id'] == subject_id), None)
        return _document(seal(REPORT_VERSION, {'schema_version': REPORT_VERSION,
            'input_id': material['input']['input_id'], 'policy_id': policy.POLICY_ID,
            'context': {'original_candidate': candidate, 'source_package': material['source']},
            'reassessments': [record] if record else [], 'comparisons': [_row(candidate, record)],
            'limitations': list(LIMITATIONS), **_authority()}, 'report_id'))

    def comparison(self):
        material = self._material()
        records = {r['subject_id']: r for r in material['input']['reassessments']}
        return _document(seal(REPORT_VERSION, {'schema_version': REPORT_VERSION,
            'input_id': material['input']['input_id'], 'policy_id': policy.POLICY_ID,
            'context': {'original_comparison': material['original'], 'source_package': material['source']},
            'reassessments': material['input']['reassessments'],
            'comparisons': [_row(c, records.get(c['subject']['subject_id'])) for c in material['original']['candidates']],
            'limitations': list(LIMITATIONS), **_authority()}, 'report_id'))

    def validate_reassessment(self, value):
        value = json.loads(owned(value, limit=INPUT_LIMIT))
        try:
            sid = value['subject_id']
            expected = next(r for r in self._material()['input']['reassessments'] if r['subject_id'] == sid)
        except (KeyError, StopIteration, TypeError):
            raise PilotError('one of five fixed reassessment records required') from None
        exact(value, expected, limit=INPUT_LIMIT)
        return _document(expected, INPUT_LIMIT)

    def validate_report(self, value):
        value = json.loads(owned(value, limit=REPORT_LIMIT))
        try:
            comparisons = value['comparisons']
            expected = self.comparison() if len(comparisons) == 7 else self.subject(comparisons[0]['subject_id'])
        except (KeyError, TypeError, IndexError):
            raise PilotError('complete seven-subject or individual report required') from None
        exact(value, expected.to_dict(), limit=REPORT_LIMIT)
        return expected

    def check(self):
        m = self._material()
        return _document(seal(CHECK_VERSION, {'schema_version': CHECK_VERSION,
            'check': 'EXACT_OFFLINE_REPRODUCTION_NOT_FRESH_SOURCE_VERIFICATION',
            'input_id': m['input']['input_id'], 'manifest_id': m['manifest']['manifest_id'],
            'source_package_id': m['input']['source_package_id'],
            'reassessment_count': 5, 'subject_count': 7,
            'original_comparison_id': m['original']['report_id'],
            'source_body_retained': False, **_authority()}, 'report_id'))


def _from_pilot(pilot, *, review_root, successor_root=None):
    from gameplay_rules.projection.mana_context_package import load_package
    package = load_package(Path(review_root) / PACKAGE_NAME, review_root=review_root).to_dict()
    original = pilot.comparison().to_dict()
    expected = _input(original, package)
    directory = Path(successor_root) if successor_root is not None else Path(__file__).resolve().parents[2] / 'data/review/mana-context-reassessment'
    value = read_json(directory / 'reassessments.json', limit=INPUT_LIMIT)
    exact(value, expected, limit=INPUT_LIMIT)
    manifest = read_json(directory / 'manifest.json', limit=INPUT_LIMIT)
    exact(manifest, _manifest(expected), limit=INPUT_LIMIT)
    if {p.name for p in directory.iterdir()} != {'reassessments.json', 'manifest.json'}:
        raise PilotError('exact two-file successor package required')
    instance = object.__new__(ManaContextReassessment)
    object.__setattr__(instance, '_raw', owned({'original': original, 'source': package,
        'input': value, 'manifest': manifest}, limit=REPORT_LIMIT))
    instance.comparison()  # Check cumulative output bound before exposing a partial view.
    return instance


def load_reassessment(*, catalog_root, mechanical_root, review_root, plan_path,
                      expected_profile_id, expected_query_snapshot_id, expected_plan_id,
                      successor_root=None):
    pilot = load_pilot(catalog_root=catalog_root, mechanical_root=mechanical_root,
        review_root=review_root, plan_path=plan_path, expected_profile_id=expected_profile_id,
        expected_query_snapshot_id=expected_query_snapshot_id, expected_plan_id=expected_plan_id)
    return _from_pilot(pilot, review_root=review_root, successor_root=successor_root)


def write_reassessments(root, pilot, source_package, *, review_root):
    """Explicit fixed package construction, validated before creating any output."""
    from gameplay_rules.projection.mana_context_package import manifest as validate_source_package
    # Accept only the actual immutable package type and exact independent view;
    # callers use source load/build APIs to establish its complete parent binding.
    from gameplay_rules.projection.mana_context_package import ContextPackage
    if type(pilot) is not InterpretationReviewPilot:
        raise PilotError('validated immutable original pilot required')
    if type(source_package) is not ContextPackage:
        raise PilotError('validated immutable context package required')
    package = source_package.to_dict()
    validate_source_package(package, review_root=review_root)
    original = pilot.comparison().to_dict()
    value = _input(original, package)
    raw = owned(value, limit=INPUT_LIMIT)
    manifest = owned(_manifest(value), limit=INPUT_LIMIT)
    root = Path(root).absolute()
    if any(p.is_symlink() for p in (root, *root.parents)):
        raise PilotError('symlink destination forbidden')
    if root.exists() and (not root.is_dir() or any(root.iterdir())):
        raise PilotError('append-only new or empty successor destination required')
    root.mkdir(parents=True, exist_ok=True)
    for name, data in (('reassessments.json', raw), ('manifest.json', manifest)):
        with (root / name).open('xb') as stream:
            stream.write(data)
    return _document(value, INPUT_LIMIT)


def render_reassessment(document):
    value = document.to_dict()
    if 'comparisons' not in value:
        return canonical(value).decode()
    lines = ['Source-backed pending mana reassessment; authored interpretation requires review.',
        'human_attestation=null; canonical_admission=false; execution_authority=BLOCKED',
        'SCOPE: retained Card text only. The original universal questions remain UNKNOWN.']
    records = {r['subject_id']: r for r in value['reassessments']}
    for row in value['comparisons']:
        lines += ['', row['subject_id'], 'Original candidate: ' + row['original_candidate_id']]
        record = records.get(row['subject_id'])
        if record:
            lines += ['Original reading: ' + record['original_criterion']['state'] + ' — ' + record['original_criterion']['rationale'],
                'Source support: ' + ', '.join(r['rule_reference'] for r in record['new_source_support']),
                'Scope change: ' + record['scope_change'], record['scope_explanation'],
                'Complete selected passage: ' + record['original_subject']['selected_passage'],
                'Complete retained Card field: ' + record['original_subject']['complete_field_value'],
                'Authored reassessment: ' + record['candidate_specific_rationale'],
                'Proposed reading: ' + record['proposed_state'],
                'Counterevidence: ' + record['counterevidence'],
                'Associated changes: ' + record['associated_revision_explanation']]
        else:
            lines += ['Unchanged control; original interpretation and identity retained.']
        for prefix, key in (('Before', 'before'), ('After', 'after')):
            result = row[key]
            lines += [prefix + ' substantive: ' + result['substantive_result'],
                prefix + ' method: ' + result['method_status'],
                prefix + ' overall: ' + result['overall_assessment']]
    return '\n'.join(lines + ['', *LIMITATIONS]) + '\n'
